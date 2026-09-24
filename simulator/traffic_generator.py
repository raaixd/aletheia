"""Simulated realistic traffic generator for Checkout API."""

import argparse
import logging
import random
import sys
import time
from typing import List, Optional
import httpx

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [traffic-gen] %(message)s",
)
logger = logging.getLogger("traffic-generator")

SAMPLE_CUSTOMERS = [
    "alice.developer@example.com",
    "bob.engineer@example.com",
    "charlie.analyst@example.com",
    "dana.ops@example.com",
    "elena.architect@example.com",
    "frank.lead@example.com",
    "grace.sre@example.com",
]


class TrafficGenerator:
    """Generates synthetic e-commerce traffic against the Checkout API."""

    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(base_url=self.base_url, timeout=10.0)

    def check_health(self) -> bool:
        """Ping checkout API health endpoint."""
        try:
            res = self.client.get("/health")
            if res.status_code == 200:
                data = res.json()
                logger.info(
                    f"Health check OK: status={data.get('status')} "
                    f"db_latency={data.get('database', {}).get('latency_ms')}ms"
                )
                return True
            else:
                logger.warning(f"Health check failed with status {res.status_code}: {res.text}")
                return False
        except Exception as exc:
            logger.error(f"Failed to reach checkout API: {exc}")
            return False

    def get_products(self) -> List[dict]:
        """Fetch list of products from catalog."""
        try:
            res = self.client.get("/api/products")
            if res.status_code == 200:
                products = res.json()
                logger.info(f"Retrieved {len(products)} products from catalog.")
                return products
            else:
                logger.warning(f"Failed to get products: {res.status_code}")
                return []
        except Exception as exc:
            logger.error(f"Error fetching products: {exc}")
            return []

    def place_order(self, products: List[dict]) -> Optional[dict]:
        """Submit a realistic order for random products."""
        if not products:
            return None

        # Pick 1 to 3 items
        items_to_pick = random.sample(products, k=min(len(products), random.randint(1, 3)))
        items_payload = [
            {"product_id": p["id"], "quantity": random.randint(1, 2)}
            for p in items_to_pick
        ]
        customer = random.choice(SAMPLE_CUSTOMERS)

        payload = {
            "customer_email": customer,
            "items": items_payload,
        }

        try:
            start = time.perf_counter()
            res = self.client.post("/api/orders", json=payload)
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)

            if res.status_code == 201:
                order_data = res.json()
                logger.info(
                    f"Order placed successfully: order_number={order_data.get('order_number')} "
                    f"total=${order_data.get('total_amount')} ({elapsed_ms}ms)"
                )
                return order_data
            else:
                logger.warning(f"Order failed ({res.status_code}) in {elapsed_ms}ms: {res.text}")
                return None
        except Exception as exc:
            logger.error(f"Error placing order: {exc}")
            return None

    def query_order(self, order_id: int) -> Optional[dict]:
        """Query a single order by ID."""
        try:
            res = self.client.get(f"/api/orders/{order_id}")
            if res.status_code == 200:
                return res.json()
            return None
        except Exception as exc:
            logger.error(f"Error querying order {order_id}: {exc}")
            return None

    def run_simulation(self, total_requests: int = 10, delay_seconds: float = 0.5) -> dict:
        """Run a simulation batch of requests."""
        logger.info(f"Starting traffic simulation against {self.base_url} ({total_requests} cycles)...")
        stats = {
            "health_checks": 0,
            "catalog_views": 0,
            "orders_placed": 0,
            "failed_requests": 0,
        }

        # Check health first
        if self.check_health():
            stats["health_checks"] += 1
        else:
            stats["failed_requests"] += 1

        products = self.get_products()
        if products:
            stats["catalog_views"] += 1
        else:
            stats["failed_requests"] += 1
            logger.error("No products available to generate orders. Exiting simulation early.")
            return stats

        for i in range(total_requests):
            # Mix actions: 60% place order, 30% view catalog, 10% health check
            action = random.choices(["order", "catalog", "health"], weights=[0.6, 0.3, 0.1])[0]

            if action == "order":
                order = self.place_order(products)
                if order:
                    stats["orders_placed"] += 1
                    # Occasionally query back the created order
                    if random.random() < 0.5:
                        self.query_order(order["id"])
                else:
                    stats["failed_requests"] += 1

            elif action == "catalog":
                p = self.get_products()
                if p:
                    stats["catalog_views"] += 1
                else:
                    stats["failed_requests"] += 1

            elif action == "health":
                if self.check_health():
                    stats["health_checks"] += 1
                else:
                    stats["failed_requests"] += 1

            time.sleep(delay_seconds)

        logger.info(f"Simulation completed. Summary: {stats}")
        return stats

    def close(self):
        """Close HTTP client."""
        self.client.close()


def main():
    """CLI entry point for traffic generator."""
    parser = argparse.ArgumentParser(description="Simulated traffic generator for Checkout API")
    parser.add_argument(
        "--target",
        type=str,
        default="http://localhost:8001",
        help="Target base URL of Checkout API (default: http://localhost:8001)",
    )
    parser.add_argument(
        "--requests",
        type=int,
        default=10,
        help="Number of request cycles to run (default: 10)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Delay in seconds between requests (default: 0.5)",
    )
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Run continuously in an infinite loop",
    )

    args = parser.parse_args()
    generator = TrafficGenerator(base_url=args.target)

    try:
        if args.loop:
            logger.info("Running in continuous loop mode. Press Ctrl+C to terminate.")
            while True:
                generator.run_simulation(total_requests=args.requests, delay_seconds=args.delay)
                time.sleep(args.delay)
        else:
            stats = generator.run_simulation(total_requests=args.requests, delay_seconds=args.delay)
            if stats["orders_placed"] == 0 and stats["failed_requests"] > 0:
                sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Traffic generation stopped by user.")
    finally:
        generator.close()


if __name__ == "__main__":
    main()
