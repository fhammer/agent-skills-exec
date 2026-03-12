"""
多租户与多场景管理模块

提供租户、场景、会话的完整管理功能
"""

from .tenant import (
    Tenant,
    TenantManager,
    TenantConfig,
    TenantStatus,
    SubscriptionPlan,
    RateLimitConfig,
    TenantFeatureFlags,
    TenantUsage,
)
from .scene import (
    Scene,
    SceneManager,
    SceneConfig,
    SceneStatus,
    PredefinedSceneManager,
    PREDEFINED_SCENES,
)
from .session import (
    TenantSession,
    SessionManager,
    SessionStatus,
    MessageRole,
    Message,
    SessionContext,
)
from .storage import (
    TenantStorage,
    SceneStorage,
    SessionStorage,
    InMemoryTenantStorage,
    InMemorySceneStorage,
    InMemorySessionStorage,
    FileBasedTenantStorage,
    FileBasedSceneStorage,
    FileBasedSessionStorage,
)
from .exceptions import (
    TenantError,
    TenantNotFoundError,
    TenantAlreadyExistsError,
    TenantDisabledError,
    SceneError,
    SceneNotFoundError,
    SceneAlreadyExistsError,
    SessionError,
    SessionNotFoundError,
    RateLimitExceededError,
)

__all__ = [
    # Tenant
    "Tenant",
    "TenantManager",
    "TenantConfig",
    "TenantStatus",
    "SubscriptionPlan",
    "RateLimitConfig",
    "TenantFeatureFlags",
    "TenantUsage",
    # Scene
    "Scene",
    "SceneManager",
    "SceneConfig",
    "SceneStatus",
    "PredefinedSceneManager",
    "PREDEFINED_SCENES",
    # Session
    "TenantSession",
    "SessionManager",
    "SessionStatus",
    "MessageRole",
    "Message",
    "SessionContext",
    # Storage
    "TenantStorage",
    "SceneStorage",
    "SessionStorage",
    "InMemoryTenantStorage",
    "InMemorySceneStorage",
    "InMemorySessionStorage",
    "FileBasedTenantStorage",
    "FileBasedSceneStorage",
    "FileBasedSessionStorage",
    # Exceptions
    "TenantError",
    "TenantNotFoundError",
    "TenantAlreadyExistsError",
    "TenantDisabledError",
    "SceneError",
    "SceneNotFoundError",
    "SceneAlreadyExistsError",
    "SessionError",
    "SessionNotFoundError",
    "RateLimitExceededError",
]
