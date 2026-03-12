"""租户管理路由 - 使用多租户管理系统"""

from fastapi import APIRouter, HTTPException, Depends, Request, status
from typing import List, Optional
from datetime import datetime

from api.schemas import (
    TenantCreateRequest,
    TenantResponse,
    LLMConfig,
    SceneCreateRequest,
    SceneResponse,
    SessionCreateRequest,
    SessionResponse,
)
from agent.multi_tenant import (
    TenantManager,
    Tenant,
    TenantConfig,
    TenantStatus,
    SubscriptionPlan,
    SceneManager,
    Scene,
    SceneConfig,
    SessionManager,
    TenantSession,
    TenantNotFoundError,
    TenantAlreadyExistsError,
)

# 认证管理器
from api.auth import get_jwt_manager, get_api_key_manager

router = APIRouter()

# 全局管理器实例
_tenant_manager: Optional[TenantManager] = None
_scene_manager: Optional[SceneManager] = None
_session_manager: Optional[SessionManager] = None


def get_tenant_manager() -> TenantManager:
    """获取租户管理器"""
    global _tenant_manager
    if _tenant_manager is None:
        raise RuntimeError("TenantManager not initialized")
    return _tenant_manager


def get_scene_manager() -> SceneManager:
    """获取场景管理器"""
    global _scene_manager
    if _scene_manager is None:
        raise RuntimeError("SceneManager not initialized")
    return _scene_manager


def get_session_manager() -> SessionManager:
    """获取会话管理器"""
    global _session_manager
    if _session_manager is None:
        raise RuntimeError("SessionManager not initialized")
    return _session_manager


def init_managers(
    tenant_manager: TenantManager,
    scene_manager: SceneManager,
    session_manager: SessionManager
):
    """初始化管理器"""
    global _tenant_manager, _scene_manager, _session_manager
    _tenant_manager = tenant_manager
    _scene_manager = scene_manager
    _session_manager = session_manager


# ============================================================================
# Tenant Endpoints
# ============================================================================

@router.post("/", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    request: TenantCreateRequest,
):
    """创建租户"""
    tenant_manager = get_tenant_manager()

    try:
        # 转换订阅计划
        plan = SubscriptionPlan(request.plan) if request.plan else SubscriptionPlan.FREE

        # 创建租户
        tenant = await tenant_manager.create_tenant(
            name=request.name,
            plan=plan,
            tenant_id=request.tenant_id,
        )

        # 如果提供了 API Key，创建一个
        api_key = None
        if request.create_api_key:
            api_key = get_api_key_manager().create_api_key(
                tenant_id=tenant.tenant_id,
                name="default",
                permissions=["admin"],
                expires_in_days=365,
            )

        # 创建 JWT Token
        jwt_token = get_jwt_manager().create_access_token(
            tenant_id=tenant.tenant_id,
            permissions=["admin"],
        )

        return TenantResponse(
            tenant_id=tenant.tenant_id,
            name=tenant.config.name,
            plan=tenant.config.plan.value,
            status=tenant.config.status.value,
            api_key=api_key,
            jwt_token=jwt_token,
            created_at=datetime.fromtimestamp(tenant.created_at).isoformat(),
        )

    except TenantAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tenant with id '{request.tenant_id}' already exists"
        )


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(tenant_id: str):
    """获取租户信息"""
    tenant_manager = get_tenant_manager()

    try:
        tenant = await tenant_manager.get_tenant(tenant_id)
        return TenantResponse(
            tenant_id=tenant.tenant_id,
            name=tenant.config.name,
            plan=tenant.config.plan.value,
            status=tenant.config.status.value,
            created_at=datetime.fromtimestamp(tenant.created_at).isoformat(),
            features=tenant.config.features.to_dict(),
            rate_limits=tenant.config.rate_limits.to_dict(),
        )
    except TenantNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant not found: {tenant_id}"
        )


@router.get("/", response_model=List[TenantResponse])
async def list_tenants(
    status: Optional[str] = None,
    plan: Optional[str] = None,
    offset: int = 0,
    limit: int = 100,
):
    """列出所有租户"""
    tenant_manager = get_tenant_manager()

    status_filter = TenantStatus(status) if status else None
    plan_filter = SubscriptionPlan(plan) if plan else None

    tenants = await tenant_manager.list_tenants(
        status=status_filter,
        plan=plan_filter,
        offset=offset,
        limit=limit,
    )

    return [
        TenantResponse(
            tenant_id=t.tenant_id,
            name=t.config.name,
            plan=t.config.plan.value,
            status=t.config.status.value,
            created_at=datetime.fromtimestamp(t.created_at).isoformat(),
        )
        for t in tenants
    ]


@router.put("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: str,
    request: TenantCreateRequest,
):
    """更新租户配置"""
    tenant_manager = get_tenant_manager()

    try:
        tenant = await tenant_manager.get_tenant(tenant_id)

        # 更新配置
        new_config = tenant.config
        if request.name:
            new_config.name = request.name
        if request.plan:
            new_config.plan = SubscriptionPlan(request.plan)

        updated = await tenant_manager.update_tenant(tenant_id, new_config)

        return TenantResponse(
            tenant_id=updated.tenant_id,
            name=updated.config.name,
            plan=updated.config.plan.value,
            status=updated.config.status.value,
            created_at=datetime.fromtimestamp(updated.created_at).isoformat(),
        )
    except TenantNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant not found: {tenant_id}"
        )


@router.delete("/{tenant_id}")
async def delete_tenant(tenant_id: str):
    """删除租户"""
    tenant_manager = get_tenant_manager()

    try:
        await tenant_manager.delete_tenant(tenant_id)
        return {"deleted": True, "tenant_id": tenant_id}
    except TenantNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant not found: {tenant_id}"
        )


@router.post("/{tenant_id}/enable")
async def enable_tenant(tenant_id: str):
    """启用租户"""
    tenant_manager = get_tenant_manager()

    try:
        tenant = await tenant_manager.enable_tenant(tenant_id)
        return {
            "tenant_id": tenant.tenant_id,
            "status": tenant.config.status.value,
            "enabled": True
        }
    except TenantNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant not found: {tenant_id}"
        )


@router.post("/{tenant_id}/disable")
async def disable_tenant(tenant_id: str):
    """禁用租户"""
    tenant_manager = get_tenant_manager()

    try:
        tenant = await tenant_manager.disable_tenant(tenant_id)
        return {
            "tenant_id": tenant.tenant_id,
            "status": tenant.config.status.value,
            "enabled": False
        }
    except TenantNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant not found: {tenant_id}"
        )


@router.post("/{tenant_id}/regenerate-api-key")
async def regenerate_api_key(
    tenant_id: str,
    name: str = "new-key",
    expires_in_days: int = 365,
):
    """重新生成 API Key"""
    tenant_manager = get_tenant_manager()

    try:
        await tenant_manager.get_tenant(tenant_id)

        api_key = get_api_key_manager().create_api_key(
            tenant_id=tenant_id,
            name=name,
            permissions=["admin"],
            expires_in_days=expires_in_days,
        )

        return {"api_key": api_key, "tenant_id": tenant_id}
    except TenantNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant not found: {tenant_id}"
        )


@router.get("/{tenant_id}/usage")
async def get_tenant_usage(tenant_id: str):
    """获取租户使用统计"""
    tenant_manager = get_tenant_manager()

    try:
        tenant = await tenant_manager.get_tenant(tenant_id)
        return {
            "tenant_id": tenant.tenant_id,
            "usage": tenant.usage.to_dict(),
        }
    except TenantNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant not found: {tenant_id}"
        )


# ============================================================================
# Scene Endpoints
# ============================================================================

@router.post("/{tenant_id}/scenes", response_model=SceneResponse, status_code=status.HTTP_201_CREATED)
async def create_scene(
    tenant_id: str,
    request: SceneCreateRequest,
):
    """为租户创建场景"""
    tenant_manager = get_tenant_manager()
    scene_manager = get_scene_manager()

    try:
        # 验证租户存在
        await tenant_manager.get_tenant(tenant_id)

        scene = await scene_manager.create_scene(
            tenant_id=tenant_id,
            name=request.name,
            description=request.description or "",
            default_skills=request.default_skills or [],
            enabled_skills=request.enabled_skills or [],
        )

        return SceneResponse(
            scene_id=scene.scene_id,
            tenant_id=scene.tenant_id,
            name=scene.config.name,
            description=scene.config.description,
            status=scene.config.status.value,
            available_skills=scene.available_skills,
            created_at=datetime.fromtimestamp(scene.created_at).isoformat(),
        )
    except TenantNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant not found: {tenant_id}"
        )


@router.get("/{tenant_id}/scenes", response_model=List[SceneResponse])
async def list_scenes(tenant_id: str):
    """列出租户的所有场景"""
    scene_manager = get_scene_manager()

    scenes = await scene_manager.get_scenes_by_tenant(tenant_id)
    return [
        SceneResponse(
            scene_id=s.scene_id,
            tenant_id=s.tenant_id,
            name=s.config.name,
            description=s.config.description,
            status=s.config.status.value,
            available_skills=s.available_skills,
            created_at=datetime.fromtimestamp(s.created_at).isoformat(),
        )
        for s in scenes
    ]


@router.get("/{tenant_id}/scenes/{scene_id}", response_model=SceneResponse)
async def get_scene(tenant_id: str, scene_id: str):
    """获取场景详情"""
    scene_manager = get_scene_manager()

    try:
        scene = await scene_manager.get_scene(scene_id)

        if scene.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Scene does not belong to this tenant"
            )

        return SceneResponse(
            scene_id=scene.scene_id,
            tenant_id=scene.tenant_id,
            name=scene.config.name,
            description=scene.config.description,
            status=scene.config.status.value,
            available_skills=scene.available_skills,
            created_at=datetime.fromtimestamp(scene.created_at).isoformat(),
        )
    except SceneNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scene not found: {scene_id}"
        )


@router.delete("/{tenant_id}/scenes/{scene_id}")
async def delete_scene(tenant_id: str, scene_id: str):
    """删除场景"""
    scene_manager = get_scene_manager()

    try:
        scene = await scene_manager.get_scene(scene_id)

        if scene.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Scene does not belong to this tenant"
            )

        await scene_manager.delete_scene(scene_id)
        return {"deleted": True, "scene_id": scene_id}
    except SceneNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scene not found: {scene_id}"
        )


# ============================================================================
# Session Endpoints
# ============================================================================

@router.post("/{tenant_id}/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    tenant_id: str,
    request: SessionCreateRequest,
):
    """创建会话"""
    tenant_manager = get_tenant_manager()
    session_manager = get_session_manager()

    try:
        # 验证租户存在
        await tenant_manager.check_tenant_access(tenant_id)

        session = await session_manager.create_session(
            tenant_id=tenant_id,
            scene_id=request.scene_id,
            user_id=request.user_id,
        )

        return SessionResponse(
            session_id=session.session_id,
            tenant_id=session.tenant_id,
            scene_id=session.scene_id,
            user_id=session.user_id,
            status=session.status.value,
            created_at=datetime.fromtimestamp(session.created_at).isoformat(),
            expires_at=datetime.fromtimestamp(session.expires_at).isoformat(),
        )
    except TenantNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant not found: {tenant_id}"
        )
    except TenantDisabledError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Tenant is disabled: {tenant_id}"
        )


@router.get("/{tenant_id}/sessions", response_model=List[SessionResponse])
async def list_sessions(tenant_id: str, user_id: Optional[str] = None):
    """列出租户的所有会话"""
    session_manager = get_session_manager()

    if user_id:
        sessions = await session_manager.get_sessions_by_user(tenant_id, user_id)
    else:
        sessions = await session_manager.get_sessions_by_tenant(tenant_id)

    return [
        SessionResponse(
            session_id=s.session_id,
            tenant_id=s.tenant_id,
            scene_id=s.scene_id,
            user_id=s.user_id,
            status=s.status.value,
            created_at=datetime.fromtimestamp(s.created_at).isoformat(),
            expires_at=datetime.fromtimestamp(s.expires_at).isoformat(),
            total_messages=s.total_messages,
        )
        for s in sessions
    ]


@router.get("/{tenant_id}/sessions/{session_id}", response_model=SessionResponse)
async def get_session(tenant_id: str, session_id: str):
    """获取会话详情"""
    session_manager = get_session_manager()

    try:
        session = await session_manager.get_session(session_id)

        if session.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Session does not belong to this tenant"
            )

        return SessionResponse(
            session_id=session.session_id,
            tenant_id=session.tenant_id,
            scene_id=session.scene_id,
            user_id=session.user_id,
            status=session.status.value,
            created_at=datetime.fromtimestamp(session.created_at).isoformat(),
            expires_at=datetime.fromtimestamp(session.expires_at).isoformat(),
            total_messages=session.total_messages,
            total_tokens=session.total_tokens,
        )
    except SessionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}"
        )


@router.delete("/{tenant_id}/sessions/{session_id}")
async def delete_session(tenant_id: str, session_id: str):
    """删除会话"""
    session_manager = get_session_manager()

    try:
        session = await session_manager.get_session(session_id)

        if session.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Session does not belong to this tenant"
            )

        await session_manager.delete_session(session_id)
        return {"deleted": True, "session_id": session_id}
    except SessionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}"
        )


@router.post("/{tenant_id}/sessions/{session_id}/close")
async def close_session(tenant_id: str, session_id: str):
    """关闭会话"""
    session_manager = get_session_manager()

    try:
        session = await session_manager.get_session(session_id)

        if session.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Session does not belong to this tenant"
            )

        await session_manager.close_session(session_id)
        return {"closed": True, "session_id": session_id, "status": "closed"}
    except SessionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}"
        )
