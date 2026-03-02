# Agent Skills Framework - 数据连接器使用指南

**版本**: 1.0.0
**日期**: 2026-03-02
**作者**: AI开发工程师

---

## 目录

1. [概述](#概述)
2. [快速开始](#快速开始)
3. [数据库连接器](#数据库连接器)
4. [HTTP连接器](#http连接器)
5. [最佳实践](#最佳实践)
6. [故障排除](#故障排除)

---

## 概述

Agent Skills Framework 的数据连接器系统提供了统一的方式来连接各种数据源，包括关系型数据库、NoSQL数据库和REST API。

### 支持的连接器类型

| 连接器类型 | 状态 | 适用场景 |
|-----------|------|---------|
| PostgreSQL | ✅ 可用 | 关系型数据存储 |
| MySQL | ✅ 可用 | 关系型数据存储 |
| MongoDB | ✅ 可用 | 文档型数据存储 |
| HTTP/REST | ✅ 可用 | 第三方API集成 |
| Redis | 🔄 计划中 | 缓存和消息队列 |
| Kafka | 🔄 计划中 | 流式数据处理 |

### 核心特性

- **连接池管理**: 自动管理数据库连接池
- **健康检查**: 内置连接健康检查和自动重连
- **异步支持**: 基于 asyncio 的高性能异步操作
- **统一接口**: 所有连接器遵循相同的接口规范
- **统计监控**: 内置连接使用统计和性能指标

---

## 快速开始

### 1. 安装依赖

```bash
# 安装核心依赖
pip install -r requirements.txt

# 安装特定数据库驱动（根据需要选择）
pip install asyncpg  # PostgreSQL
pip install aiomysql  # MySQL
pip install motor  # MongoDB
pip install aiohttp  # HTTP
```

### 2. 配置连接器

创建配置文件 `config/connectors.yaml`:

```yaml
# 连接器配置
data_sources:
  # PostgreSQL 示例
  order_db:
    type: postgresql
    connection_string: "${ORDER_DB_URL}"
    pool_size: 10
    timeout: 30
    health_check:
      interval: 30s
      query: "SELECT 1"

  # HTTP API 示例
  payment_api:
    type: http
    base_url: "https://api.payment.com/v1"
    auth:
      type: bearer
      token: "${PAYMENT_API_TOKEN}"
    retry:
      max_retries: 3
      backoff: exponential
```

### 3. 使用连接器

```python
import asyncio
from connectors.registry import ConnectorRegistry

async def main():
    # 获取连接器注册表实例
    registry = ConnectorRegistry.get_instance()

    # 获取已注册的连接器
    order_db = registry.get_connector("order_db")

    # 执行查询
    result = await order_db.fetch_one(
        "SELECT * FROM orders WHERE order_id = :order_id",
        {"order_id": "12345"}
    )

    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 数据库连接器

### PostgreSQL 连接器

#### 配置示例

```yaml
data_sources:
  user_db:
    type: postgresql
    connection_string: "postgresql://user:password@localhost:5432/mydb"
    pool_size: 10
    max_overflow: 20
    pool_timeout: 30
    echo: false  # 是否打印SQL语句
```

#### 环境变量方式

```yaml
data_sources:
  user_db:
    type: postgresql
    connection_string: "${DATABASE_URL}"
    pool_size: "${DB_POOL_SIZE:10}"  # 默认值10
```

#### 使用示例

```python
from connectors.database import PostgreSQLConnector

async def query_users():
    # 方式1: 使用连接字符串
    connector = PostgreSQLConnector(
        connection_string="postgresql://user:pass@localhost/db"
    )

    # 方式2: 使用配置字典
    config = {
        "host": "localhost",
        "port": 5432,
        "database": "mydb",
        "user": "myuser",
        "password": "mypassword"
    }
    connector = PostgreSQLConnector(**config)

    await connector.connect()

    try:
        # 查询单条记录
        user = await connector.fetch_one(
            "SELECT * FROM users WHERE id = :id",
            {"id": 1}
        )

        # 查询多条记录
        users = await connector.fetch_many(
            "SELECT * FROM users WHERE status = :status",
            {"status": "active"},
            limit=100
        )

        # 执行INSERT
        new_id = await connector.execute(
            """
            INSERT INTO users (name, email)
            VALUES (:name, :email)
            RETURNING id
            """,
            {"name": "John", "email": "john@example.com"}
        )

        # 事务支持
        async with connector.transaction():
            await connector.execute(
                "UPDATE accounts SET balance = balance - :amount WHERE id = :id",
                {"amount": 100, "id": 1}
            )
            await connector.execute(
                "UPDATE accounts SET balance = balance + :amount WHERE id = :id",
                {"amount": 100, "id": 2}
            )

        return users

    finally:
        await connector.disconnect()
```

### MySQL 连接器

#### 配置示例

```yaml
data_sources:
  product_db:
    type: mysql
    connection_string: "mysql+pymysql://user:password@localhost:3306/products"
    pool_size: 10
    timeout: 30
```

#### 使用示例

```python
from connectors.database import MySQLConnector

async def query_products():
    connector = MySQLConnector(
        connection_string="mysql://user:pass@localhost/products"
    )

    await connector.connect()

    products = await connector.fetch_many(
        "SELECT * FROM products WHERE category = %s",
        ("electronics",),
        limit=50
    )

    await connector.disconnect()
    return products
```

### MongoDB 连接器

#### 配置示例

```yaml
data_sources:
  log_db:
    type: mongodb
    connection_string: "${MONGODB_URL}"
    database: logs
    pool_size: 5
```

#### 使用示例

```python
from connectors.database import MongoDBConnector

async def query_logs():
    connector = MongoDBConnector(
        connection_string="mongodb://localhost:27017",
        database="logs"
    )

    await connector.connect()

    # 插入文档
    await connector.insert_one(
        "events",
        {
            "level": "error",
            "message": "Connection failed",
            "timestamp": datetime.utcnow(),
            "metadata": {"service": "payment-api"}
        }
    )

    # 查询文档
    logs = await connector.find_many(
        "events",
        filter={"level": "error"},
        sort={"timestamp": -1},
        limit=100
    )

    await connector.disconnect()
    return logs
```

---

## HTTP连接器

### REST API连接器

#### 配置示例

```yaml
data_sources:
  payment_api:
    type: http
    base_url: "https://api.payment.com/v1"
    auth:
      type: bearer
      token: "${PAYMENT_API_TOKEN}"
    timeout: 30
    retry:
      max_retries: 3
      backoff: exponential
      initial_delay: 1.0
      max_delay: 30.0
    headers:
      Content-Type: "application/json"
      X-API-Version: "v1"
```

#### API Key认证方式

```yaml
data_sources:
  logistics_api:
    type: http
    base_url: "https://api.logistics.com"
    auth:
      type: api_key
      key_header: X-API-Key
      key_value: "${LOGISTICS_API_KEY}"
```

#### 使用示例

```python
from connectors.http import HTTPAPIConnector

async def process_payment():
    # 方式1: 使用配置字典
    config = {
        "base_url": "https://api.payment.com/v1",
        "auth": {
            "type": "bearer",
            "token": "your-api-token"
        }
    }
    connector = HTTPAPIConnector(**config)

    # 方式2: 从注册表获取
    from connectors.registry import ConnectorRegistry
    registry = ConnectorRegistry.get_instance()
    connector = registry.get_connector("payment_api")

    await connector.connect()

    try:
        # GET请求
        user = await connector.get(
            "/users/123",
            headers={"X-Request-ID": "uuid-123"}
        )

        # POST请求
        payment = await connector.post(
            "/payments",
            data={
                "amount": 100.00,
                "currency": "USD",
                "customer_id": "cust_123",
                "payment_method": "card"
            },
            headers={"Idempotency-Key": "unique-key-123"}
        )

        # PUT请求
        update = await connector.put(
            "/orders/123",
            data={
                "status": "shipped",
                "tracking_number": "TRACK123"
            }
        )

        # DELETE请求
        delete = await connector.delete(
            "/carts/123"
        )

        # 带查询参数的GET
        orders = await connector.get(
            "/orders",
            params={
                "status": "pending",
                "page": 1,
                "limit": 50
            }
        )

        return payment

    except Exception as e:
        # 连接器会自动重试，但如果仍然失败会抛出异常
        print(f"API调用失败: {e}")
        raise
    finally:
        await connector.disconnect()
```

### 高级功能

#### 文件上传

```python
# 上传文件
with open("document.pdf", "rb") as f:
    result = await connector.post(
        "/documents",
        files={"file": ("document.pdf", f, "application/pdf")},
        data={"category": "invoice"}
    )
```

#### 流式响应处理

```python
# 处理大文件下载
response = await connector.get(
    "/files/large-file.zip",
    stream=True
)

async for chunk in response.iter_content(chunk_size=8192):
    # 处理每个数据块
    process_chunk(chunk)
```

---

## 最佳实践

### 1. 配置管理

**使用环境变量存储敏感信息**

```yaml
# config/connectors.yaml
data_sources:
  production_db:
    type: postgresql
    connection_string: "${DATABASE_URL}"
    pool_size: "${DB_POOL_SIZE:10}"
```

```bash
# .env 文件（不提交到版本控制）
DATABASE_URL=postgresql://user:password@localhost:5432/mydb
DB_POOL_SIZE=20
```

### 2. 连接池配置

**根据负载调整连接池**

```yaml
data_sources:
  high_traffic_db:
    type: postgresql
    connection_string: "${DATABASE_URL}"
    # 高并发场景
    pool_size: 20
    max_overflow: 40
    pool_timeout: 60
    # 连接回收
    pool_recycle: 3600
```

### 3. 错误处理策略

```python
from connectors.base import ConnectionError, QueryError

async def safe_query():
    connector = await get_connector()

    try:
        result = await connector.fetch_one("SELECT * FROM users WHERE id = :id", {"id": 1})
        return result
    except ConnectionError as e:
        # 连接错误，可能是网络问题或数据库宕机
        logger.error(f"数据库连接失败: {e}")
        # 可以在这里实现重试逻辑或切换到备用数据库
        raise ServiceUnavailable("数据库暂时不可用，请稍后重试")
    except QueryError as e:
        # 查询错误，可能是SQL语法错误或数据问题
        logger.error(f"查询执行失败: {e}")
        raise BadRequest(f"查询参数错误: {e}")
    except Exception as e:
        # 其他未预期的错误
        logger.exception(f"未知错误: {e}")
        raise
```

### 4. 监控和日志

```python
import logging
from connectors.registry import ConnectorRegistry

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 监控连接器状态
async def monitor_connectors():
    registry = ConnectorRegistry.get_instance()
    stats = registry.get_statistics()

    for name, connector_stats in stats.items():
        logger.info(f"连接器 {name} 统计:")
        logger.info(f"  - 总查询数: {connector_stats['total_queries']}")
        logger.info(f"  - 活动连接: {connector_stats['active_connections']}")
        logger.info(f"  - 平均响应时间: {connector_stats['avg_response_time']}ms")

        # 健康检查
        connector = registry.get_connector(name)
        health = await connector.health_check()
        if health['status'] != 'healthy':
            logger.warning(f"连接器 {name} 健康检查失败: {health}")
```

---

## 故障排除

### 常见问题

#### 1. 连接超时

**问题**: `ConnectionTimeout: Failed to connect to database`

**解决方案**:
- 检查网络连接
- 增加 `timeout` 配置
- 检查数据库服务器状态
- 确认防火墙规则

```yaml
data_sources:
  my_db:
    type: postgresql
    connection_string: "postgresql://user:pass@host/db"
    timeout: 60  # 增加超时时间
    retry:
      max_retries: 3
      backoff: exponential
```

#### 2. 连接池耗尽

**问题**: `PoolExhausted: No available connections in pool`

**解决方案**:
- 增加 `pool_size`
- 检查是否有连接未正确释放
- 优化查询性能

```yaml
data_sources:
  my_db:
    type: postgresql
    connection_string: "${DATABASE_URL}"
    pool_size: 20
    max_overflow: 40
```

#### 3. API认证失败

**问题**: `AuthenticationError: Invalid API key`

**解决方案**:
- 检查API key是否正确
- 确认认证方式
- 检查token是否过期

```python
# 使用环境变量存储敏感信息
import os

config = {
    "type": "http",
    "base_url": "https://api.example.com",
    "auth": {
        "type": "bearer",
        "token": os.getenv("API_TOKEN")  # 从环境变量读取
    }
}
```

---

## 参考资源

- [API文档](./api-reference.md)
- [示例代码](../examples/connector-examples/)
- [故障排除指南](./troubleshooting.md)
- [性能优化指南](./performance-tuning.md)

---

**最后更新**: 2026-03-02
**文档版本**: 1.0.0