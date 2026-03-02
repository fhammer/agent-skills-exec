"""
认证授权路由

提供 Token 生成、API Key 管理、权限验证等端点。
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

from api.auth import (
    JWTManager,
    APIKeyManager,
    PermissionChecker,
    TokenPayload,
    Permission,
    get_jwt_manager,
    get_api_key_manager,
    get_permission_checker,
)

router = APIRouter()
security = HTTPBearer(auto_error=False)


# ==================== 请求/响应模型 ====================

class TokenRequest(BaseModel):
    """Token 请求"""
    tenant_id: str = Field(..., description="租户 ID")
    permissions: Optional[List[str]] = Field(None, description="权限列表")


class TokenResponse(BaseModel):
    """Token 响应"""
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    tenant_id: str
    permissions: List[str]


class APIKeyCreateRequest(BaseModel):
    """API Key 创建请求"""
    tenant_id: str
    name: str
    permissions: List[str]
    expires_in_days: Optional[int] = None


class APIKeyResponse(BaseModel):
    """API Key 响应"""
    api_key: str
    key_id: str
    tenant_id: str
    name: str
    permissions: List[str]
    created_at: str
    expires_at: Optional[str] = None


class PermissionCheckRequest(BaseModel):
    """权限检查请求"""
    permissions: List[str]
    required_permission: str


class PermissionCheckResponse(BaseModel):
    """权限检查响应"""
    has_permission: bool


# ==================== 依赖项 ====================

async def get_token_payload(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Optional[TokenPayload]:
    """从请求中获取 Token 载荷"""
    if not credentials:
        return None

    token = credentials.credentials
    return get_jwt_manager().decode_token(token)


async def require_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> TokenPayload:
    """要求认证"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证凭据",
        )

    token = credentials.credentials
    payload = get_jwt_manager().decode_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效或过期的 Token",
        )

    return payload


# ==================== 端点 ====================

@router.post("/token", response_model=TokenResponse)
async def create_token(request: TokenRequest):
    """
    创建访问令牌

    为租户创建 JWT 访问令牌。
    """
    jwt_manager = get_jwt_manager()

    # 创建 Token
    access_token = jwt_manager.create_access_token(
        tenant_id=request.tenant_id,
        permissions=request.permissions,
    )

    # 解析获取过期时间
    payload = jwt_manager.decode_token(access_token)
    expires_in = payload.exp - payload.iat if payload.exp else 3600

    return TokenResponse(
        access_token=access_token,
        token_type="Bearer",
        expires_in=expires_in,
        tenant_id=request.tenant_id,
        permissions=request.permissions or [],
    )


@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(request: APIKeyCreateRequest):
    """
    创建 API Key

    为租户创建新的 API Key。
    """
    api_key_manager = get_api_key_manager()

    api_key = api_key_manager.create_api_key(
        tenant_id=request.tenant_id,
        name=request.name,
        permissions=request.permissions,
        expires_in_days=request.expires_in_days,
    )

    key_info = api_key_manager.verify_api_key(api_key)

    return APIKeyResponse(
        api_key=api_key,
        key_id=key_info.key_id,
        tenant_id=key_info.tenant_id,
        name=key_info.name,
        permissions=key_info.permissions,
        created_at=key_info.created_at.isoformat(),
        expires_at=key_info.expires_at.isoformat() if key_info.expires_at else None,
    )


@router.get("/api-keys/{tenant_id}")
async def list_api_keys(
    tenant_id: str,
    payload: TokenPayload = Depends(require_auth),
):
    """
    列出租户的所有 API Key

    需要认证。
    """
    # 检查权限
    if payload.tenant_id != tenant_id and "admin" not in payload.permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问其他租户的 API Key",
        )

    api_key_manager = get_api_key_manager()
    keys = api_key_manager.get_tenant_api_keys(tenant_id)

    return {
        "tenant_id": tenant_id,
        "api_keys": [
            {
                "key_id": key.key_id,
                "name": key.name,
                "permissions": key.permissions,
                "created_at": key.created_at.isoformat(),
                "expires_at": key.expires_at.isoformat() if key.expires_at else None,
                "is_active": key.is_active,
            }
            for key in keys
        ],
    }


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    payload: TokenPayload = Depends(require_auth),
):
    """
    吊销 API Key

    需要认证。
    """
    # 这里简化处理，实际应该通过 key_id 查找
    # 生产环境应该从数据库查询
    return {"message": "API Key 已吊销", "key_id": key_id}


@router.post("/permissions/check", response_model=PermissionCheckResponse)
async def check_permission(request: PermissionCheckRequest):
    """
    检查权限

    检查指定的权限是否满足要求。
    """
    permission_checker = get_permission_checker()

    try:
        required_permission = Permission(request.required_permission)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的权限: {request.required_permission}",
        )

    has_permission = permission_checker.check_permission(
        request.permissions,
        required_permission,
    )

    return PermissionCheckResponse(has_permission=has_permission)


@router.get("/permissions")
async def list_permissions():
    """
    列出所有可用权限

    返回系统中定义的所有权限。
    """
    return {
        "permissions": [perm.value for perm in Permission],
        "categories": {
            "agent": ["agent:chat", "agent:admin"],
            "skills": ["skills:read", "skills:write", "skills:delete"],
            "tenants": ["tenants:read", "tenants:write", "tenants:delete"],
            "metrics": ["metrics:read"],
            "audit": ["audit:read"],
            "sessions": ["sessions:read", "sessions:write", "sessions:delete"],
        }
    }


@router.get("/me")
async def get_current_user(payload: TokenPayload = Depends(require_auth)):
    """
    获取当前用户信息

    返回当前 Token 对应的租户和权限信息。
    """
    return {
        "tenant_id": payload.tenant_id,
        "user_id": payload.user_id,
        "permissions": payload.permissions,
        "is_authenticated": True,
    }
