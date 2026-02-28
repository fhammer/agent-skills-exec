"""Request/response protocol for dialogue system."""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum


class RequestType(Enum):
    """Types of requests."""
    CHAT = "chat"
    HEALTH_CHECK = "health_check"
    SKILL_EXECUTION = "skill_execution"
    STATUS = "status"
    RESET = "reset"


@dataclass
class Request:
    """A request to the agent."""
    type: RequestType
    content: str
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    request_id: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "type": self.type.value,
            "content": self.content,
            "context": self.context,
            "metadata": self.metadata,
            "request_id": self.request_id
        }


@dataclass
class Response:
    """A response from the agent."""
    content: str
    success: bool
    request_id: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "content": self.content,
            "success": self.success,
            "request_id": self.request_id,
            "error": self.error,
            "metadata": self.metadata,
            "execution_time_ms": self.execution_time_ms
        }


@dataclass
class ExecutionContext:
    """Context for skill execution."""
    sub_task: str
    user_input: str
    previous_results: Dict[str, Any]
    conversation_history: List[Dict]
    available_tools: List[str]

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "sub_task": self.sub_task,
            "user_input": self.user_input,
            "previous_results": self.previous_results,
            "conversation_history": self.conversation_history,
            "available_tools": self.available_tools
        }


class Protocol:
    """Request/response protocol handler."""

    @staticmethod
    def create_request(
        content: str,
        request_type: RequestType = RequestType.CHAT,
        context: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None
    ) -> Request:
        """Create a request.

        Args:
            content: Request content
            request_type: Type of request
            context: Optional context
            metadata: Optional metadata

        Returns:
            Request object
        """
        return Request(
            type=request_type,
            content=content,
            context=context or {},
            metadata=metadata or {}
        )

    @staticmethod
    def create_response(
        content: str,
        success: bool = True,
        request_id: str = None,
        error: str = None,
        metadata: Dict[str, Any] = None,
        execution_time_ms: float = 0
    ) -> Response:
        """Create a response.

        Args:
            content: Response content
            success: Whether successful
            request_id: Associated request ID
            error: Error message if failed
            metadata: Optional metadata
            execution_time_ms: Execution time

        Returns:
            Response object
        """
        return Response(
            content=content,
            success=success,
            request_id=request_id,
            error=error,
            metadata=metadata or {},
            execution_time_ms=execution_time_ms
        )

    @staticmethod
    def parse_request(data: Dict) -> Request:
        """Parse request from dictionary.

        Args:
            data: Request dictionary

        Returns:
            Request object
        """
        return Request(
            type=RequestType(data.get("type", RequestType.CHAT)),
            content=data.get("content", ""),
            context=data.get("context", {}),
            metadata=data.get("metadata", {}),
            request_id=data.get("request_id")
        )
