import pytest
from httpx import AsyncClient
from backend.main import app
from backend.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from backend.models.stix import StixObject
from backend.core.database import Base

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.mark.asyncio
async def test_create_stix_indicator():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/api/v1/stix/indicators", json={
            "name": "Malicious IP",
            "pattern": "[ipv4-addr:value = '198.51.100.1/32']",
            "pattern_type": "stix"
        })
    assert response.status_code == 201
    data = response.json()
    assert data["type"] == "indicator"
    assert "indicator--" in data["id"]
    assert data["name"] == "Malicious IP"
