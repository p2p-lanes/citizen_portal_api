from datetime import datetime
from enum import Enum
from typing import Literal, Optional, Union

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
    payment_capacity: Optional[str] = None
    github_profile: Optional[str] = None

    hackathon_interest: Optional[bool] = None
    host_session: Optional[str] = None
    personal_goals: Optional[str] = None
    referral: Optional[str] = None
    info_not_shared: Optional[list[str]] = None
    investor: Optional[bool] = None

    # Renter information
    is_renter: Optional[bool] = None
    booking_confirmation: Optional[str] = None

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

    requested_discount: Optional[bool] = None
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
    submitted_at: Optional[datetime] = None

    @field_validator('email')
    @classmethod
    def clean_email(cls, value: str) -> str:
        return value.lower().strip()


class Application(InternalApplicationCreate):
    id: int
    attendees: Optional[list[Attendee]] = None
    discount_assigned: Optional[int] = None
    products: Optional[list[Product]] = None

    model_config = ConfigDict(
        from_attributes=True,
    )


HIDDEN_VALUE = '*'


class AttendeesDirectory(BaseModel):
    first_name: Union[Optional[str], Literal['*']]
    last_name: Union[Optional[str], Literal['*']]
    email: Union[Optional[str], Literal['*']]
    telegram: Union[Optional[str], Literal['*']]
    brings_kids: Union[Optional[bool], Literal['*']]
    role: Union[Optional[str], Literal['*']]
    organization: Union[Optional[str], Literal['*']]
    participation: Union[Optional[list[Product]], Literal['*']]
