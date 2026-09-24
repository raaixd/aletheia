"""HTTP endpoints for the simulated Checkout API."""

import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from simulator.services.checkout_api.config import CheckoutSettings, get_checkout_settings
from simulator.services.checkout_api.database import get_db, check_db_health
from simulator.services.checkout_api.models import Product, Order, OrderItem
from simulator.services.checkout_api.schemas import (
    CheckoutHealthResponse,
    DatabaseHealth,
    ProductResponse,
    ProductCreate,
    OrderCreate,
    OrderResponse,
    OrderItemResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=CheckoutHealthResponse, tags=["Health"])
def health_check(
    db: Session = Depends(get_db),
    settings: CheckoutSettings = Depends(get_checkout_settings),
) -> CheckoutHealthResponse:
    """Return health status of the Checkout API and connected PostgreSQL database."""
    db_health = check_db_health(db)
    overall_status = "healthy" if db_health["status"] == "healthy" else "degraded"

    return CheckoutHealthResponse(
        status=overall_status,
        service=settings.service_name,
        version=settings.service_version,
        environment=settings.service_environment,
        timestamp=datetime.now(timezone.utc).isoformat(),
        database=DatabaseHealth(
            status=db_health["status"],
            latency_ms=db_health["latency_ms"],
            error=db_health["error"],
        ),
    )


# ------------------------------------------------------------------------------
# Products Catalog
# ------------------------------------------------------------------------------

@router.get("/api/products", response_model=List[ProductResponse], tags=["Products"])
def list_products(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
) -> List[Product]:
    """Retrieve catalog products with pagination."""
    return db.query(Product).offset(skip).limit(limit).all()


@router.get("/api/products/{product_id}", response_model=ProductResponse, tags=["Products"])
def get_product(product_id: int, db: Session = Depends(get_db)) -> Product:
    """Retrieve details for a single product by ID."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found",
        )
    return product


@router.post(
    "/api/products",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Products"],
)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
) -> Product:
    """Add a new product to the catalog."""
    existing = db.query(Product).filter(Product.sku == payload.sku).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product with SKU '{payload.sku}' already exists",
        )

    product = Product(
        sku=payload.sku,
        name=payload.name,
        description=payload.description,
        price=payload.price,
        inventory_count=payload.inventory_count,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


# ------------------------------------------------------------------------------
# Checkout & Orders
# ------------------------------------------------------------------------------

@router.post(
    "/api/orders",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Orders"],
)
def create_order(
    payload: OrderCreate,
    db: Session = Depends(get_db),
) -> OrderResponse:
    """Process a checkout order, reserving inventory and recording order items."""
    if not payload.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order must contain at least one item",
        )

    total_amount = Decimal("0.00")
    order_items_to_create = []

    # Process items inside transaction
    for item_spec in payload.items:
        product = db.query(Product).filter(Product.id == item_spec.product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {item_spec.product_id} not found",
            )

        if product.inventory_count < item_spec.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Insufficient stock for product '{product.name}' (SKU: {product.sku}). "
                    f"Available: {product.inventory_count}, Requested: {item_spec.quantity}"
                ),
            )

        # Deduct inventory
        product.inventory_count -= item_spec.quantity
        subtotal = product.price * Decimal(item_spec.quantity)
        total_amount += subtotal

        order_items_to_create.append(
            {
                "product": product,
                "quantity": item_spec.quantity,
                "unit_price": product.price,
                "subtotal": subtotal,
            }
        )

    order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
    new_order = Order(
        order_number=order_number,
        customer_email=payload.customer_email,
        status="COMPLETED",
        total_amount=total_amount,
    )
    db.add(new_order)
    db.flush()  # obtain new_order.id

    item_responses = []
    for item_data in order_items_to_create:
        order_item = OrderItem(
            order_id=new_order.id,
            product_id=item_data["product"].id,
            quantity=item_data["quantity"],
            unit_price=item_data["unit_price"],
            subtotal=item_data["subtotal"],
        )
        db.add(order_item)
        db.flush()

        item_responses.append(
            OrderItemResponse(
                id=order_item.id,
                product_id=item_data["product"].id,
                product_name=item_data["product"].name,
                sku=item_data["product"].sku,
                quantity=item_data["quantity"],
                unit_price=item_data["unit_price"],
                subtotal=item_data["subtotal"],
            )
        )

    db.commit()
    db.refresh(new_order)

    return OrderResponse(
        id=new_order.id,
        order_number=new_order.order_number,
        customer_email=new_order.customer_email,
        status=new_order.status,
        total_amount=new_order.total_amount,
        created_at=new_order.created_at,
        items=item_responses,
    )


@router.get("/api/orders", response_model=List[OrderResponse], tags=["Orders"])
def list_orders(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
) -> List[OrderResponse]:
    """Retrieve recent orders with their line items."""
    orders = (
        db.query(Order)
        .order_by(Order.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    results = []
    for order in orders:
        item_responses = [
            OrderItemResponse(
                id=item.id,
                product_id=item.product_id,
                product_name=item.product.name if item.product else None,
                sku=item.product.sku if item.product else None,
                quantity=item.quantity,
                unit_price=item.unit_price,
                subtotal=item.subtotal,
            )
            for item in order.items
        ]
        results.append(
            OrderResponse(
                id=order.id,
                order_number=order.order_number,
                customer_email=order.customer_email,
                status=order.status,
                total_amount=order.total_amount,
                created_at=order.created_at,
                items=item_responses,
            )
        )
    return results


@router.get("/api/orders/{order_id}", response_model=OrderResponse, tags=["Orders"])
def get_order(order_id: int, db: Session = Depends(get_db)) -> OrderResponse:
    """Retrieve order details by order ID."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID {order_id} not found",
        )

    item_responses = [
        OrderItemResponse(
            id=item.id,
            product_id=item.product_id,
            product_name=item.product.name if item.product else None,
            sku=item.product.sku if item.product else None,
            quantity=item.quantity,
            unit_price=item.unit_price,
            subtotal=item.subtotal,
        )
        for item in order.items
    ]

    return OrderResponse(
        id=order.id,
        order_number=order.order_number,
        customer_email=order.customer_email,
        status=order.status,
        total_amount=order.total_amount,
        created_at=order.created_at,
        items=item_responses,
    )
