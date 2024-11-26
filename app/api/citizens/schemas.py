from pydantic import BaseModel
from uuid import UUID


class CitizenBase(BaseModel):
    first_name: str
    last_name: str
    email: str


class CitizenCreate(CitizenBase):
    pass


class Citizen(CitizenBase):
    id: UUID

    class Config:
        from_attributes = True  # Allows Pydantic models to read SQLAlchemy models
