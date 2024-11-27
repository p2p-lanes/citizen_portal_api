from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class CitizenBase(BaseModel):
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class CitizenCreate(CitizenBase):
    pass


class InternalCitizenCreate(CitizenCreate):
    spice: Optional[str] = None


class Citizen(CitizenBase):
    id: UUID

    class Config:
        from_attributes = True  # Allows Pydantic models to read SQLAlchemy models
