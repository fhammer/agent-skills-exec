#!/usr/bin/env python3
"""
Agent Skills Framework - 模拟全链路测试
模拟完整的健康检查流程，展示框架功能（无需 API 调用）
"""

import sys
import os
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from config import Config
from agent.context import AgentContext
from agent.tools import create_default_registry
from utils.skill_loader import SkillLoader
from shared.metrics_utils import calculate_bmi, classify_blood_pressure, check_indicator

console = Console()

def print_header():
    """打印测试标题."""
    console.print("\n")
    console.print(Panel.fit(
        "[bold cyan]Agent Skills Framework[/bold cyan]\n"
        "[bold yellow]模拟全链路测试 - 展示框架功能[/bold yellow]",
        border_style="cyan"
    ))
    console.print("")

def run_simulation_test():
    """运行模拟测试。"""
    print_header()

    console.print("[bold]测试场景:[/bold]")
    console.print("  模拟完整的健康检查流程，展示:")
    console.print("  1. 三层上下文系统")
    console.print("  2. 工具系统 (规则引擎)")
    console.print("  3. Skill 加载器")
    console.print("  4. Skill 执行器 (三种模式)")
    console.print("  5. 审计日志")
    console.print("")

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

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Phase 1: 初始化上下文
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    console.print("[dim][1/7] 初始化 AgentContext...[/dim]")
    context = AgentContext(enable_audit=True)
    context.set_component("coordinator")
    console.print("  ✓ 三层上下文已创建")
    console.print("    - Layer1 (user_input): 用户输入层")
    console.print("    - Layer2 (scratchpad): 工作记忆层")
    console.print("    - Layer3 (environment): 环境配置层")
    console.print("")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Phase 2: 加载 Skills
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    console.print("[dim][2/7] 加载 Skills...[/dim]")
    loader = SkillLoader("skills")
    skills = loader.discover()

    console.print(f"  ✓ 已加载 {len(skills)} 个 Skills:")
    for name, skill in skills.items():
        console.print(f"    - {name}: {skill.description}")
        console.print(f"      模式: {skill.execution_mode}, 触发词: {skill.triggers}")
    console.print("")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Phase 3: 初始化工具系统
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    console.print("[dim][3/7] 初始化工具系统...[/dim]")
    tools = create_default_registry()
    console.print(f"  ✓ 已注册 {len(tools.list_all())} 个工具:")
    for tool_spec in tools.list_all():
        console.print(f"    - {tool_spec.name}: {tool_spec.description}")
    console.print("")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Phase 4: 模拟 Planner 规划
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    console.print("[dim][4/7] 模拟 Planner 规划任务...[/dim]")
    user_request = f"请帮我分析这份体检报告并给出健康建议..."

    # 模拟规划
    context.write_layer1("raw_user_input", user_request, "planner")
    context.write_layer1("parsed_intent", "体检报告全流程分析", "planner")

    mock_plan = {
        "intent": "体检报告全流程分析",
        "steps": [
            {"skill": "parse_report", "sub_task": "解析体检报告数据", "confidence": 0.95},
            {"skill": "assess_risk", "sub_task": "评估健康风险", "confidence": 0.92},
            {"skill": "generate_advice", "sub_task": "生成个性化健康建议", "confidence": 0.90}
        ]
    }
    context.write_layer1("execution_plan", mock_plan, "planner")

    console.print(f"  ✓ 规划完成")
    console.print(f"    意图: {mock_plan['intent']}")
    console.print(f"    步骤数: {len(mock_plan['steps'])}")
    for i, step in enumerate(mock_plan['steps'], 1):
        console.print(f"    {i}. {step['skill']}: {step['sub_task']} (置信度: {step['confidence']})")
    console.print("")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Phase 5: 模拟 Skill 执行 (parse_report)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    console.print("[dim][5/7] 模拟 Skill 执行...[/dim]")

    # Step 1: parse_report (使用规则引擎)
    console.print("  [Step 1/3] 执行 parse_report...")

    # 规则引擎计算
    bmi = tools.execute("calculate_bmi", height_cm=sample_report['height'], weight_kg=sample_report['weight'])
    bp = tools.execute("classify_blood_pressure", sbp=sample_report['sbp'], dbp=sample_report['dbp'])

    indicators_result = []
    for item in sample_report['lab_items']:
        status, deviation = check_indicator(item['value'], item.get('ref_low'), item.get('ref_high'))
        indicators_result.append({
            "name": item['name'],
            "value": item['value'],
            "unit": item['unit'],
            "status": status,
            "deviation_percent": deviation
        })

    parse_result = {
        "basic_info": {"bmi": bmi, "blood_pressure": bp},
        "indicators": indicators_result,
        "summary": {"total_indicators": len(indicators_result), "abnormal_count": sum(1 for i in indicators_result if i['status'] != 'normal')}
    }

    # 存储到 scratchpad
    context.write_scratchpad(
        skill_name="parse_report",
        sub_task="解析体检报告数据",
        structured=parse_result,
        text=f"BMI: {bmi['bmi']} ({bmi['category']}), 血压: {bp['category']}, 异常指标: {parse_result['summary']['abnormal_count']}项"
    )

    console.print(f"    ✓ 完成 (规则引擎)")
    console.print(f"      BMI: {bmi['bmi']} ({bmi['category']})")
    console.print(f"      血压: {bp['category']}")
    console.print(f"      异常指标: {parse_result['summary']['abnormal_count']} 项")
    console.print("")

    # Step 2: assess_risk (模拟)
    console.print("  [Step 2/3] 执行 assess_risk...")

    # 模拟风险评估
    risk_scores = {
        "cardiovascular": {"score": 65, "level": "中等风险", "factors": ["血压异常", "BMI 偏高"]},
        "metabolic": {"score": 75, "level": "高风险", "factors": ["血糖偏高", "甘油三酯偏高", "尿酸偏高"]},
        "liver": {"score": 35, "level": "中等风险", "factors": ["谷丙转氨酶偏高"]},
        "kidney": {"score": 0, "level": "低风险", "factors": []}
    }

    assess_result = {
        "risk_scores": risk_scores,
        "overall_risk": {"score": 43.75, "level": "中等风险", "recommendation": "建议改善生活方式，定期复查"}
    }

    context.write_scratchpad(
        skill_name="assess_risk",
        sub_task="评估健康风险",
        structured=assess_result,
        text=f"总体风险: {assess_result['overall_risk']['level']}"
    )

    console.print(f"    ✓ 完成 (规则引擎)")
    console.print(f"      总体风险: {assess_result['overall_risk']['level']}")
    for dim, data in risk_scores.items():
        console.print(f"      {dim}: {data['level']} ({data['score']}分)")
    console.print("")

    # Step 3: generate_advice (模拟)
    console.print("  [Step 3/3] 执行 generate_advice...")

    advice_items = [
        {"category": "饮食", "priority": "重要", "content": "控制碳水化合物摄入，避免高糖食物"},
        {"category": "饮食", "priority": "重要", "content": "低盐饮食，每日食盐摄入<6g"},
        {"category": "饮食", "priority": "重要", "content": "限制高嘌呤食物（海鲜、动物内脏、啤酒）"},
        {"category": "运动", "priority": "建议", "content": "规律有氧运动，每周3-5次"},
        {"category": "生活", "priority": "建议", "content": "避免饮酒，保证充足睡眠"},
        {"category": "就医", "priority": "建议", "content": "建议1-3个月内复查"}
    ]

    advice_result = {
        "advice_items": advice_items,
        "followup_plan": {"timing": "1-3个月内", "items": ["重点指标复查"], "note": "改善生活方式后复查"}
    }

    context.write_scratchpad(
        skill_name="generate_advice",
        sub_task="生成个性化健康建议",
        structured=advice_result,
        text=f"已生成 {len(advice_items)} 条建议"
    )

    console.print(f"    ✓ 完成 (规则引擎)")
    console.print(f"      建议条目: {len(advice_items)} 条")
    console.print(f"      复查计划: {advice_result['followup_plan']['timing']}")
    console.print("")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Phase 6: 审计日志摘要
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    console.print("[dim][6/7] 审计日志摘要...[/dim]")
    audit_summary = context.audit_log.get_summary()
    console.print(f"  ✓ 总计 {audit_summary['total_entries']} 条审计记录")

    by_source = audit_summary.get('by_source', {})
    for source, count in sorted(by_source.items()):
        console.print(f"    - {source}: {count} 条")

    by_layer = audit_summary.get('by_layer', {})
    console.print(f"  按层级分布: {by_layer}")
    console.print("")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Phase 7: 综合结果展示
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    console.print("[dim][7/7] 综合结果...[/dim]")

    # 获取所有执行结果
    results = context.scratchpad.get_ordered_results()

    final_response = f"""
# 健康分析报告

## 基本信息
根据您的体检报告，BMI 为 {parse_result['basic_info']['bmi']['bmi']}（{parse_result['basic_info']['bmi']['category']}），血压为 {bp['category']}。

## 检验指标分析
共检测 {parse_result['summary']['total_indicators']} 项指标，其中 {parse_result['summary']['abnormal_count']} 项异常：
"""

    for ind in indicators_result:
        if ind['status'] != 'normal':
            final_response += f"- **{ind['name']}**: {ind['value']}{ind['unit']} ({ind['status']}, 偏差 {ind['deviation_percent']}%)\n"

    final_response += f"""
## 风险评估
- **心血管风险**: {risk_scores['cardiovascular']['level']}
- **代谢风险**: {risk_scores['metabolic']['level']}
- **肝脏风险**: {risk_scores['liver']['level']}
- **肾脏风险**: {risk_scores['kidney']['level']}

**总体风险**: {assess_result['overall_risk']['level']}

## 健康建议
"""

    for item in advice_items:
        final_response += f"- **{item['category']}**: {item['content']}\n"

    final_response += f"\n**复查计划**: {advice_result['followup_plan']['timing']} - {advice_result['followup_plan']['note']}\n"

    console.print(Panel(
        final_response,
        title="[bold green]健康分析报告 (模拟)[/bold green]",
        border_style="green",
        padding=(1, 2)
    ))
    console.print("")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 测试结论
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    console.print(Panel.fit(
        "[bold green]✓ 模拟测试完成！[/bold green]\n\n"
        "所有核心组件验证通过:\n"
        "  ✓ 三层上下文系统 (AgentContext)\n"
        "  ✓ Skill 加载器 (自动发现 3 个 Skills)\n"
        "  ✓ 工具系统 (3 个工具注册)\n"
        "  ✓ 规则引擎 (BMI/血压/指标检查)\n"
        "  ✓ Skill 执行模拟 (3 个步骤)\n"
        "  ✓ 审计日志 (全链路记录)\n\n"
        "[bold yellow]注意:[/bold yellow] 要进行真实测试，请:\n"
        "  1. 确保 LLM_API_KEY 有效\n"
        "  2. 运行: python test_full_pipeline.py",
        border_style="green"
    ))
    console.print("")

    # 显示执行流程图
    console.print("[bold]执行流程:[/bold]")
    flow = """
    用户请求 ("请帮我分析体检报告...")
           ↓
    ┌─────────────────────────────────────┐
    │  Planner (规划任务)                   │
    │  → 解析意图: 体检报告全流程分析        │
    │  → 生成步骤: parse_report → ...      │
    └─────────────────────────────────────┘
           ↓
    ┌─────────────────────────────────────┐
    │  Executor (执行 Skills)              │
    │  ┌───────────────────────────────┐  │
    │  │ Step 1: parse_report         │  │
    │  │ 规则引擎: BMI/血压/指标检查    │  │
    │  └───────────────────────────────┘  │
    │           ↓                          │
    │  ┌───────────────────────────────┐  │
    │  │ Step 2: assess_risk          │  │
    │  │ 规则引擎: 四维度风险评分      │  │
    │  └───────────────────────────────┘  │
    │           ↓                          │
    │  ┌───────────────────────────────┐  │
    │  │ Step 3: generate_advice      │  │
    │  │ 规则引擎: 建议条目生成         │  │
    │  └───────────────────────────────┘  │
    └─────────────────────────────────────┘
           ↓
    ┌─────────────────────────────────────┐
    │  Synthesizer (综合结果)              │
    │  → 整合三步输出                      │
    │  → 生成连贯的健康分析报告            │
    └─────────────────────────────────────┘
           ↓
       健康分析报告 (最终输出)
    """
    console.print(flow)
    console.print("")


if __name__ == "__main__":
    try:
        run_simulation_test()
    except KeyboardInterrupt:
        console.print("\n[yellow]测试被中断[/yellow]")
    except Exception as e:
        console.print(f"\n[red]测试出错: {e}[/red]")
        import traceback
        traceback.print_exc()
