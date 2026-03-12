"""
智能增强模块与现有框架集成示例

展示如何将语义理解层和对话记忆系统集成到现有的Agent框架中
"""

import sys
sys.path.insert(0, '/home/fhammer/workspace/agent-skills-exec')

from agent.intelligence import create_semantic_layer, SlotDefinition, SlotType
from agent.memory import create_working_memory, create_user_profile_manager


class EnhancedPlanner:
    """
    增强型Planner，集成语义理解层

    扩展原有Planner，添加语义理解和对话记忆能力
    """

    def __init__(self, llm_client=None, config=None):
        self.config = config or {}
        self.llm_client = llm_client

        # 初始化语义理解层
        self.semantic_layer = create_semantic_layer(llm_client, config)

        # 初始化工作记忆
        self.working_memory = create_working_memory()

        # 用户画像管理器
        self.profile_manager = create_user_profile_manager()

        # 可用技能
        self.available_skills = []

    def register_skill(self, skill_name: str, slot_definitions=None):
        """注册技能及其槽位定义"""
        self.available_skills.append(skill_name)

        if slot_definitions:
            self.semantic_layer.register_intent_slots(skill_name, slot_definitions)

    def plan(self, user_input: str, user_id: str = None) -> dict:
        """
        执行智能规划

        1. 语义理解
        2. 对话记忆更新
        3. 生成执行计划
        """
        # 1. 语义理解
        semantic_result = self.semantic_layer.understand(
            user_input,
            conversation_context={
                "history": [
                    {"role": t.role, "content": t.content}
                    for t in self.working_memory.get_history()
                ]
            },
            available_skills=self.available_skills
        )

        # 2. 更新工作记忆
        turn = self.working_memory.add_user_message(
            user_input,
            intent=semantic_result.intent.name if semantic_result.intent else None,
            extracted_slots=semantic_result.slots
        )

        # 3. 更新用户画像（如果有用户ID）
        if user_id:
            profile = self.profile_manager.get_profile(user_id)
            profile.record_message("user")

            # 提取和记录偏好
            if "theme" in semantic_result.slots:
                profile.set_preference("theme", semantic_result.slots["theme"])

            self.profile_manager.save_profile(profile)

        # 4. 生成执行计划
        plan = self._create_execution_plan(semantic_result)

        return {
            "plan": plan,
            "semantic_result": semantic_result,
            "requires_clarification": semantic_result.clarification_needed,
            "clarification_question": semantic_result.clarification_question
        }

    def _create_execution_plan(self, semantic_result) -> dict:
        """创建执行计划"""
        if not semantic_result.intent:
            return {
                "action": "request_clarification",
                "reason": "无法确定用户意图"
            }

        if semantic_result.clarification_needed:
            return {
                "action": "request_clarification",
                "question": semantic_result.clarification_question
            }

        # 创建技能执行计划
        return {
            "action": "execute_skill",
            "skill": semantic_result.intent.name,
            "parameters": semantic_result.slots,
            "confidence": semantic_result.intent_confidence
        }

    def get_conversation_summary(self) -> str:
        """获取对话摘要"""
        return self.working_memory.get_conversation_summary()


def demo_integration():
    """演示集成"""
    print("=" * 70)
    print("智能增强模块与现有框架集成演示")
    print("=" * 70)

    # 创建增强型Planner
    planner = EnhancedPlanner()

    # 注册技能
    planner.register_skill("parse_report", [
        SlotDefinition(name="file_path", description="报告文件路径", required=True),
        SlotDefinition(name="format", description="输出格式", slot_type=SlotType.ENUM,
                      enum_values=["json", "markdown", "text"], required=False, default_value="json")
    ])

    planner.register_skill("assess_risk", [
        SlotDefinition(name="risk_type", description="风险类型", required=False),
        SlotDefinition(name="severity", description="严重程度", slot_type=SlotType.ENUM,
                      enum_values=["low", "medium", "high"], required=False)
    ])

    planner.register_skill("generate_advice", [
        SlotDefinition(name="topic", description="建议主题", required=True),
        SlotDefinition(name="detail_level", description="详细程度", required=False, default_value="medium")
    ])

    # 模拟对话
    print("\n开始模拟对话...\n")

    test_inputs = [
        "你好",
        "帮我解析 /tmp/annual_report.pdf 文件",
        "分析一下风险",
        "给我一些投资建议",
        "我不太明白"
    ]

    for i, user_input in enumerate(test_inputs, 1):
        print(f"--- 回合 {i} ---")
        print(f"用户: {user_input}")

        # 执行规划
        result = planner.plan(user_input, user_id="demo_user")

        # 显示语义理解结果
        semantic = result["semantic_result"]
        print(f"  [理解] 意图: {semantic.intent.name if semantic.intent else 'None'} "
              f"(置信度: {semantic.intent_confidence:.2f})")
        print(f"  [理解] 槽位: {semantic.slots}")

        # 显示执行计划
        plan = result["plan"]
        print(f"  [计划] 动作: {plan['action']}")
        if "skill" in plan:
            print(f"  [计划] 技能: {plan['skill']}")
            print(f"  [计划] 参数: {plan['parameters']}")
        if "question" in plan:
            print(f"  [计划] 澄清问题: {plan['question']}")

        # 模拟助手回复
        if result["requires_clarification"]:
            response = result["clarification_question"]
        elif plan["action"] == "execute_skill":
            response = f"好的，我将执行 {plan['skill']} 技能。"
        else:
            response = "收到，请继续。"

        print(f"助手: {response}")
        print()

    # 显示对话摘要
    print("=" * 70)
    print("对话摘要:")
    print(planner.get_conversation_summary())
    print("=" * 70)


if __name__ == "__main__":
    demo_integration()