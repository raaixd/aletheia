"""Unit tests for simulator database models."""

import pytest
from decimal import Decimal
from simulator.services.checkout_api.models import Product, Order, OrderItem


@pytest.mark.unit
def test_create_product_model(test_db):
    """Verify product model persistence and attributes."""
    prod = Product(
        sku="TEST-SKU-999",
        name="Test Diagnostic Item",
        description="A test item for unit tests",
        price=Decimal("49.99"),
        inventory_count=10,
    )
    test_db.add(prod)
    test_db.commit()
    test_db.refresh(prod)

    assert prod.id is not None
    assert prod.sku == "TEST-SKU-999"
    assert prod.price == Decimal("49.99")
    assert prod.inventory_count == 10
    assert prod.created_at is not None


@pytest.mark.unit
def test_create_order_with_items(test_db):
    """Verify order and order items relationships and cascade."""
    prod = test_db.query(Product).first()
    assert prod is not None

    order = Order(
        order_number="ORD-TEST-1234",
        customer_email="test.user@example.com",
        status="COMPLETED",
        total_amount=prod.price * 2,
    )
    test_db.add(order)
    test_db.flush()

    item = OrderItem(
        order_id=order.id,
        product_id=prod.id,
        quantity=2,
        unit_price=prod.price,
        subtotal=prod.price * 2,
    )
    test_db.add(item)
    test_db.commit()
    test_db.refresh(order)

    assert len(order.items) == 1
    assert order.items[0].product_id == prod.id
    assert order.items[0].quantity == 2
    assert order.items[0].unit_price == prod.price
