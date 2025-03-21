from sqlalchemy import Column, DateTime, Integer, String

from app.core.database import Base
from app.core.utils import current_time


class Organization(Base):
    __tablename__ = 'organizations'

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        unique=True,
        index=True,
    )
    name = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=current_time)
    updated_at = Column(DateTime, default=current_time, onupdate=current_time)
    created_by = Column(String)
    updated_by = Column(String)
