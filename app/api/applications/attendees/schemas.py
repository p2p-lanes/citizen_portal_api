from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class AttendeeBase(BaseModel):
    application_id: int
    name: str
    category: str
    email: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AttendeeCreate(BaseModel):
    name: str
    category: str
    email: Optional[str] = None


class InternalAttendeeCreate(AttendeeCreate):
    application_id: int


class AttendeeUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    category: Optional[str] = None


class Attendee(AttendeeBase):
    id: int

    model_config = ConfigDict(
        from_attributes=True,
    )


class AttendeeFilter(BaseModel):
    id: Optional[int] = None
    application_id: Optional[int] = None
    name: Optional[str] = None
    category: Optional[str] = None
    email: Optional[str] = None
