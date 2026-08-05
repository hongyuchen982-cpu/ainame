
from pydantic import BaseModel, Field
from typing import Annotated, Literal,List
from pydantic import BaseModel, Field, model_validator

class NameSchema(BaseModel):
    name: Annotated[str, Field(..., description="姓名")]
    reference: Annotated[str, Field(..., description="出处")]
    moral: Annotated[str, Field(..., description="寓意")]
    domain: str = Field(..., description="为该品牌设计的纯小写 .com 域名，例如: astar.com")
# 👇 新增：默认状态，稍后由我们的工具自动填入
    domain_status: str = Field(default="正在查询...", description="域名的注册状态")
class NameResultSchema(BaseModel):
    names: List[NameSchema]


CategoryLiteral = Literal["人名", "企业名", "宠物名"]
class NameIn(BaseModel):
    category: Annotated[
        CategoryLiteral,
        Field("人名", description="命名场景：人名、企业名、宠物名")
    ]

    surname: Annotated[
        str,
        Field("", description="姓氏，企业名和宠物名可以为空")
    ]

    gender: Annotated[
        Literal["不限", "男", "女"],
        Field("不限", description="性别，人名专属")
    ]

    length: Annotated[
        Literal["不限", "单字", "两字", "多字"],
        Field("不限", description="字数要求")
    ]

    other: Annotated[
        str | None,
        Field("", description="核心诉求、行业属性或性格特征")
    ]

    exclude: Annotated[
        List[str],
        Field(default_factory=list, description="需要排除的名字或字")
    ]

    @model_validator(mode="after")
    def validate_fields_by_category(self) -> "NameIn":
        if self.category == "人名" and not self.surname:
            raise ValueError("生成人名时，姓氏不能为空！")

        return self

class NameOut(BaseModel):
    names: List[NameSchema]

class NameWithThreadOut(BaseModel):
    thread_id: str
    names: List[NameSchema]

class FeedbackIn(BaseModel):
    thread_id: str = Field(..., description="前端回传的会话ID")
    category: Literal["人名", "企业名", "宠物名"] = Field(..., description="路由依据")
    feedback: str = Field(..., description="用户的修改意见，")
