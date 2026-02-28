#!/bin/bash
# Skill template creator script

set -e

if [ -z "$1" ]; then
    echo "用法: ./create_skill.sh <skill_name>"
    echo "示例: ./create_skill.sh my_awesome_skill"
    exit 1
fi

SKILL_NAME=$1
SKILL_DIR="skills/$SKILL_NAME"

# Check if skill already exists
if [ -d "$SKILL_DIR" ]; then
    echo "错误: Skill '$SKILL_NAME' 已存在于 $SKILL_DIR"
    exit 1
fi

# Create skill directory
echo "创建 Skill: $SKILL_NAME"
mkdir -p "$SKILL_DIR"

# Create SKILL.md
cat > "$SKILL_DIR/SKILL.md" << EOF
---
name: $SKILL_NAME
version: 1.0.0
description: 请填写 Skill 描述
triggers:
  - 触发词1
  - 触发词2
tags:
  - 标签1
  - 标签2
---

# $SKILL_NAME Skill

## 功能

请描述 Skill 的功能...

## 输入格式

请描述输入格式...

## 输出格式

请描述输出格式...

## 执行模式

- executor.py - 自定义执行器
- prompt.template - Prompt 模板
- SKILL.md - 文档模式
EOF

# Create executor.py
cat > "$SKILL_DIR/executor.py" << EOF
"""$SKILL_NAME Skill executor."""

from typing import Dict, Any
from agent.llm_client import LLMClient


def execute(llm: LLMClient, sub_task: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Execute $SKILL_NAME skill.

    Args:
        llm: LLM client
        sub_task: Specific sub-task description
        context: Execution context

    Returns:
        Result with structured data and text
    """
    # ─── Rule Engine: Deterministic computation ───
    # Add your rule-based logic here
    result = process_with_rules(context)

    # ─── LLM: Natural language generation ───
    prompt = f"Please explain: {result}"
    text = llm.invoke(prompt)

    return {
        "structured": {"result": result},
        "text": text,
        "metadata": {"execution_mode": "hybrid"}
    }


def process_with_rules(context: Dict[str, Any]) -> Any:
    """Process with rule-based logic."""
    # Add your rule-based processing here
    return "processed result"
EOF

# Create schema.py
cat > "$SKILL_DIR/schema.py" << EOF
"""Schema definitions for $SKILL_NAME skill."""

from typing import TypedDict, Dict, Any


class ${SKELL_NAME^}Output(TypedDict):
    """Output from $SKILL_NAME skill."""
    result: Dict[str, Any]
    text: str
    metadata: Dict[str, Any]
EOF

# Create prompt.template
cat > "$SKILL_DIR/prompt.template" << EOF
You are a specialized assistant for: {sub_task}

User input: {user_input}

Previous results:
{previous_results}

Please provide a helpful response.
EOF

echo ""
echo "✓ Skill 模板已创建: $SKILL_DIR/"
echo ""
echo "文件结构:"
echo "  ├── SKILL.md"
echo "  ├── executor.py"
echo "  ├── schema.py"
echo "  └── prompt.template"
echo ""
echo "下一步: 编辑 SKILL.md 和 executor.py 来实现你的 Skill"
