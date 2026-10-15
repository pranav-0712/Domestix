"""
Pydantic Models for Domestix Application
"""

from pydantic import BaseModel, Field
from typing import Optional, List

class UserRegister(BaseModel):
    username: str
    password: str
    full_name: str
    role: str = "Family Member"
    roll_no: Optional[str] = None
    avatar_color: Optional[str] = "indigo"

class UserLogin(BaseModel):
    username: str
    password: str

class InventoryCreate(BaseModel):
    name: str
    category: str = "Groceries"
    quantity: float = 1.0
    unit: str = "pcs"
    price: float = 0.0
    expiry_date: str
    storage_tip: Optional[str] = None

class InventoryUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    price: Optional[float] = None
    expiry_date: Optional[str] = None
    storage_tip: Optional[str] = None

class ShoppingCreate(BaseModel):
    name: str
    category: str = "Groceries"
    quantity: float = 1.0
    unit: str = "pcs"
    estimated_price: float = 0.0
    assigned_to: Optional[str] = "Kiran"

class ApplianceCreate(BaseModel):
    name: str
    serial_number: Optional[str] = None
    warranty_expiry: str
    next_service_date: str
    maintenance_notes: Optional[str] = None

class BillCreate(BaseModel):
    name: str
    category: str = "Utility"
    amount: float
    due_date: str
    assigned_to: Optional[str] = "Kiran"
    status: str = "Unpaid"

class OCRRequest(BaseModel):
    text: Optional[str] = None
    filename: Optional[str] = None
    base64_image: Optional[str] = None
    user_hint: Optional[str] = None

class AICoachRequest(BaseModel):
    prompt: Optional[str] = None
    inventory: Optional[List[dict]] = None
