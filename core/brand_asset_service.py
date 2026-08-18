import json
import os
from typing import Any

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_deepseek import ChatDeepSeek

from schemas.brand_asset_schemas import BrandAssetGenerated


load_dotenv()

SYSTEM_PROMPT = """你是一位严谨的中文品牌战略与视觉顾问。请为已确认的企业/品牌名称制作可执行的品牌价值资产包。
要求：定位具体、Slogan 有差异、Logo 方向可交付设计师、色值可直接使用。风险提示必须区分事实与建议，绝不能声称已完成法律审查、商标核准或域名注册。未知信息明确标注未知。"""

PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        (
            "user",
            """品牌名：{name}
名称寓意：{moral}
名称出处：{reference}
原始命名条件：{conditions}
用户补充简报：{brief}
名称校验快照：{validation}

请输出：品牌定位说明、3-6 条 Slogan、2-4 个 Logo 概念方向、完整品牌视觉建议，以及至少两条风险与行动建议。""",
        ),
    ]
)


async def generate_brand_asset_content(
    *,
    name: str,
    moral: str,
    reference: str,
    conditions: dict[str, Any],
    brief: str,
    validation_snapshot: dict[str, Any],
) -> BrandAssetGenerated:
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("未配置 DEEPSEEK_API_KEY，无法生成品牌资产")
    llm = ChatDeepSeek(
        model="deepseek-chat", api_key=api_key, temperature=0.55, timeout=120
    ).with_structured_output(BrandAssetGenerated)
    chain = PROMPT | llm
    payload = {
        "name": name,
        "moral": moral or "未提供",
        "reference": reference or "未提供",
        "conditions": json.dumps(conditions or {}, ensure_ascii=False),
        "brief": brief or "无补充",
        "validation": json.dumps(
            validation_snapshot or {"status": "not_run"}, ensure_ascii=False
        ),
    }
    last_error: Exception | None = None
    for _ in range(3):
        try:
            result = await chain.ainvoke(payload)
            if result is not None:
                return result
        except Exception as exc:
            last_error = exc
    raise RuntimeError("品牌资产生成失败，请稍后重试") from last_error


def build_domain_matrix(validation_snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    matrix = []
    for item in validation_snapshot.get("domains", []):
        domain = str(item.get("domain", ""))
        suffix = domain.rsplit(".", 1)[-1].lower() if "." in domain else ""
        status = item.get("status", "unknown")
        role = {
            "com": "全球主站",
            "cn": "中国市场主站",
            "net": "品牌保护",
            "io": "科技产品入口",
        }.get(suffix, "品牌保护")
        recommendation = {
            "available": "优先注册并同步配置品牌保护",
            "registered": "评估替代拼写、其他后缀或合规收购",
        }.get(status, "查询结果不完整，需人工复核")
        matrix.append(
            {
                "domain": domain,
                "suffix": suffix,
                "role": role,
                "status": status,
                "recommendation": recommendation,
                "source": item.get("source", "name_validation"),
            }
        )
    return matrix


def build_validation_snapshot(validation: Any | None) -> dict[str, Any]:
    if validation is None:
        return {"status": "not_run", "message": "尚未执行名称综合校验"}
    return {
        "id": validation.id,
        "status": validation.status,
        "risk_score": validation.risk_score,
        "risk_level": validation.risk_level,
        "coverage": validation.coverage,
        "risk_summary": validation.risk_summary,
        "domains": validation.domains,
        "trademark": validation.trademark,
        "company": validation.company,
        "social": validation.social,
    }
