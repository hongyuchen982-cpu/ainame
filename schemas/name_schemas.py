
from pydantic import BaseModel, Field
from typing import Annotated, List
class NameSchema(BaseModel):
    name: Annotated[str, Field(..., description="姓名")]
    reference: Annotated[str, Field(..., description="出处")]
    moral: Annotated[str, Field(..., description="寓意")]


class NameResultSchema(BaseModel):
    names: List[NameSchema]


from pydantic import BaseModel, Field
from typing import Annotated, Literal, List

class NameIn(BaseModel):
    surname: Annotated[str, Field(..., description="姓氏")]
    gender: Annotated[Literal["不限", "男", "女"], Field(..., description="性别")]
    length: Annotated[Literal["不限", "单字", "两字"], Field(..., description="字数")]
    other: Annotated[str|None, Field("", description="其他要求")]
    exclude: Annotated[List[str], Field([], description="排除的名字")]

class NameOut(BaseModel):
    names: List[NameSchema]