import os
# Ensure test environment uses SQLite in-memory database
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SIMULATOR_DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ALETHEIA_ENV"] = "test"

import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from aletheia.api.app import create_app
from simulator.services.checkout_api.database import Base, get_db, reset_engine
from simulator.services.checkout_api.main import create_checkout_app
from simulator.services.checkout_api.models import Product
from simulator.services.checkout_api.seed import seed_initial_data

import tempfile
import os

TEST_DB_FILE = os.path.join(tempfile.gettempdir(), "test_aletheia.db")
TEST_DATABASE_URL = f"sqlite:///{TEST_DB_FILE}"

@pytest.fixture(scope="function")
def test_db():
    """Create a fresh isolated database schema for each test."""
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except OSError:
            pass

    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
    reset_engine(engine)
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = session_factory()
    seed_initial_data(db)
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        reset_engine(None)
        engine.dispose()
        if os.path.exists(TEST_DB_FILE):
            try:
                os.remove(TEST_DB_FILE)
            except OSError:
                pass


@pytest.fixture(scope="function")
def checkout_client(test_db):
    """Provide a FastAPI TestClient for checkout-api with test DB dependency override."""
    from simulator.services.checkout_api.config import CheckoutSettings, get_checkout_settings

    test_settings = CheckoutSettings(
        database_url=TEST_DATABASE_URL,
        service_environment="test",
    )

    app = create_checkout_app()

    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_checkout_settings] = lambda: test_settings

    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def aletheia_client():
    """Provide a FastAPI TestClient for Aletheia platform API."""
    app = create_app()
    with TestClient(app) as client:
        yield client
