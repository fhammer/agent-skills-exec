"""FastAPI Web 服务入口"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import uvicorn

from api.config import settings
from api.routers import agent, tenants, skills, health, auth
from api.database import init_db, close_db

# 导入中间件
from api.middleware import RateLimitMiddleware, LoggingMiddleware, AuthMiddleware
from api.exceptions import (
    AgentException,
    TenantNotFoundException,
    RateLimitExceededException,
    AuthenticationException
)

# 全局管理器实例
_tenant_manager = None
_scene_manager = None
_session_manager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global _tenant_manager, _scene_manager, _session_manager

    # 启动时初始化
    print("🚀 Agent Framework API 启动中...")
    await init_db()
    print("✅ 数据库初始化完成")

    # 初始化多租户管理系统
    from agent.multi_tenant import TenantManager, SceneManager, SessionManager
    from agent.multi_tenant.storage import InMemoryTenantStorage, InMemorySceneStorage, InMemorySessionStorage
    from api.routers.tenants import init_managers

    _tenant_manager = TenantManager(InMemoryTenantStorage())
    await _tenant_manager.initialize()

    _scene_manager = SceneManager(InMemorySceneStorage())
    await _scene_manager.initialize()

    _session_manager = SessionManager(InMemorySessionStorage())
    await _session_manager.initialize()

    init_managers(_tenant_manager, _scene_manager, _session_manager)
    print("✅ 多租户管理系统初始化完成")

    # 创建默认租户（开发环境）
    try:
        from agent.multi_tenant import SubscriptionPlan
        await _tenant_manager.create_tenant(
            name="Default Tenant",
            plan=SubscriptionPlan.FREE,
        )
        print("✅ 默认租户创建成功")
    except Exception as e:
        print(f"ℹ️  租户已存在或创建失败: {e}")

    print("🌐 API 服务已启动")
    yield
    # 关闭时清理
    print("🛑 Agent Framework API 关闭中...")
    await close_db()
    print("✅ 清理完成")


# 创建 FastAPI 应用
app = FastAPI(
    title="Agent Framework API",
    description="通用智能体开发框架 - REST API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 简化的中间件配置 - 移除复杂的 TenantMiddleware 依赖
# 目前只添加基础中间件，认证中间件在 DEBUG 模式下会跳过
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(AuthMiddleware)


# 注册路由
app.include_router(health.router, prefix="/api/v1", tags=["健康检查"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证授权"])
app.include_router(agent.router, prefix="/api/v1/agent", tags=["智能体对话"])
app.include_router(tenants.router, prefix="/api/v1/tenants", tags=["租户管理"])
app.include_router(skills.router, prefix="/api/v1/skills", tags=["技能管理"])


# 异常处理
@app.exception_handler(AgentException)
async def agent_exception_handler(request: Request, exc: AgentException):
    """智能体框架异常处理"""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": True,
            "code": exc.code,
            "message": exc.message
        }
    )


@app.exception_handler(TenantNotFoundException)
async def tenant_not_found_handler(request: Request, exc: TenantNotFoundException):
    """租户不存在异常处理"""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": True,
            "code": "TENANT_NOT_FOUND",
            "message": f"租户不存在: {exc.tenant_id}"
        }
    )


@app.exception_handler(RateLimitExceededException)
async def rate_limit_handler(request: Request, exc: RateLimitExceededException):
    """限流异常处理"""
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error": True,
            "code": "RATE_LIMIT_EXCEEDED",
            "message": f"请求频率超限，请稍后再试"
        },
        headers={"Retry-After": str(exc.retry_after)}
    )


@app.exception_handler(AuthenticationException)
async def auth_exception_handler(request: Request, exc: AuthenticationException):
    """认证异常处理"""
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "error": True,
            "code": "AUTHENTICATION_FAILED",
            "message": "认证失败，请检查 API Key"
        }
    )


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "Agent Framework API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "docs": "/docs"
    }


def main():
    """启动服务器"""
    uvicorn.run(
        "api.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=1 if settings.DEBUG else 4,
        log_level="info"
    )


if __name__ == "__main__":
    main()
