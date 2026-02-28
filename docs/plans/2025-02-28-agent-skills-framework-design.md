# Agent Skills Framework Design Document

**Date:** 2025-02-28
**Version:** 1.0.0
**Status:** Design Approved

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Three-Layer Context System](#three-layer-context-system)
4. [Core Components](#core-components)
5. [Data Flow & Progressive Disclosure](#data-flow--progressive-disclosure)
6. [Dual Execution Engine](#dual-execution-engine)
7. [LLM Abstraction & Token Management](#llm-abstraction--token-management)
8. [Audit Logging & Performance Monitoring](#audit-logging--performance-monitoring)
9. [Error Handling & RePlan Mechanism](#error-handling--replan-mechanism)
10. [Tool System](#tool-system)
11. [Skill Loading & Execution](#skill-loading--execution)
12. [Project Structure](#project-structure)
13. [Implementation Plan](#implementation-plan)

---

## Overview

The Agent Skills Framework is a modular, single-agent orchestration system that enables a single intelligent agent to possess multiple capabilities through pluggable Skill modules.

**Core Philosophy:** "一个协调器统一调度，多个 Skills 各司其职，三层上下文贯穿始终"

**Key Benefits:**
- Lower token consumption (6K-10K vs 15K-25K for Multi-Agent)
- Simplified debugging with full audit trail
- Linear token growth through progressive disclosure
- Hybrid execution: rule engine for accuracy, LLM for intelligence

---

## Architecture

### Component Relationships

```
                    ┌─────────────────────────────────────┐
                    │         Coordinator (调度中心)         │
                    │  - 初始化 Context                    │
                    │  - 调度 Planner → Executor → Synthesizer │
                    └───────────────┬─────────────────────┘
                                    │
            ┌───────────────────────┼───────────────────────┐
            │                       │                       │
            ▼                       ▼                       ▼
    ┌──────────────┐      ┌──────────────┐        ┌──────────────┐
    │   Planner    │      │   Executor   │        │ Synthesizer  │
    │  (任务规划)   │─────▶│  (Skill执行)  │───────▶│  (结果综合)   │
    └──────────────┘      └──────────────┘        └──────────────┘
            │                       │
            ▼                       ▼
    ┌──────────────┐      ┌──────────────┐
    │  Skill加载器  │      │  Skills 目录  │
    │  (自动发现)   │      │  (即插即用)   │
    └──────────────┘      └──────────────┘
                                    │
                                    ▼
                        ┌───────────────────────┐
                        │   三层上下文            │
                        │  Layer1: 用户输入层     │
                        │  Layer2: 工作记忆层     │
                        │  Layer3: 环境配置层     │
                        └───────────────────────┘
```

---

## Three-Layer Context System

### Layer Structure

```
┌─────────────────────────────────────────────────────────┐
│                    AgentContext                          │
├─────────────────────────────────────────────────────────┤
│  Layer1: 用户输入层 (user_input)                         │
│  - raw_user_input: 原始用户请求                            │
│  - parsed_intent: Planner 解析的意图                       │
│  - execution_plan: 技能执行计划                            │
│  - conversation_history: 历史对话（仅第一步使用）            │
├─────────────────────────────────────────────────────────┤
│  Layer2: 工作记忆层 (scratchpad)                          │
│  - step_results: {skill_name: {structured, text}}         │
│  - current_step: 当前执行步骤                              │
│  - failed_steps: 失败记录（用于 RePlan）                   │
│  - audit_log: 审计日志                                    │
├─────────────────────────────────────────────────────────┤
│  Layer3: 环境配置层 (environment)                         │
│  - available_skills: 可用 Skill 列表                      │
│  - token_budget: Token 预算管理                           │
│  - model_config: LLM 配置                                 │
│  - tools_registry: 工具注册表                             │
└─────────────────────────────────────────────────────────┘
```

### Permission Control

| Component | Read Layer | Write Layer |
|-----------|------------|-------------|
| Planner | L1 + L3 | L1 |
| Executor | L1 + L3 | L2 |
| Synthesizer | L1 + L2 | - |

---

## Core Components

### 1. Coordinator
**File:** `agent/coordinator.py`
- Main orchestration loop
- Initializes AgentContext
- Coordinates Planner → Executor → Synthesizer pipeline

### 2. Planner
**File:** `agent/planner.py`
- Analyzes user intent
- Generates execution plan with confidence scores
- Filters steps below 0.5 confidence threshold

### 3. Executor
**File:** `agent/executor.py`
- Executes Skills in sequence
- Implements progressive disclosure
- Handles three execution modes
- Manages error recovery with RePlanner

### 4. Synthesizer
**File:** `agent/synthesizer.py`
- Aggregates multi-step results
- Generates coherent natural language response

### 5. AgentContext
**File:** `agent/context.py`
- Three-layer context manager
- Audit logging for all operations
- Token budget tracking

---

## Data Flow & Progressive Disclosure

### Execution Flow

```
用户输入 → Coordinator → Planner (生成计划) → Executor (链式执行) → Synthesizer (综合输出)
```

### Progressive Disclosure Strategy

Each step's input = `sub_task` + `原始请求` + `压缩的前置结果`

**Compression Strategy:**
1. **Always retain:** Original user request
2. **Fully retain:** Latest step output
3. **Can truncate:** Earlier step outputs (mark as "compressed")
4. **Can discard:** Oldest absorbed steps

**Result:** Linear token growth instead of exponential

---

## Dual Execution Engine

**Principle:** Rule engine for accuracy (准), LLM for intelligence (智)

### Execution Modes

| Mode | File Required | Use Case |
|------|---------------|----------|
| executor.py | Custom Python code | Complex calculation + LLM hybrid |
| prompt.template | Template file | Pure LLM interaction |
| SKILL.md | Documentation only | Simple conversational Skill |

### Example executor.py Structure

```python
def execute(llm: LLMClient, sub_task: str, context: dict) -> dict:
    # ─── Rule Engine: Deterministic computation ───
    bmi = calculate_bmi(height, weight)
    status = check_indicator(value, ref_low, ref_high)

    # ─── LLM: Natural language generation ───
    summary = llm.invoke(f"Summarize: BMI={bmi}, status={status}")

    return {
        "structured": {"bmi": bmi, "status": status},
        "text": summary
    }
```

---

## LLM Abstraction & Token Management

### Provider Abstraction

```python
class LLMProvider(ABC):
    @abstractmethod
    def invoke(messages, model, temperature) -> LLMResponse: pass

    @abstractmethod
    def stream(messages, model, temperature) -> Iterator[StreamChunk]: pass

    @abstractmethod
    def count_tokens(text: str) -> int: pass
```

### Supported Providers
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- Ollama (local models)
- Extensible for any provider

### Token Budget Management

```python
class TokenBudget:
    total_limit: int = 100000
    warning_threshold: float = 0.8

    def consume(amount: int, source: str) -> bool
    def get_compression_ratio() -> float
```

---

## Audit Logging & Performance Monitoring

### Audit Entry

```python
@dataclass
class AuditEntry:
    timestamp: str
    layer: AuditLayer  # user_input | scratchpad | environment
    op: AuditOp        # read | write | delete | compress
    key: str
    source: str        # planner | skill:parse_report | coordinator
    value_preview: str
    execution_time_ms: float
```

### Performance Metrics

```python
class SkillMetrics:
    total_calls: int
    success_rate: float
    avg_time_ms: float
    avg_tokens: int
    last_error: str
```

---

## Error Handling & RePlan Mechanism

### Error Types

- `SkillNotFoundError`: Skill doesn't exist
- `SkillExecutionError`: Execution failed (recoverable)
- `TokenBudgetExceeded`: Token limit exceeded
- `ContextValidationError`: Context validation failed

### RePlan Actions

| Action | Description |
|--------|-------------|
| RETRY | Retry current step (temporary error) |
| SKIP | Skip current step (non-critical) |
| ALTERNATIVE | Try alternative Skill |
| ABORT | Abort execution (critical failure) |

### RePlan Decision Flow

```
Step Failed → RePlanner.analyze() → Decision → Action
```

---

## Tool System

**Principle:** Everything is a Tool

### Tool Abstraction

```python
class Tool(ABC):
    @property
    @abstractmethod
    def spec(self) -> ToolSpec: pass

    @abstractmethod
    def execute(**kwargs) -> Any: pass
```

### Example Tools
- `ReferenceRangeChecker`: Check indicator against reference range
- `BMICalculator`: Calculate BMI
- `BloodPressureClassifier`: Classify blood pressure

---

## Skill Loading & Execution

### Skill Directory Structure

```
skills/parse_report/
├── SKILL.md              # Required: Metadata + documentation
├── prompt.template       # Optional: Prompt template
├── executor.py           # Optional: Custom executor
└── schema.py             # Optional: Output data contract
```

### SKILL.md Format

```yaml
---
name: parse_report
version: 1.0.0
description: Parse health checkup report
triggers:
  - 体检报告
  - 化验单
tags:
  - 健康
  - 数据解析
tools:
  - check_reference_range
---

# Skill 说明文档...

该 Skill 用于解析体检报告...
```

### Execution Priority

1. Has `executor.py` → Use custom executor (rule + LLM hybrid)
2. Has `prompt.template` → Fill template and call LLM
3. Neither → Use SKILL.md documentation as system prompt

---

## Project Structure

```
agent-skills-exec/
├── main.py                      # Entry point
├── config.py                    # Global configuration
├── requirements.txt             # Dependencies
├── pyproject.toml              # Project metadata
│
├── agent/                       # Core Agent components
│   ├── coordinator.py          # Orchestration loop
│   ├── context.py              # Three-layer context
│   ├── planner.py              # Task planner
│   ├── executor.py             # Skill executor
│   ├── synthesizer.py          # Result synthesizer
│   ├── skill_executor.py       # Single Skill executor
│   ├── replanner.py            # Dynamic re-planner
│   ├── llm_base.py             # LLM abstraction
│   ├── llm_client.py           # Unified LLM client
│   ├── errors.py               # Error definitions
│   ├── audit.py                # Audit logging
│   ├── metrics.py              # Performance monitoring
│   ├── tools.py                # Tool system
│   ├── token_budget.py         # Token management
│   └── providers/              # LLM providers
│       ├── openai_provider.py
│       ├── anthropic_provider.py
│       └── ollama_provider.py
│
├── skills/                     # Skills directory
│   ├── parse_report/
│   ├── assess_risk/
│   └── generate_advice/
│
├── shared/                     # Shared utilities
│   ├── context_schema.py
│   └── metrics_utils.py
│
├── utils/                      # Framework utilities
│   ├── skill_loader.py
│   └── skill_registry.py
│
└── dialogue/                   # Dialogue management
    ├── manager.py
    └── protocol.py
```

---

## Implementation Plan

### Phase 1: Core Framework
- [x] Project structure initialization
- [x] LLM abstraction layer
- [x] Three-layer context system
- [x] Tool system

### Phase 2: Orchestration Components
- [x] Skill loader and registry
- [x] Planner with RePlanner
- [x] Skill executor (three modes)
- [x] Synthesizer and Coordinator

### Phase 3: Example Skills
- [x] parse_report Skill
- [x] assess_risk Skill
- [x] generate_advice Skill

### Phase 4: Enhancement Features
- [ ] Token budget management
- [ ] Performance monitoring
- [ ] Streaming output support
- [ ] CLI tools

### Phase 5: Testing & Documentation
- [ ] Unit tests
- [ ] Integration tests
- [ ] API documentation
- [ ] Usage examples

---

## Five Core Design Principles

1. **Skill Context Isolation** — User input, working memory, and environment are separated
2. **Skill Progressive Disclosure** — Each step sees only minimum necessary context
3. **Skill Structured Contracts** — TypedDict schemas between Skills
4. **Dual Execution Engine** — Rule engine for accuracy, LLM for intelligence
5. **Full-chain Auditability** — Every read/write/compress operation is logged

---

## Conclusion

The Agent Skills Framework provides a balanced abstraction level—structured orchestration without over-engineering. It's ideal for linear, dependent task flows where Multi-Agent's complexity is unnecessary.

**Key Differentiator:** Progressive disclosure ensures linear token growth while maintaining execution accuracy.

---

*Document Version: 1.0.0*
*Last Updated: 2025-02-28*
