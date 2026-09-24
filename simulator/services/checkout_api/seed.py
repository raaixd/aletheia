"""Database seeding script for initial catalog items."""

import logging
from decimal import Decimal
from sqlalchemy.orm import Session

from simulator.services.checkout_api.models import Product

logger = logging.getLogger(__name__)

INITIAL_PRODUCTS = [
    {
        "sku": "PROD-LAPTOP-01",
        "name": "DevOps High Performance Laptop",
        "description": "64GB RAM, 2TB SSD, octa-core developer workstation",
        "price": Decimal("1899.99"),
        "inventory_count": 50,
    },
    {
        "sku": "PROD-MONITOR-02",
        "name": "4K UltraSharp Display 32-inch",
        "description": "IPS HDR professional color-calibrated monitor",
        "price": Decimal("599.99"),
        "inventory_count": 120,
    },
    {
        "sku": "PROD-KEYBOARD-03",
        "name": "Mechanical Ergonomic Keyboard",
        "description": "Tactile switches, split layout, RGB programmable",
        "price": Decimal("149.99"),
        "inventory_count": 300,
    },
    {
        "sku": "PROD-MOUSE-04",
        "name": "Wireless Precision Mouse",
        "description": "Ergonomic high-DPI wireless sensor mouse",
        "price": Decimal("79.99"),
        "inventory_count": 450,
    },
    {
        "sku": "PROD-HEADSET-05",
        "name": "Noise Cancelling Studio Headset",
        "description": "Active noise cancelling with studio monitor frequency response",
        "price": Decimal("199.99"),
        "inventory_count": 200,
    },
]


def seed_initial_data(db: Session) -> int:
    """Seed initial catalog products if table is currently empty."""
    existing_count = db.query(Product).count()
    if existing_count > 0:
        logger.info(f"Database already contains {existing_count} products. Skipping seeding.")
        return 0

    added = 0
    for item in INITIAL_PRODUCTS:
        product = Product(
            sku=item["sku"],
            name=item["name"],
            description=item["description"],
            price=item["price"],
            inventory_count=item["inventory_count"],
        )
        db.add(product)
        added += 1

    db.commit()
    logger.info(f"Successfully seeded {added} catalog products into database.")
    return added
