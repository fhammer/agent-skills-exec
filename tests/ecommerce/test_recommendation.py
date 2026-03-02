"""Ecommerce recommendation demo tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.ecommerce
@pytest.mark.e2e
class TestProductRecommendation:
    """Test product recommendation functionality."""

    async def test_demand_analysis_skill(
        self,
        client: AsyncClient,
        sample_products: list
    ):
        """Test demand analysis skill extracts constraints correctly."""
        # Setup: Create tenant and load product data
        tenant_response = await client.post("/api/v1/tenants", json={
            "name": "电商测试租户"
        })
        tenant = tenant_response.json()
        client.headers.update({
            "X-Tenant-ID": tenant["tenant_id"],
            "X-API-Key": tenant["api_key"]
        })

        # Load test products
        for product in sample_products:
            await client.post("/api/v1/ecommerce/products", json=product)

        # Test demand analysis
        response = await client.post("/api/v1/recommendation/chat", json={
            "user_id": "user_001",
            "message": "我想买个2000-3000元的手机，平时玩游戏比较多"
        })

        assert response.status_code == 200
        data = response.json()

        # Verify constraints were extracted
        assert "dialogue_state" in data
        assert "response" in data

        # Response should acknowledge the constraints
        response_text = data["response"]
        assert any(keyword in response_text for keyword in ["手机", "2000", "3000", "游戏"])

    async def test_product_search_by_constraints(
        self,
        client: AsyncClient,
        sample_products: list
    ):
        """Test product search with price and category constraints."""
        # Setup
        tenant_response = await client.post("/api/v1/tenants", json={
            "name": "搜索测试租户"
        })
        tenant = tenant_response.json()
        client.headers.update({
            "X-Tenant-ID": tenant["tenant_id"],
            "X-API-Key": tenant["api_key"]
        })

        # Load products
        for product in sample_products:
            await client.post("/api/v1/ecommerce/products", json=product)

        # Search products
        response = await client.post("/api/v1/recommendation/products", json={
            "user_id": "user_001",
            "category": "手机",
            "constraints": {
                "price_min": 2000,
                "price_max": 2500
            },
            "limit": 5
        })

        assert response.status_code == 200
        data = response.json()

        assert "recommendations" in data
        recommendations = data["recommendations"]

        # Verify price constraint
        for rec in recommendations:
            assert 2000 <= rec["price"] <= 2500
            assert rec["category"] == "手机"

    async def test_product_ranking(
        self,
        client: AsyncClient,
        sample_products: list
    ):
        """Test product ranking based on user profile."""
        # Setup
        tenant_response = await client.post("/api/v1/tenants", json={
            "name": "排序测试租户"
        })
        tenant = tenant_response.json()
        client.headers.update({
            "X-Tenant-ID": tenant["tenant_id"],
            "X-API-Key": tenant["api_key"]
        })

        # Create user with preferences
        await client.post("/api/v1/ecommerce/users", json={
            "user_id": "user_pref_001",
            "preferences": {
                "preferred_brands": ["小米"],
                "price_range": {"min": 2000, "max": 3000}
            }
        })

        # Load products
        for product in sample_products:
            await client.post("/api/v1/ecommerce/products", json=product)

        # Get recommendations
        response = await client.post("/api/v1/recommendation/products", json={
            "user_id": "user_pref_001",
            "category": "手机",
            "limit": 5
        })

        assert response.status_code == 200
        data = response.json()

        # Xiaomi product should be ranked higher
        recommendations = data["recommendations"]
        if len(recommendations) > 1:
            # First product should be Xiaomi (preferred brand)
            assert recommendations[0]["brand"] == "小米"

    async def test_multi_turn_recommendation(
        self,
        client: AsyncClient,
        sample_products: list
    ):
        """Test multi-turn recommendation conversation."""
        # Setup
        tenant_response = await client.post("/api/v1/tenants", json={
            "name": "多轮对话测试租户"
        })
        tenant = tenant_response.json()
        client.headers.update({
            "X-Tenant-ID": tenant["tenant_id"],
            "X-API-Key": tenant["api_key"]
        })

        # Load products
        for product in sample_products:
            await client.post("/api/v1/ecommerce/products", json=product)

        # First turn: General inquiry
        response1 = await client.post("/api/v1/recommendation/chat", json={
            "user_id": "user_multi_001",
            "message": "我想买个手机"
        })
        assert response1.status_code == 200
        session_id = response1.json()["session_id"]

        # Second turn: Provide constraints
        response2 = await client.post("/api/v1/recommendation/chat", json={
            "session_id": session_id,
            "user_id": "user_multi_001",
            "message": "2000元左右，玩游戏用"
        })
        assert response2.status_code == 200
        data2 = response2.json()

        # Should provide specific recommendations
        assert "recommendations" in data2 or "推荐" in data2["response"]

    async def test_recommendation_with_explanation(
        self,
        client: AsyncClient,
        sample_products: list
    ):
        """Test recommendation includes explanation."""
        # Setup
        tenant_response = await client.post("/api/v1/tenants", json={
            "name": "推荐理由测试租户"
        })
        tenant = tenant_response.json()
        client.headers.update({
            "X-Tenant-ID": tenant["tenant_id"],
            "X-API-Key": tenant["api_key"]
        })

        # Load products
        for product in sample_products:
            await client.post("/api/v1/ecommerce/products", json=product)

        # Get recommendation
        response = await client.post("/api/v1/recommendation/chat", json={
            "user_id": "user_001",
            "message": "推荐一款2000元的游戏手机"
        })

        assert response.status_code == 200
        data = response.json()

        # Response should include reasons
        response_text = data["response"]
        # Check for explanation keywords
        assert any(keyword in response_text for keyword in [
            "因为", "由于", "推荐理由", "适合", "优势"
        ])

    async def test_no_results_scenario(
        self,
        client: AsyncClient
    ):
        """Test behavior when no products match constraints."""
        # Setup
        tenant_response = await client.post("/api/v1/tenants", json={
            "name": "无结果测试租户"
        })
        tenant = tenant_response.json()
        client.headers.update({
            "X-Tenant-ID": tenant["tenant_id"],
            "X-API-Key": tenant["api_key"]
        })

        # No products loaded, search should return empty
        response = await client.post("/api/v1/recommendation/products", json={
            "user_id": "user_001",
            "category": "手机",
            "constraints": {"price_min": 100, "price_max": 200}
        })

        assert response.status_code == 200
        data = response.json()

        assert "recommendations" in data
        assert len(data["recommendations"]) == 0

        # Chat response should explain no results
        chat_response = await client.post("/api/v1/recommendation/chat", json={
            "user_id": "user_001",
            "message": "100元以下的手机"
        })
        assert chat_response.status_code == 200
        assert "没有" in chat_response.json()["response"] or "暂无" in chat_response.json()["response"]


@pytest.mark.ecommerce
@pytest.mark.e2e
class TestRecommendationScenarios:
    """Test specific recommendation scenarios."""

    async def test_budget_constrained_recommendation(
        self,
        client: AsyncClient,
        sample_products: list
    ):
        """Test recommendation with strict budget constraint."""
        # Setup
        tenant_response = await client.post("/api/v1/tenants", json={
            "name": "预算约束测试"
        })
        tenant = tenant_response.json()
        client.headers.update({
            "X-Tenant-ID": tenant["tenant_id"],
            "X-API-Key": tenant["api_key"]
        })

        # Load products
        for product in sample_products:
            await client.post("/api/v1/ecommerce/products", json=product)

        # Strict budget request
        response = await client.post("/api/v1/recommendation/chat", json={
            "user_id": "user_001",
            "message": "我只有2300元，买个什么手机好"
        })

        assert response.status_code == 200
        data = response.json()

        # Should recommend phone at or below 2300
        response_text = data["response"]
        # iQOO Neo9 is 2299, should be recommended

    async def test_brand_preference_recommendation(
        self,
        client: AsyncClient,
        sample_products: list
    ):
        """Test recommendation respects brand preference."""
        # Setup
        tenant_response = await client.post("/api/v1/tenants", json={
            "name": "品牌偏好测试"
        })
        tenant = tenant_response.json()
        client.headers.update({
            "X-Tenant-ID": tenant["tenant_id"],
            "X-API-Key": tenant["api_key"]
        })

        # Create user with brand preference
        await client.post("/api/v1/ecommerce/users", json={
            "user_id": "user_brand_001",
            "preferences": {"preferred_brands": ["华为"]}
        })

        # Load products (no Huawei products)
        for product in sample_products:
            await client.post("/api/v1/ecommerce/products", json=product)

        response = await client.post("/api/v1/recommendation/chat", json={
            "user_id": "user_brand_001",
            "message": "推荐一款手机"
        })

        assert response.status_code == 200
        # Should explain no Huawei products available

    async def test_use_case_based_recommendation(
        self,
        client: AsyncClient,
        sample_products: list
    ):
        """Test recommendation based on use case (gaming, photography)."""
        # Setup
        tenant_response = await client.post("/api/v1/tenants", json={
            "name": "使用场景测试"
        })
        tenant = tenant_response.json()
        client.headers.update({
            "X-Tenant-ID": tenant["tenant_id"],
            "X-API-Key": tenant["api_key"]
        })

        # Load products
        for product in sample_products:
            await client.post("/api/v1/ecommerce/products", json=product)

        # Gaming-focused request
        response = await client.post("/api/v1/recommendation/chat", json={
            "user_id": "user_001",
            "message": "我要买个手机，主要用来玩王者荣耀"
        })

        assert response.status_code == 200
        data = response.json()

        # Should recommend gaming-oriented phones
        response_text = data["response"]
        assert any(keyword in response_text for keyword in ["游戏", "性能", "高刷"])

    async def test_product_comparison(
        self,
        client: AsyncClient,
        sample_products: list
    ):
        """Test product comparison functionality."""
        # Setup
        tenant_response = await client.post("/api/v1/tenants", json={
            "name": "产品对比测试"
        })
        tenant = tenant_response.json()
        client.headers.update({
            "X-Tenant-ID": tenant["tenant_id"],
            "X-API-Key": tenant["api_key"]
        })

        # Load products
        for product in sample_products:
            await client.post("/api/v1/ecommerce/products", json=product)

        # Comparison request
        response = await client.post("/api/v1/recommendation/chat", json={
            "user_id": "user_001",
            "message": "Redmi K70和iQOO Neo9哪个好"
        })

        assert response.status_code == 200
        data = response.json()

        # Should provide comparison
        response_text = data["response"]
        # Should mention both products
        assert "Redmi K70" in response_text or "K70" in response_text
        assert "iQOO" in response_text

    async def test_recommendation_refinement(
        self,
        client: AsyncClient,
        sample_products: list
    ):
        """Test recommendation refinement through conversation."""
        # Setup
        tenant_response = await client.post("/api/v1/tenants", json={
            "name": "推荐细化测试"
        })
        tenant = tenant_response.json()
        client.headers.update({
            "X-Tenant-ID": tenant["tenant_id"],
            "X-API-Key": tenant["api_key"]
        })

        # Load products
        for product in sample_products:
            await client.post("/api/v1/ecommerce/products", json=product)

        # Initial broad request
        response1 = await client.post("/api/v1/recommendation/chat", json={
            "user_id": "user_001",
            "message": "推荐一款手机"
        })
        session_id = response1.json()["session_id"]

        # Refine with specific requirement
        response2 = await client.post("/api/v1/recommendation/chat", json={
            "session_id": session_id,
            "user_id": "user_001",
            "message": "要快充的"
        })

        assert response2.status_code == 200
        # Should recommend phones with fast charging
        response_text = response2.json()["response"]
        assert "快充" in response_text or "充电" in response_text


@pytest.mark.ecommerce
@pytest.mark.performance
class TestRecommendationPerformance:
    """Test recommendation system performance."""

    async def test_search_performance(
        self,
        client: AsyncClient,
        sample_products: list
    ):
        """Test product search performance."""
        import time

        # Setup
        tenant_response = await client.post("/api/v1/tenants", json={
            "name": "性能测试租户"
        })
        tenant = tenant_response.json()
        client.headers.update({
            "X-Tenant-ID": tenant["tenant_id"],
            "X-API-Key": tenant["api_key"]
        })

        # Load products
        for product in sample_products:
            await client.post("/api/v1/ecommerce/products", json=product)

        # Measure search time
        start = time.time()
        response = await client.post("/api/v1/recommendation/products", json={
            "user_id": "user_001",
            "category": "手机",
            "limit": 10
        })
        elapsed = time.time() - start

        assert response.status_code == 200
        # Search should be fast (< 1 second)
        assert elapsed < 1.0

    async def test_ranking_performance(
        self,
        client: AsyncClient
    ):
        """Test ranking performance with many candidates."""
        import time
        import asyncio

        # Setup
        tenant_response = await client.post("/api/v1/tenants", json={
            "name": "排序性能测试"
        })
        tenant = tenant_response.json()
        client.headers.update({
            "X-Tenant-ID": tenant["tenant_id"],
            "X-API-Key": tenant["api_key"]
        })

        # Load many products
        products = []
        for i in range(100):
            products.append({
                "product_id": f"p_{i:03d}",
                "name": f"测试手机{i}",
                "category": "手机",
                "brand": ["小米", "华为", "iQOO", "一加"][i % 4],
                "price": 2000 + i * 10,
                "rating": 4.0 + (i % 10) * 0.1
            })

        # Load products in parallel
        await asyncio.gather(*[
            client.post("/api/v1/ecommerce/products", json=p)
            for p in products
        ])

        # Measure ranking time
        start = time.time()
        response = await client.post("/api/v1/recommendation/products", json={
            "user_id": "user_001",
            "category": "手机",
            "limit": 5
        })
        elapsed = time.time() - start

        assert response.status_code == 200
        # Ranking should still be reasonably fast
        assert elapsed < 2.0
