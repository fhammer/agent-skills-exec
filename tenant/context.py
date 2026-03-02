"""
多租户上下文定义

提供租户和场景的上下文数据结构。
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class TenantStatus(Enum):
    """租户状态"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class SceneStatus(Enum):
    """场景状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


@dataclass
class ResourceQuota:
    """资源配额"""
    token_limit: int = 1000000  # Token预算上限
    token_used: int = 0  # 已使用Token
    qps_limit: int = 100  # 每秒请求数限制
    qps_current: int = 0  # 当前QPS
    storage_limit_mb: int = 1024  # 存储限制（MB）
    storage_used_mb: float = 0.0  # 已使用存储

    def check_token_quota(self, tokens: int) -> bool:
        """检查Token配额"""
        return self.token_used + tokens <= self.token_limit

    def consume_tokens(self, tokens: int) -> bool:
        """消耗Token配额"""
        if self.check_token_quota(tokens):
            self.token_used += tokens
            return True
        return False

    def get_token_usage_percentage(self) -> float:
        """获取Token使用百分比"""
        return (self.token_used / self.token_limit * 100) if self.token_limit > 0 else 0

    def is_near_limit(self, threshold: float = 0.9) -> bool:
        """检查是否接近配额限制"""
        return self.get_token_usage_percentage() >= threshold * 100

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "token_limit": self.token_limit,
            "token_used": self.token_used,
            "token_usage_percentage": self.get_token_usage_percentage(),
            "qps_limit": self.qps_limit,
            "qps_current": self.qps_current,
            "storage_limit_mb": self.storage_limit_mb,
            "storage_used_mb": self.storage_used_mb,
        }


@dataclass
class LLMConfig:
    """LLM配置"""
    provider: str = "anthropic"
    model: str = "glm-4.7"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: int = 30

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（隐藏敏感信息）"""
        return {
            "provider": self.provider,
            "model": self.model,
            "api_key": "***" if self.api_key else None,
            "base_url": self.base_url,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "timeout": self.timeout,
        }


@dataclass
class TenantConfig:
    """租户配置"""
    llm_config: LLMConfig = field(default_factory=LLMConfig)
    skill_whitelist: List[str] = field(default_factory=list)  # 允许使用的Skills
    rate_limit: Dict[str, int] = field(default_factory=lambda: {"requests": 100, "window": 60})
    custom_tools: List[str] = field(default_factory=list)
    enable_audit_log: bool = True
    enable_metrics: bool = True

    def merge_with_scene_config(self, scene_config: "SceneConfig") -> "TenantConfig":
        """与场景配置合并，场景配置优先级更高"""
        merged = TenantConfig(
            llm_config=LLMConfig(
                provider=scene_config.llm_config.provider or self.llm_config.provider,
                model=scene_config.llm_config.model or self.llm_config.model,
                api_key=scene_config.llm_config.api_key or self.llm_config.api_key,
                base_url=scene_config.llm_config.base_url or self.llm_config.base_url,
                temperature=scene_config.llm_config.temperature if scene_config.llm_config.temperature != 0.7 else self.llm_config.temperature,
                max_tokens=scene_config.llm_config.max_tokens if scene_config.llm_config.max_tokens != 4096 else self.llm_config.max_tokens,
                timeout=scene_config.llm_config.timeout if scene_config.llm_config.timeout != 30 else self.llm_config.timeout,
            ),
            skill_whitelist=scene_config.skill_whitelist if scene_config.skill_whitelist else self.skill_whitelist,
            rate_limit=scene_config.rate_limit if scene_config.rate_limit else self.rate_limit,
            custom_tools=scene_config.custom_tools if scene_config.custom_tools else self.custom_tools,
            enable_audit_log=scene_config.enable_audit_log if scene_config.enable_audit_log is not None else self.enable_audit_log,
            enable_metrics=scene_config.enable_metrics if scene_config.enable_metrics is not None else self.enable_metrics,
        )
        return merged


@dataclass
class SceneConfig:
    """场景配置（可覆盖租户配置）"""
    llm_config: LLMConfig = field(default_factory=LLMConfig)
    skill_whitelist: Optional[List[str]] = None
    rate_limit: Optional[Dict[str, int]] = None
    custom_tools: Optional[List[str]] = None
    enable_audit_log: Optional[bool] = None
    enable_metrics: Optional[bool] = None


@dataclass
class SceneContext:
    """场景上下文"""
    scene_id: str
    tenant_id: str
    name: str
    description: str = ""
    config: SceneConfig = field(default_factory=SceneConfig)
    status: SceneStatus = SceneStatus.ACTIVE
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "scene_id": self.scene_id,
            "tenant_id": self.tenant_id,
            "name": self.name,
            "description": self.description,
            "config": {
                "llm_config": self.config.llm_config.to_dict(),
                "skill_whitelist": self.config.skill_whitelist,
                "rate_limit": self.config.rate_limit,
                "custom_tools": self.config.custom_tools,
            },
            "status": self.status.value,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


@dataclass
class TenantContext:
    """租户上下文"""
    tenant_id: str
    name: str
    config: TenantConfig = field(default_factory=TenantConfig)
    resource_quota: ResourceQuota = field(default_factory=ResourceQuota)
    status: TenantStatus = TenantStatus.ACTIVE
    scenes: Dict[str, SceneContext] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def add_scene(self, scene: SceneContext) -> None:
        """添加场景"""
        self.scenes[scene.scene_id] = scene
        self.updated_at = datetime.utcnow()

    def remove_scene(self, scene_id: str) -> bool:
        """移除场景"""
        if scene_id in self.scenes:
            del self.scenes[scene_id]
            self.updated_at = datetime.utcnow()
            return True
        return False

    def get_scene(self, scene_id: str) -> Optional[SceneContext]:
        """获取场景"""
        return self.scenes.get(scene_id)

    def list_scenes(self, status: Optional[SceneStatus] = None) -> List[SceneContext]:
        """列出场景"""
        scenes = list(self.scenes.values())
        if status:
            scenes = [s for s in scenes if s.status == status]
        return scenes

    def get_active_scene_count(self) -> int:
        """获取活跃场景数量"""
        return len([s for s in self.scenes.values() if s.status == SceneStatus.ACTIVE])

    def get_merged_config(self, scene_id: str) -> TenantConfig:
        """获取合并后的配置（租户配置+场景配置）"""
        scene = self.get_scene(scene_id)
        if scene:
            return self.config.merge_with_scene_config(scene.config)
        return self.config

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "tenant_id": self.tenant_id,
            "name": self.name,
            "config": {
                "llm_config": self.config.llm_config.to_dict(),
                "skill_whitelist": self.config.skill_whitelist,
                "rate_limit": self.config.rate_limit,
                "custom_tools": self.config.custom_tools,
                "enable_audit_log": self.config.enable_audit_log,
                "enable_metrics": self.config.enable_metrics,
            },
            "resource_quota": self.resource_quota.to_dict(),
            "status": self.status.value,
            "scene_count": len(self.scenes),
            "active_scene_count": self.get_active_scene_count(),
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
