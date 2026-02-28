# Agent Skills Framework

模块化 Agent 能力框架 - 单智能体编排系统

## 概述

Agent Skills Framework 是一个基于"一个协调器统一调度，多个 Skills 各司其职，三层上下文贯穿始终"理念的 AI Agent 框架。

### 核心特性

- **单 Agent 编排** - 通过 Coordinator 统一调度，避免 Multi-Agent 的通信开销
- **三层上下文** - 用户输入层、工作记忆层、环境配置层，职责分明
- **渐进式披露** - 每一步只看到最小必要上下文，Token 线性增长
- **双执行引擎** - 规则引擎负责「准」，LLM 负责「智」
- **全链路审计** - 每次操作自动记录，可追溯完整决策链
- **即插即用 Skills** - 一个目录就是一个 Skill，零配置自动发现

### 适用场景

- ✅ 线性串行任务，各步依赖前步输出
- ✅ 需要确定性计算 + 自然语言生成
- ✅ 需要完整审计和可追溯性
- ✅ Token 成本敏感的场景

### 对比 Multi-Agent

| 特性 | Agent Skills | Multi-Agent |
|------|--------------|-------------|
| Token 消耗 | 6K-10K | 15K-25K |
| 通信成本 | 低 | 高 |
| 调试难度 | 低（审计日志） | 高（跨 Agent） |
| 适用场景 | 线性依赖链 | 并行/对抗/异构模型 |

## 项目结构

```
agent-skills-exec/
├── main.py                  # 入口脚本
├── config.py                # 全局配置
├── config_loader.py         # YAML 配置加载器
├── config.yaml              # 项目默认配置
├── config.local.yaml        # 本地配置（不提交）
├── agent/                   # 核心 Agent 组件
│   ├── coordinator.py       # 协调器
│   ├── context.py           # 三层上下文
│   ├── planner.py           # 任务规划
│   ├── skill_executor.py    # Skill 执行器
│   ├── synthesizer.py       # 结果综合
│   ├── replanner.py         # 动态重规划
│   ├── llm_client.py        # LLM 客户端
│   ├── token_budget.py      # Token 管理
│   ├── tools.py             # 工具系统
│   ├── audit.py             # 审计日志
│   └── providers/           # LLM 提供商
│       ├── openai_provider.py
│       ├── anthropic_provider.py
│       ├── ollama_provider.py
│       └── zhipu_provider.py
├── skills/                  # Skills 目录（即插即用）
│   ├── parse_report/        # 示例：体检报告解析
│   ├── assess_risk/         # 示例：风险评估
│   └── generate_advice/     # 示例：建议生成
├── utils/                   # 框架工具
│   └── skill_loader.py      # Skill 自动发现
└── docs/                    # 文档
    ├── QUICK_START_GUIDE.md # 快速启动指南
    └── plans/               # 设计文档
```

---

## 快速开始

### 1. 环境准备

```bash
# 克隆仓库
cd agent-skills-exec

# 安装依赖
pip install -r requirements.txt
```

**系统要求**: Python 3.8+

### 2. 配置 LLM Provider

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

### 3. 运行框架

**方式一：交互模式**

```bash
python main.py
```

**方式二：Python 代码**

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
```

**方式三：使用预设 Profile**

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

coordinator = Coordinator(config)
```

---

## 扩展能力

### 创建自定义 Skill

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
    """执行计算任务。"""
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
    pattern = r'[\d+\-*/(). ]+'
    matches = re.findall(pattern, text)
    return matches[0] if matches else text

def eval_expression(expr: str) -> float:
    """安全地计算表达式。"""
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

### 添加自定义 Tool

Tools 是 Skill 可以调用的底层功能。

```python
from agent.tools import Tool, ToolSpec, ToolInput, ToolOutput

class WeatherChecker(Tool):
    """天气查询工具。"""

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="check_weather",
            description="查询指定城市的天气",
            inputs={
                "city": ToolInput("city", "string", "城市名称", required=True)
            },
            output=ToolOutput("object", "天气信息"),
            category="weather"
        )

    def execute(self, **kwargs) -> dict:
        city = kwargs["city"]
        # 调用天气 API
        return {
            "city": city,
            "temperature": 25,
            "condition": "晴天"
        }

# 注册工具
coordinator.tools.register(WeatherChecker())
```

---

## 进阶开发

### 查看审计日志

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

### 查看 Token 使用情况

```python
budget_summary = coordinator.llm_client.budget.get_summary()
print(f"总预算: {budget_summary['total_limit']}")
print(f"已使用: {budget_summary['used']}")
print(f"剩余: {budget_summary['remaining']}")
print(f"使用率: {budget_summary['usage_ratio']:.1%}")
```

---

## 常见问题

### Q1: 如何使用不同的 LLM 模型？

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

### Q3: 如何调试 Skill 执行？

**A:** 启用审计日志，查看完整执行链：

```python
config.execution.enable_audit_log = True
coordinator = Coordinator(config)
result = coordinator.process("你的请求")

# 查看详细日志
for entry in coordinator.get_audit_trail():
    print(entry)
```

---

## 测试

```bash
# 测试配置加载
python test_config.py

# 测试框架功能
python test_with_config.py

# 测试 GLM-4.7 连接
python test_glm47_simple.py

# 查看可用模型
python test_glm_models.py
```

---

## 支持的 LLM 提供商

| 提供商 | Provider | Model 示例 | 说明 |
|--------|----------|-----------|------|
| OpenAI | `openai` | `gpt-4`, `gpt-3.5-turbo` | 需 API Key |
| Anthropic | `anthropic` | `claude-3-opus-20240229` | 需 API Key |
| Ollama | `ollama` | `llama3`, `mistral` | 本地运行 |
| 智谱 GLM | `anthropic` | `glm-4.7`, `glm-4-flash` | 使用兼容端点 |

### 智谱 GLM 配置示例

```bash
export LLM_PROVIDER=anthropic
export LLM_BASE_URL=https://open.bigmodel.cn/api/anthropic
export LLM_MODEL=glm-4.7
export LLM_API_KEY=你的智谱API密钥
```

可用模型：
- `glm-4.7` - 最新版本（推荐）
- `glm-4-flash` - 快速版本

---

## 文档

- **快速启动指南**: [docs/QUICK_START_GUIDE.md](docs/QUICK_START_GUIDE.md)
- **详细教程**: [TUTORIAL.md](TUTORIAL.md)
- **设计文档**: [docs/plans/2025-02-28-agent-skills-framework-design.md](docs/plans/2025-02-28-agent-skills-framework-design.md)

---

## 许可证

MIT License

---

## 致谢

灵感来源于以下文章：[别急着上 Multi-Agent，也许「Agent Skills」会更好](https://mp.weixin.qq.com/s/_uoHjcMbVlx9PrUXRF6Efg)
