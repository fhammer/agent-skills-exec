# Agent Skills Framework - 产品需求文档 (PRD)

**版本**: 1.0.0
**日期**: 2026-02-28
**产品经理**: AI Product Manager
**状态**: 草案

---

## 目录

1. [产品概述](#产品概述)
2. [目标用户画像](#目标用户画像)
3. [产品定位](#产品定位)
4. [核心功能需求](#核心功能需求)
5. [电商场景案例设计](#电商场景案例设计)
6. [接入流程设计](#接入流程设计)
7. [技术架构约束](#技术架构约束)
8. [成功指标](#成功指标)
9. [路线图](#路线图)

---

## 产品概述

### 产品愿景

打造一个通用智能体开发框架，让企业能够快速构建、部署和管理 AI Agent 能力，无需从零开发复杂的编排系统。

### 产品使命

降低 AI Agent 开发门槛，让业务系统快速接入智能能力，实现"一次开发，多场景复用"。

### 核心价值主张

| 维度 | 传统方案 | Agent Skills Framework |
|------|----------|----------------------|
| 开发效率 | 数周/数月 | 数小时/数天 |
| Token 成本 | 15K-25K/请求 | 6K-10K/请求 |
| 调试难度 | 高（跨 Agent 调试） | 低（全链路审计） |
| 扩展性 | 低（紧耦合） | 高（即插即用 Skills） |
| 企业级特性 | 需自建 | 开箱即用 |

---

## 目标用户画像

### 1. 企业开发者 (Enterprise Developer)

**特征**：
- 背景：后端开发工程师，在企业内部团队工作
- 技术栈：熟悉 Python/Java/Go，了解企业系统集成
- 痛点：需要快速将 AI 能力集成到现有业务系统，但不想深入学习 Multi-Agent 编排
- 预算：有预算购买企业版，需要 SLA 保障

**核心需求**：
- 与现有系统（数据库、API、消息队列）无缝集成
- 多租户/多场景隔离
- 企业级安全和合规
- 完善的监控和告警
- 技术支持和培训

**使用场景**：
- 为公司内部系统添加 AI 助手
- 构建客户服务智能体
- 自动化业务流程（如订单处理、风险评估）

### 2. 独立开发者 (Independent Developer)

**特征**：
- 背景：全栈开发者或创业公司技术负责人
- 技术栈：熟悉 Python 和 JavaScript，追求快速迭代
- 痛点：想快速验证 AI 产品想法，不想在基础设施上投入太多时间
- 预算：敏感，优先使用免费/开源版本

**核心需求**：
- 快速上手，最小化学习曲线
- 丰富的示例和模板
- 社区支持和免费文档
- 本地运行能力
- 灵活的定价模式

**使用场景**：
- 快速构建 AI 原型
- 为个人项目添加 AI 功能
- 创业公司的 MVP 开发

### 3. AI 工程师 (AI Engineer)

**特征**：
- 背景：专注 AI/ML 领域，深入了解 LLM 原理
- 技术栈：精通 Python，熟悉各种 LLM API
- 痛点：需要一个灵活的框架来定制复杂的 Agent 行为
- 预算：不是主要考虑因素，更关注功能完整性

**核心需求**：
- 高度可定制和可扩展
- 支持多种 LLM Provider
- 精细的控制和调试能力
- 高级功能（流式输出、Token 管理、自定义执行策略）
- 开放的架构

**使用场景**：
- 构建复杂的定制化 Agent
- 研究 Agent 编排模式
- 为企业开发深度定制方案

---

## 产品定位

### 市场定位

**Agent Skills Framework** 定位为"企业级 AI Agent 基础设施"，介于以下两者之间：

1. **轻量级 LLM SDK**（如 LangChain）：提供基础能力，但缺乏企业级特性
2. **复杂 Multi-Agent 框架**（如 AutoGen、CrewAI）：功能强大但成本高、调试难

### 差异化优势

| 特性 | LangChain | AutoGen | Agent Skills Framework |
|------|-----------|---------|----------------------|
| Token 效率 | 中 | 低（高通信成本） | **高（渐进式披露）** |
| 学习曲线 | 陡峭 | 陡峭 | **平缓** |
| 调试体验 | 一般 | 困难 | **优秀（审计日志）** |
| 企业级特性 | 需自建 | 需自建 | **内置** |
| 执行模式 | 纯 LLM | 纯 LLM | **双引擎（规则+LLM）** |

### 产品分层

```
┌─────────────────────────────────────────────────────────┐
│                   应用层                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │ 电商场景    │  │ 金融场景    │  │ 医疗场景    │      │
│  └─────────────┘  └─────────────┘  └─────────────┘      │
├─────────────────────────────────────────────────────────┤
│                   解决方案层                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │ Skill 市场  │  │ 行业模板    │  │ 示例项目    │      │
│  └─────────────┘  └─────────────┘  └─────────────┘      │
├─────────────────────────────────────────────────────────┤
│                   框架核心层 ⭐                            │
│  ┌─────────────────────────────────────────────────┐    │
│  │     Coordinator + Planner + Executor + Synthesizer │ │
│  │     三层上下文 + 双执行引擎 + 全链路审计          │    │
│  └─────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────┤
│                   基础设施层                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │ LLM 抽象    │  │ 多租户管理  │  │ 监控可观测  │      │
│  └─────────────┘  └─────────────┘  └─────────────┘      │
└─────────────────────────────────────────────────────────┘
```

---

## 核心功能需求

### FR1: 多租户/多场景支持

**需求描述**：支持多个租户在同一框架下独立运行，互不干扰。

**功能点**：

1.1 租户隔离
- 独立的 Skill 集合
- 独立的 LLM 配置（Provider、模型、API Key）
- 独立的 Token 预算管理
- 隔离的审计日志

1.2 多场景管理
- 同一租户可创建多个 Agent 实例（场景）
- 每个场景可配置不同的 Skill 组合
- 场景级别的配置覆盖

1.3 配置管理
- 支持租户级、场景级配置继承
- 热更新配置（无需重启）
- 配置版本管理

**技术实现**：
- 新增 `TenantContext` 封装租户级状态
- `SkillRegistry` 支持按租户隔离
- `Coordinator` 支持多实例并发

### FR2: 插件化 Skill 生态

**需求描述**：Skills 可以独立开发、管理、分发和复用。

**功能点**：

2.1 Skill 开发
- 标准 Skill 目录结构
- 三种执行模式（executor.py、prompt.template、SKILL.md）
- Skill 本地开发工具

2.2 Skill 管理
- Skill 版本管理
- Skill 依赖声明
- Skill 启用/禁用

2.3 Skill 市场（Phase 2）
- 官方 Skill 市场
- 社区贡献机制
- Skill 评分和评论

**技术实现**：
- 当前已支持本地 Skill 自动发现
- 扩展支持远程 Skill 加载（Git、HTTP）
- Skill 版本兼容性检查

### FR3: 与业务系统集成

**需求描述**：提供标准化的方式让业务系统接入 Agent 能力。

**功能点**：

3.1 REST API 服务
- 标准 HTTP API 接口
- 请求/响应标准化
- 流式输出支持（SSE）

3.2 认证与授权
- API Key 认证
- JWT Token 支持
- 租户级权限控制

3.3 数据源连接器
- 数据库连接器（MySQL、PostgreSQL、MongoDB）
- REST API 调用器
- 消息队列集成（Kafka、RabbitMQ）
- 文件存储集成（OSS、S3）

3.4 Webhook 支持
- 执行结果回调
- 异步任务通知

**技术实现**：
- 新增 API Server 模块（基于 FastAPI）
- Tool 系统扩展为数据源连接器
- 异步执行支持（asyncio）

### FR4: 监控与可观测性

**需求描述**：提供完整的监控、追踪和告警能力。

**功能点**：

4.1 实时监控
- 执行次数、成功率、平均延迟
- Token 消耗趋势
- 错误率统计

4.2 审计日志
- 完整的执行链路记录
- 可追溯每个决策过程
- 日志导出和查询

4.3 分布式追踪
- 请求级追踪
- Span 关联
- 性能分析

4.4 告警机制
- Token 预算告警
- 错误率告警
- 延迟告警
- 自定义告警规则

**技术实现**：
- 基于现有 `audit.py` 扩展
- 集成 OpenTelemetry 标准
- 新增 Metrics 模块
- Webhook/邮件/短信告警

### FR5: 开发者体验

**需求描述**：提供优秀的开发体验，降低学习成本。

**功能点**：

5.1 CLI 工具
- 项目初始化
- Skill 创建脚手架
- 本地调试服务器
- 配置管理

5.2 SDK
- Python SDK（已完成）
- JavaScript SDK（Phase 2）

5.3 文档和示例
- 快速开始指南
- API 参考文档
- 最佳实践
- 示例项目集合

5.4 调试工具
- 本地调试模式
- 单步执行
- 变量检查
- 性能分析

---

## 电商场景案例设计

### 场景 1: 订单查询智能体

**用户故事**：用户想要查询订单状态，智能体帮助查询并返回详细信息。

**Skill 设计**：

```yaml
name: order_query
version: 1.0.0
description: 查询订单状态和详细信息
triggers:
  - 查询订单
  - 订单状态
  - 我的订单
  - 订单详情
tools:
  - query_order_by_id
  - query_orders_by_user
  - query_order_status
```

**数据流**：

```
用户输入
  ↓
[Intent Recognition] - 识别查询意图
  ↓
[Parameter Extraction] - 提取订单ID/用户信息
  ↓
[Order Query Tool] - 查询数据库
  ↓
[Result Formatter] - 格式化输出
  ↓
返回结果
```

**执行示例**：

```python
# 用户输入
"帮我查询一下订单 2024022812345 的状态"

# Skill 执行
order_query.execute(
    sub_task="查询订单 2024022812345 的状态",
    context={
        "user_id": "user_123",
        "parameters": {
            "order_id": "2024022812345"
        }
    }
)

# 返回结果
{
    "structured": {
        "order_id": "2024022812345",
        "status": "已发货",
        "estimated_delivery": "2024-03-01",
        "items": [...]
    },
    "text": "您的订单 2024022812345 已发货，预计 3月1日 送达。"
}
```

### 场景 2: 商品推荐智能体

**用户故事**：用户询问商品推荐，智能体根据用户画像和商品库推荐合适商品。

**Skill 设计**：

```yaml
name: product_recommendation
version: 1.0.0
description: 根据用户需求推荐商品
triggers:
  - 推荐
  - 有什么好
  - 想买
  - 建议
tools:
  - query_user_profile
  - search_products
  - calculate_similarity
  - rank_products
```

**数据流**：

```
用户输入
  ↓
[Intent Analysis] - 分析需求类别（价格、品牌、用途）
  ↓
[User Profile] - 获取用户历史和偏好
  ↓
[Product Search] - 搜索候选商品
  ↓
[Ranking Engine] - 规则引擎排序（规则+LLM混合）
  ↓
[Explanation Generator] - 生成推荐理由
  ↓
返回结果
```

**执行示例**：

```python
# 用户输入
"我想买一个2000元左右的手机，性价比高的"

# Skill 执行
product_recommendation.execute(
    sub_task="推荐2000元左右性价比高的手机",
    context={
        "user_id": "user_123",
        "constraints": {
            "category": "手机",
            "price_range": [1500, 2500],
            "priority": "性价比"
        }
    }
)

# 返回结果
{
    "structured": {
        "recommendations": [
            {
                "product_id": "p_001",
                "name": "Xiaomi 14",
                "price": 1999,
                "score": 0.92,
                "reasons": ["旗舰处理器", "高刷新率屏幕"]
            }
        ]
    },
    "text": "根据您的需求，我推荐 Xiaomi 14，售价1999元..."
}
```

### 场景 3: 售后服务智能体

**用户故事**：用户遇到售后问题，智能体帮助处理退换货、投诉等。

**Skill 设计**：

```yaml
name: after_sales_service
version: 1.0.0
description: 处理售后问题，包括退换货、投诉、咨询
triggers:
  - 退货
  - 换货
  - 投诉
  - 售后
  - 问题
tools:
  - validate_return_policy
  - create_return_request
  - check_order_eligibility
  - query_knowledge_base
```

**数据流**：

```
用户输入
  ↓
[Intent Classification] - 分类（退货/换货/投诉/咨询）
  ↓
[Policy Check] - 检查退换货政策（规则引擎）
  ↓
[Eligibility Check] - 检查订单是否符合条件
  ↓
[Case Handling]
  ├─ 退货: 创建退货单
  ├─ 换货: 创建换货单
  ├─ 投诉: 创建工单
  └─ 咨询: 查询知识库
  ↓
[Response Generation]
  ↓
返回结果
```

**多轮对话设计**：

```python
# 第一轮
用户: "我想退货"
Agent: "好的，请问您要退哪个订单？"

# 第二轮
用户: "订单 2024022812345"
Agent: "该订单购买于7天内，符合退货条件。退货原因是什么？"

# 第三轮
用户: "质量有问题"
Agent: "已为您创建退货单，单号 RT001。请将商品寄回..."
```

**Skill 链编排**：

```yaml
plan:
  - step: classify_intent
    skill: intent_classifier
  - step: check_eligibility
    skill: eligibility_checker
    depends_on: classify_intent
  - step: handle_case
    skill: case_handler
    depends_on: check_eligibility
  - step: generate_response
    skill: response_generator
    depends_on: handle_case
```

---

## 接入流程设计

### 流程概览

```
┌─────────────────────────────────────────────────────────┐
│                    1. 注册与准备                           │
│  - 注册账号/创建租户                                      │
│  - 获取 API Key                                         │
│  - 选择定价计划                                          │
└─────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────┐
│                    2. 环境配置                            │
│  - 安装 SDK / 配置 API                                   │
│  - 配置 LLM Provider                                     │
│  - 设置 Token 预算                                       │
└─────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────┐
│                    3. Skill 选择/开发                     │
│  - 从 Skill 市场选择                                     │
│  - 或自定义开发 Skill                                    │
│  - 配置 Skill 参数                                       │
└─────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────┐
│                    4. 数据源配置                          │
│  - 配置数据库连接                                         │
│  - 配置 API 集成                                         │
│  - 测试连接                                             │
└─────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────┐
│                    5. Agent 创建与测试                    │
│  - 创建 Agent 实例                                       │
│  - 绑定 Skills                                          │
│  - 本地测试                                             │
└─────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────┐
│                    6. 部署上线                            │
│  - 部署到生产环境                                         │
│  - 配置监控告警                                          │
│  - 开始接收请求                                          │
└─────────────────────────────────────────────────────────┘
```

### 快速接入示例（5分钟）

**步骤 1: 安装 SDK**

```bash
pip install agent-skills-framework
```

**步骤 2: 初始化**

```python
from agent_skills import Client

# 初始化客户端
client = Client(
    api_key="your-api-key",
    tenant_id="your-tenant-id"
)
```

**步骤 3: 创建 Agent**

```python
# 创建 Agent
agent = client.create_agent(
    name="order-assistant",
    description="电商订单助手",
    skills=["order_query", "order_status", "refund_check"]
)
```

**步骤 4: 调用**

```python
# 发送请求
response = agent.process("帮我查一下订单 2024022812345")

print(response.text)
# 输出: 您的订单 2024022812345 已发货，预计 3月1日 送达。
```

### 企业级接入（完整）

**步骤 1: 私有化部署**

```bash
# 使用 Docker 部署
docker run -d \
  -p 8080:8080 \
  -e LICENSE_KEY=your-license \
  -v ./data:/app/data \
  agent-skills/framework:latest
```

**步骤 2: 配置租户和用户**

```python
from agent_skills.admin import AdminClient

admin = AdminClient(master_key="your-master-key")

# 创建租户
tenant = admin.create_tenant(
    name="acme-corp",
    plan="enterprise",
    token_budget=1000000
)

# 创建用户
user = admin.create_user(
    tenant_id=tenant.id,
    name="developer",
    role="admin"
)
```

**步骤 3: 配置数据源**

```python
# 配置数据库连接
agent.add_data_source(
    type="postgresql",
    name="order_db",
    connection_string="postgresql://user:pass@host:5432/db"
)

# 配置 API
agent.add_data_source(
    type="http",
    name="payment_api",
    base_url="https://api.payment.com",
    auth={"type": "bearer", "token": "xxx"}
)
```

**步骤 4: 开发自定义 Skill**

```bash
# 使用 CLI 工具创建 Skill
asf skill create my_skill --template advanced
```

```python
# skills/my_skill/executor.py
def execute(llm, sub_task, context):
    # 调用数据源
    order_db = context.get_data_source("order_db")
    order = order_db.query_order(order_id="xxx")

    # 规则处理
    status = calculate_status(order)

    # LLM 生成
    text = llm.invoke(f"生成状态说明: {status}")

    return {"structured": status, "text": text}
```

**步骤 5: 部署和监控**

```python
# 配置监控
agent.configure_monitoring(
    alert_webhook="https://your-webhook.com/alerts",
    token_budget_alert=0.8,
    error_rate_alert=0.05
)

# 启用审计日志
agent.enable_audit_log(retention_days=90)
```

---

## 技术架构约束

### 当前架构优势

基于设计文档分析，当前框架具备以下优势：

1. **高效性**
   - 单 Agent 编排，通信成本低
   - 渐进式披露，Token 线性增长
   - 双执行引擎，确定性计算用规则

2. **可扩展性**
   - 即插即用 Skills
   - LLM Provider 抽象
   - Tool 系统扩展点

3. **可维护性**
   - 全链路审计
   - 三层上下文清晰分离
   - 组件职责明确

### 需要架构调整的点

| 需求 | 当前状态 | 调整建议 | 优先级 |
|------|----------|----------|--------|
| 多租户隔离 | 不支持 | 新增 TenantContext、租户级 SkillRegistry | P0 |
| REST API | 不支持 | 新增 API Server 模块 | P0 |
| 数据源连接 | Tool 机制可用 | 标准化 Connector 接口 | P0 |
| 异步执行 | 不支持 | 引入 asyncio 支持 | P1 |
| 监控告警 | 审计日志存在 | 新增 Metrics、Alerting 模块 | P1 |
| Skill 市场 | 不支持 | Phase 2 功能 | P2 |
| 多语言 SDK | 仅 Python | JavaScript SDK | P2 |

---

## 成功指标

### 产品指标

| 指标 | 目标 | 测量方式 |
|------|------|----------|
| 月活跃用户 (MAU) | 1000+ (6个月) | 注册用户活跃统计 |
| 企业租户数 | 50+ (6个月) | 付费企业数 |
| API 调用次数 | 100万+/月 | API 调用统计 |
| 平均响应时间 | <2s | 性能监控 |
| 系统可用性 | >99.5% | 监控统计 |
| Skill 复用率 | >70% | Skill 使用统计 |

### 开发者体验指标

| 指标 | 目标 | 测量方式 |
|------|------|----------|
| 5分钟接入成功率 | >90% | 埋点统计 |
| 文档覆盖度 | 100% | 文档完整性检查 |
| Issue 响应时间 | <24h | GitHub Issues |
| 社区贡献 | 10+ Skills/月 | Skill 市场 |

### 商业指标

| 指标 | 目标 | 测量方式 |
|------|------|----------|
| 付费转化率 | >10% | 注册→付费转化 |
| 客户留存率 | >80% (3个月) | 订阅续费率 |
| 客户满意度 (NPS) | >50 | 用户调研 |
| 平均客单价 | >$500/月 | 订单统计 |

---

## 路线图

### Phase 1: 框架核心（当前 - 已完成）

- [x] 单 Agent 编排系统
- [x] 三层上下文
- [x] 双执行引擎
- [x] 基础 Skills 示例
- [x] 多 LLM Provider 支持

### Phase 2: 企业级能力 (Q2 2026)

- [ ] 多租户隔离
- [ ] REST API 服务
- [ ] 数据源连接器
- [ ] 基础监控和告警
- [ ] 电商场景 Demo

### Phase 3: 生态建设 (Q3 2026)

- [ ] Skill 市场（MVP）
- [ ] CLI 工具完善
- [ ] JavaScript SDK
- [ ] 更多行业模板
- [ ] 社区门户

### Phase 4: 高级特性 (Q4 2026)

- [ ] 多轮对话管理
- [ ] 流式输出优化
- [ ] 分布式部署
- [ ] 自定义执行策略
- [ ] 插件系统

---

## 附录

### A. 术语表

| 术语 | 定义 |
|------|------|
| Agent | 智能体，具有目标导向能力的 AI 系统 |
| Skill | 技能，Agent 具备的特定能力模块 |
| Coordinator | 协调器，统一调度整个执行流程 |
| Context | 上下文，执行过程中的状态数据 |
| Tenant | 租户，框架的使用单位（企业/团队） |
| Tool | 工具，Skill 可调用的底层功能 |
| Progressive Disclosure | 渐进式披露，逐步释放上下文的策略 |

### B. 参考资料

- 设计文档: `docs/plans/2025-02-28-agent-skills-framework-design.md`
- 快速开始: `docs/QUICK_START_GUIDE.md`
- 教程: `TUTORIAL.md`
- 原文章: [别急着上 Multi-Agent，也许「Agent Skills」会更好](https://mp.weixin.qq.com/s/_uoHjcMbVlx9PrUXRF6Efg)

---

**文档版本**: 1.0.0
**最后更新**: 2026-02-28
**下一步**: 与架构师确认技术可行性，输出详细技术方案
