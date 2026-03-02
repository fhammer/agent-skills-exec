"""API 路由"""

from api.routers import health, agent, tenants, skills, auth

__all__ = ["health", "agent", "tenants", "skills", "auth"]
