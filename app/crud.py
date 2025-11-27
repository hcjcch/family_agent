# app/crud.py
from sqlalchemy.orm import Session
from . import models, schemas


# --- Location 操作 ---
def get_locations(db: Session, user_id: int = 1, skip: int = 0, limit: int = 100):
    return (
        db.query(models.Location)
        .filter(models.Location.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_location(db: Session, location: schemas.LocationCreate, user_id: int = 1):
    db_location = models.Location(**location.dict(), user_id=user_id)
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    return db_location


# --- Item & Inventory 操作 (核心) ---
def create_item_with_inventory(
    db: Session, item_in: schemas.ItemCreate, user_id: int = 1
):
    # 1. 检查物品是否已存在 (根据名称)
    db_item = (
        db.query(models.Item)
        .filter(models.Item.name == item_in.name, models.Item.user_id == user_id)
        .first()
    )

    # 2. 如果不存在，创建新物品
    if not db_item:
        db_item = models.Item(
            name=item_in.name,
            category=item_in.category,
            image_url=item_in.image_url,
            user_id=user_id,
        )
        db.add(db_item)
        db.commit()
        db.refresh(db_item)

    # 3. 创建或更新库存记录
    # 检查该物品在指定位置是否已有库存
    db_inventory = (
        db.query(models.Inventory)
        .filter(
            models.Inventory.item_id == db_item.id,
            models.Inventory.location_id == item_in.location_id,
        )
        .first()
    )

    if db_inventory:
        # 如果有，增加数量
        db_inventory.quantity += item_in.quantity
        # 更新单位（以最新的为准，可选）
        if item_in.unit:
            db_inventory.unit = item_in.unit
    else:
        # 如果没有，创建新库存记录
        db_inventory = models.Inventory(
            item_id=db_item.id,
            location_id=item_in.location_id,
            quantity=item_in.quantity,
            unit=item_in.unit,
        )
        db.add(db_inventory)

    db.commit()
    db.refresh(db_inventory)
    return db_inventory
