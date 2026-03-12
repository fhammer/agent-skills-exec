"""
配置加载器 - 实现各种来源的配置加载

支持从文件、环境变量、命令行参数加载配置
"""

import os
import sys
import argparse
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
from abc import ABC, abstractmethod
import json
import yaml


class FileConfigLoader:
    """文件配置加载器"""

    def __init__(self, path: Optional[Path] = None):
        self.path = path

    def load(self):
        """加载配置"""
        if self.path is None:
            return {}

        if not self.path.exists():
            return {}

        with open(self.path, 'r', encoding='utf-8') as f:
            if self.path.suffix == '.json':
                return json.load(f)
            elif self.path.suffix in ['.yaml', '.yml']:
                return yaml.safe_load(f)
            else:
                raise ValueError(f"Unsupported file format: {self.path.suffix}")

    def exists(self):
        """检查配置是否存在"""
        return self.path is not None and self.path.exists()


class EnvConfigLoader:
    """环境变量配置加载器"""

    def __init__(self, prefix: str = "AGENT_"):
        self.prefix = prefix

    def load(self):
        """加载配置"""
        config = {}

        for key, value in os.environ.items():
            if key.startswith(self.prefix):
                clean_key = key[len(self.prefix):].lower()
                config[clean_key] = self._parse_value(value)

        return config

    def exists(self):
        """检查配置是否存在"""
        for key in os.environ:
            if key.startswith(self.prefix):
                return True
        return False

    def _parse_value(self, value: str):
        """解析值"""
        if value.lower() == 'true':
            return True
        if value.lower() == 'false':
            return False
        if value.isdigit():
            return int(value)
        if '.' in value and all(c.isdigit() or c == '.' for c in value):
            return float(value)
        try:
            return json.loads(value)
        except:
            return value


class CommandLineConfigLoader:
    """命令行参数配置加载器"""

    def __init__(self):
        self.parser = self._create_parser()

    def _create_parser(self):
        """创建参数解析器"""
        parser = argparse.ArgumentParser(description="智能体框架配置")
        parser.add_argument('--config', '-c', help='配置文件路径')
        parser.add_argument('--mode', help='运行模式 (development|testing|production)')
        parser.add_argument('--log-level', help='日志级别')
        parser.add_argument('--api-key', help='API密钥')
        parser.add_argument('--base-url', help='API基础URL')
        return parser

    def load(self):
        """加载配置"""
        args = self.parser.parse_args()
        config = {}

        if args.config:
            config['config_file'] = args.config

        if args.mode:
            config['mode'] = args.mode.lower()

        if args.log_level:
            config['log_level'] = args.log_level.lower()

        if args.api_key:
            config['api_key'] = args.api_key

        if args.base_url:
            config['base_url'] = args.base_url

        return config

    def exists(self):
        """检查配置是否存在"""
        return len(sys.argv) > 1


class DefaultConfigLoader:
    """默认配置加载器"""

    def __init__(self):
        self.default_config = {
            'mode': 'development',
            'log_level': 'INFO',
            'api_key': None,
            'base_url': None,
            'skills_dir': './skills',
            'models': {
                'default': 'gpt-3.5-turbo',
                'enabled': ['gpt-3.5-turbo', 'gpt-4']
            },
            'execution': {
                'enable_audit_log': True,
                'confidence_threshold': 0.7,
                'enable_replan': True
            },
            'budget': {
                'total_limit': 100000,
                'warning_threshold': 0.8,
                'enable_compression': True
            },
            'monitoring': {
                'enable': True,
                'interval': 60
            }
        }

    def load(self):
        """加载配置"""
        return self.default_config

    def exists(self):
        """检查配置是否存在"""
        return True


class MultiFileLoader:
    """多文件配置加载器"""

    def __init__(self, paths: list):
        self.paths = paths

    def load(self):
        """加载配置"""
        merged_config = {}

        for path in self.paths:
            path_obj = Path(path)
            if path_obj.exists():
                loader = FileConfigLoader(path_obj)
                config = loader.load()
                merged_config.update(config)

        return merged_config

    def exists(self):
        """检查配置是否存在"""
        for path in self.paths:
            if Path(path).exists():
                return True
        return False


class DirectoryLoader:
    """目录配置加载器"""

    def __init__(self, directory: str, extensions: list = ['.yaml', '.yml', '.json']):
        self.directory = directory
        self.extensions = extensions

    def load(self):
        """加载配置"""
        merged_config = {}

        if os.path.isdir(self.directory):
            for file_name in os.listdir(self.directory):
                if any(file_name.endswith(ext) for ext in self.extensions):
                    file_path = os.path.join(self.directory, file_name)
                    loader = FileConfigLoader(Path(file_path))
                    config = loader.load()

                    # 使用文件名作为配置键
                    key = os.path.splitext(file_name)[0]
                    merged_config[key] = config

        return merged_config

    def exists(self):
        """检查配置是否存在"""
        if os.path.isdir(self.directory):
            for file_name in os.listdir(self.directory):
                if any(file_name.endswith(ext) for ext in self.extensions):
                    return True
        return False
