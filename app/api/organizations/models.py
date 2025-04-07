from typing import TYPE_CHECKING, List

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import Mapped, relationship

from app.core.database import Base
from app.core.utils import current_time

if TYPE_CHECKING:
    from app.api.citizens.models import Citizen


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

    citizens: Mapped[List['Citizen']] = relationship(
        'Citizen',
        secondary='citizen_organizations',
        back_populates='organizations',
    )

    created_at = Column(DateTime, default=current_time)
    updated_at = Column(DateTime, default=current_time, onupdate=current_time)
    created_by = Column(String)
    updated_by = Column(String)
