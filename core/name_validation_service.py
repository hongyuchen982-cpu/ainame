import asyncio
import json
import os
import time
from difflib import SequenceMatcher
from urllib.parse import quote

import httpx


IANA_RDAP_BOOTSTRAP = "https://data.iana.org/rdap/dns.json"
DEFAULT_SUFFIXES = ["com", "cn", "net", "io"]
_bootstrap_cache: tuple[float, dict] | None = None
_bootstrap_lock = asyncio.Lock()


async def _rdap_bootstrap(client: httpx.AsyncClient) -> dict:
    global _bootstrap_cache
    if _bootstrap_cache and time.monotonic() - _bootstrap_cache[0] < 86400:
        return _bootstrap_cache[1]
    async with _bootstrap_lock:
        if _bootstrap_cache and time.monotonic() - _bootstrap_cache[0] < 86400:
            return _bootstrap_cache[1]
        response = await client.get(IANA_RDAP_BOOTSTRAP)
        response.raise_for_status()
        data = response.json()
        _bootstrap_cache = (time.monotonic(), data)
        return data


def _rdap_base(bootstrap: dict, suffix: str) -> str | None:
    suffix = suffix.lower().lstrip(".")
    for tlds, urls in bootstrap.get("services", []):
        if suffix in {str(item).lower() for item in tlds} and urls:
            return str(urls[0]).rstrip("/")
    return None


async def check_domain_rdap(
    client: httpx.AsyncClient, stem: str, suffix: str
) -> dict:
    domain = f"{stem}.{suffix.lower().lstrip('.')}"
    try:
        bootstrap = await _rdap_bootstrap(client)
        base = _rdap_base(bootstrap, suffix)
        if not base:
            return {"domain": domain, "status": "unknown", "message": "该后缀没有 RDAP 引导服务"}
        response = await client.get(f"{base}/domain/{quote(domain)}")
        if response.status_code == 404:
            return {"domain": domain, "status": "available", "message": "RDAP 未发现注册记录"}
        if response.status_code == 200:
            data = response.json()
            return {
                "domain": domain,
                "status": "registered",
                "message": "RDAP 已发现注册记录",
                "handle": str(data.get("handle", "")),
            }
        return {"domain": domain, "status": "unknown", "message": f"RDAP 返回 HTTP {response.status_code}"}
    except Exception as exc:
        return {"domain": domain, "status": "unknown", "message": f"RDAP 查询失败：{exc}"}


async def _configured_provider(
    client: httpx.AsyncClient, *, name: str, url_env: str, token_env: str
) -> dict:
    url = os.getenv(url_env, "").strip()
    if not url:
        return {"status": "unavailable", "matches": [], "message": "未配置数据提供商"}
    headers = {"Accept": "application/json"}
    token = os.getenv(token_env, "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        response = await client.post(url, json={"name": name}, headers=headers)
        response.raise_for_status()
        body = response.json()
        matches = body.get("matches", []) if isinstance(body, dict) else []
        normalized = []
        for item in matches[:20]:
            if not isinstance(item, dict):
                continue
            candidate = str(item.get("name", "")).strip()
            similarity = item.get("similarity")
            if similarity is None and candidate:
                similarity = SequenceMatcher(None, name.casefold(), candidate.casefold()).ratio()
            normalized.append({**item, "name": candidate, "similarity": round(float(similarity or 0), 4)})
        return {"status": "completed", "matches": normalized, "message": "查询完成"}
    except Exception as exc:
        return {"status": "error", "matches": [], "message": f"提供商查询失败：{exc}"}


async def check_social_profiles(client: httpx.AsyncClient, username: str) -> dict:
    raw = os.getenv("SOCIAL_PROFILE_TEMPLATES", "").strip()
    if not raw:
        return {"status": "unavailable", "profiles": [], "message": "未配置社交平台查询模板"}
    try:
        templates = json.loads(raw)
        if not isinstance(templates, dict):
            raise ValueError("必须是 JSON 对象")
    except Exception as exc:
        return {"status": "error", "profiles": [], "message": f"社交平台配置错误：{exc}"}

    async def one(platform: str, template: str) -> dict:
        url = str(template).replace("{username}", quote(username))
        try:
            response = await client.get(url, follow_redirects=True)
            if response.status_code == 404:
                status = "available"
            elif response.status_code == 200:
                status = "occupied"
            else:
                status = "unknown"
            return {"platform": platform, "url": url, "status": status, "http_status": response.status_code}
        except Exception as exc:
            return {"platform": platform, "url": url, "status": "unknown", "message": str(exc)}

    profiles = await asyncio.gather(*(one(key, value) for key, value in templates.items()))
    return {"status": "completed", "profiles": profiles, "message": "查询完成"}


def calculate_risk(domains: list[dict], trademark: dict, company: dict, social: dict) -> dict:
    score = 0
    reasons: list[str] = []
    covered = 0
    known_domains = [item for item in domains if item.get("status") in {"available", "registered"}]
    if known_domains:
        covered += 1
        registered = sum(item["status"] == "registered" for item in known_domains)
        if registered:
            score += round(25 * registered / len(known_domains))
            reasons.append(f"{registered} 个已确认后缀存在注册记录")
    if trademark.get("status") == "completed":
        covered += 1
        maximum = max((float(item.get("similarity", 0)) for item in trademark.get("matches", [])), default=0)
        if maximum >= 0.9:
            score += 40; reasons.append("发现高度近似商标")
        elif maximum >= 0.75:
            score += 25; reasons.append("发现较近似商标")
        elif maximum >= 0.6:
            score += 12; reasons.append("发现一定近似度商标")
    if company.get("status") == "completed":
        covered += 1
        matches = company.get("matches", [])
        if any(float(item.get("similarity", 0)) >= 0.98 for item in matches):
            score += 35; reasons.append("发现高度重名企业")
        elif matches:
            score += 15; reasons.append("发现相似企业名称")
    if social.get("status") == "completed":
        covered += 1
        known = [item for item in social.get("profiles", []) if item.get("status") in {"available", "occupied"}]
        occupied = sum(item["status"] == "occupied" for item in known)
        if known and occupied:
            score += round(10 * occupied / len(known)); reasons.append(f"{occupied} 个社交平台名称已占用")
    score = min(score, 100)
    level = "unknown" if covered == 0 else "high" if score >= 60 else "medium" if score >= 30 else "low"
    coverage = round(covered / 4 * 100)
    if covered < 4:
        reasons.append(f"仅完成 {covered}/4 类数据源，结论需谨慎")
    if not reasons:
        reasons.append("已查询的数据源暂未发现明显冲突")
    return {"score": score, "level": level, "coverage": coverage, "summary": "；".join(reasons)}


async def run_name_validation(name: str, domain_stem: str, suffixes: list[str]) -> dict:
    timeout = httpx.Timeout(8.0, connect=4.0)
    async with httpx.AsyncClient(timeout=timeout, headers={"User-Agent": "AiNameValidation/1.0"}) as client:
        domain_future = asyncio.gather(*(check_domain_rdap(client, domain_stem, suffix) for suffix in suffixes))
        trademark_future = _configured_provider(
            client, name=name, url_env="TRADEMARK_CHECK_API_URL", token_env="TRADEMARK_CHECK_API_TOKEN"
        )
        company_future = _configured_provider(
            client, name=name, url_env="COMPANY_CHECK_API_URL", token_env="COMPANY_CHECK_API_TOKEN"
        )
        social_future = check_social_profiles(client, domain_stem)
        domains, trademark, company, social = await asyncio.gather(
            domain_future, trademark_future, company_future, social_future
        )
    risk = calculate_risk(domains, trademark, company, social)
    statuses = [
        "completed" if any(item.get("status") != "unknown" for item in domains) else "error",
        trademark.get("status"), company.get("status"), social.get("status"),
    ]
    successful = sum(status == "completed" for status in statuses)
    status = "completed" if successful == 4 else "partial" if successful else "failed"
    return {"status": status, "domains": domains, "trademark": trademark,
            "company": company, "social": social, **risk}
