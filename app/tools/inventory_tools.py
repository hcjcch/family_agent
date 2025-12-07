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
