"""Main entry point for Agent Skills Framework."""

import sys
import os
from pathlib import Path
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from config import Config
from agent.coordinator import Coordinator

console = Console()


def print_banner():
    """Print application banner."""
    banner = """
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║         [bold cyan]Agent Skills Framework[/bold cyan]                      ║
║                                                          ║
║         模块化 Agent 能力框架 - 单智能体编排              ║
║                                                          ║
║   一个协调器统一调度，多个 Skills 各司其职               ║
║   三层上下文贯穿始终                                      ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
"""
    console.print(Panel.fit(banner, border_style="cyan"))


def print_metrics(metrics: dict):
    """Print execution metrics."""
    table = Table(title="执行指标", show_header=False)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("执行时间", f"{metrics.get('execution_time_ms', 0):.0f} ms")
    table.add_row("总请求数", str(metrics.get('total_requests', 0)))
    table.add_row("执行 Skills", str(metrics.get('total_skills_executed', 0)))

    llm_metrics = metrics.get('llm_metrics', {})
    if llm_metrics:
        table.add_row("LLM 调用次数", str(llm_metrics.get('total_calls', 0)))
        table.add_row("Token 消耗", str(llm_metrics.get('total_tokens', 0)))

    budget = metrics.get('token_budget', {})
    if budget:
        used = budget.get('used', 0)
        total = budget.get('total_limit', 0)
        ratio = budget.get('usage_ratio', 0)
        table.add_row("Token 预算", f"{used}/{total} ({ratio:.1%})")

    console.print(table)


def interactive_mode(config: Config):
    """Run interactive mode."""
    print_banner()

    # Initialize coordinator
    try:
        coordinator = Coordinator(config)
    except Exception as e:
        console.print(f"[red]初始化失败: {e}[/red]")
        console.print("\n[yellow]提示: 请确保已设置 LLM_API_KEY 环境变量[/yellow]")
        console.print("示例: export LLM_API_KEY=your-api-key-here")
        return

    console.print("[green]✓ 系统初始化成功[/green]")
    console.print(f"[dim]已加载 {len(coordinator.skill_registry.get_all_skills())} 个 Skills[/dim]\n")

    console.print("[dim]可用命令:[/dim]")
    console.print("  直接输入问题 - 发送给 AI")
    console.print("  /metrics        - 查看性能指标")
    console.print("  /audit          - 查看审计日志")
    console.print("  /explain <问题>  - 解释某个决策")
    console.print("  /reset          - 重置会话")
    console.print("  /quit 或 /exit  - 退出\n")

    while True:
        try:
            user_input = console.input("\n[bold green]你:[/bold green] ").strip()

            if not user_input:
                continue

            # Handle commands
            if user_input.lower() in ["/quit", "/exit"]:
                console.print("[yellow]再见![/yellow]")
                break

            if user_input == "/metrics":
                print_metrics(coordinator._get_execution_metrics(0))
                continue

            if user_input == "/audit":
                audit_trail = coordinator.get_audit_trail()
                if audit_trail:
                    console.print(f"\n[dim]共 {len(audit_trail)} 条审计记录[/dim]")
                    for entry in audit_trail[-10:]:  # Last 10
                        console.print(f"  [{entry['timestamp']}] {entry['source']}: {entry['op']} {entry['layer']}.{entry['key']}")
                else:
                    console.print("[dim]没有审计记录[/dim]")
                continue

            if user_input.startswith("/explain "):
                question = user_input[9:].strip()
                explanation = coordinator.explain(question)
                console.print(Panel(explanation, title="解释", border_style="blue"))
                continue

            if user_input == "/reset":
                coordinator.reset()
                console.print("[green]✓ 会话已重置[/green]")
                continue

            # Process user request
            with console.status("[bold cyan]处理中...", spinner="dots"):
                result = coordinator.process(user_input)

            # Display response
            if result.get("success"):
                console.print(Panel(
                    result["final_response"],
                    title="[bold blue]Agent[/bold blue]",
                    border_style="blue"
                ))

                # Show metrics if enabled
                if config.execution.enable_metrics:
                    console.print(f"\n[dim]执行时间: {result['metrics']['execution_time_ms']:.0f}ms[/dim]")
            else:
                console.print(f"[red]错误: {result.get('final_response', '未知错误')}[/red]")

        except KeyboardInterrupt:
            console.print("\n[yellow]使用 /quit 退出[/yellow]")
        except Exception as e:
            console.print(f"[red]错误: {e}[/red]")


def demo_mode(config: Config):
    """Run demo mode with health check example."""
    print_banner()

    console.print("[cyan]运行健康检查演示...[/cyan]\n")

    # Sample health report data
    sample_report = {
        "height": 175,
        "weight": 82,
        "sbp": 145,
        "dbp": 95,
        "lab_items": [
            {"name": "空腹血糖", "value": 7.2, "unit": "mmol/L", "ref_low": 3.9, "ref_high": 6.1},
            {"name": "总胆固醇", "value": 6.5, "unit": "mmol/L", "ref_low": 0, "ref_high": 5.2},
            {"name": "甘油三酯", "value": 2.8, "unit": "mmol/L", "ref_low": 0, "ref_high": 1.7},
            {"name": "尿酸", "value": 520, "unit": "μmol/L", "ref_low": 200, "ref_high": 420},
            {"name": "谷丙转氨酶", "value": 65, "unit": "U/L", "ref_low": 0, "ref_high": 40},
        ]
    }

    console.print("[dim]体检报告数据:[/dim]")
    console.print(f"  身高: {sample_report['height']} cm, 体重: {sample_report['weight']} kg")
    console.print(f"  血压: {sample_report['sbp']}/{sample_report['dbp']} mmHg")
    console.print(f"  检验指标: {len(sample_report['lab_items'])} 项\n")

    # Initialize coordinator
    try:
        coordinator = Coordinator(config)
    except Exception as e:
        console.print(f"[red]初始化失败: {e}[/red]")
        return

    # Process request with embedded report data
    request = f"""请帮我分析这份体检报告并给出建议：

身高: {sample_report['height']}cm, 体重: {sample_report['weight']}kg
血压: {sample_report['sbp']}/{sample_report['dbp']}mmHg
空腹血糖: {sample_report['lab_items'][0]['value']}{sample_report['lab_items'][0]['unit']}
总胆固醇: {sample_report['lab_items'][1]['value']}{sample_report['lab_items'][1]['unit']}
甘油三酯: {sample_report['lab_items'][2]['value']}{sample_report['lab_items'][2]['unit']}
尿酸: {sample_report['lab_items'][3]['value']}{sample_report['lab_items'][3]['unit']}
谷丙转氨酶: {sample_report['lab_items'][4]['value']}{sample_report['lab_items'][4]['unit']}
"""

    with console.status("[bold cyan]分析中...", spinner="dots"):
        result = coordinator.process(request)

    # Display response
    if result.get("success"):
        console.print(Panel(
            result["final_response"],
            title="[bold blue]健康分析报告[/bold blue]",
            border_style="blue"
        ))

        # Show execution plan
        if "plan" in result:
            console.print("\n[bold cyan]执行计划:[/bold cyan]")
            for i, step in enumerate(result["plan"]["steps"], 1):
                console.print(f"  {i}. {step['skill']}: {step['sub_task']} (置信度: {step['confidence']})")

        # Show metrics
        console.print("\n")
        print_metrics(result["metrics"])

        # Show audit summary
        if config.execution.enable_audit_log:
            audit_summary = coordinator.context.audit_log.get_summary()
            console.print(f"\n[dim]审计日志: {audit_summary['total_entries']} 条记录[/dim]")
    else:
        console.print(f"[red]分析失败: {result.get('final_response')}[/red]")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Agent Skills Framework")
    parser.add_argument(
        "--mode",
        choices=["interactive", "demo"],
        default="interactive",
        help="运行模式"
    )
    parser.add_argument(
        "--provider",
        choices=["openai", "anthropic", "ollama"],
        default=None,
        help="LLM 提供商"
    )
    parser.add_argument(
        "--model",
        default=None,
        help="模型名称"
    )
    args = parser.parse_args()

    # Load configuration
    config = Config.from_env()

    # Override with command line args
    if args.provider:
        config.llm.provider = args.provider
    if args.model:
        config.llm.model = args.model

    # Validate configuration
    try:
        config.validate()
    except ValueError as e:
        console.print(f"[red]配置错误: {e}[/red]")
        console.print("\n[yellow]请设置 LLM_API_KEY 环境变量[/yellow]")
        console.print("示例:")
        console.print("  export LLM_API_KEY=sk-...")
        console.print("  python main.py --demo")
        return

    # Run in selected mode
    if args.mode == "demo":
        demo_mode(config)
    else:
        interactive_mode(config)


def cli():
    """CLI entry point."""
    main()


if __name__ == "__main__":
    main()
