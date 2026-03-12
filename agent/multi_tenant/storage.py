"""
存储层模块

提供租户、场景、会话的存储抽象和实现
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import copy
import json
import os
import time

from .tenant import Tenant, TenantConfig, TenantStatus, SubscriptionPlan
from .scene import Scene, SceneConfig, SceneStatus
from .session import TenantSession, SessionStatus


class TenantStorage(ABC):
    """租户存储抽象"""

    @abstractmethod
    async def save(self, tenant: Tenant) -> None:
        """保存租户"""
        pass

    @abstractmethod
    async def load(self, tenant_id: str) -> Optional[Tenant]:
        """加载租户"""
        pass

    @abstractmethod
    async def delete(self, tenant_id: str) -> None:
        """删除租户"""
        pass

    @abstractmethod
    async def exists(self, tenant_id: str) -> bool:
        """检查租户是否存在"""
        pass

    @abstractmethod
    async def list_all(self) -> List[Tenant]:
        """列出所有租户"""
        pass


class SceneStorage(ABC):
    """场景存储抽象"""

    @abstractmethod
    async def save(self, scene: Scene) -> None:
        """保存场景"""
        pass

    @abstractmethod
    async def load(self, scene_id: str) -> Optional[Scene]:
        """加载场景"""
        pass

    @abstractmethod
    async def delete(self, scene_id: str) -> None:
        """删除场景"""
        pass

    @abstractmethod
    async def exists(self, scene_id: str) -> bool:
        """检查场景是否存在"""
        pass

    @abstractmethod
    async def list_all(self) -> List[Scene]:
        """列出所有场景"""
        pass


class SessionStorage(ABC):
    """会话存储抽象"""

    @abstractmethod
    async def save(self, session: TenantSession) -> None:
        """保存会话"""
        pass

    @abstractmethod
    async def load(self, session_id: str) -> Optional[TenantSession]:
        """加载会话"""
        pass

    @abstractmethod
    async def delete(self, session_id: str) -> None:
        """删除会话"""
        pass

    @abstractmethod
    async def exists(self, session_id: str) -> bool:
        """检查会话是否存在"""
        pass

    @abstractmethod
    async def list_all(self) -> List[TenantSession]:
        """列出所有会话"""
        pass


class InMemoryTenantStorage(TenantStorage):
    """内存租户存储实现"""

    def __init__(self):
        self._tenants: Dict[str, Tenant] = {}

    async def save(self, tenant: Tenant) -> None:
        """保存租户"""
        self._tenants[tenant.tenant_id] = tenant

    async def load(self, tenant_id: str) -> Optional[Tenant]:
        """加载租户"""
        return self._tenants.get(tenant_id)

    async def delete(self, tenant_id: str) -> None:
        """删除租户"""
        self._tenants.pop(tenant_id, None)

    async def exists(self, tenant_id: str) -> bool:
        """检查租户是否存在"""
        return tenant_id in self._tenants

    async def list_all(self) -> List[Tenant]:
        """列出所有租户"""
        return list(self._tenants.values())


class InMemorySceneStorage(SceneStorage):
    """内存场景存储实现"""

    def __init__(self):
        self._scenes: Dict[str, Scene] = {}

    async def save(self, scene: Scene) -> None:
        """保存场景"""
        self._scenes[scene.scene_id] = scene

    async def load(self, scene_id: str) -> Optional[Scene]:
        """加载场景"""
        return self._scenes.get(scene_id)

    async def delete(self, scene_id: str) -> None:
        """删除场景"""
        self._scenes.pop(scene_id, None)

    async def exists(self, scene_id: str) -> bool:
        """检查场景是否存在"""
        return scene_id in self._scenes

    async def list_all(self) -> List[Scene]:
        """列出所有场景"""
        return list(self._scenes.values())


class InMemorySessionStorage(SessionStorage):
    """内存会话存储实现"""

    def __init__(self):
        self._sessions: Dict[str, TenantSession] = {}

    async def save(self, session: TenantSession) -> None:
        """保存会话"""
        self._sessions[session.session_id] = session

    async def load(self, session_id: str) -> Optional[TenantSession]:
        """加载会话"""
        return self._sessions.get(session_id)

    async def delete(self, session_id: str) -> None:
        """删除会话"""
        self._sessions.pop(session_id, None)

    async def exists(self, session_id: str) -> bool:
        """检查会话是否存在"""
        return session_id in self._sessions

    async def list_all(self) -> List[TenantSession]:
        """列出所有会话"""
        return list(self._sessions.values())


class FileBasedTenantStorage(TenantStorage):
    """基于文件的租户存储"""

    def __init__(self, storage_dir: str = "./data/tenants"):
        self._storage_dir = storage_dir
        self._cache: Dict[str, Tenant] = {}
        os.makedirs(self._storage_dir, exist_ok=True)

    def _get_file_path(self, tenant_id: str) -> str:
        """获取文件路径"""
        return os.path.join(self._storage_dir, f"{tenant_id}.json")

    async def save(self, tenant: Tenant) -> None:
        """保存租户"""
        self._cache[tenant.tenant_id] = tenant
        file_path = self._get_file_path(tenant.tenant_id)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(tenant.to_dict(), f, ensure_ascii=False, indent=2)

    async def load(self, tenant_id: str) -> Optional[Tenant]:
        """加载租户"""
        if tenant_id in self._cache:
            return self._cache[tenant_id]

        file_path = self._get_file_path(tenant_id)
        if not os.path.exists(file_path):
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            tenant = self._dict_to_tenant(data)
            self._cache[tenant_id] = tenant
            return tenant
        except Exception:
            return None

    async def delete(self, tenant_id: str) -> None:
        """删除租户"""
        self._cache.pop(tenant_id, None)
        file_path = self._get_file_path(tenant_id)
        if os.path.exists(file_path):
            os.remove(file_path)

    async def exists(self, tenant_id: str) -> bool:
        """检查租户是否存在"""
        if tenant_id in self._cache:
            return True
        return os.path.exists(self._get_file_path(tenant_id))

    async def list_all(self) -> List[Tenant]:
        """列出所有租户"""
        tenants = []
        for filename in os.listdir(self._storage_dir):
            if filename.endswith(".json"):
                tenant_id = filename[:-5]  # remove .json
                tenant = await self.load(tenant_id)
                if tenant:
                    tenants.append(tenant)
        return tenants

    def _dict_to_tenant(self, data: Dict[str, Any]) -> Tenant:
        """字典转租户对象"""
        config = TenantConfig.from_dict(data["config"])
        tenant = Tenant(
            tenant_id=data["tenant_id"],
            config=config,
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time()),
        )
        if "usage" in data:
            usage_data = data["usage"]
            tenant.usage.tenant_id = usage_data.get("tenant_id", tenant.tenant_id)
            tenant.usage.requests_minute = usage_data.get("requests_minute", 0)
            tenant.usage.requests_hour = usage_data.get("requests_hour", 0)
            tenant.usage.requests_day = usage_data.get("requests_day", 0)
            tenant.usage.tokens_day = usage_data.get("tokens_day", 0)
            tenant.usage.current_sessions = usage_data.get("current_sessions", 0)
            tenant.usage.total_requests = usage_data.get("total_requests", 0)
            tenant.usage.total_tokens = usage_data.get("total_tokens", 0)
        return tenant


class FileBasedSceneStorage(SceneStorage):
    """基于文件的场景存储"""

    def __init__(self, storage_dir: str = "./data/scenes"):
        self._storage_dir = storage_dir
        self._cache: Dict[str, Scene] = {}
        os.makedirs(self._storage_dir, exist_ok=True)

    def _get_file_path(self, scene_id: str) -> str:
        """获取文件路径"""
        return os.path.join(self._storage_dir, f"{scene_id}.json")

    async def save(self, scene: Scene) -> None:
        """保存场景"""
        self._cache[scene.scene_id] = scene
        file_path = self._get_file_path(scene.scene_id)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(scene.to_dict(), f, ensure_ascii=False, indent=2)

    async def load(self, scene_id: str) -> Optional[Scene]:
        """加载场景"""
        if scene_id in self._cache:
            return self._cache[scene_id]

        file_path = self._get_file_path(scene_id)
        if not os.path.exists(file_path):
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            scene = self._dict_to_scene(data)
            self._cache[scene_id] = scene
            return scene
        except Exception:
            return None

    async def delete(self, scene_id: str) -> None:
        """删除场景"""
        self._cache.pop(scene_id, None)
        file_path = self._get_file_path(scene_id)
        if os.path.exists(file_path):
            os.remove(file_path)

    async def exists(self, scene_id: str) -> bool:
        """检查场景是否存在"""
        if scene_id in self._cache:
            return True
        return os.path.exists(self._get_file_path(scene_id))

    async def list_all(self) -> List[Scene]:
        """列出所有场景"""
        scenes = []
        for filename in os.listdir(self._storage_dir):
            if filename.endswith(".json"):
                scene_id = filename[:-5]
                scene = await self.load(scene_id)
                if scene:
                    scenes.append(scene)
        return scenes

    def _dict_to_scene(self, data: Dict[str, Any]) -> Scene:
        """字典转场景对象"""
        config = SceneConfig.from_dict(data["config"])
        return Scene(
            scene_id=data["scene_id"],
            tenant_id=data["tenant_id"],
            config=config,
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time()),
        )


class FileBasedSessionStorage(SessionStorage):
    """基于文件的会话存储"""

    def __init__(self, storage_dir: str = "./data/sessions"):
        self._storage_dir = storage_dir
        self._cache: Dict[str, TenantSession] = {}
        os.makedirs(self._storage_dir, exist_ok=True)

    def _get_file_path(self, session_id: str) -> str:
        """获取文件路径"""
        return os.path.join(self._storage_dir, f"{session_id}.json")

    async def save(self, session: TenantSession) -> None:
        """保存会话"""
        self._cache[session.session_id] = session
        file_path = self._get_file_path(session.session_id)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(session.to_dict(), f, ensure_ascii=False, indent=2)

    async def load(self, session_id: str) -> Optional[TenantSession]:
        """加载会话"""
        if session_id in self._cache:
            return self._cache[session_id]

        file_path = self._get_file_path(session_id)
        if not os.path.exists(file_path):
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            session = self._dict_to_session(data)
            self._cache[session_id] = session
            return session
        except Exception:
            return None

    async def delete(self, session_id: str) -> None:
        """删除会话"""
        self._cache.pop(session_id, None)
        file_path = self._get_file_path(session_id)
        if os.path.exists(file_path):
            os.remove(file_path)

    async def exists(self, session_id: str) -> bool:
        """检查会话是否存在"""
        if session_id in self._cache:
            return True
        return os.path.exists(self._get_file_path(session_id))

    async def list_all(self) -> List[TenantSession]:
        """列出所有会话"""
        sessions = []
        for filename in os.listdir(self._storage_dir):
            if filename.endswith(".json"):
                session_id = filename[:-5]
                session = await self.load(session_id)
                if session:
                    sessions.append(session)
        return sessions

    def _dict_to_session(self, data: Dict[str, Any]) -> TenantSession:
        """字典转会话对象"""
        from .session import Message, MessageRole, SessionContext

        context = SessionContext()
        if "context" in data:
            ctx_data = data["context"]
            context.user_profile = ctx_data.get("user_profile", {})
            context.previous_results = ctx_data.get("previous_results", {})
            context.environment = ctx_data.get("environment", {})
            context.metadata = ctx_data.get("metadata", {})

            for msg_data in ctx_data.get("conversation_history", []):
                role = MessageRole(msg_data["role"]) if isinstance(msg_data["role"], str) else msg_data["role"]
                message = Message(
                    message_id=msg_data["message_id"],
                    role=role,
                    content=msg_data["content"],
                    timestamp=msg_data.get("timestamp", time.time()),
                    metadata=msg_data.get("metadata", {}),
                )
                context.conversation_history.append(message)

        status = SessionStatus(data["status"]) if isinstance(data["status"], str) else data["status"]

        session = TenantSession(
            session_id=data["session_id"],
            tenant_id=data["tenant_id"],
            scene_id=data.get("scene_id"),
            user_id=data.get("user_id"),
            context=context,
            status=status,
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time()),
            last_active_at=data.get("last_active_at", time.time()),
            total_messages=data.get("total_messages", 0),
            total_tokens=data.get("total_tokens", 0),
        )
        session.expires_at = data.get("expires_at", session.created_at + session.DEFAULT_TTL)
        return session
