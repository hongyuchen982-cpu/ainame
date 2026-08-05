from pathlib import Path
from uuid import uuid4

import httpx
import settings

BACKEND_DIR = Path(__file__).resolve().parents[1]
LOGO_DIR = BACKEND_DIR / "static" / "logos"
LOGO_DIR.mkdir(parents=True, exist_ok=True)


def build_logo_prompt(company_name: str, style_feedback: str = "") -> str:
    feedback = style_feedback.strip() or "首次生成，按企业名称设计。"
    return f"""
为企业品牌“{company_name}”设计一枚专业 Logo 图形。
用户要求：{feedback}
设计要求：
1. 只生成独立 Logo 图形，不要生成中文、英文、字母或数字。
2. 极简、现代、扁平化、矢量图标风格。
3. 白色纯背景，主体居中。
4. 适合企业官网、App 图标、名片、宣传物料使用。
5. 不要水印、二维码、样机、纸张、墙面展示、复杂背景。
""".strip()


def pick_image_url(data: dict) -> str:
    """解析通义万相接口返回的图片地址"""
    # 兼容标准的 text2image 返回格式
    results = data.get("output", {}).get("results", [])
    if results and isinstance(results, list):
        return results[0].get("url", "")

    # 兼容 choices 嵌套格式
    for choice in data.get("output", {}).get("choices", []):
        for item in choice.get("message", {}).get("content", []):
            if item.get("image"):
                return item["image"]
    return ""


def generate_company_logo(company_name: str, style_feedback: str = "") -> dict:
    logo_prompt = build_logo_prompt(company_name, style_feedback)
    if not settings.DASHSCOPE_API_KEY or not settings.DASHSCOPE_IMAGE_API_URL:
        return {
            "logo_prompt": logo_prompt,
            "logo_url": "",
            "logo_status": (
                "未配置 DASHSCOPE_API_KEY 或 DASHSCOPE_IMAGE_API_URL"
            ),
        }

    request_url = settings.DASHSCOPE_IMAGE_API_URL

    # wan2.6-t2i 使用多模态生成同步接口的 messages 协议。
    payload = {
        "model": settings.WANXIANG_MODEL,
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": logo_prompt}],
                }
            ]
        },
        "parameters": {
            "prompt_extend": True,
            "watermark": False,
            "n": 1,
            "negative_prompt": (
                "文字，字母，数字，水印，二维码，照片，名片样机，"
                "墙面样机，复杂背景，模糊，变形"
            ),
            "size": "1280*1280",
        },
    }

    headers = {
        "Authorization": f"Bearer {settings.DASHSCOPE_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        with httpx.Client(timeout=180, follow_redirects=True) as client:
            response = client.post(request_url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

            if data.get("code"):
                return {
                    "logo_prompt": logo_prompt,
                    "logo_url": "",
                    "logo_status": f"生成失败：{data.get('code')} - {data.get('message')}",
                }

            image_url = pick_image_url(data)
            if not image_url:
                return {
                    "logo_prompt": logo_prompt,
                    "logo_url": "",
                    "logo_status": "生成失败：没有拿到图片地址",
                }

            image_response = client.get(image_url)
            image_response.raise_for_status()

        file_name = f"{uuid4().hex}.png"
        file_path = LOGO_DIR / file_name
        file_path.write_bytes(image_response.content)

        return {
            "logo_prompt": logo_prompt,
            "logo_url": f"{settings.APP_BASE_URL}/static/logos/{file_name}",
            "logo_status": "生成成功",
        }

    except httpx.TimeoutException:
        return {
            "logo_prompt": logo_prompt,
            "logo_url": "",
            "logo_status": "生成失败：请求超时",
        }
    except httpx.HTTPStatusError as exc:
        try:
            error_data = exc.response.json()
            error_detail = (
                f"{error_data.get('code', 'UnknownError')} - "
                f"{error_data.get('message', exc.response.text)}"
            )
        except ValueError:
            error_detail = exc.response.text[:300]

        return {
            "logo_prompt": logo_prompt,
            "logo_url": "",
            "logo_status": (
                f"生成失败：HTTP {exc.response.status_code} "
                f"{error_detail}"
            ),
        }
    except Exception as exc:
        return {
            "logo_prompt": logo_prompt,
            "logo_url": "",
            "logo_status": f"生成失败：{exc}",
        }
