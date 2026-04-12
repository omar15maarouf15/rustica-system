from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from .auth import verify_password, create_access_token, hash_password
from sqlalchemy.orm import Session
from database import SessionLocal
from models import User


router = APIRouter()



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

def login_page_html(error=False):
    error_msg = ""

    if error:
        error_msg = "Try again"

    return """
<!DOCTYPE html>
<html>
<head>
<style>
    .form {{
      --bg-light: #efefef;
      --bg-dark: #707070;
      --clr: #4A2ABF;
      --clr-alpha: #9c9c9c60;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 1rem;
      width: 100%;
      max-width: 300px;
    }}
    
    .form .input-span {{
      width: 100%;
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }}
    
    .form input[type="text"],
    .form input[type="password"] {{
      border-radius: 0.5rem;
      padding: 1rem 0.75rem;
      width: 100%;
      border: none;
      display: flex;
      align-items: center;
      gap: 0.5rem;
      background-color: var(--clr-alpha);
      outline: 2px solid var(--bg-dark);
    }}
    
    .form input:focus {{
      outline: 2px solid var(--clr);
    }}
    
    .label {{
      align-self: flex-start;
      color: var(--clr);
      font-weight: 600;
    }}
    
    .form .submit {{
      padding: 1rem 0.75rem;
      width: 100%;
      display: block;
      align-items: center;
      gap: 0.5rem;
      border-radius: 3rem;
      background-color: var(--bg-dark);
      color: var(--bg-light);
      border: none;
      cursor: pointer;
      transition: all 300ms;
      font-weight: 600;
      font-size: 0.9rem;
      margin: 0 auto;
    }}
    
    .form .submit:hover {{
      background-color: var(--clr);
      color: var(--bg-dark);
    }}
    
    .span {{
      text-decoration: none;
      color: var(--bg-dark);
    }}
    
    .span a {{
      color: var(--clr);
    }}
   
    body {{
      margin: 0;
      height: 100vh;
      display: flex;
      justify-content: center;  
      align-items: center;      
      background-color: #f5f5f5;
    }}

    .container {{
      background-color: #e0e0e0;
      padding: 40px;
      border-radius: 15px;
      box-shadow: 0 10px 30px rgba(148, 42, 191, 0.4);
      width: 320px;
      border: 1px solid rgba(148, 42, 191, 0.2);
    }}

    .error {{
      height: 20px;
      margin-top: 10px;
      color: red;
      text-align: center;
    }}
    
</style>
</head>

<body>
    <div class="container">
      <form class="form" method="post" action="/login">

        <span class="input-span">
          <label class="label">Username</label>
          <input type="text" name="username" required>
        </span>

        <span class="input-span">
          <label class="label">Password</label>
          <input type="password" name="password" required>
        </span>

        <input class="submit" type="submit" value="Log in">
        
        <div class="error">
          {error_msg}
        </div>
        
      </form>
    </div>

</body>
</html>
""".format(error_msg=error_msg)



@router.get("/", response_class=HTMLResponse)
def home():
    return login_page_html()




@router.post("/login", response_class=HTMLResponse)
def login(username: str = Form(...), password: str = Form(...)):
    db = SessionLocal()
    user = get_user(db, username)

    if not user or not verify_password(password, user.password):
        return f"""
        <html>
        <body>
            {login_page_html(error=True)}
        </body>
        </html>
        """

    token = create_access_token({
        "sub": user.username,
        "role": user.role
    })

    response = RedirectResponse(url="/admin", status_code=303)
    response.set_cookie(key="access_token", value=token)

    return response
