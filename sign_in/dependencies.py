from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer
from jose import jwt, JWTError
from .auth import SECRET_KEY, ALGORITHM

security = HTTPBearer()

def get_current_user(request: Request):
    token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(status_code=403, detail="Not authenticated")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except:
        raise HTTPException(status_code=403, detail="Invalid token")