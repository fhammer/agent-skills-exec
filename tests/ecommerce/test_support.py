"""Ecommerce support/customer service demo tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.ecommerce
@pytest.mark.e2e
class TestOrderQuery:
    """Test order query functionality."""

    async def test_query_recent_orders(
        self,
        client: AsyncClient,
        sample_orders: list
    ):
        """Test querying user's recent orders."""
        # Setup
        tenant_response = await client.post("/api/v1/tenants", json={
            "name": "订单查询测试租户"
        })
        tenant = tenant_response.json()
        client.headers.update({
            "X-Tenant-ID": tenant["tenant_id"],
            "X-API-Key": tenant["api_key"]
        })

        # Create user
        await client.post("/api/v1/ecommerce/users", json={
            "user_id": "user_order_001",
            "name": "测试用户"
        })

        # Load orders
        for order in sample_orders:
            await client.post("/api/v1/ecommerce/orders", json=order)

        # Query recent orders
        response = await client.post("/api/v1/support/chat", json={
            "user_id": "user_order_001",
            "message": "查一下我的订单"
        })

        assert response.status_code == 200
        data = response.json()

        # Should return order information
        response_text = data["response"]
        assert "订单" in response_text

        # Check if structured data is included
        if "orders" in data:
            assert len(data["orders"]) > 0

    async def test_query_by_order_id(
        self,
        client: AsyncClient,
        sample_orders: list
    ):
        """Test querying specific order by ID."""
        # Setup
        tenant_response = await client.post("/api/v1/tenants", json={
            "name": "订单号查询测试"
        })
        tenant = tenant_response.json()
        client.headers.update({
            "X-Tenant-ID": tenant["tenant_id"],
            "X-API-Key": tenant["api_key"]
        })

        # Create user and load order
        await client.post("/api/v1/ecommerce/users", json={
            "user_id": "user_order_002",
            "name": "测试用户"
        })

        target_order = sample_orders[0]
        await client.post("/api/v1/ecommerce/orders", json=target_order)

        # Query by order ID
        response = await client.post("/api/v1/support/chat", json={
            "user_id": "user_order_002",
            "message": f"订单{target_order['order_id']}怎么样了"
        })

        assert response.status_code == 200
        data = response.json()

        # Should mention the order
        response_text = data["response"]
        assert target_order["order_id"] in response_text

    async def test_order_status_check(
        self,
        client: AsyncClient,
        sample_orders: list
    ):
        """Test checking order status."""
        # Setup
        tenant_response = await client.post("/api/v1/tenants", json={
            "name": "订单状态测试"
        })
        tenant = tenant_response.json()
        client.headers.update({
            "X-Tenant-ID": tenant["tenant_id"],
            "X-API-Key": tenant["api_key"]
        })

        # Create user and load order
        await client.post("/api/v1/ecommerce/users", json={
            "user_id": "user_order_003",
            "name": "测试用户"
        })

        target_order = sample_orders[0]  # shipped status
        await client.post("/api/v1/ecommerce/orders", json=target_order)

        # Check status
        response = await client.post("/api/v1/support/chat", json={
            "user_id": "user_order_003",
            "message": f"订单{target_order['order_id']}发货了吗"
        })

        assert response.status_code == 200
        data = response.json()

        # Should mention shipping status
        response_text = data["response"]
        assert any(keyword in response_text for keyword in ["发货", "已发货", "物流"])

    async def test_logistics_tracking(
        self,
        client: AsyncClient,
        sample_orders: list
    ):
        """Test logistics tracking query."""
        # Setup
        tenant_response = await client.post("/api/v1/tenants", json={
            "name": "物流查询测试"
        })
        tenant = tenant_response.json()
        client.headers.update({
            "X-Tenant-ID": tenant["tenant_id"],
            "X-API-Key": tenant["api_key"]
        })

        # Create user and load order with logistics
        await client.post("/api/v1/ecommerce/users", json={
            "user_id": "user_order_004",
            "name": "测试用户"
        })

        target_order = sample_orders[0]
        await client.post("/api/v1/ecommerce/orders", json=target_order)

        # Query logistics
        response = await client.post("/api/v1/support/chat", json={
            "user_id": "user_order_004",
            "message": "我的快递到哪了"
        })

        assert response.status_code == 200
        data = response.json()

        # Should provide logistics info
        response_text = data["response"]
        assert any(keyword in response_text for keyword in [
            "物流", "快递", "运单", "顺丰"
        ])

    async def test_no_orders_scenario(
        self,
        client: AsyncClient
    ):
        """Test behavior when user has no orders."""
        # Setup
        tenant_response = await client.post("/api/v1/tenants", json={
            "name": "无订单测试"
        })
        tenant = tenant_response.json()
        client.headers.update({
            "X-Tenant-ID": tenant["tenant_id"],
            "X-API-Key": tenant["api_key"]
        })

        # Create user without orders
        await client.post("/api/v1/ecommerce/users", json={
            "user_id": "user_no_orders",
            "name": "新用户"
        })

        # Query orders
        response = await client.post("/api/v1/support/chat", json={
            "user_id": "user_no_orders",
            "message": "查一下我的订单"
        })

        assert response.status_code == 200
        data = response.json()

        # Should explain no orders found
        response_text = data["response"]
        assert any(keyword in response_text for keyword in [
            "没有订单", "暂无", "还没有"
        ])


@pytest.mark.ecommerce
@pytest.mark.e2e
class TestReturnRequest:
    """Test return/refund request functionality."""

    async def test_return_for_quality_issue(
        self,
        client: AsyncClient,
        sample_orders: list
    ):
        """Test return request due to quality issue."""
        # Setup
        tenant_response = await client.post("/api/v1/tenants", json={
            "name": "质量问题退货测试"
        })
        tenant = tenant_response.json()
        client.headers.update({
            "X-Tenant-ID": tenant["tenant_id"],
            "X-API-Key": tenant["api_key"]
        })

        # Create user and order
        await client.post("/api/v1/ecommerce/users", json={
            "user_id": "user_return_001",
            "name": "测试用户"
        })

        target_order = sample_orders[0]
        await client.post("/api/v1/ecommerce/orders", json=target_order)

        # Initiate return for quality issue
        response = await client.post("/api/v1/support/chat", json={
            "user_id": "user_return_001",
            "message": f"订单{target_order['order_id']}想退货，屏幕有坏点"
        })

        assert response.status_code == 200
        data = response.json()

        # Should process return request
        response_text = data["response"]
        assert any(keyword in response_text for keyword in [
            "退货", "申请", "运费"
        ])

        # Check if case was created
        if "case_id" in data:
            assert data["case_id"] is not None

    async def test_return_within_7_days(
        self,
        client: AsyncClient,
        sample_orders: list
    ):
        """Test return within 7-day no-reason policy."""
        # Setup
        tenant_response = await client.post("/api/v1/tenants", json={
            "name": "7天无理由测试"
        })
        tenant = tenant_response.json()
        client.headers.update({
            "X-Tenant-ID": tenant["tenant_id"],
            "X-API-Key": tenant["api_key"]
        })

        # Create user and recent order
        await client.post("/api/v1/ecommerce/users", json={
            "user_id": "user_return_002",
            "name": "测试用户"
        })

        await client.post("/api/v1/ecommerce/orders", json=sample_orders[0])

        # Request return without specific reason
        response = await client.post("/api/v1/support/chat", json={
            "user_id": "user_return_002",
            "message": "我不想要了，想退货"
        })

        assert response.status_code == 200
        data = response.json()

        # Should mention 7-day policy
        response_text = data["response"]
        assert "7天" in response_text or "无理由" in response_text

    async def test_return_shipping_fee_explanation(
        self,
        client: AsyncClient,
        sample_orders: list
    ):
        """Test shipping fee explanation for returns."""
        # Setup
        tenant_response = await client.post("/api/v1/tenants", json={
            "name": "运费说明测试"
        })
        tenant = tenant_response.json()
        client.headers.update({
            "X-Tenant-ID": tenant["tenant_id"],
            "X-API-Key": tenant["api_key"]
        })

        # Create user and order
        await client.post("/api/v1/ecommerce/users", json={
            "user_id": "user_return_003",
            "name": "测试用户"
        })

        await client.post("/api/v1/ecommerce/orders", json=sample_orders[0])

        # Ask about return shipping
        response = await client.post("/api/v1/support/chat", json={
            "user_id": "user_return_003",
            "message": "退货要运费吗"
        })

        assert response.status_code == 200
        data = response.json()

        # Should explain shipping fee policy
        response_text = data["response"]
        assert "运费" in response_text

    async def test_exchange_request(
        self,
        client: AsyncClient,
        sample_orders: list
    ):
        """Test exchange request."""
        # Setup
        tenant_response = await client.post("/api/v1/tenants", json={
            "name": "换货测试"
        })
        tenant = tenant_response.json()
        client.headers.update({
            "X-Tenant-ID": tenant["tenant_id"],
            "X-API-Key": tenant["api_key"]
        })

        # Create user and order
        await client.post("/api/v1/ecommerce/users", json={
            "user_id": "user_exchange_001",
            "name": "测试用户"
        })

        await client.post("/api/v1/ecommerce/orders", json=sample_orders[0])

        # Request exchange
        response = await client.post("/api/v1/support/chat", json={
            "user_id": "user_exchange_001",
            "message": "想换个颜色"
        })

        assert response.status_code == 200
        data = response.json()

        # Should handle exchange request
        response_text = data["response"]
        assert "换货" in response_text or "颜色" in response_text


@pytest.mark.ecommerce
@pytest.mark.e2e
class TestKnowledgeBase:
    """Test knowledge base/FAQ functionality."""

    async def test_faq_query(
        self,
        client: AsyncClient
    ):
        """Test FAQ query."""
        # Setup
        tenant_response = await client.post("/api/v1/tenants", json={
            "name": "FAQ测试租户"
        })
        tenant = tenant_response.json()
        client.headers.update({
            "X-Tenant-ID": tenant["tenant_id"],
            "X-API-Key": tenant["api_key"]
        })

        # Create user
        await client.post("/api/v1/ecommerce/users", json={
            "user_id": "user_faq_001",
            "name": "测试用户"
        })

        # Query FAQ
        response = await client.post("/api/v1/support/chat", json={
            "user_id": "user_faq_001",
            "message": "退货流程是什么"
        })

        assert response.status_code == 200
        data = response.json()

        # Should provide FAQ answer
        response_text = data["response"]
        assert len(response_text) > 0

    async def test_policy_inquiry(
        self,
        client: AsyncClient
    ):
        """Test policy inquiry."""
        # Setup
        tenant_response = await client.post("/api/v1/tenants", json={
            "name": "政策咨询测试"
        })
        tenant = tenant_response.json()
        client.headers.update({
            "X-Tenant-ID": tenant["tenant_id"],
            "X-API-Key": tenant["api_key"]
        })

        # Create user
        await client.post("/api/v1/ecommerce/users", json={
            "user_id": "user_policy_001",
            "name": "测试用户"
        })

        # Ask about refund policy
        response = await client.post("/api/v1/support/chat", json={
            "user_id": "user_policy_001",
            "message": "退款多久到账"
        })

        assert response.status_code == 200
        data = response.json()

        # Should explain refund timing
        response_text = data["response"]
        assert any(keyword in response_text for keyword in [
            "退款", "到账", "工作日"
        ])

    async def test_multiple_questions_in_conversation(
        self,
        client: AsyncClient
    ):
        """Test handling multiple questions in a conversation."""
        # Setup
        tenant_response = await client.post("/api/v1/tenants", json={
            "name": "多问题测试"
        })
        tenant = tenant_response.json()
        client.headers.update({
            "X-Tenant-ID": tenant["tenant_id"],
            "X-API-Key": tenant["api_key"]
        })

        # Create user
        await client.post("/api/v1/ecommerce/users", json={
            "user_id": "user_multi_q_001",
            "name": "测试用户"
        })

        # First question
        response1 = await client.post("/api/v1/support/chat", json={
            "user_id": "user_multi_q_001",
            "message": "退货要运费吗"
        })
        assert response1.status_code == 200
        session_id = response1.json()["session_id"]

        # Second question (should maintain context)
        response2 = await client.post("/api/v1/support/chat", json={
            "session_id": session_id,
            "user_id": "user_multi_q_001",
            "message": "那退款呢"
        })
        assert response2.status_code == 200


@pytest.mark.ecommerce
@pytest.mark.e2e
class TestSupportScenarios:
    """Test complete support scenarios."""

    async def test_full_return_flow(
        self,
        client: AsyncClient,
        sample_orders: list
    ):
        """Test complete return request flow."""
        # Setup
        tenant_response = await client.post("/api/v1/tenants", json={
            "name": "完整退货流程测试"
        })
        tenant = tenant_response.json()
        client.headers.update({
            "X-Tenant-ID": tenant["tenant_id"],
            "X-API-Key": tenant["api_key"]
        })

        # Create user and order
        await client.post("/api/v1/ecommerce/users", json={
            "user_id": "user_flow_001",
            "name": "测试用户"
        })

        target_order = sample_orders[0]
        await client.post("/api/v1/ecommerce/orders", json=target_order)

        # Step 1: Initiate return
        response1 = await client.post("/api/v1/support/chat", json={
            "user_id": "user_flow_001",
            "message": "我要退货"
        })
        assert response1.status_code == 200
        session_id = response1.json()["session_id"]

        # Step 2: Provide order
        response2 = await client.post("/api/v1/support/chat", json={
            "session_id": session_id,
            "user_id": "user_flow_001",
            "message": target_order["order_id"]
        })
        assert response2.status_code == 200

        # Step 3: Provide reason
        response3 = await client.post("/api/v1/support/chat", json={
            "session_id": session_id,
            "user_id": "user_flow_001",
            "message": "屏幕有坏点，质量问题"
        })
        assert response3.status_code == 200

        # Should have created return request
        data3 = response3.json()
        response_text = data3["response"]
        assert any(keyword in response_text for keyword in [
            "退货单", "申请成功", "寄回"
        ])

    async def test_intent_switching(
        self,
        client: AsyncClient,
        sample_orders: list
    ):
        """Test switching between different intents."""
        # Setup
        tenant_response = await client.post("/api/v1/tenants", json={
            "name": "意图切换测试"
        })
        tenant = tenant_response.json()
        client.headers.update({
            "X-Tenant-ID": tenant["tenant_id"],
            "X-API-Key": tenant["api_key"]
        })

        # Create user and order
        await client.post("/api/v1/ecommerce/users", json={
            "user_id": "user_intent_001",
            "name": "测试用户"
        })

        await client.post("/api/v1/ecommerce/orders", json=sample_orders[0])

        # Start with order query
        response1 = await client.post("/api/v1/support/chat", json={
            "user_id": "user_intent_001",
            "message": "查一下我的订单"
        })
        assert response1.status_code == 200
        session_id = response1.json()["session_id"]

        # Switch to return request
        response2 = await client.post("/api/v1/support/chat", json={
            "session_id": session_id,
            "user_id": "user_intent_001",
            "message": "第一个订单想退货"
        })
        assert response2.status_code == 200

        # Should handle intent switch
        data2 = response2.json()
        assert "退货" in data2["response"]

    async def test_escalation_to_human(
        self,
        client: AsyncClient
    ):
        """Test escalation to human agent."""
        # Setup
        tenant_response = await client.post("/api/v1/tenants", json={
            "name": "人工转接测试"
        })
        tenant = tenant_response.json()
        client.headers.update({
            "X-Tenant-ID": tenant["tenant_id"],
            "X-API-Key": tenant["api_key"]
        })

        # Create user
        await client.post("/api/v1/ecommerce/users", json={
            "user_id": "user_escalate_001",
            "name": "测试用户"
        })

        # Request human agent
        response = await client.post("/api/v1/support/chat", json={
            "user_id": "user_escalate_001",
            "message": "转人工客服"
        })

        assert response.status_code == 200
        data = response.json()

        # Should acknowledge or handle escalation request
        response_text = data["response"]
        assert any(keyword in response_text for keyword in [
            "人工", "转接", "客服"
        ])
