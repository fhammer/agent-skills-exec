"""
配置模板 - 提供配置模板和预设
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class ConfigSection:
    """配置段"""
    name: str
    description: str = ""
    default_value: Any = None
    type: type = str
    required: bool = False
    enum: List[Any] = field(default_factory=list)
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None
    example: Any = None


@dataclass
class ConfigTemplate:
    """配置模板"""
    name: str
    version: str = "1.0.0"
    description: str = ""
    sections: Dict[str, ConfigSection] = field(default_factory=dict)

    def get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        config = {}

        for section_name, section in self.sections.items():
            if '.' in section_name:
                keys = section_name.split('.')
                current = config
                for i, key in enumerate(keys):
                    if i == len(keys) - 1:
                        current[key] = section.default_value
                    else:
                        if key not in current:
                            current[key] = {}
                        current = current[key]
            else:
                config[section_name] = section.default_value

        return config

    def generate_config_file(self, format: str = "yaml") -> str:
        """生成配置文件"""
        config = self.get_default_config()

        if format.lower() in ["yaml", "yml"]:
            import yaml
            return yaml.dump(config, default_flow_style=False, allow_unicode=True)
        elif format.lower() == "json":
            import json
            return json.dumps(config, indent=2, ensure_ascii=False)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def validate_config(self, config: Dict[str, Any]) -> tuple:
        """验证配置"""
        errors = []
        warnings = []

        for section_name, section in self.sections.items():
            # 获取值
            value = self._get_nested_value(config, section_name)

            # 检查必需性
            if section.required and value is None:
                errors.append(f"Missing required config: {section_name}")
                continue

            if value is None:
                continue

            # 检查类型
            if not isinstance(value, section.type):
                try:
                    value = section.type(value)
                except (TypeError, ValueError):
                    errors.append(f"Invalid type for {section_name}: expected {section.type.__name__}")
                    continue

            # 检查枚举
            if section.enum and value not in section.enum:
                errors.append(f"Invalid value for {section_name}: must be one of {section.enum}")

            # 检查范围
            if isinstance(value, (int, float)):
                if section.min_value is not None and value < section.min_value:
                    errors.append(f"Value for {section_name} must be >= {section.min_value}")
                if section.max_value is not None and value > section.max_value:
                    errors.append(f"Value for {section_name} must be <= {section.max_value}")

            # 检查长度
            if isinstance(value, (str, list, tuple)):
                if section.min_length is not None and len(value) < section.min_length:
                    errors.append(f"Length for {section_name} must be >= {section.min_length}")
                if section.max_length is not None and len(value) > section.max_length:
                    errors.append(f"Length for {section_name} must be <= {section.max_length}")

        return len(errors) == 0, errors, warnings

    @staticmethod
    def _get_nested_value(config: Dict[str, Any], path: str):
        """获取嵌套值"""
        keys = path.split('.')
        current = config

        for key in keys:
            if key not in current:
                return None
            current = current[key]

        return current


# 预设配置模板

def create_development_template() -> ConfigTemplate:
    """创建开发环境配置模板"""
    template = ConfigTemplate(
        name="development",
        version="1.0.0",
        description="开发环境配置模板"
    )

    template.sections = {
        "mode": ConfigSection(
            name="mode",
            description="运行模式",
            default_value="development",
            enum=["development", "testing", "staging", "production"]
        ),
        "log_level": ConfigSection(
            name="log_level",
            description="日志级别",
            default_value="DEBUG",
            enum=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        ),
        "api_key": ConfigSection(
            name="api_key",
            description="API密钥",
            default_value=""
        ),
        "base_url": ConfigSection(
            name="base_url",
            description="API基础URL",
            default_value="https://api.example.com"
        ),
        "skills_dir": ConfigSection(
            name="skills_dir",
            description="技能目录",
            default_value="./skills"
        ),
        "execution.enable_audit_log": ConfigSection(
            name="execution.enable_audit_log",
            description="启用审计日志",
            default_value=True,
            type=bool
        ),
        "execution.confidence_threshold": ConfigSection(
            name="execution.confidence_threshold",
            description="置信度阈值",
            default_value=0.7,
            type=float,
            min_value=0.0,
            max_value=1.0
        ),
        "budget.total_limit": ConfigSection(
            name="budget.total_limit",
            description="总token限制",
            default_value=100000,
            type=int,
            min_value=1000
        ),
        "budget.warning_threshold": ConfigSection(
            name="budget.warning_threshold",
            description="警告阈值",
            default_value=0.8,
            type=float,
            min_value=0.0,
            max_value=1.0
        )
    }

    return template


def create_production_template() -> ConfigTemplate:
    """创建生产环境配置模板"""
    template = create_development_template()
    template.name = "production"
    template.description = "生产环境配置模板"

    # 修改生产环境特定值
    template.sections["mode"].default_value = "production"
    template.sections["log_level"].default_value = "INFO"
    template.sections["budget.total_limit"].default_value = 1000000

    return template


def create_testing_template() -> ConfigTemplate:
    """创建测试环境配置模板"""
    template = create_development_template()
    template.name = "testing"
    template.description = "测试环境配置模板"

    # 修改测试环境特定值
    template.sections["mode"].default_value = "testing"
    template.sections["log_level"].default_value = "WARNING"
    template.sections["budget.total_limit"].default_value = 10000

    return template


# 可用的预设模板
PRESET_TEMPLATES = {
    "development": create_development_template,
    "testing": create_testing_template,
    "production": create_production_template,
}


def get_template(template_name: str) -> Optional[ConfigTemplate]:
    """获取预设模板"""
    if template_name in PRESET_TEMPLATES:
        return PRESET_TEMPLATES[template_name]()
    return None
