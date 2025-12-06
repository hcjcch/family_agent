from app.core.tool_registry import registry
from app.services import business
from app import crud
from sqlalchemy.orm import Session


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


# @registry.register(
#     name="consume_item",x
#     description="【消耗/使用】当用户说用了、喝了、吃掉了某个物品时使用。",
#     parameters={
#         "type": "object",
#         "properties": {
#             "item_name": {"type": "string", "description": "物品名称"},
#             "quantity": {"type": "number", "description": "消耗的数量"},
#         },
#         "required": ["item_name"],
#     },
# )
# def tool_consume(item_name: str, quantity: float, db: Session, **kwargs):
#     # 假设 crud 里有 reduce_inventory
#     return crud.reduce_inventory(db, item_name, quantity)
