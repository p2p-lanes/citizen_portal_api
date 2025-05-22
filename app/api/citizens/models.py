from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
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

# Association table for citizen-organization many-to-many relationship
citizen_organizations = Table(
    'citizen_organizations',
    Base.metadata,
    Column('citizen_id', Integer, ForeignKey('humans.id'), primary_key=True),
    Column(
        'organization_id', Integer, ForeignKey('organizations.id'), primary_key=True
    ),
    Column('created_at', DateTime, default=current_time),
)


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
    age = Column(String)
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

    # Replace the single organization relationship with many-to-many
    organizations: Mapped[List['Organization']] = relationship(
        'Organization',
        secondary=citizen_organizations,
        back_populates='citizens',
    )

    created_at = Column(DateTime, default=current_time)
    updated_at = Column(DateTime, default=current_time, onupdate=current_time)
    created_by = Column(String)
    updated_by = Column(String)

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
