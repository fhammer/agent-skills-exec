"""数据连接器基类和配置"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import logging

logger = logging.getLogger(__name__)


class ConnectorType(Enum):
    """连接器类型"""
    DATABASE = "database"
    HTTP = "http"
    MESSAGE_QUEUE = "message_queue"
    CACHE = "cache"
    FILE_STORAGE = "file_storage"


class ConnectorHealthStatus(Enum):
    """健康状态"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ConnectorConfig:
    """数据源配置基类"""
    name: str
    type: ConnectorType
    connection_params: Dict[str, Any]

    # 连接池配置
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600

    # 重试配置
    retry_attempts: int = 3
    retry_delay: float = 1.0
    retry_backoff: float = 2.0

    # 超时配置
    connect_timeout: int = 10
    read_timeout: int = 30
    write_timeout: int = 30

    # 健康检查配置
    health_check_interval: int = 30
    health_check_timeout: int = 5

    # SSL/TLS配置
    ssl_enabled: bool = False
    ssl_verify: bool = True
    ssl_cert: Optional[str] = None

    # 其他配置
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "type": self.type.value,
            "enabled": self.enabled,
            "pool_size": self.pool_size,
            "retry_attempts": self.retry_attempts,
            "connect_timeout": self.connect_timeout,
            "read_timeout": self.read_timeout,
            "write_timeout": self.write_timeout,
            "health_check_interval": self.health_check_interval,
            "ssl_enabled": self.ssl_enabled,
            "metadata": self.metadata
        }


@dataclass
class HealthCheckResult:
    """健康检查结果"""
    status: ConnectorHealthStatus
    message: str
    latency_ms: Optional[float] = None
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: asyncio.get_event_loop().time().__str__)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "message": self.message,
            "latency_ms": self.latency_ms,
            "details": self.details,
            "timestamp": self.timestamp
        }


@dataclass
class ConnectorStats:
    """连接器统计信息"""
    name: str
    type: str

    # 连接统计
    total_connections: int = 0
    active_connections: int = 0
    failed_connections: int = 0

    # 请求统计
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0

    # 延迟统计 (毫秒)
    avg_latency_ms: float = 0
    min_latency_ms: float = float('inf')
    max_latency_ms: float = 0
    p50_latency_ms: float = 0
    p95_latency_ms: float = 0
    p99_latency_ms: float = 0

    # 错误统计
    error_rate: float = 0
    last_error: Optional[str] = None
    last_error_time: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type,
            "connections": {
                "total": self.total_connections,
                "active": self.active_connections,
                "failed": self.failed_connections
            },
            "requests": {
                "total": self.total_requests,
                "successful": self.successful_requests,
                "failed": self.failed_requests
            },
            "latency_ms": {
                "avg": self.avg_latency_ms,
                "min": self.min_latency_ms if self.min_latency_ms != float('inf') else 0,
                "max": self.max_latency_ms,
                "p50": self.p50_latency_ms,
                "p95": self.p95_latency_ms,
                "p99": self.p99_latency_ms
            },
            "errors": {
                "rate": self.error_rate,
                "last": self.last_error,
                "last_time": self.last_error_time
            }
        }


class BaseConnector(ABC):
    """数据源连接器基类

    所有连接器必须实现此基类定义的接口。
    """

    def __init__(self, config: ConnectorConfig):
        self.config = config
        self._connection = None
        self._health_status = ConnectorHealthStatus.UNKNOWN
        self._stats = ConnectorStats(name=config.name, type=config.type.value)
        self._health_check_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        logger.info(f"初始化连接器: {config.name} ({config.type.value})")

    @abstractmethod
    async def connect(self) -> bool:
        """建立连接

        Returns:
            bool: 连接成功返回 True
        """
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """断开连接

        Returns:
            bool: 断开成功返回 True
        """
        pass

    @abstractmethod
    async def health_check(self) -> HealthCheckResult:
        """健康检查

        Returns:
            HealthCheckResult: 健康检查结果
        """
        pass

    @property
    def is_connected(self) -> bool:
        """连接状态"""
        return self._connection is not None

    @property
    def health_status(self) -> ConnectorHealthStatus:
        """健康状态"""
        return self._health_status

    @property
    def stats(self) -> ConnectorStats:
        """统计信息"""
        return self._stats

    async def initialize(self) -> bool:
        """初始化连接器

        建立连接并启动健康检查任务
        """
        try:
            success = await self.connect()
            if success:
                # 启动健康检查任务
                if self.config.health_check_interval > 0:
                    self._health_check_task = asyncio.create_task(
                        self._health_check_loop()
                    )
                logger.info(f"连接器 {self.config.name} 初始化成功")
            return success
        except Exception as e:
            logger.error(f"连接器 {self.config.name} 初始化失败: {e}")
            self._health_status = ConnectorHealthStatus.UNHEALTHY
            return False

    async def shutdown(self) -> bool:
        """关闭连接器"""
        # 取消健康检查任务
        if self._health_check_task and not self._health_check_task.done():
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

        # 断开连接
        return await self.disconnect()

    async def _health_check_loop(self):
        """健康检查循环"""
        while True:
            try:
                result = await self.health_check()
                self._health_status = result.status
                await asyncio.sleep(self.config.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"健康检查失败: {e}")
                self._health_status = ConnectorHealthStatus.UNHEALTHY
                await asyncio.sleep(self.config.health_check_interval)

    async def _execute_with_retry(self, operation, *args, **kwargs):
        """带重试的操作执行"""
        last_error = None
        for attempt in range(self.config.retry_attempts):
            try:
                return await operation(*args, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < self.config.retry_attempts - 1:
                    delay = self.config.retry_delay * (
                        self.config.retry_backoff ** attempt
                    )
                    logger.warning(
                        f"操作失败，{delay}秒后重试 (尝试 {attempt + 1}/{self.config.retry_attempts}): {e}"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"操作失败，已达最大重试次数: {e}")
                    self._stats.failed_requests += 1
                    self._stats.last_error = str(e)
                    raise

    def _update_latency_stats(self, latency_ms: float):
        """更新延迟统计"""
        self._stats.total_requests += 1
        self._stats.successful_requests += 1

        # 更新最小/最大延迟
        if latency_ms < self._stats.min_latency_ms:
            self._stats.min_latency_ms = latency_ms
        if latency_ms > self._stats.max_latency_ms:
            self._stats.max_latency_ms = latency_ms

        # 更新平均延迟 (简单移动平均)
        self._stats.avg_latency_ms = (
            (self._stats.avg_latency_ms * (self._stats.successful_requests - 1) + latency_ms)
            / self._stats.successful_requests
        )

        # 计算错误率
        if self._stats.total_requests > 0:
            self._stats.error_rate = self._stats.failed_requests / self._stats.total_requests
