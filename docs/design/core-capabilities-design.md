# 通用智能体开发框架 - 核心能力设计文档

**版本**: 1.0.0
**日期**: 2026-02-28
**作者**: AI产品经理
**状态**: 设计阶段

---

## 目录

1. [概述](#概述)
2. [核心能力总览](#核心能力总览)
3. [能力详情](#能力详情)
   - 3.1 多租户/多场景管理能力
   - 3.2 插件化Skill生态
   - 3.3 业务系统集成能力
   - 3.4 监控与可观测性
   - 3.5 开发者体验
4. [API设计规范](#api设计规范)
5. [成功指标](#成功指标)

---

## 概述

### 设计目标

基于现有的Agent Skills Framework代码库，本设计文档定义了通用智能体开发框架的核心能力，旨在：

1. **保持现有优势** - 三层上下文、双执行引擎、渐进式披露等核心架构
2. **补齐企业级能力** - 多租户、API服务、监控告警、数据连接器
3. **提升开发者体验** - CLI工具、SDK、文档、示例

### 设计原则

| 原则 | 说明 | 体现 |
|------|------|------|
| **向后兼容** | 不破坏现有框架API | 新能力以扩展模块形式提供 |
| **渐进增强** | 核心框架保持轻量，能力按需启用 | 多租户、API服务等可独立部署 |
| **配置驱动** | 通过配置而非代码控制行为 | YAML/JSON配置覆盖代码逻辑 |
| **可观测优先** | 所有操作可追踪、可审计 | 全链路日志、指标、追踪 |

---

## 核心能力总览

### 能力矩阵

```
┌─────────────────────────────────────────────────────────────────────┐
│                        核心能力架构                                   │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐       │
│  │   多租户管理    │  │   Skill生态    │  │  业务系统集成   │       │
│  │  ├─租户隔离    │  │  ├─Skill市场   │  │  ├─数据连接器  │       │
│  │  ├─场景管理    │  │  ├─版本管理    │  │  ├─API集成     │       │
│  │  └─配置继承    │  │  └─热更新      │  │  └─Webhook    │       │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘       │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐                           │
│  │  监控可观测性    │  │   开发者体验    │                           │
│  │  ├─实时监控    │  │  ├─CLI工具     │                           │
│  │  ├─审计日志    │  │  ├─多语言SDK   │                           │
│  │  ├─分布式追踪  │  │  ├─文档示例    │                           │
│  │  └─告警机制    │  │  └─调试工具    │                           │
│  └─────────────────┘  └─────────────────┘                           │
└─────────────────────────────────────────────────────────────────────┘
```

### 优先级划分

| 优先级 | 能力 | 说明 | 与现有框架关系 |
|--------|------|------|----------------|
| P0 | 多租户管理 | 租户隔离、场景管理 | 新增模块，不影响现有代码 |
| P0 | API服务层 | REST API、认证鉴权 | 新增api/模块，独立部署 |
| P0 | 数据连接器 | 数据库/API/消息队列连接 | 扩展Tool系统 |
| P1 | 监控告警 | 指标、日志、追踪 | 扩展现有audit.py |
| P1 | 对话管理 | 多轮对话、状态管理 | 完善dialogue/模块 |
| P2 | CLI工具 | 脚手架、调试、部署 | 独立工具包 |
| P2 | Skill市场 | 分发、版本、热更新 | 独立服务 |

---

## 能力详情

### 3.1 多租户/多场景管理能力 (P0)

#### 3.1.1 用户故事

**US-1.1 租户管理** (企业开发者)
> 作为企业开发者，我希望为不同业务线创建独立的Agent实例，使得各业务线的配置、数据和权限完全隔离。

**US-1.2 场景配置** (独立开发者)
> 作为独立开发者，我希望在同一租户下创建多个场景（如客服场景、推荐场景），每个场景使用不同的Skill组合和配置。

**US-1.3 配置继承** (AI工程师)
> 作为AI工程师，我希望租户级配置可以被场景级继承覆盖，减少重复配置工作。

#### 3.1.2 功能需求

| 功能 | 需求描述 | 验收标准 |
|------|----------|----------|
| **租户创建** | 支持创建新租户，分配唯一ID | 租户ID全局唯一，创建时间<100ms |
| **租户隔离** | 租户间数据、配置、日志完全隔离 | 租户A无法访问租户B的任何数据 |
| **场景管理** | 支持租户内多场景创建和切换 | 单租户支持100+场景，切换延迟<50ms |
| **配置继承** | 支持租户级→场景级配置继承 | 支持3级继承链，覆盖优先级正确 |
| **资源配额** | 支持租户级Token预算、QPS限制 | 配额超限自动触发告警或限流 |

#### 3.1.3 接口设计

```python
# 租户上下文
@dataclass
class TenantContext:
    tenant_id: str
    name: str
    config: TenantConfig
    scenes: Dict[str, SceneContext]
    resource_quota: ResourceQuota
    created_at: datetime

# 场景上下文
@dataclass
class SceneContext:
    scene_id: str
    tenant_id: str
    name: str
    description: str
    skill_whitelist: List[str]
    llm_config: LLMConfig  # 可覆盖租户配置
    custom_tools: List[str]

# 配置管理示例
tenant_config = {
    "tenant_id": "tenant_123",
    "llm_config": {
        "provider": "anthropic",
        "model": "glm-4.7"
    },
    "scenes": {
        "customer_service": {
            "skills": ["order_query", "after_sales"],
            "llm_config": {"temperature": 0.5}  # 覆盖租户配置
        }
    }
}
```

#### 3.1.4 数据模型

```sql
-- 租户表
CREATE TABLE tenants (
    tenant_id VARCHAR(32) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    config JSONB,
    resource_quota JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 场景表
CREATE TABLE scenes (
    scene_id VARCHAR(32) PRIMARY KEY,
    tenant_id VARCHAR(32) REFERENCES tenants(tenant_id),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    skill_whitelist JSONB,
    llm_config JSONB,
    custom_tools JSONB,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_tenant_id (tenant_id)
);
```

---

### 3.2 插件化Skill生态 (P1)

#### 3.2.1 用户故事

**US-2.1 Skill开发** (AI工程师)
> 作为AI工程师，我希望使用标准模板快速创建自定义Skill，并通过声明式配置定义Skill的元数据、触发词和依赖关系。

**US-2.2 Skill管理** (企业开发者)
> 作为企业开发者，我希望在组织内部分享和复用Skill，并控制不同租户可用的Skill白名单。

**US-2.3 Skill市场** (独立开发者)
> 作为独立开发者，我希望从社区Skill市场发现和安装第三方Skill，快速扩展我的Agent能力。

#### 3.2.2 功能需求

| 功能 | 需求描述 | 验收标准 |
|------|----------|----------|
| **Skill脚手架** | 提供CLI工具快速创建Skill模板 | 5分钟内生成可用Skill骨架 |
| **本地开发** | 支持本地Skill开发和热重载 | 代码修改后10秒内生效 |
| **Skill注册** | 支持将Skill注册到租户/场景 | 注册延迟<100ms |
| **版本管理** | 支持Skill版本控制和兼容性检查 | 支持语义化版本，兼容性检查准确率>99% |
| **Skill市场(Phase 2)** | 提供Skill发布、搜索、安装功能 | 支持按标签/评分搜索，安装成功率>95% |

#### 3.2.3 Skill目录结构

```
skills/
├── builtin/                    # 内置Skills
│   ├── parse_report/
│   ├── assess_risk/
│   └── generate_advice/
├── custom/                     # 租户自定义Skills
│   └── {tenant_id}/
│       └── my_custom_skill/
└── marketplace/                # 市场下载的Skills (Phase 2)
    └── {skill_name}/{version}/
```

#### 3.2.4 SKILL.md规范

```yaml
---
name: string                    # 必需: Skill唯一标识
version: string               # 必需: 语义化版本
description: string           # 必需: 简短描述
triggers:                     # 必需: 触发词列表
  - string
tags:                         # 可选: 标签
  - string
input_schema:                 # 可选: 输入参数schema
  type: object
  properties:
    field_name:
      type: string
      description: string
output_schema: string         # 可选: 输出schema名称
tools:                        # 可选: 依赖的Tools
  - string
dependencies:                 # 可选: Skill依赖
  - name: string
    version: string
author: string                # 可选: 作者
license: string               # 可选: 许可证
---

# Skill说明文档

## 功能说明
...

## 使用示例
...

## 注意事项
...
```

---

### 3.3 业务系统集成能力 (P0)

#### 3.3.1 用户故事

**US-3.1 数据库集成** (企业开发者)
> 作为企业开发者，我希望将Agent连接到现有的业务数据库，使Skill能够查询订单、用户、商品等数据。

**US-3.2 API集成** (AI工程师)
> 作为AI工程师，我希望通过简单的配置将外部API封装为Tool，供Skill调用。

**US-3.3 消息队列集成** (企业开发者)
> 作为企业开发者，我希望Agent能够通过消息队列与现有系统进行异步通信。

#### 3.3.2 功能需求

| 功能 | 需求描述 | 验收标准 |
|------|----------|----------|
| **数据源配置** | 支持YAML配置数据源连接 | 支持10+种数据源类型 |
| **数据库连接器** | 支持MySQL、PostgreSQL、MongoDB等 | 连接池管理，连接失败自动重试 |
| **API连接器** | 支持RESTful API调用 | 支持认证、限流、超时配置 |
| **消息队列集成** | 支持Kafka、RabbitMQ | 支持发布/订阅模式 |
| **连接池管理** | 自动管理连接生命周期 | 连接泄漏检测，自动回收 |
| **健康检查** | 数据源可用性检查 | 健康状态API，异常告警 |

#### 3.3.3 Connector接口设计

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from dataclasses import dataclass

@dataclass
class ConnectorConfig:
    """数据源配置基类"""
    name: str
    type: str  # database, http, message_queue, etc.
    connection_params: Dict[str, Any]
    pool_size: int = 10
    timeout: int = 30
    retry_policy: Optional[Dict] = None

class BaseConnector(ABC):
    """数据源连接器基类"""

    def __init__(self, config: ConnectorConfig):
        self.config = config
        self._connection = None
        self._health_status = "unknown"

    @abstractmethod
    async def connect(self) -> bool:
        """建立连接"""
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """断开连接"""
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        pass

    @property
    def is_connected(self) -> bool:
        """连接状态"""
        return self._connection is not None

    @property
    def health_status(self) -> str:
        """健康状态"""
        return self._health_status

# 数据库连接器示例
class DatabaseConnector(BaseConnector):
    """数据库连接器"""

    async def connect(self) -> bool:
        # 实现数据库连接逻辑
        # 使用连接池管理
        pass

    async def disconnect(self) -> bool:
        # 实现断开连接逻辑
        pass

    async def health_check(self) -> Dict[str, Any]:
        # 执行简单查询检查连接状态
        pass

    async def execute(self, query: str, params: Optional[Dict] = None) -> Any:
        """执行SQL查询"""
        pass

    async def fetch_one(self, query: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """获取单条记录"""
        pass

    async def fetch_many(self, query: str, params: Optional[Dict] = None, limit: int = 100) -> List[Dict]:
        """获取多条记录"""
        pass

# HTTP API连接器示例
class HttpConnector(BaseConnector):
    """HTTP API连接器"""

    async def connect(self) -> bool:
        # 初始化HTTP客户端会话
        pass

    async def disconnect(self) -> bool:
        # 关闭HTTP会话
        pass

    async def health_check(self) -> Dict[str, Any]:
        # 调用健康检查端点
        pass

    async def get(self, path: str, params: Optional[Dict] = None, headers: Optional[Dict] = None) -> Any:
        """GET请求"""
        pass

    async def post(self, path: str, data: Optional[Dict] = None, headers: Optional[Dict] = None) -> Any:
        """POST请求"""
        pass
```

#### 3.3.4 数据源配置示例

```yaml
# config.yaml - 数据源配置
data_sources:
  # 订单数据库
  order_db:
    type: postgresql
    connection_string: "${ORDER_DB_URL}"
    pool_size: 10
    timeout: 30
    health_check:
      interval: 30s
      query: "SELECT 1"

  # 用户画像数据库
  user_profile_db:
    type: mongodb
    connection_string: "${USER_PROFILE_DB_URL}"
    database: "user_profiles"
    pool_size: 5

  # 支付API
  payment_api:
    type: http
    base_url: "https://api.payment.com/v1"
    auth:
      type: bearer
      token: "${PAYMENT_API_TOKEN}"
    retry:
      max_retries: 3
      backoff: exponential

  # 物流查询API
  logistics_api:
    type: http
    base_url: "https://api.logistics.com"
    auth:
      type: api_key
      key_header: X-API-Key
      key_value: "${LOGISTICS_API_KEY}"

  # 消息队列（用于异步通知）
  notification_mq:
    type: kafka
    brokers:
      - "kafka1:9092"
      - "kafka2:9092"
    topic: "agent-notifications"
    producer_config:
      acks: all
      retries: 3
```

---

### 3.4 监控与可观测性 (P1)

#### 3.4.1 用户故事

**US-4.1 实时监控** (企业开发者)
> 作为企业开发者，我希望实时监控Agent的运行状态、Token消耗和响应延迟，及时发现并处理问题。

**US-4.2 审计追踪** (AI工程师)
> 作为AI工程师，我希望查看完整的执行链路，追溯每个决策的来源和上下文。

**US-4.3 告警通知** (企业开发者)
> 作为企业开发者，我希望在Token预算耗尽、错误率升高或响应变慢时收到告警通知。

#### 3.4.2 功能需求

| 功能 | 需求描述 | 验收标准 |
|------|----------|----------|
| **指标采集** | 采集执行次数、延迟、Token消耗等 | 支持Prometheus格式，采集延迟<100ms |
| **实时监控** | 提供Dashboard展示关键指标 | 刷新间隔支持1s-5min可调 |
| **审计日志** | 记录完整的执行链路 | 支持查询最近90天日志 |
| **分布式追踪** | 支持OpenTelemetry标准 | 追踪成功率>99% |
| **告警规则** | 支持自定义告警规则 | 支持阈值、趋势、异常检测 |
| **通知渠道** | 支持Webhook、邮件、短信 | 告警触达延迟<30s |

---

### 3.5 开发者体验 (P2)

#### 3.5.1 用户故事

**US-5.1 快速开始** (独立开发者)
> 作为独立开发者，我希望在5分钟内完成环境搭建并运行第一个Agent。

**US-5.2 CLI工具** (AI工程师)
> 作为AI工程师，我希望使用CLI工具快速创建Skill模板、本地调试和部署Agent。

**US-5.3 文档和示例** (企业开发者)
> 作为企业开发者，我希望有完整的API文档、最佳实践指南和可运行的示例代码。

#### 3.5.2 功能需求

| 功能 | 需求描述 | 验收标准 |
|------|----------|----------|
| **项目脚手架** | 提供项目初始化模板 | 3步完成初始化 |
| **Skill脚手架** | 提供Skill创建模板 | 支持3种执行模式模板 |
| **本地调试** | 支持本地运行和调试 | 支持断点调试、热重载 |
| **配置管理** | 支持多环境配置 | 支持dev/test/prod环境 |
| **文档生成** | 自动生成API文档 | 支持OpenAPI/Swagger |
| **示例集合** | 提供常用场景示例 | 覆盖10+常见场景 |

---

## API设计规范

### REST API端点

```yaml
# API端点设计
paths:
  # 对话接口
  /api/v1/agent/chat:
    post:
      summary: 发送对话消息
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                session_id:
                  type: string
                user_id:
                  type: string
                message:
                  type: string
                context:
                  type: object
      responses:
        200:
          description: 成功响应
          content:
            application/json:
              schema:
                type: object
                properties:
                  response:
                    type: string
                  session_id:
                    type: string
                  metrics:
                    type: object

  /api/v1/agent/chat/stream:
    post:
      summary: 流式对话接口
      responses:
        200:
          description: SSE流式响应
          content:
            text/event-stream:
              schema:
                type: string

  # 会话管理
  /api/v1/sessions/{session_id}:
    get:
      summary: 获取会话信息
    delete:
      summary: 删除会话

  /api/v1/sessions/{session_id}/history:
    get:
      summary: 获取会话历史

  # Skill管理
  /api/v1/skills:
    get:
      summary: 获取可用Skill列表
    post:
      summary: 上传自定义Skill

  /api/v1/skills/{skill_name}:
    get:
      summary: 获取Skill详情
    delete:
      summary: 删除Skill

  # 监控指标
  /api/v1/metrics:
    get:
      summary: 获取系统指标
      parameters:
        - name: start_time
          in: query
          schema:
            type: string
        - name: end_time
          in: query
          schema:
            type: string
        - name: tenant_id
          in: query
          schema:
            type: string

  /api/v1/metrics/realtime:
    get:
      summary: 获取实时监控数据
      responses:
        200:
          description: Prometheus格式指标
          content:
            text/plain:
              schema:
                type: string

  # 审计日志
  /api/v1/audit/logs:
    get:
      summary: 查询审计日志
      parameters:
        - name: start_time
          in: query
        - name: end_time
          in: query
        - name: tenant_id
          in: query
        - name: session_id
          in: query
        - name: operation
          in: query
```

### 认证与授权

```yaml
# 认证方式
securitySchemes:
  ApiKeyAuth:
    type: apiKey
    in: header
    name: X-API-Key
  BearerAuth:
    type: http
    scheme: bearer
    bearerFormat: JWT

# 权限控制
permissions:
  - agent:chat              # 对话权限
  - agent:admin             # 管理权限
  - skills:read             # 查看Skill
  - skills:write            # 创建/修改Skill
  - tenants:read            # 查看租户信息
  - tenants:write           # 管理租户
  - metrics:read            # 查看监控指标
  - audit:read              # 查看审计日志
```

---

## 成功指标

### 产品指标

| 指标 | 目标值 | 测量方式 |
|------|--------|----------|
| 月活跃用户 (MAU) | 1000+ (6个月) | 注册用户活跃统计 |
| 企业租户数 | 50+ (6个月) | 付费企业数 |
| API调用次数 | 100万+/月 | API调用统计 |
| 平均响应时间 | <2s | 性能监控 |
| 系统可用性 | >99.5% | 监控统计 |
| Skill复用率 | >70% | Skill使用统计 |

### 开发者体验指标

| 指标 | 目标值 | 测量方式 |
|------|--------|----------|
| 5分钟接入成功率 | >90% | 埋点统计 |
| 文档覆盖度 | 100% | 文档完整性检查 |
| Issue响应时间 | <24h | GitHub Issues |
| 社区贡献 | 10+ Skills/月 | Skill市场 |

---

## 附录

### A. 术语表

| 术语 | 定义 |
|------|------|
| Agent | 智能体，具有目标导向能力的AI系统 |
| Skill | 技能，Agent具备的特定能力模块 |
| Coordinator | 协调器，统一调度整个执行流程 |
| Context | 上下文，执行过程中的状态数据 |
| Tenant | 租户，框架的使用单位（企业/团队） |
| Scene | 场景，租户内的Agent实例，具有独立的Skill组合和配置 |
| Tool | 工具，Skill可调用的底层功能 |
| Connector | 连接器，标准化的数据源接入组件 |

### B. 参考资料

- 现有PRD: `docs/PRD_Agent_Skills_Framework.md`
- 现有设计文档: `docs/plans/2025-02-28-universal-agent-framework-design.md`
- 电商场景设计: `docs/ecommerce_skills_design.md`
- 框架代码: `/agent/coordinator.py`, `/agent/context.py`, `/utils/skill_loader.py`
