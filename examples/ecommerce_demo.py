#!/usr/bin/env python3
"""
电商Demo 1: 智能导购/商品推荐Agent

展示如何使用Agent Skills Framework实现智能导购功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from skills.ecommerce_recommendation.executor import EcommerceRecommendationExecutor


def print_section(title: str):
    """打印分隔线"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")


async def demo_basic_recommendation():
    """基本推荐场景"""
    print_section("场景1: 明确需求推荐")

    executor = EcommerceRecommendationExecutor()

    user_input = "我想买个2000-3000元的手机，平时玩游戏比较多"
    print(f"用户: {user_input}\n")

    result = await executor.execute(
        user_input=user_input,
        user_id="demo_user_001"
    )

    print(f"Agent: {result.response_text}")
    print(f"\n对话状态: {result.dialogue_state.value}")
    print(f"推荐商品数: {len(result.recommendations)}")


async def demo_fuzzy_demand():
    """模糊需求场景"""
    print_section("场景2: 模糊需求引导")

    executor = EcommerceRecommendationExecutor()

    user_input = "我想买个好东西"
    print(f"用户: {user_input}\n")

    result = await executor.execute(user_input=user_input)

    print(f"Agent: {result.response_text}")
    print(f"\n对话状态: {result.dialogue_state.value}")


async def demo_brand_preference():
    """品牌偏好场景"""
    print_section("场景3: 品牌偏好推荐")

    executor = EcommerceRecommendationExecutor()

    user_input = "华为有什么好手机推荐吗？预算3000左右"
    print(f"用户: {user_input}\n")

    result = await executor.execute(
        user_input=user_input,
        user_id="demo_user_002"
    )

    print(f"Agent: {result.response_text}")


async def demo_comparison():
    """商品对比场景"""
    print_section("场景4: 商品对比")

    executor = EcommerceRecommendationExecutor()

    product_names = ["Redmi K70", "iQOO Neo9"]
    print(f"用户: 对比一下 {' 和 '.join(product_names)}\n")

    result = await executor.compare_products(product_names)

    print(f"Agent: {result.recommendation}")
    print("\n对比要点:")
    for point, values in result.comparison_points.items():
        print(f"  {point}:")
        for product_name, info in values.items():
            print(f"    {product_name}: {info['text']}")


async def demo_multi_turn_conversation():
    """多轮对话场景"""
    print_section("场景5: 多轮对话")

    executor = EcommerceRecommendationExecutor()
    user_id = "demo_user_003"

    # 第一轮
    print("=== 第1轮对话 ===")
    user_input_1 = "我想买个耳机"
    print(f"用户: {user_input_1}\n")

    result_1 = await executor.execute(
        user_input=user_input_1,
        user_id=user_id
    )
    print(f"Agent: {result_1.response_text[:100]}...\n")

    # 第二轮
    print("=== 第2轮对话 ===")
    user_input_2 = "预算500元左右，主要运动时用"
    print(f"用户: {user_input_2}\n")

    result_2 = await executor.execute(
        user_input=user_input_2,
        user_id=user_id,
        context={
            "previous_intent": result_1.demand_analysis.intent.value,
            "category": "耳机"  # 从第一轮对话中获取的商品类别
        }
    )
    print(f"Agent: {result_2.response_text[:200]}...\n")


async def demo_all_scenarios():
    """运行所有演示场景"""
    print("\n" + "=" * 60)
    print("  电商Demo 1: 智能导购/商品推荐Agent")
    print("  Agent Skills Framework 演示")
    print("=" * 60)

    try:
        await demo_basic_recommendation()
        await demo_fuzzy_demand()
        await demo_brand_preference()
        await demo_comparison()
        await demo_multi_turn_conversation()

        print_section("演示完成")
        print("所有场景演示完成！\n")

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


async def interactive_mode():
    """交互式对话模式"""
    print_section("智能导购交互式对话模式")
    print("输入 'quit' 或 'exit' 退出\n")

    executor = EcommerceRecommendationExecutor()
    user_id = "interactive_user"

    # 维护对话上下文
    conversation_context = {}
    dialogue_state = None

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
                user_id=user_id,
                context=conversation_context
            )

            print(f"\nAgent: {result.response_text}\n")

            # 更新对话上下文，保存已收集的信息
            dialogue_state = result.dialogue_state

            # 保存需求分析结果到上下文
            if result.demand_analysis:
                if result.demand_analysis.category:
                    conversation_context["category"] = result.demand_analysis.category

                # 保存价格范围约束
                for constraint in (result.demand_analysis.constraints or []):
                    if constraint.type == "price_range":
                        conversation_context["price_range"] = constraint.value

            # 如果需要澄清，记录已询问的问题
            if result.dialogue_state.value == "awaiting_clarification":
                conversation_context["awaiting_clarification"] = True

            # 如果推荐完成，清除等待澄清状态
            elif result.dialogue_state.value == "recommendation_ready":
                conversation_context.pop("awaiting_clarification", None)

        except KeyboardInterrupt:
            print("\n\n再见！")
            break
        except Exception as e:
            print(f"\n错误: {e}\n")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="电商智能导购Demo")
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="启动交互式对话模式"
    )
    parser.add_argument(
        "--scenario",
        "-s",
        choices=["basic", "fuzzy", "brand", "comparison", "multi-turn", "all"],
        default="all",
        help="选择要演示的场景"
    )

    args = parser.parse_args()

    if args.interactive:
        asyncio.run(interactive_mode())
    else:
        if args.scenario == "all":
            asyncio.run(demo_all_scenarios())
        elif args.scenario == "basic":
            asyncio.run(demo_basic_recommendation())
        elif args.scenario == "fuzzy":
            asyncio.run(demo_fuzzy_demand())
        elif args.scenario == "brand":
            asyncio.run(demo_brand_preference())
        elif args.scenario == "comparison":
            asyncio.run(demo_comparison())
        elif args.scenario == "multi-turn":
            asyncio.run(demo_multi_turn_conversation())
