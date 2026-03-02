"""租户管理路由"""

from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List
import uuid
import secrets
from datetime import datetime

from api.schemas import TenantCreateRequest, TenantResponse, LLMConfig

router = APIRouter()

# 简化的内存存储（生产环境应使用数据库）
_tenants = {}
_tenant_by_key = {}


def generate_api_key():
    """生成 API Key"""
    return f"sk_agent_{secrets.token_urlsafe(32)}"


@router.post("/", response_model=TenantResponse)
async def create_tenant(
    request: TenantCreateRequest,
    req: Request
):
    """创建租户"""
    tenant_id = f"tenant_{uuid.uuid4().hex[:12]}"
    api_key = generate_api_key()

    # 默认 LLM 配置
    llm_config = request.llm_config or LLMConfig(
        provider="anthropic",
        model="glm-4.7",
        api_key="",
        base_url="https://open.bigmodel.cn/api/anthropic"
    )

    tenant = {
        "tenant_id": tenant_id,
        "name": request.name,
        "api_key": api_key,
        "llm_config": llm_config.dict(),
        "skill_whitelist": request.skill_whitelist or [],
        "rate_limit": request.rate_limit or {"requests": 100, "window": 60},
        "custom_tools": [],
        "is_active": True,
        "created_at": datetime.utcnow().isoformat()
    }

    _tenants[tenant_id] = tenant
    _tenant_by_key[api_key] = tenant

    return TenantResponse(**tenant)


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(tenant_id: str):
    """获取租户信息"""
    tenant = _tenants.get(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")
    return TenantResponse(**tenant)


@router.get("/", response_model=List[TenantResponse])
async def list_tenants():
    """列出所有租户"""
    return [TenantResponse(**t) for t in _tenants.values()]


@router.put("/{tenant_id}")
async def update_tenant(
    tenant_id: str,
    request: TenantCreateRequest
):
    """更新租户配置"""
    tenant = _tenants.get(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")

    if request.name:
        tenant["name"] = request.name
    if request.llm_config:
        tenant["llm_config"] = request.llm_config.dict()
    if request.skill_whitelist is not None:
        tenant["skill_whitelist"] = request.skill_whitelist
    if request.rate_limit:
        tenant["rate_limit"] = request.rate_limit

    return TenantResponse(**tenant)


@router.delete("/{tenant_id}")
async def delete_tenant(tenant_id: str):
    """删除租户"""
    if tenant_id in _tenants:
        api_key = _tenants[tenant_id]["api_key"]
        del _tenants[tenant_id]
        if api_key in _tenant_by_key:
            del _tenant_by_key[api_key]
        return {"deleted": True}
    raise HTTPException(status_code=404, detail="租户不存在")


@router.post("/{tenant_id}/regenerate-api-key")
async def regenerate_api_key(tenant_id: str):
    """重新生成 API Key"""
    tenant = _tenants.get(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")

    # 删除旧 key
    old_key = tenant["api_key"]
    if old_key in _tenant_by_key:
        del _tenant_by_key[old_key]

    # 生成新 key
    new_key = generate_api_key()
    tenant["api_key"] = new_key
    _tenant_by_key[new_key] = tenant

    return {"api_key": new_key}
