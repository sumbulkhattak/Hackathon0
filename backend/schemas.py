from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


# --- Category ---
class CategoryBase(BaseModel):
    name: str
    slug: str


class CategoryCreate(CategoryBase):
    pass


class CategoryResponse(CategoryBase):
    id: int
    model_config = {"from_attributes": True}


# --- Product ---
class ProductBase(BaseModel):
    name: str
    slug: str
    description: str
    price: float
    image_url: str
    images: List[str] = []
    category_id: int
    stock: int = 50
    featured: bool = False


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    image_url: Optional[str] = None
    images: Optional[List[str]] = None
    category_id: Optional[int] = None
    stock: Optional[int] = None
    featured: Optional[bool] = None


class ProductResponse(ProductBase):
    id: int
    category_name: str = ""
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


# --- Order ---
class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    price: float
    model_config = {"from_attributes": True}


class OrderCreate(BaseModel):
    customer_name: str
    email: str
    phone: str
    address: str
    city: str
    items: List[OrderItemCreate]


class OrderResponse(BaseModel):
    id: int
    customer_name: str
    email: str
    phone: str
    address: str
    city: str
    total: float
    status: str
    created_at: Optional[datetime] = None
    items: List[OrderItemResponse] = []
    model_config = {"from_attributes": True}


class OrderStatusUpdate(BaseModel):
    status: str


# --- AI Hooks ---
class HookPayload(BaseModel):
    event: str
    data: dict


# --- Stats ---
class DashboardStats(BaseModel):
    total_orders: int
    total_revenue: float
    total_products: int
    low_stock_count: int


# --- Task Queue ---
class TaskSummary(BaseModel):
    filename: str
    queue: str
    task_type: str
    timestamp_str: str
    size: int
    modified: str


class TaskDetail(BaseModel):
    filename: str
    queue: str
    metadata: dict
    content: str


class TaskApproval(BaseModel):
    approved_by: str
    notes: Optional[str] = None


class TaskRejection(BaseModel):
    rejected_by: str
    reason: str
    reprocess: bool = False


class TaskExecution(BaseModel):
    executed_by: str
    notes: Optional[str] = None


class ProcessingResult(BaseModel):
    status: str
    task_type: str
    filename: str
    moved_to: str
    duration_ms: Optional[int] = None


# --- Audit ---
class AuditEntry(BaseModel):
    id: str
    timestamp: str
    source: str
    action: str
    entity_type: str
    entity_id: str
    actor: str
    details: dict
    queue: Optional[str] = None
    status: str
    duration_ms: Optional[int] = None
    error: Optional[str] = None


class AuditSummary(BaseModel):
    date: str
    total_entries: int
    by_action: dict
    by_entity_type: dict
    by_status: dict
    completed: int
    pending: int
    errors: int
    orders: int
    inquiries: int
    alerts: int


# --- Dashboard ---
class DashboardResponse(BaseModel):
    queue_counts: dict
    today_activity: dict
    recent_actions: list
    watchers: list
    db_stats: dict
    system_health: dict


# --- Memory ---
class ClientProfileCreate(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    tags: List[str] = []
    notes: Optional[str] = None


class MemoryFileResponse(BaseModel):
    filename: str
    slug: str
    size: int
    modified: str
