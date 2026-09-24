"""Integration tests for the Checkout API endpoints."""

import pytest
from decimal import Decimal


@pytest.mark.integration
def test_checkout_health_endpoint(checkout_client):
    """Verify Checkout API health check returns healthy status with DB latency."""
    response = checkout_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "checkout-api"
    assert data["database"]["status"] == "healthy"
    assert "latency_ms" in data["database"]
    assert data["database"]["latency_ms"] >= 0


@pytest.mark.integration
def test_list_products_returns_seeded_catalog(checkout_client):
    """Verify catalog listing returns seeded products."""
    response = checkout_client.get("/api/products")
    assert response.status_code == 200
    products = response.json()
    assert len(products) >= 5
    skus = [p["sku"] for p in products]
    assert "PROD-LAPTOP-01" in skus
    assert "PROD-MONITOR-02" in skus


@pytest.mark.integration
def test_get_single_product(checkout_client):
    """Verify retrieving a single product by ID."""
    # First get product list
    list_res = checkout_client.get("/api/products")
    product_id = list_res.json()[0]["id"]

    res = checkout_client.get(f"/api/products/{product_id}")
    assert res.status_code == 200
    prod = res.json()
    assert prod["id"] == product_id
    assert "name" in prod
    assert "price" in prod


@pytest.mark.integration
def test_get_nonexistent_product_returns_404(checkout_client):
    """Verify querying non-existent product returns 404."""
    res = checkout_client.get("/api/products/999999")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


@pytest.mark.integration
def test_create_order_success_and_inventory_decrement(checkout_client):
    """Verify placing an order creates record and decrements inventory."""
    # Get a product
    products = checkout_client.get("/api/products").json()
    target_product = products[0]
    initial_inventory = target_product["inventory_count"]
    order_qty = 2

    # Place order
    order_payload = {
        "customer_email": "jane.doe@example.com",
        "items": [
            {
                "product_id": target_product["id"],
                "quantity": order_qty,
            }
        ],
    }
    create_res = checkout_client.post("/api/orders", json=order_payload)
    assert create_res.status_code == 201
    order_data = create_res.json()
    assert order_data["customer_email"] == "jane.doe@example.com"
    assert order_data["status"] == "COMPLETED"
    assert len(order_data["items"]) == 1
    assert order_data["items"][0]["quantity"] == order_qty

    # Verify inventory was decremented
    updated_prod = checkout_client.get(f"/api/products/{target_product['id']}").json()
    assert updated_prod["inventory_count"] == initial_inventory - order_qty


@pytest.mark.integration
def test_create_order_insufficient_stock(checkout_client):
    """Verify ordering more than available stock fails with 400."""
    products = checkout_client.get("/api/products").json()
    target_product = products[0]

    excessive_qty = target_product["inventory_count"] + 100
    order_payload = {
        "customer_email": "greedy.shopper@example.com",
        "items": [
            {
                "product_id": target_product["id"],
                "quantity": excessive_qty,
            }
        ],
    }
    create_res = checkout_client.post("/api/orders", json=order_payload)
    assert create_res.status_code == 400
    assert "insufficient stock" in create_res.json()["detail"].lower()


@pytest.mark.integration
def test_list_and_get_orders(checkout_client):
    """Verify listing recent orders and fetching order by ID."""
    products = checkout_client.get("/api/products").json()
    order_payload = {
        "customer_email": "history.user@example.com",
        "items": [{"product_id": products[0]["id"], "quantity": 1}],
    }
    created = checkout_client.post("/api/orders", json=order_payload).json()
    order_id = created["id"]

    # List orders
    list_res = checkout_client.get("/api/orders")
    assert list_res.status_code == 200
    orders = list_res.json()
    assert any(o["id"] == order_id for o in orders)

    # Get single order
    get_res = checkout_client.get(f"/api/orders/{order_id}")
    assert get_res.status_code == 200
    assert get_res.json()["order_number"] == created["order_number"]
