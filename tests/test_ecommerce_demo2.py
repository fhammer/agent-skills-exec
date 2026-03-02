"""Tests for E-commerce Demo 2: Order Processing and After-sales Service."""

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


class TestEcommerceDemo2OrderQuery:
    """Test order query scenarios."""

    @pytest.fixture
    def coordinator(self):
        """Create coordinator for testing."""
        config = create_mock_config()

        with patch('agent.coordinator.LLMClient'), \
             patch('agent.coordinator.SkillRegistry'), \
             patch.object(Coordinator, '_create_llm_provider') as mock_create_provider:
            # Create mock LLM provider
            mock_provider = Mock()
            mock_create_provider.return_value = mock_provider

            coord = Coordinator(config)
            # Replace the budget with our mock
            coord.llm_client.budget = create_mock_budget()
            return coord

    def test_ord001_query_recent_orders(self, coordinator):
        """
        ORD-001: 查询最近订单

        用户输入: "查一下我的订单"
        期望: 返回最近一笔订单详情
        """
        mock_plan = ExecutionPlan(
            intent="查询订单",
            steps=[
                {"skill": "order_query", "sub_task": "查询最近订单"}
            ]
        )
        coordinator.planner.generate_plan = MagicMock(return_value=mock_plan)

        coordinator.executor.execute = MagicMock(return_value={
            "success": True,
            "structured": {
                "query_type": "recent_orders",
                "total_orders": 5,
                "orders": [
                    {
                        "order_id": "20240228123456",
                        "status": "shipped",
                        "status_text": "已发货",
                        "create_time": "2024-02-28 10:30:00",
                        "total_amount": 2499.00,
                        "items": [
                            {"name": "Redmi K70", "quantity": 1, "price": 2499.00}
                        ],
                        "logistics": {
                            "company": "顺丰速运",
                            "tracking_no": "SF1234567890",
                            "estimated_delivery": "2024-03-01"
                        }
                    }
                ]
            },
            "text": "您最近一笔订单信息如下：\n订单号：20240228123456\n商品：Redmi K70\n状态：已发货\n物流：顺丰速运 SF1234567890\n预计送达：3月1日"
        })

        coordinator.synthesizer.synthesize = MagicMock(
            return_value="您最近一笔订单信息如下：\n订单号：20240228123456\n商品：Redmi K70\n状态：已发货\n物流：顺丰速运 SF1234567890\n预计送达：3月1日"
        )

        result = coordinator.process("查一下我的订单")

        assert "订单号" in result["final_response"]
        assert "20240228123456" in result["final_response"]

    def test_ord002_query_by_order_id(self, coordinator):
        """
        ORD-002: 按订单号查询

        用户输入: "订单 20240228123456"
        期望: 返回指定订单详情
        """
        mock_plan = ExecutionPlan(
            intent="查询订单",
            steps=[
                {"skill": "order_query", "sub_task": "查询订单 20240228123456"}
            ]
        )
        coordinator.planner.generate_plan = MagicMock(return_value=mock_plan)

        coordinator.executor.execute = MagicMock(return_value={
            "success": True,
            "structured": {
                "order_id": "20240228123456",
                "status": "shipped",
                "items": [{"name": "Redmi K70", "price": 2499}],
                "logistics": {
                    "company": "顺丰速运",
                    "tracking_no": "SF1234567890"
                }
            },
            "text": "订单 20240228123456 详情：\n商品：Redmi K70 (¥2499)\n状态：已发货\n物流：顺丰速运，运单号 SF1234567890"
        })

        coordinator.synthesizer.synthesize = MagicMock(
            return_value="订单 20240228123456 详情：\n商品：Redmi K70 (¥2499)\n状态：已发货"
        )

        result = coordinator.process("订单 20240228123456")

        assert "20240228123456" in result["final_response"]

    def test_ord003_query_logistics(self, coordinator):
        """
        ORD-003: 查询物流

        用户输入: "我的快递到哪了"
        期望: 返回物流轨迹和预计送达时间
        """
        mock_plan = ExecutionPlan(
            intent="查询物流",
            steps=[
                {"skill": "order_query", "sub_task": "查询物流信息"}
            ]
        )
        coordinator.planner.generate_plan = MagicMock(return_value=mock_plan)

        coordinator.executor.execute = MagicMock(return_value={
            "success": True,
            "structured": {
                "order_id": "20240228123456",
                "logistics": {
                    "company": "顺丰速运",
                    "tracking_no": "SF1234567890",
                    "status": "in_transit",
                    "tracks": [
                        {"time": "2024-02-28 10:30", "status": "已发货", "location": "北京仓"},
                        {"time": "2024-02-29 08:30", "status": "运输中", "location": "北京转运中心"}
                    ],
                    "estimated_delivery": "2024-03-01"
                }
            },
            "text": "您的订单物流信息：\n2月28日 10:30 - 北京仓已发货\n2月29日 08:30 - 到达北京转运中心\n预计 3月1日 派送"
        })

        coordinator.synthesizer.synthesize = MagicMock(
            return_value="您的订单物流信息：\n2月28日 10:30 - 北京仓已发货\n2月29日 08:30 - 到达北京转运中心\n预计 3月1日 派送"
        )

        result = coordinator.process("我的快递到哪了")

        assert "物流" in result["final_response"] or "快递" in result["final_response"]

    def test_ord004_order_not_found(self, coordinator):
        """
        ORD-004: 订单不存在

        用户输入: "查询订单 999999999"
        期望: 友好提示订单不存在
        """
        mock_plan = ExecutionPlan(
            intent="查询订单",
            steps=[
                {"skill": "order_query", "sub_task": "查询订单 999999999"}
            ]
        )
        coordinator.planner.generate_plan = MagicMock(return_value=mock_plan)

        coordinator.executor.execute = MagicMock(return_value={
            "success": True,
            "structured": {"found": False},
            "text": "抱歉，未找到订单 999999999。请检查订单号是否正确，或者我可以帮您查询最近的订单。"
        })

        coordinator.synthesizer.synthesize = MagicMock(
            return_value="抱歉，未找到订单 999999999。请检查订单号是否正确。"
        )

        result = coordinator.process("查询订单 999999999")

        assert "未找到" in result["final_response"] or "不存在" in result["final_response"]


class TestEcommerceDemo2ReturnExchange:
    """Test return and exchange scenarios."""

    @pytest.fixture
    def coordinator(self):
        """Create coordinator for testing."""
        config = create_mock_config()

        with patch('agent.coordinator.LLMClient'), \
             patch('agent.coordinator.SkillRegistry'), \
             patch.object(Coordinator, '_create_llm_provider') as mock_create_provider:
            # Create mock LLM provider
            mock_provider = Mock()
            mock_create_provider.return_value = mock_provider

            coord = Coordinator(config)
            # Replace the budget with our mock
            coord.llm_client.budget = create_mock_budget()
            return coord

    def test_ret001_return_quality_issue(self, coordinator):
        """
        RET-001: 退货-质量问题

        用户输入: "这个手机有问题，屏幕有坏点"
        期望: 创建退货单，告知退货运费政策
        """
        mock_plan = ExecutionPlan(
            intent="退货申请",
            steps=[
                {"skill": "intent_classification", "sub_task": "识别退货意图"},
                {"skill": "policy_validation", "sub_task": "验证退货政策"},
                {"skill": "case_creation", "sub_task": "创建退货单"}
            ]
        )
        coordinator.planner.generate_plan = MagicMock(return_value=mock_plan)

        coordinator.executor.execute = MagicMock(side_effect=[
            {
                "success": True,
                "structured": {"intent": "return", "reason": "quality_issue"},
                "text": "已识别退货意图"
            },
            {
                "success": True,
                "structured": {
                    "eligible": True,
                    "return_type": "free_return",
                    "reason": "质量问题支持免费退货"
                },
                "text": "已验证退货政策"
            },
            {
                "success": True,
                "structured": {
                    "case_id": "RET20240228001",
                    "status": "approved",
                    "shipping_info": "商家承担运费"
                },
                "text": "已创建退货单"
            }
        ])

        coordinator.synthesizer.synthesize = MagicMock(
            return_value="已为您创建退货单 RET20240228001。由于是质量问题，商家将承担退货运费。稍后会有客服联系您安排退货事宜。"
        )

        result = coordinator.process("这个手机有问题，屏幕有坏点")

        assert "退货" in result["final_response"]

    def test_ret002_return_no_reason(self, coordinator):
        """
        RET-002: 退货-无理由

        用户输入: "我想退货"
        期望: 询问退货原因，告知政策
        """
        mock_plan = ExecutionPlan(
            intent="退货咨询",
            steps=[
                {"skill": "intent_classification", "sub_task": "识别退货意图"},
                {"skill": "policy_validation", "sub_task": "说明退货政策"}
            ]
        )
        coordinator.planner.generate_plan = MagicMock(return_value=mock_plan)

        coordinator.executor.execute = MagicMock(side_effect=[
            {
                "success": True,
                "structured": {"intent": "return", "reason": "unknown"},
                "text": "已识别退货意图"
            },
            {
                "success": True,
                "structured": {
                    "policy_info": {
                        "seven_day_free_return": True,
                        "user_pays_shipping": True
                    }
                },
                "text": "7天无理由退货，用户承担运费"
            }
        ])

        coordinator.synthesizer.synthesize = MagicMock(
            return_value="支持7天无理由退货。请问您退货的原因是什么？请注意，非质量问题退货需要您承担运费。"
        )

        result = coordinator.process("我想退货")

        assert "退货" in result["final_response"]

    def test_ret003_exchange_request(self, coordinator):
        """
        RET-003: 换货申请

        用户输入: "想换个颜色"
        期望: 处理换货请求
        """
        mock_plan = ExecutionPlan(
            intent="换货申请",
            steps=[
                {"skill": "intent_classification", "sub_task": "识别换货意图"},
                {"skill": "case_creation", "sub_task": "创建换货单"}
            ]
        )
        coordinator.planner.generate_plan = MagicMock(return_value=mock_plan)

        coordinator.executor.execute = MagicMock(side_effect=[
            {
                "success": True,
                "structured": {"intent": "exchange", "reason": "color_preference"},
                "text": "已识别换货意图"
            },
            {
                "success": True,
                "structured": {
                    "case_id": "EXG20240228001",
                    "status": "pending"
                },
                "text": "已创建换货单"
            }
        ])

        coordinator.synthesizer.synthesize = MagicMock(
            return_value="已为您创建换货单 EXG20240228001。请问您想换成什么颜色？我们会尽快为您安排发货。"
        )

        result = coordinator.process("想换个颜色")

        assert "换货" in result["final_response"]

    def test_ret004_expired_return(self, coordinator):
        """
        RET-004: 超过退货期

        用户输入: "半年前买的手机想退货"
        期望: 告知退货政策不支持
        """
        mock_plan = ExecutionPlan(
            intent="退货咨询",
            steps=[
                {"skill": "policy_validation", "sub_task": "验证退货期限"}
            ]
        )
        coordinator.planner.generate_plan = MagicMock(return_value=mock_plan)

        coordinator.executor.execute = MagicMock(return_value={
            "success": True,
            "structured": {
                "eligible": False,
                "reason": "超过7天退货期"
            },
            "text": "已超过退货期限"
        })

        coordinator.synthesizer.synthesize = MagicMock(
            return_value="抱歉，您的商品已超过7天无理由退货期限。如有质量问题，可以联系售后维修。"
        )

        result = coordinator.process("半年前买的手机想退货")

        assert "抱歉" in result["final_response"] or "无法" in result["final_response"]


class TestEcommerceDemo2KnowledgeBase:
    """Test knowledge base FAQ scenarios."""

    @pytest.fixture
    def coordinator(self):
        """Create coordinator for testing."""
        config = create_mock_config()

        with patch('agent.coordinator.LLMClient'), \
             patch('agent.coordinator.SkillRegistry'), \
             patch.object(Coordinator, '_create_llm_provider') as mock_create_provider:
            # Create mock LLM provider
            mock_provider = Mock()
            mock_create_provider.return_value = mock_provider

            coord = Coordinator(config)
            # Replace the budget with our mock
            coord.llm_client.budget = create_mock_budget()
            return coord

    def test_faq001_shipping_fee_inquiry(self, coordinator):
        """
        FAQ-001: 运费咨询

        用户输入: "运费多少钱"
        期望: 告知运费政策
        """
        mock_plan = ExecutionPlan(
            intent="运费咨询",
            steps=[
                {"skill": "faq_query", "sub_task": "查询运费政策"}
            ]
        )
        coordinator.planner.generate_plan = MagicMock(return_value=mock_plan)

        coordinator.executor.execute = MagicMock(return_value={
            "success": True,
            "structured": {
                "shipping_policy": {
                    "free_shipping_threshold": 99,
                    "standard_fee": 10
                }
            },
            "text": "满99元包邮，不满99元收取10元运费"
        })

        coordinator.synthesizer.synthesize = MagicMock(
            return_value="我们的运费政策是：订单满99元包邮，不满99元收取10元运费。"
        )

        result = coordinator.process("运费多少钱")

        assert "运费" in result["final_response"] or "包邮" in result["final_response"]

    def test_faq002_refund_timing(self, coordinator):
        """
        FAQ-002: 退款时效咨询

        用户输入: "退款多久到账"
        期望: 告知退款时效
        """
        mock_plan = ExecutionPlan(
            intent="退款咨询",
            steps=[
                {"skill": "faq_query", "sub_task": "查询退款时效"}
            ]
        )
        coordinator.planner.generate_plan = MagicMock(return_value=mock_plan)

        coordinator.executor.execute = MagicMock(return_value={
            "success": True,
            "structured": {
                "refund_timing": {
                    "alipay": "1-3个工作日",
                    "wechat": "1-3个工作日",
                    "bank_card": "3-7个工作日"
                }
            },
            "text": "支付宝1-3天，微信1-3天，银行卡3-7天"
        })

        coordinator.synthesizer.synthesize = MagicMock(
            return_value="退款到账时间：支付宝和微信支付1-3个工作日，银行卡支付3-7个工作日。"
        )

        result = coordinator.process("退款多久到账")

        assert "退款" in result["final_response"]


class TestEcommerceDemo2MultiTurnDialogue:
    """Test multi-turn dialogue in support scenarios."""

    @pytest.fixture
    def coordinator(self):
        """Create coordinator for testing."""
        config = create_mock_config()

        with patch('agent.coordinator.LLMClient'), \
             patch('agent.coordinator.SkillRegistry'), \
             patch.object(Coordinator, '_create_llm_provider') as mock_create_provider:
            # Create mock LLM provider
            mock_provider = Mock()
            mock_create_provider.return_value = mock_provider

            coord = Coordinator(config)
            # Replace the budget with our mock
            coord.llm_client.budget = create_mock_budget()
            return coord

    def test_faq003_multi_turn_return_collection(self, coordinator):
        """
        FAQ-003: 多轮对话-退货上门取件

        第一轮: "我想退货"
        第二轮: "上门取件"
        期望: 安排上门取件
        """
        # Turn 1
        mock_plan1 = ExecutionPlan(
            intent="退货申请",
            steps=[
                {"skill": "intent_classification", "sub_task": "识别退货意图"}
            ]
        )
        coordinator.planner.generate_plan = MagicMock(return_value=mock_plan1)

        coordinator.executor.execute = MagicMock(return_value={
            "success": True,
            "structured": {"intent": "return"},
            "text": "请问您选择什么退货方式？"
        })

        coordinator.synthesizer.synthesize = MagicMock(
            return_value="请问您选择什么退货方式？可以选择上门取件或自行寄回。"
        )

        result1 = coordinator.process("我想退货")
        assert "退货" in result1["final_response"]

        # Turn 2
        mock_plan2 = ExecutionPlan(
            intent="安排取件",
            steps=[
                {"skill": "case_creation", "sub_task": "安排上门取件"}
            ]
        )
        coordinator.planner.generate_plan = MagicMock(return_value=mock_plan2)

        coordinator.executor.execute = MagicMock(return_value={
            "success": True,
            "structured": {
                "pickup": {
                    "date": "2024-03-03",
                    "time_slot": "9:00-12:00"
                }
            },
            "text": "已安排取件"
        })

        coordinator.synthesizer.synthesize = MagicMock(
            return_value="已为您安排3月3日9:00-12:00上门取件，快递员会提前联系您，请保持电话畅通。"
        )

        result2 = coordinator.process("上门取件")

        assert "取件" in result2["final_response"] or "安排" in result2["final_response"]
