"""
Tool 抽象基类 - 工具核心抽象

定义工具的核心接口和执行上下文
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List
import time
import uuid


class ToolStatus(Enum):
    """工具状态"""
    INACTIVE = "inactive"
    READY = "ready"
    RUNNING = "running"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class ToolConfig:
    """工具配置"""
    name: str
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    tags: List[str] = field(default_factory=list)
    requires_authentication: bool = False
    timeout_seconds: int = 30
    max_retries: int = 3
    rate_limit_per_minute: int = 60
    custom_settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolContext:
    """工具执行上下文"""
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tool_name: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    user_input: str = ""
    environment: Dict[str, Any] = field(default_factory=dict)
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    started_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "request_id": self.request_id,
            "tool_name": self.tool_name,
            "parameters": self.parameters,
            "user_input": self.user_input,
            "environment": self.environment,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "started_at": self.started_at,
            "metadata": self.metadata,
        }


@dataclass
class ToolResult:
    """工具执行结果"""
    success: bool = False
    tool_name: str = ""
    structured: Dict[str, Any] = field(default_factory=dict)
    text: str = ""
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    started_at: float = field(default_factory=time.time)
    completed_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "tool_name": self.tool_name,
            "structured": self.structured,
            "text": self.text,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "metadata": self.metadata,
        }

    @classmethod
    def success(
        cls,
        tool_name: str,
        structured: Optional[Dict[str, Any]] = None,
        text: str = "",
        execution_time_ms: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "ToolResult":
        """创建成功结果"""
        now = time.time()
        return cls(
            success=True,
            tool_name=tool_name,
            structured=structured or {},
            text=text,
            error=None,
            execution_time_ms=execution_time_ms,
            started_at=now - (execution_time_ms / 1000.0) if execution_time_ms > 0 else now,
            completed_at=now,
            metadata=metadata or {},
        )

    @classmethod
    def failure(
        cls,
        tool_name: str,
        error: str,
        execution_time_ms: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "ToolResult":
        """创建失败结果"""
        now = time.time()
        return cls(
            success=False,
            tool_name=tool_name,
            structured={},
            text="",
            error=error,
            execution_time_ms=execution_time_ms,
            started_at=now - (execution_time_ms / 1000.0) if execution_time_ms > 0 else now,
            completed_at=now,
            metadata=metadata or {},
        )


class BaseTool(ABC):
    """工具抽象基类

    所有自定义工具都应该继承此类
    """

    def __init__(self, config: ToolConfig):
        self.config = config
        self._status = ToolStatus.INACTIVE
        self._created_at = time.time()
        self._last_executed_at: Optional[float] = None
        self._execution_count = 0
        self._success_count = 0
        self._error_count = 0
        self._total_execution_time_ms = 0.0

    @property
    def name(self) -> str:
        """获取工具名称"""
        return self.config.name

    @property
    def version(self) -> str:
        """获取工具版本"""
        return self.config.version

    @property
    def status(self) -> ToolStatus:
        """获取工具状态"""
        return self._status

    @property
    def created_at(self) -> float:
        """创建时间戳"""
        return self._created_at

    @property
    def last_executed_at(self) -> Optional[float]:
        """最后执行时间戳"""
        return self._last_executed_at

    @property
    def execution_count(self) -> int:
        """执行次数"""
        return self._execution_count

    @property
    def success_count(self) -> int:
        """成功次数"""
        return self._success_count

    @property
    def error_count(self) -> int:
        """错误次数"""
        return self._error_count

    @property
    def avg_execution_time_ms(self) -> float:
        """平均执行时间"""
        if self._execution_count == 0:
            return 0.0
        return self._total_execution_time_ms / self._execution_count

    async def initialize(self) -> bool:
        """初始化工具

        Returns:
            bool: 初始化是否成功
        """
        try:
            result = await self._on_initialize()
            if result:
                self._status = ToolStatus.READY
            return result
        except Exception as e:
            self._status = ToolStatus.ERROR
            await self._on_error(e)
            return False

    @abstractmethod
    async def _on_initialize(self) -> bool:
        """初始化钩子 - 子类实现

        Returns:
            bool: 初始化是否成功
        """
        return True

    async def execute(
        self,
        context: ToolContext
    ) -> ToolResult:
        """执行工具

        Args:
            context: 执行上下文

        Returns:
            ToolResult: 执行结果
        """
        start_time = time.time()
        self._status = ToolStatus.RUNNING
        self._execution_count += 1

        try:
            # 执行前钩子
            await self._before_execute(context)

            # 执行核心逻辑
            result = await self._execute(context)

            # 执行后钩子
            await self._after_execute(context, result)

            # 更新统计
            self._success_count += 1
            result.execution_time_ms = (time.time() - start_time) * 1000
            self._total_execution_time_ms += result.execution_time_ms
            self._status = ToolStatus.READY
            self._last_executed_at = time.time()

            return result

        except Exception as e:
            self._error_count += 1
            await self._on_error(e)
            self._status = ToolStatus.ERROR
            self._last_executed_at = time.time()
            execution_time_ms = (time.time() - start_time) * 1000
            self._total_execution_time_ms += execution_time_ms
            return ToolResult.failure(
                tool_name=self.name,
                error=str(e),
                execution_time_ms=execution_time_ms,
            )

    @abstractmethod
    async def _execute(self, context: ToolContext) -> ToolResult:
        """执行核心逻辑 - 子类必须实现

        Args:
            context: 执行上下文

        Returns:
            ToolResult: 执行结果
        """
        pass

    async def _before_execute(self, context: ToolContext) -> None:
        """执行前钩子 - 子类可重写

        Args:
            context: 执行上下文
        """
        pass

    async def _after_execute(self, context: ToolContext, result: ToolResult) -> None:
        """执行后钩子 - 子类可重写

        Args:
            context: 执行上下文
            result: 执行结果
        """
        pass

    async def _on_error(self, error: Exception) -> None:
        """错误处理钩子 - 子类可重写

        Args:
            error: 异常对象
        """
        pass

    async def shutdown(self) -> bool:
        """关闭工具

        Returns:
            bool: 关闭是否成功
        """
        try:
            result = await self._on_shutdown()
            self._status = ToolStatus.INACTIVE
            return result
        except Exception as e:
            await self._on_error(e)
            return False

    @abstractmethod
    async def _on_shutdown(self) -> bool:
        """关闭钩子 - 子类实现

        Returns:
            bool: 关闭是否成功
        """
        return True

    async def validate_parameters(self, parameters: Dict[str, Any]) -> List[str]:
        """验证输入参数

        Args:
            parameters: 参数字典

        Returns:
            List[str]: 错误列表
        """
        errors = []
        try:
            errors.extend(await self._validate_parameters(parameters))
        except Exception as e:
            errors.append(str(e))
        return errors

    async def _validate_parameters(self, parameters: Dict[str, Any]) -> List[str]:
        """验证输入参数 - 子类可重写

        Args:
            parameters: 参数字典

        Returns:
            List[str]: 错误列表
        """
        return []

    def get_metadata(self) -> Dict[str, Any]:
        """获取工具元数据

        Returns:
            Dict[str, Any]: 元数据字典
        """
        return {
            "name": self.name,
            "version": self.version,
            "description": self.config.description,
            "author": self.config.author,
            "tags": self.config.tags,
            "requires_authentication": self.config.requires_authentication,
            "status": self.status.value,
            "created_at": self.created_at,
            "last_executed_at": self.last_executed_at,
            "execution_count": self.execution_count,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "avg_execution_time_ms": self.avg_execution_time_ms,
        }

    def __str__(self):
        return f"{self.name} (v{self.version}) - {self.status.value}"

    def __repr__(self):
        return f"{self.__class__.__name__}(name={self.name}, version={self.version}, status={self.status.value})"
