# Aletheia Architecture: Phase 1 Foundation

## Overview

Aletheia is an AI-powered incident investigation system for software systems. Rather than asking an LLM to guess what broke, Aletheia is built on the core principle:

> *"The goal isn't to build an AI that guesses what went wrong. It's to build an investigation system that gathers evidence, constructs explanations, challenges them, and can be measured when it gets the diagnosis wrong."*

Phase 1 provides the foundational runtime environment:
1. **Aletheia Platform API** (`aletheia-api`): The root investigation platform backend (FastAPI) running on port `8000`.
2. **Simulated Production Checkout API** (`checkout-api`): A realistic production microservice running on port `8001` that performs catalog management, inventory tracking, and order placement against PostgreSQL. This service will serve as the target for controlled failure injections in later phases.
3. **Persistent PostgreSQL Database** (`postgres`): Runs on port `5432` with health checks, auto-seeding initial product catalogs, and transactional order execution.
4. **Synthetic Traffic Generator** (`traffic_generator.py`): Generates realistic client requests (catalog queries, order placements, health probes).
5. **Docker Compose Orchestration**: Allows developers to spin up the entire production-like environment with a single command.

---

## Component Diagram

```
+-------------------------------------------------------------+
|                      Host / Developer                       |
|                                                             |
|   +--------------------------+                              |
|   | simulator/traffic_gen.py |                              |
|   +------------+-------------+                              |
|                |                                            |
+----------------|--------------------------------------------+
                 |
        HTTP     |   Port 8001
                 v
+-------------------------------------------------------------+
|               Docker Compose Network (aletheia-net)         |
|                                                             |
|   +-----------------------------------------------------+   |
|   | checkout-api (Simulated Production Service)        |   |
|   |  - FastAPI (Python 3.12)                            |   |
|   |  - Routes: /health, /api/products, /api/orders      |   |
|   |  - Automatic catalog seeding on startup             |   |
|   +--------------------------+--------------------------+   |
|                              |                              |
|                              | SQL (port 5432)              |
|                              v                              |
|   +-----------------------------------------------------+   |
|   | postgres:16-alpine (Database)                       |   |
|   |  - Tables: products, orders, order_items            |   |
|   |  - Healthcheck: pg_isready                          |   |
|   +-----------------------------------------------------+   |
|                                                             |
|   +-----------------------------------------------------+   |
|   | aletheia-api (Investigation Platform Backend)       |   |
|   |  - FastAPI (Python 3.12, port 8000)                 |   |
|   |  - Routes: /health                                  |   |
|   |  - Configuration: Pydantic Settings                 |   |
|   +-----------------------------------------------------+   |
+-------------------------------------------------------------+
```

---

## Database Schema

### `products` Table
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | Primary Key, Auto-increment | Internal product ID |
| `sku` | String(64) | Unique, Indexed, Not Null | Unique stock-keeping unit |
| `name` | String(255) | Not Null | Product name |
| `description` | Text | Nullable | Detailed description |
| `price` | Numeric(10,2) | Not Null | Unit price in USD |
| `inventory_count` | Integer | Not Null, Default 0 | Available inventory |
| `created_at` | DateTime(tz) | Not Null | Creation timestamp |

### `orders` Table
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | Primary Key, Auto-increment | Internal order ID |
| `order_number` | String(64) | Unique, Indexed, Not Null | Unique alphanumeric order number |
| `customer_email` | String(255) | Not Null | Customer contact email |
| `status` | String(32) | Not Null, Default "COMPLETED" | Order status (PENDING, COMPLETED, FAILED) |
| `total_amount` | Numeric(10,2) | Not Null | Sum of order item subtotals |
| `created_at` | DateTime(tz) | Not Null | Creation timestamp |

### `order_items` Table
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | Primary Key, Auto-increment | Internal item ID |
| `order_id` | Integer | Foreign Key (`orders.id`), Not Null | Associated order |
| `product_id` | Integer | Foreign Key (`products.id`), Not Null | Associated product |
| `quantity` | Integer | Not Null | Units purchased |
| `unit_price` | Numeric(10,2) | Not Null | Unit price at purchase time |
| `subtotal` | Numeric(10,2) | Not Null | `quantity * unit_price` |

---

## Next Steps

- **Phase 2 (Observability)**: Add OpenTelemetry tracing, Prometheus metrics export, structured JSON logging with correlation IDs, and request timing headers across services.
- **Phase 3 (Failure Injection)**: Introduce controlled failure scenarios (starting with Database Query Regression `INC-001`), along with ground-truth definitions.
