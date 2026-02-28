#!/usr/bin/env python3
"""
Agent Skills Framework - 全链路测试 (使用 glm-4-flash)
"""

import sys
import os
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# 设置智谱 API - 使用 glm-4-flash 模型
os.environ["LLM_PROVIDER"] = "zhipu"
os.environ["LLM_MODEL"] = "glm-4-flash"
os.environ["LLM_API_KEY"] = "e2a6227dc48843e58d0600d4597a6810.37LhMInDNwKlpMMY"
os.environ["LLM_TEMPERATURE"] = "0.7"

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax

# 直接导入而不是通过 config
from config import Config
from agent.llm_client import LLMClient
from agent.providers.zhipu_provider import ZhipuProvider

console = Console()

def test_llm_connection():
    """测试 LLM 连接。"""
    console.print("\n")
    console.print(Panel.fit(
        "[bold cyan]Agent Skills Framework[/bold cyan]\n"
        "[bold yellow]全链路测试 - 智谱 GLM-4-Flash[/bold yellow]",
        border_style="cyan"
    ))
    console.print("")

    console.print("[bold]步骤 1: 测试 LLM 连接...[/bold]")

    # 创建 provider
    provider = ZhipuProvider(
        api_key="e2a6227dc48843e58d0600d4597a6810.37LhMInDNwKlpMMY",
        default_model="glm-4-flash"
    )

    # 创建 LLM 客户端
    from agent.token_budget import TokenBudget
    budget = TokenBudget(total_limit=50000)
    llm = LLMClient(provider, budget)

    # 测试调用
    test_prompt = "你好，请用一句话介绍你自己。"

    console.print(f"  发送测试提示: {test_prompt}")

    try:
        response = llm.invoke(test_prompt, check_budget=False)
        console.print(f"  ✓ 连接成功!")
        console.print(f"  模型回复: {response}")
        console.print(f"  Token 使用: {llm.get_metrics()}")
        console.print("")
        return llm
    except Exception as e:
        console.print(f"  ✗ 连接失败: {e}")
        return None


def test_planner(llm):
    """测试 Planner。"""
    console.print("[bold]步骤 2: 测试 Planner...[/bold]")

    from agent.planner import Planner
    from utils.skill_loader import SkillLoader

    # 加载 Skills
    loader = SkillLoader("skills")
    skills = loader.discover()

    console.print(f"  已加载 {len(skills)} 个 Skills")

    # 创建 Planner
    planner = Planner(llm, confidence_threshold=0.5)

    # 测试规划
    user_input = "请帮我分析体检报告并给出健康建议"

    console.print(f"  用户输入: {user_input}")
    console.print("  正在生成计划...")

    try:
        # 使用较小的上下文来避免 Token 问题
        plan = planner.generate_plan(user_input, skills, [])

        console.print(f"  ✓ 规划成功!")
        console.print(f"  意图: {plan.intent}")
        console.print(f"  步骤:")

        for i, step in enumerate(plan.steps, 1):
            console.print(f"    {i}. {step['skill']}: {step['sub_task']} (置信度: {step['confidence']})")

        console.print("")
        return plan
    except Exception as e:
        console.print(f"  ✗ 规划失败: {e}")
        return None


def main():
    """主测试函数。"""
    # 测试 LLM 连接
    llm = test_llm_connection()
    if not llm:
        console.print("\n[yellow]LLM 连接测试失败，无法继续测试[/yellow]")
        console.print("请检查:")
        console.print("  1. API Key 是否正确")
        console.print("  2. 是否有 glm-4-flash 模型的额度")
        return

    # 测试 Planner
    plan = test_planner(llm)
    if not plan:
        console.print("\n[yellow]Planner 测试失败[/yellow]")
        return

    # 测试完成
    console.print(Panel.fit(
        "[bold green]✓ 智谱 GLM-4-Flash 测试完成！[/bold green]\n\n"
        "框架核心组件验证通过:\n"
        "  ✓ LLM 连接 (glm-4-flash)\n"
        "  ✓ Planner 规划\n"
        "  ✓ Skill 加载\n\n"
        "[bold yellow]下一步:[/bold yellow]\n"
        "  框架已就绪，可以运行完整流程测试！",
        border_style="green"
    ))
    console.print("")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        console.print(f"\n[red]测试出错: {e}[/red]")
        import traceback
        traceback.print_exc()
