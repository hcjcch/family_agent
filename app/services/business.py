from sqlalchemy.orm import Session
from app import crud, schemas, models
from app.core.config import m
from app.services import llm_service
from datetime import datetime
import uuid


def logic_add_item(text: str, db: Session):
    """
    智能录入逻辑：
    - 如果能识别物品 -> 存库存 (MySQL) + 存记忆 (Mem0)
    - 如果不能识别 -> 只存记忆 (Mem0)
    """
    print(f"收到录入请求: {text}")

    # 1. 尝试让 LLM 提取信息
    extracted_json = llm_service.extract_item_info(text)
    print(f"LLM 提取结果: {extracted_json}")

    # 准备 Mem0 需要的 Metadata
    metadata = {"pure_text": text, "timestamp": str(datetime.now())}

    # 返回结果
    response_data = {
        "status": "success",
        "mode": "memory_only",  # 默认为纯记忆模式
        "ai_extraction": extracted_json,
    }

    # 判断标准：LLM 提取出了 JSON，并且里面有有效的 'name'
    if extracted_json and extracted_json.get("name"):
        # 进入库存模式
        response_data["mode"] = "inventory_mode"

        # A1. 处理位置
        loc_name = extracted_json.get("location") or "未分类区域"
        location_obj = crud.get_or_create_location_by_name(db, loc_name)

        # A2. 写入 MySQL
        try:
            item_data = schemas.ItemCreate(
                name=extracted_json["name"],
                category=extracted_json.get("category"),
                quantity=extracted_json.get("quantity", 1),
                unit=extracted_json.get("unit", "个"),
                location_id=location_obj.id,
                image_url=None,
            )
            inventory_rec = crud.create_item_with_inventory(db, item_data)

            # A3. 关键步骤：把生成的 item_id 放进 Metadata
            metadata["item_id"] = inventory_rec.item_id

            response_data["db_record"] = {
                "item": inventory_rec.item.name,
                "location": location_obj.name,
                "quantity": inventory_rec.quantity,
            }
        except Exception as e:
            print(f"⚠️ 写入库存失败，降级为纯记忆存储: {e}")
            # 如果数据库写入失败，不应该报错给用户，而是降级存入 Mem0
            response_data["warning"] = f"库存写入失败: {str(e)}"

    else:
        # 进入纯记忆模式
        print("未识别出具体物品，仅作为笔记存储")
        metadata["type"] = "note"  # 标记为笔记类型

    # 统一写入 Mem0
    # 无论是否提取出物品，这句话本身都是有价值的记忆
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    memory_text = f"[{current_time}] {text}"

    m.add(memory_text, user_id="user_1", metadata=metadata)

    return response_data


def logic_search_item(query: str, db: Session):
    """
    智能搜索逻辑：
    1. 先在 Mem0 中语义搜索
    2. 提取所有相关的 item_id
    3. 查 MySQL 获取库存详情
    """
    # 1. 问 Mem0
    memories = m.search(query, user_id="user_1", limit=5)

    # 调试输出
    print(f"🔍 DEBUG - Mem0 search {query} 返回类型: {type(memories)}")
    print(f"🔍 DEBUG - Mem0 search {query} 返回内容: {memories}")

    # 2. 提取所有相关的 item_id，并去重
    # 我们只关心搜到了哪些"物品"，不关心具体是哪条"记忆"触发的
    found_item_ids = set()

    # 检查 memories 的结构
    if isinstance(memories, dict):
        # 如果返回的是字典，检查是否有 results 键
        if "results" in memories:
            memory_list = memories["results"]
        else:
            memory_list = [memories]
    elif isinstance(memories, list):
        memory_list = memories
    else:
        memory_list = []

    for mem in memory_list:
        print(f"🔍 DEBUG - 处理记忆项: {mem}")
        if isinstance(mem, dict):
            meta = mem.get("metadata", {})
            print(f"🔍 DEBUG - 元数据: {meta}")
            if meta and "item_id" in meta:
                found_item_ids.add(meta["item_id"])
                print(f"🔍 DEBUG - 找到 item_id: {meta['item_id']}")

    print(f"🔍 搜索 '{query}' 关联到的物品IDs: {found_item_ids}")

    final_results = []

    # 3. 遍历每个找到的物品，查它的全量库存
    for item_id in found_item_ids:
        # 先查物品基本信息 (名字)
        item_obj = db.query(models.Item).filter(models.Item.id == item_id).first()
        if not item_obj:
            continue

        # 再查它在所有位置的分布
        inv_list = crud.get_item_all_inventories(db, item_id)

        # 构造聚合后的结果
        # 格式： 苹果 -> [冰箱: 5个, 厨房: 3个]
        locations_detail = []
        total_qty = 0

        for inv in inv_list:
            qty = float(inv.quantity)
            total_qty += qty
            locations_detail.append(
                {"location": inv.location_name, "quantity": qty, "unit": inv.unit}
            )

        final_results.append(
            {
                "item_name": item_obj.name,
                "total_quantity": total_qty,
                "locations": locations_detail,  # 这是一个列表
                "match_score": 0.9,  # 这里可以简化，或者取 Mem0 的最高分
            }
        )

    return {"results": final_results}
