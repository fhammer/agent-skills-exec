"""Test configuration and shared fixtures."""

import os
import sys
import asyncio
import pytest
from typing import AsyncGenerator, Dict, Any
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api.main import app
from api.database import Base, get_session
from api.models import Tenant, Session
from agent.coordinator import Coordinator
from agent.context import AgentContext
from config import Config

# Test database URL
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://test_user:test_pass@localhost:5433/agent_framework_test"
)

# Test Redis URL
TEST_REDIS_URL = os.getenv("TEST_REDIS_URL", "redis://localhost:6380")

# Create async engine
engine = create_async_engine(TEST_DATABASE_URL, echo=False)
async_session_maker = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


# ==================== Test Data Fixtures ====================

@pytest.fixture
def sample_tenant_data() -> Dict[str, Any]:
    """Sample tenant data for testing."""
    return {
        "tenant_id": "tenant_test_001",
        "name": "测试租户",
        "api_quota": 1000,
        "config": {
            "model": "gpt-4",
            "max_tokens": 2000,
            "temperature": 0.7
        }
    }


@pytest.fixture
def sample_user_data() -> Dict[str, Any]:
    """Sample user data for testing."""
    return {
        "user_id": "user_test_001",
        "tenant_id": "tenant_test_001",
        "name": "测试用户",
        "email": "test@example.com"
    }


@pytest.fixture
def sample_skill_data() -> Dict[str, Any]:
    """Sample skill data for testing."""
    return {
        "skill_id": "skill_test_001",
        "tenant_id": "tenant_test_001",
        "name": "测试技能",
        "description": "这是一个测试技能",
        "version": "1.0.0",
        "config": {
            "timeout": 30
        }
    }


@pytest.fixture
def sample_products() -> list:
    """Sample product data for ecommerce tests."""
    return [
        {
            "product_id": "p_001",
            "name": "Redmi K70",
            "category": "手机",
            "brand": "小米",
            "price": 2499,
            "attributes": {
                "screen": "6.67英寸 2K 120Hz",
                "processor": "骁龙8 Gen2",
                "battery": "5000mAh"
            },
            "rating": 4.7,
            "stock": 1000
        },
        {
            "product_id": "p_002",
            "name": "iQOO Neo9",
            "category": "手机",
            "brand": "iQOO",
            "price": 2299,
            "attributes": {
                "screen": "6.78英寸 144Hz",
                "processor": "骁龙8 Gen2",
                "battery": "5160mAh"
            },
            "rating": 4.6,
            "stock": 800
        },
        {
            "product_id": "p_003",
            "name": "一加 Ace 3",
            "category": "手机",
            "brand": "一加",
            "price": 2599,
            "attributes": {
                "screen": "6.78英寸 120Hz",
                "processor": "骁龙8 Gen2",
                "battery": "5500mAh"
            },
            "rating": 4.8,
            "stock": 500
        }
    ]


@pytest.fixture
def sample_orders() -> list:
    """Sample order data for ecommerce tests."""
    return [
        {
            "order_id": "20240228123456",
            "user_id": "user_test_001",
            "status": "shipped",
            "status_text": "已发货",
            "total_amount": 2499.00,
            "items": [
                {
                    "product_id": "p_001",
                    "name": "Redmi K70",
                    "quantity": 1,
                    "price": 2499.00
                }
            ],
            "logistics": {
                "company": "顺丰速运",
                "tracking_no": "SF1234567890",
                "status": "in_transit",
                "estimated_delivery": "2024-03-01"
            }
        },
        {
            "order_id": "20240227111111",
            "user_id": "user_test_001",
            "status": "delivered",
            "status_text": "已签收",
            "total_amount": 2299.00,
            "items": [
                {
                    "product_id": "p_002",
                    "name": "iQOO Neo9",
                    "quantity": 1,
                    "price": 2299.00
                }
            ]
        }
    ]


# ==================== Database Fixtures ====================

@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_maker() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db():
    """Override get_db dependency for testing."""
    async with async_session_maker() as session:
        yield session


# ==================== HTTP Client Fixtures ====================

@pytest.fixture
async def client(db_session) -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP client for testing."""
    app.dependency_overrides[get_session] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def auth_client(client: AsyncClient, sample_tenant_data) -> AsyncClient:
    """Create an authenticated client with a test tenant."""
    # Create tenant
    response = await client.post("/api/v1/tenants/", json=sample_tenant_data)
    assert response.status_code == 201
    tenant_data = response.json()

    # Return client with auth headers
    client.headers.update({
        "X-Tenant-ID": tenant_data["tenant_id"],
        "X-API-Key": tenant_data["api_key"]
    })
    return client


@pytest.fixture
async def multi_tenant_clients(client: AsyncClient) -> Dict[str, AsyncClient]:
    """Create multiple authenticated clients for different tenants."""
    tenants = {}
    for i in range(3):
        response = await client.post("/api/v1/tenants/", json={
            "name": f"测试租户{i+1}",
            "api_quota": 1000
        })
        assert response.status_code == 201
        tenant = response.json()
        tenants[f"tenant{i+1}"] = tenant

    # Create separate clients for each tenant
    clients = {}
    for name, tenant in tenants.items():
        transport = ASGITransport(app=app)
        client_copy = AsyncClient(transport=transport, base_url="http://test")
        client_copy.headers.update({
            "X-Tenant-ID": tenant["tenant_id"],
            "X-API-Key": tenant["api_key"]
        })
        clients[name] = client_copy

    return clients


# ==================== Agent Framework Fixtures ====================

@pytest.fixture
def test_config() -> Config:
    """Create a test configuration."""
    return Config(
        provider="anthropic",
        model="glm-4.7",
        api_key="test_key",
        execution={
            "max_steps": 5,
            "enable_audit_log": True,
            "token_budget": 10000
        }
    )


@pytest.fixture
def coordinator(test_config: Config) -> Coordinator:
    """Create a test coordinator."""
    return Coordinator(test_config)


@pytest.fixture
def agent_context() -> AgentContext:
    """Create a test agent context."""
    return AgentContext(
        enable_audit=True,
        tenant_id="tenant_test_001",
        session_id="session_test_001"
    )


# ==================== Async Event Loop ====================

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ==================== Pytest Configuration ====================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests"
    )
    config.addinivalue_line(
        "markers", "e2e: End-to-end tests"
    )
    config.addinivalue_line(
        "markers", "performance: Performance tests"
    )
    config.addinivalue_line(
        "markers", "security: Security tests"
    )
    config.addinivalue_line(
        "markers", "slow: Slow running tests"
    )
    config.addinivalue_line(
        "markers", "tenant: Tenant management tests"
    )
    config.addinivalue_line(
        "markers", "api: API service tests"
    )
    config.addinivalue_line(
        "markers", "ecommerce: Ecommerce demo tests"
    )


# ==================== Test Helpers ====================

class TestHelpers:
    """Helper functions for tests."""

    @staticmethod
    async def create_tenant(client: AsyncClient, name: str, **kwargs) -> Dict[str, Any]:
        """Create a test tenant."""
        data = {"name": name, **kwargs}
        response = await client.post("/api/v1/tenants", json=data)
        assert response.status_code == 201
        return response.json()

    @staticmethod
    async def create_user(client: AsyncClient, tenant_id: str, **kwargs) -> Dict[str, Any]:
        """Create a test user."""
        data = {"tenant_id": tenant_id, **kwargs}
        response = await client.post("/api/v1/users", json=data)
        assert response.status_code == 201
        return response.json()

    @staticmethod
    async def create_skill(client: AsyncClient, tenant_id: str, **kwargs) -> Dict[str, Any]:
        """Create a test skill."""
        data = {"tenant_id": tenant_id, **kwargs}
        response = await client.post("/api/v1/skills", json=data)
        assert response.status_code == 201
        return response.json()


@pytest.fixture
def test_helpers():
    """Provide test helper functions."""
    return TestHelpers
