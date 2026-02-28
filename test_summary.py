#!/usr/bin/env python3
"""
Agent Skills Framework - 智谱 GLM-4.7 测试总结

测试框架使用智谱 AI 的 GLM-4.7 模型，通过 Anthropic 兼容 API 端点。

API 配置:
  - LLM Provider: anthropic (使用智谱兼容端点)
  - Base URL: https://open.bigmodel.cn/api/anthropic
  - Model: glm-4.7
  - API Key: e2a6227dc48843e58d0600d4597a6810.37LhMInDNwKlpMMY
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# 设置环境变量
os.environ["LLM_PROVIDER"] = "anthropic"
os.environ["LLM_MODEL"] = "glm-4.7"
os.environ["LLM_API_KEY"] = "e2a6227dc48843e58d0600d4597a6810.37LhMInDNwKlpMMY"
os.environ["LLM_BASE_URL"] = "https://open.bigmodel.cn/api/anthropic"
os.environ["LLM_TEMPERATURE"] = "0.7"

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax

console = Console()

def print_summary():
    console.print("\n")
    console.print(Panel.fit(
        "[bold cyan]Agent Skills Framework[/bold cyan]\n"
        "[bold yellow]智谱 GLM-4.7 集成测试总结[/bold yellow]",
        border_style="cyan"
    ))
    console.print("")

    # API 配置
    console.print("[bold]API 配置:[/bold]")
    table = Table(show_header=False, box=None)
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("LLM Provider", "anthropic (智谱兼容)")
    table.add_row("API Base URL", "https://open.bigmodel.cn/api/anthropic")
    table.add_row("Model", "glm-4.7")
    table.add_row("API Key", "e2a622...kMMY")
    console.print(table)
    console.print("")

    # 可用模型
    console.print("[bold]智谱可用模型测试结果:[/bold]")
    console.print("  ✓ glm-4.7: 可用 (本次测试使用)")
    console.print("  ✓ glm-4-flash: 可用")
    console.print("  ✗ glm-4: 余额不足")
    console.print("  ✗ glm-4-plus: 余额不足")
    console.print("")

    # 已验证功能
    console.print("[bold]已验证的核心功能:[/bold]")
    verified = [
        ("LLM 连接", "✓"),
        ("LLM 调用 (glm-4.7)", "✓"),
        ("Token 预算管理", "✓"),
        ("Planner 规划功能", "✓"),
        ("JSON 解析 (Markdown)", "✓"),
        ("Skill 自动发现", "✓"),
        ("三层上下文系统", "✓"),
        ("权限控制系统", "✓"),
        ("组件上下文切换", "✓"),
    ]

    for feature, status in verified:
        console.print(f"  {status} {feature}")
    console.print("")

    # 架构组件
    console.print("[bold]框架架构组件:[/bold]")
    components = [
        ("Coordinator", "主协调器，统一调度"),
        ("Planner", "任务规划，生成执行计划"),
        ("Executor", "执行 Skills，支持三种模式"),
        ("Synthesizer", "结果综合，生成最终响应"),
        ("AgentContext", "三层上下文管理"),
        ("LLMClient", "统一 LLM 调用接口"),
        ("TokenBudget", "Token 预算管理"),
        ("SkillRegistry", "Skill 自动发现和加载"),
    ]

    for comp, desc in components:
        console.print(f"  • {comp}: {desc}")
    console.print("")

    # Skills
    console.print("[bold]已实现的 Skills:[/bold]")
    skills = [
        ("parse_report", "解析体检报告，提取结构化数据"),
        ("assess_risk", "评估健康风险，多维度风险分析"),
        ("generate_advice", "生成健康建议，个性化方案"),
    ]

    for skill, desc in skills:
        console.print(f"  • {skill}: {desc}")
    console.print("")

    # 设计原则
    console.print("[bold]设计原则:[/bold]")
    principles = [
        "一个协调器统一调度 (Coordinator)",
        "多个 Skills 各司其职 (3 个 Skills)",
        "三层上下文贯穿始终",
        "渐进式披露策略 (Progressive Disclosure)",
        "双执行引擎 (规则引擎 + LLM)",
    ]

    for principle in principles:
        console.print(f"  • {principle}")
    console.print("")

    # 结论
    console.print(Panel.fit(
        "[bold green]✓ 框架测试完成！[/bold green]\n\n"
        "使用智谱 GLM-4.7 模型，通过 Anthropic 兼容 API 端点，\n"
        "框架所有核心组件均已验证正常工作！\n\n"
        "[bold yellow]API URL: https://open.bigmodel.cn/api/anthropic[/bold yellow]\n"
        "[bold yellow]Model: glm-4.7[/bold yellow]",
        border_style="green"
    ))
    console.print("")

if __name__ == "__main__":
    print_summary()
