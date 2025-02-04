from typing import TYPE_CHECKING, List

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, relationship

from app.core.database import Base
from app.core.utils import current_time

if TYPE_CHECKING:
    from app.api.citizens.models import Citizen
    from app.api.products.models import Product


class GroupLeader(Base):
    __tablename__ = 'group_leaders'

    citizen_id = Column(Integer, ForeignKey('citizens.id'), primary_key=True)
    group_id = Column(Integer, ForeignKey('groups.id'), primary_key=True)


class GroupMembers(Base):
    __tablename__ = 'group_members'

    citizen_id = Column(Integer, ForeignKey('citizens.id'), primary_key=True)
    group_id = Column(Integer, ForeignKey('groups.id'), primary_key=True)


class GroupProducts(Base):
    __tablename__ = 'group_products'

    group_id = Column(Integer, ForeignKey('groups.id'), primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), primary_key=True)


class Group(Base):
    __tablename__ = 'groups'

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        unique=True,
        index=True,
    )
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    discount_percentage = Column(Float, nullable=False)
    popup_city_id = Column(Integer, ForeignKey('popups.id'), index=True, nullable=False)
    max_members = Column(Integer, nullable=False)

    created_at = Column(DateTime, default=current_time)
    updated_at = Column(DateTime, default=current_time, onupdate=current_time)
    created_by = Column(String)
    updated_by = Column(String)

    leaders: Mapped[List['Citizen']] = relationship(
        'Citizen', secondary='group_leaders', backref='led_groups'
    )
    members: Mapped[List['Citizen']] = relationship(
        'Citizen', secondary='group_members', backref='groups'
    )
    products: Mapped[List['Product']] = relationship(
        'Product', secondary='group_products', backref='groups'
    )

    def is_leader(self, citizen_id: int) -> bool:
        return any(leader.id == citizen_id for leader in self.leaders)
