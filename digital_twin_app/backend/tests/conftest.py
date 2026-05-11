"""Shared test fixtures."""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from db.database import Base, get_db
from main import app

# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    """Create tables before each test and drop after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    app.dependency_overrides[get_db] = override_get_db
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client():
    """Async HTTP test client."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture
def base_config():
    """Standard simulation config for testing."""
    return {
        "name": "Test Run",
        "stations": [
            {
                "name": "Feeding",
                "cycle_time_mean": 18.0,
                "cycle_time_std": 1.8,
                "buffer_capacity": 5,
                "operators": 1,
                "breakdown_probability": 0.0,
                "repair_time_min": 30.0,
                "repair_time_max": 90.0,
            },
            {
                "name": "Drilling",
                "cycle_time_mean": 42.0,
                "cycle_time_std": 4.2,
                "buffer_capacity": 5,
                "operators": 1,
                "breakdown_probability": 0.0,
                "repair_time_min": 30.0,
                "repair_time_max": 90.0,
            },
        ],
        "shift_duration_hours": 0.5,
        "warmup_period_minutes": 5.0,
        "num_replications": 2,
        "seed_base": 42,
    }
