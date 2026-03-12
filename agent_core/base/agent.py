"""
Agent 抽象基类 - 智能体核心抽象

定义智能体的核心接口和生命周期管理
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List
import time


class AgentState(Enum):
    """智能体状态枚举"""
    INITIALIZING = "initializing"  # 初始化中
    READY = "ready"  # 就绪
    RUNNING = "running"  # 运行中
    PAUSED = "paused"  # 暂停
    ERROR = "error"  # 错误
    SHUTTING_DOWN = "shutting_down"  # 正在关闭
    SHUTDOWN = "shutdown"  # 已关闭


@dataclass
class AgentConfig:
    """智能体配置"""
    name: str = "default_agent"
    version: str = "1.0.0"
    description: str = "Default agent configuration"
    max_concurrent_tasks: int = 10
    timeout_seconds: int = 300
    enable_audit: bool = True
    enable_metrics: bool = True
    custom_settings: Dict[str, Any] = field(default_factory=dict)


class Agent(ABC):
    """智能体抽象基类

    定义智能体的核心接口和生命周期管理
    """

    def __init__(self, config: AgentConfig):
        self.config = config
        self._state = AgentState.INITIALIZING
        self._created_at = time.time()
        self._last_activity_at = time.time()
        self._metrics = {
            "total_tasks": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "total_execution_time_ms": 0,
            "avg_execution_time_ms": 0
        }

    @property
    def state(self) -> AgentState:
        """获取当前状态"""
        return self._state

    @property
    def created_at(self) -> float:
        """创建时间戳"""
        return self._created_at

    @property
    def last_activity_at(self) -> float:
        """最后活动时间戳"""
        return self._last_activity_at

    @property
    def metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        return self._metrics.copy()

    @abstractmethod
    async def initialize(self) -> bool:
        """初始化智能体

        Returns:
            bool: 初始化是否成功
        """
        self._state = AgentState.READY
        self._last_activity_at = time.time()
        return True

    @abstractmethod
    async def process(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """处理用户请求

        Args:
            user_input: 用户输入
            context: 上下文信息

        Returns:
            Dict[str, Any]: 处理结果
        """
        self._last_activity_at = time.time()
        self._metrics["total_tasks"] += 1
        return {}

    @abstractmethod
    async def pause(self) -> bool:
        """暂停智能体

        Returns:
            bool: 暂停是否成功
        """
        self._state = AgentState.PAUSED
        self._last_activity_at = time.time()
        return True

    @abstractmethod
    async def resume(self) -> bool:
        """恢复智能体

        Returns:
            bool: 恢复是否成功
        """
        self._state = AgentState.READY
        self._last_activity_at = time.time()
        return True

    @abstractmethod
    async def shutdown(self) -> bool:
        """关闭智能体

        Returns:
            bool: 关闭是否成功
        """
        self._state = AgentState.SHUTDOWN
        self._last_activity_at = time.time()
        return True

    @abstractmethod
    def get_audit_trail(self) -> List[Dict[str, Any]]:
        """获取审计轨迹

        Returns:
            List[Dict[str, Any]]: 审计日志条目
        """
        return []

    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        """获取配置信息

        Returns:
            Dict[str, Any]: 配置字典
        """
        return self.config.__dict__

    def update_metrics(self, task_success: bool, execution_time_ms: float):
        """更新性能指标

        Args:
            task_success: 任务是否成功
            execution_time_ms: 执行时间（毫秒）
        """
        if task_success:
            self._metrics["successful_tasks"] += 1
        else:
            self._metrics["failed_tasks"] += 1

        self._metrics["total_execution_time_ms"] += execution_time_ms
        self._metrics["avg_execution_time_ms"] = (
            self._metrics["total_execution_time_ms"] / self._metrics["total_tasks"]
        )

    def __str__(self):
        return f"{self.config.name} (v{self.config.version}) - {self.state.value}"

    def __repr__(self):
        return f"{self.__class__.__name__}(name={self.config.name}, version={self.config.version}, state={self.state.value})"
