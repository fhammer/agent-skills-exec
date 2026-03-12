# 通用智能体开发框架 - 架构设计文档

**版本**: 1.0.0
**日期**: 2026-03-10
**作者**: AI架构师
**状态**: 设计完成

---

## 目录

1. [概述](#概述)
2. [整体架构](#整体架构)
3. [核心组件设计](#核心组件设计)
4. [数据流设计](#数据流设计)
5. [扩展机制](#扩展机制)
6. [与业务系统集成方案](#与业务系统集成方案)
7. [关键设计决策](#关键设计决策)
8. [附录](#附录)

---

## 概述

### 设计目标

基于现有的Agent Skills Framework代码库，本架构设计定义了通用智能体开发框架的技术架构，旨在：

1. **保持现有优势** - 三层上下文、双执行引擎、渐进式披露等核心架构
2. **补齐企业级能力** - 多租户、API服务、监控告警、数据连接器
3. **提升开发者体验** - CLI工具、SDK、文档、示例

### 架构原则

| 原则 | 说明 | 体现 |
|------|------|------|
| **向后兼容** | 不破坏现有框架API | 新能力以扩展模块形式提供 |
| **渐进增强** | 核心框架保持轻量，能力按需启用 | 多租户、API服务等可独立部署 |
| **配置驱动** | 通过配置而非代码控制行为 | YAML/JSON配置覆盖代码逻辑 |
| **可观测优先** | 所有操作可追踪、可审计 | 全链路日志、指标、追踪 |

---

## 整体架构

### 架构概览图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           通用智能体开发框架 (GADF)                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                         应用层 (Application)                           │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │ │
│  │  │   智能导购   │  │   售后客服   │  │   自定义应用  │  ...         │ │
│  │  │    Agent     │  │    Agent     │  │              │               │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘               │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                    ▲                                        │
│                                    │ HTTP/WebSocket                         │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                         API 网关层 (API Gateway)                       │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │ │
│  │  │   认证鉴权   │  │   限流熔断   │  │   路由分发   │               │ │
│  │  │    Auth      │  │ Rate Limit   │  │   Routing    │               │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘               │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                    ▲                                        │
│                                    │                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                      框架核心层 (Framework Core)                        │ │
│  │                                                                       │ │
│  │  ┌───────────────────────────────────────────────────────────────┐   │ │
│  │  │                    One Coordinator                           │   │ │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │   │ │
│  │  │  │   Planner   │  │  Executor   │  │ Synthesizer │          │   │ │
│  │  │  │   规划器    │  │   执行器    │  │   合成器    │          │   │ │
│  │  │  └─────────────┘  └─────────────┘  └─────────────┘          │   │ │
│  │  └───────────────────────────────────────────────────────────────┘   │ │
│  │                              ▲                                       │ │
│  │                              │                                       │ │
│  │  ┌───────────────────────────────────────────────────────────────┐   │ │
│  │  │               Three-Layer Context 三层上下文                  │   │ │
│  │  │                                                               │   │ │
│  │  │  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐ │   │ │
│  │  │  │   Layer 1       │  │   Layer 2       │  │   Layer 3      │ │   │ │
│  │  │  │  User Input     │  │  Scratchpad     │  │  Environment   │ │   │ │
│  │  │  │  用户输入层      │  │  工作记忆层      │  │  环境配置层    │ │   │ │
│  │  │  └─────────────────┘  └─────────────────┘  └────────────────┘ │   │ │
│  │  └───────────────────────────────────────────────────────────────┘   │ │
│  │                                                                       │ │
│  │  ┌───────────────────────────────────────────────────────────────┐   │ │
│  │  │                    Multiple Skills                            │   │ │
│  │  │                                                               │   │ │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │   │ │
│  │  │  │  Skill 1    │  │  Skill 2    │  │  Skill N    │  ...     │   │ │
│  │  │  │  (插件化)   │  │  (插件化)   │  │  (插件化)   │           │   │ │
│  │  │  └─────────────┘  └─────────────┘  └─────────────┘           │   │ │
│  │  │                                                               │   │ │
│  │  │  执行模式:                                                     │   │ │
│  │  │  1. executor.py  - 自定义Python代码                          │   │ │
│  │  │  2. prompt.template - LLM模板                                │   │ │
│  │  │  3. SKILL.md    - 文档即Skill                               │   │ │
│  │  └───────────────────────────────────────────────────────────────┘   │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                    扩展能力层 (Extensions)                              │ │
│  │                                                                       │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │ │
│  │  │   多租户管理 │  │   数据连接器  │  │   监控可观测  │               │ │
│  │  │Multi-Tenancy │  │  Connectors  │  │ Observability│               │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘               │ │
│  │                                                                       │ │
│  │  特点: 框架核心保持轻量，扩展能力按需启用                               │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 核心架构特性

1. **One Coordinator**: 统一的协调器负责整个执行流程的编排
2. **Three-Layer Context**: 三层上下文系统（用户输入/工作记忆/环境配置）
3. **Multiple Skills**: 插件化的Skill系统，支持三种执行模式
4. **Progressive Disclosure**: 渐进式上下文披露，Token效率最大化
5. **Extensions**: 可插拔的扩展能力层，按需启用

---

## 核心组件设计

### 3.1 Skill系统（插件化架构）

#### SkillRegistry (单例模式)

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
        pass

    async def get_skill(self, name: str) -> Optional[BaseSkill]:
        """获取Skill（自动健康检查）"""
        pass

    async def execute_skill(self, name: str, context: SkillExecutionContext) -> SkillExecutionResult:
        """执行Skill（完整生命周期管理）"""
        pass

    async def reload_skills(self) -> None:
        """热重载Skill（不停机更新）"""
        pass

    async def shutdown(self) -> None:
        """优雅关闭"""
        pass
```

#### BaseSkill (抽象基类)

```python
class BaseSkill(ABC):
    """Skill抽象基类 - 所有Skill必须继承"""

    # 必需属性
    name: str = ""  # Skill唯一标识
    version: str = "1.0.0"  # 语义化版本
    description: str = ""  # Skill描述

    # 可选属性
    triggers: List[str] = []  # 触发词列表
    tags: List[str] = []  # 标签
    input_schema: Optional[Dict] = None  # 输入参数schema
    output_schema: Optional[Dict] = None  # 输出schema

    @abstractmethod
    async def validate_input(self, input_data: Dict[str, Any]) -> ValidationResult:
        """验证输入数据"""
        pass

    @abstractmethod
    async def execute(self, context: SkillExecutionContext) -> SkillExecutionResult:
        """执行Skill核心逻辑"""
        pass

    @abstractmethod
    async def validate_output(self, output_data: Dict[str, Any]) -> ValidationResult:
        """验证输出数据"""
        pass
```

#### 三种Skill执行模式

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Skill 执行模式                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │   Executor模式   │  │  Template模式   │  │  Document模式   │         │
│  │                 │  │                 │  │                 │         │
│  │ 1. 加载         │  │ 1. 读取模板      │  │ 1. 解析SKILL.md │         │
│  │    executor.py │  │    prompt.template│ │ 2. 构建系统提示  │         │
│  │ 2. 实例化Skill │  │ 2. 渲染模板      │  │ 3. LLM生成回复  │         │
│  │ 3. 调用execute │  │ 3. LLM生成回复  │  │                 │         │
│  │                 │  │                 │  │                 │         │
│  │ 适用场景:       │  │ 适用场景:        │  │ 适用场景:       │         │
│  │ - 复杂业务逻辑  │  │ - 标准LLM任务   │  │ - 简单问答      │         │
│  │ - 需要外部API  │  │ - 格式转换      │  │ - 快速原型      │         │
│  │ - 数据验证转换  │  │ - 文本生成      │  │ - 文档驱动      │         │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 三层上下文系统

#### ContextManager (模板方法模式)

```python
class ContextManager:
    """三层上下文管理器 - 使用模板方法模式"""

    def __init__(self):
        # 三层上下文存储
        self._layer1_user_input: Dict[str, Any] = {}
        self._layer2_scratchpad: Dict[str, Any] = {}
        self._layer3_environment: Dict[str, Any] = {}

        # 权限检查器
        self._permission_checker: Optional[Callable] = None

    def set_permission_checker(self, checker: Callable) -> None:
        """设置权限检查器"""
        self._permission_checker = checker

    def _check_permission(self, layer: str, operation: str, key: str) -> bool:
        """检查权限"""
        if self._permission_checker:
            return self._permission_checker(layer, operation, key)
        return True

    def _record_access(self, layer: str, operation: str, key: str,
                       duration_ms: float, success: bool) -> None:
        """记录访问日志"""
        # 实现审计日志记录
        pass

    # ===== Layer 1: User Input =====
    def write_layer1(self, key: str, value: Any, source: str = "") -> None:
        """写入Layer 1"""
        if not self._check_permission("layer1_user_input", "write", key):
            raise PermissionError(f"No write permission for layer1.{key}")

        start_time = time.time()
        try:
            self._layer1_user_input[key] = {
                "value": value,
                "source": source,
                "timestamp": datetime.now().isoformat()
            }
            self._record_access("layer1", "write", key,
                               (time.time() - start_time) * 1000, True)
        except Exception as e:
            self._record_access("layer1", "write", key,
                               (time.time() - start_time) * 1000, False)
            raise

    def read_layer1(self, key: str, source: str = "") -> Any:
        """读取Layer 1"""
        if not self._check_permission("layer1_user_input", "read", key):
            raise PermissionError(f"No read permission for layer1.{key}")

        start_time = time.time()
        try:
            data = self._layer1_user_input.get(key, {})
            value = data.get("value") if isinstance(data, dict) else data
            self._record_access("layer1", "read", key,
                               (time.time() - start_time) * 1000, True)
            return value
        except Exception as e:
            self._record_access("layer1", "read", key,
                               (time.time() - start_time) * 1000, False)
            raise

    # ===== Layer 2: Scratchpad =====
    def write_scratchpad(self, key: str, value: Any, source: str = "") -> None:
        """写入Layer 2"""
        if not self._check_permission("layer2_scratchpad", "write", key):
            raise PermissionError(f"No write permission for layer2.{key}")

        start_time = time.time()
        try:
            if key not in self._layer2_scratchpad:
                self._layer2_scratchpad[key] = []

            self._layer2_scratchpad[key].append({
                "value": value,
                "source": source,
                "timestamp": datetime.now().isoformat()
            })
            self._record_access("layer2", "write", key,
                               (time.time() - start_time) * 1000, True)
        except Exception as e:
            self._record_access("layer2", "write", key,
                               (time.time() - start_time) * 1000, False)
            raise

    def read_scratchpad(self, key: str, source: str = "") -> List[Any]:
        """读取Layer 2"""
        if not self._check_permission("layer2_scratchpad", "read", key):
            raise PermissionError(f"No read permission for layer2.{key}")

        start_time = time.time()
        try:
            entries = self._layer2_scratchpad.get(key, [])
            values = [entry.get("value") for entry in entries if isinstance(entry, dict)]
            self._record_access("layer2", "read", key,
                               (time.time() - start_time) * 1000, True)
            return values
        except Exception as e:
            self._record_access("layer2", "read", key,
                               (time.time() - start_time) * 1000, False)
            raise

    # ===== Layer 3: Environment =====
    def write_layer3(self, key: str, value: Any, source: str = "") -> None:
        """写入Layer 3"""
        if not self._check_permission("layer3_environment", "write", key):
            raise PermissionError(f"No write permission for layer3.{key}")

        start_time = time.time()
        try:
            self._layer3_environment[key] = {
                "value": value,
                "source": source,
                "timestamp": datetime.now().isoformat()
            }
            self._record_access("layer3", "write", key,
                               (time.time() - start_time) * 1000, True)
        except Exception as e:
            self._record_access("layer3", "write", key,
                               (time.time() - start_time) * 1000, False)
            raise

    def read_layer3(self, key: str, source: str = "") -> Any:
        """读取Layer 3"""
        if not self._check_permission("layer3_environment", "read", key):
            raise PermissionError(f"No read permission for layer3.{key}")

        start_time = time.time()
        try:
            data = self._layer3_environment.get(key, {})
            value = data.get("value") if isinstance(data, dict) else data
            self._record_access("layer3", "read", key,
                               (time.time() - start_time) * 1000, True)
            return value
        except Exception as e:
            self._record_access("layer3", "read", key,
                               (time.time() - start_time) * 1000, False)
            raise
```

### 三层上下文数据流

```
用户请求处理流程:
─────────────────

┌──────────┐     ┌──────────────┐     ┌─────────────────┐     ┌──────────────┐
│  用户输入  │────▶│  API Gateway │────▶│  Tenant/Scene   │────▶│  Coordinator  │
│  (User)  │     │  (认证/限流)  │     │  (多租户路由)    │     │  (协调器)     │
└──────────┘     └──────────────┘     └─────────────────┘     └──────┬───────┘
                                                                    │
              ┌─────────────────────────────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                           Coordinator 执行流程                              │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐│
│  │   Step 1    │───▶│   Step 2    │───▶│   Step 3    │───▶│   Step N    ││
│  │  意图理解    │    │  需求分析    │    │  执行Skill  │    │  结果合成   ││
│  │             │    │             │    │             │    │             ││
│  │ Input:      │    │ Input:      │    │ Input:      │    │ Input:      ││
│  │ 用户原始输入 │    │ 意图+槽位   │    │ 结构化需求  │    │ Skill执行结果││
│  │             │    │             │    │             │    │             ││
│  │ Output:     │    │ Output:     │    │ Output:     │    │ Output:     ││
│  │ 意图+槽位   │───▶│ 结构化需求  │───▶│ Skill结果   │───▶│ 最终回复    ││
│  │             │    │             │    │             │    │             ││
│  │ Skill:      │    │ Skill:      │    │ Skill:      │    │             ││
│  │ intent_     │    │ demand_     │    │ product_    │    │ Synthesizer ││
│  │ classifier  │    │ analysis    │    │ search      │    │             ││
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘│
│           ▲                                                    │         │
│           │              ┌─────────────────────┐                 │         │
│           └──────────────│   Layer 2 (Scratchpad)  │◀────────────────┘         │
│                          │   - step_results     │                         │
│                          │   - failed_steps     │                         │
│                          └─────────────────────┘                         │
│                                    ▲                                     │
│                          ┌─────────┴─────────┐                           │
│                          │  Layer 1 (User)   │                           │
│                          │  - raw_user_input │                           │
│                          │  - parsed_intent  │                           │
│                          └─────────────────┘                           │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 核心组件设计

### 3.1 Coordinator (协调器)

```python
class Coordinator:
    """主协调器 - 编排整个执行流程"""

    def __init__(self, config: CoordinatorConfig):
        self.config = config
        self.planner = Planner(config.planner)
        self.executor = SkillExecutor(config.executor)
        self.synthesizer = Synthesizer(config.synthesizer)
        self.context_manager = ContextManager()
        self.audit_logger = AuditLogger()

    async def process(self, user_input: str, session_id: str = None) -> ProcessResult:
        """处理用户请求的主流程"""

        # 1. 初始化会话和上下文
        context = await self._initialize_context(user_input, session_id)

        # 2. 意图理解和规划
        plan = await self.planner.create_plan(context)

        # 3. 执行计划
        execution_results = []
        for step in plan.steps:
            result = await self.executor.execute(step, context)
            execution_results.append(result)

            # 更新上下文
            await self._update_context(context, step, result)

            # 检查是否需要重新规划
            if result.requires_replanning:
                plan = await self.planner.replan(context, plan)

        # 4. 合成最终响应
        final_response = await self.synthesizer.synthesize(
            execution_results, context
        )

        # 5. 记录审计日志
        await self._log_audit(context, execution_results, final_response)

        return ProcessResult(
            response=final_response,
            session_id=context.session_id,
            metrics=self._collect_metrics(context)
        )
```

### 3.2 Skill注册表

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
        self._skills_dir = skills_dir
        self._config = config
        self._skills: Dict[str, BaseSkill] = {}
        self._health_status: Dict[str, HealthStatus] = {}
        self._execution_stats: Dict[str, ExecutionStats] = {}

        # 发现并注册所有Skill
        await self._discover_and_register_skills()

        # 启动健康检查任务
        if self._config.enable_health_check:
            asyncio.create_task(self._health_check_loop())

        self._initialized = True

    async def get_skill(self, name: str) -> Optional[BaseSkill]:
        """获取Skill（自动健康检查）"""
        skill = self._skills.get(name)
        if skill and self._config.enable_health_check:
            health = self._health_status.get(name)
            if health and health.status != "healthy":
                # 尝试重新初始化
                await self._reinitialize_skill(name)
                skill = self._skills.get(name)
        return skill

    async def execute_skill(self, name: str, context: SkillExecutionContext) -> SkillExecutionResult:
        """执行Skill（完整生命周期管理）"""
        skill = await self.get_skill(name)
        if not skill:
            raise SkillNotFoundError(f"Skill not found: {name}")

        start_time = time.time()
        try:
            # 1. 验证输入
            validation = await skill.validate_input(context.input_data)
            if not validation.is_valid:
                return SkillExecutionResult(
                    success=False,
                    error=ValidationError(validation.errors),
                    execution_time=time.time() - start_time
                )

            # 2. 执行Skill
            result = await skill.execute(context)

            # 3. 验证输出
            output_validation = await skill.validate_output(result.output_data)
            if not output_validation.is_valid:
                return SkillExecutionResult(
                    success=False,
                    error=ValidationError(output_validation.errors),
                    execution_time=time.time() - start_time
                )

            # 更新执行统计
            self._update_execution_stats(name, True, time.time() - start_time)

            return SkillExecutionResult(
                success=True,
                output=result.output_data,
                execution_time=time.time() - start_time
            )

        except Exception as e:
            self._update_execution_stats(name, False, time.time() - start_time)
            return SkillExecutionResult(
                success=False,
                error=e,
                execution_time=time.time() - start_time
            )

    async def reload_skills(self) -> None:
        """热重载Skill（不停机更新）"""
        # 1. 备份当前状态
        backup = self._skills.copy()

        try:
            # 2. 重新发现Skill
            new_skills = await self._discover_skills()

            # 3. 计算差异
            added = set(new_skills.keys()) - set(backup.keys())
            removed = set(backup.keys()) - set(new_skills.keys())
            updated = set(new_skills.keys()) & set(backup.keys())

            # 4. 应用变更
            for name in removed:
                del self._skills[name]

            for name in added:
                self._skills[name] = new_skills[name]

            for name in updated:
                # 检查版本变化
                if backup[name].version != new_skills[name].version:
                    self._skills[name] = new_skills[name]

        except Exception as e:
            # 回滚到备份
            self._skills = backup
            raise ReloadError(f"Failed to reload skills: {e}")

    async def shutdown(self) -> None:
        """优雅关闭"""
        # 1. 停止接受新请求
        self._initialized = False

        # 2. 等待进行中的执行完成
        # (可以通过信号量或计数器实现)

        # 3. 清理资源
        self._skills.clear()
        self._health_status.clear()
        self._execution_stats.clear()

        # 4. 重置单例
        SkillRegistry._instance = None
```

---

## 数据流设计

### 4.1 请求处理流程

```
用户请求 → API Gateway → 租户/场景路由 → Coordinator → 规划 → 执行 → 合成 → 响应
```

### 4.2 数据流详解

```python
# 1. 用户输入层 (Layer 1)
layer1_data = {
    "raw_user_input": "我想买一部手机",
    "parsed_intent": {
        "primary_intent": "product_search",
        "confidence": 0.95,
        "slots": {"category": "手机"}
    },
    "execution_plan": [...],
    "conversation_history": [...]
}

# 2. 工作记忆层 (Layer 2)
layer2_data = {
    "step_results": {
        "demand_analysis": {...},
        "product_search": {...}
    },
    "current_step": 2,
    "failed_steps": [],
    "history": [...]
}

# 3. 环境配置层 (Layer 3)
layer3_data = {
    "available_skills": [...],
    "token_budget": {"total": 100000, "used": 15000},
    "model_config": {...},
    "tools_registry": {...}
}
```

---

## 扩展机制

### 5.1 Skill扩展机制

```python
# 1. 继承BaseSkill
class MyCustomSkill(BaseSkill):
    name = "my_custom_skill"
    version = "1.0.0"
    description = "My custom skill"

    async def validate_input(self, input_data: Dict) -> ValidationResult:
        # 验证逻辑
        pass

    async def execute(self, context: SkillExecutionContext) -> SkillExecutionResult:
        # 执行逻辑
        pass

    async def validate_output(self, output_data: Dict) -> ValidationResult:
        # 验证逻辑
        pass

# 2. 自动注册
# 将Skill放在 skills/ 目录下，自动发现并注册
```

### 5.2 数据连接器扩展

```python
# 继承BaseConnector
class MyCustomConnector(BaseConnector):
    """自定义数据连接器"""

    async def connect(self) -> bool:
        # 建立连接
        pass

    async def disconnect(self) -> bool:
        # 断开连接
        pass

    async def health_check(self) -> Dict[str, Any]:
        # 健康检查
        pass

    # 自定义查询方法
    async def custom_query(self, query: str) -> Any:
        pass
```

---

## 与业务系统集成方案

### 6.1 集成架构

```
业务系统 (ERP/CRM/电商平台)
    │
    │ REST API / GraphQL / WebSocket
    │
    ▼
┌─────────────────────────────────────┐
│      数据连接器层 (Connectors)       │
│  ┌──────────────┐  ┌──────────────┐ │
│  │  Database    │  │  HTTP API    │ │
│  │  Connector   │  │  Connector   │ │
│  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────┘
    │
    │ Tools注册到框架
    │
    ▼
┌─────────────────────────────────────┐
│      框架核心层 (Framework Core)      │
│  ┌──────────────┐  ┌──────────────┐ │
│  │  Coordinator │  │  SkillRegistry│ │
│  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────┘
```

### 6.2 集成示例

```python
# 1. 配置数据连接器
config = {
    "data_sources": {
        "product_db": {
            "type": "postgresql",
            "connection_string": "${PRODUCT_DB_URL}",
            "pool_size": 20
        },
        "order_api": {
            "type": "http",
            "base_url": "https://api.orders.com/v1",
            "auth": {"type": "bearer", "token": "${API_TOKEN}"}
        }
    }
}

# 2. 注册为Tools
@tool("query_products")
async def query_products(category: str, min_price: float = 0, max_price: float = float('inf')) -> List[Product]:
    """查询商品信息"""
    connector = await ConnectorRegistry.get("product_db")
    results = await connector.execute(
        "SELECT * FROM products WHERE category = $1 AND price BETWEEN $2 AND $3",
        [category, min_price, max_price]
    )
    return [Product.from_row(row) for row in results]

# 3. Skill使用Tool
class ProductSearchSkill(BaseSkill):
    name = "product_search"

    async def execute(self, context: SkillExecutionContext) -> SkillExecutionResult:
        # 调用Tool
        products = await query_products(
            category=context.input_data["category"],
            max_price=context.input_data.get("budget", float('inf'))
        )
        return SkillExecutionResult(
            success=True,
            output_data={"products": [p.to_dict() for p in products]}
        )
```

---

## 关键设计决策

### 7.1 Skill开发模式决策

| 决策点 | 决策 | 理由 |
|--------|------|------|
| 开发门槛 | 三种执行模式 | 覆盖不同技术水平开发者 |
| 复杂Skill | executor.py | Python代码适合复杂业务逻辑 |
| 标准任务 | prompt.template | 快速开发标准LLM任务 |
| 简单场景 | SKILL.md | 文档即Skill，最低门槛 |

### 7.2 多租户架构决策

| 决策点 | 决策 | 理由 |
|--------|------|------|
| 隔离级别 | 平台→租户→场景三级 | 满足电商多品牌/多业务线场景 |
| 配置继承 | 子级覆盖父级 | 减少重复配置，灵活性高 |
| 数据隔离 | 完全隔离 | 满足数据安全和隐私合规 |

### 7.3 性能与可扩展性决策

| 决策点 | 决策 | 理由 |
|--------|------|------|
| Skill加载 | 懒加载+热重载 | 减少启动时间，支持动态更新 |
| 上下文管理 | 分层+权限控制 | Token效率最大化，安全可控 |
| 数据连接 | 连接池+健康检查 | 高性能，高可用 |

---

## 附录

### A. 术语表

| 术语 | 定义 |
|------|------|
| Agent | 智能体，具有目标导向能力的AI系统 |
| Skill | 技能，Agent具备的特定能力模块 |
| Coordinator | 协调器，统一调度整个执行流程 |
| Context | 上下文，执行过程中的状态数据 |
| Tenant | 租户，框架的使用单位（企业/团队） |
| Scene | 场景，租户内的Agent实例，具有独立的Skill组合和配置 |
| Tool | 工具，Skill可调用的底层功能 |
| Connector | 连接器，标准化的数据源接入组件 |

### B. 参考资料

- 现有代码: `/agent/core/`, `/agent/intelligence/`, `/agent/memory/`
- 现有Demo: `/examples/smart_shopping_assistant/`
- 核心能力设计: `/docs/design/core-capabilities-design.md`
- 架构重构设计: `/ARCHITECTURE_REFACTOR_DESIGN.md`

---

**文档生成时间**: 2026-03-10
**版本**: 1.0.0
**状态**: 设计完成 ✅
