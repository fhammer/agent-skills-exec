# Agent Core - 通用智能体框架核心模块

## 概述

`agent_core` 是通用智能体框架的核心模块，提供了完整的智能体抽象基类、技能注册管理、上下文管理、扩展系统和业务集成适配器。

## 目录结构

```
agent_core/
├── __init__.py              # 模块入口
├── base/                    # 核心抽象基类
│   ├── __init__.py
│   ├── agent.py            # Agent 基类
│   ├── skill.py            # Skill 基类
│   ├── tool.py             # Tool 基类
│   └── connector.py        # Connector 基类
├── skill_registry.py        # 技能注册和热重载机制
├── context_manager.py       # 三层上下文管理
├── extension_system.py      # 扩展系统（Plugin、Hook、Event）
└── business_adapter.py      # 业务系统集成适配器
```

## 核心功能

### 1. 核心抽象基类

#### Agent（智能体基类）
- 定义智能体的核心接口和生命周期管理
- 支持初始化、暂停、恢复、关闭等状态管理
- 内置性能指标收集和审计日志功能

#### BaseSkill（技能基类）
- 定义技能的核心执行接口
- 支持技能的生命周期管理（初始化、执行、关闭）
- 内置执行前后钩子和错误处理
- 支持意图匹配和健康检查

#### BaseTool（工具基类）
- 定义工具的调用接口
- 支持工具的生命周期管理
- 参数验证和执行统计

#### BaseConnector（连接器基类）
- 定义数据连接器的核心接口
- 支持连接管理（连接、断开、重连）
- 健康检查和心跳机制
- 请求/响应模式和流式支持

### 2. 技能注册和热重载机制

#### SkillRegistry
- 单例模式的技能注册表
- 自动技能发现和加载
- 支持热重载（不停机更新技能）
- 健康检查和指标收集
- 生命周期管理

### 3. 三层上下文管理

#### ContextManager
- Layer 1: 用户输入层（原始输入、解析意图、执行计划）
- Layer 2: 工作记忆层（技能执行结果、中间状态）
- Layer 3: 环境配置层（可用技能、token预算、工具注册表）
- 权限控制和渐进式披露
- 审计日志记录

### 4. 扩展系统

#### ExtensionManager
- 插件管理（加载、卸载、启动、停止）
- 事件系统（事件发布、监听）
- 钩子系统（BEFORE、AROUND、AFTER、ON_ERROR阶段）
- 装饰器支持（@hook、@event_listener）

### 5. 业务系统集成适配器

#### BusinessAdapter
- 适配器模式，支持与外部系统集成
- 同步/异步请求支持
- 连接池和自动重连
- 请求/响应序列化
- 健康检查和监控

## 快速开始

### 实现自定义 Agent

```python
from agent_core.base.agent import Agent, AgentConfig, AgentState

class MyAgent(Agent):
    async def initialize(self) -> bool:
        # 初始化逻辑
        return True

    async def process(self, user_input: str, context: dict = None) -> dict:
        # 处理逻辑
        return {"result": "Processed"}

    async def pause(self) -> bool: return True
    async def resume(self) -> bool: return True
    async def shutdown(self) -> bool: return True
    def get_audit_trail(self) -> list: return []
    def get_config(self) -> dict: return {}

# 使用
config = AgentConfig(name="MyAgent", version="1.0.0")
agent = MyAgent(config)
await agent.initialize()
result = await agent.process("Hello!")
```

### 实现自定义 Skill

```python
from agent_core.base.skill import BaseSkill, SkillConfig, SkillExecutionContext, SkillExecutionResult

class CalculatorSkill(BaseSkill):
    async def _on_initialize(self) -> bool:
        return True

    async def _execute(self, context: SkillExecutionContext) -> SkillExecutionResult:
        result = self._calculate(context.user_input)
        return SkillExecutionResult.success(
            self.name,
            context.sub_task,
            {"result": result},
            f"计算结果: {result}"
        )

    async def _on_shutdown(self) -> bool:
        return True

    def can_handle(self, intent: str) -> bool:
        return "计算" in intent or "calculate" in intent.lower()

# 使用
config = SkillConfig(
    name="calculator",
    version="1.0.0",
    triggers=["计算", "calculate"]
)
skill = CalculatorSkill(config)
await skill.initialize()
```

### 使用 Skill Registry

```python
from agent_core.skill_registry import SkillRegistry, RegistryConfig

# 初始化注册表
config = RegistryConfig(
    skills_dir="./skills",
    enable_auto_discovery=True,
    enable_hot_reload=True,
    enable_health_check=True
)
registry = SkillRegistry()
await registry.initialize(config)

# 获取并执行技能
skill = await registry.get_skill("calculator")
context = SkillExecutionContext(
    sub_task="计算任务",
    user_input="10 + 5"
)
result = await registry.execute_skill("calculator", context)

# 热重载
await registry.reload_skills()
```

### 使用 Context Manager

```python
from agent_core.context_manager import ContextManager, ContextManagerConfig

# 初始化上下文管理器
config = ContextManagerConfig(
    enable_audit=True,
    enable_progressive_disclosure=True
)
context_manager = ContextManager(config)

# 设置当前组件
context_manager.set_component("coordinator")

# 写入/读取各层数据
context_manager.write_user_input("raw_user_input", "Hello World!", "source")
user_input = context_manager.read_user_input("raw_user_input")

context_manager.write_scratchpad(
    skill_name="calculator",
    sub_task="task1",
    structured={"result": 15},
    text="计算完成"
)
```

### 使用 Extension System

```python
from agent_core.extension_system import (
    ExtensionManager, ExtensionManagerConfig,
    BasePlugin, PluginConfig,
    hook, event_listener, HookPhase,
    Event
)

# 实现插件
class MyPlugin(BasePlugin):
    async def _on_load(self) -> bool:
        print("Plugin loaded")
        return True

    async def _on_start(self) -> bool:
        print("Plugin started")
        return True

    @hook("request_received", HookPhase.BEFORE)
    def on_request_received(self, context):
        print(f"Request received: {context}")

    @event_listener("user_message")
    def on_user_message(self, event):
        print(f"User message: {event.data}")

# 初始化扩展管理器
config = ExtensionManagerConfig()
manager = ExtensionManager(config)
await manager.initialize()

# 注册插件
plugin_config = PluginConfig(name="my_plugin", version="1.0.0")
plugin = MyPlugin(plugin_config)
await manager.register_plugin(plugin)
await manager.start_plugin("my_plugin")

# 发布事件
event = manager.create_event("user_message", "system", {"text": "Hello!"})
manager.emit(event)

# 执行钩子
hook_context = manager.create_hook_context("request_received", args=[1, 2, 3])
result = await manager.execute_hook("request_received", hook_context)
```

## 架构设计原则

1. **单一职责原则**：每个类只负责一个功能
2. **依赖注入**：通过构造函数注入依赖，便于测试
3. **模板方法模式**：定义算法骨架，子类实现具体步骤
4. **策略模式**：不同实现可以互换
5. **观察者模式**：事件系统实现松耦合
6. **钩子模式**：在关键点插入自定义逻辑

## 许可证

MIT License
