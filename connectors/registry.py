"""
连接器注册表

管理所有数据源连接器的注册、发现和生命周期。
"""

import asyncio
import logging
from typing import Dict, List, Optional, Type
from threading import Lock

from connectors.base import (
    BaseConnector,
    ConnectorConfig,
    ConnectorType,
    ConnectorHealthStatus,
)
from connectors.database import DatabaseConnector
from connectors.http import HttpConnector

logger = logging.getLogger(__name__)


class ConnectorRegistry:
    """
    连接器注册表

    管理所有连接器的注册、初始化、获取和清理。
    """

    # 连接器类型映射
    CONNECTOR_TYPES: Dict[ConnectorType, Type[BaseConnector]] = {
        ConnectorType.DATABASE: DatabaseConnector,
        ConnectorType.HTTP: HttpConnector,
    }

    def __init__(self):
        self._connectors: Dict[str, BaseConnector] = {}
        self._configs: Dict[str, ConnectorConfig] = {}
        self._lock = Lock()
        self._initialized = False

    @classmethod
    def register_connector_type(cls, connector_type: ConnectorType, connector_class: Type[BaseConnector]):
        """注册连接器类型"""
        cls.CONNECTOR_TYPES[connector_type] = connector_class
        logger.info(f"注册连接器类型: {connector_type.value} -> {connector_class.__name__}")

    async def initialize(self, configs: List[ConnectorConfig]):
        """
        初始化注册表

        Args:
            configs: 连接器配置列表
        """
        if self._initialized:
            logger.warning("连接器注册表已经初始化")
            return

        logger.info(f"初始化连接器注册表，配置数量: {len(configs)}")

        for config in configs:
            if not config.enabled:
                logger.info(f"跳过已禁用的连接器: {config.name}")
                continue

            try:
                await self.register(config)
            except Exception as e:
                logger.error(f"注册连接器失败 {config.name}: {e}")

        self._initialized = True
        logger.info(f"连接器注册表初始化完成，成功注册 {len(self._connectors)} 个连接器")

    async def register(self, config: ConnectorConfig) -> BaseConnector:
        """
        注册连接器

        Args:
            config: 连接器配置

        Returns:
            连接器实例
        """
        with self._lock:
            # 检查是否已存在
            if config.name in self._connectors:
                logger.warning(f"连接器已存在，将先注销: {config.name}")
                await self.unregister(config.name)

            # 创建连接器
            connector_class = self.CONNECTOR_TYPES.get(config.type)
            if not connector_class:
                raise ValueError(f"不支持的连接器类型: {config.type}")

            connector = connector_class(config)

            # 初始化连接器
            success = await connector.initialize()
            if not success:
                raise RuntimeError(f"连接器初始化失败: {config.name}")

            # 注册
            self._connectors[config.name] = connector
            self._configs[config.name] = config

            logger.info(f"注册连接器成功: {config.name} ({config.type.value})")
            return connector

    async def unregister(self, name: str) -> bool:
        """
        注销连接器

        Args:
            name: 连接器名称

        Returns:
            是否成功
        """
        with self._lock:
            connector = self._connectors.get(name)
            if not connector:
                logger.warning(f"连接器不存在: {name}")
                return False

            # 关闭连接器
            await connector.shutdown()

            # 移除
            del self._connectors[name]
            del self._configs[name]

            logger.info(f"注销连接器: {name}")
            return True

    def get(self, name: str) -> Optional[BaseConnector]:
        """
        获取连接器

        Args:
            name: 连接器名称

        Returns:
            连接器实例
        """
        return self._connectors.get(name)

    def get_by_type(self, connector_type: ConnectorType) -> List[BaseConnector]:
        """
        按类型获取连接器

        Args:
            connector_type: 连接器类型

        Returns:
            连接器列表
        """
        return [
            conn for conn in self._connectors.values()
            if self._configs[conn.config.name].type == connector_type
        ]

    def list_all(self) -> List[str]:
        """列出所有连接器名称"""
        return list(self._connectors.keys())

    def list_healthy(self) -> List[str]:
        """列出健康的连接器"""
        return [
            name for name, conn in self._connectors.items()
            if conn.health_status == ConnectorHealthStatus.HEALTHY
        ]

    def list_unhealthy(self) -> List[str]:
        """列出不健康的连接器"""
        return [
            name for name, conn in self._connectors.items()
            if conn.health_status != ConnectorHealthStatus.HEALTHY
        ]

    async def health_check_all(self) -> Dict[str, ConnectorHealthStatus]:
        """
        检查所有连接器的健康状态

        Returns:
            健康状态字典 {connector_name: health_status}
        """
        results = {}
        for name, connector in self._connectors.items():
            try:
                result = await connector.health_check()
                results[name] = result.status
            except Exception as e:
                logger.error(f"健康检查失败 {name}: {e}")
                results[name] = ConnectorHealthStatus.UNHEALTHY
        return results

    async def shutdown_all(self):
        """关闭所有连接器"""
        logger.info("关闭所有连接器...")
        for name in list(self._connectors.keys()):
            await self.unregister(name)
        logger.info("所有连接器已关闭")

    def get_statistics(self) -> Dict[str, any]:
        """获取统计信息"""
        healthy = len(self.list_healthy())
        unhealthy = len(self.list_unhealthy())

        # 按类型统计
        by_type = {}
        for config in self._configs.values():
            type_name = config.type.value
            by_type[type_name] = by_type.get(type_name, 0) + 1

        return {
            "total": len(self._connectors),
            "healthy": healthy,
            "unhealthy": unhealthy,
            "by_type": by_type,
        }


# 全局单例
_connector_registry: Optional[ConnectorRegistry] = None
_registry_lock = Lock()


def get_connector_registry() -> ConnectorRegistry:
    """获取连接器注册表单例"""
    global _connector_registry
    if _connector_registry is None:
        with _registry_lock:
            if _connector_registry is None:
                _connector_registry = ConnectorRegistry()
    return _connector_registry
