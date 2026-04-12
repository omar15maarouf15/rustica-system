from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from .auth import verify_password, create_access_token, hash_password
from sqlalchemy.orm import Session
from database import SessionLocal
from main import User


router = APIRouter()

templates = Jinja2Templates(directory="templates")

# fake db (مؤقت)
fake_db = {
    "admin": {
        "username": "admin",
        "password": hash_password("1234"),
        "role": "admin"
    }
}


def get_user(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()


@router.get("/", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    db = SessionLocal()

    user = get_user(db, username)

    if not user or not verify_password(password, user.password):
        raise HTTPException(status_code=401, detail="Wrong credentials")

    token = create_access_token({
        "sub": user.username,
        "role": user.role
    })

    response = RedirectResponse(url="/admin", status_code=303)

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/"
    )

    return response
