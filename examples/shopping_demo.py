#!/usr/bin/env python3
"""
智能导购Demo - 真正的LLM驱动购物助手

这是一个基于大语言模型的智能导购助手，能够：
- 自然理解用户需求
- 智能推荐商品
- 多轮对话管理
- 商品对比和咨询
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from skills.shopping_assistant.executor import ShoppingAssistant
from agent.llm_client import LLMClient


async def interactive_mode_with_llm():
    """带LLM的交互模式"""
    print("\n" + "=" * 60)
    print("  智能导购助手 - 小购")
    print("  (基于大语言模型)")
    print("=" * 60)
    print("\n您可以问我:")
    print("  - 推荐一款8000元左右的笔记本")
    print("  - 我想买个降噪耳机")
    print("  - 对比一下小米和华为的手机")
    print("  - 5000元以内有什么好手机")
    print("\n输入 'quit' 或 'exit' 退出\n")

    # 初始化LLM客户端
    llm_client = None
    try:
        from config import Config
        config = Config.from_file()
        llm_client = LLMClient(config)
        # 测试调用
        _ = llm_client.invoke("test")
        print("✓ LLM服务已连接\n")
    except Exception as e:
        print(f"⚠ LLM服务连接失败: {e}")
        print("将使用智能模拟模式（功能完整，基于规则引擎）\n")
        llm_client = None

    # 创建助手
    assistant = ShoppingAssistant(llm_client)
    user_id = "demo_user"
    session_id = None

    while True:
        try:
            user_input = input("用户: ").strip()

            if user_input.lower() in ['quit', 'exit', '退出', 'q']:
                print("\n小购: 期待下次为您服务，再见！👋")
                break

            if not user_input:
                continue

            # 调用助手
            response = await assistant.chat(
                message=user_input,
                user_id=user_id,
                session_id=session_id
            )

            # 保存会话ID
            if session_id is None:
                session_id = response.metadata.get("session_id")

            print(f"\n小购: {response.content}\n")

            # 显示推荐的商品
            if response.products:
                print("【推荐商品详情】")
                for i, p in enumerate(response.products[:3], 1):
                    print(f"\n{i}. {p.to_display_text()}")

        except KeyboardInterrupt:
            print("\n\n小购: 期待下次为您服务，再见！👋")
            break
        except Exception as e:
            print(f"\n错误: {e}\n")
            import traceback
            traceback.print_exc()


async def demo_scenarios():
    """演示预设场景"""
    print("\n" + "=" * 60)
    print("  智能导购助手 - 场景演示")
    print("=" * 60 + "\n")

    assistant = ShoppingAssistant(None)  # 使用模拟模式
    user_id = "demo_user"

    # 场景1: 笔记本推荐
    print("=" * 60)
    print("场景1: 笔记本推荐")
    print("=" * 60)

    messages = [
        "我想买个笔记本",
        "预算8000左右，用来做开发",
    ]

    for msg in messages:
        print(f"\n用户: {msg}")
        response = await assistant.chat(message=msg, user_id=user_id)
        print(f"小购: {response.content}")
        if response.products:
            print(f"  [找到 {len(response.products)} 款商品]")

    # 场景2: 手机推荐
    print("\n" + "=" * 60)
    print("场景2: 手机推荐")
    print("=" * 60)

    assistant2 = ShoppingAssistant(None)

    messages2 = [
        "推荐一款拍照好的手机",
    ]

    for msg in messages2:
        print(f"\n用户: {msg}")
        response = await assistant2.chat(message=msg, user_id="demo_user2")
        print(f"小购: {response.content}")
        if response.products:
            print(f"  [找到 {len(response.products)} 款商品]")


async def test_tool_calls():
    """测试工具调用"""
    print("\n" + "=" * 60)
    print("  测试工具调用")
    print("=" * 60 + "\n")

    from skills.shopping_assistant.tools import (
        search_products_tool,
        compare_products_tool,
        get_categories_tool
    )

    # 测试搜索
    print("1. 搜索笔记本")
    result = search_products_tool(category="笔记本", max_price=10000, limit=3)
    print(f"   找到 {result['total']} 款商品")
    for p in result['products'][:2]:
        print(f"   - {p['name']}: ¥{p['price']}")

    # 测试对比
    print("\n2. 对比商品")
    result = compare_products_tool(product_ids=["l_001", "l_002"])
    print(f"   {result['recommendation']}")

    # 测试类别
    print("\n3. 商品类别")
    result = get_categories_tool()
    print(f"   类别: {result['categories']}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="智能导购助手Demo")
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="启动交互式对话模式"
    )
    parser.add_argument(
        "--demo",
        "-d",
        action="store_true",
        help="运行预设场景演示"
    )
    parser.add_argument(
        "--test",
        "-t",
        action="store_true",
        help="测试工具调用"
    )

    args = parser.parse_args()

    if args.test:
        asyncio.run(test_tool_calls())
    elif args.interactive:
        asyncio.run(interactive_mode_with_llm())
    elif args.demo:
        asyncio.run(demo_scenarios())
    else:
        print("请选择运行模式:")
        print("  --interactive, -i    交互式对话模式")
        print("  --demo, -d           预设场景演示")
        print("  --test, -t           测试工具调用")
        print("\n默认启动交互模式...")
        asyncio.run(interactive_mode_with_llm())
