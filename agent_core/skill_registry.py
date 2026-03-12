"""
Skill Registry - 技能注册表

提供技能的注册、发现、热重载和生命周期管理功能
"""

import asyncio
import importlib
import importlib.util
import inspect
import json
import os
import sys
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, List, Set, Type, Callable, Tuple
import logging

from .base.skill import (
    BaseSkill,
    SkillConfig,
    SkillStatus,
    SkillExecutionContext,
    SkillExecutionResult,
)

logger = logging.getLogger(__name__)


class RegistryStatus(Enum):
    """注册表状态"""
    INITIALIZING = "initializing"
    READY = "ready"
    RELOADING = "reloading"
    SHUTTING_DOWN = "shutting_down"
    SHUTDOWN = "shutdown"
    ERROR = "error"


@dataclass
class RegistryConfig:
    """注册表配置"""
    skills_dir: str = "./skills"
    enable_auto_discovery: bool = True
    enable_hot_reload: bool = False
    hot_reload_interval_seconds: float = 5.0
    enable_health_check: bool = True
    health_check_interval_seconds: float = 30.0
    max_skills: int = 100
    enable_metrics: bool = True
    enable_caching: bool = True
    cache_ttl_seconds: int = 3600
    custom_settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SkillInfo:
    """技能信息"""
    name: str
    version: str
    path: str
    module_name: str
    skill_class: Type[BaseSkill]
    config: SkillConfig
    instance: Optional[BaseSkill] = None
    loaded_at: float = field(default_factory=time.time)
    last_modified_at: float = 0.0
    last_executed_at: Optional[float] = None
    is_enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "version": self.version,
            "path": self.path,
            "module_name": self.module_name,
            "config": {
                "name": self.config.name,
                "version": self.config.version,
                "description": self.config.description,
                "author": self.config.author,
                "tags": self.config.tags,
                "triggers": self.config.triggers,
                "timeout_seconds": self.config.timeout_seconds,
                "max_retries": self.config.max_retries,
            },
            "loaded_at": self.loaded_at,
            "last_modified_at": self.last_modified_at,
            "last_executed_at": self.last_executed_at,
            "is_enabled": self.is_enabled,
            "metadata": self.metadata,
            "instance_status": self.instance.status.value if self.instance else None,
            "execution_count": self.instance.execution_count if self.instance else 0,
            "success_count": self.instance.success_count if self.instance else 0,
            "error_count": self.instance.error_count if self.instance else 0,
        }


@dataclass
class RegistryMetrics:
    """注册表指标"""
    total_skills_registered: int = 0
    total_skills_loaded: int = 0
    total_skills_failed: int = 0
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    total_execution_time_ms: float = 0.0
    reload_count: int = 0
    last_reload_at: Optional[float] = None
    errors: List[Dict[str, Any]] = field(default_factory=list)


class SkillRegistry:
    """工业级技能注册表 - 单一职责：技能生命周期管理

    支持技能的注册、发现、加载、执行、热重载和健康检查
    """

    _instance: Optional["SkillRegistry"] = None
    _lock: asyncio.Lock = asyncio.Lock()
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_skills"):
            return
        self._skills: Dict[str, SkillInfo] = {}
        self._config: Optional[RegistryConfig] = None
        self._status = RegistryStatus.INITIALIZING
        self._metrics = RegistryMetrics()
        self._hot_reload_task: Optional[asyncio.Task] = None
        self._health_check_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        self._file_watchers: Dict[str, float] = {}

    @classmethod
    def get_instance(cls) -> "SkillRegistry":
        """获取单例实例

        Returns:
            SkillRegistry: 注册表实例
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def initialize(self, config: Optional[RegistryConfig] = None) -> bool:
        """初始化注册表

        Args:
            config: 注册表配置

        Returns:
            bool: 初始化是否成功
        """
        async with self._lock:
            if self._initialized:
                return True

            self._config = config or RegistryConfig()
            self._status = RegistryStatus.INITIALIZING

            try:
                # 确保技能目录存在
                skills_path = Path(self._config.skills_dir)
                if not skills_path.exists():
                    skills_path.mkdir(parents=True, exist_ok=True)
                    logger.warning(f"Skills directory created: {skills_path}")

                # 自动发现并加载技能
                if self._config.enable_auto_discovery:
                    await self._discover_and_load_skills()

                # 启动热重载
                if self._config.enable_hot_reload:
                    self._hot_reload_task = asyncio.create_task(self._hot_reload_loop())

                # 启动健康检查
                if self._config.enable_health_check:
                    self._health_check_task = asyncio.create_task(self._health_check_loop())

                self._status = RegistryStatus.READY
                self._initialized = True
                logger.info(f"SkillRegistry initialized with {len(self._skills)} skills")
                return True

            except Exception as e:
                self._status = RegistryStatus.ERROR
                logger.error(f"Failed to initialize SkillRegistry: {e}")
                self._record_error("initialize", str(e))
                return False

    async def _discover_and_load_skills(self) -> None:
        """发现并加载所有技能"""
        skills_path = Path(self._config.skills_dir)
        if not skills_path.exists():
            return

        # 添加技能目录到Python路径
        skills_dir_str = str(skills_path.absolute())
        if skills_dir_str not in sys.path:
            sys.path.insert(0, skills_dir_str)

        # 发现所有技能目录
        for skill_dir in skills_path.iterdir():
            if skill_dir.is_dir() and not skill_dir.name.startswith("_"):
                try:
                    await self._load_skill_from_directory(skill_dir)
                except Exception as e:
                    logger.error(f"Failed to load skill from {skill_dir}: {e}")
                    self._record_error("load_skill", str(e), {"directory": str(skill_dir)})
                    self._metrics.total_skills_failed += 1

    async def _load_skill_from_directory(self, skill_dir: Path) -> Optional[SkillInfo]:
        """从目录加载技能

        Args:
            skill_dir: 技能目录路径

        Returns:
            Optional[SkillInfo]: 加载的技能信息
        """
        # 检查是否有 SKILL.md
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            logger.debug(f"No SKILL.md in {skill_dir}, skipping")
            return None

        # 检查是否有 executor.py
        executor_py = skill_dir / "executor.py"
        if not executor_py.exists():
            logger.debug(f"No executor.py in {skill_dir}, skipping")
            return None

        # 构建模块名
        module_name = skill_dir.name
        file_path = str(executor_py)

        try:
            # 导入模块
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if not spec or not spec.loader:
                logger.warning(f"Could not create module spec for {module_name}")
                return None

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            # 查找继承BaseSkill的类
            skill_class = None
            for name, obj in inspect.getmembers(module):
                if (
                    inspect.isclass(obj)
                    and issubclass(obj, BaseSkill)
                    and obj != BaseSkill
                ):
                    skill_class = obj
                    break

            if not skill_class:
                logger.warning(f"No BaseSkill subclass found in {module_name}")
                return None

            # 创建技能配置
            config = SkillConfig(
                name=module_name,
                version="1.0.0",
                description=f"Skill loaded from {skill_dir}",
            )

            # 创建技能信息
            skill_info = SkillInfo(
                name=module_name,
                version=config.version,
                path=str(skill_dir),
                module_name=module_name,
                skill_class=skill_class,
                config=config,
                last_modified_at=executor_py.stat().st_mtime,
            )

            # 实例化并初始化技能
            skill_instance = skill_class(config)
            initialized = await skill_instance.initialize()
            if initialized:
                skill_info.instance = skill_instance
                self._skills[module_name] = skill_info
                self._metrics.total_skills_loaded += 1
                self._file_watchers[file_path] = executor_py.stat().st_mtime
                logger.info(f"Loaded skill: {module_name}")
                return skill_info
            else:
                logger.warning(f"Skill {module_name} failed to initialize")
                self._metrics.total_skills_failed += 1
                return None

        except Exception as e:
            logger.error(f"Error loading skill from {skill_dir}: {e}")
            self._record_error("load_skill", str(e), {"directory": str(skill_dir)})
            self._metrics.total_skills_failed += 1
            return None

    async def register_skill(
        self,
        skill_class: Type[BaseSkill],
        config: Optional[SkillConfig] = None
    ) -> bool:
        """注册技能

        Args:
            skill_class: 技能类
            config: 技能配置

        Returns:
            bool: 注册是否成功
        """
        async with self._lock:
            try:
                if config is None:
                    config = SkillConfig(name=skill_class.__name__)

                skill_name = config.name

                # 检查是否已存在
                if skill_name in self._skills:
                    logger.warning(f"Skill {skill_name} already registered, replacing")
                    await self._unload_skill(skill_name)

                # 创建技能信息
                skill_info = SkillInfo(
                    name=skill_name,
                    version=config.version,
                    path="",
                    module_name=skill_name,
                    skill_class=skill_class,
                    config=config,
                )

                # 实例化并初始化技能
                skill_instance = skill_class(config)
                initialized = await skill_instance.initialize()
                if initialized:
                    skill_info.instance = skill_instance
                    self._skills[skill_name] = skill_info
                    self._metrics.total_skills_registered += 1
                    self._metrics.total_skills_loaded += 1
                    logger.info(f"Registered skill: {skill_name}")
                    return True
                else:
                    logger.warning(f"Skill {skill_name} failed to initialize")
                    self._metrics.total_skills_failed += 1
                    return False

            except Exception as e:
                logger.error(f"Failed to register skill: {e}")
                self._record_error("register_skill", str(e))
                self._metrics.total_skills_failed += 1
                return False

    async def unregister_skill(self, name: str) -> bool:
        """注销技能

        Args:
            name: 技能名称

        Returns:
            bool: 注销是否成功
        """
        async with self._lock:
            return await self._unload_skill(name)

    async def _unload_skill(self, name: str) -> bool:
        """卸载技能（内部方法，不加锁）

        Args:
            name: 技能名称

        Returns:
            bool: 卸载是否成功
        """
        if name not in self._skills:
            return False

        try:
            skill_info = self._skills[name]
            if skill_info.instance:
                await skill_info.instance.shutdown()

            # 移除模块
            if skill_info.module_name in sys.modules:
                del sys.modules[skill_info.module_name]

            del self._skills[name]
            logger.info(f"Unloaded skill: {name}")
            return True

        except Exception as e:
            logger.error(f"Failed to unload skill {name}: {e}")
            self._record_error("unload_skill", str(e), {"skill": name})
            return False

    async def get_skill(self, name: str) -> Optional[BaseSkill]:
        """获取技能实例

        Args:
            name: 技能名称

        Returns:
            Optional[BaseSkill]: 技能实例
        """
        skill_info = self._skills.get(name)
        if skill_info and skill_info.is_enabled and skill_info.instance:
            return skill_info.instance
        return None

    def get_skill_info(self, name: str) -> Optional[SkillInfo]:
        """获取技能信息

        Args:
            name: 技能名称

        Returns:
            Optional[SkillInfo]: 技能信息
        """
        return self._skills.get(name)

    def list_skills(self, include_disabled: bool = False) -> List[SkillInfo]:
        """列出所有技能

        Args:
            include_disabled: 是否包含禁用的技能

        Returns:
            List[SkillInfo]: 技能信息列表
        """
        skills = list(self._skills.values())
        if not include_disabled:
            skills = [s for s in skills if s.is_enabled]
        return skills

    def get_all_skills(self) -> Dict[str, Dict[str, Any]]:
        """获取所有技能的元数据（兼容旧接口）

        Returns:
            Dict[str, Dict[str, Any]]: 技能元数据字典
        """
        return {
            name: info.to_dict()
            for name, info in self._skills.items()
            if info.is_enabled
        }

    async def execute_skill(
        self,
        name: str,
        context: SkillExecutionContext
    ) -> SkillExecutionResult:
        """执行技能

        Args:
            name: 技能名称
            context: 执行上下文

        Returns:
            SkillExecutionResult: 执行结果
        """
        self._metrics.total_executions += 1

        skill_info = self._skills.get(name)
        if not skill_info:
            result = SkillExecutionResult.failure(
                skill_name=name,
                sub_task=context.sub_task,
                error=f"Skill not found: {name}",
            )
            self._metrics.failed_executions += 1
            return result

        if not skill_info.is_enabled:
            result = SkillExecutionResult.failure(
                skill_name=name,
                sub_task=context.sub_task,
                error=f"Skill is disabled: {name}",
            )
            self._metrics.failed_executions += 1
            return result

        if not skill_info.instance:
            result = SkillExecutionResult.failure(
                skill_name=name,
                sub_task=context.sub_task,
                error=f"Skill not initialized: {name}",
            )
            self._metrics.failed_executions += 1
            return result

        try:
            # 执行技能
            result = await skill_info.instance.execute(context)

            # 更新统计
            skill_info.last_executed_at = time.time()
            self._metrics.total_execution_time_ms += result.execution_time_ms

            if result.success:
                self._metrics.successful_executions += 1
            else:
                self._metrics.failed_executions += 1

            return result

        except Exception as e:
            result = SkillExecutionResult.failure(
                skill_name=name,
                sub_task=context.sub_task,
                error=str(e),
            )
            self._metrics.failed_executions += 1
            self._record_error("execute_skill", str(e), {"skill": name})
            return result

    async def reload_skills(self) -> int:
        """热重载所有技能

        Returns:
            int: 重新加载的技能数量
        """
        async with self._lock:
            previous_status = self._status
            self._status = RegistryStatus.RELOADING

            try:
                reloaded_count = 0
                skills_to_reload = list(self._skills.keys())

                for name in skills_to_reload:
                    skill_info = self._skills.get(name)
                    if not skill_info or not skill_info.path:
                        continue

                    skill_dir = Path(skill_info.path)
                    executor_py = skill_dir / "executor.py"

                    if executor_py.exists():
                        mtime = executor_py.stat().st_mtime
                        if mtime > skill_info.last_modified_at:
                            await self._unload_skill(name)
                            await self._load_skill_from_directory(skill_dir)
                            reloaded_count += 1

                self._metrics.reload_count += 1
                self._metrics.last_reload_at = time.time()
                logger.info(f"Reloaded {reloaded_count} skills")
                return reloaded_count

            finally:
                self._status = previous_status

    async def _hot_reload_loop(self) -> None:
        """热重载循环（后台任务）"""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(self._config.hot_reload_interval_seconds)

                # 检查文件修改
                changed = False
                for file_path, last_mtime in list(self._file_watchers.items()):
                    try:
                        current_mtime = Path(file_path).stat().st_mtime
                        if current_mtime > last_mtime:
                            changed = True
                            break
                    except Exception:
                        pass

                if changed:
                    await self.reload_skills()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in hot reload loop: {e}")

    async def _health_check_loop(self) -> None:
        """健康检查循环（后台任务）"""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(self._config.health_check_interval_seconds)

                for skill_info in self._skills.values():
                    if not skill_info.instance:
                        continue

                    if skill_info.instance.status == SkillStatus.ERROR:
                        logger.warning(f"Skill {skill_info.name} is in error state, reinitializing")
                        try:
                            await skill_info.instance.shutdown()
                            success = await skill_info.instance.initialize()
                            if success:
                                logger.info(f"Skill {skill_info.name} reinitialized successfully")
                        except Exception as e:
                            logger.error(f"Failed to reinitialize skill {skill_info.name}: {e}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")

    def enable_skill(self, name: str) -> bool:
        """启用技能

        Args:
            name: 技能名称

        Returns:
            bool: 是否成功
        """
        skill_info = self._skills.get(name)
        if skill_info:
            skill_info.is_enabled = True
            return True
        return False

    def disable_skill(self, name: str) -> bool:
        """禁用技能

        Args:
            name: 技能名称

        Returns:
            bool: 是否成功
        """
        skill_info = self._skills.get(name)
        if skill_info:
            skill_info.is_enabled = False
            return True
        return False

    @property
    def status(self) -> RegistryStatus:
        """获取注册表状态"""
        return self._status

    @property
    def metrics(self) -> RegistryMetrics:
        """获取指标"""
        return self._metrics

    def get_metrics(self) -> Dict[str, Any]:
        """获取指标字典

        Returns:
            Dict[str, Any]: 指标字典
        """
        return {
            "status": self._status.value,
            "total_skills": len(self._skills),
            "enabled_skills": len([s for s in self._skills.values() if s.is_enabled]),
            "metrics": {
                "total_skills_registered": self._metrics.total_skills_registered,
                "total_skills_loaded": self._metrics.total_skills_loaded,
                "total_skills_failed": self._metrics.total_skills_failed,
                "total_executions": self._metrics.total_executions,
                "successful_executions": self._metrics.successful_executions,
                "failed_executions": self._metrics.failed_executions,
                "total_execution_time_ms": self._metrics.total_execution_time_ms,
                "reload_count": self._metrics.reload_count,
                "last_reload_at": self._metrics.last_reload_at,
                "error_count": len(self._metrics.errors),
            },
        }

    def _record_error(self, operation: str, error: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """记录错误

        Args:
            operation: 操作名称
            error: 错误信息
            extra: 额外信息
        """
        error_entry = {
            "operation": operation,
            "error": error,
            "timestamp": time.time(),
        }
        if extra:
            error_entry.update(extra)
        self._metrics.errors.append(error_entry)
        if len(self._metrics.errors) > 100:
            self._metrics.errors = self._metrics.errors[-100:]

    async def shutdown(self) -> None:
        """优雅关闭"""
        async with self._lock:
            self._status = RegistryStatus.SHUTTING_DOWN

            # 设置关闭事件
            self._shutdown_event.set()

            # 取消后台任务
            if self._hot_reload_task:
                self._hot_reload_task.cancel()
                try:
                    await self._hot_reload_task
                except asyncio.CancelledError:
                    pass

            if self._health_check_task:
                self._health_check_task.cancel()
                try:
                    await self._health_check_task
                except asyncio.CancelledError:
                    pass

            # 卸载所有技能
            for name in list(self._skills.keys()):
                await self._unload_skill(name)

            self._status = RegistryStatus.SHUTDOWN
            self._initialized = False
            logger.info("SkillRegistry shutdown complete")

    def __len__(self) -> int:
        return len(self._skills)

    def __contains__(self, name: str) -> bool:
        return name in self._skills

    def __str__(self) -> str:
        return f"SkillRegistry({len(self._skills)} skills, status={self._status.value})"
