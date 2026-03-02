# Agent Skills Framework - 扩展性与业务集成详细设计

**版本**: 1.0.0
**日期**: 2026-02-28
**状态**: 设计中
**作者**: AI 架构师

---

## 目录

1. [扩展性设计重点](#1-扩展性设计重点)
2. [Skill注册机制](#2-skill注册机制)
3. [Tool系统扩展](#3-tool系统扩展)
4. [配置扩展](#4-配置扩展)
5. [生命周期钩子](#5-生命周期钩子)
6. [事件系统](#6-事件系统)
7. [数据转换层](#7-数据转换层)
8. [向后兼容](#8-向后兼容)
9. [电商Demo集成方案](#9-电商demo集成方案)
10. [附录](#10-附录)

---

## 1. 扩展性设计重点

### 1.1 设计目标

| 目标 | 说明 | 实现策略 |
|------|------|----------|
| **业务系统零侵入** | 业务系统不需要修改框架代码 | 提供注册接口、Hook机制、配置文件 |
| **热插拔** | Skill/Tool可以动态注册/卸载 | 动态加载、版本管理、依赖检查 |
| **配置驱动** | 通过配置扩展功能 | 配置合并、配置验证、配置热更新 |
| **事件驱动** | 关键节点发布事件 | 事件总线、订阅机制、异步处理 |

### 1.2 扩展点总览

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         扩展点总览 (Extension Points)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Skill 扩展点                                       │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │    │
│  │  │ 动态注册    │  │ 本地加载    │  │ 远程加载    │  │ 热更新      │  │    │
│  │  │ (API)      │  │ (文件系统)  │  │ (Git/HTTP) │  │ (Reload)   │  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Tool 扩展点                                       │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │    │
│  │  │ 自定义Tool │  │ 业务API包装│  │ 数据库连接  │  │ 外部服务   │  │    │
│  │  │ 注册      │  │ 成Tool     │  │ 封装成Tool │  │ 接入      │  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    配置扩展点                                        │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │    │
│  │  │ 配置合并    │  │ 配置验证    │  │ 配置热更新  │  │ 环境变量   │  │    │
│  │  │ (优先级)    │  │ (Schema)   │  │ (Watch)    │  │ 覆盖       │  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    生命周期钩子 (Hooks)                              │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │    │
│  │  │ pre_process│  │ pre_plan   │  │ pre_execute│  │ post_process│  │    │
│  │  │ (处理前)   │  │ (规划前)   │  │ (执行前)   │  │ (处理后)   │  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    事件系统 (Events)                                 │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │    │
│  │  │ AgentStart │  │ PlanCreated│  │ SkillExec  │  │ AgentComplete│  │    │
│  │  │ (启动)     │  │ (计划创建) │  │ (技能执行) │  │ (完成)      │  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Skill注册机制

### 2.1 设计目标

业务系统能够方便地注册自定义Skill，无需修改框架代码。

### 2.2 注册方式

```python
# ============================================================
# 方式1: API动态注册（推荐）
# ============================================================

from agent_framework import AgentClient

# 初始化客户端
client = AgentClient(
    api_key="sk_agent_xxxxx",
    base_url="https://agent-api.example.com"
)

# 创建Agent
agent = client.create_agent(
    name="ecommerce-assistant",
    description="电商助手"
)

# 注册自定义Skill（通过API）
agent.register_skill(
    name="order_query",
    version="1.0.0",
    description="查询订单状态",
    triggers=["查订单", "订单状态"],
    # Skill文件内容
    files={
        "SKILL.md": """
---
name: order_query
version: 1.0.0
description: 查询订单状态
triggers:
  - 查订单
  - 订单状态
tools:
  - query_order_api
---
""",
        "executor.py": """
def execute(llm, sub_task, context):
    # 调用业务系统API
    order_id = extract_order_id(sub_task)
    result = context.tools.query_order_api(order_id=order_id)

    return {
        "structured": result,
        "text": f"订单 {order_id} 状态: {result['status']}"
    }
"""
    }
)

# ============================================================
# 方式2: 本地文件系统加载（开发/测试）
# ============================================================

from agent_framework import LocalAgent

# 初始化本地Agent
agent = LocalAgent(
    skills_dir="./custom_skills",  # 自定义Skill目录
    config_path="./config.yaml"
)

# Skill目录结构
# ./custom_skills/
#   ├── order_query/
#   │   ├── SKILL.md
#   │   └── executor.py
#   └── product_recommend/
#       ├── SKILL.md
#       └── executor.py

# 运行时自动发现并加载

# ============================================================
# 方式3: 远程加载（Git/HTTP）
# ============================================================

# 从Git仓库加载
agent.register_skill_from_git(
    name="inventory_check",
    git_url="https://github.com/company/agent-skills.git",
    path="skills/inventory_check",
    branch="main",
    auth_token="ghp_xxxxx"  # 可选
)

# 从HTTP URL加载
agent.register_skill_from_url(
    name="payment_query",
    url="https://cdn.example.com/skills/payment_query.zip",
    checksum="sha256:xxxxx"  # 校验和
)

# ============================================================
# 方式4: 代码内联注册（简单场景）
# ============================================================

from agent_framework import Skill, SkillExecutor

# 定义Skill类
class OrderQuerySkill(Skill):
    name = "order_query"
    version = "1.0.0"
    description = "查询订单状态"
    triggers = ["查订单", "订单状态"]

    def execute(self, sub_task: str, context: dict) -> dict:
        # 业务逻辑
        order_id = self._extract_order_id(sub_task)
        result = context["tools"]["query_order_api"](order_id)

        return {
            "structured": result,
            "text": f"订单 {order_id} 状态: {result['status']}"
        }

# 注册
agent.register_skill_class(OrderQuerySkill)
```

### 2.3 Skill注册中心

```python
# ============================================================
# Skill注册中心设计
# ============================================================

from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import hashlib
import time


class SkillSource(Enum):
    """Skill来源"""
    BUILTIN = "builtin"      # 框架内置
    LOCAL_FILE = "local"     # 本地文件
    API_UPLOAD = "api"       # API上传
    GIT_REPO = "git"         # Git仓库
    HTTP_URL = "http"        # HTTP URL
    INLINE_CODE = "inline"   # 代码内联


class SkillStatus(Enum):
    """Skill状态"""
    PENDING = "pending"      # 待审核
    ACTIVE = "active"        # 已激活
    DISABLED = "disabled"  # 已禁用
    ERROR = "error"          # 加载错误
    DEPRECATED = "deprecated"  # 已弃用


@dataclass
class SkillMetadata:
    """Skill元数据"""
    name: str
    version: str
    description: str
    author: str
    created_at: float
    updated_at: float
    source: SkillSource
    status: SkillStatus
    tags: List[str]
    triggers: List[str]
    dependencies: List[str]  # 依赖的其他Skill
    required_tools: List[str]  # 依赖的Tool
    checksum: str  # 完整性校验

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "source": self.source.value,
            "status": self.status.value,
            "tags": self.tags,
            "triggers": self.triggers,
            "dependencies": self.dependencies,
            "required_tools": self.required_tools,
            "checksum": self.checksum
        }


class SkillRegistry:
    """
    Skill注册中心

    统一管理所有Skill的注册、发现、加载和生命周期管理
    支持多租户隔离、版本管理、依赖检查
    """

    def __init__(self, tenant_id: str = "default"):
        self._tenant_id = tenant_id
        self._skills: Dict[str, 'Skill'] = {}  # name -> Skill实例
        self._metadata: Dict[str, SkillMetadata] = {}  # name -> 元数据
        self._triggers: Dict[str, List[str]] = {}  # trigger -> [skill_names]
        self._hooks: Dict[str, List[Callable]] = {}  # event -> [handlers]

    # === 注册接口 ===

    def register(
        self,
        skill: 'Skill',
        metadata: SkillMetadata,
        overwrite: bool = False
    ) -> bool:
        """
        注册Skill

        Args:
            skill: Skill实例
            metadata: Skill元数据
            overwrite: 是否覆盖已存在的同名Skill

        Returns:
            是否注册成功
        """
        name = metadata.name

        # 检查是否已存在
        if name in self._skills and not overwrite:
            raise ValueError(f"Skill '{name}' already exists. Use overwrite=True to replace.")

        # 依赖检查
        for dep in metadata.dependencies:
            if dep not in self._skills:
                raise ValueError(f"Dependency '{dep}' not found for Skill '{name}'")

        # 注册
        self._skills[name] = skill
        self._metadata[name] = metadata

        # 更新trigger索引
        for trigger in metadata.triggers:
            if trigger not in self._triggers:
                self._triggers[trigger] = []
            if name not in self._triggers[trigger]:
                self._triggers[trigger].append(name)

        # 触发事件
        self._emit_event("skill.registered", {
            "name": name,
            "version": metadata.version,
            "source": metadata.source.value
        })

        return True

    def unregister(self, name: str) -> bool:
        """注销Skill"""
        if name not in self._skills:
            return False

        # 检查是否有其他Skill依赖它
        for skill_name, metadata in self._metadata.items():
            if name in metadata.dependencies:
                raise ValueError(f"Cannot unregister '{name}': required by '{skill_name}'")

        metadata = self._metadata[name]

        # 清理trigger索引
        for trigger in metadata.triggers:
            if trigger in self._triggers and name in self._triggers[trigger]:
                self._triggers[trigger].remove(name)

        # 移除
        del self._skills[name]
        del self._metadata[name]

        # 触发事件
        self._emit_event("skill.unregistered", {"name": name})

        return True

    # === 发现接口 ===

    def get(self, name: str) -> Optional['Skill']:
        """获取Skill实例"""
        return self._skills.get(name)

    def get_metadata(self, name: str) -> Optional[SkillMetadata]:
        """获取Skill元数据"""
        return self._metadata.get(name)

    def list_all(self) -> List[SkillMetadata]:
        """列出所有Skill"""
        return list(self._metadata.values())

    def find_by_trigger(self, text: str) -> List[SkillMetadata]:
        """根据触发词查找Skill"""
        matched = []
        for trigger, skill_names in self._triggers.items():
            if trigger.lower() in text.lower():
                for name in skill_names:
                    if name in self._metadata:
                        matched.append(self._metadata[name])
        return matched

    def find_by_tag(self, tag: str) -> List[SkillMetadata]:
        """根据标签查找Skill"""
        return [m for m in self._metadata.values() if tag in m.tags]

    # === 事件系统 ===

    def add_event_listener(self, event: str, handler: Callable) -> None:
        """添加事件监听器"""
        if event not in self._hooks:
            self._hooks[event] = []
        self._hooks[event].append(handler)

    def remove_event_listener(self, event: str, handler: Callable) -> None:
        """移除事件监听器"""
        if event in self._hooks and handler in self._hooks[event]:
            self._hooks[event].remove(handler)

    def _emit_event(self, event: str, data: dict) -> None:
        """触发事件"""
        if event in self._hooks:
            for handler in self._hooks[event]:
                try:
                    handler(data)
                except Exception as e:
                    # 记录错误但不中断
                    print(f"Event handler error: {e}")


# ============================================================
# 便捷的注册装饰器
# ============================================================

def skill(
    name: str,
    version: str = "1.0.0",
    description: str = "",
    triggers: List[str] = None,
    tags: List[str] = None,
    dependencies: List[str] = None,
    required_tools: List[str] = None
):
    """
    Skill注册装饰器

    使用示例:
    @skill(
        name="order_query",
        version="1.0.0",
        description="查询订单状态",
        triggers=["查订单", "订单状态"],
        tags=["电商", "订单"]
    )
    class OrderQuerySkill(Skill):
        def execute(self, sub_task: str, context: dict) -> dict:
            # 业务逻辑
            pass
    """
    def decorator(cls):
        # 保存元数据到类
        cls._skill_metadata = SkillMetadata(
            name=name,
            version=version,
            description=description,
            author="",
            created_at=time.time(),
            updated_at=time.time(),
            source=SkillSource.INLINE_CODE,
            status=SkillStatus.ACTIVE,
            tags=tags or [],
            triggers=triggers or [],
            dependencies=dependencies or [],
            required_tools=required_tools or [],
            checksum=""
        )
        return cls
    return decorator


def register_skill_class(registry: SkillRegistry, cls):
    """
    注册被@skill装饰的Skill类

    使用示例:
    registry = SkillRegistry()
    register_skill_class(registry, OrderQuerySkill)
    """
    if not hasattr(cls, '_skill_metadata'):
        raise ValueError(f"Class {cls.__name__} is not decorated with @skill")

    # 实例化
    instance = cls()

    # 注册
    registry.register(
        skill=instance,
        metadata=cls._skill_metadata
    )
