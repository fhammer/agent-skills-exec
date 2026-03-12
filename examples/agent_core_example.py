#!/usr/bin/env python3
"""
Agent Core 示例 - 展示如何使用通用智能体框架的核心抽象基类

本示例演示：
1. 如何实现自定义 Agent
2. 如何实现自定义 Skill
3. 如何使用 Skill Registry
4. 如何使用 Context Manager
5. 如何使用 Extension System
"""

import asyncio
import sys
sys.path.insert(0, '.')

from agent_core.base.agent import Agent, AgentConfig, AgentState
from agent_core.base.skill import BaseSkill, SkillConfig, SkillExecutionContext, SkillExecutionResult
from agent_core.skill_registry import SkillRegistry, RegistryConfig
from agent_core.context_manager import ContextManager, ContextManagerConfig
from agent_core.extension_system import ExtensionManager, ExtensionManagerConfig


# ==================== 自定义 Agent 实现 ====================

class MyAgent(Agent):
    """
    自定义智能体实现
    """

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self._registry = None
        self._context_manager = None

    async def initialize(self) -> bool:
        """初始化智能体"""
        try:
            # 初始化技能注册表
            registry_config = RegistryConfig(
                skills_dir="./skills",
                enable_auto_discovery=True,
                enable_hot_reload=False,
                enable_health_check=True
            )
            self._registry = SkillRegistry(registry_config)

            # 初始化上下文管理器
            context_config = ContextManagerConfig(
                enable_audit=True,
                enable_progressive_disclosure=True,
                max_history_length=100,
                max_scratchpad_size=10 * 1024 * 1024
            )
            self._context_manager = ContextManager(context_config)

            self._status = AgentState.READY
            print(f"✅ Agent '{self.config.name}' 初始化成功")
            return True
        except Exception as e:
            self._status = AgentState.ERROR
            print(f"❌ Agent 初始化失败: {e}")
            return False

    async def process(self, user_input: str, context: dict = None) -> dict:
        """处理用户输入"""
        if self._status != AgentState.READY:
            return {"error": "Agent 未准备好"}

        self._context_manager.write_user_input("raw_query", user_input)
        self._context_manager.write_user_input("user_context", context or {})

        print(f"📝 处理请求: {user_input}")

        # 根据意图匹配技能
        matched_skills = await self._find_matching_skills(user_input)
        if not matched_skills:
            return {"response": "抱歉，我无法处理您的请求"}

        # 执行最佳匹配的技能
        result = await self._execute_best_skill(matched_skills, user_input)
        return result

    async def _find_matching_skills(self, user_input: str):
        """查找匹配的技能"""
        matching = []
        all_skills = self._registry.get_all_skills()
        for name, info in all_skills.items():
            skill = self._registry.get_skill(name)
            if skill and skill.can_handle(user_input):
                matching.append(skill)
        return matching

    async def _execute_best_skill(self, skills, user_input):
        """执行最佳技能"""
        if not skills:
            return {"response": "未找到匹配的技能"}

        best_skill = skills[0]
        context = SkillExecutionContext(
            sub_task=f"处理用户请求: {user_input}",
            user_input=user_input
        )

        result = await best_skill.execute(context)

        if result.success:
            return {
                "response": result.text,
                "data": result.structured
            }
        else:
            return {
                "error": f"执行失败: {result.error}"
            }

    async def pause(self):
        self._status = AgentState.PAUSED
        return True

    async def resume(self):
        self._status = AgentState.READY
        return True

    async def shutdown(self):
        self._status = AgentState.SHUTDOWN
        if self._registry:
            await self._registry.shutdown()
        return True

    def get_audit_trail(self):
        return self._context_manager.get_audit_trail()

    def get_config(self):
        return self.config.__dict__


# ==================== 自定义 Skill 实现 ====================

class CalculatorSkill(BaseSkill):
    """计算器技能"""

    async def _on_initialize(self):
        return True

    async def _execute(self, context: SkillExecutionContext) -> SkillExecutionResult:
        try:
            input_text = context.user_input.strip()
            result = eval(input_text)  # 简单实现，实际应该使用更安全的计算方法
            return SkillExecutionResult.success(
                self.name,
                context.sub_task,
                {"expression": input_text, "result": result},
                f"计算结果: {result}"
            )
        except Exception as e:
            return SkillExecutionResult.failure(
                self.name,
                context.sub_task,
                str(e)
            )

    async def _on_shutdown(self):
        return True

    def can_handle(self, intent: str):
        return any(op in intent.lower() for op in ['+', '-', '*', '/', '计算', '等于'])


class WeatherSkill(BaseSkill):
    """天气查询技能"""

    async def _on_initialize(self):
        return True

    async def _execute(self, context: SkillExecutionContext) -> SkillExecutionResult:
        # 简单的模拟实现
        city = self._extract_city(context.user_input)
        weather = f"{city} 天气晴朗，温度 25°C"
        return SkillExecutionResult.success(
            self.name,
            context.sub_task,
            {"city": city, "weather": weather},
            weather
        )

    async def _on_shutdown(self):
        return True

    def _extract_city(self, text):
        cities = ["北京", "上海", "广州", "深圳", "杭州"]
        for city in cities:
            if city in text:
                return city
        return "北京"

    def can_handle(self, intent: str):
        return any(keyword in intent.lower() for keyword in ['天气', '温度', '下雨', '晴天'])


# ==================== 主函数 ====================

async def main():
    print("🚀 启动 Agent Core 示例")
    print("=" * 50)

    try:
        # 1. 创建并初始化 Agent
        config = AgentConfig(
            name="智能助手",
            version="2.0.0",
            description="通用智能体框架演示",
            enable_audit=True,
            enable_metrics=True
        )
        agent = MyAgent(config)
        await agent.initialize()
        await agent.resume()

        print("\n🔍 已加载技能:")
        print(f"   - 计算器技能 (支持: 加减乘除, 计算等)")
        print(f"   - 天气技能 (支持: 天气查询, 温度, 下雨等)")

        # 2. 处理测试请求
        test_queries = [
            "北京的天气怎么样？",
            "计算 10 + 5 * 3 - 2",
            "深圳明天会下雨吗？",
            "100除以25等于多少？",
            "今天天气真好"
        ]

        print("\n📝 开始处理请求:")
        print("-" * 50)
        for query in test_queries:
            print(f"用户: {query}")
            result = await agent.process(query)
            if "response" in result:
                print(f"助手: {result['response']}")
            elif "error" in result:
                print(f"错误: {result['error']}")
            print()

        # 3. 显示运行统计
        metrics = agent.get_metrics()
        print(f"📊 运行统计: 处理了 {metrics['total_tasks']} 个请求")
        print(f"⏱️ 平均响应时间: {metrics['avg_response_time_ms']:.2f}ms")

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        print("详细信息:", traceback.format_exc())
    finally:
        await agent.shutdown()
        print("\n✅ 程序结束")


if __name__ == "__main__":
    try:
        # 添加事件循环策略（解决Windows兼容性问题）
        if sys.platform.startswith('win'):
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        # 运行主函数
        asyncio.run(main())

    except KeyboardInterrupt:
        print("\n👋 程序被中断")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
