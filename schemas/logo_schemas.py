from pydantic import BaseModel

class LogoGenerateIn(BaseModel):
    company_name: str
    style_feedback: str = ""

class LogoGenerateOut(BaseModel):
    company_name: str
    logo_prompt: str
    logo_url: str
    logo_status: str
