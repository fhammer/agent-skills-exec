#!/usr/bin/env python3
"""
批量修复导入问题
"""

import re

# Fix 1: agent/core/interfaces.py - 添加 ExecutionStatus 和 SkillExecutionError
interfaces_file = "/home/fhammer/workspace/agent-skills-exec/agent/core/interfaces.py"
with open(interfaces_file, 'r') as f:
    content = f.read()

if 'class ExecutionStatus' not in content:
    # 在 __all__ 之前插入新类
    insert_marker = "__all__ = ["
    new_classes = '''

# ============================================================================
# Execution Status and Exceptions
# ============================================================================

class ExecutionStatus(Enum):
    """Execution status for skills."""
    PENDING = auto()
    RUNNING = auto()
    SUCCESS = auto()
    FAILED = auto()
    CANCELLED = auto()


class SkillExecutionError(CoreError):
    """Error during skill execution."""

    def __init__(self, skill_name: str, message: str, cause: Optional[Exception] = None):
        self.skill_name = skill_name
        self.cause = cause
        details = {"skill": skill_name}
        if cause:
            details["cause"] = str(cause)
        super().__init__(message, code="EXECUTION_ERROR", details=details)

'''
    content = content.replace(insert_marker, new_classes + insert_marker)
    with open(interfaces_file, 'w') as f:
        f.write(content)
    print("✅ Fixed interfaces.py - Added ExecutionStatus and SkillExecutionError")
else:
    print("ℹ️ interfaces.py already has ExecutionStatus")

# Fix 2: examples/smart_shopping_assistant/types.py - 添加 IntentClassification
types_file = "/home/fhammer/workspace/agent-skills-exec/examples/smart_shopping_assistant/types.py"
with open(types_file, 'r') as f:
    content = f.read()

if 'class IntentClassification' not in content:
    # 在第一个类定义之前插入
    new_class = '''@dataclass
class IntentClassification:
    """Intent classification result"""
    intent: str
    confidence: float
    entities: Dict[str, Any] = field(default_factory=dict)
    alternatives: List[Dict[str, Any]] = field(default_factory=list)


'''
    # 在 "class IntentType" 之前插入
    content = content.replace('class IntentType', new_class + 'class IntentType')
    with open(types_file, 'w') as f:
        f.write(content)
    print("✅ Fixed types.py - Added IntentClassification")
else:
    print("ℹ️ types.py already has IntentClassification")

# Fix 3: agent/core/__init__.py - 修复导出列表
init_file = "/home/fhammer/workspace/agent-skills-exec/agent/core/__init__.py"
with open(init_file, 'r') as f:
    content = f.read()

# 删除 SkillInput 和 SkillOutput 的导入（因为它们不存在）
content = re.sub(r'SkillInput,?\s*', '', content)
content = re.sub(r'SkillOutput,?\s*', '', content)

with open(init_file, 'w') as f:
    f.write(content)
print("✅ Fixed __init__.py - Removed non-existent SkillInput/SkillOutput")

print("\n🎉 All import fixes completed!")
print("\nYou can now run:")
print("  from examples.smart_shopping_assistant.assistant import ShoppingAssistant")
print("  from agent.core import BaseSkill, SkillRegistry, ContextManager")
