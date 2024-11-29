from sqlalchemy import Boolean, Column, Date, ForeignKey, String
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import text

from app.core.database import Base


class Application(Base):
    __tablename__ = 'applications'

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text('uuid_generate_v4()'),
        unique=True,
        index=True,
    )
    first_name = Column(String, index=True, nullable=False)
    last_name = Column(String, index=True, nullable=False)
    email = Column(String, index=True, nullable=False)
    telegram = Column(String)
    organization = Column(String)
    role = Column(String)
    gender = Column(String, nullable=True)
    age = Column(String, nullable=True)
    social_media = Column(String)
    residence = Column(String)
    eth_address = Column(String)

    duration = Column(String)
    check_in = Column(Date, nullable=True)
    check_out = Column(Date, nullable=True)

    builder_boolean = Column(Boolean)
    builder_description = Column(String)

    hackathon_interest = Column(Boolean)
    gitcoin_oss = Column(Boolean)
    draft_and_demos = Column(Boolean)
    host_session = Column(String)
    personal_goals = Column(String)
    referral = Column(String)
    info_to_share = Column(ARRAY(String), nullable=True)

    investor = Column(Boolean)
    success_definition = Column(ARRAY(String), nullable=True)
    top_tracks = Column(ARRAY(String), nullable=True)

    # Family information
    brings_spouse = Column(Boolean)
    spouse_info = Column(String)
    spouse_email = Column(String)
    brings_kids = Column(Boolean)
    kids_info = Column(String)

    # Scholarship information
    scolarship_request = Column(Boolean)
    scolarship_categories = Column(ARRAY(String), nullable=True)
    scolarship_details = Column(String)

    status = Column(String)

    citizen_id = Column(UUID(as_uuid=True), ForeignKey('citizens.id'), nullable=False)
    citizen = relationship('Citizen', back_populates='applications', lazy='noload')
    popup_city_id = Column(UUID(as_uuid=True), ForeignKey('popups.id'), nullable=False)
    popup_city = relationship('PopUpCity', lazy='noload')

    __mapper_args__ = {'exclude_properties': ['citizen', 'popup_city']}
