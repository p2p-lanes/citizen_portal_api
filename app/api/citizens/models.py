from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Column, DateTime, Integer, String, event
from sqlalchemy.orm import Mapped, relationship

if TYPE_CHECKING:
    from app.api.applications.models import Application
    from app.api.groups.models import Group

from app.core.database import Base
from app.core.utils import current_time


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
    applications: Mapped[List['Application']] = relationship(
        'Application', back_populates='citizen'
    )
    groups: Mapped[List['Group']] = relationship(
        'Group', secondary='group_members', back_populates='members'
    )

    created_at = Column(DateTime, default=current_time)
    updated_at = Column(DateTime, default=current_time, onupdate=current_time)
    created_by = Column(String)
    updated_by = Column(String)

    def get_group(self, popup_city_id: int) -> Optional['Group']:
        for group in self.groups:
            if group.popup_city_id == popup_city_id:
                return group
        return None


@event.listens_for(Citizen, 'before_insert')
def clean_email(mapper, connection, target):
    if target.primary_email:
        target.primary_email = target.primary_email.lower().strip()
    if target.secondary_email:
        target.secondary_email = target.secondary_email.lower().strip()
