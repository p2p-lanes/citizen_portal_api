from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class ApplicationBase(BaseModel):
    first_name: str
    last_name: str
    email: str
    telegram_username: Optional[str]
    organization: Optional[str]
    role: Optional[str]
    gender: Optional[str]
    age: Optional[str]


class ApplicationCreate(ApplicationBase):
    pass


class Application(ApplicationBase):
    id: UUID

    class Config:
        from_attributes = True  # Allows Pydantic models to read SQLAlchemy models
