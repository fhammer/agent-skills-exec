"""
配置管理器 - 核心实现

提供统一的配置管理、验证和合并功能
"""

import os
import sys
from typing import Any, Dict, List, Optional, Union, Type
from pathlib import Path
from enum import Enum
from dataclasses import dataclass
from abc import ABC, abstractmethod
import json
import yaml


class ConfigSource(Enum):
    """配置来源"""
    FILE = "file"
    ENV = "environment"
    COMMAND_LINE = "command_line"
    DEFAULT = "default"


class ConfigMode(Enum):
    """配置模式"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"
    STAGING = "staging"


@dataclass
class LoadedConfig:
    """加载的配置"""
    data: Dict[str, Any]
    source: ConfigSource
    priority: int = 0


class ConfigLoader(ABC):
    """配置加载器抽象基类"""

    @abstractmethod
    def load(self, path: Optional[Union[str, Path]] = None) -> LoadedConfig:
        """加载配置"""
        pass

    @abstractmethod
    def exists(self, path: Optional[Union[str, Path]] = None) -> bool:
        """检查配置是否存在"""
        pass


class ConfigManager:
    """统一配置管理器"""

    def __init__(self, mode: ConfigMode = ConfigMode.DEVELOPMENT):
        self.mode = mode
        self._loaded_configs: List[LoadedConfig] = []
        self._merged_config: Optional[Dict[str, Any]] = None

    def add_loader(self, loader: ConfigLoader, source: ConfigSource, priority: int = 0):
        """添加配置加载器"""
        config = loader.load()
        self._loaded_configs.append(LoadedConfig(
            data=config.data,
            source=source,
            priority=priority
        ))
        self._merged_config = None

    def merge_configs(self) -> Dict[str, Any]:
        """合并配置"""
        if self._merged_config is not None:
            return self._merged_config

        # 按优先级排序，高优先级先处理
        sorted_configs = sorted(
            self._loaded_configs,
            key=lambda x: x.priority,
            reverse=True
        )

        # 合并配置
        merged = {}
        for config in sorted_configs:
            merged = self._deep_merge(merged, config.data)

        self._merged_config = merged
        return merged

    def get_config(self, path: str = None, default: Any = None) -> Any:
        """获取配置值"""
        if self._merged_config is None:
            self.merge_configs()

        if path is None:
            return self._merged_config

        return self._get_nested_value(self._merged_config, path, default)

    def set_config(self, path: str, value: Any):
        """设置配置值"""
        if self._merged_config is None:
            self.merge_configs()

        self._set_nested_value(self._merged_config, path, value)

    def validate_config(self, schema: Dict[str, Any]) -> bool:
        """验证配置"""
        if self._merged_config is None:
            self.merge_configs()

        return self._validate_recursive(self._merged_config, schema)

    def get_sources_info(self) -> List[Dict[str, Any]]:
        """获取配置源信息"""
        return [
            {
                "source": config.source.value,
                "priority": config.priority,
                "keys": list(config.data.keys()),
                "size": len(json.dumps(config.data)),
            }
            for config in self._loaded_configs
        ]

    @staticmethod
    def _deep_merge(base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
        """深度合并两个字典"""
        result = base.copy()

        for key, value in update.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = ConfigManager._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    @staticmethod
    def _get_nested_value(data: Dict[str, Any], path: str, default: Any) -> Any:
        """获取嵌套值"""
        keys = path.split('.')
        current = data

        for key in keys:
            if key not in current:
                return default
            current = current[key]

        return current

    @staticmethod
    def _set_nested_value(data: Dict[str, Any], path: str, value: Any):
        """设置嵌套值"""
        keys = path.split('.')
        current = data

        for i, key in enumerate(keys):
            if i == len(keys) - 1:
                current[key] = value
            else:
                if key not in current or not isinstance(current[key], dict):
                    current[key] = {}
                current = current[key]

    @staticmethod
    def _validate_recursive(data: Any, schema: Any) -> bool:
        """递归验证配置"""
        if isinstance(schema, dict) and isinstance(data, dict):
            for key, expected_type in schema.items():
                if key not in data:
                    return False

                if isinstance(expected_type, dict):
                    if not ConfigManager._validate_recursive(data[key], expected_type):
                        return False
                elif isinstance(expected_type, list):
                    if not isinstance(data[key], list):
                        return False
                    if expected_type and len(expected_type) > 0:
                        for item in data[key]:
                            if not ConfigManager._validate_recursive(item, expected_type[0]):
                                return False
                elif not isinstance(data[key], expected_type):
                    return False
            return True

        return isinstance(data, schema) if isinstance(schema, type) else True

    @staticmethod
    def from_file(file_path: Union[str, Path]) -> 'ConfigManager':
        """从文件创建配置管理器"""
        manager = ConfigManager()
        from .config_loader import FileConfigLoader
        manager.add_loader(FileConfigLoader(file_path), ConfigSource.FILE, 10)
        return manager

    @staticmethod
    def from_env(prefix: str = "AGENT_") -> 'ConfigManager':
        """从环境变量创建配置管理器"""
        manager = ConfigManager()
        from .config_loader import EnvConfigLoader
        manager.add_loader(EnvConfigLoader(prefix), ConfigSource.ENV, 20)
        return manager

    @staticmethod
    def from_command_line() -> 'ConfigManager':
        """从命令行参数创建配置管理器"""
        manager = ConfigManager()
        from .config_loader import CommandLineConfigLoader
        manager.add_loader(CommandLineConfigLoader(), ConfigSource.COMMAND_LINE, 30)
        return manager
