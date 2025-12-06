# app/main.py
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from . import models, database, schemas, crud
from datetime import datetime
import app.tools

# app/main.py
from fastapi.middleware.cors import CORSMiddleware

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="AI Family Butler")

# 👇 新增：允许所有来源访问 (开发环境方便)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许任何来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "System is running"}


# --- Location APIs ---
@app.post("/locations/", response_model=schemas.Location)
def create_location(
    location: schemas.LocationCreate, db: Session = Depends(database.get_db)
):
    return crud.create_location(db=db, location=location)


@app.get("/locations/", response_model=List[schemas.Location])
def read_locations(
    skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)
):
    locations = crud.get_locations(db, skip=skip, limit=limit)
    return locations


@app.get("/locations/tree", response_model=List[schemas.LocationNode])
def get_locations_tree(db: Session = Depends(database.get_db)):
    """
    获取树状的位置结构，适合前端级联选择器使用
    """
    return crud.get_location_tree(db)


# --- Item APIs (录入) ---
@app.post("/items/add", response_model=schemas.Inventory)
def add_item(item: schemas.ItemCreate, db: Session = Depends(database.get_db)):
    # 这里实现了：自动判断物品是否存在 -> 自动更新库存
    return crud.create_item_with_inventory(db=db, item_in=item)


from pydantic import BaseModel
from typing import Optional

# 引入我们刚刚写好的 Mem0 实例
from app.core.config import m


# 定义输入数据格式
class MemoryInput(BaseModel):
    text: str  # 用户说的自然语言，例如 "我买了箱牛奶放阳台了"


# --- 新增接口 1: 语义录入 ---
@app.post("/memories/add")
def add_memory(input: MemoryInput):
    """
    接收自然语言，将其存入向量数据库 (联想大脑)
    """
    # user_id 暂时写死，未来可以从登录信息获取
    m.add(input.text, user_id="user_1")
    return {"status": "success", "message": "Memory stored successfully"}


# --- 新增接口 2: 语义搜索 ---
@app.get("/memories/search")
def search_memory(query: str):
    """
    语义搜索：输入 "喝的"，能找到 "牛奶"
    """
    # limit=3 表示返回最相关的3条
    memories = m.search(query, user_id="user_1", limit=3)
    return {"results": memories}


# app/main.py

# 引入新写的服务
from app.services import llm_service


class OnlyTextInput(BaseModel):
    text: str


@app.post("/memories/auto_add")
def auto_add_memory(input: OnlyTextInput, db: Session = Depends(database.get_db)):
    """
    [升级版] 智能录入：
    - 如果能识别物品 -> 存库存 (MySQL) + 存记忆 (Mem0)
    - 如果不能识别 -> 只存记忆 (Mem0)
    """
    print(f"收到录入请求: {input.text}")

    # 1. 尝试让 LLM 提取信息
    extracted_json = llm_service.extract_item_info(input.text)
    print(f"LLM 提取结果: {extracted_json}")

    # 准备 Mem0 需要的 Metadata
    metadata = {"pure_text": input.text, "timestamp": str(datetime.now())}

    # 返回给前端的信息
    response_data = {
        "status": "success",
        "mode": "memory_only",  # 默认为纯记忆模式
        "ai_extraction": extracted_json,
    }

    # --- 分支判断 ---

    # 判断标准：LLM 提取出了 JSON，并且里面有有效的 'name'
    if extracted_json and extracted_json.get("name"):
        # === 进入 [库存模式] ===
        response_data["mode"] = "inventory_mode"

        # A1. 处理位置
        loc_name = extracted_json.get("location") or "未分类区域"
        location_obj = crud.get_or_create_location_by_name(db, loc_name)

        # A2. 写入 MySQL
        # (注意：如果您还没做 Decimal 修复，这里要小心 float)
        try:
            item_data = schemas.ItemCreate(
                name=extracted_json["name"],
                category=extracted_json.get("category"),
                quantity=extracted_json.get("quantity", 1),
                unit=extracted_json.get("unit", "个"),
                location_id=location_obj.id,
                image_url=None,  # 未来这里可以接图片URL
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
        # === 进入 [纯记忆模式] ===
        print("未识别出具体物品，仅作为笔记存储")
        metadata["type"] = "note"  # 标记为笔记类型

    # --- 统一写入 Mem0 ---
    # 无论是否提取出物品，这句话本身都是有价值的记忆
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    memory_text = f"[{current_time}] {input.text}"

    m.add(memory_text, user_id="user_1", metadata=metadata)

    return response_data


# app/main.py -> search_smart_memory


@app.get("/memories/search_smart")
def search_smart_memory(query: str, db: Session = Depends(database.get_db)):
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


# --- 🛠️ 调试工具接口 ---


@app.get("/debug/dump")
def dump_database(db: Session = Depends(database.get_db)):
    """
    上帝视角：一次性打印出 MySQL 中所有表的数据
    """
    # 1. 获取所有数据
    items = db.query(models.Item).all()
    locations = db.query(models.Location).all()
    inventory = db.query(models.Inventory).all()

    # 2. 简单的转换函数 (把 SQLAlchemy 对象转成字典，方便看)
    def to_dict(obj):
        return {c.name: str(getattr(obj, c.name)) for c in obj.__table__.columns}

    # 3. 组装结果
    return {
        "summary": {
            "items_count": len(items),
            "locations_count": len(locations),
            "inventory_records": len(inventory),
        },
        "data": {
            "items": [to_dict(i) for i in items],
            "locations": [to_dict(l) for l in locations],
            "inventory": [to_dict(inv) for inv in inventory],
        },
    }


@app.get("/debug/relationship")
def dump_relationships(db: Session = Depends(database.get_db)):
    """
    上帝视角：查看 [物品] --(库存)--> [位置] 的完整关系
    """
    # 联表查询：Item -> Inventory -> Location
    results = (
        db.query(
            models.Item.name.label("item_name"),
            models.Item.category,
            models.Inventory.quantity,
            models.Inventory.unit,
            models.Location.name.label("location_name"),
            models.Location.id.label("location_id"),
        )
        .join(models.Inventory, models.Inventory.item_id == models.Item.id)
        .join(models.Location, models.Inventory.location_id == models.Location.id)
        .all()
    )

    # 格式化输出
    report = []
    for row in results:
        report.append(
            {
                "📦 物品": row.item_name,
                "🏷️ 分类": row.category or "未分类",
                "📊 数量": f"{float(row.quantity)} {row.unit}",
                "📍 位置": f"{row.location_name} (ID: {row.location_id})",
            }
        )

    return {"total_records": len(report), "inventory_report": report}


# app/main.py (替换 dump_memories 函数)


@app.get("/debug/memories")
def dump_memories():
    """
    脑机接口：导出 Mem0 中的所有记忆 (Debug版)
    """
    try:
        # 1. 获取所有记忆
        all_memories = m.get_all(user_id="user_1")

        # --- 🔍 调试打印 ---
        print(f"🔍 DEBUG - Mem0 get_all 返回类型: {type(all_memories)}")
        if isinstance(all_memories, list) and len(all_memories) > 0:
            print(f"🔍 DEBUG - 第一条数据样例: {all_memories[0]}")
        else:
            print(f"🔍 DEBUG - 返回内容: {all_memories}")

        # --- 🛠️ 兼容性处理 ---
        # 如果返回的是字典（例如 {'results': [...]}），尝试取列表
        if isinstance(all_memories, dict):
            if "results" in all_memories:
                all_memories = all_memories["results"]
            elif "data" in all_memories:
                all_memories = all_memories["data"]
            else:
                return {
                    "warning": "Mem0 返回了字典，但无法识别结构",
                    "raw_data": all_memories,
                }

        # 2. 格式化输出
        formatted_list = []

        for mem in all_memories:
            # 情况 A: mem 是字典 (我们期望的)
            if isinstance(mem, dict):
                text = mem.get("memory") or mem.get("text") or "未知内容"
                meta = mem.get("metadata", {})
                mem_id = mem.get("id")
            # 情况 B: mem 是字符串 (有时候 Mem0 只返回记忆文本)
            elif isinstance(mem, str):
                text = mem
                meta = {}
                mem_id = "unknown"
            # 情况 C: 其他对象 (比如 Pydantic Model)
            else:
                # 尝试转成字典
                try:
                    mem = dict(mem)
                    text = mem.get("memory", "未知")
                    meta = mem.get("metadata", {})
                    mem_id = mem.get("id")
                except:
                    text = str(mem)
                    meta = {}
                    mem_id = "unknown"

            # 检查关联状态
            item_id = meta.get("item_id") if isinstance(meta, dict) else None

            if item_id:
                link_status = f"🔗 已关联 (Item ID: {item_id})"
            else:
                link_status = "⚠️ 未关联"

            formatted_list.append(
                {
                    "id": mem_id,
                    "text": text,
                    "link_status": link_status,
                    "raw_metadata": meta,
                }
            )

        return {"count": len(formatted_list), "memories": formatted_list}

    except Exception as e:
        import traceback

        traceback.print_exc()  # 打印完整报错堆栈到终端
        return {"error": f"无法获取记忆: {str(e)}"}


# app/main.py


class ChatInput(BaseModel):
    message: str


from app.core.tool_registry import registry
from app.services.llm_service import chat as llm_engine
import json

SYSTEM_PROMPT = """
你是一个贴心、幽默、高效的 AI 家庭管家。
你的职责是管理家庭库存、记忆物品位置，并像真人管家一样与用户对话。

【工具使用规则】
1. 根据用户意图，自主选择工具。
2. **多任务处理**：如果用户一句话包含多个动作（例如"买了A放B，又买了C放D"），**必须在一次响应中生成多个 Tool Call**。
3. **禁止废话**：在决定调用工具时，**不要生成任何普通的回复文本**。只输出 Tool Calls。等待工具执行完毕后，你再根据结果生成自然语言回复。

【关于回答风格】
当工具返回数据后，请遵守以下规则：
1. **说人话**：将 JSON 数据转化为自然的口语，不要出现 JSON 格式或 Key-Value 对。
2. **隐藏技术细节**：不要提及 ID、UUID、数据库字段名等技术术语。
3. **语气亲切**：如果库存充足，可以让人放心；如果没了，提醒补货。
4. **简洁明了**：直接回答核心问题，不要废话。

例如：
- ❌ 错误：根据数据库返回，Inventory item=apple quantity=5 location_id=2。
- ✅ 正确：我查到了，冰箱里还有 5 个苹果。
"""


@app.post("/chat")
def chat_agent(chat: ChatInput, db: Session = Depends(database.get_db)):
    """
    [Agent 模式] 这里的代码现在完全不知道 OpenAI 的存在
    """
    user_msg = chat.message
    print(f"👤 用户: {user_msg}")

    # 构造上下文
    context = {"db": db, "user_id": 1}

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_msg},
    ]

    # 获取工具 Schema
    available_tools = registry.get_schemas()

    print(f"🤖 可用工具: {[tool['function']['name'] for tool in available_tools]}")

    # --- 1. 第一次思考 (调用封装好的 LLM) ---
    # 以前: client.chat.completions.create(...)
    # 现在: llm_engine.chat(...)
    ai_msg = llm_engine(messages=messages, tools=available_tools)

    # --- 2. 判断是否命中工具 ---
    if ai_msg.tool_calls:
        # 把 AI 的思考过程加进历史
        messages.append(ai_msg)

        for tool_call in ai_msg.tool_calls:
            func_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)

            print(f"🤖 动态调用工具: {func_name}, args: {args}")

            # 执行工具
            tool_result = registry.execute(func_name, args, context)

            # 填入结果
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(tool_result, ensure_ascii=False, default=str),
                }
            )

        # --- 3. 第二次思考 (生成人话) ---
        # 再次调用封装工具，这次不需要传 tools 了（通常生成最终回复时不需要）
        final_msg = llm_engine(messages=messages)
        return {"reply": final_msg.content}

    else:
        # 纯闲聊
        return {"reply": ai_msg.content}
