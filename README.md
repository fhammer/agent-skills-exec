# Agent Skills Framework

> 通用智能体开发框架 - 单 Agent 编排系统，快速构建企业级 AI Agent 应用

[![Tests](https://img.shields.io/badge/tests-78%2F78%20passing-success)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-44%25-yellow)](tests/)
[![Version](https://img.shields.io/badge/version-2.0.0-blue)](https://github.com/fhammer/agent-skills-exec)
[![Python](https://img.shields.io/badge/python-3.8%2B-green)](https://www.python.org/)

---

## 概述

Agent Skills Framework 是一个基于"一个协调器统一调度，多个 Skills 各司其职，三层上下文贯穿始终"理念的通用 AI Agent 开发框架。它提供了完整的多租户管理、REST API 服务、数据连接器和电商场景 Demo，能够快速接入各种业务系统。

### 核心特性

- **单 Agent 编排** - 通过 Coordinator 统一调度，避免 Multi-Agent 的通信开销，Token 消耗降低 60%+
- **三层上下文** - 用户输入层、工作记忆层、环境配置层，职责分明，可追溯可调试
- **渐进式披露** - 每一步只看到最小必要上下文，Token 线性增长（6K-10K/请求）
- **双执行引擎** - 规则引擎负责确定性计算，LLM 负责智能决策
- **全链路审计** - 每次操作自动记录，可追溯完整决策链
- **即插即用 Skills** - 一个目录就是一个 Skill，零配置自动发现
- **多租户管理** - 完整的租户隔离、资源配额、场景管理
- **REST API 服务** - 生产就绪的 FastAPI 服务，支持认证鉴权
- **数据连接器** - 支持多种数据源的统一连接器接口

### 适用场景

- 线性串行任务，各步依赖前步输出
- 需要确定性计算 + 自然语言生成
- 需要完整审计和可追溯性
- Token 成本敏感的场景
- 多租户 SaaS 应用
- 需要快速集成的企业系统

### 对比 Multi-Agent

| 特性 | Agent Skills | Multi-Agent |
|------|--------------|-------------|
| Token 消耗 | 6K-10K | 15K-25K |
| 通信成本 | 低 | 高 |
| 调试难度 | 低（审计日志） | 高（跨 Agent） |
| 适用场景 | 线性依赖链 | 并行/对抗/异构模型 |

---

## 项目结构

```
agent-skills-exec/
├── main.py                      # 入口脚本
├── config.py                    # 全局配置
├── config.yaml                  # 项目默认配置
├── CLAUDE.md                    # Claude Code 开发指南
├── agent/                       # 核心 Agent 组件
│   ├── coordinator.py           # 协调器
│   ├── context.py               # 三层上下文
│   ├── planner.py               # 任务规划
│   ├── skill_executor.py        # Skill 执行器
│   ├── synthesizer.py           # 结果综合
│   ├── llm_client.py            # LLM 客户端
│   ├── connectors/              # 数据连接器
│   └── providers/               # LLM 提供商
├── tenant/                      # 多租户管理
│   ├── manager.py               # 租户管理器
│   └── context.py               # 租户上下文
├── api/                         # FastAPI REST 服务
│   ├── main.py                  # API 入口
│   ├── routers/                 # 路由模块
│   ├── auth.py                  # 认证鉴权
│   └── middleware.py            # 中间件
├── connectors/                  # 数据连接器
│   ├── database.py              # 数据库连接器
│   ├── http.py                  # HTTP 连接器
│   └── registry.py              # 连接器注册表
├── skills/                      # Skills 目录（即插即用）
│   ├── ecommerce_recommendation/# 电商推荐 Skill
│   ├── parse_report/            # 体检报告解析
│   ├── assess_risk/             # 风险评估
│   └── generate_advice/         # 建议生成
├── examples/                    # 示例和 Demo
│   ├── ecommerce_demo.py        # 电商 Demo 1: 智能导购
│   ├── ecommerce_demo2.py       # 电商 Demo 2: 订单售后
│   └── ecommerce/               # 电商 Skills
├── tests/                       # 测试套件
│   ├── test_*.py                # 单元测试
│   ├── ecommerce/               # 电商测试
│   ├── api/                     # API 测试
│   └── tenant/                  # 租户测试
└── docs/                        # 文档
    ├── PRD_Agent_Skills_Framework.md  # 产品需求文档
    ├── design/                  # 设计文档
    └── architecture/            # 架构文档
```

---

## 快速开始

### 1. 环境准备

```bash
# 克隆仓库
git clone https://github.com/fhammer/agent-skills-exec.git
cd agent-skills-exec

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

**系统要求**: Python 3.8+

### 2. 配置 LLM Provider

创建 `config.local.yaml` 文件（不提交到 Git）：

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

## 电商 Demo

框架包含两个完整的电商场景 Demo，展示实际应用能力：

### Demo 1: 智能导购 Agent

```bash
# 基础推荐场景
python examples/ecommerce_demo.py --scenario basic

# 品牌偏好场景
python examples/ecommerce_demo.py --scenario brand

# 商品对比场景
python examples/ecommerce_demo.py --scenario comparison

# 交互式模式
python examples/ecommerce_demo.py --interactive
```

**包含 Skills**:
- `demand_analysis` - 需求分析
- `product_search` - 商品搜索
- `recommendation_ranking` - 推荐排序
- `recommendation_explanation` - 推荐解释

### Demo 2: 订单售后 Agent

```bash
# 订单查询场景
python examples/ecommerce_demo2.py --scenario query-id

# 退货申请场景
python examples/ecommerce_demo2.py --scenario return-quality

# 换货申请场景
python examples/ecommerce_demo2.py --scenario exchange

# 运行所有场景
python examples/ecommerce_demo2.py --scenario all
```

**包含 Skills**:
- `intent_classification` - 意图分类
- `order_query` - 订单查询
- `policy_validation` - 政策验证
- `case_creation` - 工单创建

---

## API 服务

框架提供生产就绪的 REST API 服务：

### 启动服务

```bash
# 启动 API 服务
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

服务启动后访问：
- API 文档: http://localhost:8000/docs
- ReDoc 文档: http://localhost:8000/redoc

### API 示例

```bash
# 对话接口
curl -X POST http://localhost:8000/api/v1/agent/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-key" \
  -d '{
    "user_id": "user123",
    "message": "推荐一款手机"
  }'

# 获取会话历史
curl http://localhost:8000/api/v1/sessions/user123/messages \
  -H "X-API-Key: test-key"

# 健康检查
curl http://localhost:8000/health
```

### API 端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/v1/agent/chat` | POST | 发送对话消息 |
| `/api/v1/sessions/{user_id}/messages` | GET | 获取会话历史 |
| `/api/v1/sessions/{user_id}` | DELETE | 清除会话 |
| `/api/v1/skills` | GET | 获取可用 Skills |
| `/api/v1/tenants` | GET | 获取租户列表 |
| `/health` | GET | 健康检查 |

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

#### 示例：创建计算器 Skill

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
    expression = extract_expression(sub_task)

    try:
        result = eval_expression(expression)
        explanation = llm.invoke(f"请解释这个计算：{expression} = {result}")

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
```

### 添加数据连接器

框架支持多种数据源连接器：

```python
from connectors.registry import registry

# 注册 PostgreSQL 连接器
connector = registry.register(
    "my_db",
    type="postgresql",
    connection_string="postgresql://user:pass@localhost/db"
)

# 在 Skill 中使用
def execute(llm, sub_task, context):
    db = context.get_connector("my_db")
    data = db.fetch_one("SELECT * FROM products WHERE id = %s", (123,))
    return {"structured": data}
```

**支持的连接器类型**:
- PostgreSQL
- MySQL
- SQLite
- HTTP/REST API
- 文件系统

---

## 多租户管理

框架内置完整的多租户支持：

```python
from tenant.manager import TenantManager
from tenant.context import TenantContext

# 创建租户管理器
manager = TenantManager()

# 创建租户
tenant = manager.create_tenant(
    tenant_id="tenant_001",
    name="示例公司",
    quota={
        "max_tokens": 1000000,
        "max_requests": 10000,
        "allowed_skills": ["*"]
    }
)

# 使用租户上下文
tenant_ctx = TenantContext(tenant)
result = coordinator.process("推荐商品", tenant_context=tenant_ctx)
```

---

## 测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_context.py

# 运行测试并显示覆盖率
pytest --cov=. --cov-report=html

# 查看覆盖率报告
open htmlcov/index.html
```

### 测试统计

| 测试套件 | 用例数 | 通过率 |
|---------|--------|--------|
| 核心框架测试 | 16 | 100% |
| 数据连接器测试 | 11 | 100% |
| 多租户管理测试 | 14 | 100% |
| 电商场景测试 | 35 | 100% |
| API 测试 | - | - |
| **总计** | **78** | **100%** |

---

## 支持的 LLM 提供商

| 提供商 | Provider | Model 示例 | 说明 |
|--------|----------|-----------|------|
| OpenAI | `openai` | `gpt-4`, `gpt-3.5-turbo` | 需 API Key |
| Anthropic | `anthropic` | `claude-3-opus-20240229` | 需 API Key |
| Ollama | `ollama` | `llama3`, `mistral` | 本地运行 |
| 智谱 GLM | `anthropic` | `glm-4.7`, `glm-4-flash` | 使用兼容端点 |

### 智谱 GLM 配置

```bash
export LLM_PROVIDER=anthropic
export LLM_BASE_URL=https://open.bigmodel.cn/api/anthropic
export LLM_MODEL=glm-4.7
export LLM_API_KEY=你的智谱API密钥
```

---

## 架构设计

### 分层架构 (5层)

```
┌─────────────────────────────────────────┐
│  Layer 5: 应用接入层                     │
│  (Web App / 移动端 / 小程序 / 企业系统)    │
├─────────────────────────────────────────┤
│  Layer 4: API 网关层                     │
│  (认证鉴权 / 限流熔断 / 路由分发)         │
├─────────────────────────────────────────┤
│  Layer 3: 智能体框架核心层                │
│  (Agent Runtime / Skill Engine)         │
├─────────────────────────────────────────┤
│  Layer 2: 基础设施层                     │
│  (多租户 / 会话 / 审计 / Tool / LLM)     │
├─────────────────────────────────────────┤
│  Layer 1: 外部服务层                     │
│  (LLM服务 / 业务API / 数据库)            │
└─────────────────────────────────────────┘
```

### 核心抽象 (6个)

| 抽象层 | 关键接口/类 | 职责 | 扩展点 |
|--------|-------------|------|--------|
| **Agent** | `Agent` 基类 | 统一调度、状态管理 | `register_plugin()`, `add_hook()` |
| **Skill** | `Skill` 基类 | 业务逻辑执行 | `execute()`, `@skill`装饰器 |
| **Tool** | `Tool` 基类 | 底层功能调用 | `@tool`装饰器, `register_tool()` |
| **Context** | `AgentContext` | 三层上下文管理 | 读写权限控制 |
| **Memory** | `MemoryBackend` | 记忆存储/检索 | `store()`, `retrieve()`, `search()` |
| **Connector** | `Connector` 基类 | 数据源连接器 | `connect()`, `fetch()`, `execute()` |

---

## 文档

- **[快速启动指南](docs/QUICK_START_GUIDE.md)** - 5分钟快速上手
- **[详细教程](TUTORIAL.md)** - 深入了解框架特性
- **[产品需求文档](docs/PRD_Agent_Skills_Framework.md)** - PRD 和用户画像
- **[架构设计文档](docs/design/architecture-design.md)** - 完整架构说明
- **[连接器开发指南](docs/connectors-guide.md)** - 开发自定义连接器
- **[测试报告](docs/TEST_REPORT.md)** - 测试结果和覆盖情况

---

## 版本历史

### v2.0.0 (2026-03-02)

- 新增多租户管理系统
- 新增 FastAPI REST 服务层
- 新增数据连接器系统
- 新增电商智能导购 Demo
- 新增订单售后客服 Demo
- 78 个测试用例全部通过
- 44% 代码覆盖率

### v1.0.0 (2025-02-28)

- 核心框架实现
- 单 Agent 编排系统
- 三层上下文管理
- 渐进式披露机制

---

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 贡献

欢迎贡献代码、报告问题或提出建议！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

---

## 致谢

灵感来源于以下文章：[别急着上 Multi-Agent，也许「Agent Skills」会更好](https://mp.weixin.qq.com/s/_uoHjcMbVlx9PrUXRF6Efg)

---

## 联系方式

- GitHub Issues: [https://github.com/fhammer/agent-skills-exec/issues](https://github.com/fhammer/agent-skills-exec/issues)
- 项目主页: [https://github.com/fhammer/agent-skills-exec](https://github.com/fhammer/agent-skills-exec)
