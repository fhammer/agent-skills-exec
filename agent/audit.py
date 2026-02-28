"""Audit logging for Agent Skills Framework."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any, Dict, List
from enum import Enum
import json


class AuditOp(Enum):
    """Audit operation types."""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    COMPRESS = "compress"


class AuditLayer(Enum):
    """Context layer types."""
    USER_INPUT = "user_input"
    SCRATCHPAD = "scratchpad"
    ENVIRONMENT = "environment"


@dataclass
class AuditEntry:
    """Single audit log entry."""
    timestamp: str
    layer: AuditLayer
    op: AuditOp
    key: str
    source: str  # "planner" | "skill:parse_report" | "coordinator"
    detail: str = ""
    value_preview: str = ""  # Truncated value preview
    execution_time_ms: float = 0

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp,
            "layer": self.layer.value,
            "op": self.op.value,
            "key": self.key,
            "source": self.source,
            "detail": self.detail,
            "value_preview": self._truncate(self.value_preview, 100),
            "execution_time_ms": self.execution_time_ms
        }

    @staticmethod
    def _truncate(value: str, max_length: int) -> str:
        """Truncate value to max length."""
        if not value:
            return ""
        if len(value) <= max_length:
            return value
        return value[:max_length] + "..."


@dataclass
class CausalChain:
    """Represents a causal chain of decisions."""
    question: str
    chain: List[Dict] = field(default_factory=list)
    conclusion: str = ""

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "question": self.question,
            "chain": self.chain,
            "conclusion": self.conclusion
        }


class AuditLog:
    """Audit log manager for tracking all context operations."""

    def __init__(self):
        self.entries: List[AuditEntry] = []

    def record(
        self,
        layer: AuditLayer,
        op: AuditOp,
        key: str,
        source: str,
        detail: str = "",
        value: Any = None,
        execution_time_ms: float = 0
    ) -> None:
        """Record an audit entry.

        Args:
            layer: Context layer
            op: Operation type
            key: Key being accessed
            source: Source of operation (component name)
            detail: Additional details
            value: Value being written (for preview)
            execution_time_ms: Execution time in milliseconds
        """
        entry = AuditEntry(
            timestamp=datetime.now().isoformat(),
            layer=layer,
            op=op,
            key=key,
            source=source,
            detail=detail,
            value_preview=self._format_value(value),
            execution_time_ms=execution_time_ms
        )
        self.entries.append(entry)

    def _format_value(self, value: Any) -> str:
        """Format value for preview."""
        if value is None:
            return ""
        if isinstance(value, (str, int, float, bool)):
            return str(value)
        if isinstance(value, dict):
            try:
                return json.dumps(value, ensure_ascii=False)
            except:
                return "{dict}"
        if isinstance(value, list):
            return f"[{len(value)} items]"
        # For Skill objects and other complex types
        return f"<{type(value).__name__}>"

    def get_trace(self, skill_name: str) -> List[Dict]:
        """Get complete execution trace for a specific Skill.

        Args:
            skill_name: Name of the skill to trace

        Returns:
            List of audit entry dictionaries
        """
        return [
            entry.to_dict() for entry in self.entries
            if entry.source == f"skill:{skill_name}"
        ]

    def get_by_source(self, source: str) -> List[Dict]:
        """Get all entries from a specific source.

        Args:
            source: Source identifier (e.g., "planner", "coordinator")

        Returns:
            List of audit entry dictionaries
        """
        return [
            entry.to_dict() for entry in self.entries
            if entry.source == source
        ]

    def get_by_layer(self, layer: AuditLayer) -> List[Dict]:
        """Get all entries for a specific layer.

        Args:
            layer: Layer to filter by

        Returns:
            List of audit entry dictionaries
        """
        return [
            entry.to_dict() for entry in self.entries
            if entry.layer == layer
        ]

    def get_by_key(self, key: str) -> List[Dict]:
        """Get all operations on a specific key.

        Args:
            key: Key to search for

        Returns:
            List of audit entry dictionaries
        """
        return [
            entry.to_dict() for entry in self.entries
            if entry.key == key
        ]

    def explain(self, question: str) -> str:
        """Generate explanation for why AI made a decision.

        Args:
            question: Question to answer (e.g., "Why recommend eating less seafood?")

        Returns:
            Explanation with causal chain
        """
        # Find relevant entries based on keywords in question
        keywords = self._extract_keywords(question)
        relevant_entries = []

        for entry in self.entries:
            if any(
                kw.lower() in entry.detail.lower() or
                kw.lower() in entry.value_preview.lower()
                for kw in keywords
            ):
                relevant_entries.append(entry)

        # Build causal chain
        chain = []
        for entry in relevant_entries:
            chain.append({
                "step": entry.source,
                "action": f"{entry.op.value} {entry.key}",
                "detail": entry.detail,
                "value": entry.value_preview[:50]
            })

        if not chain:
            return f"无法找到与问题 '{question}' 相关的审计记录。"

        conclusion = f"基于以上 {len(chain)} 个步骤，AI 做出了相应决策。"

        causal = CausalChain(
            question=question,
            chain=chain,
            conclusion=conclusion
        )

        return self._format_causal_chain(causal)

    def _extract_keywords(self, question: str) -> List[str]:
        """Extract keywords from question."""
        # Simple keyword extraction (remove common words)
        stop_words = {"的", "是", "为什么", "怎么", "什么", "了", "和", "与"}
        words = question.split()
        return [w for w in words if len(w) > 1 and w not in stop_words]

    def _format_causal_chain(self, causal: CausalChain) -> str:
        """Format causal chain as readable text."""
        lines = [f"问题: {causal.question}", "\n决策链:"]
        for i, step in enumerate(causal.chain, 1):
            lines.append(f"  {i}. [{step['step']}] {step['action']}")
            if step.get('detail'):
                lines.append(f"     详情: {step['detail']}")
        lines.append(f"\n结论: {causal.conclusion}")
        return "\n".join(lines)

    def get_summary(self) -> Dict:
        """Get audit log summary."""
        if not self.entries:
            return {"total_entries": 0}

        by_source = {}
        by_layer = {}
        by_op = {}

        for entry in self.entries:
            # Count by source
            by_source[entry.source] = by_source.get(entry.source, 0) + 1
            # Count by layer
            by_layer[entry.layer.value] = by_layer.get(entry.layer.value, 0) + 1
            # Count by operation
            by_op[entry.op.value] = by_op.get(entry.op.value, 0) + 1

        return {
            "total_entries": len(self.entries),
            "by_source": by_source,
            "by_layer": by_layer,
            "by_operation": by_op,
            "time_range": {
                "first": self.entries[0].timestamp,
                "last": self.entries[-1].timestamp
            }
        }

    def clear(self) -> None:
        """Clear all audit entries."""
        self.entries = []

    def export(self) -> List[Dict]:
        """Export all entries as dictionaries."""
        return [entry.to_dict() for entry in self.entries]
