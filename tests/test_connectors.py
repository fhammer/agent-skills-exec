"""
数据连接器模块测试
"""

import pytest
import asyncio
from connectors.base import (
    ConnectorConfig,
    ConnectorType,
    ConnectorHealthStatus,
)
from connectors.database import DatabaseConnector, create_database_connector
from connectors.http import HttpConnector, AuthType, create_http_connector
from connectors.registry import ConnectorRegistry, get_connector_registry


class TestConnectorConfig:
    """连接器配置测试"""

    def test_create_database_config(self):
        """测试创建数据库配置"""
        config = ConnectorConfig(
            name="test_db",
            type=ConnectorType.DATABASE,
            connection_params={
                "db_type": "postgresql",
                "host": "localhost",
                "port": 5432,
                "database": "test",
                "user": "postgres",
                "password": "password",
            },
        )

        assert config.name == "test_db"
        assert config.type == ConnectorType.DATABASE
        assert config.pool_size == 10
        assert config.retry_attempts == 3

    def test_create_http_config(self):
        """测试创建HTTP配置"""
        config = ConnectorConfig(
            name="test_api",
            type=ConnectorType.HTTP,
            connection_params={
                "base_url": "https://api.example.com",
                "auth": {
                    "type": "bearer",
                    "token": "test_token",
                },
            },
        )

        assert config.name == "test_api"
        assert config.type == ConnectorType.HTTP


class TestHttpConnector:
    """HTTP连接器测试"""

    @pytest.mark.asyncio
    async def test_http_connector_init(self):
        """测试HTTP连接器初始化"""
        config = ConnectorConfig(
            name="test_api",
            type=ConnectorType.HTTP,
            connection_params={
                "base_url": "https://httpbin.org",
            },
        )

        connector = HttpConnector(config)
        assert connector.config.name == "test_api"
        assert connector._base_url == "https://httpbin.org"

    @pytest.mark.asyncio
    async def test_http_connector_connect(self):
        """测试HTTP连接器连接"""
        config = ConnectorConfig(
            name="httpbin",
            type=ConnectorType.HTTP,
            connection_params={
                "base_url": "https://httpbin.org",
            },
        )

        connector = HttpConnector(config)
        success = await connector.connect()

        assert success is True
        assert connector.is_connected is True
        assert connector.health_status == ConnectorHealthStatus.HEALTHY

        await connector.disconnect()

    @pytest.mark.asyncio
    async def test_http_get_request(self):
        """测试HTTP GET请求"""
        config = ConnectorConfig(
            name="httpbin",
            type=ConnectorType.HTTP,
            connection_params={
                "base_url": "https://httpbin.org",
            },
        )

        connector = HttpConnector(config)
        await connector.connect()

        result = await connector.get("/get", params={"test": "value"})

        assert result is not None
        assert "args" in result
        assert result["args"]["test"] == "value"

        await connector.disconnect()

    def test_build_url(self):
        """测试URL构建"""
        config = ConnectorConfig(
            name="test",
            type=ConnectorType.HTTP,
            connection_params={
                "base_url": "https://api.example.com",
            },
        )

        connector = HttpConnector(config)

        assert connector._build_url("/users") == "https://api.example.com/users"
        assert connector._build_url("users") == "https://api.example.com/users"


class TestConnectorRegistry:
    """连接器注册表测试"""

    @pytest.mark.asyncio
    async def test_register_connector(self):
        """测试注册连接器"""
        registry = ConnectorRegistry()

        config = ConnectorConfig(
            name="test_api",
            type=ConnectorType.HTTP,
            connection_params={
                "base_url": "https://httpbin.org",
            },
            enabled=True,
        )

        connector = await registry.register(config)

        assert connector is not None
        assert connector.config.name == "test_api"
        assert "test_api" in registry.list_all()

    @pytest.mark.asyncio
    async def test_get_connector(self):
        """测试获取连接器"""
        registry = ConnectorRegistry()

        config = ConnectorConfig(
            name="test_api",
            type=ConnectorType.HTTP,
            connection_params={
                "base_url": "https://httpbin.org",
            },
        )

        await registry.register(config)

        connector = registry.get("test_api")
        assert connector is not None
        assert connector.config.name == "test_api"

    @pytest.mark.asyncio
    async def test_unregister_connector(self):
        """测试注销连接器"""
        registry = ConnectorRegistry()

        config = ConnectorConfig(
            name="test_api",
            type=ConnectorType.HTTP,
            connection_params={
                "base_url": "https://httpbin.org",
            },
        )

        await registry.register(config)
        assert "test_api" in registry.list_all()

        await registry.unregister("test_api")
        assert "test_api" not in registry.list_all()

    @pytest.mark.asyncio
    async def test_get_statistics(self):
        """测试获取统计信息"""
        registry = ConnectorRegistry()

        config1 = ConnectorConfig(
            name="api1",
            type=ConnectorType.HTTP,
            connection_params={"base_url": "https://api1.com"},
        )

        config2 = ConnectorConfig(
            name="db1",
            type=ConnectorType.DATABASE,
            connection_params={"db_type": "sqlite", "database": ":memory:"},
        )

        await registry.register(config1)
        await registry.register(config2)

        stats = registry.get_statistics()

        assert stats["total"] == 2
        assert stats["by_type"]["http"] == 1
        assert stats["by_type"]["database"] == 1


@pytest.mark.asyncio
async def test_connector_registry_singleton():
    """测试连接器注册表单例"""
    registry1 = get_connector_registry()
    registry2 = get_connector_registry()

    assert registry1 is registry2
