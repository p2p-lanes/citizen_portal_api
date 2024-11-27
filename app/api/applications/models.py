from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import text

from app.core.database import Base


class Application(Base):
    __tablename__ = 'applications'

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text('uuid_generate_v4()'),
        unique=True,
        index=True,
    )
    first_name = Column(String, index=True, nullable=False)
    last_name = Column(String, index=True, nullable=False)
    email = Column(String, index=True, nullable=False)
    telegram_username = Column(String)
    organization = Column(String)
    role = Column(String)
    gender = Column(String)
    age = Column(String)
    citizen_id = Column(UUID(as_uuid=True), ForeignKey('citizens.id'), nullable=True)
    citizen = relationship('Citizen', back_populates='applications', lazy='noload')

    __mapper_args__ = {'exclude_properties': ['citizen']}
