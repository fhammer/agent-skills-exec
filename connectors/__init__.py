"""数据连接器模块

提供标准化的数据源接入能力，支持：
- 数据库连接器 (PostgreSQL, MySQL, MongoDB, SQLite)
- HTTP API 连接器
- 连接器注册表和管理
"""

from .base import (
    BaseConnector,
    ConnectorConfig,
    ConnectorType,
    ConnectorHealthStatus,
    HealthCheckResult,
    ConnectorStats,
)
from .database import DatabaseConnector, create_database_connector
from .http import HttpConnector, AuthType, create_http_connector
from .registry import ConnectorRegistry, get_connector_registry

__all__ = [
    # 基础类
    "BaseConnector",
    "ConnectorConfig",
    "ConnectorType",
    "ConnectorHealthStatus",
    "HealthCheckResult",
    "ConnectorStats",
    # 数据库连接器
    "DatabaseConnector",
    "create_database_connector",
    # HTTP 连接器
    "HttpConnector",
    "AuthType",
    "create_http_connector",
    # 注册表
    "ConnectorRegistry",
    "get_connector_registry",
]
