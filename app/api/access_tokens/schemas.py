from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AccessTokenBase(BaseModel):
    """Base schema for access token"""

    name: str
    value: str
    expires_at: Optional[datetime] = None


class AccessTokenCreate(AccessTokenBase):
    """Schema for creating a new access token"""

    pass


class AccessTokenUpdate(BaseModel):
    """Schema for updating an access token"""

    value: Optional[str] = None
    expires_at: Optional[datetime] = None
