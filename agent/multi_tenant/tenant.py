"""
租户管理模块

提供租户数据模型和管理器
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List
import time
import uuid

from .exceptions import (
    TenantNotFoundError,
    TenantAlreadyExistsError,
    TenantDisabledError,
    RateLimitExceededError,
)


class TenantStatus(Enum):
    """租户状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class SubscriptionPlan(Enum):
    """订阅计划枚举"""
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


@dataclass
class RateLimitConfig:
    """速率限制配置"""
    requests_per_minute: int = 100
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    tokens_per_day: int = 1000000
    max_concurrent_sessions: int = 10

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "requests_per_minute": self.requests_per_minute,
            "requests_per_hour": self.requests_per_hour,
            "requests_per_day": self.requests_per_day,
            "tokens_per_day": self.tokens_per_day,
            "max_concurrent_sessions": self.max_concurrent_sessions,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RateLimitConfig":
        """从字典创建"""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class TenantFeatureFlags:
    """租户功能开关"""
    enable_advanced_skills: bool = False
    enable_custom_skills: bool = False
    enable_streaming: bool = True
    enable_webhook: bool = False
    enable_analytics: bool = True
    enable_priority_support: bool = False
    enable_sla_guarantee: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "enable_advanced_skills": self.enable_advanced_skills,
            "enable_custom_skills": self.enable_custom_skills,
            "enable_streaming": self.enable_streaming,
            "enable_webhook": self.enable_webhook,
            "enable_analytics": self.enable_analytics,
            "enable_priority_support": self.enable_priority_support,
            "enable_sla_guarantee": self.enable_sla_guarantee,
        }


@dataclass
class TenantConfig:
    """租户配置"""
    name: str
    plan: SubscriptionPlan = SubscriptionPlan.FREE
    status: TenantStatus = TenantStatus.ACTIVE
    default_model: str = "glm-4.7"
    default_provider: str = "zhipu"
    rate_limits: RateLimitConfig = field(default_factory=RateLimitConfig)
    features: TenantFeatureFlags = field(default_factory=TenantFeatureFlags)
    custom_settings: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # 计划默认配置
    _PLAN_DEFAULTS = {
        SubscriptionPlan.FREE: {
            "rate_limits": RateLimitConfig(
                requests_per_minute=10,
                requests_per_hour=100,
                requests_per_day=1000,
                tokens_per_day=100000,
                max_concurrent_sessions=2,
            ),
            "features": TenantFeatureFlags(
                enable_advanced_skills=False,
                enable_custom_skills=False,
                enable_streaming=False,
                enable_webhook=False,
                enable_analytics=True,
                enable_priority_support=False,
                enable_sla_guarantee=False,
            ),
        },
        SubscriptionPlan.BASIC: {
            "rate_limits": RateLimitConfig(
                requests_per_minute=50,
                requests_per_hour=500,
                requests_per_day=5000,
                tokens_per_day=500000,
                max_concurrent_sessions=5,
            ),
            "features": TenantFeatureFlags(
                enable_advanced_skills=True,
                enable_custom_skills=False,
                enable_streaming=True,
                enable_webhook=False,
                enable_analytics=True,
                enable_priority_support=False,
                enable_sla_guarantee=False,
            ),
        },
        SubscriptionPlan.PRO: {
            "rate_limits": RateLimitConfig(
                requests_per_minute=200,
                requests_per_hour=2000,
                requests_per_day=20000,
                tokens_per_day=2000000,
                max_concurrent_sessions=20,
            ),
            "features": TenantFeatureFlags(
                enable_advanced_skills=True,
                enable_custom_skills=True,
                enable_streaming=True,
                enable_webhook=True,
                enable_analytics=True,
                enable_priority_support=True,
                enable_sla_guarantee=False,
            ),
        },
        SubscriptionPlan.ENTERPRISE: {
            "rate_limits": RateLimitConfig(
                requests_per_minute=1000,
                requests_per_hour=10000,
                requests_per_day=100000,
                tokens_per_day=10000000,
                max_concurrent_sessions=100,
            ),
            "features": TenantFeatureFlags(
                enable_advanced_skills=True,
                enable_custom_skills=True,
                enable_streaming=True,
                enable_webhook=True,
                enable_analytics=True,
                enable_priority_support=True,
                enable_sla_guarantee=True,
            ),
        },
    }

    def __post_init__(self):
        """初始化后应用计划默认配置"""
        if self.plan in self._PLAN_DEFAULTS:
            defaults = self._PLAN_DEFAULTS[self.plan]
            if not hasattr(self, "rate_limits") or self.rate_limits is None:
                self.rate_limits = defaults["rate_limits"]
            if not hasattr(self, "features") or self.features is None:
                self.features = defaults["features"]

    @classmethod
    def from_plan(cls, name: str, plan: SubscriptionPlan, **kwargs) -> "TenantConfig":
        """从订阅计划创建配置"""
        defaults = cls._PLAN_DEFAULTS.get(plan, {})
        return cls(
            name=name,
            plan=plan,
            rate_limits=kwargs.pop("rate_limits", defaults.get("rate_limits", RateLimitConfig())),
            features=kwargs.pop("features", defaults.get("features", TenantFeatureFlags())),
            **kwargs
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "plan": self.plan.value,
            "status": self.status.value,
            "default_model": self.default_model,
            "default_provider": self.default_provider,
            "rate_limits": self.rate_limits.to_dict(),
            "features": self.features.to_dict(),
            "custom_settings": self.custom_settings,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TenantConfig":
        """从字典创建"""
        data = data.copy()
        if "plan" in data and isinstance(data["plan"], str):
            data["plan"] = SubscriptionPlan(data["plan"])
        if "status" in data and isinstance(data["status"], str):
            data["status"] = TenantStatus(data["status"])
        if "rate_limits" in data and isinstance(data["rate_limits"], dict):
            data["rate_limits"] = RateLimitConfig.from_dict(data["rate_limits"])
        if "features" in data and isinstance(data["features"], dict):
            features = TenantFeatureFlags()
            for key, value in data["features"].items():
                if hasattr(features, key):
                    setattr(features, key, value)
            data["features"] = features
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class TenantUsage:
    """租户使用统计"""
    tenant_id: str
    requests_minute: int = 0
    requests_hour: int = 0
    requests_day: int = 0
    tokens_day: int = 0
    current_sessions: int = 0
    total_requests: int = 0
    total_tokens: int = 0
    last_reset_minute: float = field(default_factory=time.time)
    last_reset_hour: float = field(default_factory=time.time)
    last_reset_day: float = field(default_factory=time.time)

    def reset_minute(self):
        """重置分钟计数"""
        self.requests_minute = 0
        self.last_reset_minute = time.time()

    def reset_hour(self):
        """重置小时计数"""
        self.requests_hour = 0
        self.last_reset_hour = time.time()

    def reset_day(self):
        """重置天计数"""
        self.requests_day = 0
        self.tokens_day = 0
        self.last_reset_day = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "tenant_id": self.tenant_id,
            "requests_minute": self.requests_minute,
            "requests_hour": self.requests_hour,
            "requests_day": self.requests_day,
            "tokens_day": self.tokens_day,
            "current_sessions": self.current_sessions,
            "total_requests": self.total_requests,
            "total_tokens": self.total_tokens,
            "last_reset_minute": self.last_reset_minute,
            "last_reset_hour": self.last_reset_hour,
            "last_reset_day": self.last_reset_day,
        }


@dataclass
class Tenant:
    """租户数据模型"""
    tenant_id: str
    config: TenantConfig
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    usage: TenantUsage = field(init=False)

    def __post_init__(self):
        """初始化使用统计"""
        self.usage = TenantUsage(tenant_id=self.tenant_id)

    @property
    def is_active(self) -> bool:
        """是否活跃"""
        return self.config.status == TenantStatus.ACTIVE

    @property
    def is_suspended(self) -> bool:
        """是否被暂停"""
        return self.config.status == TenantStatus.SUSPENDED

    def check_rate_limit(self, limit_type: str, amount: int = 1) -> bool:
        """检查速率限制

        Args:
            limit_type: 限制类型 (minute, hour, day, tokens)
            amount: 使用量

        Returns:
            bool: 是否在限制内

        Raises:
            RateLimitExceededError: 当超出限制时
        """
        now = time.time()

        # 自动重置过期的计数
        if now - self.usage.last_reset_minute >= 60:
            self.usage.reset_minute()
        if now - self.usage.last_reset_hour >= 3600:
            self.usage.reset_hour()
        if now - self.usage.last_reset_day >= 86400:
            self.usage.reset_day()

        limits = self.config.rate_limits

        if limit_type == "minute":
            if self.usage.requests_minute + amount > limits.requests_per_minute:
                raise RateLimitExceededError(
                    self.tenant_id, "minute",
                    self.usage.requests_minute, limits.requests_per_minute
                )
            self.usage.requests_minute += amount
        elif limit_type == "hour":
            if self.usage.requests_hour + amount > limits.requests_per_hour:
                raise RateLimitExceededError(
                    self.tenant_id, "hour",
                    self.usage.requests_hour, limits.requests_per_hour
                )
            self.usage.requests_hour += amount
        elif limit_type == "day":
            if self.usage.requests_day + amount > limits.requests_per_day:
                raise RateLimitExceededError(
                    self.tenant_id, "day",
                    self.usage.requests_day, limits.requests_per_day
                )
            self.usage.requests_day += amount
        elif limit_type == "tokens":
            if self.usage.tokens_day + amount > limits.tokens_per_day:
                raise RateLimitExceededError(
                    self.tenant_id, "tokens",
                    self.usage.tokens_day, limits.tokens_per_day
                )
            self.usage.tokens_day += amount

        self.usage.total_requests += amount
        return True

    def record_tokens(self, tokens: int):
        """记录Token使用"""
        self.usage.tokens_day += tokens
        self.usage.total_tokens += tokens

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "tenant_id": self.tenant_id,
            "config": self.config.to_dict(),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "usage": self.usage.to_dict(),
        }

    @classmethod
    def create(cls, name: str, plan: SubscriptionPlan = SubscriptionPlan.FREE, **kwargs) -> "Tenant":
        """创建新租户"""
        tenant_id = kwargs.pop("tenant_id", str(uuid.uuid4()))
        config = TenantConfig.from_plan(name, plan, **kwargs)
        return cls(tenant_id=tenant_id, config=config)


class TenantManager:
    """租户管理器

    负责租户的生命周期管理
    """

    def __init__(self, storage: Optional["TenantStorage"] = None):
        """初始化租户管理器

        Args:
            storage: 租户存储实现，None则使用内存存储
        """
        from .storage import TenantStorage, InMemoryTenantStorage

        self._storage: TenantStorage = storage or InMemoryTenantStorage()
        self._cache: Dict[str, Tenant] = {}

    async def initialize(self):
        """初始化管理器"""
        # 从存储加载所有租户到缓存
        for tenant in await self._storage.list_all():
            self._cache[tenant.tenant_id] = tenant

    async def create_tenant(
        self,
        name: str,
        plan: SubscriptionPlan = SubscriptionPlan.FREE,
        **kwargs
    ) -> Tenant:
        """创建租户

        Args:
            name: 租户名称
            plan: 订阅计划
            **kwargs: 其他参数

        Returns:
            Tenant: 创建的租户

        Raises:
            TenantAlreadyExistsError: 租户已存在
        """
        tenant_id = kwargs.pop("tenant_id", str(uuid.uuid4()))

        if await self._storage.exists(tenant_id):
            raise TenantAlreadyExistsError(tenant_id)

        tenant = Tenant.create(name, plan, tenant_id=tenant_id, **kwargs)
        await self._storage.save(tenant)
        self._cache[tenant_id] = tenant
        return tenant

    async def get_tenant(self, tenant_id: str) -> Tenant:
        """获取租户

        Args:
            tenant_id: 租户ID

        Returns:
            Tenant: 租户对象

        Raises:
            TenantNotFoundError: 租户不存在
        """
        # 先查缓存
        if tenant_id in self._cache:
            return self._cache[tenant_id]

        # 再查存储
        tenant = await self._storage.load(tenant_id)
        if not tenant:
            raise TenantNotFoundError(tenant_id)

        self._cache[tenant_id] = tenant
        return tenant

    async def update_tenant(self, tenant_id: str, config: TenantConfig) -> Tenant:
        """更新租户配置

        Args:
            tenant_id: 租户ID
            config: 新的配置

        Returns:
            Tenant: 更新后的租户

        Raises:
            TenantNotFoundError: 租户不存在
        """
        tenant = await self.get_tenant(tenant_id)
        tenant.config = config
        tenant.updated_at = time.time()
        await self._storage.save(tenant)
        self._cache[tenant_id] = tenant
        return tenant

    async def delete_tenant(self, tenant_id: str):
        """删除租户

        Args:
            tenant_id: 租户ID

        Raises:
            TenantNotFoundError: 租户不存在
        """
        if not await self._storage.exists(tenant_id):
            raise TenantNotFoundError(tenant_id)

        await self._storage.delete(tenant_id)
        self._cache.pop(tenant_id, None)

    async def list_tenants(
        self,
        status: Optional[TenantStatus] = None,
        plan: Optional[SubscriptionPlan] = None,
        offset: int = 0,
        limit: int = 100
    ) -> List[Tenant]:
        """列出租户

        Args:
            status: 状态过滤
            plan: 订阅计划过滤
            offset: 偏移量
            limit: 限制数量

        Returns:
            List[Tenant]: 租户列表
        """
        tenants = await self._storage.list_all()

        if status:
            tenants = [t for t in tenants if t.config.status == status]
        if plan:
            tenants = [t for t in tenants if t.config.plan == plan]

        return tenants[offset:offset + limit]

    async def enable_tenant(self, tenant_id: str) -> Tenant:
        """启用租户

        Args:
            tenant_id: 租户ID

        Returns:
            Tenant: 更新后的租户
        """
        tenant = await self.get_tenant(tenant_id)
        tenant.config.status = TenantStatus.ACTIVE
        tenant.updated_at = time.time()
        await self._storage.save(tenant)
        self._cache[tenant_id] = tenant
        return tenant

    async def disable_tenant(self, tenant_id: str) -> Tenant:
        """禁用租户

        Args:
            tenant_id: 租户ID

        Returns:
            Tenant: 更新后的租户
        """
        tenant = await self.get_tenant(tenant_id)
        tenant.config.status = TenantStatus.INACTIVE
        tenant.updated_at = time.time()
        await self._storage.save(tenant)
        self._cache[tenant_id] = tenant
        return tenant

    async def suspend_tenant(self, tenant_id: str) -> Tenant:
        """暂停租户

        Args:
            tenant_id: 租户ID

        Returns:
            Tenant: 更新后的租户
        """
        tenant = await self.get_tenant(tenant_id)
        tenant.config.status = TenantStatus.SUSPENDED
        tenant.updated_at = time.time()
        await self._storage.save(tenant)
        self._cache[tenant_id] = tenant
        return tenant

    async def check_tenant_access(self, tenant_id: str) -> Tenant:
        """检查租户访问权限

        Args:
            tenant_id: 租户ID

        Returns:
            Tenant: 租户对象

        Raises:
            TenantNotFoundError: 租户不存在
            TenantDisabledError: 租户已禁用
        """
        tenant = await self.get_tenant(tenant_id)

        if not tenant.is_active:
            raise TenantDisabledError(tenant_id)

        return tenant

    async def record_request(self, tenant_id: str, tokens: int = 0) -> Tenant:
        """记录请求

        Args:
            tenant_id: 租户ID
            tokens: 使用的token数量

        Returns:
            Tenant: 更新后的租户
        """
        tenant = await self.check_tenant_access(tenant_id)

        # 检查速率限制
        tenant.check_rate_limit("minute")
        tenant.check_rate_limit("hour")
        tenant.check_rate_limit("day")

        if tokens > 0:
            tenant.record_tokens(tokens)

        tenant.updated_at = time.time()
        await self._storage.save(tenant)
        return tenant

    def get_cached_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """从缓存获取租户（不查询存储）

        Args:
            tenant_id: 租户ID

        Returns:
            Optional[Tenant]: 租户对象或None
        """
        return self._cache.get(tenant_id)
