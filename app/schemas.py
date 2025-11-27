# app/schemas.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


# --- Location Schemas ---
class LocationBase(BaseModel):
    name: str
    parent_id: Optional[int] = None


class LocationCreate(LocationBase):
    pass


class Location(LocationBase):
    id: int
    user_id: int
    path: Optional[str] = None
    created_at: datetime

    class Config:
        orm_mode = True  # 允许从 ORM 对象读取数据


# --- Item Schemas ---
class ItemBase(BaseModel):
    name: str
    category: Optional[str] = None
    image_url: Optional[str] = None


class ItemCreate(ItemBase):
    # 录入物品时，通常也会指定位置和数量
    location_id: int
    quantity: float
    unit: Optional[str] = "个"


class Item(ItemBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        orm_mode = True


# --- Inventory Schemas ---
class Inventory(BaseModel):
    id: int
    item: Item
    location: Location
    quantity: float
    unit: str

    class Config:
        orm_mode = True
