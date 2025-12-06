# app/tools/report_tools.py

from app.core.tool_registry import registry
from app import crud
from sqlalchemy.orm import Session


@registry.register(
    name="get_full_inventory_list",
    description="当用户想要列出家里【所有】物品的详细清单、盘点所有东西时使用。不要用于搜索单个物品。",
    parameters={"type": "object", "properties": {}},  # 无参数工具
)
def tool_full_list(db: Session, **kwargs):
    """
    获取全量库存清单
    """
    items = crud.get_all_inventory_details(db)

    # 为了防止 Token 爆炸（如果家里有1000个东西，全发给 LLM 会太长），
    # 我们可以做个简单的截断或者摘要。
    # 但对于 V1 MVP，先全量发过去。

    if not items:
        return "家里目前空空如也，还没有录入任何物品。"

    return {"summary": f"共找到 {len(items)} 条库存记录", "details": items}
