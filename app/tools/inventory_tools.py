from app.core.tool_registry import registry
from app.services import business
from app import crud
from sqlalchemy.orm import Session
from datetime import datetime
from app.core.config import m


@registry.register(
    name="record_new_item",
    description="【录入/归位】当用户购买新物品、整理物品、或告知物品位置时使用。",
    parameters={
        "type": "object",
        "properties": {
            "user_text": {"type": "string", "description": "用户的原始指令文本"}
        },
        "required": ["user_text"],
    },
)
def tool_record(user_text: str, db: Session, **kwargs):
    # 调用业务层
    print(f"工具收到录入请求: {user_text}")
    return business.logic_add_item(text=user_text, db=db)


@registry.register(
    name="consume_item",
    description="【消耗/使用】当用户说用了、喝了、吃掉了、扔掉了某个物品时使用。用于减少库存。",
    parameters={
        "type": "object",
        "properties": {
            "item_name": {"type": "string", "description": "物品名称"},
            "quantity": {"type": "number", "description": "消耗的数量 (默认为1)"},
        },
        "required": ["item_name"],
    },
)
def tool_consume(item_name: str, db: Session, quantity: float = 1, **kwargs):
    """
    消耗物品工具
    1. 调用数据库扣减库存
    2. 在 Mem0 记录行为日志
    """
    print(f"🔧 正在执行消耗: {item_name} - {quantity}")

    # 1. 执行数据库扣减
    result = crud.reduce_inventory(db, item_name, quantity)

    # 2. 记录到 Mem0 (行为日志)
    # 这条记录不关联 item_id，只作为一条"事情发生了"的流水账
    # 这样以后问"我什么时候喝了可乐"，Mem0 能搜到
    if result["status"] in ["success", "warning"]:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_text = f"[{timestamp}] 消耗记录: 用了 {quantity} 个 {item_name}"

        m.add(
            log_text,
            user_id="user_1",
            metadata={"type": "consumption", "item_name": item_name},
        )

    return result


# app/tools/inventory_tools.py (追加)


@registry.register(
    name="update_item_location",
    description="【修正/移动】当用户想要修改已有物品的位置，或者补充说明刚才物品的位置时使用。例如：'把它放冰箱'、'移到书房'。",
    parameters={
        "type": "object",
        "properties": {
            "item_name": {
                "type": "string",
                "description": "物品名称 (如果用户说'它'，请根据对话历史推断名字)",
            },
            "new_location": {"type": "string", "description": "新的位置名称"},
        },
        "required": ["item_name", "new_location"],
    },
)
def tool_update_location(item_name: str, new_location: str, db: Session, **kwargs):
    print(f"🔧 移动物品: {item_name} -> {new_location}")
    return crud.update_recent_item_location(db, item_name, new_location)
