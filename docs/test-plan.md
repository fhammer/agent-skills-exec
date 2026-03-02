# Universal Agent Framework - 测试计划

**版本**: 1.0.0
**日期**: 2026-03-02
**状态**: 测试准备阶段
**作者**: AI 测试工程师

---

## 1. 测试概述

### 1.1 测试目标

本测试计划旨在全面验证通用智能体框架的功能完整性、性能指标、安全性和可靠性，确保框架满足以下目标：

1. **功能完整性**: 所有设计的功能按需求正确实现
2. **多租户隔离**: 不同租户的数据和配置完全隔离
3. **API稳定性**: REST API接口稳定可靠，错误处理完善
4. **性能达标**: 响应时间、并发能力满足设计指标
5. **安全性**: 认证鉴权、数据隔离、权限控制有效

### 1.2 测试范围

| 测试域 | 测试内容 | 优先级 |
|--------|----------|--------|
| **多租户管理** | 租户创建/删除/更新、配置继承、数据隔离 | P0 |
| **API服务** | 认证鉴权、请求响应、错误处理、限流熔断 | P0 |
| **智能体核心** | 对话管理、Skill执行、上下文管理 | P0 |
| **数据连接器** | 连接池、健康检查、故障恢复 | P1 |
| **电商Demo** | 智能导购、订单售后两个场景 | P1 |
| **性能测试** | 响应时间、并发能力、内存使用 | P1 |
| **安全测试** | 租户隔离、权限控制、注入攻击防护 | P1 |

### 1.3 测试类型

| 测试类型 | 描述 | 工具 |
|----------|------|------|
| **单元测试** | 模块级功能测试 | pytest |
| **集成测试** | 模块间协作测试 | pytest-asyncio |
| **端到端测试** | 完整场景测试 | httpx |
| **性能测试** | 响应时间、并发测试 | locust |
| **安全测试** | 安全漏洞扫描 | pytest-security |

---

## 2. 测试环境

### 2.1 环境配置

| 环境 | 用途 | 配置 |
|------|------|------|
| **开发环境** | 开发自测 | 本地Docker |
| **测试环境** | 正式测试 | 云服务器 |
| **预发布环境** | 上线前验证 | 生产配置 |
| **生产环境** | 线上运行 | 高可用集群 |

### 2.2 测试环境依赖

```yaml
# docker-compose.test.yml
version: '3.8'
services:
  # 数据库
  postgres_test:
    image: postgres:15
    environment:
      POSTGRES_DB: agent_framework_test
      POSTGRES_USER: test_user
      POSTGRES_PASSWORD: test_pass
    ports:
      - "5433:5432"

  # 缓存
  redis_test:
    image: redis:7
    ports:
      - "6380:6379"

  # 测试运行器
  test_runner:
    build: .
    environment:
      - DATABASE_URL=postgresql://test_user:test_pass@postgres_test:5432/agent_framework_test
      - REDIS_URL=redis://redis_test:6379
      - TEST_MODE=true
    volumes:
      - ./tests:/app/tests
      - ./reports:/app/reports
```

### 2.3 测试数据

```python
# tests/fixtures/test_data.py
TEST_TENANTS = [
    {"tenant_id": "tenant_001", "name": "测试租户1", "api_quota": 1000},
    {"tenant_id": "tenant_002", "name": "测试租户2", "api_quota": 500}
]

TEST_USERS = [
    {"user_id": "user_001", "tenant_id": "tenant_001", "name": "测试用户1"},
    {"user_id": "user_002", "tenant_id": "tenant_001", "name": "测试用户2"}
]

TEST_PRODUCTS = [
    {"product_id": "p_001", "name": "Redmi K70", "category": "手机", "price": 2499},
    {"product_id": "p_002", "name": "iQOO Neo9", "category": "手机", "price": 2299}
]

TEST_ORDERS = [
    {"order_id": "20240228123456", "user_id": "user_001", "status": "shipped"}
]
```

---

## 3. 测试用例设计

### 3.1 多租户管理测试

#### TC-TENANT-001: 创建租户
```python
async def test_create_tenant():
    """测试创建新租户"""
    tenant_data = {
        "name": "新租户",
        "api_quota": 1000,
        "config": {"model": "gpt-4"}
    }
    response = await client.post("/api/v1/tenants", json=tenant_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "新租户"
    assert "tenant_id" in data
```

#### TC-TENANT-002: 租户隔离
```python
async def test_tenant_isolation():
    """测试租户数据隔离"""
    # tenant1创建skill
    response1 = await client.post(
        "/api/v1/skills",
        json={"name": "skill1"},
        headers={"X-Tenant-ID": "tenant1"}
    )
    assert response1.status_code == 201

    # tenant2无法访问tenant1的skill
    response2 = await client.get(
        "/api/v1/skills/skill1",
        headers={"X-Tenant-ID": "tenant2"}
    )
    assert response2.status_code == 404
```

### 3.2 API服务测试

#### TC-API-001: 认证鉴权
```python
async def test_authentication():
    """测试API认证"""
    # 无API Key
    response = await client.post("/api/v1/agent/chat", json={})
    assert response.status_code == 401

    # 错误API Key
    response = await client.post(
        "/api/v1/agent/chat",
        json={},
        headers={"X-API-Key": "invalid_key"}
    )
    assert response.status_code == 401

    # 正确API Key
    response = await client.post(
        "/api/v1/agent/chat",
        json={"message": "hello"},
        headers={"X-API-Key": "valid_key"}
    )
    assert response.status_code == 200
```

#### TC-API-002: 限流熔断
```python
async def test_rate_limiting():
    """测试限流机制"""
    # 发送超过配额的请求
    responses = []
    for i in range(110):  # 配额100
        response = await client.post("/api/v1/agent/chat", json={})
        responses.append(response.status_code)

    # 前100个成功
    assert all(s == 200 for s in responses[:100])
    # 后10个被限流
    assert all(s == 429 for s in responses[100:])
```

### 3.3 智能体核心测试

#### TC-AGENT-001: 对话管理
```python
async def test_conversation():
    """测试多轮对话"""
    session_id = None

    # 第一轮
    response1 = await client.post("/api/v1/agent/chat", json={
        "message": "我想买个手机"
    })
    assert response1.status_code == 200
    session_id = response1.json()["session_id"]

    # 第二轮（带session_id）
    response2 = await client.post("/api/v1/agent/chat", json={
        "session_id": session_id,
        "message": "2000元左右"
    })
    assert response2.status_code == 200
    data = response2.json()
    assert "推荐" in data["response"]
```

#### TC-AGENT-002: Skill执行
```python
async def test_skill_execution():
    """测试Skill执行"""
    response = await client.post("/api/v1/agent/chat", json={
        "message": "帮我分析这个报告"
    })
    assert response.status_code == 200
    data = response.json()
    assert "audit_log" in data
    assert len(data["audit_log"]) > 0
```

### 3.4 电商Demo测试

#### TC-ECOM-001: 商品推荐
```python
async def test_product_recommendation():
    """测试商品推荐"""
    response = await client.post("/api/v1/recommendation/chat", json={
        "user_id": "user_123",
        "message": "我想买个2000元的手机"
    })
    assert response.status_code == 200
    data = response.json()
    assert "recommendations" in data
    assert len(data["recommendations"]) > 0
    assert all("price" in r for r in data["recommendations"])
```

#### TC-ECOM-002: 订单查询
```python
async def test_order_query():
    """测试订单查询"""
    response = await client.post("/api/v1/support/chat", json={
        "user_id": "user_123",
        "message": "查一下我的订单"
    })
    assert response.status_code == 200
    data = response.json()
    assert "orders" in data
```

#### TC-ECOM-003: 退货申请
```python
async def test_return_request():
    """测试退货申请"""
    response = await client.post("/api/v1/support/chat", json={
        "user_id": "user_123",
        "message": "订单20240228123456想退货"
    })
    assert response.status_code == 200
    data = response.json()
    assert "case_id" in data
```

---

## 4. 性能测试

### 4.1 性能指标

| 指标 | 目标值 | 测试方法 |
|------|--------|----------|
| **API响应时间** | P95 < 2s | 压力测试 |
| **并发能力** | 100 QPS | 负载测试 |
| **内存使用** | < 2GB | 监控测试 |
| **数据库连接** | 最多50个 | 连接池测试 |

### 4.2 性能测试脚本

```python
# tests/performance/test_load.py
from locust import HttpUser, task, between

class AgentUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        # 初始化：创建租户和用户
        response = self.client.post("/api/v1/tenants", json={
            "name": "perf_test_tenant"
        })
        self.tenant_id = response.json()["tenant_id"]
        self.api_key = response.json()["api_key"]

    @task(3)
    def chat(self):
        """对话接口"""
        self.client.post("/api/v1/agent/chat", json={
            "message": "你好"
        }, headers={"X-API-Key": self.api_key})

    @task(1)
    def get_skills(self):
        """获取技能列表"""
        self.client.get("/api/v1/skills",
                       headers={"X-API-Key": self.api_key})
```

---

## 5. 安全测试

### 5.1 安全测试用例

| 测试项 | 测试内容 | 预期结果 |
|--------|----------|----------|
| **SQL注入** | 在输入中注入SQL语句 | 被过滤或转义 |
| **XSS攻击** | 输入脚本标签 | 被过滤或转义 |
| **越权访问** | 访问其他租户数据 | 返回403 |
| **敏感信息泄露** | 检查响应中的敏感信息 | 不包含密码等 |
| **API滥用** | 高频请求 | 被限流 |

### 5.2 安全测试示例

```python
# tests/security/test_security.py
async def test_sql_injection():
    """测试SQL注入防护"""
    malicious_inputs = [
        "'; DROP TABLE users; --",
        "' OR '1'='1",
        "<script>alert('xss')</script>"
    ]
    for input in malicious_inputs:
        response = await client.post("/api/v1/agent/chat", json={
            "message": input
        })
        assert response.status_code == 200
        # 响应不应包含执行后的内容
        assert "DROP TABLE" not in response.text

async def test_cross_tenant_access():
    """测试跨租户访问"""
    # tenant1创建数据
    await client.post("/api/v1/skills", json={"name": "skill1"},
                     headers={"X-Tenant-ID": "tenant1"})

    # tenant2尝试访问
    response = await client.get("/api/v1/skills/skill1",
                               headers={"X-Tenant-ID": "tenant2"})
    assert response.status_code == 404  # 或403
```

---

## 6. 测试执行计划

### 6.1 测试阶段

| 阶段 | 内容 | 负责人 | 时间 |
|------|------|--------|------|
| **测试准备** | 环境搭建、测试数据准备 | 测试工程师 | D1-D2 |
| **单元测试** | 执行单元测试用例 | 开发+测试 | D3-D5 |
| **集成测试** | 执行集成测试用例 | 测试工程师 | D6-D8 |
| **E2E测试** | 执行端到端测试 | 测试工程师 | D9-D10 |
| **性能测试** | 执行性能测试 | 测试工程师 | D11-D12 |
| **安全测试** | 执行安全测试 | 测试工程师 | D13 |
| **回归测试** | 验证问题修复 | 测试工程师 | D14 |
| **测试报告** | 生成测试报告 | 测试工程师 | D15 |

### 6.2 测试准入/准出标准

**准入标准**:
- [ ] 代码开发完成并通过自测
- [ ] 单元测试覆盖率 > 80%
- [ ] 测试环境就绪
- [ ] 测试数据准备完成

**准出标准**:
- [ ] P0用例通过率 100%
- [ ] P1用例通过率 > 95%
- [ ] 无P0/P1级别缺陷未解决
- [ ] 性能指标达标
- [ ] 无高危安全漏洞

---

## 7. 风险评估

| 风险 | 影响 | 概率 | 应对措施 |
|------|------|------|----------|
| **环境不稳定** | 高 | 中 | 提前验证环境，准备备用环境 |
| **测试数据不足** | 中 | 中 | 提前准备测试数据生成脚本 |
| **API变更频繁** | 高 | 高 | 冻结版本后再测试，建立变更通知机制 |
| **性能瓶颈** | 中 | 低 | 提前进行压力测试，预留优化时间 |
| **第三方服务** | 中 | 中 | Mock外部服务 |

---

## 8. 测试交付物

| 交付物 | 格式 | 说明 |
|--------|------|------|
| **测试计划** | Markdown | 本文档 |
| **测试用例** | Python | tests/目录 |
| **测试报告** | HTML/JSON | pytest生成 |
| **性能报告** | HTML | locust生成 |
| **缺陷报告** | Excel/Mantis | 问题跟踪 |

---

**文档作者**: AI 测试工程师
**最后更新**: 2026-03-02
**版本**: 1.0.0
