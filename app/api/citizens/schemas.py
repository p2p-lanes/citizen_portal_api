from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class Authenticate(BaseModel):
    email: str


class CitizenBase(BaseModel):
    primary_email: str
    secondary_email: Optional[str] = None
    email_validated: Optional[bool] = False
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CitizenCreate(CitizenBase):
    pass


class InternalCitizenCreate(CitizenCreate):
    spice: Optional[str] = None


class Citizen(CitizenBase):
    id: int

    model_config = ConfigDict(
        from_attributes=True,
        exclude={'applications'},
    )


class CitizenFilter(BaseModel):
    id: int | None = None
    primary_email: str | None = None
