from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.types import Text

from app.core.database import Base

if TYPE_CHECKING:
    from app.api.products.models import Product


class ApplicationProduct(Base):
    __tablename__ = 'application_products'

    application_id = Column(Integer, ForeignKey('applications.id'), primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), primary_key=True)
    attendee_id = Column(Integer, ForeignKey('attendees.id'))
    quantity = Column(Integer, default=1)

    application = relationship('Application', back_populates='application_products')
    product = relationship('Product', back_populates='application_products')


class Application(Base):
    __tablename__ = 'applications'

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
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
    local_resident = Column(Boolean)
    eth_address = Column(String)
    duration = Column(String)
    video_url = Column(String)

    hackathon_interest = Column(Boolean)
    host_session = Column(String)
    personal_goals = Column(String)
    referral = Column(String)
    info_not_shared = Column(ARRAY(String), nullable=True)
    investor = Column(Boolean)

    # Family information
    brings_spouse = Column(Boolean)
    spouse_info = Column(String)
    spouse_email = Column(String)
    brings_kids = Column(Boolean)
    kids_info = Column(String)

    # Builder information
    builder_boolean = Column(Boolean)
    builder_description = Column(String)

    # Scholarship information
    scolarship_request = Column(Boolean)
    scolarship_details = Column(String)
    scolarship_video_url = Column(String)

    sent_mails = Column(Text, nullable=True)

    status = Column(String)
    ticket_category = Column(String)  # builder, scolarship, standard

    payments = relationship('Payment', back_populates='application')
    attendees = relationship('Attendee', back_populates='application')
    products: Mapped[List['Product']] = relationship(
        'Product',
        secondary='application_products',
        back_populates='applications',
        viewonly=True,
    )
    application_products = relationship(
        'ApplicationProduct', back_populates='application'
    )

    citizen_id = Column(Integer, ForeignKey('citizens.id'), nullable=False)
    citizen = relationship('Citizen', back_populates='applications', lazy='noload')
    popup_city_id = Column(Integer, ForeignKey('popups.id'), nullable=False)
    popup_city = relationship('PopUpCity', lazy='noload')

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String)
    updated_by = Column(String)

    __mapper_args__ = {'exclude_properties': ['citizen', 'popup_city']}
