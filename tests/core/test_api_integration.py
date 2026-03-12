"""
API 服务层集成测试

测试 API 认证、租户管理、会话管理等功能
"""

import pytest
from fastapi.testclient import TestClient
import asyncio
import time

# 导入我们实现的核心模块
from agent.multi_tenant import (
    TenantManager,
    SceneManager,
    SessionManager,
    Tenant,
    TenantConfig,
    TenantStatus,
    SubscriptionPlan,
)
from agent.multi_tenant.storage import (
    InMemoryTenantStorage,
    InMemorySceneStorage,
    InMemorySessionStorage,
)
# 认证管理器从 api.auth 导入
from api.auth import get_jwt_manager, get_api_key_manager


class TestTenantSystem:
    """多租户系统测试"""

    @pytest.mark.asyncio
    async def test_tenant_creation(self):
        """测试创建租户"""
        storage = InMemoryTenantStorage()
        manager = TenantManager(storage)
        await manager.initialize()

        tenant = await manager.create_tenant("test-tenant", SubscriptionPlan.FREE)

        assert tenant is not None
        assert tenant.tenant_id is not None
        assert tenant.config.name == "test-tenant"
        assert tenant.config.plan == SubscriptionPlan.FREE
        assert tenant.is_active is True

    @pytest.mark.asyncio
    async def test_tenant_retrieval(self):
        """测试获取租户"""
        storage = InMemoryTenantStorage()
        manager = TenantManager(storage)
        await manager.initialize()

        created = await manager.create_tenant("test-tenant", SubscriptionPlan.FREE)
        tenant = await manager.get_tenant(created.tenant_id)

        assert tenant.tenant_id == created.tenant_id
        assert tenant.config.name == "test-tenant"

    @pytest.mark.asyncio
    async def test_tenant_disable_enable(self):
        """测试禁用和启用租户"""
        storage = InMemoryTenantStorage()
        manager = TenantManager(storage)
        await manager.initialize()

        tenant = await manager.create_tenant("test-tenant", SubscriptionPlan.FREE)
        assert tenant.is_active is True

        # 禁用
        disabled = await manager.disable_tenant(tenant.tenant_id)
        assert disabled.is_active is False
        assert disabled.config.status == TenantStatus.INACTIVE

        # 启用
        enabled = await manager.enable_tenant(tenant.tenant_id)
        assert enabled.is_active is True
        assert enabled.config.status == TenantStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """测试速率限制"""
        storage = InMemoryTenantStorage()
        manager = TenantManager(storage)
        await manager.initialize()

        tenant = await manager.create_tenant("test-tenant", SubscriptionPlan.FREE)

        # 检查在限制内的请求
        for i in range(5):
            tenant.check_rate_limit("minute")
        assert tenant.usage.requests_minute == 5


class TestSceneSystem:
    """场景系统测试"""

    @pytest.mark.asyncio
    async def test_scene_creation(self):
        """测试创建场景"""
        storage = InMemorySceneStorage()
        manager = SceneManager(storage)
        await manager.initialize()

        scene = await manager.create_scene(
            tenant_id="tenant-1",
            name="电商场景",
            description="电商购物助手",
            default_skills=["search", "recommend"]
        )

        assert scene is not None
        assert scene.scene_id is not None
        assert scene.tenant_id == "tenant-1"
        assert scene.config.name == "电商场景"
        assert scene.is_active is True

    @pytest.mark.asyncio
    async def test_scene_skills(self):
        """测试场景技能管理"""
        storage = InMemorySceneStorage()
        manager = SceneManager(storage)
        await manager.initialize()

        scene = await manager.create_scene(
            tenant_id="tenant-1",
            name="电商场景",
            enabled_skills=["search", "recommend"],
            disabled_skills=["debug"]
        )

        assert scene.is_skill_available("search") is True
        assert scene.is_skill_available("debug") is False

        # 禁用技能
        scene.disable_skill("search")
        assert scene.is_skill_available("search") is False

        # 启用技能
        scene.enable_skill("debug")
        assert scene.is_skill_available("debug") is True


class TestSessionSystem:
    """会话系统测试"""

    @pytest.mark.asyncio
    async def test_session_creation(self):
        """测试创建会话"""
        storage = InMemorySessionStorage()
        manager = SessionManager(storage)
        await manager.initialize()

        session = await manager.create_session(
            tenant_id="tenant-1",
            scene_id="scene-1",
            user_id="user-1"
        )

        assert session is not None
        assert session.session_id is not None
        assert session.tenant_id == "tenant-1"
        assert session.scene_id == "scene-1"
        assert session.user_id == "user-1"
        assert session.is_active is True

    @pytest.mark.asyncio
    async def test_session_messages(self):
        """测试会话消息"""
        storage = InMemorySessionStorage()
        manager = SessionManager(storage)
        await manager.initialize()

        session = await manager.create_session(
            tenant_id="tenant-1",
            scene_id="scene-1",
            user_id="user-1"
        )

        # 添加消息
        await manager.add_message(session.session_id, MessageRole.USER, "你好")
        await manager.add_message(session.session_id, MessageRole.ASSISTANT, "你好！")

        updated = await manager.get_session(session.session_id)
        assert updated.total_messages == 2
        assert updated.context.message_count == 2

    @pytest.mark.asyncio
    async def test_session_close(self):
        """测试关闭会话"""
        storage = InMemorySessionStorage()
        manager = SessionManager(storage)
        await manager.initialize()

        session = await manager.create_session(
            tenant_id="tenant-1",
            scene_id="scene-1",
            user_id="user-1"
        )
        assert session.is_active is True

        closed = await manager.close_session(session.session_id)
        assert closed.status == SessionStatus.CLOSED
        assert closed.is_active is False


class TestAuthSystem:
    """认证系统测试"""

    def test_jwt_creation(self):
        """测试 JWT 创建"""
        manager = get_jwt_manager()

        token = manager.create_access_token(
            tenant_id="tenant-1",
            user_id="user-1",
            permissions=["agent:chat", "skills:read"]
        )

        assert token is not None
        assert len(token) > 0

    def test_jwt_validation(self):
        """测试 JWT 验证"""
        manager = get_jwt_manager()

        token = manager.create_access_token(
            tenant_id="tenant-1",
            user_id="user-1",
            permissions=["agent:chat"]
        )

        payload = manager.decode_token(token)
        assert payload is not None
        assert payload.tenant_id == "tenant-1"
        assert payload.user_id == "user-1"

    def test_api_key_creation(self):
        """测试 API Key 创建"""
        manager = get_api_key_manager()

        api_key = manager.create_api_key(
            tenant_id="tenant-1",
            name="Test Key",
            permissions=["admin"]
        )

        assert api_key is not None
        assert api_key.startswith("sk_agent_")

    def test_api_key_validation(self):
        """测试 API Key 验证"""
        manager = get_api_key_manager()

        api_key = manager.create_api_key(
            tenant_id="tenant-1",
            name="Test Key",
            permissions=["admin"]
        )

        key_info = manager.verify_api_key(api_key)
        assert key_info is not None
        assert key_info.tenant_id == "tenant-1"
        assert key_info.name == "Test Key"
        assert key_info.is_active is True


# 导入需要的类型
from agent.multi_tenant import MessageRole, SessionStatus


class TestFullWorkflow:
    """完整工作流测试"""

    @pytest.mark.asyncio
    async def test_tenant_scene_session_workflow(self):
        """测试完整的租户-场景-会话工作流"""
        # 初始化管理器
        tenant_storage = InMemoryTenantStorage()
        scene_storage = InMemorySceneStorage()
        session_storage = InMemorySessionStorage()

        tenant_manager = TenantManager(tenant_storage)
        scene_manager = SceneManager(scene_storage)
        session_manager = SessionManager(session_storage)

        await tenant_manager.initialize()
        await scene_manager.initialize()
        await session_manager.initialize()

        # 1. 创建租户
        tenant = await tenant_manager.create_tenant(
            "电商公司",
            SubscriptionPlan.PRO
        )
        assert tenant is not None
        assert tenant.config.plan == SubscriptionPlan.PRO

        # 2. 为租户创建场景
        scene = await scene_manager.create_scene(
            tenant_id=tenant.tenant_id,
            name="智能购物助手",
            description="帮助用户选购商品",
            default_skills=["product_search", "recommendation"]
        )
        assert scene is not None
        assert scene.tenant_id == tenant.tenant_id

        # 3. 创建用户会话
        session = await session_manager.create_session(
            tenant_id=tenant.tenant_id,
            scene_id=scene.scene_id,
            user_id="customer-123"
        )
        assert session is not None
        assert session.tenant_id == tenant.tenant_id
        assert session.scene_id == scene.scene_id

        # 4. 添加对话消息
        await session_manager.add_message(
            session.session_id,
            MessageRole.USER,
            "我想买个手机"
        )
        await session_manager.add_message(
            session.session_id,
            MessageRole.ASSISTANT,
            "好的，我来帮您推荐！"
        )

        # 5. 验证数据
        updated_session = await session_manager.get_session(session.session_id)
        assert updated_session.total_messages == 2

        # 6. 记录租户请求
        await tenant_manager.record_request(tenant.tenant_id, tokens=2500)
        updated_tenant = await tenant_manager.get_tenant(tenant.tenant_id)
        assert updated_tenant.usage.total_requests >= 1
        assert updated_tenant.usage.total_tokens == 2500


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
