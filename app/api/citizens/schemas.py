from datetime import datetime
from typing import List, Optional
from urllib.parse import unquote

from pydantic import BaseModel, ConfigDict, field_validator


class Authenticate(BaseModel):
    email: str
    popup_slug: Optional[str] = None
    use_code: Optional[bool] = False

    model_config = ConfigDict(
        str_strip_whitespace=True,
        str_to_lower=True,
    )

    @field_validator('email')
    @classmethod
    def decode_email(cls, value: str) -> str:
        if not value:
            raise ValueError('Email cannot be empty')
        return unquote(value)


class CitizenBase(BaseModel):
    primary_email: str
    secondary_email: Optional[str] = None
    email_validated: Optional[bool] = False
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    x_user: Optional[str] = None
    telegram: Optional[str] = None
    gender: Optional[str] = None
    role: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @field_validator('primary_email')
    @classmethod
    def decode_primary_email(cls, value: str) -> str:
        return unquote(value)

    @field_validator('secondary_email')
    @classmethod
    def decode_secondary_email(cls, value: str) -> str:
        return unquote(value) if value else None


class CitizenCreate(CitizenBase):
    pass


class InternalCitizenCreate(CitizenCreate):
    spice: Optional[str] = None
    code: Optional[int] = None
    code_expiration: Optional[datetime] = None


class Citizen(CitizenBase):
    id: int

    model_config = ConfigDict(
        from_attributes=True,
        exclude={'applications'},
    )


class CitizenFilter(BaseModel):
    id: Optional[int] = None
    primary_email: Optional[str] = None

    @field_validator('primary_email')
    @classmethod
    def decode_primary_email(cls, value: str) -> str:
        return unquote(value) if value else None


class PoapClaim(BaseModel):
    attendee_id: int
    attendee_name: str
    attendee_email: str
    attendee_category: str
    poap_url: str
    poap_name: str
    poap_description: str
    poap_image_url: str
    poap_claimed: bool
    poap_is_active: bool


class CitizenPoapsByPopup(BaseModel):
    popup_id: int
    popup_name: str
    poaps: List[PoapClaim]


class CitizenPoaps(BaseModel):
    results: List[CitizenPoapsByPopup]
