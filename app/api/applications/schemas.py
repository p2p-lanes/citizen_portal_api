from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator

from app.api.applications.attendees.schemas import Attendee
from app.api.products.schemas import Product


class ApplicationStatus(str, Enum):
    DRAFT = 'draft'
    IN_REVIEW = 'in review'
    REJECTED = 'rejected'
    ACCEPTED = 'accepted'


class UserSettableStatus(str, Enum):
    DRAFT = ApplicationStatus.DRAFT.value
    IN_REVIEW = ApplicationStatus.IN_REVIEW.value


class TicketCategory(str, Enum):
    STANDARD = 'standard'
    DISCOUNTED = 'discounted'


class ApplicationFilter(BaseModel):
    email: Optional[str] = None
    citizen_id: Optional[int] = None
    popup_city_id: Optional[int] = None
    status: Optional[ApplicationStatus] = None


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
    video_url: Optional[str] = None

    hackathon_interest: Optional[bool] = None
    host_session: Optional[str] = None
    personal_goals: Optional[str] = None
    referral: Optional[str] = None
    info_not_shared: Optional[list[str]] = None
    investor: Optional[bool] = None

    # Family information
    brings_spouse: Optional[bool] = None
    spouse_info: Optional[str] = None
    spouse_email: Optional[str] = None
    brings_kids: Optional[bool] = None
    kids_info: Optional[str] = None

    # Builder information
    builder_boolean: Optional[bool] = None
    builder_description: Optional[str] = None

    # Scholarship information
    scholarship_request: Optional[bool] = None
    scholarship_details: Optional[str] = None
    scholarship_video_url: Optional[str] = None

    status: Optional[ApplicationStatus] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ApplicationBase(ApplicationBaseCommon):
    citizen_id: int
    popup_city_id: int


class ApplicationCreate(ApplicationBase):
    status: Optional[UserSettableStatus] = None


class ApplicationUpdate(ApplicationBaseCommon):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    status: Optional[UserSettableStatus] = None


class InternalApplicationCreate(ApplicationBase):
    email: str
    ticket_category: Optional[TicketCategory] = None

    @field_validator('email')
    @classmethod
    def clean_email(cls, value: str) -> str:
        return value.lower().strip()


class Application(InternalApplicationCreate):
    id: int
    attendees: Optional[list[Attendee]] = None
    ticket_category: Optional[TicketCategory] = None
    discount_assigned: Optional[int] = None
    products: Optional[list[Product]] = None

    model_config = ConfigDict(
        from_attributes=True,
    )
