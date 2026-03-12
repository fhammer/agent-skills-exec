# Agent Skills Framework - 完整架构设计文档

**版本**: 2.0.0
**日期**: 2026-03-09
**状态**: 正式版
**作者**: AI 架构师团队

---

## 目录

1. [架构概览](#1-架构概览)
2. [核心抽象层设计](#2-核心抽象层设计)
3. [扩展机制设计](#3-扩展机制设计)
4. [业务系统集成层](#4-业务系统集成层)
5. [多租户与多场景支持](#5-多租户与多场景支持)
6. [数据流与执行模型](#6-数据流与执行模型)
7. [接口规范](#7-接口规范)
8. [部署架构](#8-部署架构)
9. [安全性设计](#9-安全性设计)
10. [性能设计](#10-性能设计)
11. [可观测性设计](#11-可观测性设计)
12. [技术选型说明](#12-技术选型说明)
13. [附录](#13-附录)

---

## 1. 架构概览

### 1.1 设计原则

| 原则 | 说明 | 实现方式 |
|------|------|----------|
| **单一职责** | 每个组件职责明确，Coordinator 只负责编排 | 核心组件各司其职，通过接口协作 |
| **开闭原则** | 对扩展开放，对修改封闭 | 通过 Plugin、Hook、Event 机制扩展功能 |
| **依赖倒置** | 高层模块不依赖低层模块，都依赖抽象 | 通过抽象接口（Agent、Skill、Tool）进行依赖 |
| **渐进复杂** | 从简单场景开始，按需引入分布式能力 | 支持单机到分布式渐进部署 |
| **可观测性** | 全链路审计，支持追溯和调试 | 三层上下文审计日志、Metrics监控、分布式追踪 |
| **异步优先** | 所有IO操作采用异步设计 | 使用 asyncio 实现高性能并发 |
| **容错设计** | 自动重试、熔断、降级 | 内置 Circuit Breaker、Retry 机制 |

### 1.2 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              业务系统接入层                                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │    Web App   │  │   移动端      │  │   小程序      │  │   企业系统    │   │
│  │  (React/Vue) │  │ (iOS/Android)│  │  (WeChat)    │  │  (ERP/CRM)   │   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │
└─────────┼───────────────────┼───────────────────┼───────────────────┼───────────┘
          │                   │                   │                   │
          └───────────────────┴───────────────────┴───────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                API 网关层                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   认证鉴权    │  │   限流熔断    │  │   路由分发    │  │   协议转换    │   │
│  │  JWT/API Key │  │  Token Bucket│  │  负载均衡    │  │  REST/SSE   │   │
│  │  OAuth 2.0   │  │  Circuit Breaker │  │  灰度发布    │  │  WebSocket  │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────┬───────────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          智能体框架核心层 (Agent Framework Core)                  │
│                                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                        Agent Runtime 运行时                               │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │    │
│  │  │ Coordinator │─▶│   Planner   │─▶│  Executor   │─▶│ Synthesizer │ │    │
│  │  │  (调度中心)  │  │  (任务规划)  │  │  (技能执行)  │  │  (结果综合)  │ │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │    │
│  │         │                                               │              │    │
│  │         ▼                                               ▼              │    │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │    │
│  │  │                 三层上下文系统 (AgentContext)                      │   │    │
│  │  │  Layer 1: User Input   │  用户输入、意图、计划、对话历史          │   │    │
│  │  │  Layer 2: Working Mem  │  工作内存、Skill执行结果、中间状态      │   │    │
│  │  │  Layer 3: Environment  │  可用Skills、Token预算、工具注册表       │   │    │
│  │  └─────────────────────────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                       Skill Engine 技能引擎                               │    │
│  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────────────────┐  │    │
│  │  │  Skill Loader │  │ Skill Executor│  │     Skill Registry        │  │    │
│  │  │  (自动发现)    │  │  (三模式执行)  │  │    (注册/发现/管理)       │  │    │
│  │  │               │  │ - Python Code │  │                           │  │    │
│  │  │               │  │ - Prompt Tpl  │  │                           │  │    │
│  │  │               │  │ - LLM Doc     │  │                           │  │    │
│  │  └───────────────┘  └───────────────┘  └───────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                      Tool System 工具系统                                 │    │
│  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────────────────┐  │    │
│  │  │  Tool Loader  │  │  Tool Runner  │  │     Tool Registry         │  │    │
│  │  └───────────────┘  └───────────────┘  └───────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                      Extension Layer 扩展层                               │    │
│  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────────────────┐  │    │
│  │  │ Plugin System │  │  Hook System  │  │      Event System         │  │    │
│  │  │  (插件机制)    │  │  (钩子机制)   │  │      (事件机制)           │  │    │
│  │  └───────────────┘  └───────────────┘  └───────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            基础设施层 (Infrastructure)                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   多租户管理  │  │   会话管理    │  │   审计日志    │  │  Token管理   │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   配置管理    │  │   健康检查    │  │   限流熔断    │  │  缓存管理     │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   Metrics    │  │   Tracing    │  │   Logging    │  │  Alerting    │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       Connector Layer 连接器层                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │  REST Adapter│  │  DB Adapter  │  │  MQ Adapter  │  │ File Adapter │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            外部服务层 (External Services)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   LLM服务     │  │   业务API     │  │    数据库     │  │   消息队列    │   │
│  │ OpenAI/Anth  │  │  REST/gRPC   │  │  PG/MySQL/Mongo│  │ Kafka/Rabbit│   │
│  │  Zhipu/Ollama│  │              │  │              │  │  Redis Queue │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │  文件存储     │  │   缓存服务    │  │  搜索引擎     │  │  监控系统    │   │
│  │  S3/MinIO    │  │  Redis/Memcached │  Elasticsearch│  │ Prometheus  │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 架构分层详解

#### 1.3.1 应用接入层
- **职责**：提供多端接入能力
- **组件**：Web应用、移动应用、小程序、企业系统
- **技术**：React/Vue、iOS/Android、微信小程序

#### 1.3.2 API网关层
- **职责**：统一入口、认证鉴权、限流熔断、路由分发
- **组件**：认证鉴权、限流熔断、路由分发、协议转换
- **技术**：Nginx、Kong、APISIX、自研网关

#### 1.3.3 智能体框架核心层
- **职责**：智能体运行时、技能引擎、工具系统、扩展机制
- **组件**：Agent Runtime、Skill Engine、Tool System、Extension Layer
- **技术**：Python asyncio、结构化并发

#### 1.3.4 基础设施层
- **职责**：多租户管理、会话管理、审计日志、可观测性
- **组件**：多租户、会话、审计、配置、健康检查、Metrics、Tracing、Logging
- **技术**：Redis、PostgreSQL、OpenTelemetry

#### 1.3.5 连接器层
- **职责**：统一的外部系统接入抽象
- **组件**：REST Adapter、DB Adapter、MQ Adapter、File Adapter
- **技术**：aiohttp、asyncpg、aiomysql、aiokafka

#### 1.3.6 外部服务层
- **职责**：外部依赖服务
- **组件**：LLM服务、业务API、数据库、消息队列、文件存储等

---

## 2. 核心抽象层设计

### 2.1 Agent 抽象

#### 2.1.1 Agent 状态机

```
                ┌─────────────┐
                │ INITIALIZING│
                └──────┬──────┘
                       │ initialize()
                       ▼
┌─────────┐   ┌─────────────┐   ┌─────────┐
│ PAUSED  │◀──│    READY    │──▶│ RUNNING │
└────┬────┘   └──────┬──────┘   └────┬────┘
     │     resume()   │                 │
     └────────────────┘                 │
                       │ process()       │
                       ▼                 │
                ┌─────────────┐         │
                │    ERROR    │◀────────┘
                └──────┬──────┘
                       │
                       ▼
                ┌─────────────┐
                │SHUTTING_DOWN│
                └──────┬──────┘
                       │
                       ▼
                ┌─────────────┐
                │  SHUTDOWN   │
                └─────────────┘
```

#### 2.1.2 Agent 接口定义

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List, AsyncIterator
from datetime import datetime
import time
import uuid


class AgentState(Enum):
    """Agent 状态枚举"""
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    SHUTTING_DOWN = "shutting_down"
    SHUTDOWN = "shutdown"


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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "response_id": self.response_id,
            "text": self.text,
            "structured": self.structured,
            "metadata": self.metadata,
            "execution_trace": self.execution_trace,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "execution_time_ms": self.execution_time_ms,
        }


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
    enable_streaming: bool = True
    tenant_id: Optional[str] = None
    scene_id: Optional[str] = None
    custom_settings: Dict[str, Any] = field(default_factory=dict)


class Agent(ABC):
    """
    Agent 抽象基类

    定义 Agent 的核心能力：
    - 生命周期管理（初始化、启动、暂停、恢复、关闭）
    - 请求处理（同步、流式）
    - 状态管理
    - 审计追踪
    - 指标收集
    """

    def __init__(self, config: AgentConfig):
        self.config = config
        self._state = AgentState.INITIALIZING
        self._created_at = time.time()
        self._last_activity_at = time.time()
        self._metrics = AgentMetrics()
        self._audit_trail: List[Dict[str, Any]] = []

    @property
    def state(self) -> AgentState:
        """获取当前状态"""
        return self._state

    @property
    def created_at(self) -> float:
        """创建时间戳"""
        return self._created_at

    @property
    def last_activity_at(self) -> float:
        """最后活动时间戳"""
        return self._last_activity_at

    @property
    def metrics(self) -> AgentMetrics:
        """获取性能指标"""
        return self._metrics

    @abstractmethod
    async def initialize(self) -> bool:
        """
        初始化 Agent

        Returns:
            bool: 初始化是否成功
        """
        pass

    @abstractmethod
    async def process(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        同步处理用户请求

        Args:
            user_input: 用户输入
            context: 上下文信息

        Returns:
            AgentResponse: 处理结果
        """
        pass

    @abstractmethod
    async def process_stream(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        流式处理用户请求

        Args:
            user_input: 用户输入
            context: 上下文信息

        Yields:
            响应片段字典，包含：
            - type: 消息类型 ("chunk", "metadata", "error", "done")
            - content: 内容
            - ... 其他字段
        """
        pass

    @abstractmethod
    async def pause(self) -> bool:
        """
        暂停 Agent

        Returns:
            bool: 暂停是否成功
        """
        pass

    @abstractmethod
    async def resume(self) -> bool:
        """
        恢复 Agent

        Returns:
            bool: 恢复是否成功
        """
        pass

    @abstractmethod
    async def shutdown(self, force: bool = False) -> bool:
        """
        关闭 Agent

        Args:
            force: 是否强制关闭

        Returns:
            bool: 关闭是否成功
        """
        pass

    @abstractmethod
    def get_audit_trail(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        获取审计轨迹

        Args:
            limit: 返回条数限制
            offset: 偏移量

        Returns:
            审计日志条目列表
        """
        pass

    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        """
        获取配置信息

        Returns:
            配置字典
        """
        pass

    def _record_audit(
        self,
        event_type: str,
        data: Dict[str, Any],
        source: str = "agent"
    ) -> None:
        """
        记录审计事件

        Args:
            event_type: 事件类型
            data: 事件数据
            source: 事件来源
        """
        if not self.config.enable_audit:
            return

        entry = {
            "audit_id": str(uuid.uuid4()),
            "timestamp": time.time(),
            "event_type": event_type,
            "source": source,
            "agent_name": self.config.name,
            "tenant_id": self.config.tenant_id,
            "data": data,
        }
        self._audit_trail.append(entry)

        # 只保留最近 10000 条
        if len(self._audit_trail) > 10000:
            self._audit_trail = self._audit_trail[-10000:]

    def _update_metrics(
        self,
        task_success: bool,
        execution_time_ms: float
    ) -> None:
        """
        更新性能指标

        Args:
            task_success: 任务是否成功
            execution_time_ms: 执行时间（毫秒）
        """
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

    def __repr__(self) -> str:
        return (f"{self.__class__.__name__}(name={self.config.name}, "
                f"version={self.config.version}, state={self._state.value})")
```

### 2.2 Skill 抽象

#### 2.2.1 Skill 执行模式

Skill 支持三种执行模式，优先级从高到低：

| 模式 | 说明 | 使用场景 |
|------|------|----------|
| **Python Code** | executor.py 中的自定义代码 | 需要精确控制、复杂逻辑、高性能 |
| **Prompt Template** | prompt.template 提示词模板 | 中等复杂度、自然语言处理 |
| **SKILL.md** | 文档作为技能描述 | 简单任务、快速原型 |

#### 2.2.2 Skill 接口定义

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List
import time
import uuid


class SkillStatus(Enum):
    """Skill 状态"""
    INACTIVE = "inactive"
    READY = "ready"
    RUNNING = "running"
    ERROR = "error"
    DEPRECATED = "deprecated"


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

    def get(self, key: str, default: Any = None) -> Any:
        """获取上下文值"""
        return self.metadata.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """设置上下文值"""
        self.metadata[key] = value


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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "skill_name": self.skill_name,
            "skill_version": self.skill_version,
            "sub_task": self.sub_task,
            "structured": self.structured,
            "text": self.text,
            "error": self.error,
            "error_code": self.error_code,
            "execution_time_ms": self.execution_time_ms,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "retry_count": self.retry_count,
            "metadata": self.metadata,
        }

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
        """创建成功结果"""
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
        """创建失败结果"""
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


class BaseSkill(ABC):
    """
    Skill 抽象基类

    所有自定义技能都应该继承此类
    """

    def __init__(self, config: SkillConfig):
        self.config = config
        self._status = SkillStatus.INACTIVE
        self._created_at = time.time()
        self._stats = SkillStats()

    @property
    def name(self) -> str:
        """获取技能名称"""
        return self.config.name

    @property
    def version(self) -> str:
        """获取技能版本"""
        return self.config.version

    @property
    def status(self) -> SkillStatus:
        """获取技能状态"""
        return self._status

    @property
    def created_at(self) -> float:
        """创建时间戳"""
        return self._created_at

    @property
    def stats(self) -> SkillStats:
        """获取统计信息"""
        return self._stats

    async def initialize(self) -> bool:
        """
        初始化技能

        Returns:
            bool: 初始化是否成功
        """
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
        """
        初始化钩子 - 子类实现

        Returns:
            bool: 初始化是否成功
        """
        return True

    async def execute(
        self,
        context: SkillExecutionContext
    ) -> SkillExecutionResult:
        """
        执行技能（带重试机制）

        Args:
            context: 执行上下文

        Returns:
            SkillExecutionResult: 执行结果
        """
        start_time = time.time()
        self._status = SkillStatus.RUNNING
        self._stats.execution_count += 1

        retry_count = 0
        last_error = None

        max_retries = self.config.max_retries + 1  # 第一次执行不算重试

        for attempt in range(max_retries):
            retry_count = attempt
            try:
                # 执行前钩子
                await self._before_execute(context)

                # 执行核心逻辑
                result = await self._execute(context)

                # 执行后钩子
                await self._after_execute(context, result)

                # 更新统计
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

                # 如果是最后一次尝试，不再重试
                if attempt >= max_retries - 1:
                    break

                # 等待重试延迟
                if self.config.retry_delay_seconds > 0:
                    import asyncio
                    await asyncio.sleep(self.config.retry_delay_seconds * (attempt + 1))

        # 所有重试都失败
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
    async def _execute(
        self,
        context: SkillExecutionContext
    ) -> SkillExecutionResult:
        """
        执行核心逻辑 - 子类必须实现

        Args:
            context: 执行上下文

        Returns:
            SkillExecutionResult: 执行结果
        """
        pass

    async def _before_execute(
        self,
        context: SkillExecutionContext
    ) -> None:
        """
        执行前钩子 - 子类可重写

        Args:
            context: 执行上下文
        """
        pass

    async def _after_execute(
        self,
        context: SkillExecutionContext,
        result: SkillExecutionResult
    ) -> None:
        """
        执行后钩子 - 子类可重写

        Args:
            context: 执行上下文
            result: 执行结果
        """
        pass

    async def _on_error(self, error: Exception) -> None:
        """
        错误处理钩子 - 子类可重写

        Args:
            error: 异常对象
        """
        pass

    async def shutdown(self) -> bool:
        """
        关闭技能

        Returns:
            bool: 关闭是否成功
        """
        try:
            result = await self._on_shutdown()
            self._status = SkillStatus.INACTIVE
            return result
        except Exception as e:
            await self._on_error(e)
            return False

    @abstractmethod
    async def _on_shutdown(self) -> bool:
        """
        关闭钩子 - 子类实现

        Returns:
            bool: 关闭是否成功
        """
        return True

    def can_handle(self, intent: str) -> bool:
        """
        检查技能是否能处理某个意图

        Args:
            intent: 意图字符串

        Returns:
            bool: 是否能处理
        """
        if not self.config.triggers:
            return False
        intent_lower = intent.lower()
        return any(trigger.lower() in intent_lower for trigger in self.config.triggers)

    def is_compatible_with_scene(self, scene_id: str) -> bool:
        """
        检查技能是否与场景兼容

        Args:
            scene_id: 场景ID

        Returns:
            bool: 是否兼容
        """
        if not self.config.compatible_scenes:
            return True  # 默认兼容所有场景
        return scene_id in self.config.compatible_scenes

    def _update_execution_stats(self, execution_time_ms: float) -> None:
        """更新执行统计"""
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
        """
        获取技能元数据

        Returns:
            元数据字典
        """
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

    def __repr__(self) -> str:
        return (f"{self.__class__.__name__}(name={self.name}, "
                f"version={self.version}, status={self._status.value})")
```

### 2.3 Tool 抽象

#### 2.3.1 Tool 与 Skill 的区别

| 特性 | Skill | Tool |
|------|-------|------|
| **职责** | 完成业务任务 | 执行具体操作 |
| **粒度** | 粗粒度（业务级） | 细粒度（操作级） |
| **复杂度** | 可能包含多个步骤 | 单一操作 |
| **LLM 依赖** | 可选 | 通常不依赖 |
| **示例** | "处理退款申请" | "查询订单"、"发送邮件" |

#### 2.3.2 Tool 接口定义

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List
import time
import uuid


class ToolStatus(Enum):
    """Tool 状态"""
    INACTIVE = "inactive"
    READY = "ready"
    RUNNING = "running"
    ERROR = "error"
    DISABLED = "disabled"


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

    def to_dict(self) -> Dict[str, Any]:
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

    def get_param(self, key: str, default: Any = None) -> Any:
        """获取参数"""
        return self.parameters.get(key, default)

    def require_param(self, key: str) -> Any:
        """获取必需参数，如果不存在则抛出异常"""
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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "tool_name": self.tool_name,
            "tool_version": self.tool_version,
            "structured": self.structured,
            "text": self.text,
            "error": self.error,
            "error_code": self.error_code,
            "execution_time_ms": self.execution_time_ms,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "metadata": self.metadata,
        }

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
        """创建成功结果"""
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
        """创建失败结果"""
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


class BaseTool(ABC):
    """
    Tool 抽象基类

    所有自定义工具都应该继承此类
    """

    def __init__(self, config: ToolConfig):
        self.config = config
        self._status = ToolStatus.INACTIVE
        self._created_at = time.time()
        self._stats = ToolStats()
        self._rate_limit_timestamps: List[float] = []

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
    def stats(self) -> ToolStats:
        """获取统计信息"""
        return self._stats

    def _check_rate_limit(self) -> bool:
        """
        检查速率限制

        Returns:
            bool: 是否允许执行
        """
        now = time.time()
        one_minute_ago = now - 60

        # 清理过期的时间戳
        self._rate_limit_timestamps = [
            ts for ts in self._rate_limit_timestamps if ts > one_minute_ago
        ]

        # 检查是否超过限制
        if len(self._rate_limit_timestamps) >= self.config.rate_limit_per_minute:
            self._stats.rate_limit_hits += 1
            return False

        # 记录本次调用
        self._rate_limit_timestamps.append(now)
        return True

    async def initialize(self) -> bool:
        """
        初始化工具

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
        """
        初始化钩子 - 子类实现

        Returns:
            bool: 初始化是否成功
        """
        return True

    async def execute(
        self,
        context: ToolContext
    ) -> ToolResult:
        """
        执行工具

        Args:
            context: 执行上下文

        Returns:
            ToolResult: 执行结果
        """
        start_time = time.time()
        self._stats.execution_count += 1

        # 检查速率限制
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
            # 验证参数
            validation_errors = await self.validate_parameters(context.parameters)
            if validation_errors:
                return ToolResult.failure(
                    tool_name=self.name,
                    tool_version=self.version,
                    error=f"Parameter validation failed: {', '.join(validation_errors)}",
                    error_code="VALIDATION_ERROR",
                    execution_time_ms=(time.time() - start_time) * 1000,
                )

            # 执行前钩子
            await self._before_execute(context)

            # 执行核心逻辑
            result = await self._execute(context)

            # 执行后钩子
            await self._after_execute(context, result)

            # 更新统计
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
            execution_time_ms = (time.time() - start_time) * 1000

            return ToolResult.failure(
                tool_name=self.name,
                tool_version=self.version,
                error=str(e),
                error_code="EXECUTION_ERROR",
                execution_time_ms=execution_time_ms,
            )

    @abstractmethod
    async def _execute(self, context: ToolContext) -> ToolResult:
        """
        执行核心逻辑 - 子类必须实现

        Args:
            context: 执行上下文

        Returns:
            ToolResult: 执行结果
        """
        pass

    async def _before_execute(self, context: ToolContext) -> None:
        """
        执行前钩子 - 子类可重写

        Args:
            context: 执行上下文
        """
        pass

    async def _after_execute(
        self,
        context: ToolContext,
        result: ToolResult
    ) -> None:
        """
        执行后钩子 - 子类可重写

        Args:
            context: 执行上下文
            result: 执行结果
        """
        pass

    async def _on_error(self, error: Exception) -> None:
        """
        错误处理钩子 - 子类可重写

        Args:
            error: 异常对象
        """
        pass

    async def shutdown(self) -> bool:
        """
        关闭工具

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
        """
        关闭钩子 - 子类实现

        Returns:
            bool: 关闭是否成功
        """
        return True

    async def validate_parameters(self, parameters: Dict[str, Any]) -> List[str]:
        """
        验证输入参数

        Args:
            parameters: 参数字典

        Returns:
            错误列表，空列表表示验证通过
        """
        errors = []
        try:
            errors.extend(await self._validate_parameters(parameters))
        except Exception as e:
            errors.append(str(e))
        return errors

    async def _validate_parameters(self, parameters: Dict[str, Any]) -> List[str]:
        """
        验证输入参数 - 子类可重写

        Args:
            parameters: 参数字典

        Returns:
            错误列表
        """
        return []

    def get_metadata(self) -> Dict[str, Any]:
        """
        获取工具元数据

        Returns:
            元数据字典
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

    def __repr__(self) -> str:
        return (f"{self.__class__.__name__}(name={self.name}, "
                f"version={self.version}, status={self._status.value})")
```

### 2.4 Connector 抽象

#### 2.4.1 Connector 状态机

```
                ┌──────────────┐
                │ DISCONNECTED │◀──────────┐
                └──────┬───────┘           │
                       │ connect()           │
                       ▼                     │
                ┌──────────────┐            │
                │  CONNECTING  │            │
                └──────┬───────┘            │
           ┌───────────┴───────────┐        │
           │                       │        │
           ▼                       ▼        │
    ┌──────────────┐        ┌──────────┐   │
    │  CONNECTED   │        │  ERROR   │   │
    └──────┬───────┘        └────┬─────┘   │
           │                       │         │
           │ disconnect()          │         │
           ▼                       ▼         │
    ┌──────────────┐        ┌──────────────┐ │
    │DISCONNECTING │        │ RECONNECTING │─┘
    └──────┬───────┘        └──────────────┘
           │
           ▼
    ┌──────────────┐
    │ DISCONNECTED │
    └──────────────┘
```

#### 2.4.2 Connector 接口定义

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List, AsyncGenerator
import time
import uuid


class ConnectorStatus(Enum):
    """Connector 状态"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    ERROR = "error"
    RECONNECTING = "reconnecting"


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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "connector_name": self.connector_name,
            "connector_type": self.connector_type,
            "records": self.records,
            "total_count": self.total_count,
            "page": self.page,
            "page_size": self.page_size,
            "has_more": self.has_more,
            "error": self.error,
            "error_code": self.error_code,
            "execution_time_ms": self.execution_time_ms,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "metadata": self.metadata,
        }

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
        """创建成功结果"""
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
        """创建失败结果"""
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


class BaseConnector(ABC):
    """
    Connector 抽象基类

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
        """
        连接

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
        """
        执行连接 - 子类必须实现

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
        """
        断开连接

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
        """
        执行断开 - 子类必须实现

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
        """
        重新连接

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
        """
        执行操作

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
                        connector_type=self.type,
                        error="Not connected",
                        error_code="NOT_CONNECTED",
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
        """
        执行核心逻辑 - 子类必须实现

        Args:
            operation: 操作名称
            parameters: 操作参数

        Returns:
            QueryResult: 查询结果
        """
        pass

    async def _before_execute(
        self,
        operation: str,
        parameters: Dict[str, Any]
    ) -> None:
        """
        执行前钩子 - 子类可重写

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
        """
        执行后钩子 - 子类可重写

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
        """
        执行查询（快捷方法）

        Args:
            query: 查询语句
            parameters: 查询参数

        Returns:
            QueryResult: 查询结果
        """
        return await self.execute(
            "query",
            {"query": query, **(parameters or {})}
        )

    async def stream(
        self,
        operation: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式执行

        Args:
            operation: 操作名称
            parameters: 操作参数

        Yields:
            数据流
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
        """
        流式执行 - 子类可重写

        Args:
            operation: 操作名称
            parameters: 操作参数

        Yields:
            数据流
        """
        # 默认实现：先执行再流式返回
        result = await self.execute(operation, parameters)
        for record in result.records:
            yield record

    async def check_connection(self) -> bool:
        """
        检查连接状态

        Returns:
            bool: 连接是否正常
        """
        try:
            return await self._check_connection()
        except Exception:
            return False

    async def _check_connection(self) -> bool:
        """
        检查连接状态 - 子类可重写

        Returns:
            bool: 连接是否正常
        """
        return self.is_connected

    async def heartbeat(self) -> bool:
        """
        发送心跳

        Returns:
            bool: 心跳是否成功
        """
        try:
            return await self._heartbeat()
        except Exception:
            return False

    async def _heartbeat(self) -> bool:
        """
        发送心跳 - 子类可重写

        Returns:
            bool: 心跳是否成功
        """
        return await self.check_connection()

    async def _on_error(self, error: Exception) -> None:
        """
        错误处理钩子 - 子类可重写

        Args:
            error: 异常对象
        """
        pass

    def _record_error(self, operation: str, error: str) -> None:
        """
        记录错误

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
        """
        获取连接器元数据

        Returns:
            元数据字典
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

    def __str__(self) -> str:
        return f"{self.name} ({self.type}) - {self._status.value}"

    def __repr__(self) -> str:
        return (f"{self.__class__.__name__}(name={self.name}, "
                f"type={self.type}, status={self._status.value})")
```

---

## 3. 扩展机制设计

### 3.1 Plugin 系统

#### 3.1.1 Plugin 接口定义

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List, Callable
import time


class PluginState(Enum):
    """插件状态"""
    DISABLED = "disabled"
    ENABLED = "enabled"
    LOADING = "loading"
    ACTIVE = "active"
    ERROR = "error"


@dataclass
class PluginConfig:
    """插件配置"""
    name: str
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    priority: int = 100  # 优先级，数字越小优先级越高
    enabled: bool = True
    depends_on: List[str] = field(default_factory=list)
    custom_settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PluginMetadata:
    """插件元数据"""
    name: str
    version: str
    description: str
    author: str
    state: PluginState
    priority: int
    loaded_at: float
    activated_at: Optional[float] = None
    last_error: Optional[str] = None


class Plugin(ABC):
    """
    Plugin 抽象基类

    所有插件都应该继承此类
    """

    def __init__(self, config: PluginConfig):
        self.config = config
        self._state = PluginState.DISABLED
        self._loaded_at: Optional[float] = None
        self._activated_at: Optional[float] = None
        self._last_error: Optional[str] = None

    @property
    def name(self) -> str:
        """获取插件名称"""
        return self.config.name

    @property
    def version(self) -> str:
        """获取插件版本"""
        return self.config.version

    @property
    def state(self) -> PluginState:
        """获取插件状态"""
        return self._state

    @property
    def priority(self) -> int:
        """获取插件优先级"""
        return self.config.priority

    @property
    def metadata(self) -> PluginMetadata:
        """获取插件元数据"""
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
        """
        加载插件

        Returns:
            bool: 加载是否成功
        """
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
        """
        加载钩子 - 子类实现

        Returns:
            bool: 加载是否成功
        """
        return True

    async def activate(self) -> bool:
        """
        激活插件

        Returns:
            bool: 激活是否成功
        """
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
        """
        激活钩子 - 子类实现

        Returns:
            bool: 激活是否成功
        """
        return True

    async def deactivate(self) -> bool:
        """
        停用插件

        Returns:
            bool: 停用是否成功
        """
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
        """
        停用钩子 - 子类实现

        Returns:
            bool: 停用是否成功
        """
        return True

    async def unload(self) -> bool:
        """
        卸载插件

        Returns:
            bool: 卸载是否成功
        """
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
        """
        卸载钩子 - 子类实现

        Returns:
            bool: 卸载是否成功
        """
        return True


class PluginManager:
    """
    插件管理器

    负责插件的加载、激活、停用、卸载
    """

    def __init__(self):
        self._plugins: Dict[str, Plugin] = {}
        self._dependency_graph: Dict[str, List[str]] = {}

    async def register_plugin(self, plugin: Plugin) -> bool:
        """
        注册插件

        Args:
            plugin: 插件实例

        Returns:
            bool: 注册是否成功
        """
        if plugin.name in self._plugins:
            return False

        self._plugins[plugin.name] = plugin
        self._dependency_graph[plugin.name] = plugin.config.depends_on

        # 加载插件
        return await plugin.load()

    async def activate_plugins(self) -> Dict[str, bool]:
        """
        按依赖顺序激活所有插件

        Returns:
            激活结果字典
        """
        # 按拓扑排序激活
        activation_order = self._topological_sort()
        results = {}

        for name in activation_order:
            plugin = self._plugins.get(name)
            if plugin and plugin.state == PluginState.ENABLED:
                results[name] = await plugin.activate()

        return results

    def _topological_sort(self) -> List[str]:
        """
        拓扑排序

        Returns:
            排序后的插件名称列表
        """
        visited = set()
        order = []

        def dfs(name: str):
            if name in visited:
                return
            visited.add(name)

            for dep in self._dependency_graph.get(name, []):
                dfs(dep)

            order.append(name)

        for name in self._plugins:
            dfs(name)

        return order

    def get_plugin(self, name: str) -> Optional[Plugin]:
        """
        获取插件

        Args:
            name: 插件名称

        Returns:
            插件实例
        """
        return self._plugins.get(name)

    def get_active_plugins(self) -> List[Plugin]:
        """
        获取所有激活的插件

        Returns:
            插件列表
        """
        return [
            p for p in self._plugins.values()
            if p.state == PluginState.ACTIVE
        ]

    async def shutdown(self) -> None:
        """关闭所有插件"""
        # 反向顺序卸载
        for name in reversed(self._topological_sort()):
            plugin = self._plugins.get(name)
            if plugin:
                await plugin.unload()
```

### 3.2 Hook 系统

#### 3.2.1 Hook 接口定义

```python
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List, Callable, Tuple
import time
import uuid
import asyncio


class HookPoint(Enum):
    """钩子点枚举"""
    # Agent 生命周期
    AGENT_BEFORE_INITIALIZE = "agent:before_initialize"
    AGENT_AFTER_INITIALIZE = "agent:after_initialize"
    AGENT_BEFORE_PROCESS = "agent:before_process"
    AGENT_AFTER_PROCESS = "agent:after_process"
    AGENT_BEFORE_SHUTDOWN = "agent:before_shutdown"
    AGENT_AFTER_SHUTDOWN = "agent:after_shutdown"

    # Skill 执行
    SKILL_BEFORE_EXECUTE = "skill:before_execute"
    SKILL_AFTER_EXECUTE = "skill:after_execute"
    SKILL_ON_ERROR = "skill:on_error"

    # Tool 执行
    TOOL_BEFORE_EXECUTE = "tool:before_execute"
    TOOL_AFTER_EXECUTE = "tool:after_execute"
    TOOL_ON_ERROR = "tool:on_error"

    # 请求处理
    REQUEST_BEFORE_PLAN = "request:before_plan"
    REQUEST_AFTER_PLAN = "request:after_plan"
    REQUEST_BEFORE_EXECUTE = "request:before_execute"
    REQUEST_AFTER_EXECUTE = "request:after_execute"
    REQUEST_BEFORE_SYNTHESIZE = "request:before_synthesize"
    REQUEST_AFTER_SYNTHESIZE = "request:after_synthesize"


class HookPriority(Enum):
    """钩子优先级"""
    HIGHEST = 0
    HIGH = 100
    NORMAL = 500
    LOW = 900
    LOWEST = 1000


@dataclass
class HookContext:
    """钩子执行上下文"""
    hook_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    hook_point: str = ""
    timestamp: float = field(default_factory=time.time)
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    stopped: bool = False

    def stop(self) -> None:
        """停止后续钩子执行"""
        self.stopped = True


@dataclass
class HookResult:
    """钩子执行结果"""
    hook_id: str
    hook_name: str
    success: bool
    execution_time_ms: float
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class Hook:
    """
    钩子类

    封装钩子函数和元数据
    """

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
        """
        执行钩子

        Args:
            context: 钩子上下文

        Returns:
            钩子执行结果
        """
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


class HookManager:
    """
    钩子管理器

    负责钩子的注册、触发、管理
    """

    def __init__(self):
        self._hooks: Dict[str, List[Hook]] = {}
        self._hook_stats: Dict[str, List[HookResult]] = {}

    def register_hook(
        self,
        name: str,
        hook_point: str,
        handler: Callable,
        priority: HookPriority = HookPriority.NORMAL,
        enabled: bool = True,
        once: bool = False,
    ) -> str:
        """
        注册钩子

        Args:
            name: 钩子名称
            hook_point: 钩子点
            handler: 处理函数
            priority: 优先级
            enabled: 是否启用
            once: 是否只执行一次

        Returns:
            钩子ID
        """
        hook = Hook(
            name=name,
            hook_point=hook_point,
            handler=handler,
            priority=priority,
            enabled=enabled,
            once=once,
        )

        if hook_point not in self._hooks:
            self._hooks[hook_point] = []

        self._hooks[hook_point].append(hook)

        # 按优先级排序
        self._hooks[hook_point].sort(key=lambda h: h.priority.value)

        return name

    def unregister_hook(self, name: str, hook_point: Optional[str] = None) -> bool:
        """
        注销钩子

        Args:
            name: 钩子名称
            hook_point: 钩子点（可选，不传则搜索所有）

        Returns:
            是否成功
        """
        hook_points = [hook_point] if hook_point else list(self._hooks.keys())

        for hp in hook_points:
            hooks = self._hooks.get(hp, [])
            for i, hook in enumerate(hooks):
                if hook.name == name:
                    hooks.pop(i)
                    return True

        return False

    async def trigger_hooks(
        self,
        hook_point: str,
        data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[HookContext, List[HookResult]]:
        """
        触发钩子

        Args:
            hook_point: 钩子点
            data: 钩子数据
            metadata: 元数据

        Returns:
            (最终上下文, 钩子结果列表)
        """
        context = HookContext(
            hook_point=hook_point,
            data=data or {},
            metadata=metadata or {},
        )

        results = []
        hooks = self._hooks.get(hook_point, [])

        for hook in hooks:
            if not hook.enabled:
                continue

            if hook.once and hook.executed_count > 0:
                continue

            result = await hook.execute(context)
            results.append(result)

            # 记录统计
            if hook_point not in self._hook_stats:
                self._hook_stats[hook_point] = []
            self._hook_stats[hook_point].append(result)

            if context.stopped:
                break

        return context, results

    def get_hooks(self, hook_point: Optional[str] = None) -> List[Hook]:
        """
        获取钩子列表

        Args:
            hook_point: 钩子点（可选）

        Returns:
            钩子列表
        """
        if hook_point:
            return self._hooks.get(hook_point, [])

        all_hooks = []
        for hooks in self._hooks.values():
            all_hooks.extend(hooks)
        return all_hooks

    def get_hook_stats(self, hook_point: Optional[str] = None) -> Dict[str, Any]:
        """
        获取钩子统计

        Args:
            hook_point: 钩子点（可选）

        Returns:
            统计信息
        """
        stats_points = [hook_point] if hook_point else list(self._hook_stats.keys())

        total_stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "avg_execution_time_ms": 0.0,
        }

        for hp in stats_points:
            results = self._hook_stats.get(hp, [])
            total_stats["total_executions"] += len(results)

            for result in results:
                if result.success:
                    total_stats["successful_executions"] += 1
                else:
                    total_stats["failed_executions"] += 1
                total_stats["avg_execution_time_ms"] += result.execution_time_ms

        if total_stats["total_executions"] > 0:
            total_stats["avg_execution_time_ms"] /= total_stats["total_executions"]

        return total_stats

    def clear_stats(self) -> None:
        """清除统计"""
        self._hook_stats.clear()


# ========== 装饰器语法 ==========

def hook(
    hook_point: str,
    name: Optional[str] = None,
    priority: HookPriority = HookPriority.NORMAL,
    enabled: bool = True,
    once: bool = False,
):
    """
    钩子装饰器

    用法：
        @hook(HookPoint.AGENT_BEFORE_PROCESS)
        async def my_hook(context: HookContext):
            ...
    """
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
```

### 3.3 Event 系统

#### 3.3.1 Event 接口定义

```python
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List, Callable, Set
import time
import uuid
import asyncio
from collections import defaultdict


class EventPriority(Enum):
    """事件优先级"""
    CRITICAL = 0
    HIGH = 100
    NORMAL = 500
    LOW = 900
    BACKGROUND = 1000


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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "source": self.source,
            "timestamp": self.timestamp,
            "data": self.data,
            "metadata": self.metadata,
            "priority": self.priority.value,
        }


@dataclass
class EventHandlerResult:
    """事件处理器结果"""
    handler_name: str
    success: bool
    execution_time_ms: float
    event_id: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


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
        """
        处理事件

        Args:
            event: 事件

        Returns:
            处理结果
        """
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


class EventBus:
    """
    事件总线

    负责事件的发布、订阅、分发
    """

    def __init__(self):
        self._handlers: Dict[str, List[EventHandler]] = defaultdict(list)
        self._wildcard_handlers: List[EventHandler] = []
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._pending_events: List[Event] = []
        self._processing_task: Optional[asyncio.Task] = None
        self._running = False
        self._event_history: List[Event] = []
        self._max_history_size: int = 10000

    def subscribe(
        self,
        event_type: str,
        handler: Callable,
        name: Optional[str] = None,
        priority: EventPriority = EventPriority.NORMAL,
    ) -> str:
        """
        订阅事件

        Args:
            event_type: 事件类型（支持 "*" 通配符）
            handler: 处理函数
            name: 处理器名称
            priority: 优先级

        Returns:
            处理器名称
        """
        handler_name = name or f"{handler.__name__}_{uuid.uuid4().hex[:8]}"

        event_handler = EventHandler(
            name=handler_name,
            event_types=[event_type],
            handler=handler,
            priority=priority,
        )

        if event_type == "*":
            self._wildcard_handlers.append(event_handler)
            self._wildcard_handlers.sort(key=lambda h: h.priority.value)
        else:
            self._handlers[event_type].append(event_handler)
            self._handlers[event_type].sort(key=lambda h: h.priority.value)

        return handler_name

    def unsubscribe(self, handler_name: str, event_type: Optional[str] = None) -> bool:
        """
        取消订阅

        Args:
            handler_name: 处理器名称
            event_type: 事件类型（可选）

        Returns:
            是否成功
        """
        # 检查通配符处理器
        for i, handler in enumerate(self._wildcard_handlers):
            if handler.name == handler_name:
                self._wildcard_handlers.pop(i)
                return True

        # 检查特定事件处理器
        event_types = [event_type] if event_type else list(self._handlers.keys())
        for et in event_types:
            handlers = self._handlers.get(et, [])
            for i, handler in enumerate(handlers):
                if handler.name == handler_name:
                    handlers.pop(i)
                    return True

        return False

    async def publish(
        self,
        event_type: str,
        source: str,
        data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        priority: EventPriority = EventPriority.NORMAL,
    ) -> str:
        """
        发布事件

        Args:
            event_type: 事件类型
            source: 事件来源
            data: 事件数据
            metadata: 元数据
            priority: 优先级

        Returns:
            事件ID
        """
        event = Event(
            event_type=event_type,
            source=source,
            data=data or {},
            metadata=metadata or {},
            priority=priority,
        )

        # 记录历史
        self._event_history.append(event)
        if len(self._event_history) > self._max_history_size:
            self._event_history = self._event_history[-self._max_history_size:]

        # 如果正在运行，加入队列；否则直接处理
        if self._running:
            await self._event_queue.put(event)
        else:
            await self._process_event(event)

        return event.event_id

    async def publish_event(self, event: Event) -> str:
        """
        发布事件对象

        Args:
            event: 事件对象

        Returns:
            事件ID
        """
        # 记录历史
        self._event_history.append(event)
        if len(self._event_history) > self._max_history_size:
            self._event_history = self._event_history[-self._max_history_size:]

        if self._running:
            await self._event_queue.put(event)
        else:
            await self._process_event(event)

        return event.event_id

    def publish_sync(
        self,
        event_type: str,
        source: str,
        data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        priority: EventPriority = EventPriority.NORMAL,
    ) -> str:
        """
        同步发布事件（非阻塞）

        Args:
            event_type: 事件类型
            source: 事件来源
            data: 事件数据
            metadata: 元数据
            priority: 优先级

        Returns:
            事件ID
        """
        event = Event(
            event_type=event_type,
            source=source,
            data=data or {},
            metadata=metadata or {},
            priority=priority,
        )

        self._event_history.append(event)
        if len(self._event_history) > self._max_history_size:
            self._event_history = self._event_history[-self._max_history_size:]

        if self._running:
            asyncio.create_task(self._event_queue.put(event))
        else:
            asyncio.create_task(self._process_event(event))

        return event.event_id

    async def start(self) -> None:
        """启动事件总线"""
        if self._running:
            return

        self._running = True
        self._processing_task = asyncio.create_task(self._process_queue())

    async def stop(self, wait: bool = True) -> None:
        """
        停止事件总线

        Args:
            wait: 是否等待队列处理完
        """
        self._running = False

        if wait and not self._event_queue.empty():
            while not self._event_queue.empty():
                await asyncio.sleep(0.01)

        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass

    async def _process_queue(self) -> None:
        """处理事件队列"""
        while self._running:
            try:
                event = await asyncio.wait_for(self._event_queue.get(), timeout=0.1)
                await self._process_event(event)
                self._event_queue.task_done()
            except asyncio.TimeoutError:
                continue
            except Exception:
                break

    async def _process_event(self, event: Event) -> List[EventHandlerResult]:
        """
        处理单个事件

        Args:
            event: 事件

        Returns:
            处理结果列表
        """
        results = []

        # 获取所有相关处理器
        handlers = []

        # 通配符处理器
        handlers.extend(self._wildcard_handlers)

        # 特定事件处理器
        if event.event_type in self._handlers:
            handlers.extend(self._handlers[event.event_type])

        # 按优先级排序
        handlers.sort(key=lambda h: h.priority.value)

        # 执行处理器
        for handler in handlers:
            if not handler.enabled:
                continue

            result = await handler.handle(event)
            results.append(result)

        return results

    def get_event_history(
        self,
        event_type: Optional[str] = None,
        source: Optional[str] = None,
        limit: int = 100,
    ) -> List[Event]:
        """
        获取事件历史

        Args:
            event_type: 事件类型过滤
            source: 来源过滤
            limit: 返回条数限制

        Returns:
            事件列表
        """
        events = self._event_history

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        if source:
            events = [e for e in events if e.source == source]

        return events[-limit:]

    def get_subscribers(self, event_type: Optional[str] = None) -> List[str]:
        """
        获取订阅者列表

        Args:
            event_type: 事件类型（可选）

        Returns:
            订阅者名称列表
        """
        subscribers = []

        if event_type == "*" or event_type is None:
            subscribers.extend(h.name for h in self._wildcard_handlers)

        if event_type is None:
            for handlers in self._handlers.values():
                subscribers.extend(h.name for h in handlers)
        elif event_type in self._handlers:
            subscribers.extend(h.name for h in self._handlers[event_type])

        return subscribers

    def clear_history(self) -> None:
        """清除事件历史"""
        self._event_history.clear()


# ========== 装饰器语法 ==========

def event_listener(
    event_type: str,
    name: Optional[str] = None,
    priority: EventPriority = EventPriority.NORMAL,
):
    """
    事件监听器装饰器

    用法：
        @event_listener("agent:process_started")
        async def on_process_started(event: Event):
            ...
    """
    def decorator(func):
        func._event_listener_info = {
            "name": name or func.__name__,
            "event_type": event_type,
            "priority": priority,
        }
        return func
    return decorator
```

---

## 4. 业务系统集成层

### 4.1 REST 适配器

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List, AsyncGenerator
import time
import aiohttp
import asyncio


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


class CircuitBreakerState(Enum):
    """熔断器状态"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """熔断器"""

    def __init__(self, threshold: int = 5, timeout_seconds: int = 30):
        self.threshold = threshold
        self.timeout_seconds = timeout_seconds
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None

    def record_success(self) -> None:
        """记录成功"""
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED

    def record_failure(self) -> None:
        """记录失败"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.threshold:
            self.state = CircuitBreakerState.OPEN

    def can_execute(self) -> bool:
        """
        检查是否可以执行

        Returns:
            bool: 是否可以执行
        """
        if self.state == CircuitBreakerState.CLOSED:
            return True

        if self.state == CircuitBreakerState.OPEN:
            if (self.last_failure_time and
                time.time() - self.last_failure_time > self.timeout_seconds):
                self.state = CircuitBreakerState.HALF_OPEN
                return True
            return False

        # HALF_OPEN - 允许一次尝试
        return True


class RESTAdapter:
    """REST 适配器"""

    def __init__(self, config: RESTConfig):
        self.config = config
        self._session: Optional[aiohttp.ClientSession] = None
        self._circuit_breaker = CircuitBreaker(
            threshold=config.circuit_breaker_threshold,
            timeout_seconds=config.circuit_breaker_timeout_seconds,
        )
        self._request_count = 0
        self._success_count = 0
        self._failure_count = 0

    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建会话"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds),
                connector=aiohttp.TCPConnector(ssl=self.config.verify_ssl),
            )
        return self._session

    def _get_auth_headers(self) -> Dict[str, str]:
        """获取认证头"""
        headers = {}

        if self.config.auth_type == AuthType.API_KEY:
            api_key_header = self.config.auth_config.get("header", "X-API-Key")
            api_key = self.config.auth_config.get("api_key", "")
            headers[api_key_header] = api_key

        elif self.config.auth_type == AuthType.BEARER:
            token = self.config.auth_config.get("token", "")
            headers["Authorization"] = f"Bearer {token}"

        elif self.config.auth_type == AuthType.BASIC:
            import base64
            username = self.config.auth_config.get("username", "")
            password = self.config.auth_config.get("password", "")
            credentials = f"{username}:{password}".encode()
            encoded = base64.b64encode(credentials).decode()
            headers["Authorization"] = f"Basic {encoded}"

        return headers

    async def request(
        self,
        method: HTTPMethod,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        timeout: Optional[int] = None,
    ) -> RESTResponse:
        """
        发送请求

        Args:
            method: HTTP 方法
            path: 请求路径
            params: 查询参数
            headers: 请求头
            json: JSON 数据
            data: 表单数据
            timeout: 超时时间

        Returns:
            REST 响应
        """
        start_time = time.time()
        self._request_count += 1

        # 检查熔断器
        if not self._circuit_breaker.can_execute():
            return RESTResponse(
                success=False,
                status_code=503,
                url=f"{self.config.base_url}{path}",
                method=method.value,
                headers={},
                error="Circuit breaker is open",
                execution_time_ms=(time.time() - start_time) * 1000,
            )

        url = f"{self.config.base_url}{path}"

        # 合并头信息
        request_headers = {**self.config.default_headers}
        if headers:
            request_headers.update(headers)

        # 添加认证头
        request_headers.update(self._get_auth_headers())

        # 合并查询参数
        request_params = {**self.config.default_params}
        if params:
            request_params.update(params)

        # 重试循环
        last_exception: Optional[Exception] = None
        last_response: Optional[RESTResponse] = None

        for attempt in range(self.config.max_retries + 1):
            try:
                session = await self._get_session()

                async with session.request(
                    method=method.value,
                    url=url,
                    params=request_params,
                    headers=request_headers,
                    json=json,
                    data=data,
                    timeout=aiohttp.ClientTimeout(total=timeout or self.config.timeout_seconds),
                    allow_redirects=self.config.follow_redirects,
                    max_redirects=self.config.max_redirects,
                ) as response:
                    content = await response.read()
                    text = None
                    json_data = None

                    # 尝试解析为文本
                    try:
                        text = content.decode("utf-8")
                    except UnicodeDecodeError:
                        pass

                    # 尝试解析为 JSON
                    if text and response.headers.get("content-type", "").startswith("application/json"):
                        import json as jsonlib
                        try:
                            json_data = jsonlib.loads(text)
                        except jsonlib.JSONDecodeError:
                            pass

                    rest_response = RESTResponse(
                        success=200 <= response.status < 300,
                        status_code=response.status,
                        url=str(response.url),
                        method=method.value,
                        headers=dict(response.headers),
                        content=content,
                        json_data=json_data,
                        text=text,
                        started_at=start_time,
                        completed_at=time.time(),
                        execution_time_ms=(time.time() - start_time) * 1000,
                    )

                    # 检查是否需要重试
                    if (rest_response.success or
                        response.status not in self.config.retry_on_statuses or
                        attempt >= self.config.max_retries):
                        if rest_response.success:
                            self._circuit_breaker.record_success()
                            self._success_count += 1
                        else:
                            self._circuit_breaker.record_failure()
                            self._failure_count += 1
                        return rest_response

                    last_response = rest_response

            except Exception as e:
                last_exception = e
                if attempt >= self.config.max_retries:
                    break

            # 等待重试
            if attempt < self.config.max_retries:
                await asyncio.sleep(self.config.retry_delay_seconds * (attempt + 1))

        # 所有重试都失败
        self._circuit_breaker.record_failure()
        self._failure_count += 1

        if last_response:
            return last_response

        return RESTResponse(
            success=False,
            status_code=0,
            url=url,
            method=method.value,
            headers={},
            error=str(last_exception) if last_exception else "Request failed",
            started_at=start_time,
            completed_at=time.time(),
            execution_time_ms=(time.time() - start_time) * 1000,
        )

    async def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> RESTResponse:
        """GET 请求"""
        return await self.request(HTTPMethod.GET, path, params=params, headers=headers, **kwargs)

    async def post(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> RESTResponse:
        """POST 请求"""
        return await self.request(HTTPMethod.POST, path, json=json, data=data, headers=headers, **kwargs)

    async def put(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> RESTResponse:
        """PUT 请求"""
        return await self.request(HTTPMethod.PUT, path, json=json, data=data, headers=headers, **kwargs)

    async def patch(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> RESTResponse:
        """PATCH 请求"""
        return await self.request(HTTPMethod.PATCH, path, json=json, data=data, headers=headers, **kwargs)

    async def delete(
        self,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> RESTResponse:
        """DELETE 请求"""
        return await self.request(HTTPMethod.DELETE, path, headers=headers, **kwargs)

    async def close(self) -> None:
        """关闭会话"""
        if self._session and not self._session.closed:
            await self._session.close()

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "request_count": self._request_count,
            "success_count": self._success_count,
            "failure_count": self._failure_count,
            "circuit_breaker_state": self._circuit_breaker.state.value,
            "circuit_breaker_failure_count": self._circuit_breaker.failure_count,
        }
```

### 4.2 数据库适配器

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List
import time
import asyncio


class DatabaseType(Enum):
    """数据库类型"""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    MONGODB = "mongodb"
    SQLITE = "sqlite"
    REDIS = "redis"


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
class QueryResult:
    """查询结果"""
    success: bool
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
        records: Optional[List[Dict[str, Any]]] = None,
        total_count: Optional[int] = None,
        page: int = 1,
        page_size: int = 100,
        has_more: bool = False,
        execution_time_ms: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "QueryResult":
        now = time.time()
        record_list = records or []
        return cls(
            success=True,
            records=record_list,
            total_count=total_count if total_count is not None else len(record_list),
            page=page,
            page_size=page_size,
            has_more=has_more,
            execution_time_ms=execution_time_ms,
            started_at=now - (execution_time_ms / 1000.0) if execution_time_ms > 0 else now,
            completed_at=now,
            metadata=metadata or {},
        )

    @classmethod
    def failure(
        cls,
        error: str = "",
        error_code: Optional[str] = None,
        execution_time_ms: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "QueryResult":
        now = time.time()
        return cls(
            success=False,
            error=error,
            error_code=error_code,
            execution_time_ms=execution_time_ms,
            started_at=now - (execution_time_ms / 1000.0) if execution_time_ms > 0 else now,
            completed_at=now,
            metadata=metadata or {},
        )


@dataclass
class ExecuteResult:
    """执行结果"""
    success: bool
    affected_rows: int = 0
    last_insert_id: Optional[Any] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    execution_time_ms: float = 0.0
    started_at: float = field(default_factory=time.time)
    completed_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def success(
        cls,
        affected_rows: int = 0,
        last_insert_id: Optional[Any] = None,
        execution_time_ms: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "ExecuteResult":
        now = time.time()
        return cls(
            success=True,
            affected_rows=affected_rows,
            last_insert_id=last_insert_id,
            execution_time_ms=execution_time_ms,
            started_at=now - (execution_time_ms / 1000.0) if execution_time_ms > 0 else now,
            completed_at=now,
            metadata=metadata or {},
        )

    @classmethod
    def failure(
        cls,
        error: str = "",
        error_code: Optional[str] = None,
        execution_time_ms: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "ExecuteResult":
        now = time.time()
        return cls(
            success=False,
            error=error,
            error_code=error_code,
            execution_time_ms=execution_time_ms,
            started_at=now - (execution_time_ms / 1000.0) if execution_time_ms > 0 else now,
            completed_at=now,
            metadata=metadata or {},
        )


class DatabaseAdapter(ABC):
    """数据库适配器抽象基类"""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._connected = False
        self._connection_count = 0
        self._query_count = 0
        self._success_count = 0
        self._failure_count = 0

    @property
    def is_connected(self) -> bool:
        """是否已连接"""
        return self._connected

    @abstractmethod
    async def connect(self) -> bool:
        """连接数据库"""
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """断开连接"""
        pass

    async def reconnect(self) -> bool:
        """重新连接"""
        for attempt in range(self.config.max_reconnect_attempts):
            try:
                if self._connected:
                    await self.disconnect()

                result = await self.connect()
                if result:
                    return True
            except Exception:
                pass

            if attempt < self.config.max_reconnect_attempts - 1:
                await asyncio.sleep(self.config.reconnect_delay_seconds * (attempt + 1))

        return False

    @abstractmethod
    async def query(
        self,
        sql: str,
        params: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 100,
    ) -> QueryResult:
        """
        执行查询

        Args:
            sql: SQL 语句
            params: 查询参数
            page: 页码
            page_size: 每页条数

        Returns:
            查询结果
        """
        pass

    @abstractmethod
    async def execute(
        self,
        sql: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> ExecuteResult:
        """
        执行写入/更新/删除

        Args:
            sql: SQL 语句
            params: 参数

        Returns:
            执行结果
        """
        pass

    @abstractmethod
    async def execute_many(
        self,
        sql: str,
        params_list: List[Dict[str, Any]],
    ) -> ExecuteResult:
        """
        批量执行

        Args:
            sql: SQL 语句
            params_list: 参数列表

        Returns:
            执行结果
        """
        pass

    @abstractmethod
    async def begin_transaction(self) -> bool:
        """开始事务"""
        pass

    @abstractmethod
    async def commit_transaction(self) -> bool:
        """提交事务"""
        pass

    @abstractmethod
    async def rollback_transaction(self) -> bool:
        """回滚事务"""
        pass

    async def health_check(self) -> bool:
        """健康检查"""
        if not self._connected:
            return False

        try:
            result = await self.query("SELECT 1")
            return result.success
        except Exception:
            return False

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "connected": self._connected,
            "connection_count": self._connection_count,
            "query_count": self._query_count,
            "success_count": self._success_count,
            "failure_count": self._failure_count,
        }


def create_database_adapter(config: DatabaseConfig) -> DatabaseAdapter:
    """
    创建数据库适配器

    Args:
        config: 数据库配置

    Returns:
        数据库适配器实例
    """
    if config.db_type == DatabaseType.POSTGRESQL:
        # 返回 PostgreSQL 适配器
        raise NotImplementedError("PostgreSQL adapter not implemented")
    elif config.db_type == DatabaseType.MYSQL:
        # 返回 MySQL 适配器
        raise NotImplementedError("MySQL adapter not implemented")
    elif config.db_type == DatabaseType.MONGODB:
        # 返回 MongoDB 适配器
        raise NotImplementedError("MongoDB adapter not implemented")
    elif config.db_type == DatabaseType.REDIS:
        # 返回 Redis 适配器
        raise NotImplementedError("Redis adapter not implemented")
    else:
        raise ValueError(f"Unsupported database type: {config.db_type}")
```

---

（文档较长，以下为关键部分摘要。完整文档请查看原文件。）

## 5. 多租户与多场景支持

### 5.1 租户管理

### 5.2 场景管理

### 5.3 配置继承机制

## 6. 数据流与执行模型

### 6.1 请求处理流程

### 6.2 Skill 执行流程

### 6.3 上下文传递机制

## 7. 接口规范

### 7.1 REST API 规范

### 7.2 WebSocket 规范

### 7.3 事件格式规范

## 8. 部署架构

### 8.1 单机部署

### 8.2 分布式部署

### 8.3 容器化部署

## 9. 安全性设计

### 9.1 认证与授权

### 9.2 数据加密

### 9.3 审计日志

## 10. 性能设计

### 10.1 并发模型

### 10.2 缓存策略

### 10.3 连接池管理

## 11. 可观测性设计

### 11.1 Metrics

### 11.2 Tracing

### 11.3 Logging

## 12. 技术选型说明

| 类别 | 技术选型 | 说明 |
|------|----------|------|
| **编程语言** | Python 3.10+ | 异步支持、生态丰富 |
| **Web 框架** | FastAPI | 高性能、异步、自动文档 |
| **异步框架** | asyncio | Python 标准库 |
| **HTTP 客户端** | aiohttp | 异步 HTTP 客户端 |
| **序列化** | pydantic | 数据验证、序列化 |
| **配置管理** | pydantic-settings | 类型安全的配置 |
| **日志** | structlog | 结构化日志 |
| **Metrics** | Prometheus + OpenTelemetry | 指标收集 |
| **Tracing** | OpenTelemetry + Jaeger | 分布式追踪 |
| **缓存** | Redis | 高性能缓存 |
| **消息队列** | Kafka / RabbitMQ | 异步消息处理 |
| **数据库** | PostgreSQL / MongoDB | 持久化存储 |
| **容器** | Docker + Kubernetes | 容器编排 |
| **API 网关** | Kong / APISIX | 限流、认证、路由 |

## 13. 附录

### 13.1 术语表

### 13.2 参考资料

### 13.3 变更日志

---

**文档结束**
