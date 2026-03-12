"""
对话管理器 - Conversation Manager

管理多轮对话、上下文维护和历史记录。
"""

import uuid
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from .types import (
    ConversationSession, ConversationTurn, IntentType,
    UserProfile, Product
)


@dataclass
class ConversationState:
    """对话状态"""
    current_intent: Optional[IntentType] = None
    pending_slots: Dict[str, Any] = field(default_factory=dict)
    last_products_shown: List[str] = field(default_factory=list)
    topic_stack: List[str] = field(default_factory=list)
    clarification_count: int = 0
    awaiting_response: bool = False


class ConversationManager:
    """对话管理器"""

    def __init__(self, max_history: int = 20, session_timeout: int = 1800):
        """
        初始化对话管理器

        Args:
            max_history: 每会话最大历史记录数
            session_timeout: 会话超时时间（秒）
        """
        self.max_history = max_history
        self.session_timeout = timedelta(seconds=session_timeout)
        self.sessions: Dict[str, ConversationSession] = {}
        self.states: Dict[str, ConversationState] = {}

    def create_session(self, user_id: Optional[str] = None) -> str:
        """
        创建新会话

        Args:
            user_id: 用户ID（可选）

        Returns:
            会话ID
        """
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = ConversationSession(
            session_id=session_id,
            user_id=user_id
        )
        self.states[session_id] = ConversationState()
        return session_id

    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """获取会话"""
        return self.sessions.get(session_id)

    def get_or_create_session(self, session_id: Optional[str] = None,
                               user_id: Optional[str] = None) -> str:
        """获取或创建会话"""
        if session_id and session_id in self.sessions:
            # 检查会话是否过期
            session = self.sessions[session_id]
            if datetime.now() - session.last_active < self.session_timeout:
                return session_id

        return self.create_session(user_id)

    def add_turn(self, session_id: str, user_input: str, assistant_response: str,
                 intent: Optional[IntentType] = None, products_shown: Optional[List[str]] = None):
        """
        添加对话轮次

        Args:
            session_id: 会话ID
            user_input: 用户输入
            assistant_response: 助手响应
            intent: 意图类型
            products_shown: 展示的商品ID列表
        """
        if session_id not in self.sessions:
            return

        session = self.sessions[session_id]
        session.add_turn(
            user_input=user_input,
            assistant_response=assistant_response,
            intent=intent,
            products_shown=products_shown or []
        )

        # 限制历史记录数量
        if len(session.turns) > self.max_history:
            session.turns = session.turns[-self.max_history:]

        # 更新状态
        if session_id in self.states:
            state = self.states[session_id]
            state.current_intent = intent
            if products_shown:
                state.last_products_shown = products_shown

    def get_recent_history(self, session_id: str, n: int = 5) -> List[ConversationTurn]:
        """获取最近的对话历史"""
        session = self.sessions.get(session_id)
        if not session:
            return []
        return session.turns[-n:] if len(session.turns) > n else session.turns

    def get_context_summary(self, session_id: str) -> Dict[str, Any]:
        """获取上下文摘要"""
        session = self.sessions.get(session_id)
        state = self.states.get(session_id)

        if not session:
            return {}

        return {
            "turns_count": len(session.turns),
            "session_duration_minutes": (
                (session.last_active - session.created_at).total_seconds() / 60
                if session.turns else 0
            ),
            "current_intent": state.current_intent.value if state and state.current_intent else None,
            "last_products_shown": state.last_products_shown if state else [],
            "recent_topics": self._extract_recent_topics(session)
        }

    def _extract_recent_topics(self, session: ConversationSession) -> List[str]:
        """提取最近的话题"""
        topics = []
        for turn in session.turns[-5:]:
            if turn.intent:
                topic = turn.intent.value
                if topic not in topics:
                    topics.append(topic)
        return topics

    def get_current_state(self, session_id: str) -> Optional[ConversationState]:
        """获取当前对话状态"""
        return self.states.get(session_id)

    def update_state(self, session_id: str, **kwargs):
        """更新对话状态"""
        if session_id in self.states:
            state = self.states[session_id]
            for key, value in kwargs.items():
                if hasattr(state, key):
                    setattr(state, key, value)

    def clear_session(self, session_id: str):
        """清除会话"""
        if session_id in self.sessions:
            del self.sessions[session_id]
        if session_id in self.states:
            del self.states[session_id]

    def clear_expired_sessions(self):
        """清除过期会话"""
        now = datetime.now()
        expired_sessions = []

        for session_id, session in self.sessions.items():
            if now - session.last_active > self.session_timeout:
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            self.clear_session(session_id)

        return len(expired_sessions)
