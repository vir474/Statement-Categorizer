from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CategoryBase(BaseModel):
    name: str
    parent_id: Optional[int] = None
    color: str = "#6366f1"
    icon: str = "tag"


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[int] = None
    color: Optional[str] = None
    icon: Optional[str] = None


class CategoryRead(CategoryBase):
    id: int
    is_user_defined: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class CategoryRuleBase(BaseModel):
    pattern: str
    is_regex: bool = False
    priority: int = 100


class CategoryRuleCreate(CategoryRuleBase):
    category_id: int


class CategoryRuleRead(CategoryRuleBase):
    id: int
    category_id: int
    created_at: datetime

    model_config = {"from_attributes": True}
