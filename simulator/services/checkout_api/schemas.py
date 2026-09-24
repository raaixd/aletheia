"""Pydantic schemas for request and response validation in Checkout API."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, EmailStr


class ProductBase(BaseModel):
    """Base fields for a product."""
    sku: str = Field(..., max_length=64, description="Stock Keeping Unit identifier")
    name: str = Field(..., max_length=255, description="Product name")
    description: Optional[str] = Field(None, description="Detailed product description")
    price: Decimal = Field(..., gt=0, description="Product price")
    inventory_count: int = Field(..., ge=0, description="Available stock count")


class ProductCreate(ProductBase):
    """Schema for creating a product."""
    pass


class ProductResponse(ProductBase):
    """Schema for product responses."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class OrderItemCreate(BaseModel):
    """Schema for specifying an item when creating an order."""
    product_id: int = Field(..., description="ID of product being purchased")
    quantity: int = Field(..., gt=0, description="Quantity to purchase")


class OrderItemResponse(BaseModel):
    """Schema for order item in responses."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    product_name: Optional[str] = None
    sku: Optional[str] = None
    quantity: int
    unit_price: Decimal
    subtotal: Decimal


class OrderCreate(BaseModel):
    """Schema for submitting a checkout order."""
    customer_email: str = Field(..., description="Customer email address")
    items: List[OrderItemCreate] = Field(..., min_length=1, description="List of items to order")


class OrderResponse(BaseModel):
    """Schema for full checkout order response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_number: str
    customer_email: str
    status: str
    total_amount: Decimal
    created_at: datetime
    items: List[OrderItemResponse]


class DatabaseHealth(BaseModel):
    """Database connectivity details."""
    status: str
    latency_ms: float
    error: Optional[str] = None


class CheckoutHealthResponse(BaseModel):
    """Checkout service health status."""
    status: str
    service: str
    version: str
    environment: str
    timestamp: str
    database: DatabaseHealth
