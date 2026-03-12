"""
Business Adapter - 业务系统集成适配器

提供业务系统集成的适配器模式，支持与外部系统的连接和通信
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List, Callable, Generic, TypeVar
import time
import uuid
from pathlib import Path
import json

import asyncio


T = TypeVar('T')


class AdapterStatus(Enum):
    """适配器状态"""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class ConnectionMode(Enum):
    """连接模式"""
    SYNC = "sync"
    ASYNC = "async"
    BATCH = "batch"


@dataclass
class AdapterConfig:
    """适配器配置"""
    name: str
    type: str = "generic"
    version: str = "1.0.0"
    description: str = ""
    connection_string: str = ""
    timeout_seconds: int = 30
    retry_count: int = 3
    retry_delay_seconds: float = 1.0
    mode: ConnectionMode = ConnectionMode.ASYNC
    auto_reconnect: bool = True
    heartbeat_interval_seconds: int = 60
    enable_monitoring: bool = False
    custom_settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConnectionStats:
    """连接统计"""
    connection_count: int = 0
    successful_connections: int = 0
    failed_connections: int = 0
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_bytes_sent: int = 0
    total_bytes_received: int = 0
    total_connection_time_ms: float = 0.0
    last_connected_at: Optional[float] = None
    last_disconnected_at: Optional[float] = None
    errors: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class Request:
    """请求"""
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    method: str = "GET"
    path: str = ""
    params: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[Dict[str, Any]] = None
    timeout_seconds: float = 30.0
    timestamp: float = field(default_factory=time.time)


@dataclass
class Response(Generic[T]):
    """响应"""
    request_id: str
    status_code: int = 200
    status_text: str = "OK"
    data: Optional[T] = None
    headers: Dict[str, str] = field(default_factory=dict)
    duration_ms: float = 0.0
    timestamp: float = field(default_factory=time.time)
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        """是否成功"""
        return self.status_code >= 200 and self.status_code < 300 and not self.error

    @property
    def has_error(self) -> bool:
        """是否有错误"""
        return bool(self.error)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "request_id": self.request_id,
            "status_code": self.status_code,
            "status_text": self.status_text,
            "data": self.data,
            "headers": self.headers,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp,
            "error": self.error,
            "metadata": self.metadata,
        }

    @classmethod
    def success(
        cls,
        request_id: str,
        data: Optional[Any] = None,
        duration_ms: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "Response":
        """创建成功响应"""
        return cls(
            request_id=request_id,
            status_code=200,
            status_text="OK",
            data=data,
            duration_ms=duration_ms,
            metadata=metadata or {},
        )

    @classmethod
    def failure(
        cls,
        request_id: str,
        error: str,
        status_code: int = 500,
        status_text: str = "Internal Server Error",
        duration_ms: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "Response":
        """创建失败响应"""
        return cls(
            request_id=request_id,
            status_code=status_code,
            status_text=status_text,
            error=error,
            duration_ms=duration_ms,
            metadata=metadata or {},
        )


class BusinessAdapter(ABC):
    """业务适配器基类

    提供业务系统集成的核心接口
    """

    def __init__(self, config: AdapterConfig):
        self._config = config
        self._status: AdapterStatus = AdapterStatus.UNINITIALIZED
        self._stats: ConnectionStats = ConnectionStats()
        self._created_at: float = time.time()
        self._connected_since: Optional[float] = None

    @property
    def name(self) -> str:
        """名称"""
        return self._config.name

    @property
    def type(self) -> str:
        """类型"""
        return self._config.type

    @property
    def version(self) -> str:
        """版本"""
        return self._config.version

    @property
    def status(self) -> AdapterStatus:
        """状态"""
        return self._status

    @property
    def stats(self) -> ConnectionStats:
        """统计信息"""
        return self._stats

    @property
    def created_at(self) -> float:
        """创建时间"""
        return self._created_at

    @property
    def connected_since(self) -> Optional[float]:
        """连接时间"""
        return self._connected_since

    @property
    def is_connected(self) -> bool:
        """是否已连接"""
        return self._status == AdapterStatus.CONNECTED

    @abstractmethod
    async def initialize(self) -> bool:
        """初始化适配器

        Returns:
            bool: 是否成功
        """
        pass

    @abstractmethod
    async def connect(self) -> bool:
        """建立连接

        Returns:
            bool: 是否成功
        """
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """断开连接

        Returns:
            bool: 是否成功
        """
        pass

    @abstractmethod
    async def send_request(self, request: Request) -> Response:
        """发送请求

        Args:
            request: 请求

        Returns:
            Response: 响应
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查

        Returns:
            bool: 是否健康
        """
        pass

    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """获取元数据

        Returns:
            Dict[str, Any]: 元数据
        """
        pass

    async def reconnect(self, max_retries: int = 0) -> bool:
        """重新连接

        Args:
            max_retries: 最大重试次数

        Returns:
            bool: 是否成功
        """
        retry_count = 0
        while retry_count <= (max_retries or self._config.retry_count):
            try:
                if self.is_connected:
                    await self.disconnect()
                return await self.connect()
            except Exception as e:
                retry_count += 1
                if retry_count > (max_retries or self._config.retry_count):
                    self._record_error("reconnect", str(e))
                    return False
                await asyncio.sleep(self._config.retry_delay_seconds * retry_count)
        return False

    def _record_error(self, operation: str, error: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """记录错误

        Args:
            operation: 操作
            error: 错误信息
            metadata: 元数据
        """
        self._stats.errors.append({
            "operation": operation,
            "error": error,
            "timestamp": time.time(),
            **(metadata or {}),
        })
        if len(self._stats.errors) > 100:
            self._stats.errors = self._stats.errors[-100:]

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.disconnect()

    def __str__(self):
        return f"{self.name} ({self.type}) v{self.version}"


class BaseAdapter(BusinessAdapter):
    """基础适配器实现"""

    def __init__(self, config: AdapterConfig):
        super().__init__(config)

    async def initialize(self) -> bool:
        """初始化适配器"""
        self._status = AdapterStatus.READY
        return True

    async def connect(self) -> bool:
        """建立连接"""
        start_time = time.time()
        self._status = AdapterStatus.CONNECTING
        self._stats.connection_count += 1

        try:
            # 连接逻辑
            await asyncio.sleep(0.1)

            self._status = AdapterStatus.CONNECTED
            self._connected_since = time.time()
            self._stats.successful_connections += 1
            self._stats.last_connected_at = time.time()
            self._stats.total_connection_time_ms += (time.time() - start_time) * 1000

            return True

        except Exception as e:
            self._status = AdapterStatus.ERROR
            self._stats.failed_connections += 1
            self._record_error("connect", str(e))
            return False

    async def disconnect(self) -> bool:
        """断开连接"""
        self._status = AdapterStatus.DISCONNECTING

        try:
            # 断开逻辑
            await asyncio.sleep(0.1)

            if self._connected_since:
                self._stats.total_connection_time_ms += (time.time() - self._connected_since) * 1000

            self._status = AdapterStatus.DISCONNECTED
            self._connected_since = None
            self._stats.last_disconnected_at = time.time()

            return True

        except Exception as e:
            self._status = AdapterStatus.ERROR
            self._record_error("disconnect", str(e))
            return False

    async def send_request(self, request: Request) -> Response:
        """发送请求"""
        start_time = time.time()
        self._stats.total_requests += 1

        if not self.is_connected:
            if self._config.auto_reconnect:
                await self.reconnect()
            if not self.is_connected:
                return Response.failure(
                    request_id=request.request_id,
                    error="Not connected",
                    duration_ms=(time.time() - start_time) * 1000,
                )

        try:
            # 发送请求
            await asyncio.sleep(0.1)

            self._stats.successful_requests += 1
            duration = (time.time() - start_time) * 1000
            return Response.success(
                request_id=request.request_id,
                duration_ms=duration,
            )

        except Exception as e:
            self._stats.failed_requests += 1
            duration = (time.time() - start_time) * 1000
            return Response.failure(
                request_id=request.request_id,
                error=str(e),
                duration_ms=duration,
            )

    async def health_check(self) -> bool:
        """健康检查"""
        if not self.is_connected:
            return False

        try:
            request = Request(
                method="GET",
                path="/health",
                timeout_seconds=5.0,
            )
            response = await self.send_request(request)
            return response.success
        except Exception as e:
            self._record_error("health_check", str(e))
            return False

    def get_metadata(self) -> Dict[str, Any]:
        """获取元数据"""
        return {
            "name": self.name,
            "type": self.type,
            "version": self.version,
            "description": self._config.description,
            "status": self._status.value,
            "connected": self.is_connected,
            "created_at": self._created_at,
            "connected_since": self._connected_since,
            "config": self._config.__dict__,
            "stats": self._stats.__dict__,
        }


@dataclass
class AdapterRegistryConfig:
    """适配器注册表配置"""
    adapters_dir: str = "./adapters"
    enable_auto_discovery: bool = True
    enable_caching: bool = True
    cache_ttl_seconds: int = 3600
    max_adapters: int = 50


class AdapterRegistry:
    """适配器注册表"""

    _instance = None
    _lock = asyncio.Lock()

    @classmethod
    async def get_instance(cls):
        """获取单例"""
        if not cls._instance:
            async with cls._lock:
                if not cls._instance:
                    cls._instance = cls()
        return cls._instance

    def __init__(self):
        self._adapters: Dict[str, BusinessAdapter] = {}
        self._config = AdapterRegistryConfig()
        self._initialized = False

    @property
    def adapters(self) -> Dict[str, BusinessAdapter]:
        """获取所有适配器"""
        return self._adapters.copy()

    async def initialize(self, config: Optional[AdapterRegistryConfig] = None) -> bool:
        """初始化

        Args:
            config: 配置

        Returns:
            bool: 是否成功
        """
        if self._initialized:
            return True

        if config:
            self._config = config

        try:
            if self._config.enable_auto_discovery:
                await self._discover_adapters()
            self._initialized = True
            return True

        except Exception as e:
            return False

    async def _discover_adapters(self) -> None:
        """发现适配器"""
        pass

    async def register_adapter(self, adapter: BusinessAdapter) -> bool:
        """注册适配器

        Args:
            adapter: 适配器

        Returns:
            bool: 是否成功
        """
        if adapter.name in self._adapters:
            return False

        try:
            initialized = await adapter.initialize()
            if initialized:
                self._adapters[adapter.name] = adapter
            return initialized
        except Exception as e:
            return False

    async def unregister_adapter(self, name: str) -> bool:
        """注销适配器

        Args:
            name: 名称

        Returns:
            bool: 是否成功
        """
        adapter = self._adapters.get(name)
        if not adapter:
            return False

        try:
            if adapter.is_connected:
                await adapter.disconnect()
            del self._adapters[name]
            return True
        except Exception as e:
            return False

    async def get_adapter(self, name: str) -> Optional[BusinessAdapter]:
        """获取适配器

        Args:
            name: 名称

        Returns:
            BusinessAdapter: 适配器
        """
        return self._adapters.get(name)

    async def get_adapter_by_type(self, adapter_type: str) -> List[BusinessAdapter]:
        """按类型获取适配器

        Args:
            adapter_type: 类型

        Returns:
            List[BusinessAdapter]: 适配器列表
        """
        return [a for a in self._adapters.values() if a.type == adapter_type]

    async def list_adapters(self, connected: Optional[bool] = None) -> List[BusinessAdapter]:
        """列出适配器

        Args:
            connected: 是否只返回已连接的

        Returns:
            List[BusinessAdapter]: 适配器列表
        """
        if connected is None:
            return list(self._adapters.values())
        return [a for a in self._adapters.values() if a.is_connected == connected]

    def get_metadata(self) -> Dict[str, Any]:
        """获取元数据

        Returns:
            Dict[str, Any]: 元数据
        """
        return {
            "initialized": self._initialized,
            "config": self._config.__dict__,
            "adapters": [
                adapter.get_metadata() for adapter in self._adapters.values()
            ],
            "total": len(self._adapters),
            "connected": sum(1 for a in self._adapters.values() if a.is_connected),
            "disconnected": sum(1 for a in self._adapters.values() if not a.is_connected),
        }
