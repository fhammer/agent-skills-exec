#!/usr/bin/env python3
"""直接运行核心组件测试，避免 conftest.py 导入问题。"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 60)
print("Agent Skills Framework - 核心组件测试")
print("=" * 60)

all_passed = True
test_results = []


def run_test_config():
    """运行配置模块测试。"""
    print("\n[1/5] 运行配置模块测试 (test_config.py)...")
    try:
        from tests.test_config import (
            TestLLMConfig,
            TestBudgetConfig,
            TestExecutionConfig,
            TestConfig,
            TestConfigMethods,
        )

        test_count = 0
        passed = 0
        failed = 0

        # Test LLMConfig
        test_llm = TestLLMConfig()
        for name in dir(test_llm):
            if name.startswith("test_"):
                test_count += 1
                try:
                    getattr(test_llm, name)()
                    passed += 1
                    print(f"  ✓ {name}")
                except Exception as e:
                    failed += 1
                    print(f"  ✗ {name}: {e}")

        # Test BudgetConfig
        test_budget = TestBudgetConfig()
        for name in dir(test_budget):
            if name.startswith("test_"):
                test_count += 1
                try:
                    getattr(test_budget, name)()
                    passed += 1
                    print(f"  ✓ {name}")
                except Exception as e:
                    failed += 1
                    print(f"  ✗ {name}: {e}")

        # Test ExecutionConfig
        test_exec = TestExecutionConfig()
        for name in dir(test_exec):
            if name.startswith("test_"):
                test_count += 1
                try:
                    getattr(test_exec, name)()
                    passed += 1
                    print(f"  ✓ {name}")
                except Exception as e:
                    failed += 1
                    print(f"  ✗ {name}: {e}")

        # Test Config
        test_config = TestConfig()
        for name in dir(test_config):
            if name.startswith("test_"):
                test_count += 1
                try:
                    getattr(test_config, name)()
                    passed += 1
                    print(f"  ✓ {name}")
                except Exception as e:
                    failed += 1
                    print(f"  ✗ {name}: {e}")

        # Test ConfigMethods
        test_methods = TestConfigMethods()
        for name in dir(test_methods):
            if name.startswith("test_"):
                test_count += 1
                try:
                    getattr(test_methods, name)()
                    passed += 1
                    print(f"  ✓ {name}")
                except Exception as e:
                    failed += 1
                    print(f"  ✗ {name}: {e}")

        success = failed == 0
        test_results.append(("配置模块", test_count, passed, failed))
        return success
    except Exception as e:
        print(f"  ✗ 配置模块测试异常: {e}")
        test_results.append(("配置模块", 0, 0, 1))
        return False


def run_test_context():
    """运行上下文管理测试。"""
    print("\n[2/5] 运行上下文管理测试 (test_context.py)...")
    try:
        from tests.test_context import TestAgentContext

        test_count = 0
        passed = 0
        failed = 0

        test_context = TestAgentContext()
        for name in dir(test_context):
            if name.startswith("test_"):
                test_count += 1
                try:
                    getattr(test_context, name)()
                    passed += 1
                    print(f"  ✓ {name}")
                except Exception as e:
                    failed += 1
                    print(f"  ✗ {name}: {e}")

        success = failed == 0
        test_results.append(("上下文管理", test_count, passed, failed))
        return success
    except Exception as e:
        print(f"  ✗ 上下文管理测试异常: {e}")
        import traceback
        traceback.print_exc()
        test_results.append(("上下文管理", 0, 0, 1))
        return False


def run_test_coordinator():
    """运行协调器测试。"""
    print("\n[3/5] 运行协调器测试 (test_coordinator.py)...")
    try:
        from tests.test_coordinator import TestCoordinator

        test_count = 0
        passed = 0
        failed = 0

        test_coordinator = TestCoordinator()
        for name in dir(test_coordinator):
            if name.startswith("test_"):
                test_count += 1
                try:
                    # Skip async tests for this simple runner
                    import inspect
                    method = getattr(test_coordinator, name)
                    if inspect.iscoroutinefunction(method):
                        print(f"  - {name} (跳过异步测试)")
                        continue
                    method()
                    passed += 1
                    print(f"  ✓ {name}")
                except Exception as e:
                    failed += 1
                    print(f"  ✗ {name}: {e}")

        success = failed == 0
        test_results.append(("协调器", test_count, passed, failed))
        return success
    except Exception as e:
        print(f"  ✗ 协调器测试异常: {e}")
        import traceback
        traceback.print_exc()
        test_results.append(("协调器", 0, 0, 1))
        return False


def run_test_skill_executor():
    """运行技能执行器测试。"""
    print("\n[4/5] 运行技能执行器测试 (test_skill_executor.py)...")
    try:
        from tests.test_skill_executor import TestSkillExecutor

        test_count = 0
        passed = 0
        failed = 0

        test_executor = TestSkillExecutor()
        for name in dir(test_executor):
            if name.startswith("test_"):
                test_count += 1
                try:
                    getattr(test_executor, name)()
                    passed += 1
                    print(f"  ✓ {name}")
                except Exception as e:
                    failed += 1
                    print(f"  ✗ {name}: {e}")

        success = failed == 0
        test_results.append(("技能执行器", test_count, passed, failed))
        return success
    except Exception as e:
        print(f"  ✗ 技能执行器测试异常: {e}")
        import traceback
        traceback.print_exc()
        test_results.append(("技能执行器", 0, 0, 1))
        return False


def run_test_synthesizer():
    """运行结果合成器测试。"""
    print("\n[5/5] 运行结果合成器测试 (test_synthesizer.py)...")
    try:
        from tests.test_synthesizer import TestSynthesizer

        test_count = 0
        passed = 0
        failed = 0

        test_synthesizer = TestSynthesizer()
        for name in dir(test_synthesizer):
            if name.startswith("test_"):
                test_count += 1
                try:
                    getattr(test_synthesizer, name)()
                    passed += 1
                    print(f"  ✓ {name}")
                except Exception as e:
                    failed += 1
                    print(f"  ✗ {name}: {e}")

        success = failed == 0
        test_results.append(("结果合成器", test_count, passed, failed))
        return success
    except Exception as e:
        print(f"  ✗ 结果合成器测试异常: {e}")
        import traceback
        traceback.print_exc()
        test_results.append(("结果合成器", 0, 0, 1))
        return False


def print_summary():
    """打印测试总结。"""
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    total_tests = 0
    total_passed = 0
    total_failed = 0

    for module, test_count, passed, failed in test_results:
        total_tests += test_count
        total_passed += passed
        total_failed += failed
        status = "✓ 通过" if failed == 0 else "✗ 失败"
        print(f"\n{module}: {status}")
        print(f"  测试数: {test_count}, 通过: {passed}, 失败: {failed}")

    print("\n" + "-" * 60)
    print(f"总计: 测试数={total_tests}, 通过={total_passed}, 失败={total_failed}")
    print(f"成功率: {(total_passed/total_tests*100):.1f}%" if total_tests > 0 else "无测试")
    print("=" * 60)

    return total_failed == 0


def main():
    """主函数。"""
    global all_passed

    print("\n开始运行核心组件测试...\n")

    # Run all tests
    all_passed = run_test_config() and all_passed
    all_passed = run_test_context() and all_passed
    all_passed = run_test_coordinator() and all_passed
    all_passed = run_test_skill_executor() and all_passed
    all_passed = run_test_synthesizer() and all_passed

    # Print summary
    success = print_summary()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
