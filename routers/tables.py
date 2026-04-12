from fastapi import APIRouter, Depends, HTTPException
from models import Table
from sign_in.dependencies import get_current_user
from database import SessionLocal


router = APIRouter()


@router.get("/tables")
def get_tables():
    db = SessionLocal()

    tables = db.query(Table).all()

    result = []
    for table in tables:
        result.append({
            "id": table.id,
            "name": table.name,
            "status": table.status
        })

    db.close()
    return result

@router.get("/reserved")
def get_reserved_tables():
    db = SessionLocal()

    tables = db.query(Table).filter(Table.status == "reserved").all()

    result = []

    for t in tables:
        result.append({
            "id": t.id,
            "name": t.name,
            "note": t.note
        })

    db.close()
    return result



