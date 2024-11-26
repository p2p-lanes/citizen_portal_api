from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class CitizenBase(BaseModel):
    email: str
    first_name: Optional[str]
    last_name: Optional[str]


class CitizenCreate(CitizenBase):
    pass


class Citizen(CitizenBase):
    id: UUID

    class Config:
        from_attributes = True  # Allows Pydantic models to read SQLAlchemy models
