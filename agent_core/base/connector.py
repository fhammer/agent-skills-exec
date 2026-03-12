"""
Connector 抽象基类 - 连接器核心抽象

定义数据连接器的核心接口和状态管理
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List, AsyncGenerator
import time
import uuid


class ConnectorStatus(Enum):
    """连接器状态"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    ERROR = "error"
    RECONNECTING = "reconnecting"


@dataclass
class ConnectorConfig:
    """连接器配置"""
    name: str
    type: str = "generic"
    version: str = "1.0.0"
    description: str = ""
    connection_string: str = ""
    timeout_seconds: int = 30
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    enable_heartbeat: bool = False
    heartbeat_interval_seconds: int = 60
    auto_reconnect: bool = True
    max_reconnect_attempts: int = 5
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


@dataclass(kw_only=True)
class QueryResult:
    """查询结果"""
    success: bool = False
    connector_name: str = ""
    records: List[Dict[str, Any]] = field(default_factory=list)
    total_count: int = 0
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    started_at: float = field(default_factory=time.time)
    completed_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "connector_name": self.connector_name,
            "records": self.records,
            "total_count": self.total_count,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "metadata": self.metadata,
        }

    @classmethod
    def success(
        cls,
        connector_name: str,
        records: Optional[List[Dict[str, Any]]] = None,
        total_count: Optional[int] = None,
        execution_time_ms: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "QueryResult":
        """创建成功结果"""
        now = time.time()
        record_list = records or []
        return cls(
            success=True,
            connector_name=connector_name,
            records=record_list,
            total_count=total_count if total_count is not None else len(record_list),
            error=None,
            execution_time_ms=execution_time_ms,
            started_at=now - (execution_time_ms / 1000.0) if execution_time_ms > 0 else now,
            completed_at=now,
            metadata=metadata or {},
        )

    @classmethod
    def failure(
        cls,
        connector_name: str,
        error: str,
        execution_time_ms: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "QueryResult":
        """创建失败结果"""
        now = time.time()
        return cls(
            success=False,
            connector_name=connector_name,
            records=[],
            total_count=0,
            error=error,
            execution_time_ms=execution_time_ms,
            started_at=now - (execution_time_ms / 1000.0) if execution_time_ms > 0 else now,
            completed_at=now,
            metadata=metadata or {},
        )


class BaseConnector(ABC):
    """连接器抽象基类

    所有自定义连接器都应该继承此类
    """

    def __init__(self, config: ConnectorConfig):
        self.config = config
        self._status = ConnectorStatus.DISCONNECTED
        self._created_at = time.time()
        self._connected_since: Optional[float] = None
        self._stats = ConnectionStats()

    @property
    def name(self) -> str:
        """获取连接器名称"""
        return self.config.name

    @property
    def type(self) -> str:
        """获取连接器类型"""
        return self.config.type

    @property
    def version(self) -> str:
        """获取连接器版本"""
        return self.config.version

    @property
    def status(self) -> ConnectorStatus:
        """获取连接器状态"""
        return self._status

    @property
    def created_at(self) -> float:
        """创建时间戳"""
        return self._created_at

    @property
    def connected_since(self) -> Optional[float]:
        """连接开始时间"""
        return self._connected_since

    @property
    def is_connected(self) -> bool:
        """是否已连接"""
        return self._status == ConnectorStatus.CONNECTED

    @property
    def stats(self) -> ConnectionStats:
        """获取连接统计"""
        return self._stats

    async def connect(self) -> bool:
        """连接

        Returns:
            bool: 连接是否成功
        """
        start_time = time.time()
        self._status = ConnectorStatus.CONNECTING
        self._stats.connection_count += 1

        try:
            # 连接前钩子
            await self._before_connect()

            # 执行连接
            result = await self._connect()

            if result:
                self._status = ConnectorStatus.CONNECTED
                self._connected_since = time.time()
                self._stats.successful_connections += 1
                self._stats.last_connected_at = time.time()

                # 连接后钩子
                await self._after_connect()

                return True
            else:
                self._status = ConnectorStatus.ERROR
                self._stats.failed_connections += 1
                return False

        except Exception as e:
            self._status = ConnectorStatus.ERROR
            self._stats.failed_connections += 1
            self._record_error("connect", str(e))
            await self._on_error(e)
            return False

    @abstractmethod
    async def _connect(self) -> bool:
        """执行连接 - 子类必须实现

        Returns:
            bool: 连接是否成功
        """
        pass

    async def _before_connect(self) -> None:
        """连接前钩子 - 子类可重写"""
        pass

    async def _after_connect(self) -> None:
        """连接后钩子 - 子类可重写"""
        pass

    async def disconnect(self) -> bool:
        """断开连接

        Returns:
            bool: 断开是否成功
        """
        start_time = time.time()
        self._status = ConnectorStatus.DISCONNECTING

        try:
            # 断开前钩子
            await self._before_disconnect()

            # 执行断开
            result = await self._disconnect()

            if result:
                if self._connected_since:
                    connection_time_ms = (time.time() - self._connected_since) * 1000
                    self._stats.total_connection_time_ms += connection_time_ms

                self._status = ConnectorStatus.DISCONNECTED
                self._connected_since = None
                self._stats.last_disconnected_at = time.time()

                # 断开后钩子
                await self._after_disconnect()

                return True
            else:
                self._status = ConnectorStatus.ERROR
                return False

        except Exception as e:
            self._status = ConnectorStatus.ERROR
            self._record_error("disconnect", str(e))
            await self._on_error(e)
            return False

    @abstractmethod
    async def _disconnect(self) -> bool:
        """执行断开 - 子类必须实现

        Returns:
            bool: 断开是否成功
        """
        pass

    async def _before_disconnect(self) -> None:
        """断开前钩子 - 子类可重写"""
        pass

    async def _after_disconnect(self) -> None:
        """断开后钩子 - 子类可重写"""
        pass

    async def reconnect(self) -> bool:
        """重新连接

        Returns:
            bool: 重连是否成功
        """
        self._status = ConnectorStatus.RECONNECTING

        # 先断开（如果已连接）
        if self.is_connected:
            await self.disconnect()

        # 重试连接
        max_attempts = self.config.max_reconnect_attempts
        for attempt in range(1, max_attempts + 1):
            try:
                result = await self.connect()
                if result:
                    return True
            except Exception:
                pass

            if attempt < max_attempts:
                import asyncio
                delay = self.config.retry_delay_seconds * attempt
                await asyncio.sleep(delay)

        return False

    async def execute(
        self,
        operation: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> QueryResult:
        """执行操作

        Args:
            operation: 操作名称
            parameters: 操作参数

        Returns:
            QueryResult: 查询结果
        """
        start_time = time.time()
        self._stats.total_requests += 1

        try:
            # 检查连接
            if not self.is_connected:
                if self.config.auto_reconnect:
                    await self.reconnect()
                if not self.is_connected:
                    return QueryResult.failure(
                        connector_name=self.name,
                        error="Not connected",
                        execution_time_ms=(time.time() - start_time) * 1000,
                    )

            # 执行前钩子
            await self._before_execute(operation, parameters or {})

            # 执行核心逻辑
            result = await self._execute(operation, parameters or {})

            # 执行后钩子
            await self._after_execute(operation, parameters or {}, result)

            # 更新统计
            if result.success:
                self._stats.successful_requests += 1
            else:
                self._stats.failed_requests += 1

            result.execution_time_ms = (time.time() - start_time) * 1000

            return result

        except Exception as e:
            self._stats.failed_requests += 1
            self._record_error("execute", str(e))
            await self._on_error(e)
            execution_time_ms = (time.time() - start_time) * 1000
            return QueryResult.failure(
                connector_name=self.name,
                error=str(e),
                execution_time_ms=execution_time_ms,
            )

    @abstractmethod
    async def _execute(
        self,
        operation: str,
        parameters: Dict[str, Any]
    ) -> QueryResult:
        """执行核心逻辑 - 子类必须实现

        Args:
            operation: 操作名称
            parameters: 操作参数

        Returns:
            QueryResult: 查询结果
        """
        pass

    async def _before_execute(self, operation: str, parameters: Dict[str, Any]) -> None:
        """执行前钩子 - 子类可重写

        Args:
            operation: 操作名称
            parameters: 操作参数
        """
        pass

    async def _after_execute(
        self,
        operation: str,
        parameters: Dict[str, Any],
        result: QueryResult
    ) -> None:
        """执行后钩子 - 子类可重写

        Args:
            operation: 操作名称
            parameters: 操作参数
            result: 查询结果
        """
        pass

    async def query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> QueryResult:
        """执行查询（快捷方法）

        Args:
            query: 查询语句
            parameters: 查询参数

        Returns:
            QueryResult: 查询结果
        """
        return await self.execute("query", {"query": query, **(parameters or {})})

    async def stream(
        self,
        operation: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """流式执行

        Args:
            operation: 操作名称
            parameters: 操作参数

        Yields:
            Dict[str, Any]: 数据流
        """
        try:
            async for item in self._stream(operation, parameters or {}):
                yield item
        except Exception as e:
            self._record_error("stream", str(e))
            await self._on_error(e)
            raise

    async def _stream(
        self,
        operation: str,
        parameters: Dict[str, Any]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """流式执行 - 子类可重写

        Args:
            operation: 操作名称
            parameters: 操作参数

        Yields:
            Dict[str, Any]: 数据流
        """
        # 默认实现：先执行再流式返回
        result = await self.execute(operation, parameters)
        for record in result.records:
            yield record

    async def check_connection(self) -> bool:
        """检查连接状态

        Returns:
            bool: 连接是否正常
        """
        try:
            return await self._check_connection()
        except Exception:
            return False

    async def _check_connection(self) -> bool:
        """检查连接状态 - 子类可重写

        Returns:
            bool: 连接是否正常
        """
        return self.is_connected

    async def heartbeat(self) -> bool:
        """发送心跳

        Returns:
            bool: 心跳是否成功
        """
        try:
            return await self._heartbeat()
        except Exception:
            return False

    async def _heartbeat(self) -> bool:
        """发送心跳 - 子类可重写

        Returns:
            bool: 心跳是否成功
        """
        return await self.check_connection()

    async def _on_error(self, error: Exception) -> None:
        """错误处理钩子 - 子类可重写

        Args:
            error: 异常对象
        """
        pass

    def _record_error(self, operation: str, error: str) -> None:
        """记录错误

        Args:
            operation: 操作名称
            error: 错误信息
        """
        self._stats.errors.append({
            "operation": operation,
            "error": error,
            "timestamp": time.time(),
        })
        # 只保留最近100个错误
        if len(self._stats.errors) > 100:
            self._stats.errors = self._stats.errors[-100:]

    def get_metadata(self) -> Dict[str, Any]:
        """获取连接器元数据

        Returns:
            Dict[str, Any]: 元数据字典
        """
        return {
            "name": self.name,
            "type": self.type,
            "version": self.version,
            "description": self.config.description,
            "status": self.status.value,
            "is_connected": self.is_connected,
            "created_at": self.created_at,
            "connected_since": self.connected_since,
            "stats": {
                "connection_count": self._stats.connection_count,
                "successful_connections": self._stats.successful_connections,
                "failed_connections": self._stats.failed_connections,
                "total_requests": self._stats.total_requests,
                "successful_requests": self._stats.successful_requests,
                "failed_requests": self._stats.failed_requests,
                "total_bytes_sent": self._stats.total_bytes_sent,
                "total_bytes_received": self._stats.total_bytes_received,
                "total_connection_time_ms": self._stats.total_connection_time_ms,
                "last_connected_at": self._stats.last_connected_at,
                "last_disconnected_at": self._stats.last_disconnected_at,
                "error_count": len(self._stats.errors),
            },
        }

    def __str__(self):
        return f"{self.name} ({self.type}) - {self.status.value}"

    def __repr__(self):
        return f"{self.__class__.__name__}(name={self.name}, type={self.type}, status={self.status.value})"
