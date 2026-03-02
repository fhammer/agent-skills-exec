# Agent Skills Framework - CLI工具规范

**版本**: 1.0.0
**日期**: 2026-03-02
**作者**: AI架构师
**状态**: 设计中

---

## 概述

### 设计目标

提供一套命令行工具，让开发者能够在5分钟内完成：
1. 创建第一个Skill
2. 配置数据源连接
3. 测试Skill执行
4. 部署到本地或生产环境

### 核心原则

| 原则 | 说明 | 实现 |
|------|------|------|
| **简单优先** | 最少命令完成最多工作 | 智能默认值 |
| **交互式引导** | 不强制记忆所有参数 | 可选的交互式输入 |
| **即时反馈** | 每个操作都有清晰输出 | 进度提示、成功/失败标识 |
| **模板驱动** | 减少重复代码编写 | 4种Skill模板 |

---

## 命令规范

### 1. asf init - 初始化项目

**功能**: 创建新项目结构

**语法**:
```bash
asf init <project_name> [options]
```

**参数**:
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| project_name | string | ✅ | 项目名称 |

**选项**:
| 选项 | 简写 | 默认值 | 说明 |
|------|------|--------|------|
| --template | -t | basic | 项目模板类型 |
| --force | -f | false | 强制覆盖已存在目录 |

**模板类型**:
- `basic` - 基础项目结构
- `ecommerce` - 电商场景模板（包含示例Skills）

**输出示例**:
```bash
$ asf init my-agent
✓ Created directory: my-agent/
✓ Created directory: my-agent/skills/
✓ Created directory: my-agent/config/
✓ Created directory: my-agent/test_data/
✓ Created file: my-agent/config.yaml
✓ Created file: my-agent/README.md

Next steps:
  1. cd my-agent
  2. asf skill create <skill-name>
  3. asf config add-database <name>
  4. asf test <skill-name>
```

**生成结构**:
```
my-agent/
├── skills/              # Skills目录
├── config/              # 配置文件目录
│   ├── default.yaml     # 默认配置
│   └── local.yaml       # 本地配置（不提交）
├── test_data/           # 测试数据
├── config.yaml          # 项目配置
└── README.md            # 项目说明
```

---

### 2. asf skill create - 创建Skill

**功能**: 创建新Skill，基于模板生成代码

**语法**:
```bash
asf skill create <skill_name> [options]
```

**参数**:
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| skill_name | string | ✅ | Skill名称（snake_case） |

**选项**:
| 选项 | 简写 | 默认值 | 说明 |
|------|------|--------|------|
| --template | -t | basic | Skill模板类型 |
| --description | -d | "" | Skill描述 |
| --force | -f | false | 强制覆盖已存在Skill |

**模板类型**:
| 模板 | 适用场景 | 包含文件 |
|------|----------|----------|
| `basic` | 简单LLM处理 | executor.py, SKILL.md |
| `database` | 数据库查询 | executor.py, schema.py, SKILL.md, test_executor.py |
| `api` | API调用 | executor.py, schema.py, SKILL.md, test_executor.py |
| `llm` | 纯LLM处理 | executor.py, prompt.template, SKILL.md |

**输出示例**:
```bash
$ asf skill create order_query --template database
✓ Created directory: skills/order_query/
✓ Created file: skills/order_query/SKILL.md
✓ Created file: skills/order_query/executor.py
✓ Created file: skills/order_query/schema.py
✓ Created file: skills/order_query/test_executor.py

Next steps:
  1. Edit skills/order_query/executor.py to implement your logic
  2. Run: asf test order_query
```

---

### 3. asf skill list - 列出Skills

**功能**: 列出项目中所有Skills

**语法**:
```bash
asf skill list [options]
```

**选项**:
| 选项 | 简写 | 默认值 | 说明 |
|------|------|--------|------|
| --verbose | -v | false | 显示详细信息 |

**输出示例**:
```bash
$ asf skill list
Skills in project:
  ✓ order_query    - 订单查询技能 (database)
  ✓ return_request - 退货申请技能 (api)
  ✗ product_search - [未实现] (basic)

$ asf skill list --verbose
Skills in project:

  order_query (database)
    Description: 订单查询技能
    Version: 1.0.0
    Status: Implemented
    Last modified: 2026-03-02 10:30:00
    Tools: [order_db, logistics_api]

  return_request (api)
    Description: 退货申请技能
    Version: 1.0.0
    Status: Implemented
    Last modified: 2026-03-02 11:15:00
    Tools: [order_api, case_api]
```

---

### 4. asf config - 配置管理

**功能**: 管理项目配置（数据源、LLM等）

#### 4.1 asf config add-database - 添加数据库

**语法**:
```bash
asf config add-database <name> [options]
```

**参数**:
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| name | string | ✅ | 数据源名称 |

**选项**:
| 选项 | 简写 | 默认值 | 说明 |
|------|------|--------|------|
| --type | | postgresql | 数据库类型 |
| --url | | | 连接字符串 |
| --interactive | -i | false | 交互式输入 |

**交互式模式**:
```bash
$ asf config add-database order_db --interactive
? 数据库类型: postgresql
? 连接地址: localhost:5432
? 数据库名: ecommerce
? 用户名: postgres
? 密码: *****
Testing connection... ✓ Connected successfully!
Configuration saved to config/local.yaml
```

#### 4.2 asf config add-api - 添加API

**语法**:
```bash
asf config add-api <name> [options]
```

**交互式模式**:
```bash
$ asf config add-api logistics_api --interactive
? Base URL: https://api.logistics.com/v1
? 认证类型: Bearer Token
? Token: *****
Testing connection... ✓ API is reachable!
Configuration saved to config/local.yaml
```

#### 4.3 asf config list - 列出配置

**输出示例**:
```bash
$ asf config list
Data sources:
  ✓ order_db     (postgresql) - localhost:5432/ecommerce
  ✓ user_db      (mongodb) - localhost:27017/users
  ✓ logistics_api (http) - https://api.logistics.com/v1

LLM config:
  Provider: anthropic
  Model: glm-4.7
  Base URL: https://open.bigmodel.cn/api/anthropic
```

---

### 5. asf test - 测试Skill

**功能**: 本地测试Skill执行

**语法**:
```bash
asf test <skill_name> [options]
```

**参数**:
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| skill_name | string | ✅ | Skill名称 |

**选项**:
| 选项 | 简写 | 默认值 | 说明 |
|------|------|--------|------|
| --input | -i | | 输入数据（JSON或字符串） |
| --context | -c | {} | 上下文数据（JSON） |
| --verbose | -v | false | 显示详细执行过程 |
| --save-output | | | 保存输出到文件 |

**输出示例**:
```bash
$ asf test order_query --input "查询订单12345"
Testing skill: order_query
Input: "查询订单12345"
Loading LLM client...
Executing skill...
✓ Skill executed successfully

Output:
  structured:
    order_id: "12345"
    status: "shipped"
    estimated_delivery: "2026-03-05"

  text: "您的订单12345已发货，预计3月1日送达。"

Metrics:
  Duration: 1.2s
  Tokens used: 850
  LLM calls: 1
  Tool calls: 1
```

---

### 6. asf deploy - 部署

**功能**: 部署Agent服务

**语法**:
```bash
asf deploy [options]
```

**选项**:
| 选项 | 简写 | 默认值 | 说明 |
|------|------|--------|------|
| --mode | -m | local | 部署模式 |
| --port | -p | 8000 | 服务端口 |
| --host | | 0.0.0.0 | 绑定地址 |

**部署模式**:
- `local` - 本地运行（开发测试）
- `production` - 生产环境（需要配置服务器）

**输出示例**:
```bash
$ asf deploy --mode local
Loading configuration...
Loading skills...
  ✓ order_query
  ✓ return_request
Starting API server...
✓ Server started on http://localhost:8000
✓ API documentation: http://localhost:8000/docs
✓ API Key: sk_agent_xxxxxxxxxxxxxx

Press Ctrl+C to stop
```

---

### 7. asf run - 快速运行（开发模式）

**功能**: 快速测试单个请求（无需启动服务）

**语法**:
```bash
asf run <message> [options]
```

**参数**:
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| message | string | ✅ | 用户消息 |

**选项**:
| 选项 | 简写 | 默认值 | 说明 |
|------|------|--------|------|
| --skills | -s | all | 指定使用的Skills |
| --verbose | -v | false | 显示详细过程 |

**输出示例**:
```bash
$ asf run "帮我查一下订单12345"
Planning...
  Selected skills: [order_query]
Executing skill: order_query
✓ Done

Response: 您的订单12345已发货，预计3月1日送达。
```

---

### 8. asf doctor - 健康检查

**功能**: 检查项目健康状态

**语法**:
```bash
asf doctor
```

**输出示例**:
```bash
$ asf doctor
Checking project health...

Configuration:
  ✓ config.yaml exists
  ✓ LLM config is valid
  ✓ Data source connections are healthy

Skills:
  ✓ order_query - Valid
  ✓ return_request - Valid
  ⚠ product_search - Not implemented

Environment:
  ✓ Python 3.8+
  ✓ Required packages installed
  ✓ API Key configured

Overall: Healthy (2 warnings)
```

---

## Skill模板规范

### 模板1: basic - 基础LLM处理

**适用场景**: 简单的自然语言处理任务

**生成文件**:
```
skills/my_skill/
├── SKILL.md
└── executor.py
```

**executor.py模板**:
```python
"""{{skill_name}} Skill executor."""

from agent.llm_client import LLMClient
from typing import Dict, Any


def execute(llm: LLMClient, sub_task: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute {{skill_name}} skill.

    Args:
        llm: LLM client for text generation
        sub_task: The specific task to execute
        context: Execution context containing:
            - tools: Available data source tools
            - previous_results: Results from previous skills
            - user_input: Original user input

    Returns:
        Dict with:
            - structured: Processed data (dict)
            - text: Natural language response (str)
    """
    # TODO: Implement your business logic here

    # Example: Use LLM to process the task
    prompt = f"""Please process the following request: {sub_task}"""
    response = llm.invoke(prompt)

    return {
        "structured": {
            "result": response
        },
        "text": response
    }
```

---

### 模板2: database - 数据库查询

**适用场景**: 查询数据库并返回结构化结果

**生成文件**:
```
skills/my_skill/
├── SKILL.md
├── executor.py
├── schema.py
└── test_executor.py
```

**executor.py模板**:
```python
"""{{skill_name}} Skill executor (database template)."""

from agent.llm_client import LLMClient
from typing import Dict, Any


def execute(llm: LLMClient, sub_task: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute {{skill_name}} skill with database query.

    This template demonstrates:
    1. Extracting parameters using regex (rule engine)
    2. Querying database using configured tools
    3. Formatting results (rule engine)
    4. Generating natural language response (LLM)
    """
    import re

    # Step 1: Extract parameters (rule engine)
    # TODO: Update regex pattern based on your needs
    pattern = r'{{your_regex_pattern}}'
    match = re.search(pattern, sub_task)

    if not match:
        return {
            "structured": {"error": "Could not extract required parameters"},
            "text": "请提供必要的信息"
        }

    param = match.group(1)

    # Step 2: Query database using tools
    tools = context.get("tools", {})
    # TODO: Replace with your actual tool name
    db_tool = tools.get("{{your_database_tool}}")

    if not db_tool:
        return {
            "structured": {"error": "Database tool not configured"},
            "text": "数据库未配置"
        }

    result = db_tool.execute(query="SELECT * FROM {{table}} WHERE id=%s", params=(param,))

    # Step 3: Format results (rule engine)
    if not result:
        return {
            "structured": {"found": False},
            "text": "未找到相关信息"
        }

    # Step 4: Generate response (LLM)
    prompt = f"""Based on the following data, generate a friendly response:
Data: {result}
User request: {sub_task}
"""
    response = llm.invoke(prompt)

    return {
        "structured": {
            "found": True,
            "data": result
        },
        "text": response
    }
```

---

### 模板3: api - API调用

**适用场景**: 调用外部API获取数据

**生成文件**:
```
skills/my_skill/
├── SKILL.md
├── executor.py
├── schema.py
└── test_executor.py
```

**executor.py模板**:
```python
"""{{skill_name}} Skill executor (API template)."""

from agent.llm_client import LLMClient
from typing import Dict, Any


def execute(llm: LLMClient, sub_task: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute {{skill_name}} skill with API call.
    """
    import re

    # Step 1: Extract parameters
    # TODO: Update based on your API requirements
    pattern = r'{{your_regex_pattern}}'
    match = re.search(pattern, sub_task)

    if not match:
        return {
            "structured": {"error": "Could not extract required parameters"},
            "text": "请提供必要的信息"
        }

    param = match.group(1)

    # Step 2: Call API using tools
    tools = context.get("tools", {})
    api_tool = tools.get("{{your_api_tool}}")

    if not api_tool:
        return {
            "structured": {"error": "API tool not configured"},
            "text": "API未配置"
        }

    result = api_tool.get(endpoint=f"/{{endpoint}}/{param}")

    # Step 3: Process and respond
    if result.get("error"):
        return {
            "structured": {"error": result["error"]},
            "text": f"API调用失败: {result['error']}"
        }

    prompt = f"""Based on the following API response, generate a friendly response:
Response: {result}
User request: {sub_task}
"""
    response = llm.invoke(prompt)

    return {
        "structured": result,
        "text": response
    }
```

---

### 模板4: llm - 纯LLM处理

**适用场景**: 复杂的自然语言理解/生成

**生成文件**:
```
skills/my_skill/
├── SKILL.md
├── prompt.template
└── executor.py
```

**prompt.template**:
```
You are a {{skill_description}}.

User request: {user_input}

Context:
{context}

Please respond with:
1. A structured analysis
2. A natural language response

Response format:
{{output_format}}
```

---

## 配置文件规范

### config.yaml

```yaml
# 项目配置
project:
  name: my-agent
  version: 1.0.0

# LLM配置
llm:
  provider: anthropic  # openai, anthropic, ollama
  model: glm-4.7
  api_key: ${LLM_API_KEY}
  base_url: https://open.bigmodel.cn/api/anthropic
  temperature: 0.7
  max_tokens: 2000

# Token预算
budget:
  total_limit: 100000
  warning_threshold: 0.8
  enable_compression: true

# 执行配置
execution:
  max_skill_retries: 2
  enable_audit_log: true
  confidence_threshold: 0.5

# 数据源配置（由asf config add-*命令生成）
data_sources:
  # 数据库
  order_db:
    type: postgresql
    connection_string: ${DATABASE_URL}
    pool_size: 10

  # API
  logistics_api:
    type: http
    base_url: https://api.logistics.com/v1
    auth:
      type: bearer
      token: ${LOGISTICS_API_TOKEN}

# API服务配置
api:
  host: 0.0.0.0
  port: 8000
  debug: false
  api_key: ${AGENT_API_KEY}
```

---

## 实现计划

### 开发工作量

| 功能 | 优先级 | 工作量 | 依赖 |
|------|--------|--------|------|
| asf init | P0 | 2小时 | - |
| asf skill create (basic) | P0 | 2小时 | - |
| asf skill create (database) | P0 | 2小时 | - |
| asf skill create (api) | P1 | 2小时 | - |
| asf skill create (llm) | P1 | 1小时 | - |
| asf skill list | P0 | 1小时 | - |
| asf config add-database | P0 | 3小时 | - |
| asf config add-api | P0 | 3小时 | - |
| asf config list | P0 | 1小时 | - |
| asf test | P0 | 3小时 | - |
| asf deploy (local) | P0 | 3小时 | - |
| asf run | P1 | 2小时 | - |
| asf doctor | P1 | 2小时 | - |
| **总计** | - | **~32小时 (4天)** | - |

### 技术栈

- **CLI框架**: Click / Typer
- **配置解析**: PyYAML
- **交互式输入**: questionary
- **输出格式**: rich (彩色输出)

---

**文档版本**: 1.0.0
**最后更新**: 2026-03-02
**下一步**: 开始实现CLI工具
