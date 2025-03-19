from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, event

from app.core.database import Base, SessionLocal
from app.core.utils import current_time


class EmailLog(Base):
    __tablename__ = 'email_logs'

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        unique=True,
        index=True,
    )
    receiver_email = Column(String, nullable=False, index=True)
    event = Column(String, nullable=False)
    template = Column(String, nullable=False)
    params = Column(String)  # JSON string of parameters
    status = Column(String)  # success, failed, scheduled, canceled
    send_at = Column(DateTime, nullable=True)
    error_message = Column(String, nullable=True)
    entity_type = Column(String, nullable=True)
    entity_id = Column(Integer, nullable=True)

    citizen_id = Column(Integer, ForeignKey('humans.id'), index=True)
    popup_city_id = Column(Integer, ForeignKey('popups.id'), nullable=True)

    created_at = Column(DateTime, default=current_time)
    updated_at = Column(DateTime, default=current_time, onupdate=current_time)
    created_by = Column(String)
    updated_by = Column(String)


@event.listens_for(EmailLog, 'before_insert')
def set_citizen_id(mapper, connection, target):
    if target.citizen_id or not target.receiver_email:
        return

    session = SessionLocal.object_session(target)
    if not session:
        return

    from app.api.citizens.models import Citizen

    citizen = (
        session.query(Citizen)
        .filter(Citizen.primary_email == target.receiver_email)
        .first()
    )

    if citizen:
        target.citizen_id = citizen.id
