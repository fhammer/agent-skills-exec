# Agent Skills Framework - CI/CD Pipeline Design

## 1. CI/CD Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        CI/CD Pipeline Architecture                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      Git Repository (GitHub)                     │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐         │   │
│  │  │  main    │  │ develop  │  │ feature/*│  │ hotfix/* │         │   │
│  │  │  (prod)  │  │  (dev)   │  │          │  │          │         │   │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘         │   │
│  │       │             │             │             │                │   │
│  └───────┼─────────────┼─────────────┼─────────────┼────────────────┘   │
│          │             │             │             │                     │
│          ▼             ▼             ▼             ▼                     │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    GitHub Actions CI Pipeline                    │   │
│  ├─────────────────────────────────────────────────────────────────┤   │
│  │  ┌─────────────────────────────────────────────────────────────┐ │   │
│  │  │                    Stage 1: Code Quality                    │ │   │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │ │   │
│  │  │  │  Lint    │  │  Format  │  │  Type    │  │ Security │     │ │   │
│  │  │  │ (Ruff)   │  │ (Black)  │  │ (MyPy)   │  │ (Bandit) │     │ │   │
│  │  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘     │ │   │
│  │  └───────┼─────────────┼─────────────┼─────────────┼───────────┘ │   │
│  │          │             │             │             │               │   │
│  │          ▼             ▼             ▼             ▼               │   │
│  │  ┌─────────────────────────────────────────────────────────────┐ │   │
│  │  │                    Stage 2: Unit Tests                      │ │   │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │ │   │
│  │  │  │ Coordinator│ │  Planner │  │ Executor │  │ Synthesizer│    │ │   │
│  │  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘     │ │   │
│  │  │       │             │             │             │            │ │   │
│  │  │  ┌────▼─────┐  ┌────▼─────┐  ┌────▼─────┐  ┌────▼─────┐      │ │   │
│  │  │ │  Context │  │   LLM    │  │  Skills  │  │  Utils   │      │ │   │
│  │  │ └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘      │ │   │
│  │  └──────┼─────────────┼─────────────┼─────────────┼────────────┘ │   │
│  │         │             │             │             │              │   │
│  │         ▼             ▼             ▼             ▼              │   │
│  │  ┌─────────────────────────────────────────────────────────────┐ │   │
│  │  │                  Coverage Report (>80%)                     │ │   │
│  │  └─────────────────────────────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    Stage 3: Integration Tests                       │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │   │
│  │  │  API Tests  │  │   DB Tests  │  │ Cache Tests │               │   │
│  │  │  (HTTP)     │  │ (PostgreSQL)│  │  (Redis)    │               │   │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘               │   │
│  │         │                │                │                       │   │
│  │  ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐               │   │
│  │  │  Message    │  │  External   │  │  End-to-End │               │   │
│  │  │  Queue      │  │  Services   │  │  Flow       │               │   │
│  │  │ (RabbitMQ)  │  │  (Mock)     │  │  (Happy Path)│              │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘               │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    Stage 4: E2E Tests                               │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │   │
│  │  │  User Flow  │  │  Critical   │  │  Regression │               │   │
│  │  │  (Playwright)│  │  Path       │  │  Tests      │               │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘               │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    Stage 5: Performance Tests                       │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │   │
│  │  │  Load Test  │  │  Stress     │  │  Soak       │               │   │
│  │  │  (Locust)   │  │  Test       │  │  Test       │               │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘               │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## 2. 测试配置详解

### 2.1 Pytest 配置

```ini
# pyproject.toml
[tool.pytest.ini_options]
minversion = "7.0"
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]

# 标记分类
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "e2e: End-to-end tests",
    "performance: Performance tests",
    "slow: Slow tests",
    "security: Security tests",
]

# 异步支持
asyncio_mode = "auto"

# 覆盖率配置
addopts = """
    --strict-markers
    --disable-warnings
    --tb=short
    --cov=.
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-report=xml:coverage.xml
    --cov-fail-under=80
"""

# 过滤路径
norecursedirs = [
    ".git",
    ".tox",
    ".eggs",
    "*.egg",
    "build",
    "dist",
    "venv",
    ".venv",
]
```

### 2.2 测试 Fixtures

```python
# tests/conftest.py
import asyncio
import os
import tempfile
from datetime import datetime
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

from api.database import Base, get_db
from api.main import app as main_app
from agent.coordinator import Coordinator
from agent.llm_client import LLMClient


# ==================== 事件循环 ====================

@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ==================== 测试容器 ====================

@pytest.fixture(scope="session")
def postgres_container():
    """PostgreSQL 测试容器"""
    with PostgresContainer(
        image="postgres:16-alpine",
        username="test",
        password="test",
        dbname="test_db"
    ) as postgres:
        yield postgres


@pytest.fixture(scope="session")
def redis_container():
    """Redis 测试容器"""
    with RedisContainer(image="redis:7-alpine") as redis:
        yield redis


# ==================== 数据库 Fixtures ====================

@pytest_asyncio.fixture
async def db_engine(postgres_container):
    """创建数据库引擎"""
    database_url = postgres_container.get_connection_url()
    # 转换为异步URL
    async_database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")

    engine = create_async_engine(
        async_database_url,
        echo=False,
        future=True
    )

    # 创建表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # 清理
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """创建数据库会话"""
    async_session_maker = sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()


# ==================== FastAPI Fixtures ====================

@pytest.fixture
def test_app(db_session) -> FastAPI:
    """创建测试用FastAPI应用"""
    # 覆盖依赖
    def override_get_db():
        yield db_session

    main_app.dependency_overrides[get_db] = override_get_db

    return main_app


@pytest_asyncio.fixture
async def async_client(test_app) -> AsyncGenerator[AsyncClient, None]:
    """创建异步HTTP客户端"""
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        yield client


# ==================== Agent Fixtures ====================

@pytest.fixture
def mock_llm_client():
    """Mock LLM客户端"""
    client = Mock(spec=LLMClient)
    client.generate = Mock(return_value={
        "content": "Test response",
        "tokens": 10
    })
    client.generate_async = AsyncMock(return_value={
        "content": "Test async response",
        "tokens": 15
    })
    return client


@pytest.fixture
def coordinator(mock_llm_client):
    """创建Coordinator实例"""
    return Coordinator(
        llm_client=mock_llm_client,
        skills_dir="test_skills"
    )


# ==================== 测试数据 Fixtures ====================

@pytest.fixture
def sample_tenant_data():
    """示例租户数据"""
    return {
        "name": "Test Tenant",
        "description": "Test tenant description",
        "tier": "basic",
        "llm_config": {
            "provider": "anthropic",
            "model": "glm-4.7"
        },
        "quota_config": {
            "token_limit": 1000000,
            "qps_limit": 100
        }
    }


@pytest.fixture
def sample_chat_request():
    """示例聊天请求数据"""
    return {
        "message": "What is the weather today?",
        "session_id": "test_session_001",
        "user_id": "test_user_001",
        "context": {
            "location": "Beijing"
        }
    }


# ==================== 标记和配置 Fixtures ====================

@pytest.fixture(scope="session")
def test_settings():
    """测试配置"""
    return {
        "debug": True,
        "test_database": True,
        "mock_external_services": True,
        "cleanup_after_test": True
    }


@pytest.fixture(autouse=True)
def setup_test_env(test_settings, monkeypatch):
    """自动设置测试环境"""
    # 设置测试模式
    monkeypatch.setenv("TESTING", "true")
    monkeypatch.setenv("DEBUG", str(test_settings["debug"]))

    # 使用测试数据库
    if test_settings["test_database"]:
        monkeypatch.setenv("DATABASE_URL", "sqlite:///./test.db")

    yield

    # 清理
    if test_settings["cleanup_after_test"]:
        # 清理测试数据
        pass
