"""
多租户管理器

提供租户和场景的创建、查询、更新、删除等功能。
"""

import uuid
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import threading
import logging

from tenant.context import (
    TenantContext,
    SceneContext,
    TenantConfig,
    SceneConfig,
    TenantStatus,
    SceneStatus,
    ResourceQuota,
)

logger = logging.getLogger(__name__)


class TenantManager:
    """
    多租户管理器

    管理所有租户和场景的生命周期，提供租户隔离、配置继承、资源配额等功能。
    """

    def __init__(self):
        self._tenants: Dict[str, TenantContext] = {}
        self._scenes: Dict[str, SceneContext] = {}
        self._tenant_by_api_key: Dict[str, str] = {}  # api_key -> tenant_id
        self._lock = threading.RLock()
        self._initialized = False

    async def initialize(self):
        """初始化管理器"""
        if self._initialized:
            return

        logger.info("初始化租户管理器...")
        # 创建默认租户
        await self.create_default_tenant()
        self._initialized = True
        logger.info("租户管理器初始化完成")

    async def create_default_tenant(self):
        """创建默认租户"""
        default_tenant_id = "default"
        if default_tenant_id not in self._tenants:
            tenant = TenantContext(
                tenant_id=default_tenant_id,
                name="Default Tenant",
                config=TenantConfig(),
                resource_quota=ResourceQuota(
                    token_limit=1000000,
                    qps_limit=100,
                ),
                status=TenantStatus.ACTIVE,
            )
            self._tenants[default_tenant_id] = tenant
            logger.info(f"创建默认租户: {default_tenant_id}")

    # ==================== 租户管理 ====================

    def create_tenant(
        self,
        name: str,
        config: Optional[TenantConfig] = None,
        resource_quota: Optional[ResourceQuota] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TenantContext:
        """
        创建租户

        Args:
            name: 租户名称
            config: 租户配置
            resource_quota: 资源配额
            metadata: 元数据

        Returns:
            创建的租户上下文
        """
        with self._lock:
            tenant_id = f"tenant_{uuid.uuid4().hex[:12]}"
            api_key = self._generate_api_key()

            tenant = TenantContext(
                tenant_id=tenant_id,
                name=name,
                config=config or TenantConfig(),
                resource_quota=resource_quota or ResourceQuota(),
                status=TenantStatus.ACTIVE,
                metadata=metadata or {},
            )

            self._tenants[tenant_id] = tenant
            self._tenant_by_api_key[api_key] = tenant_id

            logger.info(f"创建租户: {tenant_id} ({name})")
            return tenant

    def get_tenant(self, tenant_id: str) -> Optional[TenantContext]:
        """获取租户"""
        return self._tenants.get(tenant_id)

    def get_tenant_by_api_key(self, api_key: str) -> Optional[TenantContext]:
        """通过API Key获取租户"""
        tenant_id = self._tenant_by_api_key.get(api_key)
        if tenant_id:
            return self._tenants.get(tenant_id)
        return None

    def list_tenants(
        self, status: Optional[TenantStatus] = None, limit: int = 100
    ) -> List[TenantContext]:
        """列出租户"""
        tenants = list(self._tenants.values())
        if status:
            tenants = [t for t in tenants if t.status == status]
        return tenants[:limit]

    def update_tenant(
        self,
        tenant_id: str,
        name: Optional[str] = None,
        config: Optional[TenantConfig] = None,
        resource_quota: Optional[ResourceQuota] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """更新租户"""
        with self._lock:
            tenant = self._tenants.get(tenant_id)
            if not tenant:
                return False

            if name is not None:
                tenant.name = name
            if config is not None:
                tenant.config = config
            if resource_quota is not None:
                tenant.resource_quota = resource_quota
            if metadata is not None:
                tenant.metadata.update(metadata)

            tenant.updated_at = datetime.utcnow()
            logger.info(f"更新租户: {tenant_id}")
            return True

    def delete_tenant(self, tenant_id: str) -> bool:
        """删除租户"""
        with self._lock:
            tenant = self._tenants.get(tenant_id)
            if not tenant:
                return False

            # 删除租户的所有场景
            for scene_id in list(tenant.scenes.keys()):
                self.delete_scene(scene_id)

            # 删除租户
            api_key = self._get_api_key_for_tenant(tenant_id)
            if api_key and api_key in self._tenant_by_api_key:
                del self._tenant_by_api_key[api_key]

            del self._tenants[tenant_id]
            logger.info(f"删除租户: {tenant_id}")
            return True

    def suspend_tenant(self, tenant_id: str) -> bool:
        """暂停租户"""
        tenant = self._tenants.get(tenant_id)
        if tenant:
            tenant.status = TenantStatus.SUSPENDED
            tenant.updated_at = datetime.utcnow()
            logger.info(f"暂停租户: {tenant_id}")
            return True
        return False

    def activate_tenant(self, tenant_id: str) -> bool:
        """激活租户"""
        tenant = self._tenants.get(tenant_id)
        if tenant:
            tenant.status = TenantStatus.ACTIVE
            tenant.updated_at = datetime.utcnow()
            logger.info(f"激活租户: {tenant_id}")
            return True
        return False

    def regenerate_api_key(self, tenant_id: str) -> Optional[str]:
        """重新生成API Key"""
        with self._lock:
            tenant = self._tenants.get(tenant_id)
            if not tenant:
                return None

            # 删除旧key
            old_key = self._get_api_key_for_tenant(tenant_id)
            if old_key and old_key in self._tenant_by_api_key:
                del self._tenant_by_api_key[old_key]

            # 生成新key
            new_key = self._generate_api_key()
            self._tenant_by_api_key[new_key] = tenant_id

            logger.info(f"重新生成API Key: {tenant_id}")
            return new_key

    # ==================== 场景管理 ====================

    def create_scene(
        self,
        tenant_id: str,
        name: str,
        description: str = "",
        config: Optional[SceneConfig] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[SceneContext]:
        """
        创建场景

        Args:
            tenant_id: 所属租户ID
            name: 场景名称
            description: 场景描述
            config: 场景配置
            metadata: 元数据

        Returns:
            创建的场景上下文
        """
        with self._lock:
            tenant = self._tenants.get(tenant_id)
            if not tenant:
                logger.warning(f"租户不存在，无法创建场景: {tenant_id}")
                return None

            # 检查场景数量限制
            if len(tenant.scenes) >= 100:
                logger.warning(f"租户场景数量已达上限: {tenant_id}")
                return None

            scene_id = f"scene_{uuid.uuid4().hex[:12]}"
            scene = SceneContext(
                scene_id=scene_id,
                tenant_id=tenant_id,
                name=name,
                description=description,
                config=config or SceneConfig(),
                status=SceneStatus.ACTIVE,
                metadata=metadata or {},
            )

            tenant.add_scene(scene)
            self._scenes[scene_id] = scene

            logger.info(f"创建场景: {scene_id} ({name}) in {tenant_id}")
            return scene

    def get_scene(self, scene_id: str) -> Optional[SceneContext]:
        """获取场景"""
        return self._scenes.get(scene_id)

    def list_scenes(
        self,
        tenant_id: Optional[str] = None,
        status: Optional[SceneStatus] = None,
        limit: int = 100,
    ) -> List[SceneContext]:
        """列出场景"""
        scenes = list(self._scenes.values())

        if tenant_id:
            scenes = [s for s in scenes if s.tenant_id == tenant_id]
        if status:
            scenes = [s for s in scenes if s.status == status]

        return scenes[:limit]

    def update_scene(
        self,
        scene_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        config: Optional[SceneConfig] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """更新场景"""
        with self._lock:
            scene = self._scenes.get(scene_id)
            if not scene:
                return False

            if name is not None:
                scene.name = name
            if description is not None:
                scene.description = description
            if config is not None:
                scene.config = config
            if metadata is not None:
                scene.metadata.update(metadata)

            scene.updated_at = datetime.utcnow()
            logger.info(f"更新场景: {scene_id}")
            return True

    def delete_scene(self, scene_id: str) -> bool:
        """删除场景"""
        with self._lock:
            scene = self._scenes.get(scene_id)
            if not scene:
                return False

            # 从租户中移除
            tenant = self._tenants.get(scene.tenant_id)
            if tenant:
                tenant.remove_scene(scene_id)

            del self._scenes[scene_id]
            logger.info(f"删除场景: {scene_id}")
            return True

    def activate_scene(self, scene_id: str) -> bool:
        """激活场景"""
        scene = self._scenes.get(scene_id)
        if scene:
            scene.status = SceneStatus.ACTIVE
            scene.updated_at = datetime.utcnow()
            return True
        return False

    def deactivate_scene(self, scene_id: str) -> bool:
        """停用场景"""
        scene = self._scenes.get(scene_id)
        if scene:
            scene.status = SceneStatus.INACTIVE
            scene.updated_at = datetime.utcnow()
            return True
        return False

    # ==================== 配置管理 ====================

    def get_effective_config(self, tenant_id: str, scene_id: Optional[str] = None) -> TenantConfig:
        """
        获取有效配置

        如果指定了scene_id，则返回合并后的配置（租户配置+场景配置，场景配置优先级更高）
        否则只返回租户配置

        Args:
            tenant_id: 租户ID
            scene_id: 场景ID（可选）

        Returns:
            有效的租户配置
        """
        tenant = self._tenants.get(tenant_id)
        if not tenant:
            return TenantConfig()

        if scene_id:
            return tenant.get_merged_config(scene_id)
        return tenant.config

    # ==================== 资源配额管理 ====================

    def check_token_quota(self, tenant_id: str, tokens: int) -> bool:
        """检查Token配额"""
        tenant = self._tenants.get(tenant_id)
        if tenant:
            return tenant.resource_quota.check_token_quota(tokens)
        return False

    def consume_tokens(self, tenant_id: str, tokens: int) -> bool:
        """消耗Token配额"""
        tenant = self._tenants.get(tenant_id)
        if tenant:
            return tenant.resource_quota.consume_tokens(tokens)
        return False

    def get_token_usage(self, tenant_id: str) -> Dict[str, Any]:
        """获取Token使用情况"""
        tenant = self._tenants.get(tenant_id)
        if tenant:
            return tenant.resource_quota.to_dict()
        return {}

    def check_quota_alert(self, tenant_id: str, threshold: float = 0.9) -> bool:
        """检查配额告警"""
        tenant = self._tenants.get(tenant_id)
        if tenant:
            return tenant.resource_quota.is_near_limit(threshold)
        return False

    # ==================== 工具方法 ====================

    def _generate_api_key(self) -> str:
        """生成API Key"""
        import secrets
        return f"sk_agent_{secrets.token_urlsafe(32)}"

    def _get_api_key_for_tenant(self, tenant_id: str) -> Optional[str]:
        """获取租户的API Key"""
        for api_key, tid in self._tenant_by_api_key.items():
            if tid == tenant_id:
                return api_key
        return None

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        active_tenants = [t for t in self._tenants.values() if t.status == TenantStatus.ACTIVE]
        active_scenes = [s for s in self._scenes.values() if s.status == SceneStatus.ACTIVE]

        return {
            "total_tenants": len(self._tenants),
            "active_tenants": len(active_tenants),
            "suspended_tenants": len(self._tenants) - len(active_tenants),
            "total_scenes": len(self._scenes),
            "active_scenes": len(active_scenes),
            "avg_scenes_per_tenant": len(self._scenes) / len(self._tenants) if self._tenants else 0,
        }


# 全局单例
_tenant_manager: Optional[TenantManager] = None
_manager_lock = threading.Lock()


def get_tenant_manager() -> TenantManager:
    """获取租户管理器单例"""
    global _tenant_manager
    if _tenant_manager is None:
        with _manager_lock:
            if _tenant_manager is None:
                _tenant_manager = TenantManager()
    return _tenant_manager
