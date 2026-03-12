"""
业务系统集成适配器 - 提供各种业务系统的适配支持

包含：
- REST API 适配器
- 数据库适配器
- 消息队列适配器
- 文件系统适配器
"""

from .rest_adapter import RESTAdapter, RESTConfig

__all__ = [
    "RESTAdapter",
    "RESTConfig",
]
