# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Agent Skills Framework is a Python-based modular AI Agent framework featuring single-agent orchestration. It uses a "one coordinator, multiple skills, three-layer context" architecture with progressive disclosure for efficient token usage.

Key architectural concepts:
- **Coordinator**: Central orchestrator that manages the execution pipeline
- **Skills**: Pluggable modules stored in `skills/` directory, auto-discovered at runtime
- **Three-layer Context**: Layer 1 (User Input), Layer 2 (Working Memory/Scratchpad), Layer 3 (Environment Config)
- **Progressive Disclosure**: Each step only sees minimal necessary context

## Common Development Commands

### Setup and Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Or install with optional dependencies
pip install -e ".[dev]"        # Development tools
pip install -e ".[openai]"     # OpenAI support
pip install -e ".[anthropic]"  # Anthropic support
```

### Running the Framework
```bash
# Interactive mode (default)
python main.py

# Demo mode with health check example
python main.py --mode demo

# With specific provider/model
python main.py --provider anthropic --model glm-4.7
```

### Running Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_context.py

# Run with coverage
pytest --cov=.

# Run a single test
python test_config.py
python test_with_config.py
```

### Code Quality
```bash
# Format code
black .

# Type checking
mypy .

# Linting
ruff .
```

## Configuration

Configuration uses a layered approach:
1. `config.yaml` - Default configuration (checked in)
2. `config.local.yaml` - Local overrides (gitignored)
3. Environment variables - Runtime overrides
4. Command-line arguments - Immediate overrides

### Environment Variables
- `LLM_API_KEY` - API key for LLM provider
- `LLM_PROVIDER` - Provider (openai, anthropic, ollama)
- `LLM_MODEL` - Model name
- `LLM_BASE_URL` - Custom base URL

### Using Preset Profiles
```python
from config import Config

config = Config.from_profile("zhipu_glm47")  # or "openai_gpt4", "anthropic_claude", "ollama_local"
coordinator = Coordinator(config)
```

## Project Structure

```
agent-skills-exec/
├── main.py                  # Entry point with CLI
├── config.py                # Configuration dataclasses
├── config.yaml              # Default config
├── config_loader.py         # YAML config loading
├── agent/                   # Core framework components
│   ├── coordinator.py       # Main orchestrator
│   ├── context.py           # Three-layer context system
│   ├── planner.py           # Task planning
│   ├── skill_executor.py    # Skill execution engine
│   ├── synthesizer.py       # Response synthesis
│   ├── replanner.py         # Dynamic replanning
│   ├── llm_client.py        # LLM abstraction
│   ├── audit.py             # Audit logging
│   ├── tools.py             # Tool system
│   └── providers/           # LLM provider implementations
│       ├── openai_provider.py
│       ├── anthropic_provider.py
│       ├── ollama_provider.py
│       └── zhipu_provider.py
├── skills/                  # Skill modules (auto-discovered)
│   ├── parse_report/        # Report parsing skill
│   │   ├── SKILL.md         # Skill metadata
│   │   ├── executor.py        # Execution logic
│   │   └── schema.py          # Output schema
│   ├── assess_risk/         # Risk assessment skill
│   └── generate_advice/     # Advice generation skill
├── utils/                   # Utilities
│   └── skill_loader.py      # Skill auto-discovery
├── api/                     # FastAPI REST API
│   ├── main.py              # API entry point
│   └── routers/             # API routes
├── tests/                   # Test suite
└── docs/                    # Documentation
```

## Creating a New Skill

Skills are auto-discovered from the `skills/` directory. Each skill follows this structure:

```
skills/my_skill/
├── SKILL.md          # Required: Metadata and documentation
├── executor.py       # Optional: Custom execution logic
├── prompt.template # Optional: LLM prompt template
└── schema.py         # Optional: Output data schema
```

Execution priority:
1. `executor.py` - Custom Python code (rule engine + LLM)
2. `prompt.template` - LLM prompt template
3. `SKILL.md` - Documentation as skill (LLM with doc as system prompt)

### Example SKILL.md
```yaml
---
name: calculator
version: 1.0.0
description: Math calculator supporting basic operations
triggers:
  - calculate
  - compute
tags:
  - math
---

# Calculator Skill

Performs mathematical calculations...
```

## Key Architectural Patterns

### Three-Layer Context System
The context system in `agent/context.py` separates data into three layers:
- **Layer 1 (User Input)**: Raw user input, conversation history, execution plan
- **Layer 2 (Working Memory/Scratchpad)**: Intermediate results from skill execution
- **Layer 3 (Environment)**: Available skills, token budget, tool registry

### Progressive Disclosure
Each component only receives the minimal context it needs:
- Planner sees available skills and user intent
- Executor sees only the current step's context
- Synthesizer sees aggregated results

### Dual Execution Engine
- **Rule Engine**: For deterministic, verifiable operations
- **LLM**: For natural language understanding and generation

## Common Development Workflows

### Testing a Skill
```python
from config import Config
from agent.coordinator import Coordinator

config = Config.from_file()
coordinator = Coordinator(config)

result = coordinator.process("你的测试请求")
print(result["final_response"])
```

### Debugging with Audit Log
```python
# Enable audit logging
config.execution.enable_audit_log = True
coordinator = Coordinator(config)
result = coordinator.process("请求")

# View audit trail
for entry in coordinator.get_audit_trail():
    print(entry)
```

### Checking Token Usage
```python
budget_summary = coordinator.llm_client.budget.get_summary()
print(f"Used: {budget_summary['used']}/{budget_summary['total_limit']}")
```
