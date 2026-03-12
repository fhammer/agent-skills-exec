"""
Extension System - 扩展系统

提供Plugin、Hook和Event机制，支持框架的扩展和定制
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List, Callable, Type, TypeVar, Generic, Set
import time
import uuid
import asyncio
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class EventPriority(Enum):
    """事件优先级"""
    LOWEST = 0
    LOW = 1
    NORMAL = 2
    HIGH = 3
    HIGHEST = 4


class HookPhase(Enum):
    """钩子阶段"""
    BEFORE = "before"
    AROUND = "around"
    AFTER = "after"
    ON_ERROR = "on_error"


class PluginState(Enum):
    """插件状态"""
    DISABLED = "disabled"
    LOADED = "loaded"
    INITIALIZED = "initialized"
    STARTED = "started"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class Event(Generic[T]):
    """事件"""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = ""
    source: str = ""
    timestamp: float = field(default_factory=time.time)
    data: Optional[T] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    propagated: bool = True
    cancelled: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "source": self.source,
            "timestamp": self.timestamp,
            "data": self.data,
            "metadata": self.metadata,
            "propagated": self.propagated,
            "cancelled": self.cancelled,
        }

    def cancel(self) -> None:
        """取消事件"""
        self.cancelled = True

    def stop_propagation(self) -> None:
        """停止传播"""
        self.propagated = False


@dataclass
class HookContext:
    """钩子上下文"""
    hook_name: str
    phase: HookPhase
    target: Any = None
    args: List[Any] = field(default_factory=list)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    result: Any = None
    error: Optional[Exception] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    proceed: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "hook_name": self.hook_name,
            "phase": self.phase.value,
            "args": self.args,
            "kwargs": self.kwargs,
            "result": self.result,
            "error": str(self.error) if self.error else None,
            "metadata": self.metadata,
            "proceed": self.proceed,
        }


@dataclass
class PluginConfig:
    """插件配置"""
    name: str
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    tags: List[str] = field(default_factory=list)
    enabled: bool = True
    priority: int = 0
    dependencies: List[str] = field(default_factory=list)
    custom_settings: Dict[str, Any] = field(default_factory=dict)


class Plugin(ABC):
    """插件抽象基类"""

    def __init__(self, config: PluginConfig):
        self.config = config
        self._state = PluginState.DISABLED
        self._loaded_at: Optional[float] = None
        self._started_at: Optional[float] = None

    @property
    def name(self) -> str:
        """插件名称"""
        return self.config.name

    @property
    def version(self) -> str:
        """插件版本"""
        return self.config.version

    @property
    def state(self) -> PluginState:
        """插件状态"""
        return self._state

    @property
    def loaded_at(self) -> Optional[float]:
        """加载时间"""
        return self._loaded_at

    @property
    def started_at(self) -> Optional[float]:
        """启动时间"""
        return self._started_at

    @abstractmethod
    async def load(self) -> bool:
        """加载插件

        Returns:
            bool: 是否成功
        """
        pass

    @abstractmethod
    async def unload(self) -> bool:
        """卸载插件

        Returns:
            bool: 是否成功
        """
        pass

    @abstractmethod
    async def initialize(self) -> bool:
        """初始化插件

        Returns:
            bool: 是否成功
        """
        pass

    @abstractmethod
    async def start(self) -> bool:
        """启动插件

        Returns:
            bool: 是否成功
        """
        pass

    @abstractmethod
    async def stop(self) -> bool:
        """停止插件

        Returns:
            bool: 是否成功
        """
        pass

    def get_hooks(self) -> Dict[str, List[Callable]]:
        """获取钩子列表

        Returns:
            Dict[str, List[Callable]]: 钩子字典
        """
        return {}

    def get_event_listeners(self) -> Dict[str, List[Callable]]:
        """获取事件监听器

        Returns:
            Dict[str, List[Callable]]: 事件监听器字典
        """
        return {}

    def get_metadata(self) -> Dict[str, Any]:
        """获取元数据

        Returns:
            Dict[str, Any]: 元数据
        """
        return {
            "name": self.name,
            "version": self.version,
            "description": self.config.description,
            "author": self.config.author,
            "tags": self.config.tags,
            "enabled": self.config.enabled,
            "priority": self.config.priority,
            "dependencies": self.config.dependencies,
            "state": self._state.value,
            "loaded_at": self._loaded_at,
            "started_at": self._started_at,
        }

    def __str__(self) -> str:
        return f"{self.name} (v{self.version}) - {self._state.value}"


class BasePlugin(Plugin):
    """插件基类 - 提供默认实现"""

    def __init__(self, config: PluginConfig):
        super().__init__(config)

    async def load(self) -> bool:
        """加载插件"""
        try:
            result = await self._on_load()
            if result:
                self._state = PluginState.LOADED
                self._loaded_at = time.time()
            return result
        except Exception as e:
            logger.error(f"Failed to load plugin {self.name}: {e}")
            self._state = PluginState.ERROR
            return False

    async def unload(self) -> bool:
        """卸载插件"""
        try:
            if self._state == PluginState.STARTED:
                await self.stop()

            result = await self._on_unload()
            if result:
                self._state = PluginState.DISABLED
            return result
        except Exception as e:
            logger.error(f"Failed to unload plugin {self.name}: {e}")
            return False

    async def initialize(self) -> bool:
        """初始化插件"""
        try:
            result = await self._on_initialize()
            if result:
                self._state = PluginState.INITIALIZED
            return result
        except Exception as e:
            logger.error(f"Failed to initialize plugin {self.name}: {e}")
            self._state = PluginState.ERROR
            return False

    async def start(self) -> bool:
        """启动插件"""
        try:
            if self._state != PluginState.INITIALIZED:
                await self.initialize()
                if self._state != PluginState.INITIALIZED:
                    return False

            result = await self._on_start()
            if result:
                self._state = PluginState.STARTED
                self._started_at = time.time()
            return result
        except Exception as e:
            logger.error(f"Failed to start plugin {self.name}: {e}")
            self._state = PluginState.ERROR
            return False

    async def stop(self) -> bool:
        """停止插件"""
        try:
            result = await self._on_stop()
            if result:
                self._state = PluginState.STOPPED
            return result
        except Exception as e:
            logger.error(f"Failed to stop plugin {self.name}: {e}")
            return False

    async def _on_load(self) -> bool:
        """加载钩子 - 子类可重写"""
        return True

    async def _on_unload(self) -> bool:
        """卸载钩子 - 子类可重写"""
        return True

    async def _on_initialize(self) -> bool:
        """初始化钩子 - 子类可重写"""
        return True

    async def _on_start(self) -> bool:
        """启动钩子 - 子类可重写"""
        return True

    async def _on_stop(self) -> bool:
        """停止钩子 - 子类可重写"""
        return True


@dataclass
class EventListener:
    """事件监听器"""
    listener_id: str
    event_type: str
    callback: Callable[[Event], None]
    priority: EventPriority = EventPriority.NORMAL
    once: bool = False
    async_callback: bool = False


@dataclass
class Hook:
    """钩子"""
    hook_id: str
    hook_name: str
    phase: HookPhase
    callback: Callable[[HookContext], Any]
    priority: int = 0
    async_callback: bool = False


@dataclass
class ExtensionManagerConfig:
    """扩展管理器配置"""
    enable_plugins: bool = True
    enable_events: bool = True
    enable_hooks: bool = True
    plugin_dir: str = "./plugins"
    auto_discover_plugins: bool = True
    enable_event_buffering: bool = False
    max_buffer_size: int = 1000


class ExtensionManager:
    """扩展管理器 - 统一管理插件、事件和钩子

    提供插件加载、事件发布、钩子执行等功能
    """

    def __init__(self, config: Optional[ExtensionManagerConfig] = None):
        self._config = config or ExtensionManagerConfig()
        self._plugins: Dict[str, Plugin] = {}
        self._event_listeners: Dict[str, List[EventListener]] = {}
        self._hooks: Dict[str, Dict[HookPhase, List[Hook]]] = {}
        self._event_buffer: List[Event] = []
        self._initialized = False
        self._created_at = time.time()
        self._event_counter = 0
        self._hook_counter = 0

    @property
    def plugins(self) -> Dict[str, Plugin]:
        """获取所有插件"""
        return self._plugins.copy()

    @property
    def initialized(self) -> bool:
        """是否已初始化"""
        return self._initialized

    async def initialize(self) -> bool:
        """初始化扩展管理器

        Returns:
            bool: 是否成功
        """
        if self._initialized:
            return True

        try:
            # 自动发现并加载插件
            if self._config.enable_plugins and self._config.auto_discover_plugins:
                await self._discover_and_load_plugins()

            self._initialized = True
            logger.info("ExtensionManager initialized")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize ExtensionManager: {e}")
            return False

    async def _discover_and_load_plugins(self) -> None:
        """发现并加载插件"""
        # 这里可以实现自动发现逻辑
        # 暂时留空，等待插件目录结构定义
        pass

    # ========== 插件管理 ==========

    async def register_plugin(self, plugin: Plugin) -> bool:
        """注册插件

        Args:
            plugin: 插件实例

        Returns:
            bool: 是否成功
        """
        if plugin.name in self._plugins:
            logger.warning(f"Plugin {plugin.name} already registered")
            return False

        try:
            self._plugins[plugin.name] = plugin

            # 加载插件
            if plugin.config.enabled:
                loaded = await plugin.load()
                if loaded:
                    # 注册钩子和事件监听器
                    await self._register_plugin_hooks(plugin)
                    await self._register_plugin_listeners(plugin)
                    logger.info(f"Plugin {plugin.name} registered and loaded")
                return loaded

            return True

        except Exception as e:
            logger.error(f"Failed to register plugin {plugin.name}: {e}")
            if plugin.name in self._plugins:
                del self._plugins[plugin.name]
            return False

    async def _register_plugin_hooks(self, plugin: Plugin) -> None:
        """注册插件钩子"""
        hooks = plugin.get_hooks()
        for hook_name, callbacks in hooks.items():
            for callback in callbacks:
                phase = HookPhase.BEFORE
                if hasattr(callback, "_hook_phase"):
                    phase = getattr(callback, "_hook_phase")
                self.register_hook(hook_name, phase, callback)

    async def _register_plugin_listeners(self, plugin: Plugin) -> None:
        """注册插件事件监听器"""
        listeners = plugin.get_event_listeners()
        for event_type, callbacks in listeners.items():
            for callback in callbacks:
                self.add_listener(event_type, callback)

    async def unregister_plugin(self, name: str) -> bool:
        """注销插件

        Args:
            name: 插件名称

        Returns:
            bool: 是否成功
        """
        plugin = self._plugins.get(name)
        if not plugin:
            return False

        try:
            await plugin.unload()
            del self._plugins[name]
            logger.info(f"Plugin {name} unregistered")
            return True

        except Exception as e:
            logger.error(f"Failed to unregister plugin {name}: {e}")
            return False

    async def start_plugin(self, name: str) -> bool:
        """启动插件

        Args:
            name: 插件名称

        Returns:
            bool: 是否成功
        """
        plugin = self._plugins.get(name)
        if not plugin:
            return False
        return await plugin.start()

    async def stop_plugin(self, name: str) -> bool:
        """停止插件

        Args:
            name: 插件名称

        Returns:
            bool: 是否成功
        """
        plugin = self._plugins.get(name)
        if not plugin:
            return False
        return await plugin.stop()

    def get_plugin(self, name: str) -> Optional[Plugin]:
        """获取插件

        Args:
            name: 插件名称

        Returns:
            Optional[Plugin]: 插件实例
        """
        return self._plugins.get(name)

    def list_plugins(self, state: Optional[PluginState] = None) -> List[Plugin]:
        """列出插件

        Args:
            state: 状态过滤

        Returns:
            List[Plugin]: 插件列表
        """
        plugins = list(self._plugins.values())
        if state:
            plugins = [p for p in plugins if p.state == state]
        return plugins

    # ========== 事件系统 ==========

    def add_listener(
        self,
        event_type: str,
        callback: Callable[[Event], None],
        priority: EventPriority = EventPriority.NORMAL,
        once: bool = False
    ) -> str:
        """添加事件监听器

        Args:
            event_type: 事件类型
            callback: 回调函数
            priority: 优先级
            once: 是否只触发一次

        Returns:
            str: 监听器ID
        """
        if not self._config.enable_events:
            return ""

        listener_id = str(uuid.uuid4())
        listener = EventListener(
            listener_id=listener_id,
            event_type=event_type,
            callback=callback,
            priority=priority,
            once=once,
            async_callback=asyncio.iscoroutinefunction(callback),
        )

        if event_type not in self._event_listeners:
            self._event_listeners[event_type] = []

        self._event_listeners[event_type].append(listener)
        # 按优先级排序
        self._event_listeners[event_type].sort(key=lambda l: l.priority.value, reverse=True)

        return listener_id

    def remove_listener(self, listener_id: str) -> bool:
        """移除事件监听器

        Args:
            listener_id: 监听器ID

        Returns:
            bool: 是否成功
        """
        for event_type, listeners in self._event_listeners.items():
            for i, listener in enumerate(listeners):
                if listener.listener_id == listener_id:
                    del listeners[i]
                    return True
        return False

    def emit(self, event: Event) -> None:
        """同步发布事件

        Args:
            event: 事件
        """
        if not self._config.enable_events:
            return

        self._event_counter += 1

        # 缓冲事件
        if self._config.enable_event_buffering:
            self._event_buffer.append(event)
            if len(self._event_buffer) > self._config.max_buffer_size:
                self._event_buffer = self._event_buffer[-self._config.max_buffer_size:]

        # 获取监听器
        listeners = self._event_listeners.get(event.event_type, [])
        listeners.extend(self._event_listeners.get("*", []))  # 全局监听器

        # 按优先级排序
        listeners.sort(key=lambda l: l.priority.value, reverse=True)

        # 调用监听器
        to_remove = []
        for listener in listeners:
            if event.cancelled:
                break
            if not event.propagated:
                break

            try:
                if listener.async_callback:
                    # 异步回调，创建任务但不等待
                    asyncio.create_task(listener.callback(event))
                else:
                    listener.callback(event)

                if listener.once:
                    to_remove.append(listener.listener_id)
            except Exception as e:
                logger.error(f"Error in event listener for {event.event_type}: {e}")

        # 移除一次性监听器
        for listener_id in to_remove:
            self.remove_listener(listener_id)

    async def emit_async(self, event: Event) -> None:
        """异步发布事件

        Args:
            event: 事件
        """
        if not self._config.enable_events:
            return

        self._event_counter += 1

        if self._config.enable_event_buffering:
            self._event_buffer.append(event)
            if len(self._event_buffer) > self._config.max_buffer_size:
                self._event_buffer = self._event_buffer[-self._config.max_buffer_size:]

        listeners = self._event_listeners.get(event.event_type, [])
        listeners.extend(self._event_listeners.get("*", []))
        listeners.sort(key=lambda l: l.priority.value, reverse=True)

        to_remove = []
        for listener in listeners:
            if event.cancelled:
                break
            if not event.propagated:
                break

            try:
                if listener.async_callback:
                    await listener.callback(event)
                else:
                    listener.callback(event)

                if listener.once:
                    to_remove.append(listener.listener_id)
            except Exception as e:
                logger.error(f"Error in event listener for {event.event_type}: {e}")

        for listener_id in to_remove:
            self.remove_listener(listener_id)

    # ========== 钩子系统 ==========

    def register_hook(
        self,
        hook_name: str,
        phase: HookPhase,
        callback: Callable[[HookContext], Any],
        priority: int = 0
    ) -> str:
        """注册钩子

        Args:
            hook_name: 钩子名称
            phase: 钩子阶段
            callback: 回调函数
            priority: 优先级

        Returns:
            str: 钩子ID
        """
        if not self._config.enable_hooks:
            return ""

        hook_id = str(uuid.uuid4())
        hook = Hook(
            hook_id=hook_id,
            hook_name=hook_name,
            phase=phase,
            callback=callback,
            priority=priority,
            async_callback=asyncio.iscoroutinefunction(callback),
        )

        if hook_name not in self._hooks:
            self._hooks[hook_name] = {
                HookPhase.BEFORE: [],
                HookPhase.AROUND: [],
                HookPhase.AFTER: [],
                HookPhase.ON_ERROR: [],
            }

        self._hooks[hook_name][phase].append(hook)
        self._hooks[hook_name][phase].sort(key=lambda h: h.priority, reverse=True)

        return hook_id

    def unregister_hook(self, hook_id: str) -> bool:
        """注销钩子

        Args:
            hook_id: 钩子ID

        Returns:
            bool: 是否成功
        """
        for hook_name, phases in self._hooks.items():
            for phase, hooks in phases.items():
                for i, hook in enumerate(hooks):
                    if hook.hook_id == hook_id:
                        del hooks[i]
                        return True
        return False

    async def execute_hook(
        self,
        hook_name: str,
        context: HookContext,
        execute_around: Optional[Callable] = None
    ) -> HookContext:
        """执行钩子

        Args:
            hook_name: 钩子名称
            context: 钩子上下文
            execute_around: 环绕执行函数

        Returns:
            HookContext: 钩子上下文
        """
        if not self._config.enable_hooks:
            return context

        self._hook_counter += 1

        hooks = self._hooks.get(hook_name, {})

        try:
            # BEFORE 阶段
            context.phase = HookPhase.BEFORE
            for hook in hooks.get(HookPhase.BEFORE, []):
                if not context.proceed:
                    break
                context = await self._call_hook(hook, context)

            # AROUND 阶段
            context.phase = HookPhase.AROUND
            if execute_around:
                for hook in hooks.get(HookPhase.AROUND, []):
                    if not context.proceed:
                        break
                    context = await self._call_hook(hook, context)

                if context.proceed:
                    try:
                        context.result = await execute_around()
                    except Exception as e:
                        context.error = e
            else:
                for hook in hooks.get(HookPhase.AROUND, []):
                    if not context.proceed:
                        break
                    context = await self._call_hook(hook, context)

            # AFTER 阶段
            context.phase = HookPhase.AFTER
            for hook in hooks.get(HookPhase.AFTER, []):
                context = await self._call_hook(hook, context)

        except Exception as e:
            context.error = e
            # ON_ERROR 阶段
            context.phase = HookPhase.ON_ERROR
            for hook in hooks.get(HookPhase.ON_ERROR, []):
                context = await self._call_hook(hook, context)

        return context

    async def _call_hook(self, hook: Hook, context: HookContext) -> HookContext:
        """调用钩子

        Args:
            hook: 钩子
            context: 钩子上下文

        Returns:
            HookContext: 钩子上下文
        """
        try:
            if hook.async_callback:
                result = await hook.callback(context)
            else:
                result = hook.callback(context)

            if isinstance(result, HookContext):
                return result
            return context

        except Exception as e:
            logger.error(f"Error in hook {hook.hook_id}: {e}")
            return context

    def create_event(
        self,
        event_type: str,
        source: str,
        data: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Event:
        """创建事件

        Args:
            event_type: 事件类型
            source: 来源
            data: 数据
            metadata: 元数据

        Returns:
            Event: 事件
        """
        return Event(
            event_type=event_type,
            source=source,
            data=data,
            metadata=metadata or {},
        )

    def create_hook_context(
        self,
        hook_name: str,
        args: Optional[List[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        target: Any = None
    ) -> HookContext:
        """创建钩子上下文

        Args:
            hook_name: 钩子名称
            args: 位置参数
            kwargs: 关键字参数
            target: 目标对象

        Returns:
            HookContext: 钩子上下文
        """
        return HookContext(
            hook_name=hook_name,
            phase=HookPhase.BEFORE,
            target=target,
            args=args or [],
            kwargs=kwargs or {},
        )

    def get_metrics(self) -> Dict[str, Any]:
        """获取指标

        Returns:
            Dict[str, Any]: 指标
        """
        return {
            "initialized": self._initialized,
            "created_at": self._created_at,
            "total_plugins": len(self._plugins),
            "plugins_by_state": {
                state.value: len([p for p in self._plugins.values() if p.state == state])
                for state in PluginState
            },
            "event_types": list(self._event_listeners.keys()),
            "total_events": self._event_counter,
            "hook_names": list(self._hooks.keys()),
            "total_hooks": self._hook_counter,
            "buffered_events": len(self._event_buffer),
        }

    async def shutdown(self) -> None:
        """关闭"""
        # 停止所有插件
        for name in list(self._plugins.keys()):
            await self.unregister_plugin(name)

        # 清除
        self._plugins.clear()
        self._event_listeners.clear()
        self._hooks.clear()
        self._event_buffer.clear()
        self._initialized = False

    def __str__(self) -> str:
        return f"ExtensionManager(plugins={len(self._plugins)}, events={self._event_counter}, hooks={self._hook_counter})"


# 装饰器
def hook(hook_name: str, phase: HookPhase = HookPhase.BEFORE, priority: int = 0):
    """钩子装饰器

    Args:
        hook_name: 钩子名称
        phase: 钩子阶段
        priority: 优先级

    Returns:
        装饰器
    """
    def decorator(func):
        func._hook_name = hook_name
        func._hook_phase = phase
        func._hook_priority = priority
        return func
    return decorator


def event_listener(event_type: str, priority: EventPriority = EventPriority.NORMAL, once: bool = False):
    """事件监听器装饰器

    Args:
        event_type: 事件类型
        priority: 优先级
        once: 是否只触发一次

    Returns:
        装饰器
    """
    def decorator(func):
        func._event_type = event_type
        func._event_priority = priority
        func._event_once = once
        return func
    return decorator
