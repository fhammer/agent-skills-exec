# Phase 4: 工业级架构设计

## 1. 架构愿景与目标

### 1.1 架构演进路线图

```
当前架构 (v1.0)                          目标架构 (v2.0)
┌─────────────────┐                    ┌─────────────────────────────────────┐
│   Monolithic    │   6个月演进        │      Microservices + DDD          │
│   Single Node    │   ──────────>      │   ┌─────────┐ ┌─────────┐ ┌─────┐ │
│                  │                    │   │  Agent  │ │ Tenant  │ │Skill│ │
│   ┌──────────┐  │                    │   │ Service │ │ Service │ │Svc  │ │
│   │Coordinator│ │                    │   └────┬────┘ └────┬────┘ └──┬──┘ │
│   └────┬─────┘  │                    │        │           │        │    │
│        │        │                    │   ┌────┴───────────┴────────┴──┐  │
│   ┌────▼─────┐  │                    │   │        API Gateway        │  │
│   │  Skills  │  │                    │   └───────────────────────────┘  │
│   └─────────┘  │                    └──────────────────────────────────┘
└─────────────────┘
```

### 1.2 架构设计目标

| 维度 | 当前状态 | 目标状态 | 关键指标 |
|-----|---------|---------|---------|
| **可用性** | 单机部署，无高可用 | 99.95%+ | 年停机 < 4.38小时 |
| **可扩展性** | 垂直扩展 | 水平扩展 | 支持100+实例 |
| **性能** | 单节点限制 | 分布式处理 | P99延迟 < 200ms |
| **可维护性** | 紧耦合 | 微服务+DDD | 模块独立部署 |
| **安全性** | 基础安全 | 企业级安全 | 通过等保三级 |

### 1.3 架构设计原则

```yaml
原则1: 领域驱动设计 (Domain-Driven Design)
  说明: 基于业务领域划分限界上下文
  实践:
    - Agent域: 对话管理、意图理解、上下文维护
    - Skill域: 技能发现、执行、编排
    - Tenant域: 多租户、配额、配置
    - Session域: 会话管理、状态持久化

原则2: 微服务架构 (Microservices)
  说明: 服务独立部署、独立扩展
  实践:
    - API Gateway: 统一入口、路由、认证
    - 核心服务: Agent Service、Tenant Service
    - 支撑服务: Skill Registry、Session Manager
    - 基础设施: Config Service、Metrics Service

原则3: 事件驱动架构 (Event-Driven)
  说明: 异步通信、松耦合、可扩展
  实践:
    - 领域事件: AgentCreated、SkillExecuted
    - 集成事件: TenantRegistered、SessionExpired
    - 事件总线: Kafka / Redis Streams

原则4: 数据持久化策略 (Polyglot Persistence)
  说明: 不同数据类型使用最适合的存储
  实践:
    - 关系数据: PostgreSQL（租户、配置）
    - 缓存数据: Redis（会话、热点数据）
    - 文档数据: MongoDB（对话历史）
    - 时序数据: InfluxDB（指标、日志）

原则5: 可观测性 (Observability)
  说明: 监控、日志、追踪三位一体
  实践:
    - 指标: Prometheus + Grafana
    - 日志: ELK Stack / Loki
    - 追踪: Jaeger + OpenTelemetry
    - 告警: Alertmanager + PagerDuty
```

## 2. 领域驱动设计 (DDD) 架构

### 2.1 领域划分

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Domain-Driven Architecture                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      Agent Domain                                │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │   │
│  │  │  Dialog     │  │  Intent     │  │  Context    │            │   │
│  │  │  Manager    │  │  Parser     │  │  Manager    │            │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘            │   │
│  │  职责: 对话管理、意图理解、上下文维护                           │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      Skill Domain                                │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │   │
│  │  │  Skill      │  │  Skill      │  │  Skill      │            │   │
│  │  │  Registry   │  │  Executor   │  │  Composer   │            │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘            │   │
│  │  职责: 技能发现、执行、编排                                     │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                     Tenant Domain                                │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │   │
│  │  │  Tenant     │  │  Quota      │  │  Config     │            │   │
│  │  │  Manager    │  │  Manager    │  │  Service    │            │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘            │   │
│  │  职责: 多租户管理、配额控制、配置管理                           │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Session Domain                                │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │   │
│  │  │  Session    │  │  State      │  │  History    │            │   │
│  │  │  Manager    │  │  Store      │  │  Recorder   │            │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘            │   │
│  │  职责: 会话管理、状态持久化、历史记录                           │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                  Shared Kernel (共享内核)                         │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │   │
│  │  │  Event      │  │  Common     │  │  Security   │            │   │
│  │  │  Bus        │  │  Utils      │  │  Base       │            │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘            │   │
│  │  职责: 事件总线、通用工具、安全基础                            │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 领域实体与值对象

```python
# agent/domain/entities/agent.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any
from enum import Enum
import uuid


class AgentStatus(Enum):
    IDLE = "idle"
    PROCESSING = "processing"
    ERROR = "error"
    MAINTENANCE = "maintenance"


@dataclass
class AgentConfig:
    """Agent配置值对象"""
    max_context_length: int = 4096
    temperature: float = 0.7
    top_p: float = 0.9
    max_retries: int = 3
    timeout_seconds: int = 30
    enable_streaming: bool = True
    custom_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentContext:
    """Agent上下文实体"""
    context_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    user_id: str = ""
    tenant_id: str = ""
    conversation_history: List[Dict] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def add_message(self, role: str, content: str, **kwargs):
        """添加消息到上下文"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
        self.conversation_history.append(message)
        self.updated_at = datetime.utcnow()

    def get_recent_messages(self, count: int = 10) -> List[Dict]:
        """获取最近的消息"""
        return self.conversation_history[-count:]

    def clear_history(self):
        """清除历史记录"""
        self.conversation_history.clear()
        self.updated_at = datetime.utcnow()


class Agent:
    """Agent聚合根实体"""

    def __init__(
        self,
        agent_id: str = None,
        name: str = "",
        description: str = "",
        config: AgentConfig = None,
        status: AgentStatus = AgentStatus.IDLE,
        tenant_id: str = "",
        created_by: str = ""
    ):
        self.agent_id = agent_id or str(uuid.uuid4())
        self.name = name
        self.description = description
        self.config = config or AgentConfig()
        self.status = status
        self.tenant_id = tenant_id
        self.created_by = created_by
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self._contexts: Dict[str, AgentContext] = {}
        self._event_handlers: List[callable] = []

    def create_context(
        self,
        session_id: str,
        user_id: str,
        metadata: Dict[str, Any] = None
    ) -> AgentContext:
        """创建新的上下文"""
        context = AgentContext(
            session_id=session_id,
            user_id=user_id,
            tenant_id=self.tenant_id,
            metadata=metadata or {}
        )
        self._contexts[context.context_id] = context
        self._emit_event("context_created", {"context_id": context.context_id})
        return context

    def get_context(self, context_id: str) -> Optional[AgentContext]:
        """获取上下文"""
        return self._contexts.get(context_id)

    def update_status(self, status: AgentStatus, reason: str = ""):
        """更新状态"""
        old_status = self.status
        self.status = status
        self.updated_at = datetime.utcnow()
        self._emit_event("status_changed", {
            "old_status": old_status.value,
            "new_status": status.value,
            "reason": reason
        })

    def on_event(self, handler: callable):
        """注册事件处理器"""
        self._event_handlers.append(handler)

    def _emit_event(self, event_type: str, data: Dict):
        """触发事件"""
        event = {
            "type": event_type,
            "agent_id": self.agent_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        for handler in self._event_handlers:
            try:
                handler(event)
            except Exception as e:
                print(f"Event handler error: {e}")

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "config": {
                "max_context_length": self.config.max_context_length,
                "temperature": self.config.temperature,
                "top_p": self.config.top_p,
                "max_retries": self.config.max_retries,
                "timeout_seconds": self.config.timeout_seconds,
                "enable_streaming": self.config.enable_streaming
            },
            "status": self.status.value,
            "tenant_id": self.tenant_id,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "context_count": len(self._contexts)
        }


# agent/domain/events/agent_events.py
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any


@dataclass
class AgentEvent:
    """基础Agent事件"""
    event_id: str
    event_type: str
    agent_id: str
    tenant_id: str
    timestamp: datetime
    payload: Dict[str, Any]


@dataclass
class AgentCreatedEvent(AgentEvent):
    """Agent创建事件"""
    name: str
    created_by: str
    config: Dict[str, Any]


@dataclass
class AgentStatusChangedEvent(AgentEvent):
    """Agent状态变更事件"""
    old_status: str
    new_status: str
    reason: str


@dataclass
class ContextCreatedEvent(AgentEvent):
    """上下文创建事件"""
    context_id: str
    session_id: str
    user_id: str


@dataclass
class MessageReceivedEvent(AgentEvent):
    """消息接收事件"""
    context_id: str
    message_id: str
    role: str
    content_preview: str


@dataclass
class SkillExecutedEvent(AgentEvent):
    """技能执行事件"""
    context_id: str
    skill_name: str
    execution_time_ms: int
    success: bool


@dataclass
class AgentErrorEvent(AgentEvent):
    """Agent错误事件"""
    error_type: str
    error_message: str
    stack_trace: str
    severity: str  # info, warning, error, critical


# 3. 微服务架构设计

## 3.1 服务划分

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Microservices Architecture                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      API Gateway Layer                           │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │   │
│  │  │    Kong     │  │  Rate Limit │  │    Auth     │              │   │
│  │  │  (Gateway)  │  │  (Plugin)   │  │  (Plugin)   │              │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘              │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                    │                                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      Service Mesh (Istio)                        │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │   │
│  │  │  Traffic    │  │   mTLS      │  │   Circuit   │              │   │
│  │  │  Management │  │  (Security) │  │   Breaker   │              │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘              │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                    │                                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                     Core Services (Business)                       │   │
│  │                                                                  │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │   │
│  │  │   Agent     │  │   Tenant    │  │   Session   │              │   │
│  │  │   Service   │  │   Service   │  │   Service   │              │   │
│  │  │   (Squad 1) │  │   (Squad 2) │  │   (Squad 3) │              │   │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │   │
│  │         │                │                │                     │   │
│  │  ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐              │   │
│  │  │    Skill    │  │    Audit    │  │   Metrics   │              │   │
│  │  │   Service   │  │   Service   │  │   Service   │              │   │
│  │  │  (Squad 4)  │  │  (Platform) │  │  (Platform) │              │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘              │   │
│  │                                                                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                    │                                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                   Infrastructure Services                        │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │   │
│  │  │   Config    │  │   Discovery │  │   Message   │              │   │
│  │  │   Service   │  │   Service   │  │   Queue     │              │   │
│  │  │  (Consul)   │  │  (Consul)   │  │  (Kafka)    │              │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘              │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                    │                                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      Data Layer                                    │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │   │
│  │  │ PostgreSQL  │  │    Redis    │  │ Elasticsearch│              │   │
│  │  │  (Primary)  │  │  (Cluster)  │  │  (Cluster)  │              │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘              │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## 3.2 服务接口定义

```python
# services/agent_service/interfaces.py
from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ChatRequest:
    """聊天请求"""
    message: str
    session_id: str
    user_id: str
    tenant_id: str
    context: Optional[Dict[str, Any]] = None
    stream: bool = False


@dataclass
class ChatResponse:
    """聊天响应"""
    message_id: str
    session_id: str
    content: str
    role: str = "assistant"
    tokens_used: int = 0
    latency_ms: int = 0
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ContextInfo:
    """上下文信息"""
    context_id: str
    session_id: str
    user_id: str
    tenant_id: str
    message_count: int
    created_at: datetime
    updated_at: datetime


class IAgentService(ABC):
    """Agent服务接口"""

    @abstractmethod
    async def chat(self, request: ChatRequest) -> ChatResponse:
        """
        处理聊天请求

        Args:
            request: 聊天请求

        Returns:
            聊天响应
        """
        pass

    @abstractmethod
    async def chat_stream(
        self,
        request: ChatRequest
    ) -> AsyncIterator[ChatResponse]:
        """
        流式聊天处理

        Args:
            request: 聊天请求

        Yields:
            流式聊天响应片段
        """
        pass

    @abstractmethod
    async def create_context(
        self,
        session_id: str,
        user_id: str,
        tenant_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ContextInfo:
        """
        创建对话上下文

        Args:
            session_id: 会话ID
            user_id: 用户ID
            tenant_id: 租户ID
            metadata: 元数据

        Returns:
            上下文信息
        """
        pass

    @abstractmethod
    async def get_context(self, context_id: str) -> Optional[ContextInfo]:
        """
        获取上下文信息

        Args:
            context_id: 上下文ID

        Returns:
            上下文信息，如果不存在则返回None
        """
        pass

    @abstractmethod
    async def clear_context(self, context_id: str) -> bool:
        """
        清除上下文

        Args:
            context_id: 上下文ID

        Returns:
            是否成功清除
        """
        pass

    @abstractmethod
    async def get_agent_info(self) -> Dict[str, Any]:
        """
        获取Agent信息

        Returns:
            Agent信息字典
        """
        pass


class IAgentEventHandler(ABC):
    """Agent事件处理器接口"""

    @abstractmethod
    async def on_event(self, event: Dict[str, Any]):
        """
        处理Agent事件

        Args:
            event: 事件数据
        """
        pass
