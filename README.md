# Domestix | Smart Household Management Application

> **A unified platform for inventory, shopping, maintenance, warranties and recurring tasks.**  
> *PBL Project Presentation & Implementation (Evaluation 2)*

---

## 👥 Project Team Members

| Name | Roll No. | Assigned Role |
| :--- | :--- | :--- |
| **Saee Takale** | **5185** | Project Lead / Analyst |
| **Ayusha Kale** | **3205** | Frontend & UI/UX Developer |
| **Pranav Joshi** | **5208** | Backend & Database Developer |
| **Vaishnavi Thite** | **5188** | OCR & Notification Developer |

---

## 🌟 Key Features

1. **Authentication & Multi-User Profiles:**
   - Dedicated login & registration portal ([login.html](file:///d:/Domestix/login.html)) with SHA-256 hashed passwords.
   - Quick 1-click demo login buttons for each project team member.
   - In-app profile switcher with role badges (*Household Admin, Kitchen Lead, Shopping Lead, Utilities Lead*).

2. **Household Inventory & Expiry Tracking:**
   - Centralized database of household items with quantity, unit, price, and category.
   - Color-coded expiry alerts: **Safe** (green), **Expiring Soon** (amber, $\le 4$ days), and **Expired** (rose).
   - Smart AI storage and shelf-life preservation recommendations.

3. **Multi-Modal Smart Ingestion Hub:**
   - **Type Manually + Natural Language Parser:** Auto-parses sentences like *"2L Amul Milk expiring in 3 days for ₹130"*.
   - **Photo / Label Upload:** Extracts product details, printed Indian dates (*DD/MM/YYYY, EXP, BB, PKD/MFG*).
   - **Live Camera Scanner:** Direct device camera viewfinder with date alignment target.
   - **Handwriting Pad:** Digital canvas to write notes or expiry dates directly on screen.
   - **Barcode / SKU Lookup:** Instant lookup with built-in Indian grocery barcodes (*Amul, Britannia, Maggi, etc.*).
   - **Pre-commit Verification:** Editable review dialog before committing items to the database.

4. **Smart Shopping List & Auto-Replenishment:**
   - When an inventory item is consumed, it is automatically queued for restocking in the shopping list.
   - 1-click batch checkout: Checked purchases automatically transfer to inventory with calculated shelf-life.

5. **Appliance Maintenance & Warranty Vault:**
   - Track household assets (*Split AC, Frost-Free Refrigerator, RO Water Purifier, Washing Machine, etc.*).
   - Active countdown for warranty expiry.
   - Scheduled preventive maintenance; 1-click "Log Service Done" automatically rolls forward to the next cycle (+180 days).

6. **Recurring Utilities & Bills:**
   - Tracks monthly utilities (*Electricity, Broadband, Society Maintenance, Piped Gas*).
   - Status indicators (*Paid vs Unpaid*) and family member assignment.

7. **Unified Task Lifecycle & Notifications:**
   - Categorized by **Upcoming**, **Overdue**, and **Completed** tasks.
   - Timestamps and operator attribution on all actions.

8. **Budget & Food Waste Analytics:**
   - Active inventory valuation in ₹ INR.
   - Monthly utility outflow calculation.
   - Estimated money saved by preventing food waste through proactive expiry alerts.

9. **AI Household Coach (IEEE 2026 Model):**
   - Context-aware recipe generator using expiring items in inventory.
   - Appliance maintenance checklist and preservation advice.
   - Optional live Google Gemini Vision integration via API key.

---

## 🏗️ 5-Layer System Architecture

```
┌────────────────────────────────────────────────────────┐
│ 1. User Layer: Web & Mobile Dashboard, Scanner, Canvas │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ 2. Application Layer: Inventory, Shopping, Assets, Bills│
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ 3. Service Layer: OCR Parser, Reminder Engine, AI Coach│
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ 4. Data Layer: SQLite3 Database (domestix.db) & REST   │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ 5. Output Layer: Prioritized Alerts, Recipes, Analytics│
└────────────────────────────────────────────────────────┘
```

---

## 🗄️ Database Schema (`domestix.db`)

- **`users`**: `id`, `username`, `password_hash`, `full_name`, `role`, `roll_no`, `avatar_color`, `created_at`
- **`inventory`**: `id`, `user_id`, `name`, `category`, `quantity`, `unit`, `price`, `expiry_date`, `storage_tip`, `created_at`
- **`shopping_items`**: `id`, `user_id`, `name`, `category`, `quantity`, `unit`, `estimated_price`, `assigned_to`, `is_checked`, `created_at`
- **`appliances`**: `id`, `user_id`, `name`, `serial_number`, `warranty_expiry`, `next_service_date`, `maintenance_notes`, `created_at`
- **`bills`**: `id`, `user_id`, `name`, `category`, `amount`, `due_date`, `assigned_to`, `status`, `created_at`
- **`task_history`**: `id`, `user_id`, `title`, `category`, `completed_date`, `completed_by`, `created_at`

---

## 🚀 How to Run the Application

### Option A: Full-Stack Mode (Python FastAPI + SQLite Backend)

1. Double-click [start_server.bat](file:///d:/Domestix/start_server.bat) or run in terminal:
   ```powershell
   py -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
   ```
2. Open your web browser and navigate to:
   - **Login Page:** [http://127.0.0.1:8000/login.html](http://127.0.0.1:8000/login.html)
   - **Main Dashboard:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
   - **Interactive API Docs (Swagger UI):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### Option B: Standalone PWA Mode (No Server Required)

- Simply double-click [index.html](file:///d:/Domestix/index.html) or [login.html](file:///d:/Domestix/login.html) in any modern browser.
- The built-in Virtual REST Engine activates automatically with complete `localStorage` persistence and full functionality!

---

## 📚 IEEE Literature Survey References

1. *Intelligent Grocery Management System Using IoT for Personalized Shopping and Inventory Management*, IEEE ICoACT, 2025.
2. *An AI Smart Refrigerator: Enhancing Food Management with Computer Vision, Sensor, IoT, and Automated Temperature Control*, IEEE ICETEA, 2025.
3. *A Technology-Driven Solution for Food Waste Management: Enhancing Sustainability*, IEEE ICIMTech, 2025.
4. *An AI-Powered Food Expiry Optimizer and Meal Planner*, IEEE ICoECIT, 2026.
5. *Architecture for Efficient Food Management and Waste Reduction*, IEEE Conference Publication, 2024.
6. *Smart Refrigerator Inventory Management Using Convolutional Neural Networks*, IEEE AICAS, 2021.
7. *IoT based Grocery Management System: Smart Refrigerator and Smart Cabinet*, IEEE, 2019.
8. *Understanding Motivations for Using Grocery Shopping Applications*, IEEE Pervasive Computing, 2015.
9. *Digital Twin-Based Dynamic Task Assignment for Smart Home Maintenance*, IEEE ICC, 2024.
10. *Design and Implementation of an Android Application for Smart Shopping*, IEEE ICCSP, 2019.
