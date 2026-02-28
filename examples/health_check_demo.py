"""Health check demonstration for Agent Skills Framework."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config
from agent.coordinator import Coordinator


def main():
    """Run health check demonstration."""
    print("=" * 60)
    print("Agent Skills Framework - 健康检查演示")
    print("=" * 60)

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

    print("\n体检报告数据:")
    print(f"  身高: {sample_report['height']} cm, 体重: {sample_report['weight']} kg")
    print(f"  血压: {sample_report['sbp']}/{sample_report['dbp']} mmHg")
    print(f"  检验指标: {len(sample_report['lab_items'])} 项")
    for item in sample_report['lab_items']:
        print(f"    - {item['name']}: {item['value']}{item['unit']} (参考: {item['ref_low']}-{item['ref_high']})")

    # Load configuration
    config = Config.from_env()
    config.validate()

    # Initialize coordinator
    print("\n初始化系统...")
    coordinator = Coordinator(config)
    print(f"✓ 已加载 {len(coordinator.skill_registry.get_all_skills())} 个 Skills")

    # Process request
    request = f"""请帮我分析这份体检报告并给出建议：

身高: {sample_report['height']}cm, 体重: {sample_report['weight']}kg
血压: {sample_report['sbp']}/{sample_report['dbp']}mmHg
空腹血糖: {sample_report['lab_items'][0]['value']}{sample_report['lab_items'][0]['unit']}
总胆固醇: {sample_report['lab_items'][1]['value']}{sample_report['lab_items'][1]['unit']}
甘油三酯: {sample_report['lab_items'][2]['value']}{sample_report['lab_items'][2]['unit']}
尿酸: {sample_report['lab_items'][3]['value']}{sample_report['lab_items'][3]['unit']}
谷丙转氨酶: {sample_report['lab_items'][4]['value']}{sample_report['lab_items'][4]['unit']}
"""

    print("\n处理请求...")
    result = coordinator.process(request)

    # Display result
    if result.get("success"):
        print("\n" + "=" * 60)
        print("健康分析报告")
        print("=" * 60)
        print(result["final_response"])

        # Show execution plan
        if "plan" in result:
            print("\n执行计划:")
            for i, step in enumerate(result["plan"]["steps"], 1):
                print(f"  {i}. {step['skill']}: {step['sub_task']} (置信度: {step['confidence']})")

        # Show metrics
        metrics = result["metrics"]
        print(f"\n执行指标:")
        print(f"  执行时间: {metrics['execution_time_ms']:.0f} ms")
        print(f"  执行 Skills: {metrics['total_skills_executed']}")
        print(f"  LLM 调用: {metrics['llm_metrics']['total_calls']} 次")
        print(f"  Token 消耗: {metrics['llm_metrics']['total_tokens']}")
    else:
        print(f"\n错误: {result.get('final_response')}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
