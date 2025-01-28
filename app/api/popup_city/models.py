from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String

from app.core.database import Base


class EmailTemplate(Base):
    __tablename__ = 'popup_email_templates'

    id = Column(Integer, primary_key=True)
    popup_city_id = Column(Integer, ForeignKey('popups.id'), nullable=False)
    event = Column(String, nullable=False)
    template = Column(String, nullable=False)
    frequency = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


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
    passes_description = Column(String)
    image_url = Column(String)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    clickable_in_portal = Column(Boolean, nullable=True, default=False)
    visible_in_portal = Column(Boolean, nullable=True, default=False)
    requires_approval = Column(Boolean, nullable=False, default=True)
    portal_order = Column(Float, nullable=False, default=0)
    simplefi_api_key = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String)
    updated_by = Column(String)
