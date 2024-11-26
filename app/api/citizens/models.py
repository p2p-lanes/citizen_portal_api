from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
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
    email = Column(String, index=True, unique=True, nullable=False)
    first_name = Column(String, index=True)
    last_name = Column(String, index=True)
