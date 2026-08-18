from pydantic import BaseModel, Field
from typing import Annotated, Literal
# result:success / result:failure
class ResponseOut(BaseModel):
    
    result: Annotated[Literal["success", "failure"], Field("success", 
    description="操作的结果！")]
    message: str = "操作成功"
