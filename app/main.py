# app/main.py
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from . import models, database, schemas, crud

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="AI Family Butler")


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
    # 1. 让 LLM 提取信息
    extracted_json = llm_service.extract_item_info(input.text)

    if not extracted_json or not extracted_json.get("name"):
        return {"status": "error", "message": "无法识别物品信息，请再说详细点"}

    # 2. 处理位置 (String -> ID)
    loc_name = extracted_json.get("location") or "未分类区域"
    location_obj = crud.get_or_create_location_by_name(db, loc_name)

    # 3. 构造 ItemCreate 对象
    item_data = schemas.ItemCreate(
        name=extracted_json["name"],
        category=extracted_json.get("category"),
        quantity=extracted_json.get("quantity", 1),
        unit=extracted_json.get("unit", "个"),
        location_id=location_obj.id,  # 填入刚才获取的 ID
        image_url=None,
    )

    # 4. 写入 MySQL (事实大脑)
    inventory_rec = crud.create_item_with_inventory(db, item_data)

    # 5. 写入 Mem0 (联想大脑)
    # 关联 item_id
    m.add(input.text, user_id="user_1", metadata={"item_id": inventory_rec.item_id})

    return {
        "status": "success",
        "ai_extraction": extracted_json,
        "db_record": {
            "item": inventory_rec.item.name,
            "location": location_obj.name,
            "quantity": inventory_rec.quantity,
        },
    }
