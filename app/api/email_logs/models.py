from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy import event
from app.core.database import Base
from app.core.database import SessionLocal


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
    template = Column(String, nullable=False)
    params = Column(String)  # JSON string of parameters
    status = Column(String)  # success, failed
    error_message = Column(String, nullable=True)

    citizen_id = Column(Integer, ForeignKey('citizens.id'), index=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
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
