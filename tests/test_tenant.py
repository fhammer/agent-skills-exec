"""
多租户管理模块测试
"""

import pytest
import asyncio
from tenant.context import (
    TenantContext,
    SceneContext,
    TenantConfig,
    SceneConfig,
    ResourceQuota,
    TenantStatus,
    SceneStatus,
)
from tenant.manager import TenantManager, get_tenant_manager


class TestTenantContext:
    """租户上下文测试"""

    def test_create_tenant_context(self):
        """测试创建租户上下文"""
        tenant = TenantContext(
            tenant_id="tenant_001",
            name="Test Tenant",
            config=TenantConfig(),
            resource_quota=ResourceQuota(token_limit=100000),
        )

        assert tenant.tenant_id == "tenant_001"
        assert tenant.name == "Test Tenant"
        assert tenant.status == TenantStatus.ACTIVE
        assert len(tenant.scenes) == 0

    def test_add_scene(self):
        """测试添加场景"""
        tenant = TenantContext(
            tenant_id="tenant_001",
            name="Test Tenant",
        )

        scene = SceneContext(
            scene_id="scene_001",
            tenant_id="tenant_001",
            name="Test Scene",
        )

        tenant.add_scene(scene)

        assert len(tenant.scenes) == 1
        assert tenant.get_scene("scene_001") == scene

    def test_remove_scene(self):
        """测试移除场景"""
        tenant = TenantContext(
            tenant_id="tenant_001",
            name="Test Tenant",
        )

        scene = SceneContext(
            scene_id="scene_001",
            tenant_id="tenant_001",
            name="Test Scene",
        )

        tenant.add_scene(scene)
        assert len(tenant.scenes) == 1

        tenant.remove_scene("scene_001")
        assert len(tenant.scenes) == 0

    def test_get_merged_config(self):
        """测试配置合并"""
        tenant_config = TenantConfig()
        scene_config = SceneConfig(
            llm_config=SceneConfig().llm_config,
            skill_whitelist=["skill1", "skill2"],
        )

        tenant = TenantContext(
            tenant_id="tenant_001",
            name="Test Tenant",
            config=tenant_config,
        )

        scene = SceneContext(
            scene_id="scene_001",
            tenant_id="tenant_001",
            name="Test Scene",
            config=scene_config,
        )

        tenant.add_scene(scene)

        merged = tenant.get_merged_config("scene_001")
        assert merged.skill_whitelist == ["skill1", "skill2"]


class TestResourceQuota:
    """资源配额测试"""

    def test_check_token_quota(self):
        """检查Token配额"""
        quota = ResourceQuota(token_limit=1000, token_used=500)

        assert quota.check_token_quota(400) is True
        assert quota.check_token_quota(600) is False

    def test_consume_tokens(self):
        """测试消耗Token"""
        quota = ResourceQuota(token_limit=1000, token_used=500)

        assert quota.consume_tokens(400) is True
        assert quota.token_used == 900

        assert quota.consume_tokens(200) is False
        assert quota.token_used == 900

    def test_get_token_usage_percentage(self):
        """测试获取使用百分比"""
        quota = ResourceQuota(token_limit=1000, token_used=500)

        assert quota.get_token_usage_percentage() == 50.0

    def test_is_near_limit(self):
        """测试是否接近限制"""
        quota = ResourceQuota(token_limit=1000, token_used=850)

        assert quota.is_near_limit(threshold=0.9) is False
        assert quota.is_near_limit(threshold=0.8) is True


class TestTenantManager:
    """租户管理器测试"""

    @pytest.fixture
    async def manager(self):
        """创建管理器"""
        manager = TenantManager()
        await manager.initialize()
        return manager

    @pytest.mark.asyncio
    async def test_create_tenant(self, manager):
        """测试创建租户"""
        tenant = manager.create_tenant(
            name="Test Tenant",
            resource_quota=ResourceQuota(token_limit=100000),
        )

        assert tenant.tenant_id.startswith("tenant_")
        assert tenant.name == "Test Tenant"
        assert tenant.status == TenantStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_get_tenant(self, manager):
        """测试获取租户"""
        tenant = manager.create_tenant(name="Test Tenant")
        retrieved = manager.get_tenant(tenant.tenant_id)

        assert retrieved is not None
        assert retrieved.tenant_id == tenant.tenant_id

    @pytest.mark.asyncio
    async def test_create_scene(self, manager):
        """测试创建场景"""
        tenant = manager.create_tenant(name="Test Tenant")

        scene = manager.create_scene(
            tenant_id=tenant.tenant_id,
            name="Test Scene",
            description="A test scene",
        )

        assert scene is not None
        assert scene.scene_id.startswith("scene_")
        assert scene.tenant_id == tenant.tenant_id
        assert scene.status == SceneStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_token_quota_check(self, manager):
        """测试Token配额检查"""
        tenant = manager.create_tenant(
            name="Test Tenant",
            resource_quota=ResourceQuota(token_limit=1000),
        )

        assert manager.check_token_quota(tenant.tenant_id, 500) is True
        assert manager.consume_tokens(tenant.tenant_id, 500) is True
        assert manager.check_token_quota(tenant.tenant_id, 600) is False


class TestConfigInheritance:
    """配置继承测试"""

    def test_tenant_config_default(self):
        """测试租户默认配置"""
        config = TenantConfig()

        assert config.llm_config.provider == "anthropic"
        assert config.llm_config.model == "glm-4.7"
        assert len(config.skill_whitelist) == 0
        assert config.enable_audit_log is True

    def test_scene_config_override(self):
        """测试场景配置覆盖"""
        tenant_config = TenantConfig(
            skill_whitelist=["skill1", "skill2"],
        )

        scene_config = SceneConfig(
            skill_whitelist=["skill3"],
            rate_limit={"requests": 200},
        )

        merged = tenant_config.merge_with_scene_config(scene_config)

        # 场景配置应该覆盖租户配置
        assert merged.skill_whitelist == ["skill3"]
        assert merged.rate_limit == {"requests": 200}
