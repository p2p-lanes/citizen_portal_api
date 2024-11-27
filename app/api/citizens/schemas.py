from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class CitizenBase(BaseModel):
    primary_email: str
    secondary_email: Optional[str] = None
    email_validated: bool = False
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class CitizenCreate(CitizenBase):
    pass


class InternalCitizenCreate(CitizenCreate):
    spice: Optional[str] = None


class Citizen(CitizenBase):
    id: UUID

    model_config = {
        'from_attributes': True  # Allows Pydantic models to read SQLAlchemy models
    }
