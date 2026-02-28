"""Dry-run test of Agent Skills Framework without API calls."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 70)
print("Agent Skills Framework - 框架测试（无 API 调用）")
print("=" * 70)

# Test 1: Import all modules
print("\n[1/5] 测试模块导入...")
try:
    from agent.context import AgentContext
    from agent.scratchpad import Scratchpad
    from agent.audit import AuditLog, AuditLayer, AuditOp
    from agent.token_budget import TokenBudget
    from agent.tools import ToolRegistry, create_default_registry
    from agent.llm_base import LLMProvider, LLMMessage
    from agent.llm_client import LLMClient
    from agent.errors import AgentError, SkillNotFoundError
    from utils.skill_loader import Skill, SkillLoader, SkillRegistry
    from shared.metrics_utils import calculate_bmi, classify_blood_pressure, check_indicator
    print("  ✓ 所有核心模块导入成功")
except Exception as e:
    print(f"  ✗ 导入失败: {e}")
    sys.exit(1)

# Test 2: Three-layer context system
print("\n[2/5] 测试三层上下文系统...")
try:
    context = AgentContext(enable_audit=True)
    context.set_component("coordinator")

    # Layer 1 operations
    context.write_layer1("raw_user_input", "请帮我分析体检报告", "test")
    context.write_layer1("parsed_intent", "体检报告分析", "test")

    # Layer 2 operations
    context.scratchpad.set_result("test_skill", "test_task", {"key": "value"}, "test output")
    result = context.read_scratchpad("test_skill")
    assert result.skill_name == "test_skill"

    # Layer 3 operations
    context.write_layer3("test_config", {"setting": "value"}, "test")

    # Verify audit logging
    assert len(context.audit_log.entries) > 0
    print("  ✓ 三层上下文系统正常")
    print(f"    - Layer1 条目: {len([e for e in context.audit_log.entries if e.layer == AuditLayer.USER_INPUT])}")
    print(f"    - Layer2 条目: {len([e for e in context.audit_log.entries if e.layer == AuditLayer.SCRATCHPAD])}")
    print(f"    - Layer3 条目: {len([e for e in context.audit_log.entries if e.layer == AuditLayer.ENVIRONMENT])}")
except Exception as e:
    print(f"  ✗ 失败: {e}")
    sys.exit(1)

# Test 3: Token budget management
print("\n[3/5] 测试 Token 预算管理...")
try:
    budget = TokenBudget(total_limit=10000, warning_threshold=0.8)

    budget.consume(1000, "test_invoke")
    budget.consume(2000, "test_invoke_2")

    summary = budget.get_summary()
    assert summary["used"] == 3000
    assert summary["remaining"] == 7000
    assert abs(summary["usage_ratio"] - 0.3) < 0.01

    # Test compression ratio - after using 3000, remaining is 7000 < 20000
    ratio = budget.get_compression_ratio()
    # With 7000 remaining, we get 0.5 compression ratio
    assert ratio == 0.5

    print("  ✓ Token 预算管理正常")
    print(f"    - 已用: {summary['used']}/{summary['total_limit']}")
    print(f"    - 压缩比例: {ratio}")
except Exception as e:
    print(f"  ✗ 失败: {e}")
    sys.exit(1)

# Test 4: Tool system
print("\n[4/5] 测试工具系统...")
try:
    registry = create_default_registry()

    # Test BMI calculator
    bmi_result = registry.execute("calculate_bmi", height_cm=175, weight_kg=70)
    assert bmi_result["bmi"] == 22.9
    assert bmi_result["category"] == "正常"

    # Test blood pressure classifier
    bp_result = registry.execute("classify_blood_pressure", sbp=120, dbp=80)
    assert bp_result["category"] == "正常"

    # Test reference range checker
    range_result = registry.execute("check_reference_range", value=7.2, ref_low=3.9, ref_high=6.1)
    assert range_result["status"] == "high"
    assert range_result["deviation_percent"] == 18.0

    print("  ✓ 工具系统正常")
    print(f"    - 已注册工具: {len(registry.list_all())}")
    print(f"    - BMI 示例: {bmi_result}")
    print(f"    - 血压分类: {bp_result['category']}")
    print(f"    - 参考范围检查: {range_result['status']}")
except Exception as e:
    print(f"  ✗ 失败: {e}")
    sys.exit(1)

# Test 5: Skill loader
print("\n[5/5] 测试 Skill 加载器...")
try:
    loader = SkillLoader("skills")
    skills = loader.discover()

    print(f"  ✓ Skill 加载器正常")
    print(f"    - 发现 Skills: {len(skills)}")

    for name, skill in skills.items():
        print(f"    - {name}: {skill.description}")
        print(f"      模式: {skill.execution_mode}")
        print(f"      触发词: {', '.join(skill.triggers)}")

    summary = loader.get_summary()
    print(f"    - 执行模式分布: {summary['by_execution_mode']}")

except Exception as e:
    print(f"  ✗ 失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 6: Shared utilities
print("\n[6/6] 测试共享工具函数...")
try:
    # BMI calculation
    bmi = calculate_bmi(175, 70)
    assert 22 <= bmi <= 23

    # Blood pressure classification
    bp_cat = classify_blood_pressure(140, 90)
    assert bp_cat == "高血压1级"

    # Indicator check
    status, deviation = check_indicator(7.2, 3.9, 6.1)
    assert status == "high"
    assert deviation == 18.0

    print("  ✓ 共享工具函数正常")
    print(f"    - BMI (175cm, 70kg): {bmi:.1f}")
    print(f"    - 血压 (140/90): {bp_cat}")
    print(f"    - 指标检查 (7.2, ref 3.9-6.1): {status}, 偏差 {deviation}%")
except Exception as e:
    print(f"  ✗ 失败: {e}")
    sys.exit(1)

# Summary
print("\n" + "=" * 70)
print("框架测试完成！✓")
print("=" * 70)
print("\n所有核心组件测试通过：")
print("  ✓ 三层上下文系统 (AgentContext, Scratchpad, AuditLog)")
print("  ✓ Token 预算管理 (TokenBudget)")
print("  ✓ 工具系统 (ToolRegistry, BMI/血压/参考范围检查)")
print("  ✓ Skill 加载器 (SkillLoader, 自动发现)")
print("  ✓ 共享工具函数 (metrics_utils)")
print("\n已加载的 Skills:")
print("  1. parse_report - 体检报告解析")
print("  2. assess_risk - 健康风险评估")
print("  3. generate_advice - 健康建议生成")
print("\n下一步:")
print("  1. 设置 LLM_API_KEY 环境变量")
print("  2. 运行: python main.py --mode demo")
print("  3. 或创建自定义 Skill: ./scripts/create_skill.sh my_skill")
print()
