from typing import TYPE_CHECKING, Optional

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
from app.core.utils import current_time

if TYPE_CHECKING:
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
    point_of_contact = Column(String)
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
    applications = relationship('Application', back_populates='citizen')

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

    __table_args__ = (
        Index(
            'ix_humans_primary_email_unique',
            primary_email,
            unique=True,
            postgresql_where=(primary_email is not None),
        ),
        Index('ix_humans_organization_id', 'organization_id'),
    )


@event.listens_for(Citizen, 'before_insert')
def clean_email(mapper, connection, target):
    if target.primary_email:
        target.primary_email = target.primary_email.lower().strip()
    if target.secondary_email:
        target.secondary_email = target.secondary_email.lower().strip()
