from fastapi import APIRouter, Form, Response, HTTPException, Cookie, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from .auth import verify_password, hash_password
from sqlalchemy.orm import Session
from database import SessionLocal
from models import User


router = APIRouter()



# fake db (مؤقت)
fake_db = {
    "admin": {
        "username": "admin",
        "password": hash_password("1234"),
        "code": hash_password("1010101"),
        "role": "admin"
    }
}


def get_user(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def login_page_html(error=False):
    error_msg = ""

    if error:
        error_msg = "Try again"

    return f"""
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
      font-size: 36px;
    }}
    
    .form .input-span {{
      width: 100%;
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }}
    
    .form input[type="text"],
    .form input[type="password"] {{
      border-radius: 10px;
      padding: 50px 200px;
      width: 100%;
      border: none;
      display: flex;
      align-items: center;
      gap: 0.5rem;
      background-color: var(--clr-alpha);
      outline: 2px solid var(--bg-dark);
      font-size: 24px;
    }}
    
    .form input:focus {{
      outline: 4px solid var(--clr);
    }}
    
    .label {{
      align-self: flex-start;
      color: var(--clr);
      font-weight: 600;
    }}
    
    .form .submit {{
      padding: 20px 352px;
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
      font-size: 34px;
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
      min-height: 100vh;
      display: flex;
      justify-content: center;
      align-items: center;           
      background-color: #FAEAF7;
    }}

    .container {{
      background-color: #e0e0e0;
      padding: 30px;
      border-radius: 15px;
      box-shadow: 0 10px 30px rgba(148, 42, 191, 0.4);
      width: 710px;
      border: 1px solid rgba(148, 42, 191, 0.2);
      position: relative;
      z-index: 1;
    }}

    .error {{
      height: 20px;
      margin-top: 10px;
      color: red;
      text-align: center;
    }}
    
    .switches {{
      display: flex;
      justify-content: center;
      align-items: center;
      gap: 12px;
      margin-top: 10px;
    }}
    
    .switches input {{
      display: none;
    }}
    
    .toggleSwitch {{
      position: relative;
      width: 50px;
      height: 115px;
      background-color: rgb(199, 199, 199);
      border-radius: 35px;
      cursor: pointer;
      display: block;
    }}
    
    .toggleSwitch::after {{
      content: "";
      position: absolute;
      width: 50px;
      height: 115px;
      top: 0;
      left: 0;
      background: rgb(120, 120, 120);
      border-radius: 50%;
      transition: .3s;
    }}
    
    #s1:checked + label::after,
    #s2:checked + label::after,
    #s3:checked + label::after,
    #s4:checked + label::after,
    #s5:checked + label::after,
    #s6:checked + label::after,
    #s7:checked + label::after {{
      transform: translateY(28px);
      background: rgb(199, 199, 199);
    }}
    
    #s1:checked + label,
    #s2:checked + label,
    #s3:checked + label,
    #s4:checked + label,
    #s5:checked + label,
    #s6:checked + label,
    #s7:checked + label {{
      background-color: #BF2A9F;
    }}

    input[type="checkbox"] {{
      display: none;
    }}

    #snow {{
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      pointer-events: none;
      z-index: 0;
    }}
    
</style>
</head>

<body>
<canvas id="snow"></canvas>
    <div class="container">
      <form class="form" method="post" action="/login" autocomplete="off">

        <span class="input-span">
          <label class="label">Username</label>
          <input type="text" name="username" required autocomplete="off">
        </span>

        <span class="input-span">
          <label class="label">Password</label>
          <input type="password" name="password" required>
        </span>

        <div class="switches">
        
          <input id="s1" type="checkbox" name="code1" value="1">
          <label class="toggleSwitch" for="s1"></label>
        
          <input id="s2" type="checkbox" name="code2" value="1">
          <label class="toggleSwitch" for="s2"></label>
        
          <input id="s3" type="checkbox" name="code3" value="1">
          <label class="toggleSwitch" for="s3"></label>
        
          <input id="s4" type="checkbox" name="code4" value="1">
          <label class="toggleSwitch" for="s4"></label>
        
          <input id="s5" type="checkbox" name="code5" value="1">
          <label class="toggleSwitch" for="s5"></label>
        
          <input id="s6" type="checkbox" name="code6" value="1">
          <label class="toggleSwitch" for="s6"></label>
        
          <input id="s7" type="checkbox" name="code7" value="1">
          <label class="toggleSwitch" for="s7"></label>
        
        </div>
        
        <input class="submit" type="submit" value="Log in">
        
        <div class="error">
          {error_msg}
        </div>
        
      </form>
    </div>
<script>
const canvas = document.getElementById("snow");
const ctx = canvas.getContext("2d");

canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

const emojis = ["🍲","🧇","🍕","🍩","🍫","🍟","🍔","🍪","🍦","🍴","🍰","🍚","🍮"];

let snowflakes = [];

for (let i = 0; i < 100; i++) {{
  snowflakes.push({{
    x: Math.random() * canvas.width,
    y: Math.random() * canvas.height,
    size: Math.random() * 20 + 16,
    emoji: emojis[Math.floor(Math.random() * emojis.length)],
    d: Math.random() + 1
  }});
}}

function drawSnow() {{
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  for (let i = 0; i < snowflakes.length; i++) {{
    let f = snowflakes[i];

    ctx.font = f.size + "px Arial";
    ctx.fillStyle ="#E279CB";

    ctx.shadowColor = "rgba(226, 121, 203, 0.5)";
    ctx.shadowBlur = 10;

    ctx.fillText(f.emoji, f.x, f.y);
  }}

  moveSnow();
}}

function moveSnow() {{
  for (let i = 0; i < snowflakes.length; i++) {{
    let f = snowflakes[i];
    f.y += f.d;
    f.x += Math.sin(f.y * 0.01);

    if (f.y > canvas.height) {{
      f.y = 0;
      f.x = Math.random() * canvas.width;
    }}
  }}
}}

setInterval(drawSnow, 25);
</script>
</body>
</html>
"""



@router.get("/", response_class=HTMLResponse)
def home():
    return login_page_html()




@router.post("/login", response_class=HTMLResponse)
def login(
    response: Response,
    username: str = Form(...),
    password: str = Form(...),

    code1: str = Form(None),
    code2: str = Form(None),
    code3: str = Form(None),
    code4: str = Form(None),
    code5: str = Form(None),
    code6: str = Form(None),
    code7: str = Form(None),
):
    user = fake_db.get(username)   

    code = ""
    code += "1" if code1 else "0"
    code += "1" if code2 else "0"
    code += "1" if code3 else "0"
    code += "1" if code4 else "0"
    code += "1" if code5 else "0"
    code += "1" if code6 else "0"
    code += "1" if code7 else "0"

    if (
        not user
        or not verify_password(password, user["password"])
        or not verify_password(code, user["code"])
    ):
        return login_page_html(error=True)

    response = RedirectResponse(url="/admin", status_code=302)

    response.set_cookie(
        key="session",
        value=username,
        httponly=True
    )

    return response


@router.get("/admin", response_class=HTMLResponse)
def admin_page(session: str = Cookie(None)):

    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = fake_db.get(session)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid session")

    if user["role"] != "admin":
        raise HTTPException(status_code=403)

    return """
    <!DOCTYPE html>
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    
    <style>
    body {
      margin: 0;
      font-family: Arial;
      background: #f5f5f5;
    }
    
    /* زر الثلاث نقاط */
    .menu-btn {
      font-size: 24px;
      padding: 15px;
      cursor: pointer;
    }
    
    /* الخلفية مع blur */
    .overlay {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      backdrop-filter: blur(5px);
      background: rgba(0,0,0,0.2);
      opacity: 0;
      pointer-events: none;
      transition: 0.3s;
    }
    
    /* لما يفتح */
    .overlay.active {
      opacity: 1;
      pointer-events: all;
    }
    
    /* السايد بار */
    .sidebar {
      position: fixed;
      top: 0;
      left: -100%;
      width: fit-content;
      height: 100%;
      max-width: 280px;
      min-width: 220px;
      background: #EA9FDA;
      color: white;
      padding: 20px;
      transition: 0.3s;
      border-radius: 0 20px 20px 0;
    }
    
    /* فتح */
    .sidebar.active {
      left: 0;
    }
    
    /* عناصر القائمة */
    .sidebar h2 {
      margin-top: 0;
    }
    
    .menu-item {
      padding: 15px;
      border-radius: 10px;
      margin: 10px 0;
      background: rgba(255,255,255,0.1);
      cursor: pointer;
      transition: 0.2s;
    }
    
    .menu-item:hover {
      background: rgba(255,255,255,0.2);
    }
    
    /* المحتوى */
    .content {
      padding: 20px;
    }
    
    body {
      background-color: #FAEAF7;
    }

    #snow {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      pointer-events: none;
    }

    .sidebar, .content {
      position: relative;
      z-index: 1;
    }

    </style>
    </head>
    
    <body>
    
   <canvas id="snow"></canvas>

    <!-- زر -->
    <div class="menu-btn" onclick="openMenu()">☰</div>
    
    <!-- Overlay -->
    <div id="overlay" class="overlay" onclick="closeMenu()"></div>
    
    <!-- Sidebar -->
    <div id="sidebar" class="sidebar">
    
      <h2>⚙️ Settings</h2>
    
      <div class="menu-item" onclick="go('/devices')">
        ➕ إضافة جهاز
      </div>
    
      <div class="menu-item" onclick="go('/theme')">
        🎨 تعديل الثيم
      </div>
    
      <div class="menu-item" onclick="go('/edit-menu')">
        🍔 تعديل المنيو
      </div>
    
      <div class="menu-item" onclick="go('/users')">
        👤 الحسابات
      </div>
    
      <div class="menu-item" onclick="go('/stats')">
        📊 الإحصائيات
      </div>
    
    </div>
    
    <!-- المحتوى -->
    <div class="content">
      <h1>Admin Panel 🔥</h1>
      <p>أهلاً في لوحة التحكم</p>
    </div>
    
    <script>
    function openMenu() {
      document.getElementById("sidebar").classList.add("active");
      document.getElementById("overlay").classList.add("active");
    }
    
    function closeMenu() {
      document.getElementById("sidebar").classList.remove("active");
      document.getElementById("overlay").classList.remove("active");
    }
    
    function go(path) {
      window.location.href = path;
    }
    </script>
    <script>
    const canvas = document.getElementById("snow");
    const ctx = canvas.getContext("2d");
    
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    
    const emojis = ["🍲","🧇","🍕","🍩","🍫","🍟","🍔","🍪","🍦","🍴","🍰","🍚","🍮"];

    let snowflakes = [];
    
    for (let i = 0; i < 35; i++) {
      snowflakes.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        size: Math.random() * 20 + 16,
        emoji: emojis[Math.floor(Math.random() * emojis.length)],
        d: Math.random() + 1
      });
    }
    
    function drawSnow() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    
      for (let i = 0; i < snowflakes.length; i++) {
        let f = snowflakes[i];
    
        ctx.font = f.size + "px Arial";
        ctx.fillStyle ="#E279CB";
    
        ctx.shadowColor = "rgba(226, 121, 203, 0.5)";
        ctx.shadowBlur = 10;
    
        ctx.fillText(f.emoji, f.x, f.y);
      }
    
      moveSnow();
    }
    
    function moveSnow() {
      for (let i = 0; i < snowflakes.length; i++) {
        let f = snowflakes[i];
        f.y += f.d;
        f.x += Math.sin(f.y * 0.01);
    
        if (f.y > canvas.height) {
          f.y = 0;
          f.x = Math.random() * canvas.width;
        }
      }
    }
    
    setInterval(drawSnow, 25);
    </script>
    </body>
    </html>
    """