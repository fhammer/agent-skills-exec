# Agent Skills Framework - 快速启动与扩展指南

## 目录

1. [环境准备](#环境准备)
2. [快速启动](#快速启动)
3. [基础使用](#基础使用)
4. [扩展能力](#扩展能力)
5. [进阶开发](#进阶开发)
6. [常见问题](#常见问题)

---

## 环境准备

### 1. 系统要求

- Python 3.8+
- pip 包管理器

### 2. 安装依赖

```bash
cd agent-skills-exec
pip install -r requirements.txt
```

### 3. 配置 LLM Provider

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

---

## 快速启动

### 方式一：运行主程序（交互模式）

```bash
python main.py
```

进入交互式对话界面，输入你的请求即可。

### 方式二：使用 Python 代码

```python
from config import Config
from agent.coordinator import Coordinator

# 加载配置
config = Config.from_file()

# 创建协调器
coordinator = Coordinator(config)

# 处理请求
result = coordinator.process("请帮我分析体检报告")

# 获取结果
print(result["final_response"])

# 查看执行详情
if result["success"]:
    print(f"执行时间: {result['metrics']['execution_time_ms']}ms")
    print(f"执行技能数: {result['metrics']['total_skills_executed']}")
```

### 方式三：运行测试脚本

```bash
# 测试配置加载
python test_config.py

# 测试框架功能
python test_with_config.py

# 测试 GLM-4.7 连接
python test_glm47_simple.py
```

---

## 基础使用

### 1. 理解框架架构

```
┌─────────────────────────────────────────────────────────┐
│                     Coordinator                         │
│              (统一调度整个执行流程)                        │
└─────────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│   Planner   │   │  Executor   │   │ Synthesizer │
│  (任务规划)  │   │  (技能执行)  │   │  (结果综合)  │
└─────────────┘   └─────────────┘   └─────────────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                    ┌──────▼──────┐
                    │ AgentContext │
                    │ (三层上下文)  │
                    └─────────────┘
```

### 2. 三层上下文系统

| 层级 | 内容 | 用途 |
|------|------|------|
| Layer 1 | 用户输入、意图、计划 | 存储原始请求和执行计划 |
| Layer 2 | 工作记忆、Skill 结果 | 存储 Skill 执行的中间结果 |
| Layer 3 | 环境、Skills、预算 | 存储全局配置和状态 |

### 3. 使用预设 Profiles

```python
from config import Config

# 智谱 GLM-4.7（推荐）
config = Config.from_profile("zhipu_glm47")

# 智谱 GLM-4-Flash（快速版）
config = Config.from_profile("zhipu_flash")

# OpenAI GPT-4
config = Config.from_profile("openai_gpt4")

# Anthropic Claude
config = Config.from_profile("anthropic_claude")

# Ollama 本地模型
config = Config.from_profile("ollama_local")
```

---

## 扩展能力

### 1. 创建自定义 Skill

#### Skill 目录结构

```
skills/my_skill/
├── SKILL.md          # 必需：元数据和文档
├── executor.py       # 可选：自定义执行器（优先级最高）
├── prompt.template   # 可选：Prompt 模板
└── schema.py         # 可选：输出数据契约
```

#### 执行优先级

1. **executor.py** - 自定义 Python 代码（规则引擎 + LLM）
2. **prompt.template** - Prompt 模板（纯 LLM）
3. **SKILL.md** - 文档即 Skill（纯 LLM，用文档作为系统提示）

#### 示例：创建一个计算器 Skill

**步骤 1：创建目录**

```bash
mkdir -p skills/calculator
```

**步骤 2：创建 SKILL.md**

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

**步骤 3：创建 executor.py**

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

**步骤 4：测试 Skill**

```python
from config import Config
from agent.coordinator import Coordinator

config = Config.from_file()
coordinator = Coordinator(config)

# 发送计算请求
result = coordinator.process("请帮我计算：123 * 456 + 789")
print(result["final_response"])
```

### 2. 添加自定义 Tool

Tools 是 Skill 可以调用的底层功能。

```python
from agent.tools import Tool, ToolSpec, ToolInput, ToolOutput
from agent.coordinator import Coordinator

class WeatherChecker(Tool):
    """天气查询工具。"""

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="check_weather",
            description="查询指定城市的天气",
            inputs={
                "city": ToolInput("city", "string", "城市名称", required=True),
                "date": ToolInput("date", "string", "日期（YYYY-MM-DD）", required=False)
            },
            output=ToolOutput("object", "天气信息"),
            category="weather"
        )

    def execute(self, **kwargs) -> dict:
        city = kwargs["city"]
        # 这里可以调用真实的天气 API
        return {
            "city": city,
            "temperature": 25,
            "condition": "晴天",
            "humidity": 60
        }

# 注册工具
coordinator.tools.register(WeatherChecker())
```

### 3. 添加新的 LLM Provider

```python
from agent.llm_base import LLMProvider, LLMResponse

class MyProvider(LLMProvider):
    """自定义 LLM Provider。"""

    def __init__(self, api_key: str, base_url: str = None, default_model: str = "my-model"):
        self.api_key = api_key
        self.base_url = base_url
        self.default_model = default_model
        # 初始化你的客户端

    def invoke(self, messages, model=None, **kwargs) -> LLMResponse:
        """实现 LLM 调用。"""
        # 你的实现
        pass

    def stream(self, messages, model=None, **kwargs):
        """实现流式输出。"""
        # 你的实现
        pass

    def count_tokens(self, text: str) -> int:
        """实现 Token 计数。"""
        # 你的实现
        pass
```

然后在 `coordinator.py` 中注册：

```python
elif provider_name == "my_provider":
    from agent.providers.my_provider import MyProvider
    return MyProvider(
        api_key=self.config.llm.api_key,
        base_url=self.config.llm.base_url,
        default_model=self.config.llm.model
    )
```

### 4. 添加新的配置 Profile

在 `config.yaml` 中添加：

```yaml
profiles:
  my_profile:
    llm:
      provider: anthropic
      model: glm-4.7
      base_url: https://open.bigmodel.cn/api/anthropic
    budget:
      total_limit: 50000
    execution:
      confidence_threshold: 0.6
```

使用：

```python
config = Config.from_profile("my_profile")
```

---

## 进阶开发

### 1. 查看审计日志

```python
# 启用审计日志
config.execution.enable_audit_log = True
coordinator = Coordinator(config)

# 执行请求
result = coordinator.process("你的请求")

# 查看审计日志
audit_trail = coordinator.get_audit_trail()
for entry in audit_trail:
    print(f"{entry['timestamp']} - {entry['component']}: {entry['operation']}")

# 解释某个决策
explanation = coordinator.explain("为什么选择了 parse_report skill")
print(explanation)
```

### 2. 查看 Token 使用情况

```python
# 查看 Token 预算状态
budget_summary = coordinator.llm_client.budget.get_summary()
print(f"总预算: {budget_summary['total_limit']}")
print(f"已使用: {budget_summary['used']}")
print(f"剩余: {budget_summary['remaining']}")
print(f"使用率: {budget_summary['usage_ratio']:.1%}")

# 获取压缩建议
if budget_summary['usage_ratio'] > 0.8:
    print("建议启用压缩以节省 Token")
```

### 3. 查看执行指标

```python
result = coordinator.process("你的请求")

metrics = result["metrics"]
print(f"执行时间: {metrics['execution_time_ms']}ms")
print(f"总请求数: {metrics['total_requests']}")
print(f"执行技能数: {metrics['total_skills_executed']}")

# LLM 调用统计
llm_metrics = metrics["llm_metrics"]
print(f"LLM 调用次数: {llm_metrics['total_calls']}")
print(f"总 Token 使用: {llm_metrics['total_tokens']}")
```

### 4. 流式输出

```python
# 启用流式输出
result = coordinator.process("你的请求", stream=True)

# 如果使用生成器
if hasattr(result["final_response"], "__iter__"):
    for chunk in result["final_response"]:
        print(chunk, end="", flush=True)
```

### 5. 自定义 Skill 执行策略

```python
from agent.skill_executor import SkillExecutor

class CustomExecutor(SkillExecutor):
    """自定义执行器，添加重试逻辑。"""

    def execute(self, skill, sub_task, context):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = super().execute(skill, sub_task, context)
                if result.get("success"):
                    return result
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                print(f"重试 {attempt + 1}/{max_retries}...")
```

---

## 常见问题

### Q1: 如何调试 Skill 执行？

**A:** 启用审计日志，查看完整执行链：

```python
config.execution.enable_audit_log = True
coordinator = Coordinator(config)
result = coordinator.process("你的请求")

# 查看详细日志
for entry in coordinator.get_audit_trail():
    print(entry)
```

### Q2: Skills 之间如何传递数据？

**A:** 通过 Scratchpad (Layer 2)，前一个 Skill 的输出自动传递给下一个：

```python
# Skill 1 输出
return {
    "structured": {"bmi": 25.5, "category": "overweight"},
    "text": "BMI 为 25.5，属于超重范围。"
}

# Skill 2 可以访问
previous_results = context.get("previous_results", {})
bmi_data = previous_results.get("skill1", {}).get("structured", {})
```

### Q3: 如何控制 Token 使用？

**A:** 设置预算阈值和启用压缩：

```python
config.budget.total_limit = 50000
config.budget.warning_threshold = 0.8
config.budget.enable_compression = True
```

### Q4: 如何使用不同的 LLM 模型？

**A:** 修改配置文件或使用 profile：

```python
# 方式一：修改配置
config.llm.model = "gpt-4"

# 方式二：使用 profile
config = Config.from_profile("openai_gpt4")

# 方式三：环境变量
import os
os.environ["LLM_MODEL"] = "claude-3-opus-20240229"
config = Config.from_env()
```

### Q5: 如何添加新的配置环境？

**A:** 创建新的 profile 配置：

```yaml
# config.yaml
profiles:
  production:
    llm:
      model: claude-3-opus-20240229
    budget:
      total_limit: 500000
  development:
    llm:
      model: claude-3-haiku-20240307
    budget:
      total_limit: 10000
```

---

## 项目文件说明

| 文件/目录 | 说明 |
|-----------|------|
| `main.py` | 主入口，交互模式 |
| `config.py` | 全局配置类 |
| `config_loader.py` | YAML 配置加载器 |
| `config.yaml` | 项目默认配置 |
| `config.local.yaml` | 本地配置（不提交） |
| `agent/coordinator.py` | 协调器 |
| `agent/planner.py` | 任务规划 |
| `agent/skill_executor.py` | Skill 执行器 |
| `agent/synthesizer.py` | 结果综合 |
| `agent/context.py` | 三层上下文 |
| `agent/scratchpad.py` | 工作记忆 |
| `agent/llm_client.py` | LLM 客户端 |
| `agent/token_budget.py` | Token 预算 |
| `agent/audit.py` | 审计日志 |
| `agent/replanner.py` | 动态恢复 |
| `agent/tools.py` | Tool 系统 |
| `agent/providers/` | LLM Provider 实现 |
| `skills/` | Skills 目录 |
| `utils/skill_loader.py` | Skill 加载器 |

---

## 更多资源

- 设计文档：`docs/plans/2025-02-28-agent-skills-framework-design.md`
- 教程文档：`TUTORIAL.md`
- 示例 Skills：`skills/` 目录
- 原文章：[别急着上 Multi-Agent，也许「Agent Skills」会更好](https://mp.weixin.qq.com/s/_uoHjcMbVlx9PrUXRF6Efg)

---

**最后更新**: 2026-02-28
