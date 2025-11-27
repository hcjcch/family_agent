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
