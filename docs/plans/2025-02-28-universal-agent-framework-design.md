# 通用智能体开发框架 - 设计文档

## 1. 产品定位

### 1.1 产品愿景

打造一个**通用、可扩展、易接入**的智能体开发框架，让业务系统能够快速集成 AI 能力，无需深入了解 AI 技术细节。

### 1.2 目标用户

| 用户类型 | 需求 | 接入方式 |
|---------|------|----------|
| **企业开发者** | 快速集成 AI 能力到现有系统 | API / SDK |
| **独立开发者** | 简单易用，快速上手 | REST API |
| **AI 工程师** | 高度可定制，灵活扩展 | 插件开发 |

### 1.3 核心价值

- **降低接入门槛** - 3 行代码接入智能体
- **开箱即用** - 内置常用 Skills 和 Tools
- **灵活扩展** - 插件化架构，自定义 Skills
- **生产就绪** - 完整的监控、日志、限流能力

---

## 2. 系统架构

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         业务系统层                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   电商系统   │  │   客服系统   │  │   其他业务   │             │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘             │
└─────────┼────────────────┼────────────────┼────────────────────┘
          │                │                │
          └────────────────┼────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────────────┐
│                      API 网关层                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  认证鉴权     │  │  限流熔断     │  │  路由分发     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└──────────────────────────┬─────────────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────────────┐
│                     智能体服务层                                  │
│  ┌─────────────────────────────────────────────────────┐       │
│  │                  Agent Runtime                        │       │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ │       │
│  │  │Coordinator│ │  Planner │ │ Executor ││Synthesizer│ │       │
│  │  └──────────┘ └──────────┘ └──────────┘ └────────┘ │       │
│  └─────────────────────────────────────────────────────┘       │
│  ┌─────────────────────────────────────────────────────┐       │
│  │                  Skill Engine                         │       │
│  │  ┌─────────────────────────────────────────────┐    │       │
│  │  │  Skill Loader  │  Skill Executor  │  Skill  │    │       │
│  │  │    Registry     │     (3 Modes)     │  Store  │    │       │
│  │  └─────────────────────────────────────────────┘    │       │
│  └─────────────────────────────────────────────────────┘       │
└──────────────────────────┬─────────────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────────────┐
│                      基础设施层                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  多租户管理   │  │  上下文管理   │  │  审计日志     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Token 管理   │  │  Tool 系统    │  │  LLM 适配器   │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└──────────────────────────┬─────────────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────────────┐
│                      外部服务层                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  LLM 服务     │  │  业务 API     │  │  消息队列     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 核心模块

#### 2.2.1 多租户管理

```python
# 租户配置
@dataclass
class TenantConfig:
    tenant_id: str
    name: str
    llm_config: LLMConfig
    skill_whitelist: List[str]  # 允许使用的 Skills
    rate_limit: RateLimit
    custom_tools: List[str]
```

#### 2.2.2 会话管理

```python
# 会话状态
@dataclass
class AgentSession:
    session_id: str
    tenant_id: str
    user_id: str
    context: AgentContext
    created_at: datetime
    last_active: datetime
    metadata: Dict[str, Any]
```

#### 2.2.3 API 接口设计

```python
# REST API 端点
POST /api/v1/agent/chat           # 对话接口
POST /api/v1/agent/chat/stream    # 流式对话
GET  /api/v1/sessions/{id}        # 获取会话
GET  /api/v1/sessions/{id}/history # 获取历史
POST /api/v1/skills/custom        # 上传自定义 Skill
GET  /api/v1/metrics              # 获取指标
```

---

## 3. 电商场景 Demo 设计

### 3.1 场景一：订单查询智能体

**用户意图**：查询订单状态、物流信息、申请退款

**Skills 设计**：

| Skill | 功能 | 触发词 |
|-------|------|--------|
| query_order | 查询订单基本信息 | 查订单、我的订单 |
| track_logistics | 查询物流信息 | 物流、快递、配送 |
| request_refund | 申请退款/退货 | 退款、退货、返还 |
| order_analytics | 订单数据分析 | 订单统计、消费分析 |

**数据流**：

```
用户输入 → 意图识别 → Skill 调用 → 业务 API → 结果综合
                                    ↓
                          电商订单系统 API
```

### 3.2 场景二：商品推荐智能体

**用户意图**：获取商品推荐、比价、咨询

**Skills 设计**：

| Skill | 功能 | 触发词 |
|-------|------|--------|
| recommend_product | 基于偏好推荐商品 | 推荐、有什么好的 |
| compare_product | 商品对比 | 对比、区别 |
| product_detail | 商品详情查询 | 多少钱、怎么样 |
| search_product | 商品搜索 | 找、搜索 |

**数据流**：

```
用户输入 → 意图识别 → 偏好分析 → Skill 调用 → 商品 API → 结果综合
                                   ↓
                         用户画像 + 商品库 API
```

---

## 4. 扩展机制

### 4.1 Skill 扩展

**目录结构**：

```
skills/
├── builtin/              # 内置 Skills
│   ├── query_order/
│   ├── recommend_product/
│   └── ...
└── custom/               # 租户自定义 Skills
    ├── tenant_123/
    │   └── my_skill/
    └── tenant_456/
        └── their_skill/
```

**上传 Skill**：

```python
# 通过 API 上传
POST /api/v1/skills/custom
{
    "tenant_id": "tenant_123",
    "skill_name": "my_skill",
    "files": {
        "SKILL.md": "...",
        "executor.py": "..."
    }
}
```

### 4.2 Tool 扩展

**业务 Tool 注册**：

```python
# 通过 API 注册
POST /api/v1/tools/register
{
    "tenant_id": "tenant_123",
    "tool": {
        "name": "query_user_points",
        "description": "查询用户积分",
        "endpoint": "https://api.example.com/points",
        "method": "GET"
    }
}
```

### 4.3 LLM Provider 扩展

```python
# 配置自定义 Provider
PUT /api/v1/tenants/{id}/llm-config
{
    "provider": "custom",
    "endpoint": "https://your-llm-api.com",
    "api_key": "your-key",
    "model": "your-model"
}
```

---

## 5. 接入流程

### 5.1 快速接入（3 步）

**Step 1: 创建租户**

```bash
curl -X POST https://agent-api.example.com/api/v1/tenants \
  -H "Content-Type: application/json" \
  -d '{
    "name": "电商业务",
    "llm_config": {
      "provider": "anthropic",
      "model": "glm-4.7",
      "api_key": "your-key"
    }
  }'
```

**Step 2: 获取 API Key**

```bash
# 返回结果包含
{
  "tenant_id": "tenant_123",
  "api_key": "sk_agent_xxxxx"
}
```

**Step 3: 调用智能体**

```python
import requests

response = requests.post(
    "https://agent-api.example.com/api/v1/agent/chat",
    headers={"Authorization": "Bearer sk_agent_xxxxx"},
    json={
        "user_id": "user_456",
        "message": "帮我查一下最近的订单"
    }
)

print(response.json()["response"])
```

### 5.2 SDK 接入

```python
# pip install agent-framework-sdk

from agent_framework import AgentClient

# 初始化客户端
client = AgentClient(
    api_key="sk_agent_xxxxx",
    base_url="https://agent-api.example.com"
)

# 对话
response = client.chat(
    user_id="user_456",
    message="帮我查一下最近的订单"
)

print(response.content)
```

---

## 6. 技术栈

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| Web 框架 | FastAPI | 高性能异步框架 |
| 数据库 | PostgreSQL | 租户、会话、日志存储 |
| 缓存 | Redis | 会话缓存、限流 |
| 消息队列 | Redis | 异步任务队列 |
| LLM SDK | OpenAI/Anthropic | 多 Provider 支持 |
| 部署 | Docker + K8s | 容器化部署 |
| 监控 | Prometheus + Grafana | 指标监控 |

---

## 7. 非功能性需求

### 7.1 性能指标

| 指标 | 目标值 |
|------|--------|
| QPS | 1000+ |
| P95 延迟 | < 2s |
| P99 延迟 | < 5s |
| 可用性 | 99.9% |

### 7.2 安全性

- API Key 认证
- 租户数据隔离
- 敏感信息脱敏
- 请求签名验证

### 7.3 可观测性

- 结构化日志
- 分布式追踪
- 指标采集
- 审计日志

---

## 8. 实施计划

### Phase 1: 核心框架（2 周）
- 多租户管理
- Web API 服务
- 会话管理
- 基础 Skills

### Phase 2: 电商 Demo（1 周）
- 订单查询智能体
- 商品推荐智能体
- 前端演示页面

### Phase 3: 生产增强（1 周）
- 监控告警
- 性能优化
- 文档完善

---

## 9. 交付物

1. **框架代码** - 可部署的智能体服务
2. **电商 Demo** - 2 个完整场景案例
3. **SDK** - Python SDK
4. **文档** - API 文档、接入指南
5. **测试报告** - 功能、性能测试报告
