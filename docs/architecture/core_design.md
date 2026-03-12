# Core Architecture Design Document

## Overview

This document describes the core architecture of the Agent Skills Framework, focusing on the redesigned components that form the foundation of the system.

## Architecture Principles

1. **Single Responsibility**: Each class has a single, well-defined purpose
2. **Open/Closed**: Open for extension, closed for modification
3. **Liskov Substitution**: Subclasses can be substituted for their base classes
4. **Interface Segregation**: Small, focused interfaces
5. **Dependency Inversion**: Depend on abstractions, not concrete implementations

## Core Components

### 1. BaseSkill (Abstract Base Class)

**File**: `agent/core/base_skill.py`

**Purpose**: Define the standard interface that all skills must implement.

**Key Features**:
- Abstract properties for `name` and `version`
- Abstract methods for input validation, execution, output validation, and metadata
- Concrete method `execute_with_validation()` providing complete execution pipeline
- Statistics tracking (execution count, total execution time)
- Factory function `create_simple_skill()` for quick skill creation

**Usage Example**:
```python
class MySkill(BaseSkill):
    @property
    def name(self) -> str:
        return "my_skill"

    @property
    def version(self) -> str:
        return "1.0.0"

    def validate_input(self, input_data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        # Validate input
        return True, None

    async def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        # Execute skill logic
        return {"result": "success"}

    def validate_output(self, output_data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        # Validate output
        return True, None

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "description": "My custom skill",
            "tags": ["custom"],
            "triggers": ["my"]
        }
```

### 2. SkillRegistry (Singleton)

**File**: `agent/core/skill_registry.py`

**Purpose**: Central registry for managing skills with features like hot-reloading, health checks, and version management.

**Key Features**:
- Singleton pattern using `@singleton` decorator
- Skill discovery from directories
- Hot reload using watchdog (optional)
- Health checks with periodic status updates
- Version management using semantic versioning
- Execution metrics tracking
- Skill info metadata storage

**Architecture**:
```
┌─────────────────────────────────────┐
│          SkillRegistry              │
│           (Singleton)               │
├─────────────────────────────────────┤
│  - _skills: Dict[name, instance]    │
│  - _skill_info: Dict[name, SkillInfo]│
│  - _skills_dir: Path                │
│  - _observer: Optional[Observer]    │
│  - _health_check_task: Optional[Task]│
├─────────────────────────────────────┤
│  + initialize(skills_dir)            │
│  + register_skill(name, skill)     │
│  + unregister_skill(name)          │
│  + get_skill(name)                 │
│  + health_check()                  │
│  + record_execution(...)           │
└─────────────────────────────────────┘
```

**Usage Example**:
```python
from agent.core.skill_registry import get_skill_registry

# Get registry instance
registry = get_skill_registry()

# Initialize with skills directory
registry.initialize("./skills")

# Get a skill
skill = registry.get_skill("parse_report")

# Register a new skill
registry.register_skill("my_skill", skill_instance, skill_info)

# Get health status
health_results = registry.health_check()

# Get summary
summary = registry.get_summary()
```

### 3. ContextManager (Three-Layer Context)

**File**: `agent/core/context_manager.py`

**Purpose**: Manage the three-layer context system using the Template Method pattern.

**Architecture**:
```
┌─────────────────────────────────────────────────────────────┐
│                     ContextManager                           │
│                      (Facade)                                │
├─────────────────────────────────────────────────────────────┤
│  - _layer1: Layer1Context (User Input)                       │
│  - _layer2: Layer2Context (Scratchpad)                     │
│  - _layer3: Layer3Context (Environment)                    │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼──────┐    ┌────────▼───────┐    ┌──────▼────────┐
│ Layer1Context│    │ Layer2Context  │    │ Layer3Context │
│ (User Input) │    │ (Scratchpad)   │    │ (Environment)│
├──────────────┤    ├────────────────┤    ├───────────────┤
│ Template:    │    │ Template:      │    │ Template:     │
│ - raw_user_  │    │ - results      │    │ - skills_reg  │
│   input      │    │ - current_step │    │ - token_budget│
│ - parsed_    │    │ - failed_steps │    │ - model_config│
│   intent     │    │                │    │ - tools_reg   │
│ - execution_ │    │                │    │               │
│   plan       │    │                │    │               │
│ - conv_      │    │                │    │               │
│   history    │    │                │    │               │
└──────────────┘    └────────────────┘    └───────────────┘
```

**Key Features**:
- Template Method pattern in `BaseContext` for common data operations
- Layer-specific implementations for specialized behavior
- Permission control based on component type
- Comprehensive audit logging
- Cross-layer data flow support

**Template Method Pattern**:
```python
class BaseContext(ABC):
    # Template methods - define algorithm skeleton
    def get_data(self, key: str, default: Any = None) -> Any:
        self._check_permission("read", key)
        data = self._load_data(key)
        if data is None:
            data = self._default_value(key, default)
        data = self._validate_data(key, data)
        return data

    def set_data(self, key: str, value: Any) -> None:
        self._check_permission("write", key)
        validated = self._validate_data(key, value)
        validated = self._transform_data(key, validated)
        self._save_data(key, validated)
        self._notify_change(key, validated)

    # Abstract methods - must be implemented by subclasses
    @abstractmethod
    def _load_data(self, key: str) -> Any: ...

    @abstractmethod
    def _save_data(self, key: str, value: Any) -> None: ...

    # Hook methods - can be overridden by subclasses
    def _validate_data(self, key: str, data: Any) -> Any:
        return data

    def _default_value(self, key: str, default: Any) -> Any:
        return default

    def _transform_data(self, key: str, data: Any) -> Any:
        return data

    def _notify_change(self, key: str, value: Any) -> None:
        pass
```

**Usage Example**:
```python
from agent.core.context_manager import ContextManager, ComponentType

# Create context manager
context = ContextManager()

# Set component type for permission control
context.set_component(ComponentType.COORDINATOR)

# Layer 1: User Input
context.layer1.set_data("raw_user_input", "Parse this report")
context.layer1.set_data("conversation_history", [])

# Layer 2: Working Memory
context.layer2.set_result("parse_report", {"parsed": True, "data": {...}})

# Layer 3: Environment
context.layer3.set_model_config({"model": "gpt-4", "temperature": 0.7})
context.layer3.set_skills_registry(skills_registry)

# Prepare context for skill execution
step = {"sub_task": "Analyze report"}
execution_context = context.prepare_for_step(step)

# Get audit trail
audit_entries = context.layer1.get_audit_log()
```

## Design Patterns Used

### 1. Template Method Pattern
Used in `BaseContext` to define the algorithm skeleton for data operations while allowing subclasses to customize specific steps.

### 2. Singleton Pattern
Used in `SkillRegistry` to ensure only one registry instance exists globally.

### 3. Facade Pattern
Used in `ContextManager` to provide a simplified interface to the complex three-layer context subsystem.

### 4. Observer Pattern (Implicit)
The hot reload mechanism in `SkillRegistry` uses file system event observation to trigger skill reloads.

## Testing Strategy

Each core component has comprehensive unit tests:

- **BaseSkill**: Tests for properties, validation, execution, and error handling
- **SkillRegistry**: Tests for singleton behavior, skill management, health checks, and metrics
- **ContextManager**: Tests for layer operations, permission control, and audit logging

Test coverage target: >80%

## Future Enhancements

1. **Distributed Context**: Support for distributed context across multiple nodes
2. **Persistent Context**: Option to persist context to database/storage
3. **Context Versioning**: Track context changes over time
4. **Advanced Permissions**: Role-based access control for context operations
5. **Metrics Export**: Export context metrics to monitoring systems (Prometheus, etc.)
