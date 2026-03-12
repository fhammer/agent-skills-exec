"""
多租户模块单元测试
"""

import pytest
import time
import asyncio

from agent.multi_tenant import (
    # Tenant
    Tenant,
    TenantManager,
    TenantConfig,
    TenantStatus,
    SubscriptionPlan,
    RateLimitConfig,
    # Scene
    Scene,
    SceneManager,
    SceneConfig,
    SceneStatus,
    PredefinedSceneManager,
    # Session
    TenantSession,
    SessionManager,
    SessionStatus,
    MessageRole,
    Message,
    # Storage
    InMemoryTenantStorage,
    InMemorySceneStorage,
    InMemorySessionStorage,
    # Exceptions
    TenantNotFoundError,
    TenantAlreadyExistsError,
    TenantDisabledError,
    SceneNotFoundError,
    SceneAlreadyExistsError,
    SessionNotFoundError,
    RateLimitExceededError,
)


class TestTenantModel:
    """租户模型测试"""

    def test_create_tenant(self):
        """测试创建租户"""
        tenant = Tenant.create("test-tenant", SubscriptionPlan.FREE)

        assert tenant is not None
        assert tenant.tenant_id is not None
        assert tenant.config.name == "test-tenant"
        assert tenant.config.plan == SubscriptionPlan.FREE
        assert tenant.config.status == TenantStatus.ACTIVE
        assert tenant.is_active is True

    def test_tenant_plan_defaults(self):
        """测试计划默认配置"""
        tenant = Tenant.create("pro-tenant", SubscriptionPlan.PRO)

        assert tenant.config.features.enable_advanced_skills is True
        assert tenant.config.features.enable_custom_skills is True
        assert tenant.config.rate_limits.requests_per_minute == 200

    def test_rate_limit_check(self):
        """测试速率限制"""
        tenant = Tenant.create("test", SubscriptionPlan.FREE)

        # 初始应该成功
        assert tenant.check_rate_limit("minute") is True

        # 达到限制应该抛出异常
        tenant.usage.requests_minute = tenant.config.rate_limits.requests_per_minute
        with pytest.raises(RateLimitExceededError):
            tenant.check_rate_limit("minute")

    def test_record_tokens(self):
        """测试记录Token"""
        tenant = Tenant.create("test", SubscriptionPlan.FREE)
        tenant.record_tokens(1000)

        assert tenant.usage.tokens_day == 1000
        assert tenant.usage.total_tokens == 1000

    def test_to_dict_from_dict(self):
        """测试字典转换"""
        tenant = Tenant.create("test", SubscriptionPlan.BASIC)
        tenant_dict = tenant.to_dict()

        assert tenant_dict["tenant_id"] == tenant.tenant_id
        assert tenant_dict["config"]["name"] == "test"
        assert tenant_dict["config"]["plan"] == "basic"


class TestTenantManager:
    """租户管理器测试"""

    @pytest.mark.asyncio
    async def test_create_tenant(self):
        """测试创建租户"""
        storage = InMemoryTenantStorage()
        manager = TenantManager(storage)
        await manager.initialize()

        tenant = await manager.create_tenant("test-tenant", SubscriptionPlan.FREE)

        assert tenant is not None
        assert tenant.config.name == "test-tenant"

        # 再次创建应该失败
        with pytest.raises(TenantAlreadyExistsError):
            await manager.create_tenant("test-tenant", SubscriptionPlan.FREE, tenant_id=tenant.tenant_id)

    @pytest.mark.asyncio
    async def test_get_tenant(self):
        """测试获取租户"""
        storage = InMemoryTenantStorage()
        manager = TenantManager(storage)
        await manager.initialize()

        created = await manager.create_tenant("test-tenant")
        tenant = await manager.get_tenant(created.tenant_id)

        assert tenant is not None
        assert tenant.tenant_id == created.tenant_id

        # 获取不存在的租户应该失败
        with pytest.raises(TenantNotFoundError):
            await manager.get_tenant("non-existent")

    @pytest.mark.asyncio
    async def test_update_tenant(self):
        """测试更新租户"""
        storage = InMemoryTenantStorage()
        manager = TenantManager(storage)
        await manager.initialize()

        tenant = await manager.create_tenant("test-tenant")
        new_config = TenantConfig.from_plan(
            "updated-name",
            SubscriptionPlan.PRO,
            status=TenantStatus.ACTIVE
        )

        updated = await manager.update_tenant(tenant.tenant_id, new_config)

        assert updated.config.name == "updated-name"
        assert updated.config.plan == SubscriptionPlan.PRO

    @pytest.mark.asyncio
    async def test_disable_enable_tenant(self):
        """测试禁用/启用租户"""
        storage = InMemoryTenantStorage()
        manager = TenantManager(storage)
        await manager.initialize()

        tenant = await manager.create_tenant("test-tenant")

        # 禁用
        disabled = await manager.disable_tenant(tenant.tenant_id)
        assert disabled.config.status == TenantStatus.INACTIVE
        assert disabled.is_active is False

        # 检查访问应该失败
        with pytest.raises(TenantDisabledError):
            await manager.check_tenant_access(tenant.tenant_id)

        # 启用
        enabled = await manager.enable_tenant(tenant.tenant_id)
        assert enabled.config.status == TenantStatus.ACTIVE
        assert enabled.is_active is True

    @pytest.mark.asyncio
    async def test_list_tenants(self):
        """测试列出租户"""
        storage = InMemoryTenantStorage()
        manager = TenantManager(storage)
        await manager.initialize()

        await manager.create_tenant("tenant1")
        await manager.create_tenant("tenant2")
        await manager.create_tenant("tenant3")

        tenants = await manager.list_tenants()
        assert len(tenants) == 3


class TestSceneModel:
    """场景模型测试"""

    def test_create_scene(self):
        """测试创建场景"""
        scene = Scene.create(
            tenant_id="tenant1",
            name="test-scene",
            description="test description",
            default_skills=["skill1", "skill2"]
        )

        assert scene is not None
        assert scene.scene_id is not None
        assert scene.tenant_id == "tenant1"
        assert scene.config.name == "test-scene"
        assert scene.is_active is True

    def test_scene_skills(self):
        """测试场景技能"""
        scene = Scene.create(
            tenant_id="tenant1",
            name="test",
            enabled_skills=["skill1", "skill2"],
            disabled_skills=["skill3"]
        )

        assert scene.is_skill_available("skill1") is True
        assert scene.is_skill_available("skill3") is False

        # 禁用技能
        scene.disable_skill("skill1")
        assert scene.is_skill_available("skill1") is False

        # 启用技能
        scene.enable_skill("skill3")
        assert scene.is_skill_available("skill3") is True


class TestSessionModel:
    """会话模型测试"""

    def test_create_session(self):
        """测试创建会话"""
        session = TenantSession.create(
            tenant_id="tenant1",
            scene_id="scene1",
            user_id="user1"
        )

        assert session is not None
        assert session.session_id is not None
        assert session.tenant_id == "tenant1"
        assert session.scene_id == "scene1"
        assert session.user_id == "user1"
        assert session.is_active is True

    def test_session_messages(self):
        """测试会话消息"""
        session = TenantSession.create(tenant_id="tenant1")

        session.add_message(MessageRole.USER, "Hello")
        session.add_message(MessageRole.ASSISTANT, "Hi there")

        assert session.total_messages == 2
        assert session.context.message_count == 2

        last_msg = session.context.last_message
        assert last_msg is not None
        assert last_msg.content == "Hi there"
        assert last_msg.role == MessageRole.ASSISTANT

    def test_session_ttl(self):
        """测试会话TTL"""
        session = TenantSession.create(tenant_id="tenant1")
        original_expire = session.expires_at

        # 刷新应该延长TTL
        time.sleep(0.01)
        session.refresh()
        assert session.expires_at > original_expire

    def test_close_session(self):
        """测试关闭会话"""
        session = TenantSession.create(tenant_id="tenant1")

        assert session.is_active is True
        session.close()

        assert session.status == SessionStatus.CLOSED
        assert session.is_active is False


class TestMultiTenantIntegration:
    """多租户集成测试"""

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """测试完整工作流"""
        # 创建管理器
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
        tenant = await tenant_manager.create_tenant("ecommerce", SubscriptionPlan.PRO)
        assert tenant.is_active is True

        # 2. 为租户创建场景
        scene = await scene_manager.create_scene(
            tenant.tenant_id,
            "电商导购场景",
            description="智能产品推荐",
            default_skills=["product_search", "recommendation"]
        )

        assert scene.tenant_id == tenant.tenant_id

        # 3. 创建用户会话
        session = await session_manager.create_session(
            tenant.tenant_id,
            scene_id=scene.scene_id,
            user_id="user123"
        )

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
            "好的，我来帮您推荐手机"
        )

        # 5. 检查租户请求记录
        await tenant_manager.record_request(tenant.tenant_id, tokens=1500)
        tenant = await tenant_manager.get_tenant(tenant.tenant_id)

        assert tenant.usage.total_requests >= 1
        assert tenant.usage.tokens_day == 1500

        # 6. 验证会话
        final_session = await session_manager.get_session(session.session_id)
        assert final_session.total_messages == 2

    @pytest.mark.asyncio
    async def test_predefined_scenes(self):
        """测试预定义场景"""
        assert PredefinedSceneManager.is_predefined_scene("health") is True
        assert PredefinedSceneManager.is_predefined_scene("ecommerce_recommendation") is True
        assert PredefinedSceneManager.is_predefined_scene("nonexistent") is False

        health_config = PredefinedSceneManager.get_predefined_scene("health")
        assert health_config.name == "健康分析场景"
        assert len(health_config.default_skills) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
