# 架构重构详细设计文档

## 1. 重构SkillRegistry

### 1.1 当前问题分析

**问题1：职责混淆**
- `SkillLoader`负责技能发现和加载
- `SkillRegistry`只是`SkillLoader`的简单包装
- 两者都维护`_skills`字典，存在数据冗余风险

**问题2：单例模式缺陷**
- 使用全局变量`_instance`，测试时难以重置状态
- 没有线程安全保障

**问题3：缺乏工业级功能**
- 没有健康检查机制
- 不支持热重载
- 没有指标收集
- 缺乏优雅关闭

### 1.2 工业级设计方案

**核心原则**：
1. **单一职责**：`SkillRegistry`只负责Skill的生命周期管理和访问控制
2. **依赖注入**：通过构造函数注入依赖，便于测试
3. **异步安全**：所有操作使用`asyncio.Lock`保护
4. **可观测性**：自动收集指标，支持健康检查

**类设计**：

```python
class SkillRegistry:
    """工业级Skill注册表 - 单一职责：Skill生命周期管理"""

    _instance: Optional["SkillRegistry"] = None
    _lock: asyncio.Lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    async def initialize(self, skills_dir: str, config: RegistryConfig) -> None:
        """初始化注册表"""
        # ... 初始化逻辑 ...

    async def get_skill(self, name: str) -> Optional[BaseSkill]:
        """获取Skill（自动健康检查）"""
        # ... 获取逻辑 ...

    async def execute_skill(self, name: str, context: SkillExecutionContext) -> SkillExecutionResult:
        """执行Skill（完整生命周期管理）"""
        # ... 执行逻辑 ...

    async def reload_skills(self) -> None:
        """热重载Skill（不停机更新）"""
        # ... 热重载逻辑 ...

    async def shutdown(self) -> None:
        """优雅关闭"""
        # ... 关闭逻辑 ...
```

**关键特性**：

1. **单例模式**：使用`__new__`实现真正的单例，确保全局唯一
2. **异步锁**：所有操作都使用`asyncio.Lock`保护，保证线程安全
3. **健康检查**：自动定期健康检查，不健康时尝试重新初始化
4. **热重载**：支持不停机更新Skill，自动处理版本切换
5. **指标收集**：自动收集执行指标，便于监控和优化
6. **优雅关闭**：支持优雅关闭，清理资源

**使用示例**：

```python
# 1. 创建注册表（单例）
registry = SkillRegistry()

# 2. 初始化
await registry.initialize("./skills", config)

# 3. 执行Skill
result = await registry.execute_skill("ecommerce_recommendation", context)

# 4. 热重载
await registry.reload_skills()

# 5. 优雅关闭
await registry.shutdown()
```

---

## 2. 重构三层上下文

### 2.1 当前问题分析

**问题：重复代码严重**

当前的三层上下文读写逻辑几乎完全相同：

```python
# Layer 1 的读写方法（约60行）
def write_layer1(self, key: str, value: Any, source: str = "") -> None:
    if not self._check_permission("layer1_user_input", "write", key):
        raise ContextValidationError(f"No write permission for layer1.{key}")
    # ... 重复代码：时间统计、写入、审计日志

def read_layer1(self, key: str, source: str = "") -> Any:
    if not self._check_permission("layer1_user_input", "read", key):
        raise ContextValidationError(f"No read permission for layer1.{key}")
    # ... 重复代码：时间统计、读取、审计日志

# Layer 2 的方法（约150行）
def write_scratchpad(self, ...): ...
def read_scratchpad(self, ...): ...

# Layer 3 的读写方法（约60行）
def write_layer3(self, key: str, value: Any, source: str = "") -> None:
    if not self._check_permission("layer3_environment", "write", key):
        raise ContextValidationError(f"No write permission for layer3.{key}")
    # ... 完全相同的模式
```

**问题分析**：
1. 三层上下文的读写逻辑几乎完全相同（权限检查→时间统计→数据操作→审计日志）
2. 只有`_check_permission()`的第一个参数不同
3. 大量重复代码使维护困难

### 2.2 工业级设计方案

**核心原则**：
1. **DRY原则**：提取通用逻辑，消除重复代码
2. **模板方法模式**：定义算法骨架，子类实现特定步骤
3. **策略模式**：不同的权限检查策略可以互换

**类设计**：

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Callable
from enum import Enum
import time
from dataclasses import dataclass

class ContextPermission(Enum):
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

class ContextLayer(ABC):
    """上下文层基类 - 使用模板方法模式"""

    def __init__(self, name: str, permission_key: str):
        self._name = name
        self._permission_key = permission_key
        self._data: Dict[str, Any] = {}
        self._access_logs: List[ContextAccessLog] = []
        self._permission_checker: Optional[Callable] = None

    def set_permission_checker(self, checker: Callable) -> None:
        """设置权限检查器（策略模式）"""
        self._permission_checker = checker

    def _check_permission(self, operation: str, key: str) -> bool:
        """检查权限（模板方法，可重写）"""
        if self._permission_checker:
            return self._permission_checker(self._permission_key, operation, key)
        return True  # 默认允许

    def _before_access(self, operation: str, key: str) -> None:
        """访问前钩子（可重写）"""
        pass

    def _after_access(self, operation: str, key: str, success: bool,
                     duration_ms: float, error: Optional[str] = None) -> None:
        """访问后钩子（可重写）"""
        # 记录访问日志
        log = ContextAccessLog(
            timestamp=time.time(),
            layer=self._name,
            key=key,
            operation=operation,
            source="",  # 可以从上下文获取
            duration_ms=duration_ms,
            success=success,
            error_message=error
        )
        self._access_logs.append(log)

    # ========== 模板方法：统一读写接口 ==========

    def write(self, key: str, value: Any, source: str = "") -> None:
        """统一的写入方法（模板方法）"""
        start_time = time.time()

        try:
            # 1. 访问前钩子
            self._before_access("write", key)

            # 2. 权限检查
            if not self._check_permission("write", key):
                raise PermissionError(f"No write permission for {self._name}.{key}")

            # 3. 具体写入逻辑（由子类实现）
            self._do_write(key, value)

            # 4. 访问后钩子
            duration_ms = (time.time() - start_time) * 1000
            self._after_access("write", key, True, duration_ms)

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._after_access("write", key, False, duration_ms, str(e))
            raise

    def read(self, key: str, source: str = "") -> Any:
        """统一的读取方法（模板方法）"""
        start_time = time.time()

        try:
            # 1. 访问前钩子
            self._before_access("read", key)

            # 2. 权限检查
            if not self._check_permission("read", key):
                raise PermissionError(f"No read permission for {self._name}.{key}")

            # 3. 具体读取逻辑（由子类实现）
            value = self._do_read(key)

            # 4. 访问后钩子
            duration_ms = (time.time() - start_time) * 1000
            self._after_access("read", key, True, duration_ms)

            return value

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._after_access("read", key, False, duration_ms, str(e))
            raise

    @abstractmethod
    def _do_write(self, key: str, value: Any) -> None:
        """具体的写入逻辑（子类必须实现）"""
        pass

    @abstractmethod
    def _do_read(self, key: str) -> Any:
        """具体的读取逻辑（子类必须实现）"""
        pass


# ==================== 具体实现 ====================

class Layer1UserInput(ContextLayer):
    """第一层：用户输入层"""

    def __init__(self):
        super().__init__("layer1", "layer1_user_input")
        self._data = {
            "raw_user_input": "",
            "parsed_intent": None,
            "execution_plan": None,
            "conversation_history": []
        }

    def _do_write(self, key: str, value: Any) -> None:
        if key not in self._data:
            raise KeyError(f"Unknown key: {key}")
        self._data[key] = value

    def _do_read(self, key: str) -> Any:
        if key not in self._data:
            raise KeyError(f"Unknown key: {key}")
        return self._data[key]


class Layer2Scratchpad(ContextLayer):
    """第二层：工作记忆/临时存储"""

    def __init__(self):
        super().__init__("layer2", "layer2_scratchpad")
        self._step_results: Dict[str, Any] = {}
        self._failed_steps: List[Dict] = []
        self._history: List[Dict] = []

    def _do_write(self, key: str, value: Any) -> None:
        # 支持动态key
        self._step_results[key] = value
        self._history.append({
            "timestamp": time.time(),
            "operation": "write",
            "key": key,
            "value": value
        })

    def _do_read(self, key: str) -> Any:
        if key not in self._step_results:
            raise KeyError(f"No result for step: {key}")
        return self._step_results[key]


class Layer3Environment(ContextLayer):
    """第三层：环境配置层"""

    def __init__(self):
        super().__init__("layer3", "layer3_environment")
        self._data = {
            "available_skills": [],
            "token_budget": None,
            "model_config": {},
            "tools_registry": None
        }

    def _do_write(self, key: str, value: Any) -> None:
        if key not in self._data:
            raise KeyError(f"Unknown key: {key}")
        self._data[key] = value

    def _do_read(self, key: str) -> Any:
        if key not in self._data:
            raise KeyError(f"Unknown key: {key}")
        return self._data[key]


# ==================== 整合：AgentContext ====================

class AgentContext:
    """整合的三层上下文"""

    def __init__(self, enable_audit: bool = True):
        self.layer1 = Layer1UserInput()
        self.layer2 = Layer2Scratchpad()
        self.layer3 = Layer3Environment()
        self._enable_audit = enable_audit
        self._audit_logs = []

    def set_permission_checker(self, checker: Callable) -> None:
        """设置权限检查器"""
        self.layer1.set_permission_checker(checker)
        self.layer2.set_permission_checker(checker)
        self.layer3.set_permission_checker(checker)

    # 便捷方法
    def write_user_input(self, key: str, value: Any, source: str = "") -> None:
        """写入用户输入层"""
        self.layer1.write(key, value, source)

    def read_user_input(self, key: str, source: str = "") -> Any:
        """读取用户输入层"""
        return self.layer1.read(key, source)

    def write_scratchpad(self, key: str, value: Any, source: str = "") -> None:
        """写入工作记忆"""
        self.layer2.write(key, value, source)

    def read_scratchpad(self, key: str, source: str = "") -> Any:
        """读取工作记忆"""
        return self.layer2.read(key, source)

    def write_environment(self, key: str, value: Any, source: str = "") -> None:
        """写入环境配置"""
        self.layer3.write(key, value, source)

    def read_environment(self, key: str, source: str = "") -> Any:
        """读取环境配置"""
        return self.layer3.read(key, source)

    def get_audit_logs(self) -> List[Dict]:
        """获取审计日志"""
        # 合并各层的审计日志
        logs = []
        for layer in [self.layer1, self.layer2, self.layer3]:
            if hasattr(layer, '_access_logs'):
                logs.extend(layer._access_logs)
        return sorted(logs, key=lambda x: x["timestamp"])
