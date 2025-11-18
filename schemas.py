"""
Database Schemas for Bbrother Cafe

Each Pydantic model represents a collection in MongoDB. The collection
name is the lowercase version of the class name.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class Menuitem(BaseModel):
    """
    Cafe menu items
    Collection name: "menuitem"
    """
    name: str = Field(..., description="Display name of the item")
    description: Optional[str] = Field(None, description="Short description")
    price: float = Field(..., ge=0, description="Price in local currency")
    category: str = Field(..., description="e.g., Coffee, Tea, Pastry, Sandwich")
    image_url: Optional[str] = Field(None, description="Image URL")
    is_available: bool = Field(True, description="If the item is currently available")
    tags: List[str] = Field(default_factory=list, description="e.g., hot, iced, vegan")


class Service(BaseModel):
    """
    Other services offered by the cafe (e.g., catering, workspace, events)
    Collection name: "service"
    """
    title: str
    summary: Optional[str] = None
    icon: Optional[str] = Field(None, description="Icon keyword for frontend display")
    price_from: Optional[float] = Field(None, ge=0, description="Starting price if applicable")
    active: bool = Field(True)


class Orderitem(BaseModel):
    menu_item_id: str = Field(..., description="Referenced menu item _id as string")
    name: str = Field(..., description="Snapshot name for historical integrity")
    unit_price: float = Field(..., ge=0)
    quantity: int = Field(..., ge=1)


class Customer(BaseModel):
    name: str
    phone: str
    notes: Optional[str] = None


class Order(BaseModel):
    """
    Customer orders
    Collection name: "order"
    """
    items: List[Orderitem]
    customer: Customer
    status: str = Field("pending", description="pending, confirmed, preparing, ready, delivered, cancelled")
    total_amount: float = Field(..., ge=0)
    table_number: Optional[str] = Field(None, description="Optional dine-in table number")
