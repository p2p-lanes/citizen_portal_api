from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class PopUpCityBase(BaseModel):
    name: str
    slug: str
    tagline: Optional[str] = None
    location: Optional[str] = None
    passes_description: Optional[str] = None
    image_url: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    clickable_in_portal: Optional[bool] = False
    visible_in_portal: Optional[bool] = False
    requires_approval: Optional[bool] = True

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PopUpCityCreate(PopUpCityBase):
    pass


class PopUpCity(PopUpCityBase):
    id: int

    model_config = ConfigDict(
        from_attributes=True,
    )
