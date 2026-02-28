"""Dialogue manager for multi-turn conversations."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Message:
    """A message in the conversation."""
    role: str  # "user" | "assistant" | "system"
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }


class DialogueManager:
    """Manage multi-turn conversations.

    Handles conversation history, context management,
    and dialogue state.
    """

    def __init__(self, max_history: int = 50):
        """Initialize dialogue manager.

        Args:
            max_history: Maximum number of messages to keep in history
        """
        self.max_history = max_history
        self.messages: List[Message] = []
        self.state: Dict[str, Any] = {}

    def add_message(
        self,
        role: str,
        content: str,
        metadata: Dict[str, Any] = None
    ) -> None:
        """Add a message to the conversation.

        Args:
            role: Message role (user/assistant/system)
            content: Message content
            metadata: Optional metadata
        """
        message = Message(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        self.messages.append(message)

        # Trim history if needed
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history:]

    def get_history(self, last_n: Optional[int] = None) -> List[Dict]:
        """Get conversation history.

        Args:
            last_n: Only get last N messages (None for all)

        Returns:
            List of message dictionaries
        """
        history = [msg.to_dict() for msg in self.messages]
        if last_n:
            return history[-last_n:]
        return history

    def get_user_messages(self) -> List[Message]:
        """Get all user messages."""
        return [msg for msg in self.messages if msg.role == "user"]

    def get_assistant_messages(self) -> List[Message]:
        """Get all assistant messages."""
        return [msg for msg in self.messages if msg.role == "assistant"]

    def clear_history(self) -> None:
        """Clear conversation history."""
        self.messages = []

    def set_state(self, key: str, value: Any) -> None:
        """Set dialogue state value.

        Args:
            key: State key
            value: State value
        """
        self.state[key] = value

    def get_state(self, key: str, default: Any = None) -> Any:
        """Get dialogue state value.

        Args:
            key: State key
            default: Default value if not found

        Returns:
            State value
        """
        return self.state.get(key, default)

    def clear_state(self) -> None:
        """Clear dialogue state."""
        self.state = {}

    def get_summary(self) -> Dict:
        """Get conversation summary.

        Returns:
            Summary dictionary
        """
        return {
            "total_messages": len(self.messages),
            "user_messages": len(self.get_user_messages()),
            "assistant_messages": len(self.get_assistant_messages()),
            "state_keys": list(self.state.keys())
        }

    def export(self) -> Dict:
        """Export conversation.

        Returns:
            Export dictionary
        """
        return {
            "messages": [msg.to_dict() for msg in self.messages],
            "state": self.state,
            "summary": self.get_summary()
        }

    def import_data(self, data: Dict) -> None:
        """Import conversation data.

        Args:
            data: Export dictionary from export()
        """
        self.messages = [
            Message(
                role=msg["role"],
                content=msg["content"],
                timestamp=msg.get("timestamp"),
                metadata=msg.get("metadata", {})
            )
            for msg in data.get("messages", [])
        ]
        self.state = data.get("state", {})
