# API 接口详细规范

**版本**: 1.0.0
**日期**: 2026-02-28

---

## 目录

1. [通用规范](#1-通用规范)
2. [Agent API](#2-agent-api)
3. [Skill Management API](#3-skill-management-api)
4. [Session API](#4-session-api)
5. [Admin API](#5-admin-api)
6. [WebSocket 协议](#6-websocket-协议)
7. [Webhook 规范](#7-webhook-规范)
8. [错误处理](#8-错误处理)

---

## 1. 通用规范

### 1.1 基础 URL

```
生产环境: https://api.agent.example.com
开发环境: http://localhost:8000
```

### 1.2 通用请求头

```
Content-Type: application/json
Authorization: Bearer <jwt_token>
X-Request-ID: <uuid>
X-Tenant-ID: <tenant_id>
```

### 1.3 通用响应头

```
Content-Type: application/json
X-Request-ID: <uuid>
X-Rate-Limit-Remaining: <count>
X-Rate-Limit-Reset: <timestamp>
```

### 1.4 通用响应格式

```json
{
  "success": true,
  "data": {},
  "error": null,
  "meta": {
    "request_id": "uuid",
    "timestamp": "2026-02-28T10:00:00Z",
    "version": "1.0.0"
  }
}
```

### 1.5 分页规范

```json
{
  "items": [],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 100,
    "total_pages": 5,
    "has_next": true,
    "has_prev": false
  }
}
```

---

## 2. Agent API

### 2.1 发送消息

```http
POST /api/v1/agent/chat
```

**请求体**:
```json
{
  "message": "请帮我分析这份体检报告",
  "session_id": "session-uuid-or-null",
  "stream": false,
  "context": {
    "user_profile": {
      "age": 30,
      "gender": "male"
    },
    "metadata": {
      "source": "web"
    }
  }
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "response": "根据您的体检报告，我为您分析如下...",
    "session_id": "session-uuid",
    "plan": {
      "intent": "分析健康体检报告",
      "steps": [
        {
          "skill": "parse_report",
          "sub_task": "解析体检报告数据",
          "confidence": 0.95
        },
        {
          "skill": "assess_risk",
          "sub_task": "评估健康风险",
          "confidence": 0.90
        },
        {
          "skill": "generate_advice",
          "sub_task": "生成健康建议",
          "confidence": 0.88
        }
      ],
      "estimated_tokens": 8000
    },
    "metrics": {
      "duration_ms": 3500,
      "tokens_used": 7500,
      "skills_executed": 3,
      "llm_calls": 4
    },
    "audit_id": "audit-uuid"
  },
  "meta": {
    "request_id": "req-uuid",
    "timestamp": "2026-02-28T10:00:00Z"
  }
}
```

### 2.2 流式对话

```
WS /api/v1/agent/chat/stream?token=<jwt_token>
```

**客户端消息**:
```json
{
  "type": "request",
  "id": "req-uuid",
  "data": {
    "message": "请帮我分析...",
    "session_id": "session-uuid-or-null"
  }
}
```

**服务端消息流**:
```json
// 1. 开始处理
{"type": "start", "id": "req-uuid", "data": {"session_id": "session-uuid"}}

// 2. 计划生成
{"type": "plan", "id": "req-uuid", "data": {"plan": {...}}}

// 3. Skill 执行开始
{"type": "skill_start", "id": "req-uuid", "data": {"skill": "parse_report"}}

// 4. 响应片段
{"type": "chunk", "id": "req-uuid", "data": {"content": "根据您的体检报告..."}}
{"type": "chunk", "id": "req-uuid", "data": {"content": "您的血压略高..."}}

// 5. 完成
{
  "type": "done",
  "id": "req-uuid",
  "data": {
    "metrics": {
      "duration_ms": 3500,
      "tokens_used": 7500
    }
  }
}
```

### 2.3 批量处理

```http
POST /api/v1/agent/batch
```

**请求体**:
```json
{
  "requests": [
    {"id": "req1", "message": "第一个问题"},
    {"id": "req2", "message": "第二个问题"},
    {"id": "req3", "message": "第三个问题"}
  ]
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "id": "req1",
        "success": true,
        "response": "..."
      },
      {
        "id": "req2",
        "success": true,
        "response": "..."
      },
      {
        "id": "req3",
        "success": false,
        "error": {
          "code": "SKILL_NOT_FOUND",
          "message": "Required skill not available"
        }
      }
    ]
  }
}
```

### 2.4 取消请求

```http
DELETE /api/v1/agent/requests/{request_id}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "cancelled": true,
    "status": "cancelled"
  }
}
```

---

## 3. Skill Management API

### 3.1 列出 Skills

```http
GET /api/v1/skills
```

**查询参数**:
- `category`: 技能分类过滤
- `tag`: 标签过滤
- `enabled`: 仅显示启用的技能
- `page`: 页码
- `page_size`: 每页数量

**响应**:
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "name": "parse_report",
        "version": "1.0.0",
        "description": "解析健康体检报告",
        "category": "health",
        "triggers": ["体检报告", "化验单"],
        "tags": ["健康", "数据解析"],
        "execution_mode": "executor",
        "enabled": true,
        "author": "system",
        "created_at": "2026-01-01T00:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 15,
      "total_pages": 1
    }
  }
}
```

### 3.2 获取 Skill 详情

```http
GET /api/v1/skills/{skill_name}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "name": "parse_report",
    "version": "1.0.0",
    "description": "解析健康体检报告，提取关键指标",
    "documentation": "# Parse Report Skill\n\n该 Skill 用于...",
    "schema": {
      "input": {
        "type": "object",
        "properties": {
          "report_text": {"type": "string"}
        }
      },
      "output": {
        "type": "object",
        "properties": {
          "basic_info": {"type": "object"},
          "indicators": {"type": "array"}
        }
      }
    },
    "examples": [
      {
        "input": {"report_text": "体检报告内容..."},
        "output": {"basic_info": {...}}
      }
    ],
    "dependencies": [],
    "timeout": 30
  }
}
```

### 3.3 上传 Skill

```http
POST /api/v1/skills
Content-Type: multipart/form-data
```

**表单数据**:
- `skill_file`: Skill 包文件 (.zip)
- `manifest`: 清单 JSON

**manifest 格式**:
```json
{
  "name": "custom_skill",
  "version": "1.0.0",
  "description": "自定义技能",
  "category": "custom",
  "execution_mode": "executor"
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "skill": {
      "name": "custom_skill",
      "version": "1.0.0",
      "status": "pending_review"
    }
  }
}
```

### 3.4 启用/禁用 Skill

```http
PATCH /api/v1/skills/{skill_name}/status
```

**请求体**:
```json
{
  "enabled": true
}
```

### 3.5 删除 Skill

```http
DELETE /api/v1/skills/{skill_name}
```

---

## 4. Session API

### 4.1 获取会话详情

```http
GET /api/v1/sessions/{session_id}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "session_id": "session-uuid",
    "tenant_id": "tenant-uuid",
    "user_id": "user-uuid",
    "messages": [
      {
        "id": "msg-uuid",
        "role": "user",
        "content": "请帮我分析体检报告",
        "timestamp": "2026-02-28T10:00:00Z",
        "metadata": {}
      },
      {
        "id": "msg-uuid",
        "role": "assistant",
        "content": "根据您的体检报告...",
        "timestamp": "2026-02-28T10:00:03Z",
        "metadata": {
          "skills_used": ["parse_report", "assess_risk"]
        }
      }
    ],
    "context_state": {},
    "created_at": "2026-02-28T09:55:00Z",
    "updated_at": "2026-02-28T10:00:03Z",
    "expires_at": "2026-02-28T10:55:00Z"
  }
}
```

### 4.2 获取会话列表

```http
GET /api/v1/sessions?page=1&page_size=20
```

### 4.3 清空会话上下文

```http
POST /api/v1/sessions/{session_id}/clear
```

**响应**:
```json
{
  "success": true,
  "data": {
    "cleared": true,
    "message": "Session context cleared, history preserved"
  }
}
```

### 4.4 删除会话

```http
DELETE /api/v1/sessions/{session_id}
```

---

## 5. Admin API

### 5.1 健康检查

```http
GET /api/v1/health
```

**响应**:
```json
{
  "status": "healthy",
  "checks": {
    "database": "ok",
    "redis": "ok",
    "llm_api": "ok"
  },
  "version": "1.0.0"
}
```

### 5.2 获取指标

```http
GET /api/v1/metrics
```

**响应** (Prometheus 格式):
```
# HELP agent_requests_total Total number of requests
# TYPE agent_requests_total counter
agent_requests_total{tenant_id="tenant-1"} 1234

# HELP agent_request_duration_seconds Request duration
# TYPE agent_request_duration_seconds histogram
agent_request_duration_seconds_bucket{le="0.1"} 100
agent_request_duration_seconds_bucket{le="1.0"} 500
```

### 5.3 租户管理

```http
# 创建租户
POST /api/v1/admin/tenants

# 获取租户列表
GET /api/v1/admin/tenants

# 获取租户详情
GET /api/v1/admin/tenants/{tenant_id}

# 更新租户
PUT /api/v1/admin/tenants/{tenant_id}

# 删除租户
DELETE /api/v1/admin/tenants/{tenant_id}
```

**创建租户请求**:
```json
{
  "name": "示例公司",
  "plan": "pro",
  "settings": {
    "default_model": "glm-4.7"
  },
  "rate_limits": {
    "requests_per_minute": 100,
    "tokens_per_day": 500000
  }
}
```

### 5.4 用户管理

```http
# 创建用户
POST /api/v1/admin/users

# 获取用户列表
GET /api/v1/admin/users?tenant_id={tenant_id}

# 更新用户
PUT /api/v1/admin/users/{user_id}

# 删除用户
DELETE /api/v1/admin/users/{user_id}
```

---

## 6. WebSocket 协议

### 6.1 连接

```
wss://api.agent.example.com/api/v1/agent/chat/stream?token=<jwt_token>
```

### 6.2 心跳

```json
// 客户端 → 服务端 (每 30 秒)
{"type": "ping", "id": "ping-1"}

// 服务端 → 客户端
{"type": "pong", "id": "ping-1"}
```

### 6.3 消息类型

| 类型 | 方向 | 说明 |
|------|------|------|
| `request` | C→S | 发送请求 |
| `start` | S→C | 开始处理 |
| `plan` | S→C | 执行计划 |
| `skill_start` | S→C | Skill 开始 |
| `skill_end` | S→C | Skill 完成 |
| `chunk` | S→C | 响应片段 |
| `error` | S→C | 错误信息 |
| `done` | S→C | 处理完成 |
| `cancel` | C→S | 取消请求 |
| `ping/pong` | 双向 | 心跳 |

---

## 7. Webhook 规范

### 7.1 事件类型

| 事件 | 说明 |
|------|------|
| `agent.completed` | 请求完成 |
| `agent.failed` | 请求失败 |
| `skill.executed` | Skill 执行完成 |
| `skill.failed` | Skill 执行失败 |
| `threshold.exceeded` | 阈值告警 |

### 7.2 Webhook Payload

```json
{
  "id": "evt-uuid",
  "event": "agent.completed",
  "timestamp": "2026-02-28T10:00:00Z",
  "tenant_id": "tenant-uuid",
  "data": {
    "request_id": "req-uuid",
    "session_id": "session-uuid",
    "user_id": "user-uuid",
    "user_input": "用户输入...",
    "response": "响应内容...",
    "metrics": {
      "duration_ms": 3500,
      "tokens_used": 7500,
      "skills_executed": 3
    }
  }
}
```

### 7.3 签名验证

```python
# 服务端签名
signature = hmac_sha256(webhook_secret, json.dumps(payload))

# 请求头
X-Webhook-Signature: sha256=<signature>

# 客户端验证
expected_sig = hmac_sha256(webhook_secret, body)
if not hmac.compare_digest(expected_sig, received_sig):
    raise SecurityError("Invalid signature")
```

---

## 8. 错误处理

### 8.1 错误响应格式

```json
{
  "success": false,
  "error": {
    "code": "SKILL_NOT_FOUND",
    "message": "Skill 'xxx' not found",
    "details": {},
    "request_id": "req-uuid"
  }
}
```

### 8.2 HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 400 | 请求错误 |
| 401 | 未认证 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 429 | 请求过多 |
| 500 | 服务器错误 |

### 8.3 错误码列表

| 错误码 | 说明 |
|--------|------|
| `INVALID_REQUEST` | 请求参数无效 |
| `UNAUTHORIZED` | 未认证 |
| `FORBIDDEN` | 无权限 |
| `RATE_LIMIT_EXCEEDED` | 请求过多 |
| `SKILL_NOT_FOUND` | Skill 不存在 |
| `SKILL_EXECUTION_FAILED` | Skill 执行失败 |
| `TOKEN_LIMIT_EXCEEDED` | Token 额度超限 |
| `TENANT_DISABLED` | 租户已禁用 |

---

*文档版本: 1.0.0*
*最后更新: 2026-02-28*
