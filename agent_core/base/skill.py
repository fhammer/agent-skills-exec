"""
Skill 抽象基类 - 技能核心抽象

定义技能的核心接口和执行上下文
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List
import time
import uuid


class SkillStatus(Enum):
    """技能状态"""
    INACTIVE = "inactive"
    READY = "ready"
    RUNNING = "running"
    ERROR = "error"
    DEPRECATED = "deprecated"


@dataclass
class SkillConfig:
    """技能配置"""
    name: str
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    tags: List[str] = field(default_factory=list)
    triggers: List[str] = field(default_factory=list)
    timeout_seconds: int = 60
    max_retries: int = 3
    requires_approval: bool = False
    custom_settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SkillExecutionContext:
    """技能执行上下文"""
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sub_task: str = ""
    user_input: str = ""
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    previous_results: Dict[str, Any] = field(default_factory=dict)
    environment: Dict[str, Any] = field(default_factory=dict)
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    started_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "request_id": self.request_id,
            "task_id": self.task_id,
            "sub_task": self.sub_task,
            "user_input": self.user_input,
            "conversation_history": self.conversation_history,
            "previous_results": self.previous_results,
            "environment": self.environment,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "started_at": self.started_at,
            "metadata": self.metadata,
        }


@dataclass
class SkillExecutionResult:
    """技能执行结果"""
    success: bool = False
    skill_name: str = ""
    sub_task: str = ""
    structured: Dict[str, Any] = field(default_factory=dict)
    text: str = ""
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    started_at: float = field(default_factory=time.time)
    completed_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "skill_name": self.skill_name,
            "sub_task": self.sub_task,
            "structured": self.structured,
            "text": self.text,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "metadata": self.metadata,
        }

    @classmethod
    def success(
        cls,
        skill_name: str,
        sub_task: str = "",
        structured: Optional[Dict[str, Any]] = None,
        text: str = "",
        execution_time_ms: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "SkillExecutionResult":
        """创建成功结果"""
        now = time.time()
        return cls(
            success=True,
            skill_name=skill_name,
            sub_task=sub_task,
            structured=structured or {},
            text=text,
            error=None,
            execution_time_ms=execution_time_ms,
            started_at=now - (execution_time_ms / 1000.0) if execution_time_ms > 0 else now,
            completed_at=now,
            metadata=metadata or {},
        )

    @classmethod
    def failure(
        cls,
        skill_name: str,
        sub_task: str = "",
        error: str = "",
        execution_time_ms: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "SkillExecutionResult":
        """创建失败结果"""
        now = time.time()
        return cls(
            success=False,
            skill_name=skill_name,
            sub_task=sub_task,
            structured={},
            text="",
            error=error,
            execution_time_ms=execution_time_ms,
            started_at=now - (execution_time_ms / 1000.0) if execution_time_ms > 0 else now,
            completed_at=now,
            metadata=metadata or {},
        )


class BaseSkill(ABC):
    """技能抽象基类

    所有自定义技能都应该继承此类
    """

    def __init__(self, config: SkillConfig):
        self.config = config
        self._status = SkillStatus.INACTIVE
        self._created_at = time.time()
        self._last_executed_at: Optional[float] = None
        self._execution_count = 0
        self._success_count = 0
        self._error_count = 0
        self._total_execution_time_ms = 0.0

    @property
    def name(self) -> str:
        """获取技能名称"""
        return self.config.name

    @property
    def version(self) -> str:
        """获取技能版本"""
        return self.config.version

    @property
    def status(self) -> SkillStatus:
        """获取技能状态"""
        return self._status

    @property
    def created_at(self) -> float:
        """创建时间戳"""
        return self._created_at

    @property
    def last_executed_at(self) -> Optional[float]:
        """最后执行时间戳"""
        return self._last_executed_at

    @property
    def execution_count(self) -> int:
        """执行次数"""
        return self._execution_count

    @property
    def success_count(self) -> int:
        """成功次数"""
        return self._success_count

    @property
    def error_count(self) -> int:
        """错误次数"""
        return self._error_count

    @property
    def avg_execution_time_ms(self) -> float:
        """平均执行时间"""
        if self._execution_count == 0:
            return 0.0
        return self._total_execution_time_ms / self._execution_count

    async def initialize(self) -> bool:
        """初始化技能

        Returns:
            bool: 初始化是否成功
        """
        try:
            result = await self._on_initialize()
            if result:
                self._status = SkillStatus.READY
            return result
        except Exception as e:
            self._status = SkillStatus.ERROR
            await self._on_error(e)
            return False

    @abstractmethod
    async def _on_initialize(self) -> bool:
        """初始化钩子 - 子类实现

        Returns:
            bool: 初始化是否成功
        """
        return True

    async def execute(
        self,
        context: SkillExecutionContext
    ) -> SkillExecutionResult:
        """执行技能

        Args:
            context: 执行上下文

        Returns:
            SkillExecutionResult: 执行结果
        """
        start_time = time.time()
        self._status = SkillStatus.RUNNING
        self._execution_count += 1

        try:
            # 执行前钩子
            await self._before_execute(context)

            # 执行核心逻辑
            result = await self._execute(context)

            # 执行后钩子
            await self._after_execute(context, result)

            # 更新统计
            self._success_count += 1
            result.execution_time_ms = (time.time() - start_time) * 1000
            self._total_execution_time_ms += result.execution_time_ms
            self._status = SkillStatus.READY
            self._last_executed_at = time.time()

            return result

        except Exception as e:
            self._error_count += 1
            await self._on_error(e)
            self._status = SkillStatus.ERROR
            self._last_executed_at = time.time()
            execution_time_ms = (time.time() - start_time) * 1000
            self._total_execution_time_ms += execution_time_ms
            return SkillExecutionResult.failure(
                skill_name=self.name,
                sub_task=context.sub_task,
                error=str(e),
                execution_time_ms=execution_time_ms,
            )

    @abstractmethod
    async def _execute(
        self,
        context: SkillExecutionContext
    ) -> SkillExecutionResult:
        """执行核心逻辑 - 子类必须实现

        Args:
            context: 执行上下文

        Returns:
            SkillExecutionResult: 执行结果
        """
        pass

    async def _before_execute(
        self,
        context: SkillExecutionContext
    ) -> None:
        """执行前钩子 - 子类可重写

        Args:
            context: 执行上下文
        """
        pass

    async def _after_execute(
        self,
        context: SkillExecutionContext,
        result: SkillExecutionResult
    ) -> None:
        """执行后钩子 - 子类可重写

        Args:
            context: 执行上下文
            result: 执行结果
        """
        pass

    async def _on_error(self, error: Exception) -> None:
        """错误处理钩子 - 子类可重写

        Args:
            error: 异常对象
        """
        pass

    async def shutdown(self) -> bool:
        """关闭技能

        Returns:
            bool: 关闭是否成功
        """
        try:
            result = await self._on_shutdown()
            self._status = SkillStatus.INACTIVE
            return result
        except Exception as e:
            await self._on_error(e)
            return False

    @abstractmethod
    async def _on_shutdown(self) -> bool:
        """关闭钩子 - 子类实现

        Returns:
            bool: 关闭是否成功
        """
        return True

    def can_handle(self, intent: str) -> bool:
        """检查技能是否能处理某个意图

        Args:
            intent: 意图字符串

        Returns:
            bool: 是否能处理
        """
        if not self.config.triggers:
            return False
        intent_lower = intent.lower()
        return any(trigger.lower() in intent_lower for trigger in self.config.triggers)

    def get_metadata(self) -> Dict[str, Any]:
        """获取技能元数据

        Returns:
            Dict[str, Any]: 元数据字典
        """
        return {
            "name": self.name,
            "version": self.version,
            "description": self.config.description,
            "author": self.config.author,
            "tags": self.config.tags,
            "triggers": self.config.triggers,
            "status": self.status.value,
            "created_at": self.created_at,
            "last_executed_at": self.last_executed_at,
            "execution_count": self.execution_count,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "avg_execution_time_ms": self.avg_execution_time_ms,
        }

    def __str__(self):
        return f"{self.name} (v{self.version}) - {self.status.value}"

    def __repr__(self):
        return f"{self.__class__.__name__}(name={self.name}, version={self.version}, status={self.status.value})"
