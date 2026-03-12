"""
Base 模块 - 核心抽象基类

包含通用智能体框架的核心抽象基类：
- agent.py: Agent 抽象基类
- skill.py: Skill 抽象基类
- tool.py: Tool 抽象基类
- connector.py: Connector 抽象基类
"""

from .agent import Agent, AgentConfig, AgentState
from .skill import (
    BaseSkill,
    SkillConfig,
    SkillStatus,
    SkillExecutionContext,
    SkillExecutionResult,
)
from .tool import (
    BaseTool,
    ToolConfig,
    ToolStatus,
    ToolContext,
    ToolResult,
)
from .connector import (
    BaseConnector,
    ConnectorConfig,
    ConnectorStatus,
    ConnectionStats,
    QueryResult,
)

__all__ = [
    # Agent
    "Agent",
    "AgentConfig",
    "AgentState",
    # Skill
    "BaseSkill",
    "SkillConfig",
    "SkillStatus",
    "SkillExecutionContext",
    "SkillExecutionResult",
    # Tool
    "BaseTool",
    "ToolConfig",
    "ToolStatus",
    "ToolContext",
    "ToolResult",
    # Connector
    "BaseConnector",
    "ConnectorConfig",
    "ConnectorStatus",
    "ConnectionStats",
    "QueryResult",
]
