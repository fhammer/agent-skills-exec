# 通用智能体开发框架 - 扩展指南

**版本**: 1.0.0
**日期**: 2026-03-10
**作者**: AI架构师
**状态**: 设计完成

---

## 目录

1. [概述](#概述)
2. [如何开发新的Skill](#如何开发新的skill)
3. [如何集成到业务系统](#如何集成到业务系统)
4. [配置说明](#配置说明)
5. [最佳实践](#最佳实践)
6. [常见问题](#常见问题)

---

## 概述

本指南帮助开发者：
- 开发自定义Skill扩展框架能力
- 将框架集成到现有业务系统
- 遵循最佳实践确保代码质量

### 扩展类型

| 扩展类型 | 说明 | 复杂度 |
|----------|------|--------|
| **Skill** | 自定义业务逻辑Skill | 中 |
| **Connector** | 自定义数据连接器 | 中 |
| **Tool** | 自定义工具函数 | 低 |
| **Middleware** | 自定义中间件 | 高 |

---

## 如何开发新的Skill

### 开发流程

```
1. 确定Skill功能 → 2. 选择执行模式 → 3. 实现Skill → 4. 测试验证 → 5. 部署注册
```

### 模式1: Executor模式 (Python代码)

适用于：复杂业务逻辑、需要外部API调用、数据验证转换

```python
# skills/product_search/executor.py
from agent.core.base_skill import BaseSkill, SkillExecutionContext, SkillExecutionResult
from agent.core.interfaces import ValidationResult
from typing import Dict, Any, List
import asyncio

class ProductSearchSkill(BaseSkill):
    """商品搜索Skill"""

    # Skill元数据
    name = "product_search"
    version = "1.0.0"
    description = "根据用户需求搜索商品"
    triggers = ["搜索", "查找", "推荐"]
    tags = ["ecommerce", "search"]

    def __init__(self):
        super().__init__()
        self.product_db = None  # 将在initialize中初始化

    async def initialize(self, config: Dict[str, Any]):
        """初始化Skill"""
        # 初始化数据库连接
        from agent.connectors.database import DatabaseConnector
        self.product_db = DatabaseConnector(config["database"])
        await self.product_db.connect()

    async def validate_input(self, input_data: Dict[str, Any]) -> ValidationResult:
        """验证输入数据"""
        errors = []

        # 检查必需的参数
        if "category" not in input_data:
            errors.append("缺少必需的参数: category")

        # 检查参数类型
        if "max_price" in input_data and not isinstance(input_data["max_price"], (int, float)):
            errors.append("max_price必须是数字类型")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )

    async def execute(self, context: SkillExecutionContext) -> SkillExecutionResult:
        """执行搜索逻辑"""
        try:
            # 构建查询条件
            query = self._build_query(context.input_data)

            # 执行数据库查询
            products = await self.product_db.execute(query)

            # 处理结果
            results = self._process_results(products, context.input_data)

            return SkillExecutionResult(
                success=True,
                output_data={
                    "products": results,
                    "total_count": len(results),
                    "search_params": context.input_data
                }
            )

        except Exception as e:
            return SkillExecutionResult(
                success=False,
                error=e,
                error_message=f"搜索商品时出错: {str(e)}"
            )

    async def validate_output(self, output_data: Dict[str, Any]) -> ValidationResult:
        """验证输出数据"""
        errors = []

        if "products" not in output_data:
            errors.append("输出缺少products字段")
        elif not isinstance(output_data["products"], list):
            errors.append("products必须是列表类型")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )

    def _build_query(self, params: Dict[str, Any]) -> str:
        """构建数据库查询"""
        conditions = ["category = $1"]
        values = [params["category"]]

        if "max_price" in params:
            conditions.append(f"price <= ${len(values) + 1}")
            values.append(params["max_price"])

        where_clause = " AND ".join(conditions)
        return f"SELECT * FROM products WHERE {where_clause} LIMIT 50"

    def _process_results(self, products: List[Dict], params: Dict[str, Any]) -> List[Dict]:
        """处理查询结果"""
        # 排序逻辑
        if "sort_by" in params:
            reverse = params.get("sort_order", "asc") == "desc"
            products = sorted(
                products,
                key=lambda x: x.get(params["sort_by"], 0),
                reverse=reverse
            )

        return products


# SKILL.md 文件
"""
---
name: product_search
version: 1.0.0
description: 根据用户需求搜索商品
triggers:
  - 搜索
  - 查找
  - 推荐
tags:
  - ecommerce
  - search
input_schema:
  type: object
  properties:
    category:
      type: string
      description: 商品类别
    max_price:
      type: number
      description: 最高价格
    sort_by:
      type: string
      description: 排序字段
    sort_order:
      type: string
      enum: [asc, desc]
      description: 排序顺序
  required:
    - category
output_schema:
  type: object
  properties:
    products:
      type: array
      items:
        type: object
    total_count:
      type: integer
---

# 商品搜索Skill

## 功能说明

根据用户提供的搜索条件，从商品数据库中查询匹配的商品。

## 使用示例

```python
result = await skill_registry.execute_skill("product_search", {
    "category": "手机",
    "max_price": 5000,
    "sort_by": "price",
    "sort_order": "asc"
})
```

## 注意事项

- 必须提供category参数
- 搜索结果最多返回50条
- 支持按价格、评分等字段排序
"""
```

### 模式2: Template模式 (LLM模板)

适用于：标准LLM任务、格式转换、文本生成

```yaml
# skills/text_summary/prompt.template
---
system: |
  你是一个专业的文本摘要助手。
  你的任务是将用户提供的文本进行摘要，提取关键信息。

  要求：
  1. 摘要长度不超过原文的30%
  2. 保留关键数据和事实
  3. 使用简洁的语言
  4. 保持客观中立

user: |
  请对以下文本进行摘要：

  {{text}}

expected_output: |
  摘要：
  {{summary}}

  关键要点：
  {{key_points}}

examples:
  - input:
      text: "..."
    output:
      summary: "..."
      key_points:
        - "..."
        - "..."
---
```

### 模式3: Document模式 (文档即Skill)

适用于：简单问答、快速原型、文档驱动

```markdown
# skills/faq/SKILL.md

---
name: faq
version: 1.0.0
description: 常见问题解答
triggers:
  - 问题
  - 帮助
  - FAQ
---

# FAQ Skill

## 功能

回答用户关于产品的常见问题。

## 知识库

### 问题1: 如何重置密码？

**回答**:
1. 访问登录页面
2. 点击"忘记密码"
3. 输入注册邮箱
4. 查收重置链接
5. 设置新密码

### 问题2: 支持哪些支付方式？

**回答**:
- 支付宝
- 微信支付
- 银行卡
- PayPal

### 问题3: 如何联系客服？

**回答**:
- 在线客服: 工作日 9:00-18:00
- 电话: 400-xxx-xxxx
- 邮箱: support@example.com
```

---

## 如何集成到业务系统

### 集成流程

```
1. 确定集成方式 → 2. 配置数据连接器 → 3. 开发业务Skill → 4. 配置场景 → 5. 测试部署
```

### 集成方式

#### 方式1: REST API调用

适用于：前端应用、移动端、第三方系统

```python
import requests

# 调用Agent API
response = requests.post(
    "http://localhost:8000/api/v1/agent/chat",
    headers={"Authorization": "Bearer YOUR_API_KEY"},
    json={
        "session_id": "user_123_session",
        "user_id": "user_123",
        "message": "我想买一部手机，预算3000以内",
        "context": {
            "tenant_id": "tenant_001",
            "scene_id": "smart_shopping"
        }
    }
)

result = response.json()
print(result["response"])
```

#### 方式2: Python SDK

适用于：Python后端服务

```python
from agent_framework import Agent, SkillRegistry
from agent_framework.config import CoordinatorConfig

# 初始化配置
config = CoordinatorConfig.from_file("config.yaml")

# 创建Agent实例
agent = Agent(config)

# 处理用户请求
async def handle_user_request(user_input: str, user_id: str):
    result = await agent.process(
        user_input=user_input,
        user_id=user_id,
        tenant_id="tenant_001",
        scene_id="customer_service"
    )
    return result.response
```

#### 方式3: Webhook事件

适用于：异步通知、事件驱动

```python
from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/webhook/agent-events")
async def handle_agent_events(request: Request):
    event = await request.json()

    # 处理不同类型的事件
    if event["type"] == "skill.completed":
        # Skill执行完成
        await handle_skill_completed(event["data"])
    elif event["type"] == "token.budget.low":
        # Token预算告警
        await handle_budget_alert(event["data"])
    elif event["type"] == "error.occurred":
        # 错误发生
        await handle_error(event["data"])

    return {"status": "ok"}
```

### 配置说明

#### 基础配置 (config.yaml)

```yaml
# 基础配置
app:
  name: "通用智能体开发框架"
  version: "1.0.0"
  debug: false

# LLM配置
llm:
  provider: "anthropic"  # 可选: openai, anthropic, zhipu, ollama
  model: "glm-4.7"
  temperature: 0.7
  max_tokens: 4096
  api_key: "${LLM_API_KEY}"
  base_url: "${LLM_BASE_URL}"

# 框架核心配置
coordinator:
  max_iterations: 10
  enable_replanning: true
  replan_threshold: 0.5

# 上下文管理
context:
  max_layer1_size: 10000  # bytes
  max_layer2_size: 50000  # bytes
  max_layer3_size: 10000  # bytes
  enable_audit_log: true

# Skill注册表
skill_registry:
  skills_dir: "./skills"
  enable_health_check: true
  health_check_interval: 30  # seconds
  enable_hot_reload: true

# 数据连接器
connectors:
  - name: "product_db"
    type: "postgresql"
    connection_string: "${PRODUCT_DB_URL}"
    pool_size: 20
    timeout: 30
    health_check:
      interval: 30s
      query: "SELECT 1"

  - name: "order_api"
    type: "http"
    base_url: "https://api.orders.com/v1"
    auth:
      type: "bearer"
      token: "${ORDER_API_TOKEN}"
    retry:
      max_retries: 3
      backoff: "exponential"

# API服务
api:
  host: "0.0.0.0"
  port: 8000
  workers: 4
  cors:
    enabled: true
    origins: ["*"]
  auth:
    type: "jwt"
    secret: "${JWT_SECRET}"
    token_expire: 86400  # 24 hours
  rate_limit:
    enabled: true
    requests_per_minute: 60

# 监控与日志
observability:
  metrics:
    enabled: true
    exporter: "prometheus"
    port: 9090
  logging:
    level: "info"
    format: "json"
    output: "stdout"
  tracing:
    enabled: true
    exporter: "jaeger"
    jaeger_endpoint: "${JAEGER_ENDPOINT}"
```

#### 多租户配置 (tenant.yaml)

```yaml
# 多租户配置示例
tenants:
  # 平台级配置
  platform:
    tenant_id: "platform"
    name: "平台管理"
    config:
      llm_provider: "anthropic"
      llm_model: "glm-4.7"
      token_budget: 10000000

  # 品牌租户：小米
  xiaomi:
    tenant_id: "brand_xiaomi"
    name: "小米官方旗舰店"
    parent_tenant: "platform"
    config:
      llm_model: "glm-4.7"
      token_budget: 2000000
    scenes:
      smart_shopping:
        name: "智能导购"
        skills: ["demand_analysis", "product_search", "recommendation_ranking"]
        data_sources: ["xiaomi_products", "user_profiles"]
      after_sales:
        name: "售后客服"
        skills: ["order_query", "policy_validation", "case_creation"]
        data_sources: ["xiaomi_orders", "service_cases"]

  # 品牌租户：华为
  huawei:
    tenant_id: "brand_huawei"
    name: "华为官方旗舰店"
    parent_tenant: "platform"
    config:
      token_budget: 1500000
    scenes:
      smart_shopping:
        name: "智能导购"
        skills: ["demand_analysis", "product_search", "recommendation_ranking"]
        data_sources: ["huawei_products", "user_profiles"]
```

---

## 最佳实践

### 1. Skill开发最佳实践

#### DO ✅

```python
# 1. 明确的输入输出定义
class MySkill(BaseSkill):
    input_schema = {
        "type": "object",
        "properties": {
            "user_id": {"type": "string"},
            "query": {"type": "string", "minLength": 1}
        },
        "required": ["user_id", "query"]
    }

# 2. 完善的错误处理
async def execute(self, context):
    try:
        result = await self._do_work(context)
        return SkillExecutionResult(success=True, output=result)
    except ValidationError as e:
        return SkillExecutionResult(
            success=False,
            error=e,
            error_type="VALIDATION_ERROR"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return SkillExecutionResult(
            success=False,
            error=e,
            error_type="INTERNAL_ERROR"
        )

# 3. 使用连接池管理资源
async def initialize(self, config):
    self.db = DatabaseConnector(config["db"])
    await self.db.connect()  # 连接池自动管理

async def shutdown(self):
    if self.db:
        await self.db.disconnect()
```

#### DON'T ❌

```python
# 1. 不要硬编码配置
class BadSkill(BaseSkill):
    def __init__(self):
        self.api_key = "hardcoded-key"  # ❌ 安全风险
        self.db_url = "postgres://..."  # ❌ 不灵活

# 2. 不要忽略错误
async def execute(self, context):
    result = await some_operation()  # ❌ 没有try-catch
    return result  # ❌ 没有错误处理

# 3. 不要创建大量连接
async def execute(self, context):
    for i in range(100):
        db = DatabaseConnector()  # ❌ 每次创建新连接
        await db.connect()
        result = await db.query(...)
        await db.disconnect()
```

### 2. 业务系统集成最佳实践

#### API设计原则

```python
# 1. 版本控制
@app.get("/api/v1/products")  # ✅ 带版本
async def list_products():
    pass

# 2. 统一响应格式
{
    "success": True,
    "data": {...},
    "meta": {
        "page": 1,
        "per_page": 20,
        "total": 100
    }
}

# 3. 错误处理
{
    "success": False,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid input data",
        "details": {
            "price": ["Must be a positive number"]
        }
    }
}
```

#### 安全最佳实践

```python
# 1. 输入验证
from pydantic import BaseModel, validator

class ProductSearchRequest(BaseModel):
    category: str
    max_price: float = Field(gt=0)
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, le=100)

    @validator('category')
    def validate_category(cls, v):
        allowed = ['手机', '电脑', '服装', '食品']
        if v not in allowed:
            raise ValueError(f'不支持的类别: {v}')
        return v

# 2. SQL注入防护
# ✅ 使用参数化查询
query = "SELECT * FROM products WHERE category = $1 AND price <= $2"
results = await db.execute(query, [category, max_price])

# ❌ 不要拼接SQL
query = f"SELECT * FROM products WHERE category = '{category}'"  # 危险！

# 3. 敏感信息保护
# ✅ 使用环境变量
api_key = os.getenv("API_KEY")

# ✅ 日志脱敏
logger.info(f"User {user_id} searched for {category}")
# 不要记录: logger.info(f"Password: {password}")
```

### 3. 性能优化最佳实践

```python
# 1. 连接池管理
class DatabaseConnector:
    def __init__(self, config):
        self.pool = None
        self.config = config

    async def connect(self):
        # 创建连接池
        self.pool = await asyncpg.create_pool(
            dsn=self.config["dsn"],
            min_size=5,      # 最小连接数
            max_size=20,     # 最大连接数
            command_timeout=60,
            server_settings={
                'jit': 'off'
            }
        )

    async def execute(self, query, params=None):
        # 从连接池获取连接
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *(params or []))

# 2. 缓存策略
from functools import wraps
import aioredis

# 设置缓存
async def cache_result(key, value, ttl=3600):
    redis = await aioredis.create_redis_pool('redis://localhost')
    await redis.setex(key, ttl, json.dumps(value))
    redis.close()
    await redis.wait_closed()

# 获取缓存
async def get_cached_result(key):
    redis = await aioredis.create_redis_pool('redis://localhost')
    value = await redis.get(key)
    redis.close()
    await redis.wait_closed()
    return json.loads(value) if value else None

# 装饰器方式
def cache_result_decorator(ttl=3600):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存key
            cache_key = f"{func.__name__}:{hash(str(args))}:{hash(str(kwargs))}"

            # 尝试从缓存获取
            cached = await get_cached_result(cache_key)
            if cached is not None:
                return cached

            # 执行函数
            result = await func(*args, **kwargs)

            # 缓存结果
            await cache_result(cache_key, result, ttl)

            return result
        return wrapper
    return decorator

# 使用示例
@cache_result_decorator(ttl=1800)  # 缓存30分钟
async def search_products(category: str, filters: dict):
    # 耗时的查询操作
    results = await expensive_query(category, filters)
    return results

# 3. 异步批量处理
async def batch_process(items: List[Dict], batch_size: int = 100):
    """批量异步处理"""
    results = []

    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]

        # 并发处理批次
        batch_results = await asyncio.gather(*[
            process_item(item) for item in batch
        ], return_exceptions=True)

        results.extend(batch_results)

    return results

# 4. 数据库查询优化
# ✅ 使用索引
# 在category和price字段上创建复合索引
# CREATE INDEX idx_products_category_price ON products(category, price);

# ✅ 分页查询
async def paginated_query(
    category: str,
    page: int = 1,
    per_page: int = 20
):
    offset = (page - 1) * per_page

    # 查询数据
    data_query = """
        SELECT * FROM products
        WHERE category = $1
        ORDER BY created_at DESC
        LIMIT $2 OFFSET $3
    """
    results = await db.fetch(data_query, category, per_page, offset)

    # 查询总数
    count_query = """
        SELECT COUNT(*) FROM products
        WHERE category = $1
    """
    total = await db.fetchval(count_query, category)

    return {
        "data": results,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": (total + per_page - 1) // per_page
        }
    }
```

---

## 常见问题

### Q1: 如何选择Skill执行模式？

**A**: 根据任务复杂度选择：

| 场景 | 推荐模式 | 理由 |
|------|----------|------|
| 复杂业务逻辑 | Executor | 需要Python代码处理复杂逻辑 |
| 标准LLM任务 | Template | 快速开发，无需写代码 |
| 简单问答 | Document | 最低门槛，文档即Skill |

### Q2: 如何处理Skill之间的依赖？

**A**: 使用依赖声明和依赖注入：

```python
class MySkill(BaseSkill):
    dependencies = [
        {"name": "user_service", "version": ">=1.0.0"},
        {"name": "notification_service", "version": ">=2.0.0"}
    ]

    async def initialize(self, config, dependencies):
        # 通过依赖注入获取依赖服务
        self.user_service = dependencies["user_service"]
        self.notification_service = dependencies["notification_service"]
```

### Q3: 如何进行性能调优？

**A**: 参考性能优化最佳实践章节，主要策略：
1. 使用连接池管理数据库连接
2. 使用缓存减少重复计算
3. 使用异步批量处理
4. 优化数据库查询（索引、分页）

### Q4: 如何保证安全性？

**A**: 参考安全最佳实践章节，主要措施：
1. 输入验证和SQL注入防护
2. 使用环境变量管理敏感信息
3. 日志脱敏
4. 权限控制

---

**文档生成时间**: 2026-03-10
**版本**: 1.0.0
**状态**: 设计完成 ✅
