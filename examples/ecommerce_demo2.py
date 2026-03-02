#!/usr/bin/env python3
"""
电商Demo 2: 订单处理/售后客服Agent

展示如何使用Agent Skills Framework实现售后客服功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from examples.ecommerce.support.executor import CustomerSupportExecutor


def print_section(title: str):
    """打印分隔线"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")


async def demo_order_query_recent():
    """场景1: 查询最近订单"""
    print_section("场景1: 查询最近订单")

    executor = CustomerSupportExecutor()

    user_input = "帮我查一下我的订单"
    print(f"用户: {user_input}\n")

    result = await executor.execute(
        user_input=user_input,
        user_id="user_123"  # 使用Mock数据中存在的用户ID
    )

    print(f"Agent: {result.response_text}")
    print(f"\n意图: {result.intent.value}")
    print(f"对话状态: {result.dialogue_state.value}")


async def demo_order_query_by_id():
    """场景2: 按订单号查询"""
    print_section("场景2: 按订单号查询")

    executor = CustomerSupportExecutor()

    user_input = "查询一下订单 20240228123456"
    print(f"用户: {user_input}\n")

    result = await executor.execute(
        user_input=user_input,
        user_id="user_123"  # 使用Mock数据中存在的用户ID
    )

    print(f"Agent: {result.response_text}")
    print(f"\n意图: {result.intent.value}")


async def demo_logistics_query():
    """场景3: 查询物流"""
    print_section("场景3: 查询物流信息")

    executor = CustomerSupportExecutor()

    user_input = "我的快递到哪了？订单号 20240228123456"
    print(f"用户: {user_input}\n")

    result = await executor.execute(
        user_input=user_input,
        user_id="user_123"  # 使用Mock数据中存在的用户ID
    )

    print(f"Agent: {result.response_text}")


async def demo_return_request_quality_issue():
    """场景4: 质量问题退货"""
    print_section("场景4: 质量问题退货")

    executor = CustomerSupportExecutor()
    user_id = "user_123"
    session_id = "test_return_quality_001"

    # 第一轮：退货申请
    print("=== 第1轮对话 ===")
    user_input_1 = "我想退货，屏幕有坏点"
    print(f"用户: {user_input_1}\n")

    result_1 = await executor.execute(
        user_input=user_input_1,
        user_id=user_id,
        session_id=session_id
    )

    print(f"Agent: {result_1.response_text}")
    print(f"对话状态: {result_1.dialogue_state.value}\n")

    # 第二轮：提供订单号
    print("=== 第2轮对话 ===")
    user_input_2 = "订单 20240228123456"
    print(f"用户: {user_input_2}\n")

    result_2 = await executor.execute(
        user_input=user_input_2,
        user_id=user_id,
        session_id=session_id
    )

    print(f"Agent: {result_2.response_text}")
    print(f"\n是否创建工单: {result_2.case_created}")


async def demo_return_request_no_reason():
    """场景5: 7天无理由退货"""
    print_section("场景5: 7天无理由退货")

    executor = CustomerSupportExecutor()
    user_id = "demo_user_003"

    # 第一轮：退货申请
    print("=== 第1轮对话 ===")
    user_input_1 = "这个手机不想要了，想退货"
    print(f"用户: {user_input_1}\n")

    result_1 = await executor.execute(
        user_input=user_input_1,
        user_id=user_id
    )

    print(f"Agent: {result_1.response_text}\n")

    # 第二轮：提供订单号
    print("=== 第2轮对话 ===")
    user_input_2 = "订单 20240228123456"
    print(f"用户: {user_input_2}\n")

    result_2 = await executor.execute(
        user_input=user_input_2,
        user_id=user_id
    )

    print(f"Agent: {result_2.response_text}")
    print(f"\n是否创建工单: {result_2.case_created}")


async def demo_exchange_request():
    """场景6: 换货申请"""
    print_section("场景6: 换货申请")

    executor = CustomerSupportExecutor()
    user_id = "demo_user_004"

    # 第一轮：换货申请
    print("=== 第1轮对话 ===")
    user_input_1 = "想换个颜色"
    print(f"用户: {user_input_1}\n")

    result_1 = await executor.execute(
        user_input=user_input_1,
        user_id=user_id
    )

    print(f"Agent: {result_1.response_text}\n")

    # 第二轮：提供订单号
    print("=== 第2轮对话 ===")
    user_input_2 = "订单 20240228123456，想换成白色"
    print(f"用户: {user_input_2}\n")

    result_2 = await executor.execute(
        user_input=user_input_2,
        user_id=user_id
    )

    print(f"Agent: {result_2.response_text}")
    print(f"\n是否创建工单: {result_2.case_created}")


async def demo_policy_inquiry():
    """场景7: 售后政策咨询"""
    print_section("场景7: 售后政策咨询")

    executor = CustomerSupportExecutor()

    user_input = "退货需要运费吗？"
    print(f"用户: {user_input}\n")

    result = await executor.execute(
        user_input=user_input,
        user_id="demo_user_005"
    )

    print(f"Agent: {result.response_text}")


async def demo_expired_return():
    """场景8: 超过退货期限"""
    print_section("场景8: 超过退货期限（测试边界情况）")

    executor = CustomerSupportExecutor()

    # 使用一个较老的订单号模拟过期
    user_input = "订单 20240220111111 想退货"
    print(f"用户: {user_input}\n")

    result = await executor.execute(
        user_input=user_input,
        user_id="demo_user_006"
    )

    print(f"Agent: {result.response_text}")
    print(f"\n是否创建工单: {result.case_created}")


async def demo_all_scenarios():
    """运行所有演示场景"""
    print("\n" + "=" * 60)
    print("  电商Demo 2: 订单处理/售后客服Agent")
    print("  Agent Skills Framework 演示")
    print("=" * 60)

    try:
        await demo_order_query_recent()
        await demo_order_query_by_id()
        await demo_logistics_query()
        await demo_return_request_quality_issue()
        await demo_return_request_no_reason()
        await demo_exchange_request()
        await demo_policy_inquiry()
        await demo_expired_return()

        print_section("演示完成")
        print("所有场景演示完成！\n")

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


async def interactive_mode():
    """交互式对话模式"""
    print_section("售后客服交互式对话模式")
    print("输入 'quit' 或 'exit' 退出\n")

    executor = CustomerSupportExecutor()
    user_id = "interactive_user"

    while True:
        try:
            user_input = input("用户: ").strip()

            if user_input.lower() in ['quit', 'exit', '退出', 'q']:
                print("再见！")
                break

            if not user_input:
                continue

            result = await executor.execute(
                user_input=user_input,
                user_id=user_id
            )

            print(f"\nAgent: {result.response_text}\n")

        except KeyboardInterrupt:
            print("\n\n再见！")
            break
        except Exception as e:
            print(f"\n错误: {e}\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="电商售后客服Demo")
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="启动交互式对话模式"
    )
    parser.add_argument(
        "--scenario",
        "-s",
        choices=[
            "query-recent",
            "query-id",
            "logistics",
            "return-quality",
            "return-no-reason",
            "exchange",
            "policy",
            "expired",
            "all"
        ],
        default="all",
        help="选择要演示的场景"
    )

    args = parser.parse_args()

    if args.interactive:
        asyncio.run(interactive_mode())
    else:
        if args.scenario == "all":
            asyncio.run(demo_all_scenarios())
        elif args.scenario == "query-recent":
            asyncio.run(demo_order_query_recent())
        elif args.scenario == "query-id":
            asyncio.run(demo_order_query_by_id())
        elif args.scenario == "logistics":
            asyncio.run(demo_logistics_query())
        elif args.scenario == "return-quality":
            asyncio.run(demo_return_request_quality_issue())
        elif args.scenario == "return-no-reason":
            asyncio.run(demo_return_request_no_reason())
        elif args.scenario == "exchange":
            asyncio.run(demo_exchange_request())
        elif args.scenario == "policy":
            asyncio.run(demo_policy_inquiry())
        elif args.scenario == "expired":
            asyncio.run(demo_expired_return())
