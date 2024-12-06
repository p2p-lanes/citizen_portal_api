from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, event
from sqlalchemy.orm import relationship

from app.core.database import Base


class Citizen(Base):
    __tablename__ = 'citizens'

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        unique=True,
        index=True,
    )
    primary_email = Column(String, index=True, unique=True, nullable=False)
    secondary_email = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    email_validated = Column(Boolean, default=False)
    spice = Column(String)
    applications = relationship('Application', back_populates='citizen')

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String)
    updated_by = Column(String)


@event.listens_for(Citizen, 'before_insert')
def clean_email(mapper, connection, target):
    if target.primary_email:
        target.primary_email = target.primary_email.lower().strip()
    if target.secondary_email:
        target.secondary_email = target.secondary_email.lower().strip()
