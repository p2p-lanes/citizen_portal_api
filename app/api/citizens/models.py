from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    event,
)
from sqlalchemy.orm import Mapped, relationship

from app.core.database import Base
from app.core.security import Token, create_access_token
from app.core.utils import current_time

if TYPE_CHECKING:
    from app.api.applications.models import Application
    from app.api.groups.models import Group
    from app.api.organizations.models import Organization


class Citizen(Base):
    __tablename__ = 'humans'

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        unique=True,
        index=True,
    )
    primary_email = Column(String, index=True, nullable=True)
    secondary_email = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    x_user = Column(String)
    telegram = Column(String)
    organization = Column(String)
    role = Column(String)
    residence = Column(String)
    social_media = Column(String)
    age = Column(Integer)
    gender = Column(String)
    eth_address = Column(String)
    referral = Column(String)

    email_validated = Column(Boolean, default=False)
    spice = Column(String)
    code = Column(Integer)
    code_expiration = Column(DateTime)

    applications: Mapped[List['Application']] = relationship(
        'Application', back_populates='citizen'
    )
    groups_as_member: Mapped[List['Group']] = relationship(
        'Group', secondary='group_members', back_populates='members'
    )

    organization_id = Column(
        Integer, ForeignKey('organizations.id'), nullable=True, index=True
    )
    organization_rel: Mapped[Optional['Organization']] = relationship(
        'Organization', lazy='joined'
    )

    created_at = Column(DateTime, default=current_time)
    updated_at = Column(DateTime, default=current_time, onupdate=current_time)
    created_by = Column(String)
    updated_by = Column(String)

    def get_group(self, popup_city_id: int) -> Optional['Group']:
        for group in self.groups_as_member:
            if group.popup_city_id == popup_city_id:
                return group
        return None

    def get_application(self, popup_city_id: int) -> Optional['Application']:
        for application in self.applications:
            if application.popup_city_id == popup_city_id:
                return application
        return None

    def get_authorization(self) -> Token:
        data = {'citizen_id': self.id, 'email': self.primary_email}
        return Token(
            access_token=create_access_token(data=data),
            token_type='Bearer',
        )

    __table_args__ = (
        Index(
            'ix_humans_primary_email_unique',
            primary_email,
            unique=True,
            postgresql_where=(primary_email is not None),
        ),
    )


@event.listens_for(Citizen, 'before_insert')
def clean_email(mapper, connection, target):
    if target.primary_email:
        target.primary_email = target.primary_email.lower().strip()
    if target.secondary_email:
        target.secondary_email = target.secondary_email.lower().strip()
