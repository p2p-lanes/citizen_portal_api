from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, field_validator

from app.api.products.schemas import Product


class GroupMemberValidatorMixin:
    """Mixin class for shared group member validators"""

    @field_validator('telegram', 'organization', 'role', 'gender')
    @classmethod
    def validate_optional_fields(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not value:
            raise ValueError('This field cannot be empty if provided')
        return value

    @field_validator('email')
    @classmethod
    def clean_email(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            return value.lower()
        return value


class GroupMember(BaseModel, GroupMemberValidatorMixin):
    first_name: str
    last_name: str
    email: str
    telegram: Optional[str] = None
    organization: Optional[str] = None
    role: Optional[str] = None
    gender: Optional[str] = None

    @field_validator('first_name', 'last_name', 'email')
    @classmethod
    def validate_required_fields(cls, value: str) -> str:
        if not value:
            raise ValueError('This field cannot be empty')
        return value

    model_config = ConfigDict(str_strip_whitespace=True)


class GroupMemberUpdate(BaseModel, GroupMemberValidatorMixin):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    telegram: Optional[str] = None
    organization: Optional[str] = None
    role: Optional[str] = None
    gender: Optional[str] = None


class GroupMemberBatch(BaseModel):
    members: List[GroupMember]

    @field_validator('members')
    @classmethod
    def validate_members_list(cls, value: List[GroupMember]) -> List[GroupMember]:
        if not value:
            raise ValueError('Members list cannot be empty')
        return value


class MemberWithProducts(GroupMember):
    id: int
    products: List[Product]


class MemberBatchResult(MemberWithProducts):
    success: bool
    err_msg: Optional[str] = None


class GroupBase(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    discount_percentage: float
    popup_city_id: int
    max_members: Optional[int] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Group(GroupBase):
    id: int
    popup_name: str

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


class GroupWithMembers(Group):
    members: List[MemberWithProducts]


class GroupFilter(BaseModel):
    id: Optional[int] = None
    id_in: Optional[List[int]] = None
    name: Optional[str] = None
    slug: Optional[str] = None
    popup_city_id: Optional[int] = None
