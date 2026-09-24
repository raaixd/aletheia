"""Unit tests for the synthetic traffic generator."""

import pytest
from unittest.mock import MagicMock, patch
from simulator.traffic_generator import TrafficGenerator


@pytest.mark.unit
def test_traffic_generator_health_check_success():
    """Verify traffic generator handles healthy response."""
    generator = TrafficGenerator(base_url="http://localhost:8001")
    with patch.object(generator.client, "get") as mock_get:
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"status": "healthy", "database": {"latency_ms": 1.2}},
        )
        assert generator.check_health() is True


@pytest.mark.unit
def test_traffic_generator_get_products():
    """Verify traffic generator fetches catalog products."""
    generator = TrafficGenerator(base_url="http://localhost:8001")
    sample_products = [
        {"id": 1, "sku": "PROD-1", "name": "Laptop", "price": 1000, "inventory_count": 10}
    ]
    with patch.object(generator.client, "get") as mock_get:
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: sample_products,
        )
        products = generator.get_products()
        assert len(products) == 1
        assert products[0]["sku"] == "PROD-1"


@pytest.mark.unit
def test_traffic_generator_place_order():
    """Verify traffic generator constructs valid order payload."""
    generator = TrafficGenerator(base_url="http://localhost:8001")
    sample_products = [
        {"id": 1, "sku": "PROD-1", "name": "Laptop", "price": 1000, "inventory_count": 10}
    ]
    with patch.object(generator.client, "post") as mock_post:
        mock_post.return_value = MagicMock(
            status_code=201,
            json=lambda: {
                "id": 100,
                "order_number": "ORD-TEST-001",
                "total_amount": "1000.00",
                "status": "COMPLETED",
            },
        )
        order = generator.place_order(sample_products)
        assert order is not None
        assert order["order_number"] == "ORD-TEST-001"
