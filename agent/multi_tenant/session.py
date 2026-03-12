"""
会话管理模块

提供租户会话管理功能
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, Optional, List, Tuple
import time
import uuid

from .exceptions import (
    SessionNotFoundError,
)


class SessionStatus(Enum):
    """会话状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    CLOSED = "closed"


class MessageRole(Enum):
    """消息角色枚举"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


@dataclass
class Message:
    """会话消息"""
    message_id: str
    role: MessageRole
    content: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        role: MessageRole,
        content: str,
        message_id: Optional[str] = None,
        **kwargs
    ) -> "Message":
        """创建消息"""
        return cls(
            message_id=message_id or str(uuid.uuid4()),
            role=role,
            content=content,
            **kwargs
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "message_id": self.message_id,
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


@dataclass
class SessionContext:
    """会话上下文"""
    user_profile: Dict[str, Any] = field(default_factory=dict)
    conversation_history: List[Message] = field(default_factory=list)
    previous_results: Dict[str, Any] = field(default_factory=dict)
    environment: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def message_count(self) -> int:
        """获取消息数量"""
        return len(self.conversation_history)

    @property
    def last_message(self) -> Optional[Message]:
        """获取最后一条消息"""
        if self.conversation_history:
            return self.conversation_history[-1]
        return None

    def add_message(self, role: MessageRole, content: str, **kwargs):
        """添加消息"""
        message = Message.create(role, content, **kwargs)
        self.conversation_history.append(message)

    def get_messages(
        self,
        limit: int = 100,
        role: Optional[MessageRole] = None
    ) -> List[Message]:
        """获取消息列表"""
        messages = self.conversation_history
        if role:
            messages = [m for m in messages if m.role == role]
        if limit > 0:
            messages = messages[-limit:]
        return messages

    def clear_messages(self):
        """清空消息"""
        self.conversation_history.clear()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "user_profile": self.user_profile,
            "conversation_history": [m.to_dict() for m in self.conversation_history],
            "previous_results": self.previous_results,
            "environment": self.environment,
            "metadata": self.metadata,
        }


@dataclass
class TenantSession:
    """租户会话"""
    session_id: str
    tenant_id: str
    scene_id: Optional[str] = None
    user_id: Optional[str] = None
    context: SessionContext = field(default_factory=SessionContext)
    status: SessionStatus = SessionStatus.ACTIVE
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    last_active_at: float = field(default_factory=time.time)
    expires_at: float = field(init=False)
    total_messages: int = 0
    total_tokens: int = 0

    DEFAULT_TTL = 3600  # 1小时

    def __post_init__(self):
        """后处理"""
        if not hasattr(self, "expires_at") or self.expires_at is None:
            self.expires_at = self.created_at + self.DEFAULT_TTL

    @property
    def is_active(self) -> bool:
        """是否活跃"""
        return (
            self.status == SessionStatus.ACTIVE and
            time.time() < self.expires_at
        )

    @property
    def is_expired(self) -> bool:
        """是否过期"""
        return time.time() > self.expires_at

    def extend_ttl(self, ttl: int = DEFAULT_TTL):
        """延长会话TTL"""
        self.expires_at = time.time() + ttl
        self.last_active_at = time.time()
        self.updated_at = time.time()

    def refresh(self):
        """刷新会话"""
        self.extend_ttl()

    def add_message(self, role: MessageRole, content: str, **kwargs):
        """添加消息"""
        self.context.add_message(role, content, **kwargs)
        self.total_messages += 1
        self.refresh()

    def record_tokens(self, tokens: int):
        """记录Token使用"""
        self.total_tokens += tokens

    def close(self):
        """关闭会话"""
        self.status = SessionStatus.CLOSED
        self.updated_at = time.time()
        self.last_active_at = time.time()

    def update_status(self, status: SessionStatus):
        """更新状态"""
        self.status = status
        self.updated_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "session_id": self.session_id,
            "tenant_id": self.tenant_id,
            "scene_id": self.scene_id,
            "user_id": self.user_id,
            "status": self.status.value,
            "context": self.context.to_dict(),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_active_at": self.last_active_at,
            "expires_at": self.expires_at,
            "total_messages": self.total_messages,
            "total_tokens": self.total_tokens,
        }

    @classmethod
    def create(
        cls,
        tenant_id: str,
        scene_id: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs
    ) -> "TenantSession":
        """创建会话"""
        session_id = kwargs.pop("session_id", str(uuid.uuid4()))
        return cls(
            session_id=session_id,
            tenant_id=tenant_id,
            scene_id=scene_id,
            user_id=user_id,
            **kwargs
        )


class SessionManager:
    """会话管理器"""

    def __init__(self, storage: Optional["SessionStorage"] = None):
        """初始化"""
        from .storage import SessionStorage, InMemorySessionStorage

        self._storage: SessionStorage = storage or InMemorySessionStorage()
        self._cache: Dict[str, TenantSession] = {}

    async def initialize(self):
        """初始化"""
        for session in await self._storage.list_all():
            self._cache[session.session_id] = session

    async def create_session(
        self,
        tenant_id: str,
        scene_id: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs
    ) -> TenantSession:
        """创建会话"""
        session = TenantSession.create(
            tenant_id=tenant_id,
            scene_id=scene_id,
            user_id=user_id,
            **kwargs
        )
        await self._storage.save(session)
        self._cache[session.session_id] = session
        return session

    async def get_session(self, session_id: str) -> TenantSession:
        """获取会话"""
        if session_id in self._cache:
            session = self._cache[session_id]
            # 检查是否过期
            if session.is_expired and session.status == SessionStatus.ACTIVE:
                session.update_status(SessionStatus.EXPIRED)
                await self._storage.save(session)
            return session

        session = await self._storage.load(session_id)
        if not session:
            raise SessionNotFoundError(session_id)

        if session.is_expired and session.status == SessionStatus.ACTIVE:
            session.update_status(SessionStatus.EXPIRED)
            await self._storage.save(session)

        self._cache[session_id] = session
        return session

    async def get_sessions_by_tenant(self, tenant_id: str) -> List[TenantSession]:
        """获取租户的所有会话"""
        all_sessions = await self._storage.list_all()
        return [
            session for session in all_sessions
            if session.tenant_id == tenant_id
        ]

    async def get_sessions_by_user(self, tenant_id: str, user_id: str) -> List[TenantSession]:
        """获取用户的所有会话"""
        return [
            session for session in await self.get_sessions_by_tenant(tenant_id)
            if session.user_id == user_id
        ]

    async def update_session(self, session: TenantSession) -> TenantSession:
        """更新会话"""
        session.updated_at = time.time()
        session.refresh()
        await self._storage.save(session)
        self._cache[session.session_id] = session
        return session

    async def delete_session(self, session_id: str):
        """删除会话"""
        if not await self._storage.exists(session_id):
            raise SessionNotFoundError(session_id)

        await self._storage.delete(session_id)
        self._cache.pop(session_id, None)

    async def list_sessions(
        self,
        tenant_id: Optional[str] = None,
        status: Optional[SessionStatus] = None,
        offset: int = 0,
        limit: int = 100
    ) -> List[TenantSession]:
        """列出会话"""
        sessions = await self._storage.list_all()

        if tenant_id:
            sessions = [s for s in sessions if s.tenant_id == tenant_id]
        if status:
            sessions = [s for s in sessions if s.status == status]

        return sessions[offset:offset + limit]

    async def close_session(self, session_id: str) -> TenantSession:
        """关闭会话"""
        session = await self.get_session(session_id)
        session.close()
        await self._storage.save(session)
        self._cache[session_id] = session
        return session

    async def expire_session(self, session_id: str) -> TenantSession:
        """过期会话"""
        session = await self.get_session(session_id)
        session.update_status(SessionStatus.EXPIRED)
        await self._storage.save(session)
        self._cache[session_id] = session
        return session

    async def clear_expired_sessions(self) -> int:
        """清理过期会话"""
        count = 0
        all_sessions = await self._storage.list_all()
        for session in all_sessions:
            if session.is_expired and session.status == SessionStatus.ACTIVE:
                session.update_status(SessionStatus.EXPIRED)
                await self._storage.save(session)
                count += 1
        return count

    async def count_sessions(
        self,
        tenant_id: Optional[str] = None,
        status: Optional[SessionStatus] = None
    ) -> int:
        """统计会话数量"""
        sessions = await self.list_sessions(tenant_id, status)
        return len(sessions)

    async def add_message(
        self,
        session_id: str,
        role: MessageRole,
        content: str,
        **kwargs
    ) -> TenantSession:
        """添加消息"""
        session = await self.get_session(session_id)
        session.add_message(role, content, **kwargs)
        await self._storage.save(session)
        self._cache[session_id] = session
        return session

    async def record_tokens(
        self,
        session_id: str,
        tokens: int
    ) -> TenantSession:
        """记录Token使用"""
        session = await self.get_session(session_id)
        session.record_tokens(tokens)
        await self._storage.save(session)
        self._cache[session_id] = session
        return session

    def get_cached_session(self, session_id: str) -> Optional[TenantSession]:
        """从缓存获取会话"""
        return self._cache.get(session_id)
