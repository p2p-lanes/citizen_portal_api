from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.api.applications.models import Application


class Attendee(Base):
    __tablename__ = 'attendees'

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        unique=True,
        index=True,
    )
    application_id = Column(Integer, ForeignKey('applications.id'), nullable=False)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    email = Column(String)

    application: Mapped['Application'] = relationship(
        'Application', back_populates='attendees'
    )

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
