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
├── agent/                   # 核心 Agent 组件
│   ├── coordinator.py       # 协调器
│   ├── context.py           # 三层上下文
│   ├── planner.py           # 任务规划
│   ├── executor.py          # Skill 执行
│   ├── synthesizer.py       # 结果综合
│   ├── skill_executor.py    # 单 Skill 执行器
│   ├── replanner.py         # 动态重规划
│   ├── llm_base.py          # LLM 抽象
│   ├── llm_client.py        # LLM 客户端
│   ├── token_budget.py      # Token 管理
│   ├── tools.py             # 工具系统
│   ├── audit.py             # 审计日志
│   └── providers/           # LLM 提供商
│       ├── openai_provider.py
│       ├── anthropic_provider.py
│       └── ollama_provider.py
├── skills/                  # Skills 目录（即插即用）
│   ├── parse_report/        # 示例：体检报告解析
│   ├── assess_risk/         # 示例：风险评估
│   └── generate_advice/     # 示例：建议生成
├── shared/                  # 共享工具
│   ├── metrics_utils.py     # 健康指标计算
│   └── context_schema.py    # 数据契约
├── utils/                   # 框架工具
│   └── skill_loader.py      # Skill 自动发现
└── dialogue/                # 对话管理
    ├── manager.py           # 会话管理器
    └── protocol.py          # 请求/响应协议
```

## 快速开始

### 安装

```bash
# 克隆仓库
cd agent-skills-exec

# 安装依赖
pip install -r requirements.txt

# 或安装完整依赖
pip install -e ".[all]"
```

### 配置

设置环境变量：

```bash
# OpenAI
export LLM_PROVIDER=openai
export LLM_API_KEY=your-api-key-here
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

或复制 `.env.example` 到 `.env` 并填写：

```bash
cp .env.example .env
# 编辑 .env 文件
```

> **提示**: 详细使用教程请参考 [TUTORIAL.md](TUTORIAL.md)

### 运行

```bash
# 交互模式
python main.py

# 演示模式（健康检查示例）
python main.py --demo

# 直接运行示例
python examples/health_check_demo.py
```

## 开发指南

### 创建新 Skill

一个 Skill 就是一个目录：

```
skills/my_skill/
├── SKILL.md          # 必需：元数据 + 文档
├── executor.py       # 可选：自定义执行器
├── prompt.template   # 可选：Prompt 模板
└── schema.py         # 可选：输出数据契约
```

**SKILL.md 格式：**

```yaml
---
name: my_skill
version: 1.0.0
description: 我的 Skill 描述
triggers:
  - 触发词1
  - 触发词2
tags:
  - 标签1
  - 标签2
---

# Skill 说明

详细的功能说明...
```

**executor.py 示例：**

```python
from agent.llm_client import LLMClient
from typing import Dict, Any

def execute(llm: LLMClient, sub_task: str, context: Dict[str, Any]) -> Dict[str, Any]:
    # 规则引擎：确定性计算
    result = calculate_something()

    # LLM：自然语言生成
    text = llm.invoke(f"请解释: {result}")

    return {
        "structured": {"result": result},
        "text": text
    }
```

### 五条核心设计原则

1. **Skill 上下文隔离** - 用户输入、工作记忆、环境信息各自独立
2. **Skill 渐进式披露** - 每一步只看到最小必要上下文
3. **Skill 结构化契约** - Skills 之间用 TypedDict schema 定义数据格式
4. **双执行引擎** - 确定性计算交给代码，自然语言生成交给 LLM
5. **全链路可审计** - 每次 read/write/compress 操作自动记录

## 示例

### 健康检查流程

用户请求：`"帮我分析体检报告并给出建议"`

```
输入 → Planner 规划 → Executor 执行 → Synthesizer 综合
                  ↓
      [parse_report] → 解析报告数据
                  ↓
      [assess_risk] → 评估健康风险
                  ↓
      [generate_advice] → 生成健康建议
                  ↓
            输出综合报告
```

### 交互模式命令

```
/metrics        # 查看性能指标
/audit          # 查看审计日志
/explain <问题>  # 解释某个决策
/reset          # 重置会话
/quit           # 退出
```

## 技术栈

- **Python**: >=3.10
- **LLM Providers**: OpenAI, Anthropic, Ollama, 智谱 GLM
- **CLI**: Rich, Typer
- **Testing**: Pytest

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

## 设计文档

详细设计文档：[docs/plans/2025-02-28-agent-skills-framework-design.md](docs/plans/2025-02-28-agent-skills-framework-design.md)

## 许可证

MIT License

## 致谢

灵感来源于以下文章：[别急着上 Multi-Agent，也许「Agent Skills」会更好](https://mp.weixin.qq.com/s/_uoHjcMbVlx9PrUXRF6Efg)
