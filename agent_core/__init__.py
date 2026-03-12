"""
Agent Core - 通用智能体框架核心模块

本模块提供通用智能体框架的核心抽象基类和基础设施：
- base/: 核心抽象基类（Agent、Skill、Tool、Connector）
- skill_registry.py: Skill注册和热重载机制
- context_manager.py: 上下文管理器
- extension_system.py: 扩展系统（Plugin、Hook、Event）
- business_adapter/: 业务系统集成适配器（REST、数据库、消息队列、文件系统）
- config_manager/: 配置管理系统
"""

__version__ = "2.0.0"
__author__ = "Agent Skills Framework Team"

from .base.agent import Agent, AgentConfig, AgentState
from .base.skill import BaseSkill, SkillConfig, SkillExecutionContext, SkillExecutionResult
from .base.tool import BaseTool, ToolConfig, ToolContext, ToolResult
from .base.connector import BaseConnector, ConnectorConfig, ConnectorStatus
from .skill_registry import SkillRegistry, RegistryConfig
from .context_manager import ContextManager, ContextLayer
from .extension_system import Plugin, Hook, Event, ExtensionManager
from .config_manager import (
    ConfigManager, ConfigSource, ConfigMode,
    FileConfigLoader, EnvConfigLoader, CommandLineConfigLoader,
    ConfigValidator, ValidationResult,
    ConfigTemplate, ConfigSection
)
from .business_adapter import (
    RESTAdapter, RESTConfig,
    DatabaseAdapter, DatabaseConfig, DatabaseType, create_database_adapter,
    MessageQueueAdapter, MQConfig, MQType, create_mq_adapter,
    FileAdapter, FileConfig, FileType, create_file_adapter,
    create_local_file_adapter, create_s3_file_adapter
)

__all__ = [
    # Base abstractions
    "Agent",
    "AgentConfig",
    "AgentState",
    "BaseSkill",
    "SkillConfig",
    "SkillExecutionContext",
    "SkillExecutionResult",
    "BaseTool",
    "ToolConfig",
    "ToolContext",
    "ToolResult",
    "BaseConnector",
    "ConnectorConfig",
    "ConnectorStatus",
    # Core components
    "SkillRegistry",
    "RegistryConfig",
    "ContextManager",
    "ContextLayer",
    # Extension system
    "Plugin",
    "Hook",
    "Event",
    "ExtensionManager",
    # Configuration
    "ConfigManager",
    "ConfigSource",
    "ConfigMode",
    "FileConfigLoader",
    "EnvConfigLoader",
    "CommandLineConfigLoader",
    "ConfigValidator",
    "ValidationResult",
    "ConfigTemplate",
    "ConfigSection",
    # Business adapters
    "RESTAdapter",
    "RESTConfig",
    "DatabaseAdapter",
    "DatabaseConfig",
    "DatabaseType",
    "create_database_adapter",
    "MessageQueueAdapter",
    "MQConfig",
    "MQType",
    "create_mq_adapter",
    "FileAdapter",
    "FileConfig",
    "FileType",
    "create_file_adapter",
    "create_local_file_adapter",
    "create_s3_file_adapter",
]
