from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, field_validator

from app.api.products.schemas import Product


class AttendeeBase(BaseModel):
    application_id: int
    name: str
    category: str
    email: Optional[str] = None
    group_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AttendeeCreate(BaseModel):
    name: str
    category: str
    email: Optional[str] = None
    group_id: Optional[int] = None

    @field_validator('email')
    @classmethod
    def validate_email(cls, value: str) -> str:
        if not value:
            return None
        return value.lower().strip()


class InternalAttendeeCreate(AttendeeCreate):
    application_id: int


class AttendeeUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None

    @field_validator('email')
    @classmethod
    def validate_email(cls, value: str) -> str:
        if not value:
            return None
        return value.lower().strip()


class Attendee(AttendeeBase):
    id: int
    products: List[Product]

    model_config = ConfigDict(from_attributes=True)


class AttendeeFilter(BaseModel):
    id: Optional[int] = None
    application_id: Optional[int] = None
    name: Optional[str] = None
    category: Optional[str] = None
    email: Optional[str] = None
