from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class GroupMember(BaseModel):
    first_name: str
    last_name: str
    email: str


class GroupBase(BaseModel):
    name: str
    description: Optional[str] = None
    discount_percentage: float
    popup_city_id: int
    max_members: int

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Group(GroupBase):
    id: int

    model_config = ConfigDict(
        from_attributes=True,
    )


class GroupFilter(BaseModel):
    id: Optional[int] = None
    id_in: Optional[List[int]] = None
    name: Optional[str] = None
    popup_city_id: Optional[int] = None
