"""
配置验证器 - 提供配置验证功能
"""

import re
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field


@dataclass
class ValidationError:
    """验证错误"""
    path: str
    message: str
    severity: str = "error"


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)


class ConfigValidator:
    """配置验证器"""

    def __init__(self, schema: Dict[str, Any]):
        self.schema = schema
        self._validators = self._build_validators()

    def _build_validators(self):
        """构建验证器"""
        return {
            'type': self._validate_type,
            'required': self._validate_required,
            'min_length': self._validate_min_length,
            'max_length': self._validate_max_length,
            'pattern': self._validate_pattern,
            'minimum': self._validate_minimum,
            'maximum': self._validate_maximum,
            'enum': self._validate_enum,
            'custom': self._validate_custom,
        }

    def validate(self, config: Dict[str, Any]) -> ValidationResult:
        """验证配置"""
        errors = []
        warnings = []

        self._validate_recursive('', config, self.schema, errors, warnings)

        is_valid = len(errors) == 0
        return ValidationResult(is_valid, errors, warnings)

    def _validate_recursive(
        self,
        path: str,
        value: Any,
        schema: Any,
        errors: List[ValidationError],
        warnings: List[ValidationError]
    ):
        """递归验证"""
        if isinstance(schema, dict):
            if 'properties' in schema:
                for key, prop_schema in schema['properties'].items():
                    full_path = f"{path}.{key}" if path else key

                    if key in value:
                        self._validate_recursive(
                            full_path,
                            value[key],
                            prop_schema,
                            errors,
                            warnings
                        )
                    elif prop_schema.get('required', False):
                        errors.append(ValidationError(
                            path=full_path,
                            message="Required property is missing"
                        ))

            else:
                for validator_name, validator_func in self._validators.items():
                    if validator_name in schema:
                        result = validator_func(value, schema[validator_name])
                        if result is not None:
                            if result.get('severity') == 'warning':
                                warnings.append(ValidationError(
                                    path=path,
                                    message=result['message'],
                                    severity='warning'
                                ))
                            else:
                                errors.append(ValidationError(
                                    path=path,
                                    message=result['message']
                                ))

    def _validate_type(self, value: Any, expected_type: Any) -> Optional[Dict[str, Any]]:
        """验证类型"""
        if not isinstance(value, expected_type):
            return {
                'message': f"Expected type {expected_type.__name__}, got {type(value).__name__}"
            }
        return None

    def _validate_required(self, value: Any, required: bool) -> Optional[Dict[str, Any]]:
        """验证必需性"""
        if required and value is None:
            return {
                'message': "Value is required and cannot be None"
            }
        return None

    def _validate_min_length(self, value: Any, min_length: int) -> Optional[Dict[str, Any]]:
        """验证最小长度"""
        if isinstance(value, (str, list, tuple)):
            if len(value) < min_length:
                return {
                    'message': f"Value must be at least {min_length} characters/elements"
                }
        return None

    def _validate_max_length(self, value: Any, max_length: int) -> Optional[Dict[str, Any]]:
        """验证最大长度"""
        if isinstance(value, (str, list, tuple)):
            if len(value) > max_length:
                return {
                    'message': f"Value must be at most {max_length} characters/elements"
                }
        return None

    def _validate_pattern(self, value: Any, pattern: str) -> Optional[Dict[str, Any]]:
        """验证模式"""
        if isinstance(value, str):
            if not re.match(pattern, value):
                return {
                    'message': f"Value does not match pattern {pattern}"
                }
        return None

    def _validate_minimum(self, value: Any, minimum: float) -> Optional[Dict[str, Any]]:
        """验证最小值"""
        if isinstance(value, (int, float)):
            if value < minimum:
                return {
                    'message': f"Value must be at least {minimum}"
                }
        return None

    def _validate_maximum(self, value: Any, maximum: float) -> Optional[Dict[str, Any]]:
        """验证最大值"""
        if isinstance(value, (int, float)):
            if value > maximum:
                return {
                    'message': f"Value must be at most {maximum}"
                }
        return None

    def _validate_enum(self, value: Any, enum: List[Any]) -> Optional[Dict[str, Any]]:
        """验证枚举"""
        if value not in enum:
            return {
                'message': f"Value must be one of {enum}"
            }
        return None

    def _validate_custom(self, value: Any, validator: Callable) -> Optional[Dict[str, Any]]:
        """验证自定义验证器"""
        result = validator(value)
        if not result[0]:
            return {
                'message': result[1]
            }
        return None
