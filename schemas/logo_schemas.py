from pydantic import BaseModel, Field

class LogoGenerateIn(BaseModel):
    selection_id: int = Field(..., gt=0)
    style_feedback: str = Field("", max_length=500)

class LogoGenerateOut(BaseModel):
    selection_id: int
    company_name: str
    logo_prompt: str
    logo_url: str
    logo_status: str
