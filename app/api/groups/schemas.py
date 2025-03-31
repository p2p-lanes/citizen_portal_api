from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, field_validator


class GroupMember(BaseModel):
    first_name: str
    last_name: str
    email: str
    telegram: Optional[str] = None
    organization: Optional[str] = None
    role: Optional[str] = None
    gender: Optional[str] = None

    @field_validator('first_name', 'last_name', 'email')
    def validate_required_fields(cls, value: str) -> str:
        if not value:
            raise ValueError('This field cannot be empty')
        return value

    @field_validator('telegram', 'organization', 'role', 'gender')
    def validate_optional_fields(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not value:
            raise ValueError('This field cannot be empty if provided')
        return value

    @field_validator('email')
    def clean_email(cls, value: str) -> str:
        return value.lower()

    model_config = ConfigDict(str_strip_whitespace=True)


class GroupBase(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    discount_percentage: float
    popup_city_id: int
    max_members: int

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Group(GroupBase):
    id: int
    popup_name: str

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


class GroupFilter(BaseModel):
    id: Optional[int] = None
    id_in: Optional[List[int]] = None
    name: Optional[str] = None
    slug: Optional[str] = None
    popup_city_id: Optional[int] = None
