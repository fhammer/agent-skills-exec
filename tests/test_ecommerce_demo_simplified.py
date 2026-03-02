"""Simplified tests for E-commerce Demos."""

import pytest
from unittest.mock import Mock, MagicMock, patch


def test_recommendation_skill_basic():
    """Test basic recommendation skill functionality."""
    from skills.ecommerce_recommendation.executor import EcommerceRecommendationExecutor
    import asyncio

    async def run_test():
        executor = EcommerceRecommendationExecutor()

        # Test 1: Clear requirement
        result1 = await executor.execute(
            user_input="我想买个2000-3000的手机，平时玩游戏比较多",
            user_id="test_user_123"
        )

        assert result1 is not None
        assert result1.dialogue_state.value in ["recommendation_ready", "awaiting_clarification"]
        assert result1.response_text

    asyncio.run(run_test())


def test_recommendation_skill_clarification():
    """Test clarification response."""
    from skills.ecommerce_recommendation.executor import EcommerceRecommendationExecutor
    import asyncio

    async def run_test():
        executor = EcommerceRecommendationExecutor()

        # Test: Vague requirement
        result = await executor.execute(
            user_input="我想买个好东西"
        )

        assert result is not None
        assert result.dialogue_state.value == "awaiting_clarification"
        assert "请补充" in result.response_text or "请问" in result.response_text

    asyncio.run(run_test())


def test_product_comparison():
    """Test product comparison functionality."""
    from skills.ecommerce_recommendation.executor import EcommerceRecommendationExecutor
    import asyncio

    async def run_test():
        executor = EcommerceRecommendationExecutor()

        result = await executor.compare_products(
            product_names=["Redmi K70", "iQOO Neo9"],
            user_id="test_user_123"
        )

        assert result is not None
        assert len(result.products) == 2
        assert result.comparison_points
        assert result.recommendation

    asyncio.run(run_test())


def test_context_management():
    """Test context management in recommendations."""
    from skills.ecommerce_recommendation.executor import EcommerceRecommendationExecutor
    import asyncio

    async def run_test():
        executor = EcommerceRecommendationExecutor()

        # First turn - category only
        result1 = await executor.execute(
            user_input="推荐手机",
            user_id="test_user_123"
        )

        # Second turn - add constraints
        result2 = await executor.execute(
            user_input="2000左右，玩游戏",
            user_id="test_user_123"
        )

        assert result2 is not None
        # Should use context from first turn
        assert "2000" in result2.response_text or "游戏" in result2.response_text

    asyncio.run(run_test())


def test_order_query_skill():
    """Test order query skill functionality."""
    from skills.after_sales_support.executor import AfterSalesSupportExecutor
    import asyncio

    async def run_test():
        executor = AfterSalesSupportExecutor()

        # Test: Query recent orders
        result = await executor.execute(
            user_input="查一下我的订单",
            user_id="test_user_123"
        )

        assert result is not None
        assert result.response_text
        # Should mention orders or ask for user ID
        assert "订单" in result.response_text or "用户" in result.response_text

    asyncio.run(run_test())


def test_return_request_skill():
    """Test return request skill functionality."""
    from skills.after_sales_support.executor import AfterSalesSupportExecutor
    import asyncio

    async def run_test():
        executor = AfterSalesSupportExecutor()

        # Test: Quality issue return
        result = await executor.execute(
            user_input="这个手机有问题，屏幕有坏点",
            user_id="test_user_123"
        )

        assert result is not None
        assert result.response_text
        assert "退货" in result.response_text or "问题" in result.response_text

    asyncio.run(run_test())


def test_faq_handling():
    """Test FAQ handling."""
    from skills.after_sales_support.executor import AfterSalesSupportExecutor
    import asyncio

    async def run_test():
        executor = AfterSalesSupportExecutor()

        # Test: Shipping fee inquiry
        result = await executor.execute(
            user_input="运费多少钱",
            user_id="test_user_123"
        )

        assert result is not None
        assert result.response_text
        # Should mention shipping or fees
        assert "运费" in result.response_text or "包邮" in result.response_text or "邮费" in result.response_text

    asyncio.run(run_test())


class TestEcommerceScenarios:
    """Test complete e-commerce scenarios."""

    @pytest.mark.asyncio
    async def test_complete_shopping_flow(self):
        """Test complete shopping flow from inquiry to recommendation."""
        from skills.ecommerce_recommendation.executor import EcommerceRecommendationExecutor

        executor = EcommerceRecommendationExecutor()

        # Step 1: Initial inquiry
        result1 = await executor.execute(
            user_input="我想买个手机",
            user_id="user_001"
        )
        assert result1.response_text

        # Step 2: Provide budget
        result2 = await executor.execute(
            user_input="2000左右",
            user_id="user_001"
        )
        assert result2.response_text

        # Step 3: Provide use case
        result3 = await executor.execute(
            user_input="平时玩游戏比较多",
            user_id="user_001"
        )
        assert result3.response_text
        # Should now have recommendations
        assert len(result3.recommendations) > 0 or "推荐" in result3.response_text

    @pytest.mark.asyncio
    async def test_complete_support_flow(self):
        """Test complete support flow from issue to resolution."""
        from skills.after_sales_support.executor import AfterSalesSupportExecutor

        executor = AfterSalesSupportExecutor()

        # Step 1: User reports issue
        result1 = await executor.execute(
            user_input="我的订单有问题",
            user_id="user_001"
        )
        assert result1.response_text

        # Step 2: Provide order ID
        result2 = await executor.execute(
            user_input="订单号是20240228123456",
            user_id="user_001"
        )
        assert result2.response_text

        # Step 3: Describe issue
        result3 = await executor.execute(
            user_input="屏幕有坏点",
            user_id="user_001"
        )
        assert result3.response_text
        # Should provide return options
        assert "退货" in result3.response_text or "换货" in result3.response_text or "售后" in result3.response_text
