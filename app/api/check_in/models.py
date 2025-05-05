from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String

from app.core.database import Base
from app.core.utils import current_time


class CheckIn(Base):
    __tablename__ = 'check_ins'

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        unique=True,
        index=True,
    )
    code = Column(String, nullable=False)
    attendee_id = Column(
        Integer,
        ForeignKey('attendees.id'),
        nullable=False,
        unique=True,
    )
    arrival_date = Column(DateTime, nullable=True)
    departure_date = Column(DateTime, nullable=True)
    virtual_check_in = Column(Boolean, nullable=False)
    virtual_check_in_timestamp = Column(DateTime, nullable=True)
    qr_check_in = Column(Boolean, nullable=False)
    qr_scan_timestamp = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=current_time)
    updated_at = Column(DateTime, default=current_time, onupdate=current_time)
