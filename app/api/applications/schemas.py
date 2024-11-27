from typing import Optional
from uuid import UUID

from pydantic import BaseModel
from app.api.citizens.models import Citizen


class ApplicationBase(BaseModel):
    citizen_id: UUID
    popup_city_id: UUID
    first_name: str
    last_name: str
    telegram: Optional[str] = None
    organization: Optional[str] = None
    role: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[str] = None


class ApplicationCreate(ApplicationBase):
    pass


class InternalApplicationCreate(ApplicationBase):
    email: str


class Application(InternalApplicationCreate):
    id: UUID
    citizen: Optional[Citizen] = None

    model_config = {
        'from_attributes': True,
        'arbitrary_types_allowed': True,
    }
