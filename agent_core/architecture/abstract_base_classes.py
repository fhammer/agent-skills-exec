"""
通用智能体框架核心接口定义

本文件包含架构设计文档中描述的核心抽象基类
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List, AsyncIterator, Callable
import time
import uuid


# =============================================================================
# 1. 核心状态枚举
# =============================================================================

class AgentState(Enum):
    """Agent 状态"""
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    SHUTTING_DOWN = "shutting_down"
    SHUTDOWN = "shutdown"


class SkillStatus(Enum):
    """Skill 状态"""
    INACTIVE = "inactive"
    READY = "ready"
    RUNNING = "running"
    ERROR = "error"
    DEPRECATED = "deprecated"


class ToolStatus(Enum):
    """Tool 状态"""
    INACTIVE = "inactive"
    READY = "ready"
    RUNNING = "running"
    ERROR = "error"
    DISABLED = "disabled"


class ConnectorStatus(Enum):
    """Connector 状态"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    ERROR = "error"
    RECONNECTING = "reconnecting"


class PluginState(Enum):
    """Plugin 状态"""
    DISABLED = "disabled"
    ENABLED = "enabled"
    LOADING = "loading"
    ACTIVE = "active"
    ERROR = "error"


class HookPriority(Enum):
    """Hook 优先级"""
    HIGHEST = 0
    HIGH = 100
    NORMAL = 500
    LOW = 900
    LOWEST = 1000


class EventPriority(Enum):
    """Event 优先级"""
    CRITICAL = 0
    HIGH = 100
    NORMAL = 500
    LOW = 900
    BACKGROUND = 1000


class CircuitBreakerState(Enum):
    """熔断器状态"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class DatabaseType(Enum):
    """数据库类型"""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    MONGODB = "mongodb"
    SQLITE = "sqlite"
    REDIS = "redis"


class HTTPMethod(Enum):
    """HTTP 方法"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class AuthType(Enum):
    """认证类型"""
    NONE = "none"
    API_KEY = "api_key"
    BEARER = "bearer"
    BASIC = "basic"
    DIGEST = "digest"
    OAUTH2 = "oauth2"


# =============================================================================
# 2. 核心数据类定义
# =============================================================================

@dataclass
class AgentConfig:
    """Agent 配置"""
    name: str = "default_agent"
    version: str = "1.0.0"
    description: str = "Default agent configuration"
    max_concurrent_tasks: int = 10
    timeout_seconds: int = 300
    enable_audit: bool = True
    enable_metrics: bool = True
    custom_settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentMetrics:
    """Agent 性能指标"""
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    total_execution_time_ms: float = 0.0
    avg_execution_time_ms: float = 0.0
    max_execution_time_ms: float = 0.0
    min_execution_time_ms: float = 0.0
    last_task_at: Optional[float] = None


@dataclass
class AgentResponse:
    """Agent 响应"""
    response_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    text: str = ""
    structured: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_trace: Optional[Dict[str, Any]] = None
    started_at: float = field(default_factory=time.time)
    completed_at: float = field(default_factory=time.time)
    execution_time_ms: float = 0.0


@dataclass
class SkillConfig:
    """Skill 配置"""
    name: str
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    tags: List[str] = field(default_factory=list)
    triggers: List[str] = field(default_factory=list)
    timeout_seconds: int = 60
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    requires_approval: bool = False
    compatible_scenes: List[str] = field(default_factory=list)
    custom_settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SkillExecutionContext:
    """Skill 执行上下文"""
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sub_task: str = ""
    user_input: str = ""
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    previous_results: Dict[str, Any] = field(default_factory=dict)
    environment: Dict[str, Any] = field(default_factory=dict)
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    scene_id: Optional[str] = None
    started_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "task_id": self.task_id,
            "sub_task": self.sub_task,
            "user_input": self.user_input,
            "conversation_history": self.conversation_history,
            "previous_results": self.previous_results,
            "environment": self.environment,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "scene_id": self.scene_id,
            "started_at": self.started_at,
            "metadata": self.metadata,
        }


@dataclass
class SkillExecutionResult:
    """Skill 执行结果"""
    success: bool = False
    skill_name: str = ""
    skill_version: str = ""
    sub_task: str = ""
    structured: Dict[str, Any] = field(default_factory=dict)
    text: str = ""
    error: Optional[str] = None
    error_code: Optional[str] = None
    execution_time_ms: float = 0.0
    started_at: float = field(default_factory=time.time)
    completed_at: float = field(default_factory=time.time)
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def success(
        cls,
        skill_name: str,
        skill_version: str = "1.0.0",
        sub_task: str = "",
        structured: Optional[Dict[str, Any]] = None,
        text: str = "",
        execution_time_ms: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "SkillExecutionResult":
        now = time.time()
        return cls(
            success=True,
            skill_name=skill_name,
            skill_version=skill_version,
            sub_task=sub_task,
            structured=structured or {},
            text=text,
            error=None,
            error_code=None,
            execution_time_ms=execution_time_ms,
            started_at=now - (execution_time_ms / 1000.0) if execution_time_ms > 0 else now,
            completed_at=now,
            metadata=metadata or {},
        )

    @classmethod
    def failure(
        cls,
        skill_name: str,
        skill_version: str = "1.0.0",
        sub_task: str = "",
        error: str = "",
        error_code: Optional[str] = None,
        execution_time_ms: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "SkillExecutionResult":
        now = time.time()
        return cls(
            success=False,
            skill_name=skill_name,
            skill_version=skill_version,
            sub_task=sub_task,
            structured={},
            text="",
            error=error,
            error_code=error_code,
            execution_time_ms=execution_time_ms,
            started_at=now - (execution_time_ms / 1000.0) if execution_time_ms > 0 else now,
            completed_at=now,
            metadata=metadata or {},
        )


@dataclass
class SkillStats:
    """Skill 统计信息"""
    execution_count: int = 0
    success_count: int = 0
    error_count: int = 0
    total_execution_time_ms: float = 0.0
    avg_execution_time_ms: float = 0.0
    max_execution_time_ms: float = 0.0
    min_execution_time_ms: float = 0.0
    last_executed_at: Optional[float] = None


@dataclass
class ToolConfig:
    """Tool 配置"""
    name: str
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    tags: List[str] = field(default_factory=list)
    requires_authentication: bool = False
    timeout_seconds: int = 30
    max_retries: int = 3
    retry_delay_seconds: float = 0.5
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000
    custom_settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolContext:
    """Tool 执行上下文"""
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

    def get_param(self, key: str, default: Any = None) -> Any:
        return self.parameters.get(key, default)

    def require_param(self, key: str) -> Any:
        if key not in self.parameters:
            raise ValueError(f"Required parameter '{key}' is missing")
        return self.parameters[key]


@dataclass
class ToolResult:
    """Tool 执行结果"""
    success: bool = False
    tool_name: str = ""
    tool_version: str = ""
    structured: Dict[str, Any] = field(default_factory=dict)
    text: str = ""
    error: Optional[str] = None
    error_code: Optional[str] = None
    execution_time_ms: float = 0.0
    started_at: float = field(default_factory=time.time)
    completed_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def success(
        cls,
        tool_name: str,
        tool_version: str = "1.0.0",
        structured: Optional[Dict[str, Any]] = None,
        text: str = "",
        execution_time_ms: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "ToolResult":
        now = time.time()
        return cls(
            success=True,
            tool_name=tool_name,
            tool_version=tool_version,
            structured=structured or {},
            text=text,
            error=None,
            error_code=None,
            execution_time_ms=execution_time_ms,
            started_at=now - (execution_time_ms / 1000.0) if execution_time_ms > 0 else now,
            completed_at=now,
            metadata=metadata or {},
        )

    @classmethod
    def failure(
        cls,
        tool_name: str,
        tool_version: str = "1.0.0",
        error: str = "",
        error_code: Optional[str] = None,
        execution_time_ms: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "ToolResult":
        now = time.time()
        return cls(
            success=False,
            tool_name=tool_name,
            tool_version=tool_version,
            structured={},
            text="",
            error=error,
            error_code=error_code,
            execution_time_ms=execution_time_ms,
            started_at=now - (execution_time_ms / 1000.0) if execution_time_ms > 0 else now,
            completed_at=now,
            metadata=metadata or {},
        )


@dataclass
class ToolStats:
    """Tool 统计信息"""
    execution_count: int = 0
    success_count: int = 0
    error_count: int = 0
    rate_limit_hits: int = 0
    total_execution_time_ms: float = 0.0
    avg_execution_time_ms: float = 0.0
    last_executed_at: Optional[float] = None


@dataclass
class ConnectorConfig:
    """Connector 配置"""
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
    pool_size: int = 10
    max_pool_size: int = 20
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
    connector_type: str = ""
    records: List[Dict[str, Any]] = field(default_factory=list)
    total_count: int = 0
    page: int = 1
    page_size: int = 100
    has_more: bool = False
    error: Optional[str] = None
    error_code: Optional[str] = None
    execution_time_ms: float = 0.0
    started_at: float = field(default_factory=time.time)
    completed_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def success(
        cls,
        connector_name: str,
        connector_type: str = "generic",
        records: Optional[List[Dict[str, Any]]] = None,
        total_count: Optional[int] = None,
        page: int = 1,
        page_size: int = 100,
        has_more: bool = False,
        execution_time_ms: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "QueryResult":
        now = time.time()
        record_list = records or []
        return cls(
            success=True,
            connector_name=connector_name,
            connector_type=connector_type,
            records=record_list,
            total_count=total_count if total_count is not None else len(record_list),
            page=page,
            page_size=page_size,
            has_more=has_more,
            error=None,
            error_code=None,
            execution_time_ms=execution_time_ms,
            started_at=now - (execution_time_ms / 1000.0) if execution_time_ms > 0 else now,
            completed_at=now,
            metadata=metadata or {},
        )

    @classmethod
    def failure(
        cls,
        connector_name: str,
        connector_type: str = "generic",
        error: str = "",
        error_code: Optional[str] = None,
        execution_time_ms: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "QueryResult":
        now = time.time()
        return cls(
            success=False,
            connector_name=connector_name,
            connector_type=connector_type,
            records=[],
            total_count=0,
            error=error,
            error_code=error_code,
            execution_time_ms=execution_time_ms,
            started_at=now - (execution_time_ms / 1000.0) if execution_time_ms > 0 else now,
            completed_at=now,
            metadata=metadata or {},
        )


@dataclass
class PluginConfig:
    """Plugin 配置"""
    name: str
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    priority: int = 100
    enabled: bool = True
    depends_on: List[str] = field(default_factory=list)
    custom_settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PluginMetadata:
    """Plugin 元数据"""
    name: str
    version: str
    description: str
    author: str
    state: "PluginState"
    priority: int
    loaded_at: float
    activated_at: Optional[float] = None
    last_error: Optional[str] = None


@dataclass
class HookContext:
    """Hook 执行上下文"""
    hook_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    hook_point: str = ""
    timestamp: float = field(default_factory=time.time)
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    stopped: bool = False

    def stop(self) -> None:
        self.stopped = True


@dataclass
class HookResult:
    """Hook 执行结果"""
    hook_id: str
    hook_name: str
    success: bool
    execution_time_ms: float
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class Event:
    """事件类"""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = ""
    source: str = ""
    timestamp: float = field(default_factory=time.time)
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    priority: EventPriority = EventPriority.NORMAL


@dataclass
class EventHandlerResult:
    """事件处理器结果"""
    handler_name: str
    success: bool
    execution_time_ms: float
    event_id: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class DatabaseConfig:
    """数据库配置"""
    name: str
    db_type: DatabaseType
    host: str = "localhost"
    port: int = 5432
    database: str = ""
    username: str = ""
    password: str = ""
    connection_string: Optional[str] = None
    pool_size: int = 10
    max_pool_size: int = 20
    max_idle_time_seconds: int = 300
    connection_timeout_seconds: int = 30
    command_timeout_seconds: int = 60
    enable_reconnect: bool = True
    max_reconnect_attempts: int = 3
    reconnect_delay_seconds: float = 1.0
    custom_settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RESTConfig:
    """REST 适配器配置"""
    name: str
    base_url: str
    timeout_seconds: int = 30
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    retry_on_statuses: List[int] = field(default_factory=lambda: [429, 500, 502, 503, 504])
    auth_type: AuthType = AuthType.NONE
    auth_config: Dict[str, str] = field(default_factory=dict)
    default_headers: Dict[str, str] = field(default_factory=dict)
    default_params: Dict[str, str] = field(default_factory=dict)
    verify_ssl: bool = True
    follow_redirects: bool = True
    max_redirects: int = 10
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout_seconds: int = 30


@dataclass
class RESTResponse:
    """REST 响应"""
    success: bool
    status_code: int
    url: str
    method: str
    headers: Dict[str, str]
    content: Optional[bytes] = None
    json_data: Optional[Dict[str, Any]] = None
    text: Optional[str] = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    started_at: float = field(default_factory=time.time)
    completed_at: float = field(default_factory=time.time)


# =============================================================================
# 3. 核心抽象基类
# =============================================================================

class Agent(ABC):
    """Agent 抽象基类"""

    def __init__(self, config: AgentConfig):
        self.config = config
        self._state = AgentState.INITIALIZING
        self._created_at = time.time()
        self._last_activity_at = time.time()
        self._metrics = AgentMetrics()
        self._audit_trail: List[Dict[str, Any]] = []

    @property
    def state(self) -> AgentState:
        return self._state

    @property
    def created_at(self) -> float:
        return self._created_at

    @property
    def last_activity_at(self) -> float:
        return self._last_activity_at

    @property
    def metrics(self) -> AgentMetrics:
        return self._metrics

    @abstractmethod
    async def initialize(self) -> bool:
        pass

    @abstractmethod
    async def process(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        pass

    @abstractmethod
    async def process_stream(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        pass

    @abstractmethod
    async def pause(self) -> bool:
        pass

    @abstractmethod
    async def resume(self) -> bool:
        pass

    @abstractmethod
    async def shutdown(self, force: bool = False) -> bool:
        pass

    @abstractmethod
    def get_audit_trail(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        pass

    def _record_audit(
        self,
        event_type: str,
        data: Dict[str, Any],
        source: str = "agent"
    ) -> None:
        if not self.config.enable_audit:
            return

        entry = {
            "audit_id": str(uuid.uuid4()),
            "timestamp": time.time(),
            "event_type": event_type,
            "source": source,
            "agent_name": self.config.name,
            "tenant_id": getattr(self.config, "tenant_id", None),
            "data": data,
        }
        self._audit_trail.append(entry)

        if len(self._audit_trail) > 10000:
            self._audit_trail = self._audit_trail[-10000:]

    def _update_metrics(
        self,
        task_success: bool,
        execution_time_ms: float
    ) -> None:
        if not self.config.enable_metrics:
            return

        self._metrics.total_tasks += 1
        self._metrics.last_task_at = time.time()

        if task_success:
            self._metrics.successful_tasks += 1
        else:
            self._metrics.failed_tasks += 1

        self._metrics.total_execution_time_ms += execution_time_ms
        self._metrics.avg_execution_time_ms = (
            self._metrics.total_execution_time_ms / self._metrics.total_tasks
        )

        if self._metrics.max_execution_time_ms < execution_time_ms:
            self._metrics.max_execution_time_ms = execution_time_ms

        if (self._metrics.min_execution_time_ms == 0 or
            self._metrics.min_execution_time_ms > execution_time_ms):
            self._metrics.min_execution_time_ms = execution_time_ms

    def __str__(self) -> str:
        return f"{self.config.name} (v{self.config.version}) - {self._state.value}"


class BaseSkill(ABC):
    """Skill 抽象基类"""

    def __init__(self, config: SkillConfig):
        self.config = config
        self._status = SkillStatus.INACTIVE
        self._created_at = time.time()
        self._stats = SkillStats()

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def version(self) -> str:
        return self.config.version

    @property
    def status(self) -> SkillStatus:
        return self._status

    @property
    def created_at(self) -> float:
        return self._created_at

    @property
    def stats(self) -> SkillStats:
        return self._stats

    async def initialize(self) -> bool:
        try:
            result = await self._on_initialize()
            if result:
                self._status = SkillStatus.READY
            return result
        except Exception as e:
            self._status = SkillStatus.ERROR
            await self._on_error(e)
            return False

    @abstractmethod
    async def _on_initialize(self) -> bool:
        return True

    async def execute(
        self,
        context: SkillExecutionContext
    ) -> SkillExecutionResult:
        start_time = time.time()
        self._status = SkillStatus.RUNNING
        self._stats.execution_count += 1

        retry_count = 0
        last_error = None
        max_retries = self.config.max_retries + 1

        for attempt in range(max_retries):
            retry_count = attempt
            try:
                await self._before_execute(context)
                result = await self._execute(context)
                await self._after_execute(context, result)

                if result.success:
                    self._stats.success_count += 1
                else:
                    self._stats.error_count += 1

                result.execution_time_ms = (time.time() - start_time) * 1000
                result.retry_count = retry_count
                result.skill_version = self.version

                self._update_execution_stats(result.execution_time_ms)
                self._status = SkillStatus.READY
                self._stats.last_executed_at = time.time()

                return result
            except Exception as e:
                last_error = e
                await self._on_error(e)

                if attempt < max_retries - 1:
                    await self._wait_retry(attempt)

        self._stats.error_count += 1
        self._status = SkillStatus.ERROR
        self._stats.last_executed_at = time.time()
        execution_time_ms = (time.time() - start_time) * 1000
        self._update_execution_stats(execution_time_ms)

        return SkillExecutionResult.failure(
            skill_name=self.name,
            skill_version=self.version,
            sub_task=context.sub_task,
            error=str(last_error) if last_error else "Unknown error",
            error_code="EXECUTION_FAILED",
            execution_time_ms=execution_time_ms,
            metadata={"retry_count": retry_count},
        )

    @abstractmethod
    async def _execute(self, context: SkillExecutionContext) -> SkillExecutionResult:
        pass

    async def _before_execute(self, context: SkillExecutionContext) -> None:
        pass

    async def _after_execute(self, context: SkillExecutionContext, result: SkillExecutionResult) -> None:
        pass

    async def _on_error(self, error: Exception) -> None:
        pass

    async def _wait_retry(self, attempt: int) -> None:
        await asyncio.sleep(self.config.retry_delay_seconds * (attempt + 1))

    async def shutdown(self) -> bool:
        try:
            result = await self._on_shutdown()
            self._status = SkillStatus.INACTIVE
            return result
        except Exception as e:
            await self._on_error(e)
            return False

    @abstractmethod
    async def _on_shutdown(self) -> bool:
        return True

    def can_handle(self, intent: str) -> bool:
        if not self.config.triggers:
            return False
        intent_lower = intent.lower()
        return any(trigger.lower() in intent_lower for trigger in self.config.triggers)

    def is_compatible_with_scene(self, scene_id: str) -> bool:
        if not self.config.compatible_scenes:
            return True
        return scene_id in self.config.compatible_scenes

    def _update_execution_stats(self, execution_time_ms: float) -> None:
        self._stats.total_execution_time_ms += execution_time_ms

        if self._stats.execution_count > 0:
            self._stats.avg_execution_time_ms = (
                self._stats.total_execution_time_ms / self._stats.execution_count
            )

        if self._stats.max_execution_time_ms < execution_time_ms:
            self._stats.max_execution_time_ms = execution_time_ms

        if (self._stats.min_execution_time_ms == 0 or
            self._stats.min_execution_time_ms > execution_time_ms):
            self._stats.min_execution_time_ms = execution_time_ms

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.config.description,
            "author": self.config.author,
            "tags": self.config.tags,
            "triggers": self.config.triggers,
            "status": self.status.value,
            "created_at": self.created_at,
            "stats": {
                "execution_count": self._stats.execution_count,
                "success_count": self._stats.success_count,
                "error_count": self._stats.error_count,
                "avg_execution_time_ms": self._stats.avg_execution_time_ms,
                "max_execution_time_ms": self._stats.max_execution_time_ms,
                "min_execution_time_ms": self._stats.min_execution_time_ms,
                "last_executed_at": self._stats.last_executed_at,
            },
        }

    def __str__(self) -> str:
        return f"{self.name} (v{self.version}) - {self._status.value}"


class BaseTool(ABC):
    """Tool 抽象基类"""

    def __init__(self, config: ToolConfig):
        self.config = config
        self._status = ToolStatus.INACTIVE
        self._created_at = time.time()
        self._stats = ToolStats()
        self._rate_limit_timestamps: List[float] = []

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def version(self) -> str:
        return self.config.version

    @property
    def status(self) -> ToolStatus:
        return self._status

    @property
    def created_at(self) -> float:
        return self._created_at

    @property
    def stats(self) -> ToolStats:
        return self._stats

    def _check_rate_limit(self) -> bool:
        now = time.time()
        one_minute_ago = now - 60

        self._rate_limit_timestamps = [
            ts for ts in self._rate_limit_timestamps if ts > one_minute_ago
        ]

        if len(self._rate_limit_timestamps) >= self.config.rate_limit_per_minute:
            self._stats.rate_limit_hits += 1
            return False

        self._rate_limit_timestamps.append(now)
        return True

    async def initialize(self) -> bool:
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
        return True

    async def execute(
        self,
        context: ToolContext
    ) -> ToolResult:
        start_time = time.time()
        self._stats.execution_count += 1

        if not self._check_rate_limit():
            return ToolResult.failure(
                tool_name=self.name,
                tool_version=self.version,
                error="Rate limit exceeded",
                error_code="RATE_LIMIT_EXCEEDED",
                execution_time_ms=(time.time() - start_time) * 1000,
            )

        self._status = ToolStatus.RUNNING

        try:
            validation_errors = await self.validate_parameters(context.parameters)
            if validation_errors:
                return ToolResult.failure(
                    tool_name=self.name,
                    tool_version=self.version,
                    error=f"Validation failed: {', '.join(validation_errors)}",
                    error_code="VALIDATION_ERROR",
                    execution_time_ms=(time.time() - start_time) * 1000,
                )

            await self._before_execute(context)
            result = await self._execute(context)
            await self._after_execute(context, result)

            if result.success:
                self._stats.success_count += 1
            else:
                self._stats.error_count += 1

            result.execution_time_ms = (time.time() - start_time) * 1000
            result.tool_version = self.version
            self._status = ToolStatus.READY
            self._stats.last_executed_at = time.time()

            return result
        except Exception as e:
            self._stats.error_count += 1
            await self._on_error(e)
            self._status = ToolStatus.ERROR
            self._stats.last_executed_at = time.time()

            return ToolResult.failure(
                tool_name=self.name,
                tool_version=self.version,
                error=str(e),
                error_code="EXECUTION_ERROR",
                execution_time_ms=(time.time() - start_time) * 1000,
            )

    @abstractmethod
    async def _execute(self, context: ToolContext) -> ToolResult:
        pass

    async def _before_execute(self, context: ToolContext) -> None:
        pass

    async def _after_execute(self, context: ToolContext, result: ToolResult) -> None:
        pass

    async def _on_error(self, error: Exception) -> None:
        pass

    async def shutdown(self) -> bool:
        try:
            result = await self._on_shutdown()
            self._status = ToolStatus.INACTIVE
            return result
        except Exception as e:
            await self._on_error(e)
            return False

    @abstractmethod
    async def _on_shutdown(self) -> bool:
        return True

    async def validate_parameters(self, parameters: Dict[str, Any]) -> List[str]:
        errors = []
        try:
            errors.extend(await self._validate_parameters(parameters))
        except Exception as e:
            errors.append(str(e))
        return errors

    async def _validate_parameters(self, parameters: Dict[str, Any]) -> List[str]:
        return []

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.config.description,
            "author": self.config.author,
            "tags": self.config.tags,
            "requires_authentication": self.config.requires_authentication,
            "status": self.status.value,
            "created_at": self.created_at,
            "stats": {
                "execution_count": self._stats.execution_count,
                "success_count": self._stats.success_count,
                "error_count": self._stats.error_count,
                "rate_limit_hits": self._stats.rate_limit_hits,
                "avg_execution_time_ms": self._stats.avg_execution_time_ms,
                "last_executed_at": self._stats.last_executed_at,
            },
        }

    def __str__(self) -> str:
        return f"{self.name} (v{self.version}) - {self._status.value}"


class BaseConnector(ABC):
    """Connector 抽象基类"""

    def __init__(self, config: ConnectorConfig):
        self.config = config
        self._status = ConnectorStatus.DISCONNECTED
        self._created_at = time.time()
        self._connected_since: Optional[float] = None
        self._stats = ConnectionStats()

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def type(self) -> str:
        return self.config.type

    @property
    def version(self) -> str:
        return self.config.version

    @property
    def status(self) -> ConnectorStatus:
        return self._status

    @property
    def created_at(self) -> float:
        return self._created_at

    @property
    def connected_since(self) -> Optional[float]:
        return self._connected_since

    @property
    def is_connected(self) -> bool:
        return self._status == ConnectorStatus.CONNECTED

    @property
    def stats(self) -> ConnectionStats:
        return self._stats

    async def connect(self) -> bool:
        start_time = time.time()
        self._status = ConnectorStatus.CONNECTING
        self._stats.connection_count += 1

        try:
            await self._before_connect()
            result = await self._connect()

            if result:
                self._status = ConnectorStatus.CONNECTED
                self._connected_since = time.time()
                self._stats.successful_connections += 1
                self._stats.last_connected_at = time.time()
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
        pass

    async def _before_connect(self) -> None:
        pass

    async def _after_connect(self) -> None:
        pass

    async def disconnect(self) -> bool:
        start_time = time.time()
        self._status = ConnectorStatus.DISCONNECTING

        try:
            await self._before_disconnect()
            result = await self._disconnect()

            if result:
                if self._connected_since:
                    connection_time_ms = (time.time() - self._connected_since) * 1000
                    self._stats.total_connection_time_ms += connection_time_ms

                self._status = ConnectorStatus.DISCONNECTED
                self._connected_since = None
                self._stats.last_disconnected_at = time.time()
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
        pass

    async def _before_disconnect(self) -> None:
        pass

    async def _after_disconnect(self) -> None:
        pass

    async def reconnect(self) -> bool:
        self._status = ConnectorStatus.RECONNECTING

        if self.is_connected:
            await self.disconnect()

        max_attempts = self.config.max_reconnect_attempts
        for attempt in range(1, max_attempts + 1):
            try:
                result = await self.connect()
                if result:
                    return True
            except Exception:
                pass

            if attempt < max_attempts:
                await asyncio.sleep(self.config.retry_delay_seconds * attempt)

        return False

    async def execute(
        self,
        operation: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> QueryResult:
        start_time = time.time()
        self._stats.total_requests += 1

        try:
            if not self.is_connected:
                if self.config.auto_reconnect:
                    await self.reconnect()
                if not self.is_connected:
                    return QueryResult.failure(
                        connector_name=self.name,
                        connector_type=self.type,
                        error="Not connected",
                        error_code="NOT_CONNECTED",
                        execution_time_ms=(time.time() - start_time) * 1000,
                    )

            await self._before_execute(operation, parameters or {})
            result = await self._execute(operation, parameters or {})
            await self._after_execute(operation, parameters or {}, result)

            if result.success:
                self._stats.successful_requests += 1
            else:
                self._stats.failed_requests += 1

            result.execution_time_ms = (time.time() - start_time) * 1000
            result.connector_type = self.type

            return result
        except Exception as e:
            self._stats.failed_requests += 1
            self._record_error("execute", str(e))
            await self._on_error(e)
            execution_time_ms = (time.time() - start_time) * 1000

            return QueryResult.failure(
                connector_name=self.name,
                connector_type=self.type,
                error=str(e),
                error_code="EXECUTION_ERROR",
                execution_time_ms=execution_time_ms,
            )

    @abstractmethod
    async def _execute(
        self,
        operation: str,
        parameters: Dict[str, Any]
    ) -> QueryResult:
        pass

    async def _before_execute(
        self,
        operation: str,
        parameters: Dict[str, Any]
    ) -> None:
        pass

    async def _after_execute(
        self,
        operation: str,
        parameters: Dict[str, Any],
        result: QueryResult
    ) -> None:
        pass

    async def query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> QueryResult:
        return await self.execute("query", {"query": query, **(parameters or {})})

    async def stream(
        self,
        operation: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[Dict[str, Any]]:
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
    ) -> AsyncIterator[Dict[str, Any]]:
        result = await self.execute(operation, parameters)
        for record in result.records:
            yield record

    async def check_connection(self) -> bool:
        try:
            return await self._check_connection()
        except Exception:
            return False

    async def _check_connection(self) -> bool:
        return self.is_connected

    async def heartbeat(self) -> bool:
        try:
            return await self._heartbeat()
        except Exception:
            return False

    async def _heartbeat(self) -> bool:
        return await self.check_connection()

    async def _on_error(self, error: Exception) -> None:
        pass

    def _record_error(self, operation: str, error: str) -> None:
        self._stats.errors.append({
            "operation": operation,
            "error": error,
            "timestamp": time.time(),
        })
        if len(self._stats.errors) > 100:
            self._stats.errors = self._stats.errors[-100:]

    def get_metadata(self) -> Dict[str, Any]:
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

    def __str__(self) -> str:
        return f"{self.name} ({self.type}) - {self._status.value}"


class Plugin(ABC):
    """插件抽象基类"""

    def __init__(self, config: PluginConfig):
        self.config = config
        self._state = PluginState.DISABLED
        self._loaded_at: Optional[float] = None
        self._activated_at: Optional[float] = None
        self._last_error: Optional[str] = None

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def version(self) -> str:
        return self.config.version

    @property
    def state(self) -> PluginState:
        return self._state

    @property
    def priority(self) -> int:
        return self.config.priority

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name=self.name,
            version=self.version,
            description=self.config.description,
            author=self.config.author,
            state=self._state,
            priority=self.priority,
            loaded_at=self._loaded_at or 0,
            activated_at=self._activated_at,
            last_error=self._last_error,
        )

    async def load(self) -> bool:
        if not self.config.enabled:
            self._state = PluginState.DISABLED
            return False

        self._state = PluginState.LOADING

        try:
            result = await self._on_load()
            if result:
                self._state = PluginState.ENABLED
                self._loaded_at = time.time()
            else:
                self._state = PluginState.ERROR
                self._last_error = "Load failed"
            return result
        except Exception as e:
            self._state = PluginState.ERROR
            self._last_error = str(e)
            return False

    @abstractmethod
    async def _on_load(self) -> bool:
        return True

    async def activate(self) -> bool:
        if self._state != PluginState.ENABLED:
            return False

        try:
            result = await self._on_activate()
            if result:
                self._state = PluginState.ACTIVE
                self._activated_at = time.time()
            return result
        except Exception as e:
            self._state = PluginState.ERROR
            self._last_error = str(e)
            return False

    @abstractmethod
    async def _on_activate(self) -> bool:
        return True

    async def deactivate(self) -> bool:
        if self._state != PluginState.ACTIVE:
            return True

        try:
            result = await self._on_deactivate()
            if result:
                self._state = PluginState.ENABLED
            return result
        except Exception as e:
            self._last_error = str(e)
            return False

    @abstractmethod
    async def _on_deactivate(self) -> bool:
        return True

    async def unload(self) -> bool:
        try:
            if self._state == PluginState.ACTIVE:
                await self.deactivate()

            result = await self._on_unload()
            self._state = PluginState.DISABLED
            return result
        except Exception as e:
            self._last_error = str(e)
            return False

    @abstractmethod
    async def _on_unload(self) -> bool:
        return True


class Hook:
    """钩子类"""

    def __init__(
        self,
        name: str,
        hook_point: str,
        handler: Callable,
        priority: HookPriority = HookPriority.NORMAL,
        enabled: bool = True,
        once: bool = False,
    ):
        self.name = name
        self.hook_point = hook_point
        self.handler = handler
        self.priority = priority
        self.enabled = enabled
        self.once = once
        self.executed_count = 0

    async def execute(self, context: HookContext) -> HookResult:
        start_time = time.time()

        try:
            if asyncio.iscoroutinefunction(self.handler):
                result_data = await self.handler(context)
            else:
                result_data = self.handler(context)

            self.executed_count += 1

            return HookResult(
                hook_id=context.hook_id,
                hook_name=self.name,
                success=True,
                execution_time_ms=(time.time() - start_time) * 1000,
                data=result_data if isinstance(result_data, dict) else None,
            )
        except Exception as e:
            return HookResult(
                hook_id=context.hook_id,
                hook_name=self.name,
                success=False,
                execution_time_ms=(time.time() - start_time) * 1000,
                error=str(e),
            )


class EventHandler:
    """事件处理器"""

    def __init__(
        self,
        name: str,
        event_types: List[str],
        handler: Callable,
        priority: EventPriority = EventPriority.NORMAL,
        enabled: bool = True,
    ):
        self.name = name
        self.event_types = event_types
        self.handler = handler
        self.priority = priority
        self.enabled = enabled
        self.executed_count = 0

    async def handle(self, event: Event) -> EventHandlerResult:
        start_time = time.time()

        try:
            if asyncio.iscoroutinefunction(self.handler):
                result_data = await self.handler(event)
            else:
                result_data = self.handler(event)

            self.executed_count += 1

            return EventHandlerResult(
                handler_name=self.name,
                success=True,
                execution_time_ms=(time.time() - start_time) * 1000,
                event_id=event.event_id,
                data=result_data if isinstance(result_data, dict) else None,
            )
        except Exception as e:
            return EventHandlerResult(
                handler_name=self.name,
                success=False,
                execution_time_ms=(time.time() - start_time) * 1000,
                event_id=event.event_id,
                error=str(e),
            )


class CircuitBreaker:
    """熔断器"""

    def __init__(self, threshold: int = 5, timeout_seconds: int = 30):
        self.threshold = threshold
        self.timeout_seconds = timeout_seconds
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None

    def record_success(self) -> None:
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED

    def record_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.threshold:
            self.state = CircuitBreakerState.OPEN

    def can_execute(self) -> bool:
        if self.state == CircuitBreakerState.CLOSED:
            return True

        if self.state == CircuitBreakerState.OPEN:
            if (self.last_failure_time and
                time.time() - self.last_failure_time > self.timeout_seconds):
                self.state = CircuitBreakerState.HALF_OPEN
                return True
            return False

        return True


# =============================================================================
# 4. 装饰器语法
# =============================================================================

def hook(
    hook_point: str,
    name: Optional[str] = None,
    priority: HookPriority = HookPriority.NORMAL,
    enabled: bool = True,
    once: bool = False,
):
    """钩子装饰器"""
    def decorator(func):
        func._hook_info = {
            "name": name or func.__name__,
            "hook_point": hook_point,
            "priority": priority,
            "enabled": enabled,
            "once": once,
        }
        return func
    return decorator


def event_listener(
    event_type: str,
    name: Optional[str] = None,
    priority: EventPriority = EventPriority.NORMAL,
):
    """事件监听器装饰器"""
    def decorator(func):
        func._event_listener_info = {
            "name": name or func.__name__,
            "event_type": event_type,
            "priority": priority,
        }
        return func
    return decorator


# =============================================================================
# 5. 工具函数
# =============================================================================

def create_database_adapter(config: DatabaseConfig) -> "DatabaseAdapter":
    """创建数据库适配器"""
    raise NotImplementedError("Database adapter creation not implemented")


def create_rest_adapter(config: RESTConfig) -> "RESTAdapter":
    """创建 REST 适配器"""
    raise NotImplementedError("REST adapter creation not implemented")


def create_file_adapter(config: Any) -> "FileAdapter":
    """创建文件适配器"""
    raise NotImplementedError("File adapter creation not implemented")


def create_message_queue_adapter(config: Any) -> "MessageQueueAdapter":
    """创建消息队列适配器"""
    raise NotImplementedError("Message queue adapter creation not implemented")
