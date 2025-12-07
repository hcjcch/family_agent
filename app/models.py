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


# app/models.py (追加)

# 为了支持 UUID 和 Enum，需要额外引入
import uuid
from sqlalchemy.dialects.mysql import LONGTEXT


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, nullable=False, default=1)
    title = Column(String(100), nullable=True)
    summary = Column(Text, nullable=True)  # 长期记忆的压缩摘要
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    is_active = Column(Integer, default=1)  # 1=活跃, 0=归档

    # 关系：一个会话有多条消息
    messages = relationship(
        "ChatMessage", back_populates="session", order_by="ChatMessage.created_at"
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant, system, tool
    content = Column(
        LONGTEXT, nullable=True
    )  # 内容可能很长，如果是工具调用可能包含 JSON
    tool_call_id = Column(String(100), nullable=True)  # 专门存 OpenAI 的 tool_call_id
    token_count = Column(Integer, default=0)  # 预留，未来做精细化控制
    created_at = Column(DateTime, server_default=func.now())

    session = relationship("Session", back_populates="messages")
