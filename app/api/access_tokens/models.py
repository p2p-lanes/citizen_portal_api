from sqlalchemy import Column, DateTime, Integer, String, Text

from app.core.database import Base
from app.core.utils import current_time


class AccessToken(Base):
    """Model to store access tokens for various external services"""

    __tablename__ = 'access_tokens'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    value = Column(Text, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=current_time)
    updated_at = Column(DateTime, default=current_time, onupdate=current_time)
