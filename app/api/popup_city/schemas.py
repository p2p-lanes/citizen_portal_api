from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PopUpCityBase(BaseModel):
    name: str
    tagline: Optional[str] = None
    location: Optional[str] = None
    image_url: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class PopUpCityCreate(PopUpCityBase):
    pass


class PopUpCity(PopUpCityBase):
    id: UUID

    model_config = ConfigDict(
        from_attributes=True,
    )
