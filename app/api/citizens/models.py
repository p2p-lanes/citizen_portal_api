from sqlalchemy import Boolean, Column, DateTime, Index, Integer, String, event
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.core.utils import current_time


class Citizen(Base):
    __tablename__ = "citizens"

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

    email_validated = Column(Boolean, default=False)
    spice = Column(String)
    applications = relationship("Application", back_populates="citizen")

    created_at = Column(DateTime, default=current_time)
    updated_at = Column(DateTime, default=current_time, onupdate=current_time)
    created_by = Column(String)
    updated_by = Column(String)

    __table_args__ = (
        Index(
            "ix_citizens_primary_email_unique",
            primary_email,
            unique=True,
            postgresql_where=(primary_email is not None),
        ),
    )


@event.listens_for(Citizen, "before_insert")
def clean_email(mapper, connection, target):
    if target.primary_email:
        target.primary_email = target.primary_email.lower().strip()
    if target.secondary_email:
        target.secondary_email = target.secondary_email.lower().strip()
