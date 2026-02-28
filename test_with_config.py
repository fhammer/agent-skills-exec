#!/usr/bin/env python3
"""
测试使用配置文件加载器运行框架
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

def test_with_config():
    """使用配置文件测试框架。"""
    console.print("\n")
    console.print(Panel.fit(
        "[bold cyan]使用配置文件测试框架[/bold cyan]",
        border_style="cyan"
    ))
    console.print("")

    # 测试 1: 从文件加载配置
    console.print("[dim][1/3] 从配置文件加载...[/dim]")
    try:
        from config import Config
        from agent.coordinator import Coordinator

        config = Config.from_file()
        console.print(f"  ✓ 配置加载成功")
        console.print(f"    Provider: {config.llm.provider}")
        console.print(f"    Model: {config.llm.model}")
        console.print(f"    Base URL: {config.llm.base_url}")
        console.print("")
    except Exception as e:
        console.print(f"  ✗ 加载失败: {e}")
        import traceback
        console.print(traceback.format_exc())
        return

    # 测试 2: 初始化 Coordinator
    console.print("[dim][2/3] 初始化 Coordinator...[/dim]")
    try:
        coordinator = Coordinator(config)
        console.print(f"  ✓ Coordinator 初始化成功")
        console.print(f"    已加载 {len(coordinator.skill_registry.get_all_skills())} 个 Skills")
        console.print("")
    except Exception as e:
        console.print(f"  ✗ 初始化失败: {e}")
        import traceback
        console.print(traceback.format_exc())
        return

    # 测试 3: 测试 LLM 连接
    console.print("[dim][3/3] 测试 LLM 连接...[/dim]")
    try:
        from agent.llm_client import LLMClient
        from agent.providers.anthropic_provider import AnthropicProvider
        from agent.token_budget import TokenBudget

        provider = AnthropicProvider(
            api_key=config.llm.api_key,
            base_url=config.llm.base_url,
            default_model=config.llm.model
        )
        budget = TokenBudget(total_limit=config.budget.total_limit)
        llm = LLMClient(provider, budget)

        response = llm.invoke("你好，请用一句话介绍你自己。", check_budget=False)
        console.print(f"  ✓ LLM 连接成功!")
        console.print(f"    回复: {response[:60]}...")
        console.print("")
    except Exception as e:
        console.print(f"  ✗ LLM 连接失败: {e}")
        import traceback
        console.print(traceback.format_exc())
        return

    # 测试结论
    console.print(Panel.fit(
        "[bold green]✓ 配置文件测试完成！[/bold green]\n\n"
        "已验证功能:\n"
        "  ✓ 从 config.local.yaml 加载配置\n"
        "  ✓ Coordinator 初始化\n"
        "  ✓ LLM 连接和调用\n\n"
        "[bold yellow]配置文件优先级:[/bold yellow]\n"
        "1. config.local.yaml (本地配置)\n"
        "2. config.yaml (项目默认配置)\n"
        "3. 环境变量 (覆盖文件配置)\n\n"
        "[bold yellow]使用方法:[/bold yellow]\n"
        "config = Config.from_file()\n"
        "coordinator = Coordinator(config)",
        border_style="green"
    ))
    console.print("")

if __name__ == "__main__":
    try:
        test_with_config()
    except Exception as e:
        console.print(f"\n[red]测试出错: {e}[/red]")
        import traceback
        traceback.print_exc()
