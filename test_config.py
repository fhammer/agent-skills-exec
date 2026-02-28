#!/usr/bin/env python3
"""
测试配置文件加载
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

def test_config_loading():
    """测试配置文件加载。"""
    console.print("\n")
    console.print(Panel.fit(
        "[bold cyan]配置文件加载测试[/bold cyan]",
        border_style="cyan"
    ))
    console.print("")

    # 测试 1: 从文件加载
    console.print("[dim][1/4] 测试从文件加载配置...[/dim]")
    try:
        from config import Config
        config = Config.from_file()
        console.print(f"  ✓ 配置加载成功")
        console.print(f"    Provider: {config.llm.provider}")
        console.print(f"    Model: {config.llm.model}")
        console.print(f"    Base URL: {config.llm.base_url}")
        console.print(f"    API Key: {config.llm.api_key[:20]}...")
        console.print("")
    except Exception as e:
        console.print(f"  ✗ 加载失败: {e}")
        return

    # 测试 2: 从 profile 加载
    console.print("[dim][2/4] 测试从 profile 加载配置...[/dim]")
    try:
        # 注意: profile 需要在 config.yaml 中定义，config.local.yaml 只覆盖 API Key
        config_profile = Config.from_profile("zhipu_glm47")
        console.print(f"  ✓ Profile 加载成功")
        console.print(f"    Provider: {config_profile.llm.provider}")
        console.print(f"    Model: {config_profile.llm.model}")
        console.print(f"    Base URL: {config_profile.llm.base_url}")
        console.print("")
    except Exception as e:
        console.print(f"  ✗ Profile 加载失败: {e}")
        console.print("    提示: profiles 定义在 config.yaml 中，需要同时保留两个文件")
        console.print("")

    # 测试 3: 可用的 profiles
    console.print("[dim][3/4] 可用的 Profiles:[/dim]")
    profiles = [
        ("zhipu_glm47", "智谱 GLM-4.7"),
        ("zhipu_flash", "智谱 GLM-4-Flash"),
        ("openai_gpt4", "OpenAI GPT-4"),
        ("anthropic_claude", "Anthropic Claude"),
        ("ollama_local", "Ollama 本地模型"),
    ]
    for name, desc in profiles:
        console.print(f"  • {name}: {desc}")
    console.print("")

    # 测试 4: 配置文件位置
    console.print("[dim][4/4] 配置文件说明:[/dim]")
    console.print("  1. config.local.yaml - 本地配置（最高优先级，不提交）")
    console.print("  2. config.yaml - 项目默认配置")
    console.print("  3. 环境变量 - 覆盖文件配置")
    console.print("")

    # 使用示例
    console.print(Panel.fit(
        "[bold green]配置加载成功！[/bold green]\n\n"
        "[bold yellow]使用示例:[/bold yellow]\n\n"
        "# 从文件加载\n"
        "config = Config.from_file()\n\n"
        "# 从 profile 加载\n"
        "config = Config.from_profile(\"zhipu_glm47\")\n\n"
        "# 从环境变量加载\n"
        "config = Config.from_env()\n\n"
        "[bold yellow]配置文件优先级:[/bold yellow]\n"
        "config.local.yaml > config.yaml > 环境变量 > 默认值",
        border_style="green"
    ))
    console.print("")

if __name__ == "__main__":
    try:
        test_config_loading()
    except Exception as e:
        console.print(f"\n[red]测试出错: {e}[/red]")
        import traceback
        traceback.print_exc()
