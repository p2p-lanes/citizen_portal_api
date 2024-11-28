from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import text

from app.core.database import Base


class PopUpCity(Base):
    __tablename__ = 'popups'

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text('uuid_generate_v4()'),
        unique=True,
        index=True,
    )
    name = Column(String, index=True, nullable=False)
    tagline = Column(String)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
