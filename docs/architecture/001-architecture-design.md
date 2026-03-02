# Agent Skills Framework - 架构设计文档 (ADD)

**版本**: 2.0.0
**日期**: 2026-02-28
**状态**: 设计中
**作者**: AI 架构师

---

## 目录

1. [概述](#1-概述)
2. [系统架构](#2-系统架构)
3. [核心模块设计](#3-核心模块设计)
4. [接口规范](#4-接口规范)
5. [数据模型设计](#5-数据模型设计)
6. [部署架构](#6-部署架构)
7. [技术栈选型](#7-技术栈选型)
8. [非功能性需求](#8-非功能性需求)
9. [扩展性设计](#9-扩展性设计)
10. [安全设计](#10-安全设计)
11. [电商场景方案](#11-电商场景方案)
12. [附录](#12-附录)

---

## 1. 概述

### 1.1 文档目的

本文档定义 Agent Skills Framework 的完整技术架构，支持从单机到分布式、从单一场景到多租户多场景的企业级部署。

### 1.2 系统定位

Agent Skills Framework 是一个**通用智能体开发框架**，采用"单 Agent 编排 + 多 Skill 协作"的架构理念，提供：

- **统一调度**: Coordinator 统一编排，避免 Multi-Agent 通信开销
- **三层上下文**: 用户输入/工作记忆/环境配置，职责分明
- **渐进式披露**: Token 线性增长，成本可控
- **双执行引擎**: 规则引擎负责确定性，LLM 负责智能性

### 1.3 架构演进路线

```
┌─────────────────────────────────────────────────────────────────┐
│                        架构演进路线图                             │
├─────────────────────────────────────────────────────────────────┤
│  v1.0 (当前)    单机版 - 健康分析场景                            │
│  v2.0 (本文档)  企业版 - 多租户、分布式、插件化                   │
│  v3.0 (未来)    云原生版 - Serverless、边缘计算、联邦学习         │
└─────────────────────────────────────────────────────────────────┘
```

### 1.4 核心设计原则

| 原则 | 说明 |
|------|------|
| **单一职责** | 每个组件职责明确，Coordinator 只负责编排 |
| **渐进复杂** | 从简单场景开始，按需引入分布式能力 |
| **合约优先** | Skills 之间通过 Schema 定义数据契约 |
| **可观测性** | 全链路审计，支持追溯和调试 |
| **插件化** | Skills、Tools、Providers 均可热插拔 |

---

## 2. 系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              客户端层 (Client Layer)                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │   Web App    │  │  Mobile App  │  │   CLI Tool   │  │  Third-party │             │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘             │
│         │                  │                  │                  │                     │
│         └──────────────────┼──────────────────┼──────────────────┘                     │
│                            │                  │                                        │
└────────────────────────────┼──────────────────┼────────────────────────────────────────┘
                             │                  │
                             ▼                  ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           API 网关层 (API Gateway Layer)                              │
│  ┌────────────────────────────────────────────────────────────────────────────────┐ │
│  │  API Gateway (Kong / Traefik / Cloudflare)                                     │ │
│  │  - 认证鉴权 (JWT / OAuth2)                                                    │ │
│  │  - 限流熔断 (Rate Limiting)                                                    │ │
│  │  - 负载均衡 (Load Balancing)                                                   │ │
│  │  - 协议转换 (HTTP/WS/gRPC)                                                      │ │
│  └────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           应用服务层 (Application Layer)                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐     │
│  │  Agent API  │  │ Skill API   │  │ Admin API   │  │  WebSocket Gateway     │     │
│  │  (FastAPI)  │  │  (FastAPI)  │  │  (FastAPI)  │  │  (Real-time Comm)      │     │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────┘     │
│         │                │                │                      │                   │
│         └────────────────┼────────────────┼──────────────────────┘                   │
│                          │                │                                          │
│                          ▼                ▼                                          │
│  ┌───────────────────────────────────────────────────────────────────────────────┐ │
│  │                    Agent Runtime (智能体运行时)                                  │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐   │ │
│  │  │ Coordinator │─▶│   Planner   │  │  Executor   │  │    Synthesizer      │   │ │
│  │  │  (协调器)    │  │  (任务规划)  │  │  (技能执行)  │  │    (结果综合)       │   │ │
│  │  └──────┬──────┘  └─────────────┘  └──────┬──────┘  └─────────────────────┘   │ │
│  │         │                                  │                                  │ │
│  │         ▼                                  ▼                                  │ │
│  │  ┌─────────────────────────────────────────────────────────────────────┐    │ │
│  │  │                    AgentContext (三层上下文)                          │    │ │
│  │  │  Layer1: 用户输入 │ Layer2: 工作记忆 │ Layer3: 环境配置              │    │ │
│  │  └─────────────────────────────────────────────────────────────────────┘    │ │
│  │                                                                               │ │
│  │  ┌─────────────────────────────────────────────────────────────────────┐    │ │
│  │  │                    Plugin System (插件系统)                           │    │ │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐     │    │ │
│  │  │  │  Skills  │  │  Tools   │  │Providers │  │   Middleware     │     │    │ │
│  │  │  │ (技能库)  │  │ (工具集)  │  │ (LLM)    │  │   (中间件)        │     │    │ │
│  │  │  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘     │    │ │
│  │  └─────────────────────────────────────────────────────────────────────┘    │ │
│  └──────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           中间件层 (Middleware Layer)                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │ Message Queue│  │   Cache      │  │   Metrics    │  │   Tracing    │             │
│  │ (Redis/RMQ)  │  │  (Redis)     │  │ (Prometheus) │  │  (Jaeger)    │             │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘             │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           数据层 (Data Layer)                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │ PostgreSQL   │  │    MongoDB   │  │    S3/MinIO  │  │ Vector DB    │             │
│  │ (业务数据)    │  │  (文档存储)   │  │  (文件存储)   │  │ (向量检索)    │             │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘             │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           外部集成层 (Integration Layer)                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │ LLM APIs     │  │ Business API │  │ Webhook      │  │ 3rd Party    │             │
│  │ (OpenAI/...) │  │ (电商/CRM)   │  │ (异步回调)    │  │ Services     │             │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘             │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 核心组件关系图

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                         核心组件交互时序图                                             │
├──────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│  Client                                                                              │
│    │                                                                                  │
│    │ 1. POST /api/v1/agent/chat                                                      │
│    ├───────────────────────────────────────────────────────────────────────────────▶ │
│    │                                                                                  │
│  API Gateway                                     Agent Runtime                       │
│    │    2. 路由 + 认证                                                                  │
│    ├──────────────────────────────────────────────────────────────────────────────▶  │
│    │                                                                                  │
│    │                                          3. process(user_input)                  │
│    │                                          Coordinator                             │
│    │                                            │                                     │
│    │                                            ├─▶ Planner.generate_plan()          │
│    │                                            │   └─▶ LLM (意图分析)                │
│    │                                            │                                     │
│    │                                            ├─▶ Executor.execute_plan()          │
│    │                                            │   └─▶ Skill 1 (规则+LLM)            │
│    │                                            │   └─▶ Skill 2 (规则+LLM)            │
│    │                                            │   └─▶ Skill 3 (规则+LLM)            │
│    │                                            │                                     │
│    │                                            └─▶ Synthesizer.synthesize()         │
│    │                                                └─▶ LLM (综合结果)                │
│    │                                                                                  │
│    │ 4. 返回响应                                                                       │
│    │◀──────────────────────────────────────────────────────────────────────────────  │
│    │                                                                                  │
│    ▼                                                                                  │
│  Client                                                                              │
│                                                                                        │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 部署视图

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                               Kubernetes 集群                                        │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                          Namespace: gateway                                   │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                          │   │
│  │  │ API Gateway │  │   Ingress   │  │   Cert Mgr   │                          │   │
│  │  │   (Kong)    │  │ Controller  │  │             │                          │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                          │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                        Namespace: agent-runtime                               │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐    │   │
│  │  │                      Agent Service (Deployment)                      │    │   │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐              │    │   │
│  │  │  │  Pod-1   │  │  Pod-2   │  │  Pod-3   │  │  Pod-N   │  (HPA)      │    │   │
│  │  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘              │    │   │
│  │  └─────────────────────────────────────────────────────────────────────┘    │   │
│  │                                                                                │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐    │   │
│  │  │                    Skill Worker (Deployment - Optional)              │    │   │
│  │  │  CPU/Memory Intensive Skills execution in separate workers            │    │   │
│  │  └─────────────────────────────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                         Namespace: data                                       │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │   │
│  │  │ PostgreSQL  │  │    Redis    │  │   MongoDB   │  │ Vector DB   │         │   │
│  │  │  (Stateful) │  │  (Stateful) │  │  (Stateful) │  │  (Stateful) │         │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘         │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                        Namespace: observability                              │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │   │
│  │  │ Prometheus  │  │   Grafana   │  │   Jaeger    │  │   Loki      │         │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘         │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. 核心模块设计

### 3.1 Coordinator (协调器)

**职责**: 统一调度整个请求处理流程

**接口**:
```python
class Coordinator:
    def process(
        self,
        user_input: str,
        session_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        stream: bool = False
    ) -> ProcessResult:
        """处理用户请求的核心入口"""

    def process_batch(
        self,
        requests: List[ProcessRequest]
    ) -> List[ProcessResult]:
        """批量处理请求"""

    async def aprocess(
        self,
        user_input: str,
        session_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        stream: bool = False
    ) -> ProcessResult:
        """异步处理入口"""
```

**状态管理**:
- 无状态设计，支持水平扩展
- Session 数据存储在 Redis
- 通过 Context Loader 恢复会话上下文

### 3.2 Planner (任务规划器)

**职责**: 分析用户意图，生成执行计划

**增强功能**:
```python
class Planner:
    def generate_plan(
        self,
        user_input: str,
        available_skills: Dict[str, Skill],
        conversation_history: Optional[List[Message]] = None,
        user_profile: Optional[UserProfile] = None,
        context_hints: Optional[Dict] = None
    ) -> ExecutionPlan:
        """生成执行计划

        增强:
        - 用户画像感知
        - 上下文提示
        - 多意图识别
        """

    def estimate_tokens(self, plan: ExecutionPlan) -> int:
        """估算 Token 消耗"""

    def validate_plan(self, plan: ExecutionPlan) -> ValidationResult:
        """验证计划可行性"""
```

### 3.3 SkillExecutor (技能执行器)

**职责**: 执行单个 Skill，支持三种模式

**执行模式**:
```python
class ExecutionMode(Enum):
    EXECUTOR = "executor"      # 自定义 Python 代码
    TEMPLATE = "template"      # Prompt 模板
    DOCUMENT = "document"      # 文档即 Skill
    HYBRID = "hybrid"          # 混合模式 (新增)
    REMOTE = "remote"          # 远程 Skill (新增)
```

**增强接口**:
```python
class SkillExecutor:
    def execute(
        self,
        skill: Skill,
        sub_task: str,
        context: Dict[str, Any],
        timeout: Optional[float] = None,
        retry: int = 0
    ) -> SkillResult:
        """执行 Skill

        增强:
        - 超时控制
        - 重试机制
        - 熔断降级
        """

    async def aexecute(
        self,
        skill: Skill,
        sub_task: str,
        context: Dict[str, Any]
    ) -> SkillResult:
        """异步执行"""

    def execute_stream(
        self,
        skill: Skill,
        sub_task: str,
        context: Dict[str, Any]
    ) -> AsyncIterator[str]:
        """流式执行"""
```

### 3.4 Synthesizer (结果综合器)

**职责**: 综合多步结果，生成最终响应

**增强接口**:
```python
class Synthesizer:
    def synthesize(
        self,
        context: AgentContext,
        style: Optional[str] = None,
        format: OutputFormat = OutputFormat.TEXT
    ) -> str:
        """综合结果

        增强:
        - 风格控制 (formal/casual/professional)
        - 格式支持 (text/markdown/json/html)
        - 多语言支持
        """

    def synthesize_stream(
        self,
        context: AgentContext
    ) -> AsyncIterator[str]:
        """流式综合"""
```

### 3.5 AgentContext (上下文管理)

**职责**: 三层上下文管理，权限控制

**增强功能**:
```python
class AgentContext:
    # 原有三层
    layer1: UserInputLayer    # 用户输入
    layer2: ScratchpadLayer   # 工作记忆
    layer3: EnvironmentLayer  # 环境配置

    # 新增
    layer4: TenantLayer       # 租户隔离 (新增)
    layer5: AuditLayer        # 审计日志 (增强)

    def load_session(self, session_id: str) -> bool:
        """从 Redis 加载会话"""

    def save_session(self, session_id: str, ttl: int = 3600) -> bool:
        """保存会话到 Redis"""

    def export_trace(self) -> TraceData:
        """导出完整追踪数据"""
```

### 3.6 Plugin System (插件系统)

**职责**: Skills、Tools、Providers 的动态加载和管理

**接口设计**:
```python
class PluginManager:
    def register_plugin(
        self,
        plugin_type: PluginType,
        plugin: Plugin,
        source: PluginSource
    ) -> bool:
        """注册插件

        支持来源:
        - 本地文件系统
        - Git 仓库
        - HTTP(S) URL
        - Package Registry
        """

    def load_plugin(
        self,
        plugin_id: str,
        version: Optional[str] = None
    ) -> Plugin:
        """加载插件"""

    def unload_plugin(self, plugin_id: str) -> bool:
        """卸载插件"""

    def hot_reload(self, plugin_id: str) -> bool:
        """热重载插件"""

    def list_plugins(
        self,
        plugin_type: Optional[PluginType] = None,
        tenant_id: Optional[str] = None
    ) -> List[PluginInfo]:
        """列出可用插件"""

    def resolve_dependencies(
        self,
        plugin_id: str
    ) -> List[PluginDependency]:
        """解析依赖关系"""
```

---

## 4. 接口规范

### 4.1 REST API 设计

#### 4.1.1 基础规范

- **协议**: HTTPS
- **数据格式**: JSON
- **认证**: JWT Bearer Token
- **版本控制**: URL 版本 (/api/v1/)
- **限流**: 基于租户和用户的分级限流

#### 4.1.2 Agent API

```yaml
# 对话接口
POST /api/v1/agent/chat
Request:
  {
    "message": "string",           # 用户消息
    "session_id": "string?",       # 会话 ID（首次为空）
    "tenant_id": "string?",        # 租户 ID
    "stream": "boolean?",          # 是否流式输出
    "context": {                   # 额外上下文
      "user_profile": {},
      "metadata": {}
    }
  }
Response:
  {
    "response": "string",          # 响应内容
    "session_id": "string",        # 会话 ID
    "plan": {                      # 执行计划
      "intent": "string",
      "steps": []
    },
    "metrics": {                   # 性能指标
      "duration_ms": 1000,
      "tokens_used": 500,
      "skills_executed": 3
    },
    "audit_id": "string"           # 审计 ID
  }

# 流式对话接口
WS /api/v1/agent/chat/stream
Message:
  {
    "type": "request|response|error|done",
    "data": {}
  }

# 批量处理接口
POST /api/v1/agent/batch
Request:
  {
    "requests": [
      {"message": "...", "id": "1"},
      {"message": "...", "id": "2"}
    ]
  }

# 取消请求
DELETE /api/v1/agent/requests/{request_id}
```

#### 4.1.3 Skill Management API

```yaml
# 列出 Skills
GET /api/v1/skills
Response:
  {
    "skills": [
      {
        "name": "parse_report",
        "version": "1.0.0",
        "description": "...",
        "triggers": [],
        "tags": [],
        "execution_mode": "executor"
      }
    ]
  }

# 获取 Skill 详情
GET /api/v1/skills/{skill_name}
Response:
  {
    "name": "parse_report",
    "schema": {...},
    "documentation": "...",
    "examples": []
  }

# 上传 Skill (租户私有)
POST /api/v1/skills
Request (multipart):
  {
    "skill_file": "file",
    "manifest": "json"
  }

# 删除 Skill
DELETE /api/v1/skills/{skill_name}

# 启用/禁用 Skill
PATCH /api/v1/skills/{skill_name}/status
Request:
  {
    "enabled": true
  }
```

#### 4.1.4 Session API

```yaml
# 获取会话历史
GET /api/v1/sessions/{session_id}
Response:
  {
    "session_id": "...",
    "messages": [
      {"role": "user", "content": "...", "timestamp": "..."},
      {"role": "assistant", "content": "...", "timestamp": "..."}
    ],
    "context": {},
    "created_at": "...",
    "updated_at": "..."
  }

# 获取会话列表
GET /api/v1/sessions
Query: limit=20, offset=0

# 删除会话
DELETE /api/v1/sessions/{session_id}

# 清空会话上下文（保留历史）
POST /api/v1/sessions/{session_id}/clear
```

#### 4.1.5 Admin API

```yaml
# 健康检查
GET /api/v1/health

# 指标
GET /api/v1/metrics

# 配置
GET /api/v1/config
PUT /api/v1/config

# 租户管理
GET /api/v1/admin/tenants
POST /api/v1/admin/tenants
DELETE /api/v1/admin/tenants/{tenant_id}

# 用户管理
GET /api/v1/admin/users
POST /api/v1/admin/users
```

### 4.2 WebSocket 协议

#### 4.2.1 连接

```
WS /api/v1/agent/chat/stream?token={jwt_token}
```

#### 4.2.2 消息格式

```yaml
# 客户端请求
{
  "type": "request",
  "id": "uuid",
  "data": {
    "message": "...",
    "session_id": "...?"
  }
}

# 服务端响应片段
{
  "type": "chunk",
  "id": "uuid",
  "data": {
    "content": "text片段...",
    "done": false
  }
}

# 完成
{
  "type": "done",
  "id": "uuid",
  "data": {
    "metrics": {...}
  }
}

# 错误
{
  "type": "error",
  "id": "uuid",
  "data": {
    "code": "ERROR_CODE",
    "message": "..."
  }
}
```

### 4.3 Webhook 规范

```yaml
# Webhook 事件类型
EVENT_TYPES:
  - agent.completed:       请求完成
  - agent.failed:          请求失败
  - skill.executed:        Skill 执行完成
  - skill.failed:          Skill 执行失败
  - threshold.exceeded:    阈值告警（Token/时间）

# Webhook Payload
{
  "event": "agent.completed",
  "timestamp": "2026-02-28T10:00:00Z",
  "tenant_id": "...",
  "data": {
    "request_id": "...",
    "session_id": "...",
    "user_input": "...",
    "response": "...",
    "metrics": {...}
  }
}

# 签名
Header: X-Webhook-Signature: sha256=<signature>
计算方法: HMAC_SHA256(secret, body)
```

---

## 5. 数据模型设计

### 5.1 核心数据模型

```python
from dataclasses import dataclass
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum

# ─── 基础类型 ───

class MessageType(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class ExecutionStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class SkillMode(Enum):
    EXECUTOR = "executor"
    TEMPLATE = "template"
    DOCUMENT = "document"
    REMOTE = "remote"

# ─── 消息模型 ───

@dataclass
class Message:
    id: str
    role: MessageType
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = None
    tokens_used: int = 0

# ─── 会话模型 ───

@dataclass
class Session:
    id: str
    tenant_id: str
    user_id: str
    messages: List[Message]
    context_state: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None

# ─── 执行计划模型 ───

@dataclass
class ExecutionStep:
    skill: str
    sub_task: str
    confidence: float
    depends_on: List[str] = None
    timeout: float = 30.0

@dataclass
class ExecutionPlan:
    id: str
    intent: str
    steps: List[ExecutionStep]
    estimated_tokens: int
    created_at: datetime

# ─── Skill 模型 ───

@dataclass
class SkillSchema:
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]

@dataclass
class Skill:
    name: str
    version: str
    description: str
    execution_mode: SkillMode
    triggers: List[str]
    tags: List[str]
    schema: SkillSchema
    documentation: str
    author: str
    dependencies: List[str] = None
    timeout: float = 30.0

@dataclass
class SkillResult:
    skill_name: str
    success: bool
    structured: Dict[str, Any]
    text: str
    execution_time_ms: float
    tokens_used: int
    error: Optional[str] = None

# ─── 审计模型 ───

@dataclass
class AuditEntry:
    id: str
    timestamp: datetime
    tenant_id: str
    session_id: str
    request_id: str
    component: str
    operation: str
    layer: str
    key: str
    value_preview: str
    execution_time_ms: float

# ─── 租户模型 ───

@dataclass
class Tenant:
    id: str
    name: str
    plan: str  # free/pro/enterprise
    settings: Dict[str, Any]
    rate_limits: Dict[str, int]
    created_at: datetime
    enabled: bool = True

@dataclass
class TenantSkillConfig:
    tenant_id: str
    skill_name: str
    enabled: bool
    config: Dict[str, Any]

# ─── 用户模型 ───

@dataclass
class User:
    id: str
    tenant_id: str
    username: str
    email: str
    role: str  # admin/user/developer
    preferences: Dict[str, Any]
    created_at: datetime

# ─── API 密钥模型 ───

@dataclass
class APIKey:
    id: str
    tenant_id: str
    user_id: str
    key_hash: str
    scopes: List[str]
    expires_at: Optional[datetime]
    last_used: Optional[datetime]
    created_at: datetime
```

### 5.2 数据库表设计

```sql
-- 租户表
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    plan VARCHAR(50) NOT NULL DEFAULT 'free',
    settings JSONB DEFAULT '{}',
    rate_limits JSONB DEFAULT '{"requests_per_minute": 60, "tokens_per_day": 100000}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    enabled BOOLEAN DEFAULT TRUE
);

-- 用户表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255),
    role VARCHAR(50) DEFAULT 'user',
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);

-- API 密钥表
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    user_id UUID REFERENCES users(id),
    key_hash VARCHAR(255) NOT NULL,
    scopes JSONB DEFAULT '["chat", "skills:read"]',
    expires_at TIMESTAMP,
    last_used TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 会话表
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    user_id UUID REFERENCES users(id),
    context_state JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
);

-- 消息表
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id),
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    tokens_used INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 请求记录表
CREATE TABLE requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    session_id UUID REFERENCES sessions(id),
    user_input TEXT NOT NULL,
    response TEXT,
    status VARCHAR(20) NOT NULL,
    plan JSONB,
    metrics JSONB,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- Skill 执行记录表
CREATE TABLE skill_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID REFERENCES requests(id),
    skill_name VARCHAR(100) NOT NULL,
    sub_task TEXT NOT NULL,
    success BOOLEAN NOT NULL,
    structured_output JSONB,
    text_output TEXT,
    error_message TEXT,
    execution_time_ms FLOAT,
    tokens_used INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 审计日志表
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    session_id UUID,
    request_id UUID,
    component VARCHAR(50) NOT NULL,
    operation VARCHAR(50) NOT NULL,
    layer VARCHAR(50) NOT NULL,
    key_name VARCHAR(255),
    value_preview TEXT,
    execution_time_ms FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Webhook 表
CREATE TABLE webhooks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    url VARCHAR(500) NOT NULL,
    events JSONB NOT NULL,
    secret VARCHAR(255),
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_sessions_tenant_user ON sessions(tenant_id, user_id);
CREATE INDEX idx_sessions_expires ON sessions(expires_at);
CREATE INDEX idx_messages_session ON messages(session_id, created_at);
CREATE INDEX idx_requests_tenant ON requests(tenant_id, created_at);
CREATE INDEX idx_audit_logs_tenant ON audit_logs(tenant_id, created_at);
CREATE INDEX idx_skill_executions_request ON skill_executions(request_id);
```

### 5.3 Redis 数据结构

```python
# Session 缓存
session:{session_id} = {
    "tenant_id": "...",
    "user_id": "...",
    "messages": [...],
    "context_state": {...},
    "expires_at": "..."
}
TTL: 3600 (可配置)

# Rate Limiting
rate_limit:{tenant_id}:{user_id}:requests = count
TTL: 60

# Token Budget
token_budget:{tenant_id}:{date} = used_tokens
TTL: 86400

# Skill 缓存
skill:{skill_name}:{version} = {
    "name": "...",
    "schema": {...},
    "code": "..."
}
TTL: 3600

# 分布式锁
lock:session:{session_id} = owner_id
TTL: 30

# Pub/Sub 频道
channel:tenant:{tenant_id}:events
channel:skill:{skill_name}:updates
```

---

## 6. 部署架构

### 6.1 容器化设计

#### 6.1.1 Dockerfile

```dockerfile
# 多阶段构建
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .

ENV PATH=/root/.local/bin:$PATH
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 6.1.2 Docker Compose (开发环境)

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/agent
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
    volumes:
      - ./skills:/app/skills

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: agent
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"

volumes:
  postgres_data:
  redis_data:
```

### 6.2 Kubernetes 部署

#### 6.2.1 Namespace

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: agent-runtime
```

#### 6.2.2 Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agent-service
  namespace: agent-runtime
spec:
  replicas: 3
  selector:
    matchLabels:
      app: agent-service
  template:
    metadata:
      labels:
        app: agent-service
    spec:
      containers:
      - name: agent-api
        image: agent-skills:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-secret
              key: url
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
          limits:
            cpu: 2000m
            memory: 2Gi
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: agent-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: agent-service
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

#### 6.2.3 Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: agent-service
  namespace: agent-runtime
spec:
  selector:
    app: agent-service
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP
```

#### 6.2.4 Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: agent-ingress
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    traefik.ingress.kubernetes.io/rate-limit: "100"
spec:
  tls:
  - hosts:
    - api.agent.example.com
    secretName: agent-tls
  rules:
  - host: api.agent.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: agent-service
            port:
              number: 80
```

---

## 7. 技术栈选型

### 7.1 技术选型表

| 层级 | 技术选型 | 理由 |
|------|---------|------|
| **Web 框架** | FastAPI | 高性能、异步支持、自动文档 |
| **ASGI 服务器** | Uvicorn | 高性能、原生异步 |
| **数据库** | PostgreSQL 15 | 关系型、JSONB 支持、成熟稳定 |
| **文档存储** | MongoDB 7 | 灵活 Schema、适合 Skill 存储 |
| **缓存** | Redis 7 | 高性能、支持 Pub/Sub |
| **消息队列** | Redis Stream / RabbitMQ | 轻量级 / 可靠消息 |
| **向量数据库** | Weaviate / Milvus | 语义搜索、RAG 支持 |
| **对象存储** | MinIO / S3 | 文件存储、Skill 包管理 |
| **监控** | Prometheus + Grafana | 云原生监控 |
| **链路追踪** | Jaeger / Tempo | 分布式追踪 |
| **日志** | Loki / ELK | 日志聚合 |
| **API 网关** | Kong / Traefik | 功能丰富、易用 |
| **服务网格** | Istio (可选) | 流量管理、安全 |
| **容器编排** | Kubernetes | 标准、成熟 |
| **CI/CD** | GitLab CI / GitHub Actions | DevOps |

### 7.2 依赖清单

```txt
# requirements.txt

# Web 框架
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
pydantic-settings==2.1.0

# 数据库
asyncpg==0.29.0          # PostgreSQL 异步驱动
sqlalchemy[asyncio]==2.0.25
alembic==1.13.1          # 数据库迁移
motor==3.3.2             # MongoDB 异步驱动
redis==5.0.1
hiredis==2.3.2           # C 扩展

# 认证鉴权
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6

# LLM 客户端
openai==1.10.0
anthropic==0.18.1
httpx==0.26.0

# 工具库
pyyaml==6.0.1
python-dotenv==1.0.0
tenacity==8.2.3          # 重试
structlog==24.1.0        # 结构化日志

# 监控追踪
prometheus-client==0.19.0
opentelemetry-api==1.22.0
opentelemetry-sdk==1.22.0
opentelemetry-instrumentation-fastapi==0.43b0

# 开发工具
pytest==7.4.4
pytest-asyncio==0.23.3
pytest-cov==4.1.0
black==24.1.1
ruff==0.1.14
mypy==1.8.0
```

---

## 8. 非功能性需求

### 8.1 性能指标

| 指标 | 目标值 | 测量方法 |
|------|--------|----------|
| **响应时间** | P50 < 2s, P95 < 5s, P99 < 10s | API 监控 |
| **吞吐量** | 100+ QPS 单实例 | 负载测试 |
| **并发用户** | 1000+ 并发连接 | WebSocket 测试 |
| **Token 效率** | < 10K tokens/请求 | Token 计数 |
| **可用性** | 99.9% SLA | 运维监控 |

### 8.2 可扩展性

- **水平扩展**: 无状态设计，支持 Pod 水平扩展
- **垂直扩展**: 支持 GPU 加速的 LLM 推理
- **数据分片**: 按租户 ID 分片
- **缓存策略**: 多级缓存 (本地 + Redis)

### 8.3 安全性

- **认证**: JWT + OAuth2
- **授权**: RBAC 基于角色的访问控制
- **数据隔离**: 租户级别数据隔离
- **加密**: TLS 传输加密，数据库存储加密
- **审计**: 完整操作审计日志
- **输入验证**: Pydantic 模型验证
- **输出过滤**: 敏感信息脱敏

### 8.4 可观测性

```python
# 指标
- request_count_total: 请求总数
- request_duration_seconds: 请求延迟
- skill_execution_duration_seconds: Skill 执行时间
- token_consumed_total: Token 消耗
- llm_api_calls_total: LLM API 调用

# 日志
- 结构化日志 (JSON)
- 日志级别: DEBUG/INFO/WARNING/ERROR
- 关联 ID: request_id / trace_id

# 追踪
- OpenTelemetry 分布式追踪
- Span 类型: http, skill, llm, database
```

---

## 9. 扩展性设计

### 9.1 多租户支持

```python
class TenantMiddleware:
    async def process_request(self, request: Request):
        # 从 JWT 中提取租户 ID
        tenant_id = self.extract_tenant(request)

        # 设置租户上下文
        request.state.tenant_id = tenant_id

        # 加载租户配置
        config = await self.load_tenant_config(tenant_id)
        request.state.tenant_config = config

        # 检查租户状态
        if not config.enabled:
            raise HTTPException(403, "Tenant disabled")

class TenantIsolation:
    @staticmethod
    def filter_query(table: Table, tenant_id: str):
        """自动添加租户过滤条件"""
        return table.select().where(table.c.tenant_id == tenant_id)
```

### 9.2 插件系统

```python
class PluginLoader:
    async def load_from_git(self, repo_url: str, ref: str = "main"):
        """从 Git 仓库加载 Skill"""
        # 1. Clone 仓库
        # 2. 解析 SKILL.md
        # 3. 加载依赖
        # 4. 注册到 SkillRegistry

    async def load_from_http(self, url: str):
        """从 HTTP URL 加载 Skill"""
        # 1. 下载 Skill 包
        # 2. 验证签名
        # 3. 解压加载

    async def hot_reload(self, skill_name: str):
        """热重载 Skill"""
        # 1. 卸载旧版本
        # 2. 加载新版本
        # 3. 更新路由
```

### 9.3 分布式支持

```python
class DistributedExecutor:
    async def execute(self, skill: Skill, context: Dict):
        """分布式执行 Skill"""
        # 1. 检查是否需要远程执行
        if skill.requires_remote:
            # 2. 发送到消息队列
            await self.queue.publish(
                "skill.execute",
                {"skill": skill.name, "context": context}
            )
            # 3. 等待结果
            result = await self.wait_for_result(task_id)
            return result
        else:
            # 本地执行
            return await self.local_executor.execute(skill, context)
```

### 9.4 热加载/热更新

```python
class HotReloadManager:
    def watch_skills_dir(self):
        """监控 Skills 目录变化"""
        watcher = watchdog.Observer()
        watcher.schedule(
            SkillsDirHandler(),
            path=self.skills_dir,
            recursive=True
        )
        watcher.start()

    async def reload_skill(self, skill_name: str):
        """重载 Skill"""
        # 1. 检查是否有正在执行的请求
        # 2. 等待执行完成
        # 3. 重新加载 Skill 定义
        # 4. 更新 SkillRegistry
```

---

## 10. 安全设计

### 10.1 认证鉴权

```python
from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_token(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> TokenData:
    """验证 JWT Token"""
    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        tenant_id = payload.get("tenant_id")
        user_id = payload.get("sub")

        if not tenant_id or not user_id:
            raise HTTPException(401, "Invalid token")

        return TokenData(tenant_id=tenant_id, user_id=user_id)

    except JWTError:
        raise HTTPException(401, "Invalid token")

def require_scope(*scopes: str):
    """检查权限范围"""
    def decorator(func):
        async def wrapper(*args, token: TokenData = Depends(verify_token)):
            user_scopes = await get_user_scopes(token.user_id)
            if not any(s in user_scopes for s in scopes):
                raise HTTPException(403, "Insufficient permissions")
            return await func(*args, token=token)
        return wrapper
    return decorator
```

### 10.2 数据隔离

```python
class TenantDataFilter:
    """租户数据过滤中间件"""

    async def filter_response(self, response: Dict, tenant_id: str):
        """过滤响应数据，确保只返回租户自己的数据"""
        # 1. 递归遍历响应
        # 2. 过滤跨租户数据
        # 3. 移除敏感字段

    async def sanitize_input(self, input_data: Dict):
        """清理输入数据"""
        # 1. 移除租户 ID 注入尝试
        # 2. SQL 注入防护
        # 3. XSS 防护
```

### 10.3 API 限流

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v1/agent/chat")
@limiter.limit("60/minute")  # 每分钟 60 次
async def chat(
    request: Request,
    message: ChatMessage,
    token: TokenData = Depends(verify_token)
):
    # 租户级别限流
    tenant_limit = await get_tenant_rate_limit(token.tenant_id)
    if not await check_tenant_limit(token.tenant_id, tenant_limit):
        raise HTTPException(429, "Tenant rate limit exceeded")

    # 处理请求
    ...
```

---

## 11. 电商场景方案

### 11.1 电商 Skill 设计

```python
# skills/ecommerce/product_search/executor.py
async def execute(llm, sub_task, context):
    """商品搜索 Skill"""
    query = extract_query(sub_task)
    filters = extract_filters(context)

    # 调用电商 API
    products = await ecommerce_api.search_products(
        query=query,
        filters=filters
    )

    # LLM 生成推荐描述
    summary = await llm.invoke(f"""
    用户搜索: {query}
    找到 {len(products)} 个商品
    前3个: {[p['name'] for p in products[:3]]}

    请生成推荐说明:
    """)

    return {
        "structured": {
            "products": products[:10],
            "total": len(products)
        },
        "text": summary
    }

# skills/ecommerce/recommendation/executor.py
async def execute(llm, sub_task, context):
    """个性化推荐 Skill"""
    user_id = context.get("user_id")
    history = await get_user_history(user_id)

    # 获取推荐
    recommendations = await recommendation_engine.get_recommendations(
        user_id=user_id,
        history=history,
        limit=10
    )

    return {
        "structured": {"recommendations": recommendations},
        "text": format_recommendations(recommendations)
    }
```

### 11.2 会话管理

```python
class EcommerceSessionManager:
    """电商场景会话管理"""

    async def create_cart_session(self, user_id: str) -> str:
        """创建购物车会话"""
        session_id = generate_id()
        await redis.setex(
            f"cart:{session_id}",
            3600,  # 1小时过期
            json.dumps({
                "user_id": user_id,
                "items": [],
                "created_at": now()
            })
        )
        return session_id

    async def add_to_cart(self, session_id: str, product: dict):
        """添加商品到购物车"""
        cart = await redis.get(f"cart:{session_id}")
        cart_data = json.loads(cart)
        cart_data["items"].append(product)
        await redis.setex(f"cart:{session_id}", 3600, json.dumps(cart_data))
```

### 11.3 电商 API 对接

```python
class EcommerceAPIAdapter:
    """电商 API 适配器"""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key

    async def search_products(
        self,
        query: str,
        category: str = None,
        price_range: tuple = None,
        sort: str = "relevance"
    ) -> List[Product]:
        """搜索商品"""
        params = {"q": query, "sort": sort}
        if category:
            params["category"] = category
        if price_range:
            params["min_price"], params["max_price"] = price_range

        response = await self.http_client.get(
            f"{self.base_url}/products/search",
            params=params,
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        return response.json()["products"]

    async def get_product_details(self, product_id: str) -> Product:
        """获取商品详情"""
        response = await self.http_client.get(
            f"{self.base_url}/products/{product_id}",
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        return response.json()

    async def create_order(
        self,
        user_id: str,
        items: List[OrderItem],
        shipping_address: Address
    ) -> Order:
        """创建订单"""
        response = await self.http_client.post(
            f"{self.base_url}/orders",
            json={
                "user_id": user_id,
                "items": [asdict(i) for i in items],
                "shipping_address": asdict(shipping_address)
            },
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        return response.json()
```

---

## 12. 附录

### 12.1 错误码定义

```python
class ErrorCode(Enum):
    # 通用错误 1000-1999
    UNKNOWN_ERROR = (1000, "Unknown error")
    INVALID_REQUEST = (1001, "Invalid request")
    RATE_LIMIT_EXCEEDED = (1002, "Rate limit exceeded")

    # 认证鉴权 2000-2999
    UNAUTHORIZED = (2001, "Unauthorized")
    FORBIDDEN = (2003, "Forbidden")
    TOKEN_EXPIRED = (2004, "Token expired")

    # Skill 错误 3000-3999
    SKILL_NOT_FOUND = (3001, "Skill not found")
    SKILL_EXECUTION_FAILED = (3002, "Skill execution failed")
    SKILL_TIMEOUT = (3003, "Skill execution timeout")

    # LLM 错误 4000-4999
    LLM_API_ERROR = (4001, "LLM API error")
    LLM_QUOTA_EXCEEDED = (4002, "LLM quota exceeded")
    TOKEN_LIMIT_EXCEEDED = (4003, "Token limit exceeded")

    # 租户错误 5000-5999
    TENANT_NOT_FOUND = (5001, "Tenant not found")
    TENANT_DISABLED = (5002, "Tenant disabled")
    TENANT_QUOTA_EXCEEDED = (5003, "Tenant quota exceeded")
```

### 12.2 配置示例

```yaml
# config/production.yaml

server:
  host: "0.0.0.0"
  port: 8000
  workers: 4

database:
  url: "postgresql://user:pass@postgres:5432/agent"
  pool_size: 20
  max_overflow: 10

redis:
  url: "redis://redis:6379/0"
  session_ttl: 3600
  cache_ttl: 300

llm:
  default_provider: "anthropic"
  default_model: "glm-4.7"
  timeout: 30
  max_retries: 3

skills:
  directory: "/app/skills"
  hot_reload: true
  timeout: 30

security:
  secret_key: "${SECRET_KEY}"
  algorithm: "HS256"
  token_expire_hours: 24

limits:
  requests_per_minute: 60
  tokens_per_day: 100000
  concurrent_sessions: 10

monitoring:
  enabled: true
  metrics_port: 9090
  trace_enabled: true
```

---

*文档版本: 2.0.0*
*最后更新: 2026-02-28*
*作者: AI 架构师*
