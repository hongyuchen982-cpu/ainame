from fastapi import APIRouter, HTTPException

from core.logo_tools import generate_company_logo
from schemas.logo_schemas import LogoGenerateIn, LogoGenerateOut

router = APIRouter(prefix="/logos", tags=["logos"])


@router.post("/generate", response_model=LogoGenerateOut)
def generate_logo(data: LogoGenerateIn):
    company_name = data.company_name.strip()
    if not company_name:
        raise HTTPException(status_code=400, detail="请输入企业名称")

    logo = generate_company_logo(
        company_name=company_name,
        style_feedback=data.style_feedback,
    )

    return {
        "company_name": company_name,
        **logo,
    }
