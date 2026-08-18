from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class PackageOut(BaseModel):
    id: int
    name: str
    price: Decimal
    description: str
    credit_count: int
    sort_order: int

    model_config = ConfigDict(from_attributes=True)


class AdminPackageOut(PackageOut):
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PackageCreateIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field("", max_length=255)
    price: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)
    credit_count: int = Field(..., ge=1, le=100000)
    is_active: bool = True
    sort_order: int = Field(0, ge=0, le=1000000)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("套餐名称不能为空")
        return value

    @field_validator("description")
    @classmethod
    def strip_description(cls, value: str) -> str:
        return value.strip()


class PackageUpdateIn(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=255)
    price: Decimal | None = Field(None, gt=0, max_digits=10, decimal_places=2)
    credit_count: int | None = Field(None, ge=1, le=100000)
    sort_order: int | None = Field(None, ge=0, le=1000000)

    @field_validator("name")
    @classmethod
    def strip_optional_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("套餐名称不能为空")
        return value

    @field_validator("description")
    @classmethod
    def strip_optional_description(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None

    @model_validator(mode="after")
    def require_change(self):
        if not self.model_fields_set:
            raise ValueError("没有需要修改的套餐字段")
        for field_name in self.model_fields_set:
            if getattr(self, field_name) is None:
                raise ValueError(f"套餐字段 {field_name} 不能为 null")
        return self


class PackageStatusIn(BaseModel):
    is_active: bool


class PackageSortItem(BaseModel):
    id: int = Field(..., ge=1)
    sort_order: int = Field(..., ge=0, le=1000000)


class PackageSortIn(BaseModel):
    items: list[PackageSortItem] = Field(..., min_length=1, max_length=200)

    @model_validator(mode="after")
    def unique_ids(self):
        ids = [item.id for item in self.items]
        if len(ids) != len(set(ids)):
            raise ValueError("套餐排序列表中存在重复 ID")
        return self
