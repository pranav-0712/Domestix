"""
Domestix - Smart Household Management Application
Database Layer: SQLite3 Database & Seed Data
Team Members:
  - Saee Takale (5185)
  - Ayusha Kale (3205)
  - Pranav Joshi (5208)
  - Vaishnavi Thite (5188)
"""

import sqlite3
import os
import hashlib
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "domestix.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def offset_date(days: int) -> str:
    d = datetime.now() + timedelta(days=days)
    return d.strftime("%Y-%m-%d")

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON;")

    # 1. Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        role TEXT NOT NULL,
        roll_no TEXT,
        avatar_color TEXT DEFAULT 'indigo',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Inventory Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        quantity REAL DEFAULT 1,
        unit TEXT DEFAULT 'pcs',
        price REAL DEFAULT 0,
        expiry_date TEXT NOT NULL,
        storage_tip TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
    );
    """)

    # 3. Shopping List Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS shopping_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        quantity REAL DEFAULT 1,
        unit TEXT DEFAULT 'pcs',
        estimated_price REAL DEFAULT 0,
        assigned_to TEXT DEFAULT 'Kiran',
        is_checked INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
    );
    """)

    # 4. Appliances & Warranty Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS appliances (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT NOT NULL,
        serial_number TEXT,
        warranty_expiry TEXT NOT NULL,
        next_service_date TEXT NOT NULL,
        maintenance_notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
    );
    """)

    # 5. Recurring Bills & Utilities Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT NOT NULL,
        category TEXT DEFAULT 'Utility',
        amount REAL NOT NULL,
        due_date TEXT NOT NULL,
        assigned_to TEXT DEFAULT 'Kiran',
        status TEXT DEFAULT 'Unpaid',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
    );
    """)

    # 6. Task Completion History
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS task_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT NOT NULL,
        category TEXT DEFAULT 'General',
        completed_date TEXT NOT NULL,
        completed_by TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
    );
    """)

    conn.commit()

    # Seed Default Team Members / Users if table is empty
    cursor.execute("SELECT COUNT(*) FROM users;")
    if cursor.fetchone()[0] == 0:
        seed_users = [
            ("pranav", hash_password("admin123"), "Pranav Joshi", "Project Lead & Backend", "5208", "indigo"),
            ("saee", hash_password("saee123"), "Saee Takale", "Lead Analyst & Inventory", "5185", "emerald"),
            ("ayusha", hash_password("ayusha123"), "Ayusha Kale", "UI/UX & Shopping Lead", "3205", "sky"),
            ("vaishnavi", hash_password("vaishnavi123"), "Vaishnavi Thite", "Testing & Utilities Lead", "5188", "amber"),
            ("admin", hash_password("admin123"), "Household Admin", "System Administrator", "0001", "indigo")
        ]
        cursor.executemany("""
            INSERT INTO users (username, password_hash, full_name, role, roll_no, avatar_color)
            VALUES (?, ?, ?, ?, ?, ?);
        """, seed_users)

    # Seed Default Inventory if empty
    cursor.execute("SELECT COUNT(*) FROM inventory;")
    if cursor.fetchone()[0] == 0:
        seed_inventory = [
            (1, "Amul Taaza Toned Milk", "Dairy", 2.0, "L", 112.0, offset_date(2), "Store on middle fridge shelf at 4°C; avoid storing in door rack."),
            (1, "Fresh Malai Paneer", "Perishables", 200.0, "g", 95.0, offset_date(3), "Submerge in cold water inside an airtight container; change water every 2 days."),
            (1, "Whole Wheat Brown Bread", "Bakery", 1.0, "pk", 50.0, offset_date(-1), "Keep in cool dry pantry or freeze slices to prevent fungal growth."),
            (1, "Quaker Rolled Oats", "Groceries", 1.0, "kg", 199.0, offset_date(120), "Transfer to an airtight glass jar with a bay leaf to repel pantry pests."),
            (1, "Paracetamol 650mg Tablets", "Medicine", 15.0, "pcs", 35.0, offset_date(240), "Store in a cool dry medicine cabinet away from direct sunlight and humidity."),
            (1, "Farm Fresh Eggs (Pack of 6)", "Dairy", 6.0, "pcs", 48.0, offset_date(8), "Refrigerate pointed end down to keep yolk centered and fresh."),
            (1, "Surf Excel Matic Front Load", "Cleaning", 2.0, "L", 420.0, offset_date(360), "Store in a cool dry area sealed with child-safe cap.")
        ]
        cursor.executemany("""
            INSERT INTO inventory (user_id, name, category, quantity, unit, price, expiry_date, storage_tip)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, seed_inventory)

    # Seed Shopping Items if empty
    cursor.execute("SELECT COUNT(*) FROM shopping_items;")
    if cursor.fetchone()[0] == 0:
        seed_shopping = [
            (1, "Greek Yogurt / Thick Curd", "Dairy", 1.0, "pk", 65.0, "Ayusha Kale", 0),
            (1, "Dishwash Gel Refill (500ml)", "Cleaning", 1.0, "pk", 115.0, "Vaishnavi Thite", 1),
            (1, "Ripe Tomatoes & Coriander", "Perishables", 1.0, "kg", 50.0, "Saee Takale", 0)
        ]
        cursor.executemany("""
            INSERT INTO shopping_items (user_id, name, category, quantity, unit, estimated_price, assigned_to, is_checked)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, seed_shopping)

    # Seed Appliances if empty
    cursor.execute("SELECT COUNT(*) FROM appliances;")
    if cursor.fetchone()[0] == 0:
        seed_appliances = [
            (1, "Blue Star Split Inverter AC 1.5T", "BS-AC-9021X", offset_date(320), offset_date(14), "Clean indoor air filter mesh & inspect outdoor condenser fan."),
            (1, "LG Smart Frost-Free Refrigerator", "LG-RF-4410Z", offset_date(540), offset_date(60), "Vacuum rear condenser coils & inspect door rubber gasket seal."),
            (1, "Aquaguard RO Water Purifier", "AQ-RO-1182M", offset_date(25), offset_date(-3), "Replace sediment and activated carbon pre-filters immediately.")
        ]
        cursor.executemany("""
            INSERT INTO appliances (user_id, name, serial_number, warranty_expiry, next_service_date, maintenance_notes)
            VALUES (?, ?, ?, ?, ?, ?);
        """, seed_appliances)

    # Seed Bills if empty
    cursor.execute("SELECT COUNT(*) FROM bills;")
    if cursor.fetchone()[0] == 0:
        seed_bills = [
            (1, "MSEDCL Electricity Bill", "Utility", 1840.0, offset_date(4), "Pranav Joshi", "Unpaid"),
            (1, "JioFiber Broadband Wi-Fi", "Internet", 999.0, offset_date(9), "Ayusha Kale", "Unpaid"),
            (1, "Society Maintenance Charges", "Housing", 2500.0, offset_date(-5), "Saee Takale", "Paid")
        ]
        cursor.executemany("""
            INSERT INTO bills (user_id, name, category, amount, due_date, assigned_to, status)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """, seed_bills)

    # Seed Task History if empty
    cursor.execute("SELECT COUNT(*) FROM task_history;")
    if cursor.fetchone()[0] == 0:
        seed_tasks = [
            (1, "Paid Society Maintenance Charges (₹2500)", "Bill Payment", offset_date(-5), "Saee Takale"),
            (1, "Deep cleaned refrigerator shelves & crisper", "Hygiene", offset_date(-12), "Pranav Joshi")
        ]
        cursor.executemany("""
            INSERT INTO task_history (user_id, title, category, completed_date, completed_by)
            VALUES (?, ?, ?, ?, ?);
        """, seed_tasks)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at:", DB_PATH)
