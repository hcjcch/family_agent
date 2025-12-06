from app.core.tool_registry import registry
from app.services import business
from app import crud
from sqlalchemy.orm import Session


@registry.register(
    name="search_item",
    description="【搜索/寻找】当用户问某东西在哪、有多少时使用。",
    parameters={
        "type": "object",
        "properties": {"query": {"type": "string", "description": "搜索关键词"}},
        "required": ["query"],
    },
)
def tool_search(query: str, db: Session, **kwargs):
    return business.logic_search_item(query=query, db=db)


# @registry.register(
#     name="get_inventory_report",
#     description="【全局报表】当用户想看全家库存汇总、各分类统计时使用。",
#     parameters={"type": "object", "properties": {}},
# )
# def tool_report(db: Session, **kwargs):
#     return crud.get_inventory_summary(db)
