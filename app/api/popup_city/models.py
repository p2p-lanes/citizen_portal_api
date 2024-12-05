from sqlalchemy import Boolean, Column, DateTime, Integer, String
from datetime import datetime

from app.core.database import Base


class PopUpCity(Base):
    __tablename__ = 'popups'

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        unique=True,
        index=True,
    )
    name = Column(String, index=True, nullable=False)
    slug = Column(String, index=True, nullable=False, unique=True)
    tagline = Column(String)
    location = Column(String)
    image_url = Column(String)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    clickable_in_portal = Column(Boolean, nullable=True, default=False)
    visible_in_portal = Column(Boolean, nullable=True, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String)
    updated_by = Column(String)
