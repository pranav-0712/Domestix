"""
Domestix - Smart Household Management Application
Backend Engine: FastAPI REST API & SQLite Controller
Team Members:
  - Saee Takale (Roll No: 5185)
  - Ayusha Kale (Roll No: 3205)
  - Pranav Joshi (Roll No: 5208)
  - Vaishnavi Thite (Roll No: 5188)
"""

import os
import re
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from .database import get_db, init_db, hash_password, offset_date
from .models import (
    UserRegister, UserLogin, InventoryCreate, InventoryUpdate,
    ShoppingCreate, ApplianceCreate, BillCreate, OCRRequest, AICoachRequest
)

# Initialize Database
init_db()

app = FastAPI(
    title="Domestix Smart Household Management API",
    description="Unified platform for inventory, shopping, maintenance, warranties and recurring tasks",
    version="2.0.0"
)

# Enable CORS for local testing and cross-origin frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Helper function to generate storage tips
def generate_storage_tip(name: str, category: str) -> str:
    n = name.lower()
    if "milk" in n:
        return "Store on middle refrigerator shelf at 4°C, avoid door shelves."
    elif "paneer" in n:
        return "Submerge block in fresh cold water in an airtight container; change water every 2 days."
    elif "bread" in n:
        return "Seal with a clip in a dry bread box, or freeze sliced portions in humid weather."
    elif any(k in n for k in ["oat", "rice", "dal", "flour", "atta"]):
        return "Store in an airtight glass/steel container with a bay leaf in a cool, dark pantry."
    elif "egg" in n:
        return "Keep in original carton on main shelf, pointed ends downward."
    elif category == "Medicine":
        return "Store in original blister pack inside a dry medicine box away from direct light."
    elif category == "Perishables":
        return "Wrap in a breathable paper towel and keep in the crisper drawer."
    elif category == "Cleaning":
        return "Keep tightly sealed in a cool, child-safe utility cabinet."
    return "Store tightly sealed in a cool, dry place away from heat."

# Helper to calculate days diff
def days_until(date_str: str) -> int:
    try:
        target = datetime.strptime(date_str, "%Y-%m-%d").date()
        today = datetime.now().date()
        return (target - today).days
    except Exception:
        return 0

# ============================================================================
# 1. SYSTEM & TEAM INFORMATION (PBL Slides Reference)
# ============================================================================

@app.get("/api/system/info")
def get_system_info():
    return {
        "project": "SMART HOUSEHOLD MANAGEMENT APPLICATION (Domestix)",
        "tagline": "A unified platform for inventory, shopping, maintenance, warranties and recurring tasks",
        "version": "2.0.0",
        "team_members": [
            {"name": "Saee Takale", "roll_no": "5185", "role": "Project Lead / Analyst"},
            {"name": "Ayusha Kale", "roll_no": "3205", "role": "Frontend Developer"},
            {"name": "Pranav Joshi", "roll_no": "5208", "role": "Backend / Database Developer"},
            {"name": "Vaishnavi Thite", "roll_no": "5188", "role": "OCR & Notification Developer"}
        ],
        "architecture_layers": [
            {"layer": 1, "name": "User Layer", "components": "Web & Mobile Dashboard, Bill Scanner, Handwriting Pad, Barcode Input"},
            {"layer": 2, "name": "Application Layer", "components": "Product Inventory, Shopping List, Maintenance Scheduler, Warranty Tracker, Bills"},
            {"layer": 3, "name": "Service Layer", "components": "OCR / Barcode Extraction Engine, Reminder Engine, Authentication REST API"},
            {"layer": 4, "name": "Data Layer", "components": "SQLite3 Database, Receipt Records, Task Status, User Settings"},
            {"layer": 5, "name": "Output Layer", "components": "Alerts, Upcoming Tasks, Overdue Items, Waste Analytics, AI Rescue Recipes"}
        ],
        "status": "Online",
        "server_time": datetime.now().isoformat()
    }

# ============================================================================
# 2. AUTHENTICATION & USERS
# ============================================================================

@app.post("/api/auth/register")
def register(user: UserRegister):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (user.username.strip().lower(),))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Username already exists")

    pwd_hash = hash_password(user.password)
    cursor.execute("""
        INSERT INTO users (username, password_hash, full_name, role, roll_no, avatar_color)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user.username.strip().lower(), pwd_hash, user.full_name, user.role, user.roll_no, user.avatar_color))
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()

    return {
        "success": True,
        "message": "Account created successfully",
        "user": {
            "id": user_id,
            "username": user.username.strip().lower(),
            "full_name": user.full_name,
            "role": user.role,
            "roll_no": user.roll_no,
            "avatar_color": user.avatar_color,
            "token": f"token-{user_id}-{hash_password(user.username)[:10]}"
        }
    }

@app.post("/api/auth/login")
def login(creds: UserLogin):
    conn = get_db()
    cursor = conn.cursor()
    pwd_hash = hash_password(creds.password)
    cursor.execute("""
        SELECT id, username, full_name, role, roll_no, avatar_color
        FROM users
        WHERE username = ? AND password_hash = ?
    """, (creds.username.strip().lower(), pwd_hash))
    user = cursor.fetchone()
    conn.close()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    return {
        "success": True,
        "message": "Login successful",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "full_name": user["full_name"],
            "role": user["role"],
            "roll_no": user["roll_no"],
            "avatar_color": user["avatar_color"],
            "token": f"token-{user['id']}-{hash_password(user['username'])[:10]}"
        }
    }

@app.get("/api/auth/users")
def list_users():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, full_name, role, roll_no, avatar_color FROM users ORDER BY id ASC")
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"users": users}

# ============================================================================
# 3. PRODUCT INVENTORY & EXPIRY TRACKING
# ============================================================================

@app.get("/api/inventory")
def get_inventory(category: Optional[str] = None, search: Optional[str] = None):
    conn = get_db()
    cursor = conn.cursor()
    query = "SELECT * FROM inventory WHERE 1=1"
    params = []

    if category and category.upper() != "ALL":
        query += " AND category = ?"
        params.append(category)

    if search:
        query += " AND name LIKE ?"
        params.append(f"%{search}%")

    query += " ORDER BY expiry_date ASC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    items = []
    for r in rows:
        d = dict(r)
        d["days_left"] = days_until(d["expiry_date"])
        if d["days_left"] < 0:
            d["status"] = "expired"
        elif d["days_left"] <= 4:
            d["status"] = "expiring_soon"
        else:
            d["status"] = "safe"
        items.append(d)

    return {"inventory": items, "count": len(items)}

@app.post("/api/inventory")
def add_inventory(item: InventoryCreate):
    tip = item.storage_tip or generate_storage_tip(item.name, item.category)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO inventory (user_id, name, category, quantity, unit, price, expiry_date, storage_tip)
        VALUES (1, ?, ?, ?, ?, ?, ?, ?)
    """, (item.name.strip(), item.category, item.quantity, item.unit, item.price, item.expiry_date, tip))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    return {
        "success": True,
        "message": f"Added {item.name} to inventory",
        "item": {
            "id": new_id,
            "name": item.name,
            "category": item.category,
            "quantity": item.quantity,
            "unit": item.unit,
            "price": item.price,
            "expiry_date": item.expiry_date,
            "storage_tip": tip
        }
    }

@app.put("/api/inventory/{item_id}")
def update_inventory(item_id: int, item: InventoryUpdate):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM inventory WHERE id = ?", (item_id,))
    existing = cursor.fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Item not found")

    name = item.name if item.name is not None else existing["name"]
    category = item.category if item.category is not None else existing["category"]
    quantity = item.quantity if item.quantity is not None else existing["quantity"]
    unit = item.unit if item.unit is not None else existing["unit"]
    price = item.price if item.price is not None else existing["price"]
    expiry_date = item.expiry_date if item.expiry_date is not None else existing["expiry_date"]
    tip = item.storage_tip if item.storage_tip is not None else (existing["storage_tip"] or generate_storage_tip(name, category))

    cursor.execute("""
        UPDATE inventory
        SET name = ?, category = ?, quantity = ?, unit = ?, price = ?, expiry_date = ?, storage_tip = ?
        WHERE id = ?
    """, (name, category, quantity, unit, price, expiry_date, tip, item_id))
    conn.commit()
    conn.close()

    return {"success": True, "message": "Item updated successfully"}

@app.delete("/api/inventory/{item_id}")
def delete_inventory(item_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM inventory WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return {"success": True, "message": "Item deleted"}

@app.post("/api/inventory/{item_id}/consume")
def consume_inventory(item_id: int, auto_restock: bool = True):
    """
    Marks an item as consumed:
    - Removes it from inventory
    - Logs it in completed task history
    - Optionally creates a replenishment entry in the shopping list
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM inventory WHERE id = ?", (item_id,))
    item = cursor.fetchone()
    if not item:
        conn.close()
        raise HTTPException(status_code=404, detail="Item not found")

    # Remove from inventory
    cursor.execute("DELETE FROM inventory WHERE id = ?", (item_id,))

    # Log in task history
    cursor.execute("""
        INSERT INTO task_history (user_id, title, category, completed_date, completed_by)
        VALUES (1, ?, 'Inventory', ?, 'Household Member')
    """, (f"Consumed {item['name']} ({item['quantity']}{item['unit']})", offset_date(0)))

    # Auto-add to shopping list
    if auto_restock:
        cursor.execute("SELECT id FROM shopping_items WHERE LOWER(name) = LOWER(?)", (item["name"],))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO shopping_items (user_id, name, category, quantity, unit, estimated_price, assigned_to, is_checked)
                VALUES (1, ?, ?, 1.0, ?, ?, 'Kitchen Lead', 0)
            """, (item["name"], item["category"], item["unit"], item["price"]))

    conn.commit()
    conn.close()
    return {"success": True, "message": f"Consumed {item['name']} and scheduled auto-restock"}

# ============================================================================
# 4. SMART SHOPPING LIST
# ============================================================================

@app.get("/api/shopping")
def get_shopping_list():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM shopping_items ORDER BY is_checked ASC, id DESC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return {"shopping_items": rows, "count": len(rows)}

@app.post("/api/shopping")
def add_shopping_item(item: ShoppingCreate):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO shopping_items (user_id, name, category, quantity, unit, estimated_price, assigned_to, is_checked)
        VALUES (1, ?, ?, ?, ?, ?, ?, 0)
    """, (item.name.strip(), item.category, item.quantity, item.unit, item.estimated_price, item.assigned_to))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return {"success": True, "id": new_id, "message": f"Added {item.name} to shopping list"}

@app.patch("/api/shopping/{item_id}/toggle")
def toggle_shopping_item(item_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT is_checked FROM shopping_items WHERE id = ?", (item_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Item not found")

    new_val = 0 if row["is_checked"] else 1
    cursor.execute("UPDATE shopping_items SET is_checked = ? WHERE id = ?", (new_val, item_id))
    conn.commit()
    conn.close()
    return {"success": True, "is_checked": bool(new_val)}

@app.delete("/api/shopping/{item_id}")
def delete_shopping_item(item_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM shopping_items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return {"success": True, "message": "Shopping item deleted"}

@app.post("/api/shopping/checkout")
def checkout_shopping():
    """
    Transfers all checked shopping items into Household Inventory with smart calculated expiry dates.
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM shopping_items WHERE is_checked = 1")
    checked = cursor.fetchall()

    if not checked:
        conn.close()
        return {"success": False, "transferred": 0, "message": "No checked items to checkout"}

    transferred = 0
    for item in checked:
        # Calculate sensible shelf life
        cat = item["category"]
        if cat == "Dairy":
            days = 5
        elif cat == "Perishables":
            days = 7
        elif cat == "Bakery":
            days = 4
        elif cat == "Medicine":
            days = 365
        else:
            days = 90

        exp = offset_date(days)
        tip = generate_storage_tip(item["name"], cat)

        cursor.execute("""
            INSERT INTO inventory (user_id, name, category, quantity, unit, price, expiry_date, storage_tip)
            VALUES (1, ?, ?, ?, ?, ?, ?, ?)
        """, (item["name"], cat, item["quantity"], item["unit"], item["estimated_price"], exp, tip))
        transferred += 1

    # Remove checked items from shopping list
    cursor.execute("DELETE FROM shopping_items WHERE is_checked = 1")

    # Log task
    cursor.execute("""
        INSERT INTO task_history (user_id, title, category, completed_date, completed_by)
        VALUES (1, ?, 'Shopping', ?, 'Household Admin')
    """, (f"Checked out {transferred} items from shopping list into inventory", offset_date(0)))

    conn.commit()
    conn.close()

    return {"success": True, "transferred": transferred, "message": f"Successfully moved {transferred} items to inventory"}

# ============================================================================
# 5. APPLIANCE MAINTENANCE & WARRANTY TRACKER
# ============================================================================

@app.get("/api/appliances")
def get_appliances():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM appliances ORDER BY next_service_date ASC")
    rows = cursor.fetchall()
    conn.close()

    appliances = []
    for r in rows:
        d = dict(r)
        d["warranty_days_left"] = days_until(d["warranty_expiry"])
        d["service_days_left"] = days_until(d["next_service_date"])
        appliances.append(d)

    return {"appliances": appliances, "count": len(appliances)}

@app.post("/api/appliances")
def add_appliance(appliance: ApplianceCreate):
    conn = get_db()
    cursor = conn.cursor()
    sn = appliance.serial_number or f"DOM-{datetime.now().strftime('%M%S')}"
    note = appliance.maintenance_notes or "Periodic performance and filter inspection"

    cursor.execute("""
        INSERT INTO appliances (user_id, name, serial_number, warranty_expiry, next_service_date, maintenance_notes)
        VALUES (1, ?, ?, ?, ?, ?)
    """, (appliance.name.strip(), sn, appliance.warranty_expiry, appliance.next_service_date, note))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    return {"success": True, "id": new_id, "message": f"Appliance {appliance.name} registered"}

@app.post("/api/appliances/{appliance_id}/service")
def log_appliance_service(appliance_id: int):
    """
    Logs maintenance completed and automatically schedules the next service date in +180 days.
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM appliances WHERE id = ?", (appliance_id,))
    appliance = cursor.fetchone()
    if not appliance:
        conn.close()
        raise HTTPException(status_code=404, detail="Appliance not found")

    next_date = offset_date(180)
    cursor.execute("UPDATE appliances SET next_service_date = ? WHERE id = ?", (next_date, appliance_id))

    cursor.execute("""
        INSERT INTO task_history (user_id, title, category, completed_date, completed_by)
        VALUES (1, ?, 'Maintenance', ?, 'Technician / Admin')
    """, (f"Logged periodic service for {appliance['name']}", offset_date(0)))

    conn.commit()
    conn.close()
    return {"success": True, "next_service_date": next_date, "message": f"Service logged! Next service due: {next_date}"}

@app.delete("/api/appliances/{appliance_id}")
def delete_appliance(appliance_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM appliances WHERE id = ?", (appliance_id,))
    conn.commit()
    conn.close()
    return {"success": True, "message": "Appliance record deleted"}

# ============================================================================
# 6. RECURRING UTILITIES & BILL PAYMENTS
# ============================================================================

@app.get("/api/bills")
def get_bills():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bills ORDER BY due_date ASC")
    rows = cursor.fetchall()
    conn.close()

    bills = []
    for r in rows:
        d = dict(r)
        d["days_left"] = days_until(d["due_date"])
        bills.append(d)

    return {"bills": bills, "count": len(bills)}

@app.post("/api/bills")
def add_bill(bill: BillCreate):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO bills (user_id, name, category, amount, due_date, assigned_to, status)
        VALUES (1, ?, ?, ?, ?, ?, ?)
    """, (bill.name.strip(), bill.category, bill.amount, bill.due_date, bill.assigned_to, bill.status))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    return {"success": True, "id": new_id, "message": f"Bill {bill.name} added"}

@app.post("/api/bills/{bill_id}/pay")
def pay_bill(bill_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bills WHERE id = ?", (bill_id,))
    bill = cursor.fetchone()
    if not bill:
        conn.close()
        raise HTTPException(status_code=404, detail="Bill not found")

    cursor.execute("UPDATE bills SET status = 'Paid' WHERE id = ?", (bill_id,))
    cursor.execute("""
        INSERT INTO task_history (user_id, title, category, completed_date, completed_by)
        VALUES (1, ?, 'Bills', ?, ?)
    """, (f"Paid {bill['name']} (₹{bill['amount']})", offset_date(0), bill["assigned_to"] or "Household Member"))

    conn.commit()
    conn.close()
    return {"success": True, "message": f"Marked {bill['name']} as Paid"}

@app.delete("/api/bills/{bill_id}")
def delete_bill(bill_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM bills WHERE id = ?", (bill_id,))
    conn.commit()
    conn.close()
    return {"success": True, "message": "Bill record deleted"}

# ============================================================================
# 7. UNIFIED TASK LIFECYCLE & NOTIFICATIONS (Upcoming / Overdue / Completed)
# ============================================================================

@app.get("/api/tasks")
def get_tasks():
    conn = get_db()
    cursor = conn.cursor()

    # 1. Inventory Expiry Tasks
    cursor.execute("SELECT * FROM inventory")
    inv_rows = cursor.fetchall()

    # 2. Unpaid Bills
    cursor.execute("SELECT * FROM bills WHERE status = 'Unpaid'")
    bill_rows = cursor.fetchall()

    # 3. Appliances
    cursor.execute("SELECT * FROM appliances")
    app_rows = cursor.fetchall()

    # 4. Completed Tasks
    cursor.execute("SELECT * FROM task_history ORDER BY id DESC LIMIT 20")
    completed_rows = [dict(r) for r in cursor.fetchall()]

    conn.close()

    upcoming = []
    overdue = []

    # Process Inventory
    for i in inv_rows:
        diff = days_until(i["expiry_date"])
        if diff < 0:
            overdue.append({
                "type": "inventory",
                "id": i["id"],
                "title": f"Expired Stock: {i['name']}",
                "detail": f"Expired on {i['expiry_date']} ({abs(diff)}d ago)",
                "badge": "EXPIRED",
                "color": "rose",
                "action": "consume"
            })
        elif diff <= 4:
            upcoming.append({
                "type": "inventory",
                "id": i["id"],
                "title": f"Consume {i['name']} ({i['quantity']}{i['unit']})",
                "detail": f"Expires in {diff} days ({i['expiry_date']})",
                "badge": "EXPIRING SOON",
                "color": "amber",
                "action": "consume"
            })

    # Process Bills
    for b in bill_rows:
        diff = days_until(b["due_date"])
        if diff < 0:
            overdue.append({
                "type": "bill",
                "id": b["id"],
                "title": f"Overdue Bill: {b['name']} (₹{b['amount']})",
                "detail": f"Was due on {b['due_date']} • Assigned: {b['assigned_to']}",
                "badge": "BILL OVERDUE",
                "color": "rose",
                "action": "pay"
            })
        else:
            upcoming.append({
                "type": "bill",
                "id": b["id"],
                "title": f"Pay {b['name']} (₹{b['amount']})",
                "detail": f"Due on {b['due_date']} ({diff}d left) • Assigned: {b['assigned_to']}",
                "badge": "BILL DUE",
                "color": "indigo",
                "action": "pay"
            })

    # Process Appliances
    for a in app_rows:
        diff = days_until(a["next_service_date"])
        if diff < 0:
            overdue.append({
                "type": "appliance",
                "id": a["id"],
                "title": f"Overdue Service: {a['name']}",
                "detail": f"Scheduled for {a['next_service_date']} • {a['maintenance_notes']}",
                "badge": "SERVICE OVERDUE",
                "color": "rose",
                "action": "service"
            })
        elif diff <= 30:
            upcoming.append({
                "type": "appliance",
                "id": a["id"],
                "title": f"Upcoming Maintenance: {a['name']}",
                "detail": f"Due on {a['next_service_date']} ({diff}d left) • {a['maintenance_notes']}",
                "badge": "MAINTENANCE",
                "color": "emerald",
                "action": "service"
            })

    return {
        "upcoming": upcoming,
        "overdue": overdue,
        "completed": completed_rows,
        "counts": {
            "upcoming": len(upcoming),
            "overdue": len(overdue),
            "completed": len(completed_rows)
        }
    }

# ============================================================================
# 8. OCR & BILL/LABEL PARSING ENGINE
# ============================================================================

@app.post("/api/ocr/parse")
def parse_ocr(req: OCRRequest):
    """
    Advanced multi-format receipt and product label OCR parser:
    - Extracts product name, price, quantity, expiry date, manufacturing date
    - Handles Indian & international formats: DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY, DD Mon YYYY, MM/YYYY, Dot-Matrix
    - Automatically calculates expiry from packaging date + shelf-life duration (e.g. Best Before 6 Months)
    """
    raw_text = (req.text or req.filename or req.user_hint or "").strip()
    upper_text = raw_text.upper()

    MONTH_MAP = {
        "JAN": "01", "FEB": "02", "MAR": "03", "APR": "04", "MAY": "05", "JUN": "06",
        "JUL": "07", "AUG": "08", "SEP": "09", "OCT": "10", "NOV": "11", "DEC": "12"
    }

    all_detected = []
    exp_date = None
    mfg_date = None

    # Normalization helper for dot-matrix text like 'E X P 2 4 / 1 0 / 2 6'
    normalized_text = re.sub(r'(\d)\s+([/\-\.])\s+(\d)', r'\1\2\3', upper_text)
    normalized_text = re.sub(r'([A-Z])\s+([A-Z])\s+([A-Z])', r'\1\2\3', normalized_text)

    # 1. Search for explicitly labeled EXP / USE BY / BEST BEFORE dates
    # e.g., EXP: 24/10/2026, BEST BEFORE 18-11-26, USE BY 22.12.2026
    exp_matches = re.finditer(
        r'(?:EXP(?:IRY)?|USE\s*BY|BEST\s*BEFORE|BB|UBD|EXD)[\s\:\.\-]*(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{2,4})',
        normalized_text
    )
    for m in exp_matches:
        d, mo, y = m.group(1).zfill(2), m.group(2).zfill(2), m.group(3)
        if len(y) == 2:
            y = "20" + y
        date_str = f"{y}-{mo}-{d}"
        exp_date = date_str
        all_detected.append({"type": "EXPIRY", "date": date_str, "raw": m.group(0)})

    # 2. Search for EXP with Month Name: e.g. EXP 24 OCT 2026, 18-NOV-26, BEST BEFORE 15 DEC 2027
    if not exp_date:
        mon_matches = re.finditer(
            r'(?:EXP(?:IRY)?|USE\s*BY|BEST\s*BEFORE|BB)?[\s\:\.\-]*(\d{1,2})[\s\/\-\.](JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)[A-Z]*[\s\/\-\.](\d{2,4})',
            normalized_text
        )
        for m in mon_matches:
            d, mon_str, y = m.group(1).zfill(2), m.group(2), m.group(3)
            mo = MONTH_MAP.get(mon_str, "01")
            if len(y) == 2:
                y = "20" + y
            date_str = f"{y}-{mo}-{d}"
            exp_date = date_str
            all_detected.append({"type": "EXPIRY", "date": date_str, "raw": m.group(0)})
            break

    # 3. Search for MM/YYYY or MM/YY e.g. EXP 10/2026 or EXP 08/27 (common in medicines/cans)
    if not exp_date:
        my_matches = re.finditer(
            r'(?:EXP(?:IRY)?|USE\s*BY|BEST\s*BEFORE|BB)[\s\:\.\-]*(\d{1,2})[\/\-\.](\d{2,4})',
            normalized_text
        )
        for m in my_matches:
            mo, y = m.group(1).zfill(2), m.group(2)
            if 1 <= int(mo) <= 12:
                if len(y) == 2:
                    y = "20" + y
                # End of month
                date_str = f"{y}-{mo}-28"
                exp_date = date_str
                all_detected.append({"type": "EXPIRY_MONTH", "date": date_str, "raw": m.group(0)})
                break

    # 4. Search for Manufacturing / Packaging date (MFG / PKD)
    mfg_matches = re.finditer(
        r'(?:MFG|PKD|PACKED|PACKAGING)[\s\:\.\-]*(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{2,4})',
        normalized_text
    )
    for m in mfg_matches:
        d, mo, y = m.group(1).zfill(2), m.group(2).zfill(2), m.group(3)
        if len(y) == 2:
            y = "20" + y
        date_str = f"{y}-{mo}-{d}"
        mfg_date = date_str
        all_detected.append({"type": "MANUFACTURING", "date": date_str, "raw": m.group(0)})

    # If only manufacturing date is found, check for "BEST BEFORE X MONTHS / DAYS"
    if not exp_date and mfg_date:
        shelf_match = re.search(r'BEST\s*BEFORE\s*(\d+)\s*(MONTH|DAY|YEAR)', normalized_text)
        if shelf_match:
            qty = int(shelf_match.group(1))
            unit = shelf_match.group(2)
            try:
                base_dt = datetime.strptime(mfg_date, "%Y-%m-%d")
                if "MONTH" in unit:
                    calc_dt = base_dt + timedelta(days=qty * 30)
                elif "YEAR" in unit:
                    calc_dt = base_dt + timedelta(days=qty * 365)
                else:
                    calc_dt = base_dt + timedelta(days=qty)
                exp_date = calc_dt.strftime("%Y-%m-%d")
                all_detected.append({"type": "CALCULATED_EXPIRY", "date": exp_date, "raw": f"{shelf_match.group(0)} from {mfg_date}"})
            except Exception:
                pass

    # 5. General fallback date scan (any DD/MM/YYYY in the text)
    if not exp_date:
        gen_matches = re.finditer(r'(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{2,4})', normalized_text)
        for m in gen_matches:
            d, mo, y = m.group(1).zfill(2), m.group(2).zfill(2), m.group(3)
            # Basic sanity check
            if 1 <= int(d) <= 31 and 1 <= int(mo) <= 12:
                if len(y) == 2:
                    y = "20" + y
                if int(y) >= 2024:
                    date_str = f"{y}-{mo}-{d}"
                    exp_date = date_str
                    all_detected.append({"type": "GENERAL_DATE", "date": date_str, "raw": m.group(0)})
                    break

    # Ultimate fallback if no date found at all
    if not exp_date:
        exp_date = offset_date(7)

    # 2. Price Detection (₹, Rs, Rs., or MRP)
    price = 60.0
    match_price = re.search(r'(?:MRP|₹|RS\.?|INR)[\s\:\.\-]*(\d+(?:\.\d{1,2})?)', upper_text)
    if match_price:
        price = float(match_price.group(1))

    # 3. Clean Name & Category Heuristics
    name = raw_text
    # Strip date patterns and prices from name
    name = re.sub(r'(?:EXP|EXPIRY|USE\s*BY|BEST\s*BEFORE|BB|MFG|PKD)[\s\:\.\-]*\d+[\/\-\.]\d+[\/\-\.]\d+', '', name, flags=re.IGNORECASE)
    name = re.sub(r'(?:MRP|₹|RS\.?|INR)[\s\:\.\-]*\d+(?:\.\d{1,2})?', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\b\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}\b', '', name)
    name = re.sub(r'[\r\n\t]+', ' ', name).strip()
    name = re.sub(r'\s{2,}', ' ', name)

    if not name or len(name) < 2:
        name = "Scanned Household Product"

    cat = "Groceries"
    n_lower = (raw_text + " " + name).lower()
    if any(k in n_lower for k in ["milk", "curd", "yogurt", "butter", "cheese", "paneer", "amul", "cream"]):
        cat = "Dairy"
    elif any(k in n_lower for k in ["tomato", "onion", "veg", "spinach", "fruit", "apple", "potato"]):
        cat = "Perishables"
    elif any(k in n_lower for k in ["bread", "bun", "cake", "toast", "biscuit", "rusk", "cookie"]):
        cat = "Bakery"
    elif any(k in n_lower for k in ["tablet", "med", "paracetamol", "syrup", "capsule", "dolo", "crocin"]):
        cat = "Medicine"
    elif any(k in n_lower for k in ["detergent", "soap", "surf", "vim", "clean", "harpic", "shampoo"]):
        cat = "Cleaning"

    return {
        "success": True,
        "extracted": {
            "name": name,
            "category": cat,
            "quantity": 1.0,
            "unit": "pcs",
            "price": price,
            "expiry_date": exp_date,
            "mfg_date": mfg_date,
            "storage_tip": generate_storage_tip(name, cat),
            "source": "Domestix Neural OCR & Expiry Engine"
        },
        "all_detected_dates": all_detected
    }

# ============================================================================
# ============================================================================
# 9. AI HOUSEHOLD COACH & RECIPE OPTIMIZER (Lively Conversational Engine)
# ============================================================================

@app.post("/api/ai/coach")
def ai_coach(req: AICoachRequest):
    """
    Lively, intelligent, conversational household AI Coach:
    - Handles greetings ('hi', 'hello', 'hey', 'good morning', etc.) warmly and naturally
    - Conversational banter, small talk, jokes, kitchen hacks
    - Context-aware recipe suggestions using actual DB inventory items
    - Proactive expiry rescue, budget tips, appliance care, and utility bill tracking
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM inventory ORDER BY expiry_date ASC")
    inv = [dict(r) for r in cursor.fetchall()]
    cursor.execute("SELECT * FROM bills WHERE status = 'Unpaid' ORDER BY due_date ASC")
    unpaid_bills = [dict(r) for r in cursor.fetchall()]
    cursor.execute("SELECT * FROM appliances ORDER BY next_service_date ASC")
    appliances = [dict(r) for r in cursor.fetchall()]
    conn.close()

    expiring_soon = [i for i in inv if days_until(i["expiry_date"]) <= 4 and days_until(i["expiry_date"]) >= 0]
    expired_items = [i for i in inv if days_until(i["expiry_date"]) < 0]
    exp_names = [i["name"] for i in expiring_soon]
    total_val = sum(i.get("price", 0) for i in inv)
    saved_pot = sum(i.get("price", 50) for i in expiring_soon)

    user_query = (req.prompt or "").strip().lower()
    clean_q = re.sub(r'[^\w\s]', '', user_query).strip()

    # 1. GREETINGS & CASUAL OPENERS (e.g. 'hi', 'hello', 'hey', 'good morning', etc.)
    greetings = ["hi", "hello", "hey", "heyy", "hii", "hi there", "hello there", "hola", "namaste", "good morning", "good afternoon", "good evening", "howdy", "sup", "yo"]
    if clean_q in greetings or any(clean_q.startswith(g + " ") for g in ["hi", "hello", "hey", "good morning", "good evening"]):
        exp_text = f"You have <b>{len(expiring_soon)} item(s)</b> ({', '.join(exp_names)}) to use soon." if expiring_soon else "All your perishables are fresh and safe!"
        advice = (
            f"Hello! 👋 Glad to help you with your kitchen and home chores.<br><br>"
            f"I'm your <b>Domestix Household Assistant</b> — here to give you cooking suggestions, food storage tips, and help you keep track of home tasks.<br><br>"
            f"<b>Quick Home Update:</b><br>"
            f"• 📦 <b>Pantry:</b> <b>{len(inv)} items</b> currently in stock.<br>"
            f"• ⏰ <b>Expiry Watch:</b> {exp_text}<br>"
            f"• ⚡ <b>Bills:</b> {len(unpaid_bills)} pending utility payment(s).<br><br>"
            f"Here are a few things you can ask:<br>"
            f"• <i>\"What can I cook for dinner?\"</i><br>"
            f"• <i>\"What's expiring next?\"</i><br>"
            f"• <i>\"Give me a food storage tip\"</i><br>"
            f"• <i>\"How do I save money on groceries?\"</i>"
        )
        return {"success": True, "response": advice, "intent": "greeting", "expiring_items": exp_names}

    # 2. STATUS & HOW ARE YOU
    if any(k in user_query for k in ["how are you", "how r u", "how you doing", "what's up", "whats up"]):
        advice = (
            "I'm doing great, thank you! 😊 Always here to help you manage your household easily.<br><br>"
            f"Your household currently has <b>{len(inv)} pantry items</b> and <b>{len(appliances)} appliances</b> registered.<br>"
            "How can I assist you right now? Hungry, checking groceries, or looking for appliance advice?"
        )
        return {"success": True, "response": advice, "intent": "smalltalk", "expiring_items": exp_names}

    # 3. IDENTITY & CAPABILITIES
    if any(k in user_query for k in ["who are you", "what can you do", "introduce", "what is domestix", "help me"]):
        advice = (
            "🏡 <b>Domestix Household Assistant:</b><br><br>"
            "I'm your digital helper for smart home and kitchen management:<br>"
            "• 🥘 <b>Recipe Suggestions:</b> Practical meal ideas prioritizing ingredients that expire first.<br>"
            "• 🏷️ <b>Expiry Tracking:</b> Reminds you before food items spoil so you save money.<br>"
            "• ❄️ <b>Food Care & Storage:</b> Practical storage tips to keep dairy and bakery fresh longer.<br>"
            "• 🛠️ <b>Home Maintenance:</b> Reminders for AC servicing and monthly utility bills.<br><br>"
            "Feel free to ask any question anytime!"
        )
        return {"success": True, "response": advice, "intent": "identity", "expiring_items": exp_names}

    # 4. HUNGER & RECIPES
    if any(k in user_query for k in ["recipe", "cook", "meal", "hungry", "eat", "dinner", "lunch", "breakfast", "snack"]):
        if exp_names:
            items_str = ", ".join(exp_names[:3])
            advice = (
                f"🥘 <b>Lively Chef Recommendation — Rescue Tonight!</b><br><br>"
                f"You have <b>{items_str}</b> expiring soon. Let's make sure none of that goes to waste!<br><br>"
                f"• <b>Quick Dish:</b> <i>Golden Paneer & Herb Stir-Fry with Toasted Bread</i> or <i>Warm Spiced Porridge</i>.<br>"
                f"• <b>Prep Time:</b> ~10 minutes.<br>"
                f"• <b>Financial Win:</b> Preparing this saves ~<b>₹{saved_pot}</b> of groceries from being discarded.<br>"
                f"• <b>Chef Tip:</b> Squeeze a drop of fresh lemon juice at the end to brighten the flavors!"
            )
        else:
            pantry_names = [i["name"] for i in inv[:3]]
            advice = (
                f"🍲 <b>Fresh Kitchen Ideas:</b> All your perishables are well within their safe dates! 🎉<br><br>"
                f"Based on your stock ({', '.join(pantry_names)}):<br>"
                f"• <b>Healthy Choice:</b> <i>High-Protein Masala Oats Bowl with Milk</i> or <i>Crispy Whole Wheat Sandwiches</i>.<br>"
                f"• <b>Quick & Light:</b> Ready in under 12 minutes, zero food waste!"
            )
        return {"success": True, "response": advice, "intent": "recipe", "expiring_items": exp_names}

    # 5. EXPIRY CHECK & SPOILAGE
    if any(k in user_query for k in ["expir", "spoil", "waste", "shelf life", "rotten", "bad", "use by"]):
        if expiring_soon:
            lines = [f"• <b>{i['name']}</b> ({i['quantity']}{i['unit']}) — Due in <b>{days_until(i['expiry_date'])} days</b> ({i['expiry_date']})" for i in expiring_soon]
            advice = (
                f"⏰ <b>Urgent Expiry Watch ({len(expiring_soon)} item(s)):</b><br><br>"
                + "<br>".join(lines) +
                f"<br><br>💡 <b>Rescue Action:</b> Consume or freeze these first. Rescuing them saves ₹{saved_pot}!"
            )
        elif expired_items:
            advice = (
                f"⚠️ You have <b>{len(expired_items)} item(s)</b> past their expiry date ({', '.join(i['name'] for i in expired_items)}).<br>"
                "Please inspect them carefully or discard & restock via the shopping list."
            )
        else:
            advice = "🎉 <b>Clear Skies!</b> Zero items are expiring in the next 4 days. Your pantry is fresh and well-managed!"
        return {"success": True, "response": advice, "intent": "expiry", "expiring_items": exp_names}

    # 6. KITCHEN HACKS & PRESERVATION TIPS
    if any(k in user_query for k in ["hack", "tip", "trick", "storage", "preserve", "keep fresh"]):
        advice = (
            "💡 <b>Domestix Pro Kitchen Hacks:</b><br><br>"
            "1. <b>Never Refrigerate Bread:</b> The cold temperatures cause starch retrogradation, making bread go stale 6x faster! Store at room temp or freeze sliced portions.<br>"
            "2. <b>The Paneer Water Bath:</b> Submerge fresh paneer in drinking water in a sealed box; change water every 2 days to keep it soft for over a week.<br>"
            "3. <b>Keep Bananas Away from Onions:</b> Bananas emit ethylene gas, accelerating ripening and spoiling neighboring vegetables.<br>"
            "4. <b>Milk Sweet Spot:</b> Keep milk on the middle or bottom fridge shelf, never on the door where warm air hits on every open."
        )
        return {"success": True, "response": advice, "intent": "hack", "expiring_items": exp_names}

    # 7. SAVING MONEY & BUDGET
    if any(k in user_query for k in ["money", "budget", "save", "cost", "cheap", "expensive", "spend"]):
        bill_sum = sum(b.get("amount", 0) for b in unpaid_bills)
        advice = (
            "💰 <b>Domestix Smart Household Savings Blueprint:</b><br><br>"
            f"1. <b>Eliminate Food Waste:</b> Average households lose ₹2,000–₹4,000/month in spoiled food. Rescuing your {len(expiring_soon)} expiring item(s) immediately saves ~₹{saved_pot}.<br>"
            f"2. <b>Pay Utility Bills On Time:</b> You have ₹{bill_sum} in pending bills ({', '.join(b['name'] for b in unpaid_bills[:2])}). Settling them avoids late penalty charges.<br>"
            "3. <b>AC Maintenance:</b> Keeping air filters dust-free saves up to 15% on monthly electricity bills!"
        )
        return {"success": True, "response": advice, "intent": "budget", "expiring_items": exp_names}

    # 8. JOKES & BANTER
    if any(k in user_query for k in ["joke", "funny", "laugh", "bored", "humor"]):
        advice = (
            "😄 <b>Here's one for your kitchen:</b><br><br>"
            "<i>Why did the tomato blush?</i><br>"
            "👉 <b>Because it saw the salad dressing!</b> 🥗😂<br><br>"
            "Speaking of fresh salads, check your veggies in the Inventory tab to make sure they're dressed and eaten before expiring!"
        )
        return {"success": True, "response": advice, "intent": "joke", "expiring_items": exp_names}

    # 9. APPLIANCES & UTILITIES
    if any(k in user_query for k in ["appliance", "ac", "filter", "service", "clean", "water", "ro"]):
        app_list = [f"• <b>{a['name']}</b> (Next service: {a['next_service_date']})" for a in appliances]
        advice = (
            "🛠️ <b>Appliance Health & Preventive Care:</b><br><br>"
            + "<br>".join(app_list) +
            "<br><br><b>Pro-tip:</b> Regular filter cleaning on ACs and timely RO cartridge replacements prevent expensive breakdown repairs!"
        )
        return {"success": True, "response": advice, "intent": "appliance", "expiring_items": exp_names}

    # 10. BILLS
    if any(k in user_query for k in ["bill", "electricity", "due", "pay", "msedcl", "water bill"]):
        if unpaid_bills:
            b_lines = [f"• <b>{b['name']}</b> — ₹{b['amount']} (Due: {b['due_date']})" for b in unpaid_bills]
            advice = (
                f"⚡ <b>Pending Household Bills ({len(unpaid_bills)}):</b><br><br>"
                + "<br>".join(b_lines) +
                "<br><br>You can mark these paid with one click in the Bills tab!"
            )
        else:
            advice = "✅ All household utility bills are fully paid! No overdue accounts."
        return {"success": True, "response": advice, "intent": "bills", "expiring_items": exp_names}

    # 11. COURTESY / THANK YOU
    if any(k in user_query for k in ["thank", "thanks", "great", "awesome", "cool", "nice", "good job", "perfect"]):
        advice = "You're so welcome! 😊 Always a pleasure keeping your home running smoothly. Whenever you need recipe ideas, storage hacks, or expiry checks, I'm right here!"
        return {"success": True, "response": advice, "intent": "courtesy", "expiring_items": exp_names}

    # 12. GENERAL CONVERSATIONAL FALLBACK
    advice = (
        f"💡 <b>Domestix Household Guide:</b><br><br>"
        f"Here is your household summary:<br>"
        f"• <b>Pantry:</b> <b>{len(inv)} items</b> tracked in pantry (₹{total_val:.0f} total stock value).<br>"
        f"• <b>Expiring Soon:</b> {len(expiring_soon)} item(s) need attention ({', '.join(exp_names) if exp_names else 'All safe'}).<br>"
        f"• <b>Utilities:</b> {len(unpaid_bills)} pending bill(s).<br><br>"
        f"Try asking: <i>\"What should I eat tonight?\"</i>, <i>\"What is expiring next?\"</i>, or <i>\"Give me a food storage tip!\"</i>"
    )
    return {
        "success": True,
        "response": advice,
        "intent": "general",
        "expiring_items": exp_names
    }

# ============================================================================
# 10. BUDGET & WASTE REDUCTION ANALYTICS
# ============================================================================

@app.get("/api/analytics")
def get_analytics():
    conn = get_db()
    cursor = conn.cursor()

    # Total inventory stock value
    cursor.execute("SELECT SUM(price * quantity) FROM inventory")
    stock_value = cursor.fetchone()[0] or 0.0

    # Total pending bills
    cursor.execute("SELECT SUM(amount) FROM bills WHERE status = 'Unpaid'")
    pending_bills = cursor.fetchone()[0] or 0.0

    # Total settled bills
    cursor.execute("SELECT SUM(amount) FROM bills WHERE status = 'Paid'")
    settled_bills = cursor.fetchone()[0] or 0.0

    # Total tasks logged
    cursor.execute("SELECT COUNT(*) FROM task_history")
    completed_task_count = cursor.fetchone()[0] or 0

    # Category counts
    cursor.execute("SELECT category, COUNT(*) as count, SUM(price * quantity) as total FROM inventory GROUP BY category")
    category_breakdown = [dict(r) for r in cursor.fetchall()]

    conn.close()

    # Estimated waste prevented: ~₹85 saved per proactive task/consumption logged
    waste_prevented = completed_task_count * 85.0

    return {
        "stock_value": round(stock_value, 2),
        "pending_bills": round(pending_bills, 2),
        "settled_bills": round(settled_bills, 2),
        "waste_prevented": round(waste_prevented, 2),
        "completed_tasks": completed_task_count,
        "category_breakdown": category_breakdown
    }

# ============================================================================
# 11. STATIC FILES & HTML DELIVERY
# ============================================================================

@app.get("/")
def serve_root():
    index_path = os.path.join(ROOT_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Domestix API is running. index.html not found in root."}

@app.get("/login.html")
def serve_login():
    login_path = os.path.join(ROOT_DIR, "login.html")
    if os.path.exists(login_path):
        return FileResponse(login_path)
    return FileResponse(os.path.join(ROOT_DIR, "index.html"))

# Mount remaining static files if needed
app.mount("/static", StaticFiles(directory=ROOT_DIR), name="static")
