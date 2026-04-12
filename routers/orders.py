from fastapi import APIRouter, Body, HTTPException, Depends
from fastapi.responses import HTMLResponse

from database import SessionLocal
from models import Order, OrderItem, Table, MenuItem, Group
from datetime import datetime

import socket

from sign_in.dependencies import get_current_user 

router = APIRouter()

def print_to_printer(ip, text):
    import socket

    try:
        port = 9100  # البورت الخاص بالطابعات الحرارية

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)  # حتى ما يعلق إذا الطابعة ما ردت

        s.connect((ip, port))

        # مهم: بعض الطابعات بدها encoding بسيط
        s.sendall(text.encode("cp864"))

        s.close()

        print("✅ Printed successfully")

    except Exception as e:
        print("❌ Printer Error:", e)


@router.get("/kitchen-print", response_class=HTMLResponse)
def kitchen_print():

    db = SessionLocal()

    # 🔥 فقط الطلبات pending
    orders = db.query(OrderItem).join(Order).filter(
        Order.status == "pending"
    ).all()

    now = datetime.now()

    rows = ""
    printed_orders_ids = set()

    for o in orders:
        if o.item.section == "kitchen":

            rows += f"""
            <div class="item">
                <span>{o.item.name}</span>
                <span>x{o.quantity}</span>
            </div>
            """

            printed_orders_ids.add(o.order_id)

    # 🔥 تحديث حالة الطلبات بعد الطباعة
    for order_id in printed_orders_ids:
        order = db.query(Order).filter(Order.id == order_id).first()
        if order:
            order.status = "printed"

    db.commit()
    db.close()

    return f"""
    <html>
    <head>
        <style>
            body {{
                width: 280px;
                font-family: monospace;
                padding: 10px;
            }}

            .center {{
                text-align: center;
            }}

            .title {{
                font-size: 18px;
                font-weight: bold;
                margin: 10px 0;
            }}

            .line {{
                border-top: 1px dashed black;
                margin: 8px 0;
            }}

            .info {{
                font-size: 14px;
                margin: 3px 0;
            }}

            .item {{
                display: flex;
                justify-content: space-between;
                font-size: 16px;
                margin: 5px 0;
            }}

            .big {{
                font-size: 20px;
                font-weight: bold;
            }}
        </style>
    </head>

    <body onload="window.print()">

        <div class="center">
            <div>Rustica Resto Cafe</div>
            <div class="info">Kitchen Order</div>
        </div>

        <div class="title center">
            Orders
        </div>

        <div class="info">Printed At: {now.strftime("%Y/%m/%d %I:%M %p")}</div>

        <div class="line"></div>

        {rows}

        <div class="line"></div>

        <div class="center big">NEW</div>

        <div class="center" style="margin-top:10px;">
            ---- END ----
        </div>

    </body>
    </html>
    """    

@router.get("/kitchen")
def kitchen_orders():
    db = SessionLocal()

    orders = db.query(OrderItem).all()

    result = []

    for item in orders:
        if item.item.section == "kitchen":
            result.append({
                "table": item.order.table.id,
                "item": item.item.name,
                "qty": item.quantity
            })

    db.close()
    return result


@router.get("/bar")
def bar_orders():
    db = SessionLocal()

    orders = db.query(OrderItem).all()

    result = []

    for item in orders:
        if item.item.section == "bar":
            result.append({
                "table": item.order.table.id,
                "item": item.item.name,
                "qty": item.quantity
            })

    db.close()
    return result


@router.get("/shisha")
def shisha_orders():
    db = SessionLocal()

    orders = db.query(OrderItem).all()

    result = []

    for item in orders:
        if item.item.section == "shisha":
            result.append({
                "table": item.order.table.id,
                "item": item.item.name,
                "qty": item.quantity
            })

    db.close()
    return result


@router.post("/reserve/{table_id}")
def reserve_table(table_id: int, data: dict = {}):
    db = SessionLocal()

    table = db.query(Table).filter(Table.id == table_id).first()

    if not table:
        return {"error": "Table not found"}

    if table.status == "reserved":
        table.status = "free"
        table.note = None
    else:
        table.status = "reserved"
        table.note = data.get("note")

    db.commit()
    db.close()

    return {"message": "ok"}


@router.get("/note/{table_id}")
def get_note(table_id: int):
    db = SessionLocal()

    table = db.query(Table).filter(Table.id == table_id).first()

    db.close()

    return {
        "table": table_id,
        "note": table.note if table else None
    }

@router.post("/update-note/{table_id}")
def update_note(table_id: int, data: dict):
    db = SessionLocal()

    table = db.query(Table).filter(Table.id == table_id).first()

    if not table:
        return {"error": "Table not found"}

    table.note = data.get("note")

    db.commit()
    db.close()

    return {"message": "note updated"}

@router.post("/update-discount/{table_id}")
def update_discount(table_id: int, data: dict):
    db = SessionLocal()

    table = db.query(Table).filter(Table.id == table_id).first()

    if not table:
        return {"error": "Table not found"}

    table.discount = data.get("discount", 0)

    db.commit()
    db.close()

    return {"message": "ok"}



@router.post("/orders")
def create_order(data: dict):
    db = SessionLocal()

    table_id = data.get("table_id")
    items = data.get("items", [])

    if not table_id or not items:
        return {"error": "Missing data"}

    # إنشاء order جديد (متل ما أنت بدك)
    order = Order(table_id=table_id)
    db.add(order)
    db.commit()
    db.refresh(order)

    order_id = order.id

    # 🖨️ إعداد الطابعات
    kitchen_ip = "192.168.223.1"
    bar_ip = "192.168.1.51"
    shisha_ip = "192.168.1.52"

    kitchen_items = []
    bar_items = []
    shisha_items = []

    # 🔥 تحسين الأداء: جلب كل العناصر مرة وحدة
    item_ids = [i["item_id"] for i in items]

    db_items = db.query(MenuItem).filter(MenuItem.id.in_(item_ids)).all()
    items_map = {i.id: i for i in db_items}

    # 🔥 معالجة الطلب
    for item in items:

        db_item = items_map.get(item["item_id"])

        if not db_item:
            continue  # حماية من أي ID غلط

        line = f"{db_item.name} x{item['quantity']}"

        # توزيع حسب القسم
        if db_item.section == "kitchen":
            kitchen_items.append(line)

        elif db_item.section == "bar":
            bar_items.append(line)

        elif db_item.section == "shisha":
            shisha_items.append(line)

        # تخزين في DB
        db.add(OrderItem(
            order_id=order_id,
            item_id=item["item_id"],
            quantity=item["quantity"]
        ))

    # تحديث حالة الطاولة
    table = db.query(Table).filter(Table.id == table_id).first()
    if table:
        table.status = "occupied"

    db.commit()

    # 🖨️ بناء نص الطباعة
    def build_text(title, items_list):
        text = f"\n{title}\nTable {table_id}\n\n"
        for i in items_list:
            text += i + "\n"
        text += "\n--- END ---\n"
        return text

    # 🖨️ طباعة
    if kitchen_items:
        print_to_printer(kitchen_ip, build_text("Kitchen Order", kitchen_items))

    if bar_items:
        print_to_printer(bar_ip, build_text("Bar Order", bar_items))

    if shisha_items:
        print_to_printer(shisha_ip, build_text("Shisha Order", shisha_items))

    db.close()

    return {"message": "Order created", "order_id": order_id}


@router.get("/test-print")
def test_print():

    text = "\x1b@\n"  # reset printer
    text += "HELLO\n"
    text += "TEST PRINT\n"
    text += "----------------\n"
    text += "\n\n\n"

    print_to_printer("192.168.8.101", text)

    return {"message": "sent"}


@router.get("/groups/{category_id}")
def get_groups(category_id: int):

    db = SessionLocal()

    groups = (
        db.query(Group)
        .filter(Group.category_id == category_id)
        .order_by(Group.position.asc())
        .all()
    )

    return [
        {
            "id": g.id,
            "name": g.name
        }
        for g in groups
    ]



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


