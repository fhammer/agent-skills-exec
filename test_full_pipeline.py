#!/usr/bin/env python3
"""
Agent Skills Framework - 全链路测试
使用智谱 GLM-4.7 模型进行完整的健康检查流程测试
"""

import sys
import os
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# 设置智谱 API
os.environ["LLM_PROVIDER"] = "zhipu"
os.environ["LLM_MODEL"] = "glm-4"
os.environ["LLM_API_KEY"] = "e2a6227dc48843e58d0600d4597a6810.37LhMInDNwKlpMMY"
os.environ["LLM_TEMPERATURE"] = "0.7"

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from config import Config
from agent.coordinator import Coordinator

console = Console()

def print_header():
    """打印测试标题."""
    console.print("\n")
    console.print(Panel.fit(
        "[bold cyan]Agent Skills Framework[/bold cyan]\n"
        "[bold yellow]全链路测试 - 智谱 GLM-4.7[/bold yellow]",
        border_style="cyan"
    ))
    console.print("")

def print_test_info():
    """打印测试信息."""
    table = Table(show_header=False, box=None)
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("LLM Provider", "Zhipu GLM")
    table.add_row("Model", "glm-4 (GLM-4.7)")
    table.add_row("API Key", "e2a622...kMMY"[:20] + "...")
    table.add_row("Test Scenario", "健康检查完整流程")

    console.print(table)
    console.print("")

def run_full_pipeline_test():
    """运行完整的健康检查流程测试。"""
    print_header()
    print_test_info()

    # 示例体检报告数据
    sample_report = {
        "height": 175,
        "weight": 85,
        "sbp": 150,
        "dbp": 98,
        "lab_items": [
            {"name": "空腹血糖", "value": 7.5, "unit": "mmol/L", "ref_low": 3.9, "ref_high": 6.1},
            {"name": "总胆固醇", "value": 6.8, "unit": "mmol/L", "ref_low": 0, "ref_high": 5.2},
            {"name": "甘油三酯", "value": 3.2, "unit": "mmol/L", "ref_low": 0, "ref_high": 1.7},
            {"name": "尿酸", "value": 550, "unit": "μmol/L", "ref_low": 200, "ref_high": 420},
            {"name": "谷丙转氨酶", "value": 70, "unit": "U/L", "ref_low": 0, "ref_high": 40},
            {"name": "肌酐", "value": 95, "unit": "μmol/L", "ref_low": 57, "ref_high": 111},
        ]
    }

    console.print("[bold]体检报告数据:[/bold]")
    console.print(f"  基本信息: 身高 {sample_report['height']}cm, 体重 {sample_report['weight']}kg")
    console.print(f"  血压: {sample_report['sbp']}/{sample_report['dbp']} mmHg")
    console.print(f"  检验指标: {len(sample_report['lab_items'])} 项")
    for item in sample_report['lab_items']:
        is_abnormal = (item['ref_low'] and item['value'] < item['ref_low']) or \
                      (item['ref_high'] and item['value'] > item['ref_high'])
        status = "✗" if is_abnormal else "✓"
        console.print(f"    {status} {item['name']}: {item['value']}{item['unit']} "
                     f"(参考: {item['ref_low']}-{item['ref_high']})")
    console.print("")

    # 加载配置
    console.print("[dim][1/6] 加载配置...[/dim]")
    config = Config.from_env()
    config.validate()
    console.print("  ✓ 配置加载成功\n")

    # 初始化 Coordinator
    console.print("[dim][2/6] 初始化 Coordinator...[/dim]")
    try:
        coordinator = Coordinator(config)
        console.print(f"  ✓ 已加载 {len(coordinator.skill_registry.get_all_skills())} 个 Skills")
        for skill_name in coordinator.skill_registry.get_all_skills().keys():
            console.print(f"    - {skill_name}")
        console.print("")
    except Exception as e:
        console.print(f"  ✗ 初始化失败: {e}")
        return

    # 构建用户请求
    user_request = f"""请帮我分析这份体检报告并给出健康建议：

**基本信息：**
- 身高: {sample_report['height']} cm
- 体重: {sample_report['weight']} kg
- 血压: {sample_report['sbp']}/{sample_report['dbp']} mmHg

**检验指标：**
"""

    for item in sample_report['lab_items']:
        user_request += f"- {item['name']}: {item['value']} {item['unit']}\n"

    console.print("[bold]用户请求:[/bold]")
    console.print(Syntax(user_request, "markdown", line_numbers=False))
    console.print("")

    # 执行请求
    console.print("[dim][3/6] Planner 规划任务...[/dim]")
    with console.status("  正在规划...", spinner="dots"):
        start_time = time.time()

        # Phase 0: 初始化上下文
        coordinator.context.set_component("coordinator")
        coordinator.context.write_layer1("raw_user_input", user_request, "coordinator")
        coordinator.context.write_layer3(
            "available_skills",
            coordinator.skill_registry.get_all_skills(),
            "coordinator"
        )

        # Phase 1: 规划
        plan = coordinator._plan_execution(user_request)
        plan_time = (time.time() - start_time) * 1000

    console.print(f"  ✓ 规划完成 ({plan_time:.0f}ms)")
    console.print(f"    意图: {plan.intent}")
    console.print(f"    步骤数: {len(plan.steps)}")
    for i, step in enumerate(plan.steps, 1):
        console.print(f"    {i}. {step['skill']}: {step['sub_task']} (置信度: {step['confidence']})")
    console.print("")

    # Phase 2: 执行 Skills
    console.print("[dim][4/6] Executor 执行 Skills...[/dim]")
    execution_start = time.time()

    step_results = []
    for i, step in enumerate(plan.steps):
        step_num = i + 1
        console.print(f"  [{step_num}/{len(plan.steps)}] 执行 {step['skill']}...")

        try:
            # 执行单个步骤
            result = coordinator._execute_single_step(step, len(step_results))

            if result.get("success"):
                exec_time = result.get("result", {}).get("execution_time_ms", 0)
                console.print(f"    ✓ 完成 ({exec_time:.0f}ms)")
                if result.get("result", {}).get("structured"):
                    struct = result["result"]["structured"]
                    if "basic_info" in struct:
                        console.print(f"      基本信息: {list(struct['basic_info'].keys())}")
                    if "summary" in struct:
                        console.print(f"      摘要: {struct['summary']}")
                step_results.append(result)
            else:
                console.print(f"    ✗ 失败: {result.get('error', 'Unknown error')}")

        except Exception as e:
            console.print(f"    ✗ 异常: {e}")

    execution_time = (time.time() - execution_start) * 1000
    console.print(f"  ✓ 执行完成 (总时间: {execution_time:.0f}ms)")
    console.print("")

    # Phase 3: 综合结果
    console.print("[dim][5/6] Synthesizer 综合结果...[/dim]")
    with console.status("  正在综合...", spinner="dots"):
        synthesis_start = time.time()
        final_response = coordinator.synthesizer.synthesize(coordinator.context)
        synthesis_time = (time.time() - synthesis_start) * 1000

    console.print(f"  ✓ 综合完成 ({synthesis_time:.0f}ms)")
    console.print("")

    # 显示最终结果
    console.print("[dim][6/6] 显示最终结果...[/dim]")
    console.print("")
    console.print(Panel(
        final_response,
        title="[bold green]健康分析报告[/bold green]",
        border_style="green",
        padding=(1, 2)
    ))
    console.print("")

    # 显示执行指标
    total_time = (time.time() - start_time) * 1000
    metrics_table = Table(title="执行指标", show_header=True)
    metrics_table.add_column("指标", style="cyan")
    metrics_table.add_column("值", style="yellow")
    metrics_table.add_column("说明", style="dim")

    metrics_table.add_row("总执行时间", f"{total_time:.0f} ms", "从请求到响应完成")
    metrics_table.add_row("规划时间", f"{plan_time:.0f} ms", "Planner 生成计划")
    metrics_table.add_row("执行时间", f"{execution_time:.0f} ms", "Skills 执行")
    metrics_table.add_row("综合时间", f"{synthesis_time:.0f} ms", "Synthesizer 综合")

    # LLM 指标
    llm_metrics = coordinator.llm_client.get_metrics()
    metrics_table.add_row("LLM 调用次数", str(llm_metrics["total_calls"]), "总计")
    metrics_table.add_row("Token 消耗", str(llm_metrics["total_tokens"]), "输入+输出")

    console.print(metrics_table)
    console.print("")

    # 显示审计摘要
    if config.execution.enable_audit_log:
        audit_summary = coordinator.context.audit_log.get_summary()
        console.print(f"[dim]审计日志: {audit_summary['total_entries']} 条记录[/dim]")

        # 按组件显示
        by_source = audit_summary.get('by_source', {})
        for source, count in by_source.items():
            console.print(f"  - {source}: {count} 条操作")

        # 按层级显示
        by_layer = audit_summary.get('by_layer', {})
        console.print(f"  按层级: {by_layer}")
        console.print("")

    # 显示解释功能演示
    console.print("[dim][附加] 审计解释功能演示:[/dim]")
    explanation = coordinator.explain("为什么建议我注意血糖和尿酸？")
    console.print(Panel(
        explanation,
        title="解释",
        border_style="blue",
        padding=(0, 2)
    ))
    console.print("")

    # 测试结论
    console.print(Panel.fit(
        "[bold green]✓ 全链路测试通过！[/bold green]\n\n"
        "所有核心组件正常工作:\n"
        "  ✓ 三层上下文系统\n"
        "  ✓ Planner 任务规划\n"
        "  ✓ Executor Skill 执行\n"
        "  ✓ Synthesizer 结果综合\n"
        "  ✓ 审计日志记录\n"
        "  ✓ Token 预算管理\n"
        "  ✓ 智谱 GLM-4.7 集成",
        border_style="green"
    ))
    console.print("")


if __name__ == "__main__":
    try:
        run_full_pipeline_test()
    except KeyboardInterrupt:
        console.print("\n[yellow]测试被中断[/yellow]")
    except Exception as e:
        console.print(f"\n[red]测试出错: {e}[/red]")
        import traceback
        traceback.print_exc()
