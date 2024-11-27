from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class PopUpCityBase(BaseModel):
    name: str
    tagline: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class PopUpCityCreate(PopUpCityBase):
    pass


class PopUpCity(PopUpCityBase):
    id: UUID

    model_config = {
        'from_attributes': True  # Allows Pydantic models to read SQLAlchemy models
    }
