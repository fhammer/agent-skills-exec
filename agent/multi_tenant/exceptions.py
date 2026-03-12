"""
多租户模块异常定义
"""


class TenantError(Exception):
    """租户相关错误的基类"""

    def __init__(self, message: str, tenant_id: str = None):
        self.tenant_id = tenant_id
        super().__init__(message)


class TenantNotFoundError(TenantError):
    """租户不存在错误"""

    def __init__(self, tenant_id: str):
        super().__init__(f"Tenant not found: {tenant_id}", tenant_id)


class TenantAlreadyExistsError(TenantError):
    """租户已存在错误"""

    def __init__(self, tenant_id: str):
        super().__init__(f"Tenant already exists: {tenant_id}", tenant_id)


class TenantDisabledError(TenantError):
    """租户已禁用错误"""

    def __init__(self, tenant_id: str):
        super().__init__(f"Tenant is disabled: {tenant_id}", tenant_id)


class SceneError(Exception):
    """场景相关错误的基类"""

    def __init__(self, message: str, scene_id: str = None):
        self.scene_id = scene_id
        super().__init__(message)


class SceneNotFoundError(SceneError):
    """场景不存在错误"""

    def __init__(self, scene_id: str):
        super().__init__(f"Scene not found: {scene_id}", scene_id)


class SceneAlreadyExistsError(SceneError):
    """场景已存在错误"""

    def __init__(self, scene_id: str):
        super().__init__(f"Scene already exists: {scene_id}", scene_id)


class SessionError(Exception):
    """会话相关错误的基类"""

    def __init__(self, message: str, session_id: str = None):
        self.session_id = session_id
        super().__init__(message)


class SessionNotFoundError(SessionError):
    """会话不存在错误"""

    def __init__(self, session_id: str):
        super().__init__(f"Session not found: {session_id}", session_id)


class RateLimitExceededError(TenantError):
    """速率限制超限错误"""

    def __init__(self, tenant_id: str, limit_type: str, current: int, limit: int):
        message = f"Rate limit exceeded for {tenant_id}: {limit_type} (current: {current}, limit: {limit})"
        super().__init__(message, tenant_id)
        self.limit_type = limit_type
        self.current = current
        self.limit = limit
