"""Tests for E-commerce Demo 1: Smart Shopping Assistant (Product Recommendation)."""

import pytest
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from agent.coordinator import Coordinator
from agent.planner import ExecutionPlan


def create_mock_budget():
    """Create a fully mocked budget object."""
    budget = Mock()
    budget.total_limit = 100000
    budget.warning_threshold = 0.8
    budget.enable_compression = False
    budget.used = 0
    budget.total = 100000
    budget.usage_ratio = PropertyMock(return_value=0.0)
    budget.get_compression_ratio = Mock(return_value=0.0)
    budget.check_budget = Mock(return_value=True)
    budget.consume_tokens = Mock(return_value=None)
    budget.get_summary = Mock(return_value={"used": 0, "total": 10000})
    budget.can_compress = Mock(return_value=False)
    budget.reset = Mock(return_value=None)
    return budget


def create_mock_config():
    """Create a fully mocked configuration."""
    config = Mock()
    config.budget = create_mock_budget()
    config.execution = Mock()
    config.execution.enable_audit_log = True
    config.execution.confidence_threshold = 0.7
    config.execution.enable_replan = False
    config.llm = Mock()
    config.llm.provider = "openai"
    config.llm.api_key = "test_key"
    config.llm.model = "test_model"
    config.llm.base_url = None
    config.skills_dir = Mock()
    config.skills_dir.__str__ = Mock(return_value="/tmp/skills")
    return config


class TestEcommerceDemo1Recommendation:
    """Test product recommendation scenarios."""

    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        return create_mock_config()

    @pytest.fixture
    def coordinator(self, mock_config):
        """Create coordinator with mocked dependencies."""
        with patch('agent.coordinator.LLMClient'), \
             patch('agent.coordinator.SkillRegistry'), \
             patch.object(Coordinator, '_create_llm_provider') as mock_create_provider:
            # Create mock LLM provider
            mock_provider = Mock()
            mock_create_provider.return_value = mock_provider

            coord = Coordinator(mock_config)
            # Replace the budget with our mock
            coord.llm_client.budget = create_mock_budget()
            return coord

    def test_rec001_explicit_requirement_recommendation(self, coordinator):
        """
        REC-001: 明确需求推荐

        用户输入: "我想买个2000元左右的手机，主要拍照用"
        期望: 推荐拍照手机Top5，包含推荐理由
        """
        # Mock planner to generate recommendation plan with ExecutionPlan object
        mock_plan = ExecutionPlan(
            intent="拍照手机推荐",
            steps=[
                {"skill": "demand_analysis", "sub_task": "分析用户需求：手机、2000元、拍照"},
                {"skill": "user_profiling", "sub_task": "获取用户画像"},
                {"skill": "product_search", "sub_task": "搜索拍照手机，价格1500-2500"},
                {"skill": "recommendation_ranking", "sub_task": "按拍照能力排序"},
                {"skill": "recommendation_explanation", "sub_task": "生成推荐理由"}
            ]
        )
        coordinator.planner.generate_plan = MagicMock(return_value=mock_plan)

        # Mock skill execution results - use execute method
        coordinator.executor.execute = MagicMock(side_effect=[
            {
                "success": True,
                "structured": {
                    "category": "手机",
                    "constraints": {"price_range": [1500, 2500], "priority": "拍照"}
                },
                "text": "已分析用户需求"
            },
            {
                "success": True,
                "structured": {
                    "user_profile": {
                        "preferred_brands": ["华为", "小米"],
                        "price_preference": "中端"
                    }
                },
                "text": "已获取用户画像"
            },
            {
                "success": True,
                "structured": {
                    "products": [
                        {"product_id": "p001", "name": "华为Nova 11", "price": 1999, "camera_score": 9.2},
                        {"product_id": "p002", "name": "小米Civi 3", "price": 2299, "camera_score": 9.0},
                    ]
                },
                "text": "已搜索商品"
            },
            {
                "success": True,
                "structured": {
                    "ranked_products": [
                        {"rank": 1, "product_id": "p001", "name": "华为Nova 11", "score": 0.92},
                        {"rank": 2, "product_id": "p002", "name": "小米Civi 3", "score": 0.88}
                    ]
                },
                "text": "已排序商品"
            },
            {
                "success": True,
                "structured": {"response_type": "recommendation"},
                "text": "根据您的需求，为您推荐以下拍照手机：\n\n1. 华为Nova 11 (¥1999)\n   - 5000万超感光主摄，拍照效果出色\n   - 人像拍摄专业，适合日常拍照\n\n2. 小米Civi 3 (¥2299)\n   - 前置仿生双主摄，自拍效果优秀"
            }
        ])

        coordinator.synthesizer.synthesize = MagicMock(return_value=
            "根据您的需求，为您推荐以下拍照手机：\n\n1. 华为Nova 11 (¥1999)\n   - 5000万超感光主摄，拍照效果出色\n\n2. 小米Civi 3 (¥2299)\n   - 前置仿生双主摄，自拍效果优秀"
        )

        result = coordinator.process("我想买个2000元左右的手机，主要拍照用")

        assert "final_response" in result
        assert "拍照" in result["final_response"]
        # Verify all 5 skills were executed
        assert coordinator.executor.execute.call_count == 5

    def test_rec002_vague_requirement_clarification(self, coordinator):
        """
        REC-002: 模糊需求引导

        用户输入: "我想买个好东西"
        期望: 询问具体类别、预算、用途
        """
        mock_plan = ExecutionPlan(
            intent="需求引导",
            steps=[
                {"skill": "demand_analysis", "sub_task": "引导用户明确需求"}
            ]
        )
        coordinator.planner.generate_plan = MagicMock(return_value=mock_plan)

        coordinator.executor.execute = MagicMock(return_value={
            "success": True,
            "structured": {
                "missing_info": ["category", "budget", "use_case"],
                "dialogue_state": "awaiting_clarification"
            },
            "text": "好的，我很乐意帮您推荐！请问您想买什么类型的商品呢？比如手机、电脑、耳机等。您的预算大概是多少？主要用途是什么？"
        })

        coordinator.synthesizer.synthesize = MagicMock(
            return_value="好的，我很乐意帮您推荐！请问您想买什么类型的商品呢？比如手机、电脑、耳机等。您的预算大概是多少？主要用途是什么？"
        )

        result = coordinator.process("我想买个好东西")

        # Check for key phrases that indicate clarification is needed
        assert any(phrase in result["final_response"] for phrase in ["类别", "类型", "什么商品", "买什么"])
        assert "预算" in result["final_response"]

    def test_rec003_multi_turn_dialogue(self, coordinator):
        """
        REC-003: 多轮对话

        第一轮: "推荐手机"
        第二轮: "2000左右，玩游戏"
        期望: 第二轮返回游戏手机推荐
        """
        # First turn - vague request
        mock_plan1 = ExecutionPlan(
            intent="手机推荐",
            steps=[
                {"skill": "demand_analysis", "sub_task": "收集更多信息"}
            ]
        )
        coordinator.planner.generate_plan = MagicMock(return_value=mock_plan1)

        coordinator.executor.execute = MagicMock(return_value={
            "success": True,
            "structured": {"dialogue_state": "awaiting_constraints"},
            "text": "好的，为您推荐手机。请问您的预算大概多少？主要用途是什么？比如玩游戏、拍照、办公等。"
        })

        coordinator.synthesizer.synthesize = MagicMock(
            return_value="好的，为您推荐手机。请问您的预算大概多少？主要用途是什么？"
        )

        result1 = coordinator.process("推荐手机")

        assert "预算" in result1["final_response"]

        # Second turn - with constraints
        mock_plan2 = ExecutionPlan(
            intent="游戏手机推荐",
            steps=[
                {"skill": "demand_analysis", "sub_task": "分析需求：手机、2000元、游戏"},
                {"skill": "product_search", "sub_task": "搜索游戏手机"},
                {"skill": "recommendation_ranking", "sub_task": "按游戏性能排序"}
            ]
        )
        coordinator.planner.generate_plan = MagicMock(return_value=mock_plan2)

        coordinator.executor.execute = MagicMock(side_effect=[
            {
                "success": True,
                "structured": {"constraints": {"price_range": [1800, 2200], "use_case": "gaming"}},
                "text": "已分析需求"
            },
            {
                "success": True,
                "structured": {"products": [{"name": "Redmi K70", "price": 1999, "performance_score": 9.5}]},
                "text": "已搜索商品"
            },
            {
                "success": True,
                "structured": {"ranked_products": [{"rank": 1, "name": "Redmi K70"}]},
                "text": "已排序"
            }
        ])

        coordinator.synthesizer.synthesize = MagicMock(
            return_value="根据您的需求，推荐 Redmi K70 (¥1999)，搭载骁龙8 Gen2，游戏性能出色。"
        )

        result2 = coordinator.process("2000左右，玩游戏")

        assert "游戏" in result2["final_response"] or "性能" in result2["final_response"]

    def test_rec004_product_comparison(self, coordinator):
        """
        REC-004: 商品对比

        用户输入: "Redmi K70和iQOO Neo9哪个好"
        期望: 对比两款手机的优缺点
        """
        mock_plan = ExecutionPlan(
            intent="商品对比",
            steps=[
                {"skill": "product_comparison", "sub_task": "对比 Redmi K70 和 iQOO Neo9"}
            ]
        )
        coordinator.planner.generate_plan = MagicMock(return_value=mock_plan)

        coordinator.executor.execute = MagicMock(return_value={
            "success": True,
            "structured": {
                "comparison": [
                    {"dimension": "屏幕", "k70": "2K 120Hz", "neo9": "1.5K 144Hz"},
                    {"dimension": "处理器", "k70": "骁龙8 Gen2", "neo9": "骁龙8 Gen2"},
                    {"dimension": "价格", "k70": "¥2499", "neo9": "¥2299"}
                ]
            },
            "text": "Redmi K70 和 iQOO Neo9 对比如下：\n\n屏幕: K70的2K分辨率更清晰，Neo9的144Hz刷新率更流畅\n处理器: 两者都是骁龙8 Gen2，性能相当\n价格: Neo9便宜200元，性价比更高"
        })

        coordinator.synthesizer.synthesize = MagicMock(
            return_value="Redmi K70 和 iQOO Neo9 对比如下：\n\n屏幕: K70的2K分辨率更清晰，Neo9的144Hz刷新率更流畅\n处理器: 两者都是骁龙8 Gen2，性能相当\n价格: Neo9便宜200元，性价比更高"
        )

        result = coordinator.process("Redmi K70和iQOO Neo9哪个好")

        assert "对比" in result["final_response"] or "K70" in result["final_response"]

    def test_rec005_price_filter(self, coordinator):
        """
        REC-005: 价格筛选

        用户输入: "1000元以下的耳机推荐"
        期望: 返回符合预算的耳机列表
        """
        mock_plan = ExecutionPlan(
            intent="价格筛选",
            steps=[
                {"skill": "product_search", "sub_task": "搜索1000元以下耳机"}
            ]
        )
        coordinator.planner.generate_plan = MagicMock(return_value=mock_plan)

        coordinator.executor.execute = MagicMock(return_value={
            "success": True,
            "structured": {
                "products": [
                    {"name": "小米蓝牙耳机", "price": 299},
                    {"name": "华为FreeBuds", "price": 599}
                ],
                "total_found": 15
            },
            "text": "为您找到15款1000元以下的耳机，推荐：\n1. 小米蓝牙耳机 (¥299)\n2. 华为FreeBuds (¥599)"
        })

        coordinator.synthesizer.synthesize = MagicMock(
            return_value="为您找到15款1000元以下的耳机，推荐：\n1. 小米蓝牙耳机 (¥299)\n2. 华为FreeBuds (¥599)"
        )

        result = coordinator.process("1000元以下的耳机推荐")

        assert "耳机" in result["final_response"]

    def test_rec006_brand_preference(self, coordinator):
        """
        REC-006: 品牌偏好

        用户输入: "华为的手机有什么好推荐"
        期望: 推荐华为手机，体现品牌偏好
        """
        mock_plan = ExecutionPlan(
            intent="品牌筛选",
            steps=[
                {"skill": "product_search", "sub_task": "搜索华为手机"}
            ]
        )
        coordinator.planner.generate_plan = MagicMock(return_value=mock_plan)

        coordinator.executor.execute = MagicMock(return_value={
            "success": True,
            "structured": {
                "products": [
                    {"name": "华为Mate 60", "price": 5999},
                    {"name": "华为Nova 11", "price": 1999}
                ],
                "brand_filtered": True
            },
            "text": "为您推荐以下华为手机：\n1. 华为Mate 60 (¥5999) - 旗舰机型\n2. 华为Nova 11 (¥1999) - 中端拍照"
        })

        coordinator.synthesizer.synthesize = MagicMock(
            return_value="为您推荐以下华为手机：\n1. 华为Mate 60 (¥5999) - 旗舰机型\n2. 华为Nova 11 (¥1999) - 中端拍照"
        )

        result = coordinator.process("华为的手机有什么好推荐")

        assert "华为" in result["final_response"]

    def test_rec007_no_results_handling(self, coordinator):
        """
        REC-007: 无结果处理

        用户输入: "推荐99999元的手机"
        期望: 友好提示无符合商品，给出建议
        """
        mock_plan = ExecutionPlan(
            intent="无结果处理",
            steps=[
                {"skill": "product_search", "sub_task": "搜索99999元手机"}
            ]
        )
        coordinator.planner.generate_plan = MagicMock(return_value=mock_plan)

        coordinator.executor.execute = MagicMock(return_value={
            "success": True,
            "structured": {"products": [], "total_found": 0},
            "text": "抱歉，没有找到价格99999元的手机。您的预算是否可以调整一下？或者告诉我您的具体需求，我为您推荐其他价位的手机。"
        })

        coordinator.synthesizer.synthesize = MagicMock(
            return_value="抱歉，没有找到价格99999元的手机。您的预算是否可以调整一下？"
        )

        result = coordinator.process("推荐99999元的手机")

        # Should provide helpful suggestion
        assert "没有" in result["final_response"] or "抱歉" in result["final_response"]


class TestEcommerceDemo1ContextManagement:
    """Test context management in multi-turn conversations."""

    @pytest.fixture
    def coordinator(self):
        """Create coordinator for context testing."""
        config = Mock()
        config.budget.total_limit = 100000
        config.budget.warning_threshold = 0.8
        config.budget.enable_compression = False
        config.execution.enable_audit_log = True
        config.execution.confidence_threshold = 0.7
        config.execution.enable_replan = False
        config.llm.provider = "openai"
        config.llm.api_key = "test_key"
        config.llm.model = "test_model"
        config.llm.base_url = None
        config.skills_dir = Mock()
        config.skills_dir.__str__ = Mock(return_value="/tmp/skills")

        with patch('agent.coordinator.LLMClient'), \
             patch('agent.coordinator.SkillRegistry'), \
             patch.object(Coordinator, '_create_llm_provider') as mock_create_provider:
            # Create mock LLM provider
            mock_provider = Mock()
            mock_create_provider.return_value = mock_provider
            return Coordinator(config)

    def test_rec008_context_aware_response(self, coordinator):
        """
        REC-008: 上下文保持

        多轮对话中引用之前内容
        期望: 正确理解并回应
        """
        # Turn 1: User asks about phones
        mock_plan1 = ExecutionPlan(
            intent="手机推荐",
            steps=[
                {"skill": "demand_analysis", "sub_task": "收集手机需求"}
            ]
        )
        coordinator.planner.generate_plan = MagicMock(return_value=mock_plan1)

        coordinator.executor.execute = MagicMock(return_value={
            "success": True,
            "structured": {},
            "text": "好的，为您推荐手机。请问预算多少？"
        })

        coordinator.synthesizer.synthesize = MagicMock(
            return_value="好的，为您推荐手机。请问预算多少？"
        )

        result1 = coordinator.process("推荐手机")

        # Turn 2: User says "那个2000的" (referring to previous context)
        mock_plan2 = ExecutionPlan(
            intent="上下文推荐",
            steps=[
                {"skill": "product_search", "sub_task": "搜索2000元手机"}
            ]
        )
        coordinator.planner.generate_plan = MagicMock(return_value=mock_plan2)

        coordinator.executor.execute = MagicMock(return_value={
            "success": True,
            "structured": {
                "products": [{"name": "Redmi K70", "price": 1999}]
            },
            "text": "为您推荐 Redmi K70，售价1999元。"
        })

        coordinator.synthesizer.synthesize = MagicMock(
            return_value="为您推荐 Redmi K70，售价1999元。"
        )

        result2 = coordinator.process("那个2000的")

        # Should understand the reference to 2000 yuan from context
        assert "2000" in result2["final_response"] or "1999" in result2["final_response"]
