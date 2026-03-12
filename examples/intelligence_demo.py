"""
智能增强模块演示

展示语义理解层和对话记忆系统的使用
"""

import sys
sys.path.insert(0, '/home/fhammer/workspace/agent-skills-exec')

from agent.intelligence import create_semantic_layer, IntentClassifier, SlotFiller
from agent.intelligence.slot_filler import SlotDefinition, SlotType
from agent.memory import create_working_memory, create_user_profile_manager


def demo_intent_classifier():
    """演示意图分类器"""
    print("=" * 60)
    print("演示1: 意图分类器")
    print("=" * 60)

    # 创建分类器（无LLM，使用基于规则的分类）
    classifier = IntentClassifier(llm_client=None)

    # 注册一些意图定义
    classifier.register_intent(
        name="parse_report",
        description="解析报告文件",
        examples=["帮我解析报告", "分析报告内容", "处理这个报告"]
    )

    classifier.register_intent(
        name="assess_risk",
        description="风险评估",
        examples=["评估风险", "风险分析", "检查风险"]
    )

    # 测试用例
    test_inputs = [
        "你好",
        "帮我解析这份报告",
        "分析一下风险",
        "再见",
        "这个我不明白"
    ]

    for user_input in test_inputs:
        result = classifier.classify(user_input)

        print(f"\n用户输入: {user_input}")
        if result.primary_intent:
            print(f"  主意图: {result.primary_intent.name} (置信度: {result.primary_intent.confidence:.2f})")
        if result.secondary_intents:
            print(f"  次要意图: {', '.join(i.name for i in result.secondary_intents)}")
        if result.clarification_needed:
            print(f"  需要澄清: {result.clarification_question}")


def demo_slot_filler():
    """演示槽位填充器"""
    print("\n" + "=" * 60)
    print("演示2: 槽位填充器")
    print("=" * 60)

    # 创建填充器
    filler = SlotFiller(llm_client=None)

    # 注册槽位定义
    filler.register_slot(SlotDefinition(
        name="date",
        description="日期",
        slot_type=SlotType.DATE,
        required=True
    ))

    filler.register_slot(SlotDefinition(
        name="location",
        description="地点",
        slot_type=SlotType.STRING,
        required=True
    ))

    filler.register_slot(SlotDefinition(
        name="count",
        description="数量",
        slot_type=SlotType.INTEGER,
        required=False,
        default_value=1
    ))

    # 测试用例
    test_cases = [
        "2024-03-15在北京开会",
        "2024-06-01在上海举办活动，参加人数50",
        "明天要去深圳"  # 缺少日期
    ]

    for user_input in test_cases:
        result = filler.fill_slots(user_input)

        print(f"\n用户输入: {user_input}")
        print(f"  提取的槽位:")
        for name, slot in result.slots.items():
            if slot.value is not None:
                print(f"    {name}: {slot.value} (来源: {slot.source})")

        if result.missing_required:
            print(f"  缺失的必填槽位: {result.missing_required}")

        if result.invalid_slots:
            print(f"  无效的槽位: {result.invalid_slots}")

        if result.follow_up_questions:
            print(f"  后续问题:")
            for q in result.follow_up_questions:
                print(f"    - {q}")


def demo_semantic_layer():
    """演示语义理解层"""
    print("\n" + "=" * 60)
    print("演示3: 语义理解层（整合）")
    print("=" * 60)

    # 创建语义理解层
    semantic_layer = create_semantic_layer(llm_client=None)

    # 注册一些槽位
    from agent.intelligence.slot_filler import SlotDefinition, SlotType
    semantic_layer.register_intent_slots("parse_report", [
        SlotDefinition(name="file_path", description="文件路径", required=True),
        SlotDefinition(name="format", description="输出格式", required=False, default_value="json")
    ])

    # 测试用例
    test_inputs = [
        "你好",
        "帮我解析 /tmp/report.pdf 文件",
        "分析一下风险",
        "我不太明白"
    ]

    for user_input in test_inputs:
        result = semantic_layer.understand(user_input)

        print(f"\n用户输入: {user_input}")
        print(f"  意图: {result.intent.name if result.intent else 'None'} "
              f"(置信度: {result.intent_confidence:.2f})")
        print(f"  槽位: {result.slots}")
        print(f"  缺失槽位: {result.missing_slots}")
        print(f"  需要澄清: {result.clarification_needed}")
        print(f"  是否清晰: {result.is_clear()}")


def demo_working_memory():
    """演示工作记忆"""
    print("\n" + "=" * 60)
    print("演示4: 工作记忆")
    print("=" * 60)

    # 创建工作记忆
    wm = create_working_memory(session_id="demo_session")

    # 模拟对话
    print("\n模拟对话:")

    wm.add_user_message("你好，我想分析报告")
    wm.set_current_intent("parse_report")
    print("  用户: 你好，我想分析报告")

    wm.add_assistant_message("好的，请提供报告文件路径")
    print("  助手: 好的，请提供报告文件路径")

    wm.add_user_message("文件在 /tmp/report.pdf")
    wm.confirm_information("file_path", "/tmp/report.pdf")
    print("  用户: 文件在 /tmp/report.pdf")

    # 显示对话历史
    print("\n对话历史:")
    for turn in wm.get_history():
        role = "用户" if turn.role == "user" else "助手"
        print(f"  [{role}] {turn.content}")

    # 显示当前状态
    print(f"\n当前意图: {wm.context.current_intent}")
    print(f"已确认信息: {wm.get_confirmed_info()}")

    # 显示摘要
    print(f"\n对话摘要:\n{wm.get_conversation_summary()}")


def demo_user_profile():
    """演示用户画像"""
    print("\n" + "=" * 60)
    print("演示5: 用户画像")
    print("=" * 60)

    # 创建用户画像管理器
    manager = create_user_profile_manager()

    # 创建用户画像
    user_id = "user_demo_001"
    profile = manager.get_profile(user_id)

    # 设置基本信息
    profile.display_name = "张三"
    profile.email = "zhangsan@example.com"

    # 设置偏好
    profile.set_preference(
        key="theme",
        value="dark",
        confidence=0.95,
        source="explicit"
    )
    profile.set_preference(
        key="language",
        value="zh-CN",
        confidence=1.0,
        source="explicit"
    )
    profile.set_preference(
        key="notifications",
        value=True,
        confidence=0.8,
        source="implicit"
    )

    # 添加标签
    profile.add_tag("premium_user")
    profile.add_tag("early_adopter")

    # 添加行为模式
    pattern = BehaviorPattern(
        pattern_id="weekly_report",
        pattern_type="temporal",
        description="每周查看报告",
        confidence=0.85,
        occurrence_count=10
    )
    profile.add_behavior_pattern(pattern)

    # 记录交互
    profile.record_session_start()
    profile.record_message("user")
    profile.record_message("assistant")
    profile.stats.record_response_time(1.5)

    # 保存画像
    manager.save_profile(profile)

    # 显示画像信息
    print(f"\n用户画像: {profile.user_id}")
    print(f"  显示名称: {profile.display_name}")
    print(f"  邮箱: {profile.email}")

    print(f"\n偏好设置:")
    for key, pref in profile.preferences.items():
        print(f"  {key}: {pref.value} (置信度: {pref.confidence:.2f}, 来源: {pref.source})")

    print(f"\n标签: {', '.join(profile.tags)}")

    print(f"\n行为模式:")
    for pid, pattern in profile.behavior_patterns.items():
        print(f"  {pattern.description} (置信度: {pattern.confidence:.2f}, 出现次数: {pattern.occurrence_count})")

    print(f"\n交互统计:")
    print(f"  总会话数: {profile.stats.total_sessions}")
    print(f"  总消息数: {profile.stats.total_messages}")
    print(f"  平均响应时间: {profile.stats.get_average_response_time():.2f}秒")

    # 测试查找
    print(f"\n通过标签查找premium_user:")
    results = manager.find_profiles_by_tag("premium_user")
    print(f"  找到 {len(results)} 个用户")


def demo_memory_manager():
    """演示记忆管理器"""
    print("\n" + "=" * 60)
    print("演示6: 记忆管理器")
    print("=" * 60)

    # 创建记忆管理器
    manager = create_memory_manager()

    # 添加各种类型的记忆
    print("\n添加记忆:")

    # 事实型记忆
    fact = manager.add_memory(
        content="用户的名字是张三",
        memory_type=MemoryType.FACT,
        importance=MemoryImportance.HIGH,
        tags={"user_info", "name"}
    )
    print(f"  [FACT] {fact.content[:30]}...")

    # 偏好型记忆
    preference = manager.add_memory(
        content="用户偏好深色主题",
        memory_type=MemoryType.PREFERENCE,
        importance=MemoryImportance.MEDIUM,
        tags={"user_info", "preference", "theme"}
    )
    print(f"  [PREFERENCE] {preference.content[:30]}...")

    # 事件型记忆
    event = manager.add_memory(
        content="用户于2024-03-15完成了一次报告分析",
        memory_type=MemoryType.EVENT,
        importance=MemoryImportance.HIGH,
        tags={"history", "report"}
    )
    print(f"  [EVENT] {event.content[:30]}...")

    # 添加更多记忆以测试压缩
    print("\n添加更多记忆用于测试...")
    for i in range(10):
        manager.add_memory(
            content=f"记忆条目 {i}: 这是一个测试记忆",
            memory_type=MemoryType.FACT,
            importance=MemoryImportance.LOW,
            tags={"test"}
        )

    # 关键词搜索
    print("\n关键词搜索 '用户':")
    results = manager.search_by_keywords(["用户"])
    for entry in results[:3]:
        print(f"  - {entry.content[:40]}... (重要性: {entry.importance.name})")

    # 标签搜索
    print("\n标签搜索 'user_info':")
    results = manager.search_by_tags({"user_info"})
    for entry in results:
        print(f"  - {entry.content}")

    # 显示记忆统计
    print(f"\n记忆统计:")
    print(f"  总记忆数: {len(manager._memories)}")
    print(f"  按类型分布:")
    for mem_type, ids in manager._index_by_type.items():
        print(f"    {mem_type.value}: {len(ids)}")

    # 测试访问和保留分数
    print("\n测试记忆访问:")
    fact.access()
    print(f"  记忆 '{fact.content[:20]}...' 访问次数: {fact.access_count}")

    # 更新保留分数
    fact.update_retention_score()
    print(f"  保留分数: {fact.retention_score:.2f}")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("智能增强模块演示")
    print("=" * 60)

    # 运行所有演示
    demo_intent_classifier()
    demo_slot_filler()
    demo_semantic_layer()
    demo_working_memory()
    demo_user_profile()
    demo_memory_manager()

    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()