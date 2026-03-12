# Agent Skills Framework - 工业级测试策略

## 1. 测试金字塔与策略总览

```
                    ╱╲
                   ╱  ╲
                  ╱ E2E╲         ← 端到端测试 (5%)
                 ╱────────╲          - 完整用户场景
                ╱          ╲         - 生产环境验证
               ╱ Integration ╲   ← 集成测试 (15%)
              ╱────────────────╲       - API/DB/缓存集成
             ╱                    ╲    - 外部服务Mock
            ╱      Unit Tests      ╲ ← 单元测试 (80%)
           ╱──────────────────────────╲  - 业务逻辑
          ╱                              ╲ - 边缘情况
         ╱__________________________________╲
```

## 2. 测试分层架构

### 2.1 单元测试层 (Unit Tests)

**覆盖范围**: 80%
**执行时间**: < 2分钟
**目标**: 快速反馈、高覆盖率

```python
# tests/unit/test_coordinator.py
import pytest
from unittest.mock import Mock, AsyncMock, patch
from agent.coordinator import Coordinator
from agent.context import AgentContext


class TestCoordinator:
    """Coordinator 单元测试"""

    @pytest.fixture
    def mock_llm_client(self):
        """Mock LLM客户端"""
        client = Mock()
        client.generate = AsyncMock(return_value={
            "content": "test response",
            "tokens": 10
        })
        return client

    @pytest.fixture
    def coordinator(self, mock_llm_client):
        """Coordinator实例"""
        return Coordinator(
            llm_client=mock_llm_client,
            skills_dir="test_skills"
        )

    @pytest.mark.asyncio
    async def test_process_simple_request(self, coordinator):
        """测试简单请求处理"""
        # Arrange
        request = "What is the weather?"

        # Act
        result = await coordinator.process(request)

        # Assert
        assert result is not None
        assert "response" in result
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_process_with_context(self, coordinator):
        """测试带上下文的处理"""
        # Arrange
        context = AgentContext(
            session_id="test_session",
            user_id="test_user"
        )

        # Act
        result = await coordinator.process(
            "Remember my name is John",
            context=context
        )

        # Assert
        assert context.memory.get("user_name") == "John"

    @pytest.mark.asyncio
    async def test_error_handling(self, coordinator, mock_llm_client):
        """测试错误处理"""
        # Arrange
        mock_llm_client.generate.side_effect = Exception("LLM Error")

        # Act & Assert
        with pytest.raises(CoordinatorError) as exc_info:
            await coordinator.process("test")

        assert "LLM Error" in str(exc_info.value)

    @pytest.mark.parametrize("input_text,expected_skill", [
        ("parse report", "parse_report"),
        ("assess risk", "assess_risk"),
        ("generate advice", "generate_advice"),
    ])
    @pytest.mark.asyncio
    async def test_skill_selection(self, coordinator, input_text, expected_skill):
        """测试技能选择逻辑"""
        # Act
        selected_skill = coordinator._select_skill(input_text)

        # Assert
        assert selected_skill == expected_skill
```

### 2.2 集成测试层 (Integration Tests)

**覆盖范围**: 15%
**执行时间**: 5-10分钟
**目标**: 组件间协作、外部依赖验证

```python
# tests/integration/test_api.py
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.main import app
from api.database import get_db
from tests.conftest import TestingSessionLocal


@pytest_asyncio.fixture
async def async_client():
    """创建异步测试客户端"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    """创建测试数据库会话"""
    async with TestingSessionLocal() as session:
        yield session
        # 清理测试数据
        await session.rollback()


class TestHealthEndpoints:
    """健康检查端点集成测试"""

    @pytest.mark.asyncio
    async def test_health_check(self, async_client):
        """测试健康检查"""
        response = await async_client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "database" in data
        assert "redis" in data

    @pytest.mark.asyncio
    async def test_readiness_check(self, async_client):
        """测试就绪检查"""
        response = await async_client.get("/api/v1/health/ready")

        assert response.status_code == 200
        data = response.json()
        assert data["ready"] is True


class TestTenantEndpoints:
    """租户管理端点集成测试"""

    @pytest.mark.asyncio
    async def test_create_tenant(self, async_client, db_session):
        """测试创建租户"""
        # Arrange
        tenant_data = {
            "name": "Test Tenant",
            "description": "Test description",
            "tier": "basic"
        }

        # Act
        response = await async_client.post(
            "/api/v1/tenants",
            json=tenant_data,
            headers={"Authorization": "Bearer test_api_key"}
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == tenant_data["name"]
        assert "tenant_id" in data
        assert "api_key" in data

    @pytest.mark.asyncio
    async def test_get_tenant(self, async_client, db_session):
        """测试获取租户"""
        # Arrange - 先创建一个租户
        create_response = await async_client.post(
            "/api/v1/tenants",
            json={"name": "Test Tenant"},
            headers={"Authorization": "Bearer test_api_key"}
        )
        tenant_id = create_response.json()["tenant_id"]

        # Act
        response = await async_client.get(
            f"/api/v1/tenants/{tenant_id}",
            headers={"Authorization": "Bearer test_api_key"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["tenant_id"] == tenant_id

    @pytest.mark.asyncio
    async def test_list_tenants(self, async_client, db_session):
        """测试列出租户"""
        # Act
        response = await async_client.get(
            "/api/v1/tenants",
            headers={"Authorization": "Bearer test_api_key"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)


class TestAgentEndpoints:
    """Agent对话端点集成测试"""

    @pytest.mark.asyncio
    async def test_chat(self, async_client, db_session):
        """测试对话接口"""
        # Arrange
        chat_data = {
            "message": "What is the weather today?",
            "session_id": "test_session_001",
            "context": {}
        }

        # Act
        response = await async_client.post(
            "/api/v1/agent/chat",
            json=chat_data,
            headers={
                "Authorization": "Bearer test_api_key",
                "X-Tenant-ID": "test_tenant"
            }
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "session_id" in data

    @pytest.mark.asyncio
    async def test_chat_streaming(self, async_client, db_session):
        """测试流式对话接口"""
        # Arrange
        chat_data = {
            "message": "Tell me a story",
            "session_id": "test_session_002",
            "stream": True
        }

        # Act
        response = await async_client.post(
            "/api/v1/agent/chat",
            json=chat_data,
            headers={"Authorization": "Bearer test_api_key"}
        )

        # Assert
        assert response.status_code == 200
        # 流式响应验证


class TestErrorHandling:
    """错误处理集成测试"""

    @pytest.mark.asyncio
    async def test_invalid_api_key(self, async_client):
        """测试无效API Key"""
        response = await async_client.get(
            "/api/v1/tenants",
            headers={"Authorization": "Bearer invalid_key"}
        )

        assert response.status_code == 401
        data = response.json()
        assert data["error"]["code"] == "AUTHENTICATION_FAILED"

    @pytest.mark.asyncio
    async def test_rate_limit(self, async_client):
        """测试限流"""
        # 快速发送多个请求
        responses = []
        for _ in range(150):  # 超过默认100/min限制
            response = await async_client.get(
                "/api/v1/health",
                headers={"Authorization": "Bearer test_key"}
            )
            responses.append(response)

        # 验证部分请求被限流
        rate_limited = [r for r in responses if r.status_code == 429]
        assert len(rate_limited) > 0

    @pytest.mark.asyncio
    async def test_not_found(self, async_client):
        """测试404错误"""
        response = await async_client.get(
            "/api/v1/nonexistent",
            headers={"Authorization": "Bearer test_key"}
        )

        assert response.status_code == 404
        data = response.json()
        assert "error" in data
