from sqlalchemy.orm import Session
from . import models, schemas
from decimal import Decimal


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
        db_inventory.quantity += Decimal(str(item_in.quantity))
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


# app/crud.py (追加)


def get_or_create_location_by_name(db: Session, name: str, user_id: int = 1):
    """
    根据名字找位置 ID，找不到就自动新建
    """
    # 1. 尝试查找
    loc = (
        db.query(models.Location)
        .filter(models.Location.name == name, models.Location.user_id == user_id)
        .first()
    )

    # 2. 找到直接返回
    if loc:
        return loc

    # 3. 没找到，自动创建
    new_loc = models.Location(name=name, user_id=user_id)
    db.add(new_loc)
    db.commit()
    db.refresh(new_loc)
    return new_loc


# app/crud.py (追加)


def get_location_tree(db: Session, user_id: int = 1):
    # 1. 取出该用户所有位置
    all_locs = (
        db.query(models.Location).filter(models.Location.user_id == user_id).all()
    )

    # 2. 构建 ID 到 Node 的映射字典
    # 我们用 schemas.LocationNode 来包装数据，方便最后返回
    nodes = {}
    for loc in all_locs:
        nodes[loc.id] = schemas.LocationNode(id=loc.id, name=loc.name, children=[])

    # 3. 组装树结构
    roots = []
    for loc in all_locs:
        node = nodes[loc.id]
        if loc.parent_id is None:
            # 没有父级，说明是根节点
            roots.append(node)
        else:
            # 有父级，把自己挂到父级的 children 里
            if loc.parent_id in nodes:
                parent = nodes[loc.parent_id]
                parent.children.append(node)

    return roots


def get_item_details(db: Session, item_id: int):
    """
    联表查询：获取物品详情 + 库存 + 位置名称
    """
    result = (
        db.query(
            models.Item.name,
            models.Item.image_url,
            models.Inventory.quantity,
            models.Inventory.unit,
            models.Location.name.label("location_name"),
            models.Location.path,
        )
        .join(models.Inventory, models.Inventory.item_id == models.Item.id)
        .join(models.Location, models.Inventory.location_id == models.Location.id)
        .filter(models.Item.id == item_id)
        .first()
    )
    return result


# app/crud.py


def get_item_all_inventories(db: Session, item_id: int):
    """
    查询某物品在所有位置的库存分布
    返回：List of (quantity, unit, location_name, path)
    """
    results = (
        db.query(
            models.Inventory.quantity,
            models.Inventory.unit,
            models.Location.name.label("location_name"),
            models.Location.path,
        )
        .join(models.Location, models.Inventory.location_id == models.Location.id)
        .filter(models.Inventory.item_id == item_id)
        .all()
    )  # ✅ 改为 .all()，获取所有记录

    return results


def get_all_inventory_details(db: Session):
    """
    [报表] 获取所有库存明细
    """
    # 联表查询: Item + Inventory + Location
    results = (
        db.query(
            models.Item.name,
            models.Item.category,
            models.Inventory.quantity,
            models.Inventory.unit,
            models.Location.name.label("location_name"),
        )
        .join(models.Inventory, models.Inventory.item_id == models.Item.id)
        .join(models.Location, models.Inventory.location_id == models.Location.id)
        .order_by(models.Item.category, models.Item.name)  # 按分类和名字排序，好看点
        .all()
    )

    # 转成字典列表
    data = []
    for row in results:
        data.append(
            {
                "item": row.name,
                "cat": row.category or "杂项",
                "qty": float(row.quantity),
                "unit": row.unit,
                "loc": row.location_name,
            }
        )
    return data


# 减少库存
def reduce_inventory(db: Session, item_name: str, quantity: float, user_id: int = 1):
    """
    [核心逻辑] 消耗物品
    策略：自动查找该物品的所有库存，优先扣减数量多的位置 (避免产生大量碎片库存)
    """
    # 1. 查找该物品的所有库存记录
    # 联表查询：Inventory + Item
    records = (
        db.query(models.Inventory)
        .join(models.Item, models.Inventory.item_id == models.Item.id)
        .filter(models.Item.name == item_name, models.Item.user_id == user_id)
        .order_by(models.Inventory.quantity.desc())  # 降序排列，先用多的
        .all()
    )

    if not records:
        return {"status": "error", "message": f"家里找不到'{item_name}'，无法消耗。"}

    # 准备计算
    needed = Decimal(str(quantity))
    total_deducted = Decimal("0")
    logs = []

    # 2. 开始循环扣减
    for inv in records:
        if needed <= 0:
            break

        current_qty = inv.quantity

        if current_qty >= needed:
            # A. 当前位置够扣
            inv.quantity -= needed
            total_deducted += needed
            logs.append(f"从位置(ID:{inv.location_id}) 扣除 {needed}")
            needed = Decimal("0")  # 扣完了
        else:
            # B. 当前位置不够，全部扣光，继续下一个
            deducted = current_qty
            inv.quantity = Decimal("0")
            total_deducted += deducted
            needed -= deducted
            logs.append(f"位置(ID:{inv.location_id}) 已用光({deducted})")

    # 3. 提交事务
    db.commit()

    # 4. 生成返回消息
    if needed > 0:
        return {
            "status": "warning",
            "message": f"库存不足！只扣减了 {total_deducted}，还缺 {needed}。",
            "details": logs,
        }
    else:
        return {
            "status": "success",
            "message": f"成功消耗 {total_deducted} 个 {item_name}。",
            "details": logs,
        }
