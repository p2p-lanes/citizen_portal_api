from sqlalchemy import Boolean, Column, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import text

from app.core.database import Base


class Citizen(Base):
    __tablename__ = 'citizens'

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text('uuid_generate_v4()'),
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
