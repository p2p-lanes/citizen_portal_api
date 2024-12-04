from typing import Optional
from datetime import date

from pydantic import BaseModel, ConfigDict

from app.api.citizens.schemas import Citizen


class ApplicationFilter(BaseModel):
    email: Optional[str] = None
    citizen_id: Optional[int] = None
    popup_city_id: Optional[int] = None
    status: Optional[str] = None


class ApplicationBaseCommon(BaseModel):
    first_name: str
    last_name: str
    telegram: Optional[str] = None
    organization: Optional[str] = None
    role: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[str] = None
    social_media: Optional[str] = None
    residence: Optional[str] = None
    local_resident: Optional[bool] = None
    eth_address: Optional[str] = None

    duration: Optional[str] = None
    check_in: Optional[date] = None
    check_out: Optional[date] = None

    builder_boolean: Optional[bool] = None
    builder_description: Optional[str] = None

    hackathon_interest: Optional[bool] = None
    gitcoin_oss: Optional[bool] = None
    draft_and_demos: Optional[bool] = None
    host_session: Optional[str] = None
    personal_goals: Optional[str] = None
    referral: Optional[str] = None
    info_to_share: Optional[list[str]] = None

    investor: Optional[bool] = None
    success_definition: Optional[list[str]] = None
    top_tracks: Optional[list[str]] = None

    # Family information
    brings_spouse: Optional[bool] = None
    spouse_info: Optional[str] = None
    spouse_email: Optional[str] = None
    brings_kids: Optional[bool] = None
    kids_info: Optional[str] = None

    # Scholarship information
    scolarship_request: Optional[bool] = None
    scolarship_categories: Optional[list[str]] = None
    scolarship_details: Optional[str] = None

    status: Optional[str] = None


class ApplicationBase(ApplicationBaseCommon):
    citizen_id: int
    popup_city_id: int


class ApplicationCreate(ApplicationBase):
    pass


class ApplicationUpdate(ApplicationBaseCommon):
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class InternalApplicationCreate(ApplicationBase):
    email: str


class Application(InternalApplicationCreate):
    id: int
    citizen: Optional[Citizen] = None

    model_config = ConfigDict(
        from_attributes=True,
    )
