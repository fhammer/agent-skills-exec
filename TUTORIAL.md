# Agent Skills Framework 使用教程

## 目录

1. [快速开始](#快速开始)
2. [配置说明](#配置说明)
3. [运行测试](#运行测试)
4. [创建自定义 Skill](#创建自定义-skill)
5. [API 参考](#api-参考)
6. [常见问题](#常见问题)

---

## 快速开始

### 1. 环境准备

```bash
# 进入项目目录
cd agent-skills-exec

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置 LLM Provider

框架支持三种配置方式，优先级从高到低：

1. **config.local.yaml** - 本地配置文件（最高优先级，不提交到版本控制）
2. **config.yaml** - 项目默认配置文件
3. **环境变量** - 覆盖文件配置

#### 方式一：配置文件（推荐）

创建 `config.local.yaml` 文件：

```yaml
# LLM 配置
llm:
  provider: anthropic
  model: glm-4.7
  api_key: 你的智谱API密钥
  base_url: https://open.bigmodel.cn/api/anthropic
  temperature: 0.7
  max_tokens: 2000

# Token 预算配置
budget:
  total_limit: 100000
  warning_threshold: 0.8
  enable_compression: true

# 执行配置
execution:
  max_skill_retries: 2
  enable_streaming: true
  enable_audit_log: true
  enable_replan: true
  confidence_threshold: 0.5
```

然后使用配置文件：

```python
from config import Config

# 从配置文件加载
config = Config.from_file()

# 或从预设 profile 加载
config = Config.from_profile("zhipu_glm47")

coordinator = Coordinator(config)
```

#### 方式二：环境变量

```bash
# OpenAI
export LLM_PROVIDER=openai
export LLM_API_KEY=sk-xxx
export LLM_MODEL=gpt-4

# Anthropic (Claude)
export LLM_PROVIDER=anthropic
export LLM_API_KEY=sk-ant-xxx
export LLM_MODEL=claude-3-opus-20240229

# Ollama (本地)
export LLM_PROVIDER=ollama
export LLM_MODEL=llama3

# 智谱 GLM (使用 Anthropic 兼容端点)
export LLM_PROVIDER=anthropic
export LLM_API_KEY=你的智谱API密钥
export LLM_MODEL=glm-4.7
export LLM_BASE_URL=https://open.bigmodel.cn/api/anthropic
```

#### 方式三：.env 文件

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的配置
```

### 3. 使用配置 Profiles

框架提供了预设配置文件，方便快速切换：

```python
from config import Config

# 智谱 GLM-4.7
config = Config.from_profile("zhipu_glm47")

# 智谱 GLM-4-Flash (快速版)
config = Config.from_profile("zhipu_flash")

# OpenAI GPT-4
config = Config.from_profile("openai_gpt4")

# Anthropic Claude
config = Config.from_profile("anthropic_claude")

# Ollama 本地模型
config = Config.from_profile("ollama_local")
```

### 3. 运行框架

```bash
# 运行主程序（交互模式）
python main.py

# 或运行测试脚本
python test_framework.py
```

---

## 配置说明

### 智谱 GLM 配置 (推荐)

智谱 AI 提供了兼容 Anthropic API 的端点，可以直接使用：

| 配置项 | 值 |
|--------|-----|
| `LLM_PROVIDER` | `anthropic` |
| `LLM_BASE_URL` | `https://open.bigmodel.cn/api/anthropic` |
| `LLM_MODEL` | `glm-4.7` 或 `glm-4-flash` |
| `LLM_API_KEY` | 你的智谱 API Key |

### 完整配置选项

```python
from config import Config

config = Config()

# LLM 配置
config.llm.provider = "openai"      # openai | anthropic | ollama
config.llm.model = "gpt-4"
config.llm.api_key = "sk-xxx"
config.llm.base_url = None           # 可选：自定义 API 端点
config.llm.temperature = 0.7
config.llm.max_tokens = 2000

# Token 预算配置
config.budget.total_limit = 100000
config.budget.warning_threshold = 0.8
config.budget.enable_compression = True

# 执行配置
config.execution.max_skill_retries = 2
config.execution.enable_streaming = True
config.execution.enable_audit_log = True
config.execution.enable_replan = True
config.execution.confidence_threshold = 0.5
```

---

## 运行测试

### 单元测试（无需 API）

```bash
python test_framework.py
```

### LLM 集成测试

```bash
# 智谱 GLM-4.7 测试
python test_glm47_simple.py

# 显示测试总结
python test_summary.py
```

### 查看可用模型

```bash
python test_glm_models.py
```

---

## 创建自定义 Skill

### Skill 目录结构

```
skills/my_skill/
├── SKILL.md          # 必需：元数据和文档
├── executor.py       # 可选：自定义执行器（优先级最高）
├── prompt.template   # 可选：Prompt 模板
└── schema.py         # 可选：输出数据契约
```

### 执行优先级

1. **executor.py** - 自定义 Python 代码（规则引擎 + LLM）
2. **prompt.template** - Prompt 模板（纯 LLM）
3. **SKILL.md** - 文档即 Skill（纯 LLM，用文档作为系统提示）

### 示例：创建一个计算器 Skill

#### 步骤 1：创建目录

```bash
mkdir -p skills/calculator
```

#### 步骤 2：创建 SKILL.md

```markdown
---
name: calculator
version: 1.0.0
description: 数学计算器，支持基础运算和复杂表达式
triggers:
  - 计算
  - 算一下
  - 求值
tags:
  - math
  - calculator
---

# 计算器 Skill

执行各种数学计算，包括：
- 基础运算：加减乘除
- 复杂表达式：支持括号、函数
- 单位转换：长度、重量、温度等
```

#### 步骤 3：创建 executor.py

```python
"""Calculator Skill executor."""

from agent.llm_client import LLMClient
from typing import Dict, Any
import re

def execute(llm: LLMClient, sub_task: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """执行计算任务。

    Args:
        llm: LLM 客户端
        sub_task: 子任务描述
        context: 执行上下文

    Returns:
        计算结果
    """
    # 提取数学表达式
    expression = extract_expression(sub_task)

    try:
        # 规则引擎：确定性计算
        result = eval_expression(expression)

        # LLM：生成解释
        explanation = llm.invoke(
            f"请解释这个计算：{expression} = {result}。"
            f"任务描述：{sub_task}"
        )

        return {
            "structured": {
                "expression": expression,
                "result": result,
                "type": "calculation"
            },
            "text": f"计算结果：{result}\n\n{explanation}"
        }
    except Exception as e:
        return {
            "structured": {"error": str(e)},
            "text": f"计算失败：{str(e)}"
        }

def extract_expression(text: str) -> str:
    """从文本中提取数学表达式。"""
    # 简单实现：提取数字和运算符
    pattern = r'[\d+\-*/(). ]+'
    matches = re.findall(pattern, text)
    return matches[0] if matches else text

def eval_expression(expr: str) -> float:
    """安全地计算表达式。"""
    # 只允许安全的字符
    allowed = set('0123456789+-*/(). ')
    if not all(c in allowed for c in expr):
        raise ValueError("表达式包含非法字符")
    return eval(expr)
```

#### 步骤 4：测试 Skill

```python
from config import Config
from agent.coordinator import Coordinator

config = Config.from_env()
coordinator = Coordinator(config)

# 发送计算请求
result = coordinator.process("请帮我计算：123 * 456 + 789")
print(result["final_response"])
```

---

## API 参考

### Coordinator

主协调器，统一管理整个执行流程。

```python
from config import Config
from agent.coordinator import Coordinator

config = Config.from_env()
coordinator = Coordinator(config)

# 处理用户请求
result = coordinator.process(
    user_input="请帮我分析体检报告",
    stream=False  # 是否流式输出
)

# 结果结构
{
    "final_response": "最终回复文本",
    "success": True,
    "metrics": {
        "execution_time_ms": 1234,
        "total_skills_executed": 3,
        "llm_metrics": {...},
        "token_budget": {...}
    },
    "plan": {...},
    "execution_summary": {...}
}

# 查看审计日志
audit_trail = coordinator.get_audit_trail()

# 解释某个决策
explanation = coordinator.explain("为什么选择了 parse_report skill")

# 重置状态
coordinator.reset()
```

### 直接使用组件

```python
from config import Config
from agent.coordinator import Coordinator
from agent.llm_client import LLMClient
from agent.providers.anthropic_provider import AnthropicProvider
from agent.token_budget import TokenBudget

# 创建 LLM 客户端
provider = AnthropicProvider(
    api_key="your-api-key",
    base_url="https://open.bigmodel.cn/api/anthropic",
    default_model="glm-4.7"
)
budget = TokenBudget(total_limit=100000)
llm = LLMClient(provider, budget)

# 调用 LLM
response = llm.invoke("你好，请介绍一下你自己")

# 查看指标
metrics = llm.get_metrics()
print(f"总调用次数: {metrics['total_calls']}")
print(f"总 Token 使用: {metrics['total_tokens']}")
```

---

## 常见问题

### Q1: 如何使用智谱 GLM 模型？

**A:** 使用智谱的 Anthropic 兼容端点：

```bash
export LLM_PROVIDER=anthropic
export LLM_BASE_URL=https://open.bigmodel.cn/api/anthropic
export LLM_MODEL=glm-4.7
export LLM_API_KEY=你的智谱API密钥
```

### Q2: Token 预算如何管理？

**A:** 框架会自动跟踪 Token 使用，并在接近预算时启用压缩：

```python
# 查看预算状态
budget_summary = llm.budget.get_summary()
print(f"使用率: {budget_summary['usage_ratio']:.1%}")

# 获取压缩建议
if budget_summary['usage_ratio'] > 0.8:
    compression = llm.budget.get_compression_strategy()
    print(f"建议压缩: {compression}")
```

### Q3: 如何调试 Skill 执行？

**A:** 启用审计日志，查看完整执行链：

```python
from config import Config
from agent.coordinator import Coordinator

config = Config()
config.execution.enable_audit_log = True

coordinator = Coordinator(config)
result = coordinator.process("你的请求")

# 查看审计日志
for entry in coordinator.get_audit_trail():
    print(f"{entry['timestamp']} - {entry['component']}: {entry['operation']}")
```

### Q4: Skills 之间如何传递数据？

**A:** 通过 Scratchpad (工作记忆层)，前一个 Skill 的输出自动传递给下一个：

```python
# Skill 1 输出
return {
    "structured": {"bmi": 25.5, "category": "overweight"},
    "text": "BMI 为 25.5，属于超重范围。"
}

# Skill 2 可以访问
previous_results = context.get("previous_results", {})
bmi_data = previous_results.get("parse_report", {}).get("structured", {})
```

### Q5: 如何添加新的 LLM Provider？

**A:** 继承 `LLMProvider` 基类：

```python
from agent.llm_base import LLMProvider

class MyProvider(LLMProvider):
    def __init__(self, api_key: str, **kwargs):
        # 初始化你的客户端
        pass

    def invoke(self, messages, model=None, **kwargs):
        # 实现 LLM 调用
        pass

    def stream(self, messages, model=None, **kwargs):
        # 实现流式输出
        pass

    def count_tokens(self, text: str) -> int:
        # 实现 Token 计数
        pass
```

然后在 `coordinator.py` 中添加：

```python
elif provider_name == "my_provider":
    from agent.providers.my_provider import MyProvider
    return MyProvider(...)
```

---

## 项目文件说明

| 文件/目录 | 说明 |
|-----------|------|
| `main.py` | 主入口，交互模式 |
| `config.py` | 全局配置 |
| `agent/coordinator.py` | 协调器 |
| `agent/planner.py` | 任务规划 |
| `agent/skill_executor.py` | Skill 执行器 |
| `agent/synthesizer.py` | 结果综合 |
| `agent/context.py` | 三层上下文 |
| `agent/llm_client.py` | LLM 客户端 |
| `agent/token_budget.py` | Token 预算 |
| `skills/` | Skills 目录 |
| `test_*.py` | 各种测试脚本 |

---

## 更多信息

- 设计文档：`docs/plans/2025-02-28-agent-skills-framework-design.md`
- 示例 Skills：`skills/` 目录
- 原文章：[别急着上 Multi-Agent，也许「Agent Skills」会更好](https://mp.weixin.qq.com/s/_uoHjcMbVlx9PrUXRF6Efg)
