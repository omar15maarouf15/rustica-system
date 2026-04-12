from fastapi import APIRouter, Query, Depends, HTTPException
from database import SessionLocal
from models import Category, MenuItem
from models import Group




router = APIRouter()


@router.get("/menu")
def get_menu():
    db = SessionLocal()

    categories = db.query(Category).all()
    result = []

    for cat in categories:
        items = db.query(MenuItem).filter(MenuItem.category_id == cat.id).all()

        result.append({
            "category": cat.name,
            "items": [
                {
                    "name": item.name,
                    "price": item.price,
                    "section": item.section
                }
                for item in items
            ]
        })

    db.close()
    return result

@router.get("/categories")
def get_categories():
    db = SessionLocal()

    categories = db.query(Category).all()

    result = []
    for c in categories:
        result.append({
            "id": c.id,
            "name": c.name
        })

    db.close()
    return result

@router.get("/groups/{category_id}")
def get_groups(category_id: int):
    db = SessionLocal()

    groups = db.query(Group)\
        .filter(Group.category_id == category_id)\
        .order_by(Group.position)\
        .all()

    return groups


@router.get("/items/{category_id}")
def get_items(category_id: int, group: int = Query(None)):
    db = SessionLocal()

    query = db.query(MenuItem).filter(MenuItem.category_id == category_id)

    if group:
        query = query.filter(MenuItem.group_id == group)

    items = query.all()

    result = []
    for item in items:
        result.append({
            "id": item.id,
            "name": item.name,
            "price": item.price
        })

    db.close()
    return result


@router.delete("/delete-category/{category_id}")
def delete_category(category_id: int):
    db = SessionLocal()

    category = db.query(Category).filter(Category.id == category_id).first()

    if not category:
        db.close()
        return {"error": "Category not found"}

    db.delete(category)
    db.commit()
    db.close()

    return {"message": "Category deleted"}

@router.post("/rename-category/{category_id}")
def rename_category(category_id: int, data: dict):
    db = SessionLocal()

    category = db.query(Category).filter(Category.id == category_id).first()

    if not category:
        db.close()
        return {"error": "Category not found"}

    category.name = data.get("name", category.name)

    db.commit()
    db.close()

    return {"message": "Renamed"}


from pydantic import BaseModel

class GroupCreate(BaseModel):
    name: str
    category_id: int


@router.post("/add-group")
def add_group(data: GroupCreate):

    db = SessionLocal()

    g = Group(
        name=data.name,
        category_id=data.category_id
    )

    db.add(g)
    db.commit()

    db.close()

    return {"status": "ok"}


@router.delete("/delete-group/{group_id}")
def delete_group(group_id: int):

    db = SessionLocal()

    group = db.query(Group).filter(Group.id == group_id).first()

    if group:
        db.delete(group)
        db.commit()

    db.close()

    return {"status": "deleted"}


@router.post("/rename-group/{id}")
def rename_group(id: int, data: dict):

    db = SessionLocal()

    new_name = data.get("name")
   
    # 🔥 عدل حسب الداتابيس تبعك
    group = db.query(Group).filter(Group.id == id).first()

    if group:
        group.name = new_name
        db.commit()

    return {"status": "ok"}


from fastapi import Body

@router.post("/reorder-groups")
def reorder_groups(groups: list = Body(...)):

    db = SessionLocal()

    print("DATA:", groups)

    for item in groups:
        print("ITEM:", item)

        group = db.query(Group).filter(Group.id == int(item["id"])).first()

        if group:
            print("FOUND GROUP:", group.id)
            group.position = int(item["position"])
        else:
            print("GROUP NOT FOUND")

    db.commit()

    return {"status": "ok"}


@router.post("/move-group")
def move_group(data: dict = Body(...)):

    db = SessionLocal()

    group_id = int(data["group_id"])
    direction = data["direction"]

    group = db.query(Group).filter(Group.id == group_id).first()

    if not group:
        return {"error": "not found"}

    groups = db.query(Group)\
        .filter(Group.category_id == group.category_id)\
        .order_by(Group.position)\
        .all()

    index = next((i for i, g in enumerate(groups) if g.id == group.id), None)

    if index is None:
        return {"error": "index error"}

    if direction == "up":
        new_index = (index - 1) % len(groups)
    else:
        new_index = (index + 1) % len(groups)

    other = groups[new_index]

    # swap
    group.position, other.position = other.position, group.position

    db.commit()

    return {"status": "ok"}



