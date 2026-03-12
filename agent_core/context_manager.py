"""
Context Manager - 上下文管理器

提供三层上下文管理和渐进式披露功能
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List, Callable
import time
import uuid
import copy


class ContextPermission(Enum):
    """上下文权限"""
    NONE = "none"
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


@dataclass
class ContextAccessLog:
    """上下文访问日志"""
    timestamp: float
    layer: str
    key: str
    operation: str  # "read" or "write"
    source: str
    duration_ms: float
    success: bool
    error_message: Optional[str] = None


@dataclass
class LayerConfig:
    """层配置"""
    name: str
    permission_key: str
    initial_data: Dict[str, Any] = field(default_factory=dict)
    enable_access_log: bool = True
    max_access_logs: int = 1000


class ContextLayer(ABC):
    """上下文层基类 - 使用模板方法模式"""

    def __init__(self, config: LayerConfig):
        self._config = config
        self._data: Dict[str, Any] = copy.deepcopy(config.initial_data)
        self._access_logs: List[ContextAccessLog] = []
        self._permission_checker: Optional[Callable] = None
        self._created_at = time.time()

    @property
    def name(self) -> str:
        """获取层名称"""
        return self._config.name

    @property
    def permission_key(self) -> str:
        """获取权限键"""
        return self._config.permission_key

    @property
    def created_at(self) -> float:
        """创建时间"""
        return self._created_at

    def set_permission_checker(self, checker: Callable) -> None:
        """设置权限检查器（策略模式）

        Args:
            checker: 权限检查函数，签名为 check(layer_key, operation, key) -> bool
        """
        self._permission_checker = checker

    def _check_permission(self, operation: str, key: str) -> bool:
        """检查权限（模板方法，可重写）

        Args:
            operation: 操作类型
            key: 访问的键

        Returns:
            bool: 是否有权限
        """
        if self._permission_checker:
            return self._permission_checker(self._config.permission_key, operation, key)
        return True  # 默认允许

    def _before_access(self, operation: str, key: str) -> None:
        """访问前钩子（可重写）

        Args:
            operation: 操作类型
            key: 访问的键
        """
        pass

    def _after_access(
        self,
        operation: str,
        key: str,
        success: bool,
        duration_ms: float,
        source: str = "",
        error: Optional[str] = None
    ) -> None:
        """访问后钩子（可重写）

        Args:
            operation: 操作类型
            key: 访问的键
            success: 是否成功
            duration_ms: 耗时（毫秒）
            source: 来源
            error: 错误信息
        """
        if self._config.enable_access_log:
            log = ContextAccessLog(
                timestamp=time.time(),
                layer=self._config.name,
                key=key,
                operation=operation,
                source=source,
                duration_ms=duration_ms,
                success=success,
                error_message=error
            )
            self._access_logs.append(log)
            # 限制日志数量
            if len(self._access_logs) > self._config.max_access_logs:
                self._access_logs = self._access_logs[-self._config.max_access_logs:]

    # ========== 模板方法：统一读写接口 ==========

    def write(self, key: str, value: Any, source: str = "") -> None:
        """统一的写入方法（模板方法）

        Args:
            key: 键
            value: 值
            source: 来源
        """
        start_time = time.time()

        try:
            # 1. 访问前钩子
            self._before_access("write", key)

            # 2. 权限检查
            if not self._check_permission("write", key):
                raise PermissionError(f"No write permission for {self._config.name}.{key}")

            # 3. 具体写入逻辑（由子类实现）
            self._do_write(key, value)

            # 4. 访问后钩子
            duration_ms = (time.time() - start_time) * 1000
            self._after_access("write", key, True, duration_ms, source)

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._after_access("write", key, False, duration_ms, source, str(e))
            raise

    def read(self, key: str, source: str = "") -> Any:
        """统一的读取方法（模板方法）

        Args:
            key: 键
            source: 来源

        Returns:
            Any: 值
        """
        start_time = time.time()

        try:
            # 1. 访问前钩子
            self._before_access("read", key)

            # 2. 权限检查
            if not self._check_permission("read", key):
                raise PermissionError(f"No read permission for {self._config.name}.{key}")

            # 3. 具体读取逻辑（由子类实现）
            value = self._do_read(key)

            # 4. 访问后钩子
            duration_ms = (time.time() - start_time) * 1000
            self._after_access("read", key, True, duration_ms, source)

            return value

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._after_access("read", key, False, duration_ms, source, str(e))
            raise

    def has(self, key: str) -> bool:
        """检查键是否存在

        Args:
            key: 键

        Returns:
            bool: 是否存在
        """
        return key in self._data

    def keys(self) -> List[str]:
        """获取所有键

        Returns:
            List[str]: 键列表
        """
        return list(self._data.keys())

    def clear(self) -> None:
        """清除所有数据"""
        self._data.clear()

    def get_all(self) -> Dict[str, Any]:
        """获取所有数据（只读副本）

        Returns:
            Dict[str, Any]: 数据副本
        """
        return copy.deepcopy(self._data)

    def get_access_logs(self, limit: int = 100) -> List[ContextAccessLog]:
        """获取访问日志

        Args:
            limit: 返回数量限制

        Returns:
            List[ContextAccessLog]: 访问日志
        """
        return list(self._access_logs[-limit:])

    @abstractmethod
    def _do_write(self, key: str, value: Any) -> None:
        """具体的写入逻辑（子类必须实现）

        Args:
            key: 键
            value: 值
        """
        pass

    @abstractmethod
    def _do_read(self, key: str) -> Any:
        """具体的读取逻辑（子类必须实现）

        Args:
            key: 键

        Returns:
            Any: 值
        """
        pass


class Layer1UserInput(ContextLayer):
    """第一层：用户输入层

    存储用户输入、解析意图、执行计划、对话历史
    """

    DEFAULT_DATA = {
        "raw_user_input": "",
        "parsed_intent": None,
        "execution_plan": None,
        "conversation_history": [],
    }

    def __init__(self, initial_data: Optional[Dict[str, Any]] = None):
        data = {**self.DEFAULT_DATA, **(initial_data or {})}
        config = LayerConfig(
            name="layer1",
            permission_key="layer1_user_input",
            initial_data=data,
        )
        super().__init__(config)

    def _do_write(self, key: str, value: Any) -> None:
        """写入数据

        Args:
            key: 键
            value: 值
        """
        self._data[key] = value

    def _do_read(self, key: str) -> Any:
        """读取数据

        Args:
            key: 键

        Returns:
            Any: 值
        """
        return self._data.get(key)


class Layer2Scratchpad(ContextLayer):
    """第二层：工作记忆/临时存储

    存储技能执行结果、中间状态
    """

    def __init__(self):
        config = LayerConfig(
            name="layer2",
            permission_key="layer2_scratchpad",
            initial_data={},
        )
        super().__init__(config)
        self._step_results: Dict[str, Any] = {}
        self._failed_steps: List[Dict] = []
        self._history: List[Dict] = []
        self._current_step: int = 0

    @property
    def current_step(self) -> int:
        """当前步骤"""
        return self._current_step

    @current_step.setter
    def current_step(self, value: int) -> None:
        self._current_step = value

    def _do_write(self, key: str, value: Any) -> None:
        """写入数据

        Args:
            key: 键
            value: 值
        """
        self._step_results[key] = value
        self._history.append({
            "timestamp": time.time(),
            "operation": "write",
            "key": key,
        })

    def _do_read(self, key: str) -> Any:
        """读取数据

        Args:
            key: 键

        Returns:
            Any: 值
        """
        return self._step_results.get(key)

    def set_result(
        self,
        skill_name: str,
        sub_task: str,
        structured: Dict[str, Any],
        text: str,
        success: bool = True,
        error: str = "",
        execution_time_ms: float = 0
    ) -> None:
        """设置技能执行结果

        Args:
            skill_name: 技能名称
            sub_task: 子任务
            structured: 结构化数据
            text: 文本数据
            success: 是否成功
            error: 错误信息
            execution_time_ms: 执行时间
        """
        key = f"{skill_name}_{sub_task}" if sub_task else skill_name
        self._step_results[key] = {
            "skill_name": skill_name,
            "sub_task": sub_task,
            "structured": structured,
            "text": text,
            "success": success,
            "error": error,
            "execution_time_ms": execution_time_ms,
            "timestamp": time.time(),
        }

    def get_result(self, skill_name: str) -> Optional[Dict[str, Any]]:
        """获取技能执行结果

        Args:
            skill_name: 技能名称

        Returns:
            Optional[Dict[str, Any]]: 结果
        """
        # 尝试直接匹配
        if skill_name in self._step_results:
            return self._step_results[skill_name]

        # 尝试前缀匹配
        for key, value in self._step_results.items():
            if key.startswith(f"{skill_name}_"):
                return value

        return None

    def get_all_results(self) -> Dict[str, Any]:
        """获取所有结果

        Returns:
            Dict[str, Any]: 所有结果
        """
        return self._step_results.copy()

    def get_ordered_results(self) -> List[Dict[str, Any]]:
        """获取有序的结果列表

        Returns:
            List[Dict[str, Any]]: 结果列表
        """
        return list(self._step_results.values())

    def record_failure(self, step: Dict, error: str, attempt: int = 1) -> None:
        """记录失败步骤

        Args:
            step: 步骤
            error: 错误信息
            attempt: 尝试次数
        """
        self._failed_steps.append({
            "step": step,
            "error": error,
            "attempt": attempt,
            "timestamp": time.time(),
        })

    def compress_result(self, skill_name: str) -> bool:
        """压缩结果

        Args:
            skill_name: 技能名称

        Returns:
            bool: 是否成功
        """
        result = self.get_result(skill_name)
        if result:
            # 只保留成功标记和摘要
            key = f"{skill_name}_compressed"
            self._step_results[key] = {
                "skill_name": skill_name,
                "compressed": True,
                "success": result.get("success", True),
                "timestamp": time.time(),
            }
            return True
        return False

    def get_summary(self) -> Dict[str, Any]:
        """获取摘要

        Returns:
            Dict[str, Any]: 摘要
        """
        return {
            "total_results": len(self._step_results),
            "total_failed": len(self._failed_steps),
            "current_step": self._current_step,
            "skill_names": list(self._step_results.keys()),
        }


class Layer3Environment(ContextLayer):
    """第三层：环境配置层

    存储可用技能、token预算、模型配置、工具注册表
    """

    DEFAULT_DATA = {
        "available_skills": {},
        "token_budget": None,
        "model_config": {},
        "tools_registry": None,
    }

    def __init__(self, initial_data: Optional[Dict[str, Any]] = None):
        data = {**self.DEFAULT_DATA, **(initial_data or {})}
        config = LayerConfig(
            name="layer3",
            permission_key="layer3_environment",
            initial_data=data,
        )
        super().__init__(config)

    def _do_write(self, key: str, value: Any) -> None:
        """写入数据

        Args:
            key: 键
            value: 值
        """
        self._data[key] = value

    def _do_read(self, key: str) -> Any:
        """读取数据

        Args:
            key: 键

        Returns:
            Any: 值
        """
        return self._data.get(key)


@dataclass
class ContextManagerConfig:
    """上下文管理器配置"""
    enable_audit: bool = True
    enable_progressive_disclosure: bool = True
    max_history_length: int = 100
    max_scratchpad_size: int = 10 * 1024 * 1024  # 10MB


class ContextManager:
    """上下文管理器 - 整合三层上下文

    提供三层上下文的统一管理和渐进式披露功能
    """

    def __init__(self, config: Optional[ContextManagerConfig] = None):
        self._config = config or ContextManagerConfig()
        self._layer1 = Layer1UserInput()
        self._layer2 = Layer2Scratchpad()
        self._layer3 = Layer3Environment()
        self._current_component: Optional[str] = None
        self._created_at = time.time()
        self._request_id = str(uuid.uuid4())

        # 权限配置
        self._permissions: Dict[str, Dict[str, Dict[str, ContextPermission]]] = {}
        self._setup_default_permissions()

    @property
    def layer1(self) -> Layer1UserInput:
        """第一层：用户输入"""
        return self._layer1

    @property
    def layer2(self) -> Layer2Scratchpad:
        """第二层：工作记忆"""
        return self._layer2

    @property
    def layer3(self) -> Layer3Environment:
        """第三层：环境配置"""
        return self._layer3

    @property
    def request_id(self) -> str:
        """请求ID"""
        return self._request_id

    @property
    def created_at(self) -> float:
        """创建时间"""
        return self._created_at

    def _setup_default_permissions(self) -> None:
        """设置默认权限"""
        self._permissions = {
            "planner": {
                "layer1_user_input": {"any": ContextPermission.READ},
                "layer2_scratchpad": {},
                "layer3_environment": {"any": ContextPermission.READ},
            },
            "executor": {
                "layer1_user_input": {"any": ContextPermission.READ},
                "layer2_scratchpad": {"any": ContextPermission.WRITE},
                "layer3_environment": {"any": ContextPermission.READ},
            },
            "synthesizer": {
                "layer1_user_input": {"any": ContextPermission.READ},
                "layer2_scratchpad": {"any": ContextPermission.READ},
                "layer3_environment": {"any": ContextPermission.READ},
            },
            "coordinator": {
                "layer1_user_input": {"any": ContextPermission.WRITE},
                "layer2_scratchpad": {"any": ContextPermission.WRITE},
                "layer3_environment": {"any": ContextPermission.WRITE},
            },
        }

    def set_component(self, component: str) -> None:
        """设置当前组件（用于权限检查）

        Args:
            component: 组件名称
        """
        self._current_component = component

        # 设置权限检查器
        def permission_checker(layer_key: str, operation: str, key: str) -> bool:
            return self._check_permission(component, layer_key, operation, key)

        self._layer1.set_permission_checker(permission_checker)
        self._layer2.set_permission_checker(permission_checker)
        self._layer3.set_permission_checker(permission_checker)

    def _check_permission(
        self,
        component: str,
        layer_key: str,
        operation: str,
        key: str
    ) -> bool:
        """检查权限

        Args:
            component: 组件名称
            layer_key: 层键
            operation: 操作
            key: 键

        Returns:
            bool: 是否有权限
        """
        if component == "coordinator":
            return True

        component_perms = self._permissions.get(component, {})
        layer_perms = component_perms.get(layer_key, {})

        perm = layer_perms.get("any", ContextPermission.NONE)
        if key in layer_perms:
            perm = layer_perms[key]

        if operation == "read":
            return perm in (ContextPermission.READ, ContextPermission.WRITE, ContextPermission.ADMIN)
        elif operation == "write":
            return perm in (ContextPermission.WRITE, ContextPermission.ADMIN)
        return False

    # ========== 便捷方法 ==========

    def write_user_input(self, key: str, value: Any, source: str = "") -> None:
        """写入用户输入层

        Args:
            key: 键
            value: 值
            source: 来源
        """
        self._layer1.write(key, value, source)

    def read_user_input(self, key: str, source: str = "") -> Any:
        """读取用户输入层

        Args:
            key: 键
            source: 来源

        Returns:
            Any: 值
        """
        return self._layer1.read(key, source)

    def write_scratchpad(
        self,
        skill_name: str,
        sub_task: str,
        structured: Dict[str, Any],
        text: str,
        success: bool = True,
        error: str = "",
        execution_time_ms: float = 0,
        source: str = ""
    ) -> None:
        """写入工作记忆

        Args:
            skill_name: 技能名称
            sub_task: 子任务
            structured: 结构化数据
            text: 文本
            success: 是否成功
            error: 错误信息
            execution_time_ms: 执行时间
            source: 来源
        """
        self._layer2.set_result(
            skill_name, sub_task, structured, text, success, error, execution_time_ms
        )

    def read_scratchpad(self, skill_name: str = "", source: str = "") -> Any:
        """读取工作记忆

        Args:
            skill_name: 技能名称
            source: 来源

        Returns:
            Any: 值
        """
        if skill_name:
            return self._layer2.get_result(skill_name)
        return self._layer2.get_all_results()

    def write_environment(self, key: str, value: Any, source: str = "") -> None:
        """写入环境配置

        Args:
            key: 键
            value: 值
            source: 来源
        """
        self._layer3.write(key, value, source)

    def read_environment(self, key: str, source: str = "") -> Any:
        """读取环境配置

        Args:
            key: 键
            source: 来源

        Returns:
            Any: 值
        """
        return self._layer3.read(key, source)

    def prepare_for_step(
        self,
        step: Dict,
        include_history: bool = False
    ) -> Dict[str, Any]:
        """为步骤准备上下文（渐进式披露）

        Args:
            step: 步骤定义
            include_history: 是否包含对话历史

        Returns:
            Dict[str, Any]: 准备好的上下文
        """
        context = {
            "sub_task": step.get("sub_task", ""),
            "user_input": self._layer1.read("raw_user_input") or "",
            "previous_results": {},
            "conversation_history": [],
        }

        # 添加之前的技能结果（渐进式披露）
        ordered = self._layer2.get_ordered_results()
        for i, result in enumerate(ordered):
            if i == len(ordered) - 1:
                # 总是包含最新结果的完整信息
                context["previous_results"][result.get("skill_name", f"step_{i}")] = {
                    "structured": result.get("structured", {}),
                    "text": result.get("text", ""),
                }
            else:
                # 旧结果简化
                context["previous_results"][result.get("skill_name", f"step_{i}")] = {
                    "compressed": True,
                    "success": result.get("success", True),
                }

        # 添加对话历史
        if include_history:
            context["conversation_history"] = self._layer1.read("conversation_history") or []

        return context

    def get_summary(self) -> Dict[str, Any]:
        """获取上下文摘要

        Returns:
            Dict[str, Any]: 摘要
        """
        return {
            "request_id": self._request_id,
            "created_at": self._created_at,
            "current_component": self._current_component,
            "layer1_keys": self._layer1.keys(),
            "layer2_summary": self._layer2.get_summary(),
            "layer3_keys": self._layer3.keys(),
        }

    def get_audit_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取审计日志

        Args:
            limit: 数量限制

        Returns:
            List[Dict[str, Any]]: 审计日志
        """
        logs = []
        for layer in [self._layer1, self._layer2, self._layer3]:
            for log in layer.get_access_logs(limit):
                logs.append({
                    "timestamp": log.timestamp,
                    "layer": log.layer,
                    "key": log.key,
                    "operation": log.operation,
                    "source": log.source,
                    "duration_ms": log.duration_ms,
                    "success": log.success,
                    "error_message": log.error_message,
                })
        return sorted(logs, key=lambda x: x["timestamp"], reverse=True)[:limit]

    def clear(self) -> None:
        """清除所有上下文"""
        self._layer1.clear()
        self._layer2.clear()
        self._layer3.clear()
        self._request_id = str(uuid.uuid4())

    def __str__(self) -> str:
        return f"ContextManager(request_id={self._request_id}, component={self._current_component})"
