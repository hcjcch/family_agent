# app/models.py
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    DECIMAL,
    DateTime,
    func,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from .database import Base


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, default=1)  # 暂时默认用户ID为1
    name = Column(String(255), nullable=False)
    category = Column(String(100))
    image_url = Column(String(500))
    created_at = Column(DateTime, server_default=func.now())

    # 关系：一个物品可以有多个库存记录
    inventory_records = relationship("Inventory", back_populates="item")

    # 约束：同一个用户下物品名唯一
    __table_args__ = (UniqueConstraint("user_id", "name", name="uix_user_item_name"),)


class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, default=1)
    name = Column(String(255), nullable=False)
    parent_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    path = Column(String(1000))  # 例如 "/1/5"
    created_at = Column(DateTime, server_default=func.now())

    # 关系：自关联 (子位置)
    children = relationship("Location", backref="parent", remote_side=[id])
    inventory_records = relationship("Inventory", back_populates="location")


class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    quantity = Column(DECIMAL(10, 2), nullable=False, default=1.00)
    unit = Column(String(50), default="个")
    expiry_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关系
    item = relationship("Item", back_populates="inventory_records")
    location = relationship("Location", back_populates="inventory_records")

    __table_args__ = (
        UniqueConstraint("item_id", "location_id", name="uix_item_location"),
    )
