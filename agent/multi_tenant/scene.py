"""
场景管理模块

提供场景定义和管理功能
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List, Set
import time
import uuid

from .exceptions import (
    SceneNotFoundError,
    SceneAlreadyExistsError,
)


class SceneStatus(Enum):
    """场景状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"
    ARCHIVED = "archived"


@dataclass
class SceneConfig:
    """场景配置"""
    name: str
    description: str = ""
    status: SceneStatus = SceneStatus.ACTIVE
    default_skills: List[str] = field(default_factory=list)
    enabled_skills: List[str] = field(default_factory=list)
    disabled_skills: List[str] = field(default_factory=list)
    skill_priorities: Dict[str, int] = field(default_factory=dict)
    custom_settings: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """后处理"""
        if not self.enabled_skills:
            self.enabled_skills = self.default_skills.copy()

    @property
    def available_skills(self) -> List[str]:
        """获取可用技能列表"""
        return [
            skill for skill in self.enabled_skills
            if skill not in self.disabled_skills
        ]

    def is_skill_available(self, skill_name: str) -> bool:
        """检查技能是否可用"""
        return skill_name in self.available_skills

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "default_skills": self.default_skills,
            "enabled_skills": self.enabled_skills,
            "disabled_skills": self.disabled_skills,
            "skill_priorities": self.skill_priorities,
            "custom_settings": self.custom_settings,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SceneConfig":
        """从字典创建"""
        data = data.copy()
        if "status" in data and isinstance(data["status"], str):
            data["status"] = SceneStatus(data["status"])
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class Scene:
    """场景数据模型"""
    scene_id: str
    tenant_id: str
    config: SceneConfig
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    @property
    def is_active(self) -> bool:
        """是否活跃"""
        return self.config.status == SceneStatus.ACTIVE

    @property
    def name(self) -> str:
        """获取名称"""
        return self.config.name

    @property
    def available_skills(self) -> List[str]:
        """获取可用技能"""
        return self.config.available_skills

    def get_skill_priority(self, skill_name: str) -> int:
        """获取技能优先级"""
        return self.config.skill_priorities.get(skill_name, 0)

    def is_skill_available(self, skill_name: str) -> bool:
        """检查技能是否可用"""
        return self.config.is_skill_available(skill_name)

    def enable_skill(self, skill_name: str):
        """启用技能"""
        if skill_name not in self.config.enabled_skills:
            self.config.enabled_skills.append(skill_name)
        if skill_name in self.config.disabled_skills:
            self.config.disabled_skills.remove(skill_name)
        self.updated_at = time.time()

    def disable_skill(self, skill_name: str):
        """禁用技能"""
        if skill_name not in self.config.disabled_skills:
            self.config.disabled_skills.append(skill_name)
        if skill_name in self.config.enabled_skills:
            self.config.enabled_skills.remove(skill_name)
        self.updated_at = time.time()

    def update_skill_priority(self, skill_name: str, priority: int):
        """更新技能优先级"""
        self.config.skill_priorities[skill_name] = priority
        self.updated_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "scene_id": self.scene_id,
            "tenant_id": self.tenant_id,
            "config": self.config.to_dict(),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def create(
        cls,
        tenant_id: str,
        name: str,
        description: str = "",
        **kwargs
    ) -> "Scene":
        """创建场景"""
        scene_id = kwargs.pop("scene_id", str(uuid.uuid4()))
        config = SceneConfig(
            name=name,
            description=description,
            **kwargs
        )
        return cls(scene_id=scene_id, tenant_id=tenant_id, config=config)


class SceneManager:
    """场景管理器"""

    def __init__(self, storage: Optional["SceneStorage"] = None):
        """初始化场景管理器"""
        from .storage import SceneStorage, InMemorySceneStorage

        self._storage: SceneStorage = storage or InMemorySceneStorage()
        self._cache: Dict[str, Scene] = {}

    async def initialize(self):
        """初始化管理器"""
        for scene in await self._storage.list_all():
            self._cache[scene.scene_id] = scene

    async def create_scene(
        self,
        tenant_id: str,
        name: str,
        description: str = "",
        **kwargs
    ) -> Scene:
        """创建场景"""
        scene_id = kwargs.pop("scene_id", str(uuid.uuid4()))

        if await self._storage.exists(scene_id):
            raise SceneAlreadyExistsError(scene_id)

        scene = Scene.create(
            tenant_id=tenant_id,
            name=name,
            description=description,
            scene_id=scene_id,
            **kwargs
        )

        await self._storage.save(scene)
        self._cache[scene_id] = scene
        return scene

    async def get_scene(self, scene_id: str) -> Scene:
        """获取场景"""
        if scene_id in self._cache:
            return self._cache[scene_id]

        scene = await self._storage.load(scene_id)
        if not scene:
            raise SceneNotFoundError(scene_id)

        self._cache[scene_id] = scene
        return scene

    async def get_scenes_by_tenant(self, tenant_id: str) -> List[Scene]:
        """获取租户的所有场景"""
        all_scenes = await self._storage.list_all()
        return [
            scene for scene in all_scenes
            if scene.tenant_id == tenant_id
        ]

    async def update_scene(self, scene_id: str, config: SceneConfig) -> Scene:
        """更新场景配置"""
        scene = await self.get_scene(scene_id)
        scene.config = config
        scene.updated_at = time.time()
        await self._storage.save(scene)
        self._cache[scene_id] = scene
        return scene

    async def delete_scene(self, scene_id: str):
        """删除场景"""
        if not await self._storage.exists(scene_id):
            raise SceneNotFoundError(scene_id)

        await self._storage.delete(scene_id)
        self._cache.pop(scene_id, None)

    async def list_scenes(
        self,
        tenant_id: Optional[str] = None,
        status: Optional[SceneStatus] = None,
        offset: int = 0,
        limit: int = 100
    ) -> List[Scene]:
        """列场景表"""
        scenes = await self._storage.list_all()

        if tenant_id:
            scenes = [scene for scene in scenes if scene.tenant_id == tenant_id]
        if status:
            scenes = [scene for scene in scenes if scene.config.status == status]

        return scenes[offset:offset + limit]

    async def enable_scene(self, scene_id: str) -> Scene:
        """启用场景"""
        scene = await self.get_scene(scene_id)
        scene.config.status = SceneStatus.ACTIVE
        scene.updated_at = time.time()
        await self._storage.save(scene)
        self._cache[scene_id] = scene
        return scene

    async def disable_scene(self, scene_id: str) -> Scene:
        """禁用场景"""
        scene = await self.get_scene(scene_id)
        scene.config.status = SceneStatus.INACTIVE
        scene.updated_at = time.time()
        await self._storage.save(scene)
        self._cache[scene_id] = scene
        return scene

    async def archive_scene(self, scene_id: str) -> Scene:
        """归档场景"""
        scene = await self.get_scene(scene_id)
        scene.config.status = SceneStatus.ARCHIVED
        scene.updated_at = time.time()
        await self._storage.save(scene)
        self._cache[scene_id] = scene
        return scene

    async def update_skills(
        self,
        scene_id: str,
        enabled_skills: List[str],
        disabled_skills: List[str]
    ) -> Scene:
        """更新技能配置"""
        scene = await self.get_scene(scene_id)
        scene.config.enabled_skills = enabled_skills
        scene.config.disabled_skills = disabled_skills
        scene.updated_at = time.time()
        await self._storage.save(scene)
        self._cache[scene_id] = scene
        return scene

    def get_cached_scene(self, scene_id: str) -> Optional[Scene]:
        """从缓存获取场景"""
        return self._cache.get(scene_id)


# 预定义场景配置
PREDEFINED_SCENES = {
    "health": SceneConfig(
        name="健康分析场景",
        description="用于健康报告分析和健康风险评估",
        default_skills=["parse_report", "assess_risk", "generate_advice"],
        custom_settings={
            "temperature": 0.1,
            "max_tokens": 2000,
            "enable_streaming": True,
        },
        metadata={
            "category": "health",
            "industry": "healthcare",
            "version": "1.0.0",
        },
    ),
    "ecommerce_recommendation": SceneConfig(
        name="电商推荐场景",
        description="智能导购和产品推荐",
        default_skills=["product_search", "recommendation", "demand_analysis"],
        custom_settings={
            "temperature": 0.7,
            "max_tokens": 3000,
            "enable_personalization": True,
        },
        metadata={
            "category": "ecommerce",
            "industry": "retail",
            "version": "1.0.0",
        },
    ),
    "ecommerce_support": SceneConfig(
        name="电商售后场景",
        description="订单查询、退换货处理",
        default_skills=["order_query", "refund_processing", "policy_validation"],
        custom_settings={
            "temperature": 0.2,
            "max_tokens": 1500,
            "enable_webhook": True,
        },
        metadata={
            "category": "ecommerce",
            "industry": "retail",
            "version": "1.0.0",
        },
    ),
    "financial_analysis": SceneConfig(
        name="财务分析场景",
        description="财务报告分析和投资建议",
        default_skills=["parse_financial_report", "analyze_financial_data", "generate_report"],
        custom_settings={
            "temperature": 0.1,
            "max_tokens": 4000,
            "enable_advanced_analysis": False,
        },
        metadata={
            "category": "finance",
            "industry": "finance",
            "version": "1.0.0",
        },
    ),
}


class PredefinedSceneManager:
    """预定义场景管理器"""

    @classmethod
    def get_predefined_scene(cls, scene_type: str) -> SceneConfig:
        """获取预定义场景配置"""
        if scene_type not in PREDEFINED_SCENES:
            raise SceneNotFoundError(f"Predefined scene '{scene_type}' not found")
        return PREDEFINED_SCENES[scene_type]

    @classmethod
    def list_predefined_scenes(cls) -> List[SceneConfig]:
        """列出所有预定义场景"""
        return list(PREDEFINED_SCENES.values())

    @classmethod
    def is_predefined_scene(cls, scene_type: str) -> bool:
        """检查是否是预定义场景"""
        return scene_type in PREDEFINED_SCENES
