from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from database import engine, SessionLocal
from database import SessionLocal

from models import Base, Table, Category, MenuItem
from models import Group, OrderItem, Order, Table, User

from routers import tables, menu, orders

from datetime import datetime

from sign_in.dependencies import get_current_user
from sign_in.routes import router as auth_router
from sign_in.auth import hash_password





Base.metadata.create_all(bind=engine)
app = FastAPI(title="Rustica Restaurant System")
templates = Jinja2Templates(directory="templates")




def create_admin():
    db = SessionLocal()

    user = db.query(User).filter(User.username == "admin").first()

    if not user:
        new_user = User(
            username="admin",
            password=hash_password("1234"),
            role="admin"
        )
        db.add(new_user)
        db.commit()
        print("✅ admin created")
    else:
        print("ℹ️ admin already exists")

    db.close()

create_admin()

# ===== إنشاء الطاولات =====
def create_tables():
    db = SessionLocal()

    if db.query(Table).first():
        db.close()
        return

    for i in range(1, 46):
        db.add(Table(name=f"T{i}", status="free"))

    for i in range(1, 41):
        db.add(Table(name=f"P{i}", status="free"))

    db.commit()
    db.close()


# ===== إنشاء المنيو =====

def create_menu():
    db = SessionLocal()

    # إذا في بيانات → لا تعيد الإنشاء
    if db.query(Category).first():
        db.close()
        return

    # ===== Categories =====
    categories = [
        "Breakfast",
        "Soup & Salad",
        "Dessert",
        "Argulieh",
        "Starters",
        "Main Dishes",
        "Beverages"
    ]

    category_map = {}

    for cat in categories:
        c = Category(name=cat)
        db.add(c)
        db.commit()
        db.refresh(c)
        category_map[cat] = c.id

    # ===== Groups =====
    groups = {}

    # Main Dishes → Burgers
    burger_group = Group(
        name="Burgers",
        category_id=category_map["Main Dishes"]
    )
    db.add(burger_group)
    db.commit()
    db.refresh(burger_group)

    groups["burgers"] = burger_group.id

    # (مستقبلاً فيك تضيف Groups تانية هون)
    # مثال:
    # pizza_group = Group(name="Pizza", category_id=category_map["Main Dishes"])

    # ===== Items =====
    items = [

        # ===== Burgers (Grouped) =====
        ("BBQ Burger", 4.5, "Main Dishes", "kitchen", groups["burgers"]),
        ("Cheese Burger", 4.0, "Main Dishes", "kitchen", groups["burgers"]),

        # ===== Main بدون group =====
        ("Chicken Parmesan", 5.5, "Main Dishes", "kitchen", None),

        # ===== Starters =====
        ("Nachos Supreme", 3.5, "Starters", "kitchen", None),
        ("Fried Mozzarella", 3.0, "Starters", "kitchen", None),

        # ===== Dessert =====
        ("Cheese Cake", 2.5, "Dessert", "bar", None),
        ("Chocolate Cake", 2.5, "Dessert", "bar", None),

        # ===== Drinks =====
        ("Water", 0.5, "Beverages", "bar", None),
        ("Mango Juice", 1.5, "Beverages", "bar", None),

        # ===== Shisha =====
        ("Apple", 3.0, "Argulieh", "shisha", None),
        ("Apple Mint", 3.0, "Argulieh", "shisha", None),
    ]

    for name, price, cat, section, group_id in items:
        db.add(MenuItem(
            name=name,
            price=price,
            category_id=category_map[cat],
            section=section,
            group_id=group_id
        ))

    db.commit()
    db.close()

# تشغيل الإنشاء مرة واحدة
create_tables()
create_menu()


# ربط الروترات
app.include_router(tables.router)
app.include_router(menu.router)
app.include_router(orders.router)
app.include_router(auth_router)



@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
    <head>
        <title>Main</title>

        <style>
            body {
                text-align: center;
                font-family: Arial;
            }

            button {
                margin: 10px;
                padding: 10px;
                width: 200px;
            }
        </style>
    </head>

    <body>

        <h1>Rustica System</h1>

        <button onclick="goTables()">Tables</button><br>
        <button onclick="goReserved()">Reserved Tables</button><br>
        <button>Today Stats</button><br>
        <button onclick="goSettings()">Settings</button>

        <script>
        function goTables() {
            window.location.href = "/tables-ui";
        }

        function goReserved() {
            window.location.href = "/reserved-ui";
        }

        function goSettings() {
            window.location.href = "/settings";
        }
        </script>

    </body>
    </html>
    """

@app.get("/view-table/{table_id}", response_class=HTMLResponse)
def view_table(table_id: int):

    db = SessionLocal()

    table = db.query(Table).filter(Table.id == table_id).first()

    items = db.query(OrderItem).join(Order).filter(Order.table_id == table_id).all()

    total = 0
    items_html = ""

    for i in items:
        name = i.item.name
        price = i.item.price
        qty = i.quantity

        line_total = price * qty
        total += line_total

        items_html += f'''
        <div class="item">
            <span>{name} x{qty}</span>
            <div class="price">{line_total}</div>
        </div>
        '''

    status = table.status if table else "free"
    note = table.note if table and table.note else ""
    note = note.replace("\n", "<br>")

    discount = table.discount if table and table.discount else 0

    final_total = total - discount
    if final_total < 0:
        final_total = 0

    db.close()

    reserve_btn = ""
    edit_note_btn = ""
    discount_btn = ""

    if status == "free":
        reserve_btn = '<div class="btn" onclick="handleReserve()">Reserve</div>'

    elif status == "reserved":
        reserve_btn = '<div class="btn" onclick="handleReserve()">Cancel Reservation</div>'
        edit_note_btn = '<div class="btn" onclick="showNoteBox()">Edit Note</div>'

    if status == "occupied":
        discount_btn = '<div class="btn" onclick="showDiscount()">Add Discount</div>'

    show_items = "block" if status == "occupied" else "none"

    return f"""
    <html>
    <head>
        <title>Table {table_id}</title>

        <style>
            body {{
                margin: 0;
                font-family: Arial;
                display: flex;
                height: 100vh;
            }}

            .left {{
                width: 25%;
                background: #e5e5e5;
            }}

            .center {{
                width: 50%;
                display: flex;
                flex-direction: column;
                align-items: center;
                padding-top: 20px;
            }}

            .title {{
                background: black;
                color: white;
                padding: 15px 40px;
                border-radius: 20px;
                margin-bottom: 10px;
            }}

            .note {{
                margin-bottom: 10px;
                color: #555;
                font-size: 18px;
                line-height: 1.6;
            }}

            .items-container {{
                width: 80%;
                max-height: 350px;
                overflow-y: auto;
                display: {show_items};
            }}

            .item {{
                display: flex;
                justify-content: space-between;
                padding: 10px;
                border-radius: 15px;
                margin: 5px 0;
                background: #ddd;
            }}

            .price {{
                background: #555;
                color: white;
                padding: 8px 12px;
                border-radius: 15px;
            }}

            .summary {{
                width: 80%;
                margin-top: 15px;
                display: {show_items};
            }}

            .row {{
                display: flex;
                justify-content: space-between;
                background: #6fa58c;
                padding: 12px;
                border-radius: 15px;
                margin-top: 5px;
                color: white;
            }}

            .right {{
                width: 25%;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                gap: 20px;
            }}

            .btn {{
                width: 210px;
                padding: 15px 0;
                border-radius: 20px;
                border: 2px solid black;
                text-align: center;
                cursor: pointer;
                background: white;
                font-size: 16px;
            }}

            textarea {{
                width: 250px;
                height: 80px;
            }}

            #discountValue {{
                width: 200px;
                height: 35px;
                font-size: 16px;
            }}

            /* 🔔 إضافة الإشعار فقط */
            .toast {{
                position: fixed;
                top: 20px;
                right: 20px;
                background: #4CAF50;
                color: white;
                padding: 15px 25px;
                border-radius: 10px;
                font-size: 16px;
                z-index: 9999;
            }}
        </style>
    </head>

    <body>

    <div class="left">
        <div style="padding:20px;">
            <h3>Discount</h3>

            <div id="discountOptions" style="display:none; margin-top:15px;">
                <div class="btn" onclick="selectPercent()">Percentage</div>
                <div class="btn" onclick="selectAmount()">Amount</div>
            </div>

            <div id="discountInput" style="display:none; margin-top:15px;">
                <input id="discountValue" type="number"><br><br>
                <div class="btn" onclick="applyDiscount()">Apply</div>

                <div id="discountError" style="color:red; margin-top:10px;"></div>
            </div>
        </div>
    </div>

    <div class="center">
        <div class="title">Table {table_id}</div>
        <div class="note" dir="auto">{note}</div>

        <div id="noteBox" style="display:none;">
            <textarea id="noteInput"></textarea><br>
            <button onclick="saveNote()">Save</button>
        </div>

        <div class="items-container">{items_html}</div>

        <div class="summary">
            <div class="row">
                <span>Discount</span>
                <span>{discount}</span>
            </div>

            <div class="row">
                <span>Total</span>
                <span>{final_total}</span>
            </div>
        </div>
    </div>

    <div class="right">
        {reserve_btn}
        {edit_note_btn}
        {discount_btn}

        <div class="btn" onclick="goOrder()">Add Order</div>
        <div class="btn" onclick="goBack()">Back</div>
    </div>

    <script>

    // 🔔 إضافة الإشعار فقط
    function showToast(message) {{
        const toast = document.createElement("div");
        toast.className = "toast";
        toast.innerText = message;

        document.body.appendChild(toast);

        setTimeout(() => toast.remove(), 2500);
    }}

    if (localStorage.getItem("printed")) {{
        showToast("Printed successfully ✅");
        localStorage.removeItem("printed");
    }}

    let discountType = null;

    function showDiscount() {{
        document.getElementById("discountOptions").style.display = "block";
    }}

    function selectPercent() {{
        discountType = "percent";
        document.getElementById("discountInput").style.display = "block";
    }}

    function selectAmount() {{
        discountType = "amount";
        document.getElementById("discountInput").style.display = "block";
    }}

    function applyDiscount() {{

        let value = parseFloat(document.getElementById("discountValue").value);
        let total = {total};

        let errorBox = document.getElementById("discountError");
        if (errorBox) errorBox.innerText = "";

        if (isNaN(value)) {{
            if (errorBox) errorBox.innerText = "Enter valid number";
            return;
        }}

        if (value < 0) {{
            if (errorBox) errorBox.innerText = "Value cannot be negative";
            return;
        }}

        let discount = 0;

        if (discountType === "percent") {{

            if (value > 100) {{
                if (errorBox) errorBox.innerText = "Percentage cannot exceed 100%";
                return;
            }}

            discount = (total * value) / 100;
            discount = Math.round(discount * 20) / 20;

        }} else {{

            if (value > total) {{
                if (errorBox) errorBox.innerText = "Discount cannot exceeds total bill";
                return;
            }}

            discount = value;
        }}

        fetch("/update-discount/{table_id}", {{
            method: "POST",
            headers: {{
                "Content-Type": "application/json"
            }},
            body: JSON.stringify({{ discount: discount }})
        }}).then(() => location.reload());
    }}

    function goOrder() {{
        window.location.href = "/order/{table_id}";
    }}

    function goBack() {{
        window.location.href = "/tables-ui";
    }}

    function showNoteBox() {{
        document.getElementById("noteBox").style.display = "block";
    }}

    function handleReserve() {{
        if ("{status}" === "free") {{
            document.getElementById("noteBox").style.display = "block";
        }} else {{
            fetch("/reserve/{table_id}", {{
                method: "POST"
            }}).then(() => location.reload());
        }}
    }}

    function saveNote() {{
        const note = document.getElementById("noteInput").value;

        if ("{status}" === "free") {{
            fetch("/reserve/{table_id}", {{
                method: "POST",
                headers: {{
                    "Content-Type": "application/json"
                }},
                body: JSON.stringify({{ note: note }})
            }}).then(() => location.reload());
        }} else {{
            fetch("/update-note/{table_id}", {{
                method: "POST",
                headers: {{
                    "Content-Type": "application/json"
                }},
                body: JSON.stringify({{ note: note }})
            }}).then(() => location.reload());
        }}
    }}

    </script>

    </body>
    </html>
    """


@app.get("/reserved-ui", response_class=HTMLResponse)
def reserved_ui():
    return """
    <html>
    <head>
        <title>Reserved Tables</title>
        <style>
            body { font-family: Arial; text-align:center; }

            .box {
                border: 2px solid black;
                margin: 10px auto;
                padding: 10px;
                width: 250px;
                background: #f5f5f5;
            }

            button {
                margin-top: 20px;
                padding: 10px;
            }
        </style>
    </head>

    <body>

    <h2>Reserved Tables</h2>

    <div id="list"></div>

    <button onclick="goBack()">Back</button>

    <script>
    async function loadReserved() {
        const res = await fetch('/reserved');
        const data = await res.json();

        const container = document.getElementById("list");
        container.innerHTML = "";

        data.forEach(t => {
            const div = document.createElement("div");
            div.className = "box";

            div.innerHTML = `
                <strong>${t.name}</strong><br>
                ${t.note ? t.note : "No note"}
            `;

            container.appendChild(div);
        });
    }

    function goBack() {
        window.location.href = "/";
    }

    loadReserved();
    </script>

    </body>
    </html>
    """



@app.get("/outside", response_class=HTMLResponse)
def outside_tables():
    return """
    <html>
    <head>
        <title>Outdoor Tables</title>

        <style>
            body { font-family: Arial; text-align:center; }

            .grid {
                display: grid;
                grid-template-columns: repeat(5, 1fr);
                gap: 10px;
                padding: 20px;
            }

            .table {
                position: relative;
                padding: 20px;
                border-radius: 10px;
                border: 2px solid black;
                cursor: pointer;
                background: white;
            }

            .indicator {
                width: 12px;
                height: 12px;
                border-radius: 50%;
                position: absolute;
                top: 5px;
                right: 5px;
            }

            .free { background:red; }
            .occupied { background:green; }
            .reserved { background:orange; }

            button {
                margin:10px;
                padding:10px;
                width:200px;
            }
        </style>
    </head>

    <body>

    <h2>Outdoor Tables</h2>

    <div class="grid" id="tables"></div>

    <button onclick="goInside()">Indoor Tables</button>
    <button onclick="goHome()">Main</button>

    <script>
    async function loadTables() {
        const res = await fetch('/tables');
        const data = await res.json();

        const container = document.getElementById("tables");
        container.innerHTML = "";

        data.forEach(t => {

            if (!t.name.startsWith("P")) return;

            const div = document.createElement("div");
            div.className = "table";
            div.innerText = t.name;

            const dot = document.createElement("div");
            dot.className = "indicator";

            if (t.status === "free") dot.classList.add("free");
            else if (t.status === "occupied") dot.classList.add("occupied");
            else dot.classList.add("reserved");

            div.appendChild(dot);

            div.onclick = () => {
                window.location.href = `/view-table/${t.id}?from=outside`;
            };

            container.appendChild(div);
        });
    }

    function goInside() {
        window.location.href = "/tables-ui";
    }

    function goHome() {
        window.location.href = "/";
    }

    loadTables();
    </script>

    </body>
    </html>
    """




@app.get("/tables-ui", response_class=HTMLResponse)
def tables_ui():
    print("1")
    return """
    <html>
    <head>
        <title>Indoor Tables</title>

        <style>
            body { font-family: Arial; text-align:center; }

            .grid {
                display: grid;
                grid-template-columns: repeat(5, 1fr);
                gap: 10px;
                padding: 20px;
            }

            .table {
                position: relative;
                padding: 20px;
                border-radius: 10px;
                border: 2px solid black;
                cursor: pointer;
                background: white;
            }

            .indicator {
                width: 12px;
                height: 12px;
                border-radius: 50%;
                position: absolute;
                top: 5px;
                right: 5px;
            }

            .free { background:red; }
            .occupied { background:green; }
            .reserved { background:orange; }

            button {
                margin:10px;
                padding:10px;
                width:200px;
            }
        </style>
    </head>

    <body>

    <h2>Indoor Tables</h2>

    <div class="grid" id="tables"></div>

    <button onclick="goOutside()">Outdoor Tables</button>
    <button onclick="goHome()">Main</button>

    <script>
    async function loadTables() {
        const res = await fetch('/tables');
        const data = await res.json();

        const container = document.getElementById("tables");
        container.innerHTML = "";

        data.forEach(t => {

            if (!t.name.startsWith("T")) return;

            const div = document.createElement("div");
            div.className = "table";
            div.innerText = t.name;

            const dot = document.createElement("div");
            dot.className = "indicator";

            if (t.status === "free") dot.classList.add("free");
            else if (t.status === "occupied") dot.classList.add("occupied");
            else dot.classList.add("reserved");

            div.appendChild(dot);

            div.onclick = () => {
                window.location.href = `/view-table/${t.id}`;
            };

            container.appendChild(div);
        });
    }

    function goOutside() {
        window.location.href = "/outside";
    }

    function goHome() {
        window.location.href = "/";
    }

    loadTables();
    </script>

    </body>
    </html>
    """

@app.get("/order/{table_id}", response_class=HTMLResponse)
def order_categories(table_id: int):
    return f"""
    <html>
    <head>
        <title>Order</title>

        <style>
            body {{
                font-family: Arial;
                text-align: center;
            }}

            .grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, 140px); /* 🔥 ديناميكي */
                justify-content: center; /* 🔥 توسيط */
                gap: 15px;
                padding: 20px 140px; /* 🔥 مساحة يمين ويسار = مربع */
            }}

            .card {{
                border: 2px solid black;
                width: 140px;
                height: 140px;
                border-radius: 15px;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                background: #f5f5f5;
                font-size: 16px;
                transition: 0.2s;
            }}

            .card:hover {{
                background: #ddd;
                transform: scale(1.05);
            }}

            button {{
                margin-top: 20px;
                padding: 10px;
            }}
        </style>
    </head>

    <body>

    <h2>Select Category (Table {table_id})</h2>

    <div class="grid" id="cats"></div>

    <button onclick="goBack()">Back</button>

    <script>
    async function loadCats() {{
        const res = await fetch('/categories');
        const data = await res.json();

        const container = document.getElementById("cats");
        container.innerHTML = "";

        data.forEach(c => {{
            const div = document.createElement("div");
            div.className = "card";
            div.innerText = c.name;

            div.onclick = () => {{
                window.location.href = `/order-groups/{table_id}/${{c.id}}`;
            }};

            container.appendChild(div);
        }});
    }}

    function goBack() {{
        window.location.href = "/tables-ui";
    }}

    loadCats();
    </script>

    </body>
    </html>
    """



@app.get("/order-groups/{table_id}/{category_id}", response_class=HTMLResponse)
def order_groups(request: Request, table_id: int, category_id: int):

    return f"""
    <html>
    <head>
        <title>Groups</title>

        <style>
            body {{
                font-family: Arial;
                text-align: center;
            }}

            .grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, 140px);
                justify-content: center;
                gap: 15px;
                padding: 20px 140px;
            }}

            .card {{
                width: 140px;
                height: 140px;
                border: 2px solid black;
                border-radius: 15px;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                background: #f5f5f5;
            }}
        </style>
    </head>

    <body>

    <h2>Select Group</h2>

    <div class="grid" id="groups"></div>

    <button onclick="goBack()">Back</button>

    <script>
    async function loadGroups() {{
        const res = await fetch('/groups/{category_id}');
        const data = await res.json();

        const container = document.getElementById("groups");
        container.innerHTML = "";

        if (data.length === 0) {{
            window.location.href = `/order-items/{table_id}/{category_id}?from=category`;
            return;
        }}

        data.forEach(g => {{
            const div = document.createElement("div");
            div.className = "card";
            div.innerText = g.name;

            div.onclick = () => {{
                window.location.href = `/order-items/{table_id}/{category_id}?group=${{g.id}}&from=group`;
            }};

            container.appendChild(div);
        }});
    }}

    function goBack() {{
        window.location.href = `/order/{table_id}`;
    }}

    loadGroups();
    </script>

    </body>
    </html>
    """



@app.get("/order-items/{table_id}/{category_id}", response_class=HTMLResponse)
def order_items(request: Request, table_id: int, category_id: int):

    group_id = request.query_params.get("group")
    from_page = request.query_params.get("from")

    return f"""
    <html>
    <head>
        <title>Items</title>

        <style>
            body {{
                font-family: Arial;
                text-align: center;
            }}

            .grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, 140px);
                justify-content: center;
                gap: 15px;
                padding: 20px 140px;
            }}

            .card {{
                width: 140px;
                height: 140px;
                border: 2px solid black;
                border-radius: 15px;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                background: #f5f5f5;
            }}

            .popup {{
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: white;
                border: 2px solid black;
                padding: 20px;
                z-index: 1000;
            }}

            .spinner {{
                border: 6px solid #f3f3f3;
                border-top: 6px solid #3498db;
                border-radius: 50%;
                width: 50px;
                height: 50px;
                animation: spin 1s linear infinite;
            }}

            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
        </style>
    </head>

    <body>

    <h2>Select Item (Table {table_id})</h2>

    <div class="grid" id="items"></div>

    <button onclick="goBack()">Back</button>

    <script>

    const TABLE_ID = {table_id};
    const FROM = "{from_page}";
    const CATEGORY_ID = {category_id};

    async function loadItems() {{

        let url = `/items/{category_id}`;
        const group = "{group_id}";

        if (group && group !== "None") {{
            url += `?group=${{group}}`;
        }}

        const res = await fetch(url);
        const data = await res.json();

        const container = document.getElementById("items");
        container.innerHTML = "";

        data.forEach(i => {{
            const div = document.createElement("div");
            div.className = "card";

            div.innerHTML = `
                <strong>${{i.name}}</strong>
                <br>
                $${{i.price}}
            `;

            div.onclick = () => showQtyPopup(i.id);

            container.appendChild(div);
        }});
    }}

    function showQtyPopup(itemId) {{

        const popup = document.createElement("div");
        popup.className = "popup";

        popup.innerHTML = `
            <p>Enter Quantity</p>
            <input id="qtyInput" type="number" min="1"><br><br>
            <button onclick="confirmQty(${{itemId}})">OK</button>
        `;

        document.body.appendChild(popup);
    }}

    function confirmQty(itemId) {{

        let qty = parseInt(document.getElementById("qtyInput").value);

        if (!qty || qty <= 0) {{
            alert("Quantity must be greater than 0");
            return;
        }}

        if (window.isSubmitting) return;
        window.isSubmitting = true;

        const loading = document.createElement("div");
        loading.style.position = "fixed";
        loading.style.top = "0";
        loading.style.left = "0";
        loading.style.width = "100%";
        loading.style.height = "100%";
        loading.style.background = "rgba(0,0,0,0.6)";
        loading.style.display = "flex";
        loading.style.flexDirection = "column";
        loading.style.alignItems = "center";
        loading.style.justifyContent = "center";
        loading.style.color = "white";
        loading.style.fontSize = "20px";
        loading.style.zIndex = "9999";

        loading.innerHTML = `
            <div class="spinner"></div>
            <p>Waiting for printing...</p>
            <button id="continueBtn" style="margin-top:20px; padding:10px;">
                Continue
            </button>
        `;

        document.body.appendChild(loading);

        fetch('/orders', {{
            method: "POST",
            headers: {{
                "Content-Type": "application/json"
            }},
            body: JSON.stringify({{
                table_id: TABLE_ID,
                items: [
                    {{
                        item_id: itemId,
                        quantity: qty
                    }}
                ]
            }})
        }});

        let autoRedirect = setTimeout(() => {{
            if (!window.userClicked) {{
                localStorage.setItem("printed", "1");
                goNext();
            }}
        }}, 1500);

        document.getElementById("continueBtn").onclick = () => {{
            window.userClicked = true;
            clearTimeout(autoRedirect);
            localStorage.setItem("printed", "1");
            goNext();
        }};

        function goNext() {{
            if (FROM === "outside") {{
                window.location.href = `/view-table/${{TABLE_ID}}?from=outside`;
            }} else {{
                window.location.href = `/view-table/${{TABLE_ID}}`;
            }}
        }}
    }}

    function goBack() {{
        if (FROM === "group") {{
            window.location.href = `/order-groups/${{TABLE_ID}}/${{CATEGORY_ID}}`;
        }} else {{
            window.location.href = `/order/${{TABLE_ID}}`;
        }}
    }}

    loadItems();

    </script>

    </body>
    </html>
    """


@app.get("/settings", response_class=HTMLResponse)
def settings_page():
    return """
    <html>
    <head>
        <title>Settings</title>

        <style>
            body {
                margin: 0;
                font-family: Arial;
                display: flex;
                height: 100vh;
            }

            /* 🔥 المستطيل الرمادي */
            .left {
                width: 25%;
                background: #e5e5e5;
                display: flex;
                flex-direction: column;
                align-items: center;
                padding-top: 20px;
            }

            .title {
                background: black;
                color: white;
                padding: 12px 30px;
                border-radius: 20px;
                margin-bottom: 20px;
            }

            .btn {
                width: 210px;
                padding: 15px 0;
                border-radius: 20px;
                border: 2px solid black;
                text-align: center;
                cursor: pointer;
                background: white;
                font-size: 16px;
                margin: 10px 0;
            }

            .btn:hover {
                background: #ddd;
            }

            .right {
                width: 75%;
            }
        </style>
    </head>

    <body>

        <div class="left">

            <div class="title">User: admin</div>

            <div class="btn" onclick="goTheme()">Theme</div>

            <div class="btn" onclick="goEditMenu()">Edit Menu</div>

            <div class="btn" onclick="goDevice()">Add Device</div>

            <div class="btn" onclick="goBack()">Back</div>

        </div>

        <div class="right"></div>

        <script>

        function goTheme() {
            alert("Coming soon");
        }

        function goEditMenu() {
            window.location.href = "/edit-menu";
        }

        function goDevice() {
            alert("Coming soon");
        }

        function goBack() {
            window.location.href = "/";
        }

        </script>

    </body>
    </html>
    """


@app.get("/edit-menu", response_class=HTMLResponse)
def edit_menu():
    return """
    <html>
    <head>
        <title>Edit Menu</title>

        <style>
            body {
                margin: 0;
                font-family: Arial;
                display: flex;
                height: 100vh;
            }

            .left {
                width: 260px;              
                background: #e5e5e5;
            
                position: fixed;
                left: 0;
                top: 0;
                height: 100vh;
            
                display: flex;
                flex-direction: column;
                align-items: center;
                padding-top: 20px;
            }

            .title {
                background: black;
                color: white;
                padding: 12px 30px;
                border-radius: 20px;
                margin-bottom: 20px;
            }

            .tab-btn, .action-btn {
                width: 180px;
                padding: 10px;
                margin: 5px;
                border-radius: 15px;
                border: 2px solid black;
                text-align: center;
                cursor: pointer;
                background: white;
            }

            .tab-btn.active {
                background: #ccc;
            }

            .action-btn {
                background: #eee;
                color: #999;
            }
            #saveBtn:hover {
                background: #6fa58c;
                color: white;
                border: 2px solid black;
            }
            
            #cancelBtn:hover {
                background: #d9534f;
                color: white;
                border: 2px solid black;
            }

            .action-btn.active {
                background: white;
                color: black;
            }

            .back-btn {
                margin-top: auto;
                margin-bottom: 20px;
                width: 180px;
                padding: 10px;
                border-radius: 15px;
                border: 2px solid black;
                background: white;
                cursor: pointer;
            }

            .right {
                margin-left: 260px;   /* نفس عرض اليسار */
                padding: 20px;
            }

            /* 🔥 رجعنا grid */
            .grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, 140px);
                gap: 15px;
            }

            .card {
                width: 140px;
                height: 140px;
                border: 2px solid black;
                border-radius: 15px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: #f5f5f5;
                cursor: pointer;
                touch-action: none;
            }

            .card.selected {
                background: #6fa58c;
                color: white;
            }
            .placeholder {
                width: 140px;
                height: 140px;
                border: 2px dashed #6fa58c;
                border-radius: 15px;
            }
            .card {
                width: 140px;
                height: 140px;
            
                border: 2px solid black;
                border-radius: 15px;
            
                display: flex;
                align-items: center;
                justify-content: center;
            
                text-align: center;   /* 🔥 مهم */
            
                background: #f5f5f5;
                cursor: default;
            }
        </style>
    </head>

    <body>

        <div class="left">

            <div class="title">Edit Menu</div>

            <div class="tab-btn active" onclick="setTab('categories', this)">Categories</div>
            <div class="tab-btn" onclick="setTab('groups', this)">Groups</div>
            <div class="tab-btn" onclick="setTab('items', this)">Items</div>

            <div class="action-btn" id="deleteBtn"style="margin-top:35px;">Delete</div>
            <div class="action-btn" id="moveBtn">Move</div>
            <div class="action-btn" id="renameBtn">Rename</div>
            <div class="action-btn" id="priceBtn">Edit Price</div>

            <div class="action-btn active" id="addBtn">Add</div>
            <div id="saveBtn" class="action-btn" style="display:none;">Save</div>
            <div id="cancelBtn" class="action-btn" style="display:none;">Cancel</div>
            <div id="renameBox" style="
                display:none;
                margin-top:10px;
                width:180px;
                background:white;
                border:2px solid black;
                border-radius:15px;
                padding:10px;
                text-align:center;
            ">
                <input id="renameInput2" type="text" placeholder="New name"
                    style="width:100%; padding:5px; margin-bottom:10px; border-radius:8px; border:1px solid #ccc;">
                
                <button id="renameSave" style="margin:3px;">OK</button>
                <button id="renameCancel" style="margin:3px;">Cancel</button>
            </div>
            <div id="addBox" style="
                display:none;
                margin-top:10px;
                width:180px;
                background:white;
                border:2px solid black;
                border-radius:15px;
                padding:10px;
                text-align:center;
            ">
                <input id="addInput" type="text" placeholder="Group name"
                    style="width:100%; padding:5px; margin-bottom:10px; border-radius:8px; border:1px solid #ccc;">
                
                <button id="addSave">OK</button>
                <button id="addCancel">Cancel</button>
            </div>
            <div id="moveBox" style="
                display:none;
                margin-top:10px;
                width:180px;
                background:white;
                border:2px solid black;
                border-radius:15px;
                padding:10px;
                text-align:center;
            ">
                <div style="margin-bottom:10px; font-weight:bold;">Move</div>
            
                <button id="moveUp">⬆</button>
                <button id="moveDown">⬇</button>
            </div>           
                        <div class="back-btn" onclick="goBack()">Back</div>

        </div>

        <div class="right" id="content"></div>
        <div id="popup" style="
            position: absolute;
            display: none;
            background: white;
            border: 2px solid black;
            padding: 15px;
            border-radius: 10px;
            z-index: 1000;
        ">
            <input id="renameInput" type="text" placeholder="New name"><br><br>
            <button id="renameOkBtn">OK</button>
        </div>


        <script>
        
        let selectedItem = null;
        let selectedItemType = null;
        let selectedCategoryId = null;
        let selectedGroupId = null;
        let pendingName = null;
        let currentTab = "categories";
        

        function setTab(tab, el) {
        
            currentTab = tab;

            const addBtn = document.getElementById("addBtn");
            
            if (tab === "groups") {
                addBtn.classList.add("active");
            } else {
                addBtn.classList.remove("active");
            }
        
            document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
            el.classList.add("active");
        
            selectedItem = null;
            selectedId = null;
        
            updateActions();
        
            if (tab === "categories") loadCategories();
            else if (tab === "groups") loadGroups();
            else if (tab === "items") loadItems();
        }
        
        async function loadGroups() {
        
            const res = await fetch('/categories');
            const categories = await res.json();
        
            let html = '';
        
            for (let c of categories) {
        
                const res2 = await fetch(`/groups/${c.id}`);
                const groups = await res2.json();
        
                html += `
                    <div style="margin-bottom:30px;">
        
                        <!-- 🔥 Category -->
                        <div class="card" 
                             data-id="${c.id}" 
                             onclick="selectItem(this)"
                             style="margin-bottom:10px; font-weight:bold;">
                            ${c.name}
                        </div>
        
                        <!-- 🔥 Groups -->
                        <div class="grid">
                `;
        
                groups.forEach(g => {
                    html += `
                        <div class="card" data-id="${g.id}" onclick="selectItem(this)">
                            ${g.name}
                        </div>
                    `;
                });
        
                html += `
                        </div>
                    </div>
                `;
            }
        
            document.getElementById("content").innerHTML = html;
        }
        
        async function loadCategories() {
        
            const res = await fetch('/categories');
            const data = await res.json();
        
            let html = '<div class="grid" style="margin-left:100px;">';
        
            data.forEach(c => {
                html += `
                    <div class="card" data-id="${c.id}" onclick="selectItem(this)">
                        ${c.name}
                    </div>
                `;
            });
        
            html += '</div>';
        
            document.getElementById("content").innerHTML = html;
        }
        
        function loadItems() {
            document.getElementById("content").innerHTML = "<h2>Items</h2>";
        }
        
        function selectItem(el) {
            
            document.querySelectorAll(".card").forEach(c => c.classList.remove("selected"));
        
            el.classList.add("selected");
        
            selectedItem = true;
            selectedId = el.getAttribute("data-id");
            
            // 🔥 نحدد نوع العنصر
            if (currentTab === "groups") {
                if (el.parentElement.classList.contains("grid")) {
                    // هذا Group
                    selectedItemType = "group";
                } else {
                    // هذا Category
                    selectedItemType = "category";
                }
            }
        
            updateActions();
        }
        
        function updateActions() {
        
            const deleteBtn = document.getElementById("deleteBtn");
            const renameBtn = document.getElementById("renameBtn");
            const addBtn = document.getElementById("addBtn");
            const addBtn = document.getElementById("moveBtn");

            // 🔥 داخل Groups
            if (currentTab === "groups") {
            
                if (selectedItemType === "category") {
                    // Category → فقط Add
                    deleteBtn.classList.remove("active");
                    renameBtn.classList.remove("active");
                    addBtn.classList.add("active");
            
                } else if (selectedItemType === "group") {
                    // Group → فقط تعديل
                    deleteBtn.classList.add("active");
                    renameBtn.classList.add("active");
                    addBtn.classList.remove("active");
                    moveBtn.classList.remove("active)
            
                } else {
                    // ولا شي محدد
                    deleteBtn.classList.remove("active");
                    renameBtn.classList.remove("active");
                    addBtn.classList.remove("active");
                }
            
            } else {
                // باقي التابات (خليها مثل قبل)
                const buttons = ["deleteBtn", "renameBtn"];
            
                buttons.forEach(id => {
                    const btn = document.getElementById(id);
            
                    if (selectedItem) btn.classList.add("active");
                    else btn.classList.remove("active");
                });
            
                addBtn.classList.remove("active");
            }
        }
        
        function goBack() {
            window.location.href = "/settings";
        }
        
        window.onload = function () {
        
            loadCategories();
        
            // DELETE
            document.getElementById("deleteBtn").onclick = async function () {
            
                if (!selectedId) return;
            
                // 🔥 إذا Group
                if (currentTab === "groups" && selectedItemType === "group") {
            
                    await fetch(`/delete-group/${selectedId}`, {
                        method: "DELETE"
                    });
            
                    loadGroups();
                }
            
                // 🔥 إذا Category
                else {
            
                    await fetch(`/delete-category/${selectedId}`, {
                        method: "DELETE"
                    });
            
                    loadCategories();
                }
            
                // 🔥 reset الحالة
                selectedItem = null;
                selectedItemType = null;
                selectedId = null;
            
                updateActions();
            };
        
            // RENAME
            document.getElementById("renameBtn").onclick = function () {
            
                if (!selectedId) return;
            
                document.getElementById("renameBox").style.display = "block";
                document.getElementById("renameInput2").value = "";
            };
        
            document.getElementById("renameOkBtn").onclick = function () {
        
                const val = document.getElementById("renameInput").value;
        
                if (!val) return;
        
                pendingName = val;
        
                document.getElementById("popup").style.display = "none";
        
                document.getElementById("saveBtn").style.display = "block";
                document.getElementById("cancelBtn").style.display = "block";
            };
        
            document.getElementById("saveBtn").onclick = async function () {
        
                if (!pendingName) return;
        
                await fetch(`/rename-category/${selectedId}`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({ name: pendingName })
                });
        
                pendingName = null;
        
                document.getElementById("saveBtn").style.display = "none";
                document.getElementById("cancelBtn").style.display = "none";
        
                loadCategories();
            };
        
            document.getElementById("cancelBtn").onclick = function () {
        
                pendingName = null;
        
                document.getElementById("saveBtn").style.display = "none";
                document.getElementById("cancelBtn").style.display = "none";
            };
        
            document.getElementById("addBtn").onclick = function () {
            
                if (currentTab !== "groups" || selectedItemType !== "category") return;
            
                document.getElementById("addBox").style.display = "block";
                document.getElementById("addInput").value = "";
            };
            
            document.getElementById("addSave").onclick = function () {
            
                const name = document.getElementById("addInput").value;
            
                if (!name) return;
            
                fetch("/add-group", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({
                        name: name,
                        category_id: selectedId
                    })
                }).then(() => {
            
                    document.getElementById("addBox").style.display = "none";
            
                    selectedItem = null;
                    selectedItemType = null;
                    selectedId = null;
            
                    loadGroups();
                    updateActions();
                });
            };

            document.getElementById("addCancel").onclick = function () {
                document.getElementById("addBox").style.display = "none";
            };


            document.getElementById("renameSave").onclick = async function () {
            
                const val = document.getElementById("renameInput2").value;
            
                if (!val) return;
            
                // 🔥 الحل هون
                if (currentTab === "groups" && selectedItemType === "group") {
            
                    await fetch(`/rename-group/${selectedId}`, {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({ name: val })
                    });
            
                } else {
            
                    await fetch(`/rename-category/${selectedId}`, {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({ name: val })
                    });
                }
            
                document.getElementById("renameBox").style.display = "none";
            
                if (currentTab === "groups") {
                    loadGroups();
                } else {
                    loadCategories();
                }
            };
            document.getElementById("renameCancel").onclick = function () {
            
                document.getElementById("renameBox").style.display = "none";
            };


            document.getElementById("moveBtn").onclick = function () {
            
                if (currentTab !== "groups" || selectedItemType !== "group") return;
            
                document.getElementById("moveBox").style.display = "block";
            };
            
            document.getElementById("moveUp").onclick = async function () {
            
                console.log("UP CLICK");

                if (!selectedId) return;
            
                await fetch("/move-group", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        group_id: selectedId,
                        direction: "up"
                    })
                });
            
                loadGroups();
            };
            
            document.getElementById("moveDown").onclick = async function () {
            
                if (!selectedId) return;
            
                await fetch("/move-group", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        group_id: selectedId,
                        direction: "down"
                    })
                });
            
                loadGroups();
            };

        };
        </script>

    </body>
    </html>
    """

@app.get("/edit-categories", response_class=HTMLResponse)
def edit_categories():

    db = SessionLocal()
    categories = db.query(Category).all()
    db.close()

    html = ""

    for c in categories:
        html += f'''
        <div class="card" onclick="selectItem(this, {c.id})">
            {c.name}
        </div>
        '''

    return html





@app.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request, user=Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403)

    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "user": user
        }
    )