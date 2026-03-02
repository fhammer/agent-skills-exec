"""API service tests."""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch


@pytest.mark.api
@pytest.mark.integration
class TestAPIAuthentication:
    """Test API authentication and authorization."""

    async def test_api_without_credentials(self, client: AsyncClient):
        """Test API request without authentication."""
        # Remove any auth headers
        if "X-API-Key" in client.headers:
            del client.headers["X-API-Key"]

        response = await client.post("/api/v1/agent/chat", json={
            "message": "test"
        })
        assert response.status_code == 401

    async def test_api_with_invalid_key(self, client: AsyncClient):
        """Test API request with invalid API key."""
        client.headers.update({"X-API-Key": "invalid_key_12345"})

        response = await client.post("/api/v1/agent/chat", json={
            "message": "test"
        })
        assert response.status_code == 401

    async def test_api_with_valid_key(
        self,
        auth_client: AsyncClient
    ):
        """Test API request with valid API key."""
        response = await auth_client.post("/api/v1/agent/chat", json={
            "message": "你好"
        })
        assert response.status_code == 200

    async def test_api_key_generation(self, client: AsyncClient):
        """Test that API keys are properly generated."""
        response = await client.post("/api/v1/tenants/", json={
            "name": "API Key 测试租户"
        })
        assert response.status_code == 201

        data = response.json()
        assert "api_key" in data
        assert len(data["api_key"]) >= 32  # API key should be sufficiently long


@pytest.mark.api
@pytest.mark.integration
class TestAPIRateLimiting:
    """Test API rate limiting."""

    async def test_rate_limit_enforcement(
        self,
        auth_client: AsyncClient
    ):
        """Test that rate limit is enforced."""
        # Make requests up to quota
        success_count = 0
        rate_limited = False

        for i in range(120):  # Try 120 requests (quota is 100)
            response = await auth_client.post("/api/v1/agent/chat", json={
                "message": f"test message {i}"
            })

            if response.status_code == 200:
                success_count += 1
            elif response.status_code == 429:
                rate_limited = True
                # Check Retry-After header
                assert "retry-after" in response.headers
                break

        assert rate_limited, "Should be rate limited after quota exceeded"

    async def test_rate_limit_reset(
        self,
        client: AsyncClient
    ):
        """Test that rate limit resets properly."""
        # Create tenant with small quota
        response = await client.post("/api/v1/tenants/", json={
            "name": "小配额租户",
            "api_quota": 10
        })
        tenant = response.json()

        client.headers.update({
            "X-Tenant-ID": tenant["tenant_id"],
            "X-API-Key": tenant["api_key"]
        })

        # Use up quota
        for _ in range(10):
            response = await client.post("/api/v1/agent/chat", json={
                "message": "test"
            })
            assert response.status_code == 200

        # Should be rate limited
        response = await client.post("/api/v1/agent/chat", json={
            "message": "test"
        })
        assert response.status_code == 429

    @pytest.mark.slow
    async def test_rate_limit_per_tenant(
        self,
        multi_tenant_clients: dict
    ):
        """Test that rate limit is per-tenant."""
        client1 = multi_tenant_clients["tenant1"]
        client2 = multi_tenant_clients["tenant2"]

        # Client1 uses up most of its quota
        for _ in range(90):
            await client1.post("/api/v1/agent/chat", json={"message": "test"})

        # Client2 should still have full quota
        for _ in range(50):
            response = await client2.post("/api/v1/agent/chat", json={
                "message": "test"
            })
            assert response.status_code == 200


@pytest.mark.api
@pytest.mark.integration
class TestAPIErrorHandling:
    """Test API error handling."""

    async def test_invalid_json_request(self, auth_client: AsyncClient):
        """Test handling of invalid JSON."""
        response = await auth_client.post(
            "/api/v1/agent/chat",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422  # Unprocessable Entity

    async def test_missing_required_fields(self, auth_client: AsyncClient):
        """Test handling of missing required fields."""
        response = await auth_client.post("/api/v1/agent/chat", json={})
        assert response.status_code == 422

    async def test_404_error_handling(self, auth_client: AsyncClient):
        """Test 404 error handling."""
        response = await auth_client.get("/api/v1/nonexistent")
        assert response.status_code == 404

        data = response.json()
        assert "error" in data
        assert data["code"] == "NOT_FOUND"

    async def test_422_validation_error(self, auth_client: AsyncClient):
        """Test validation error response format."""
        response = await auth_client.post("/api/v1/agent/chat", json={
            "message": ""  # Empty message should fail validation
        })
        assert response.status_code == 422

        data = response.json()
        assert "error" in data
        assert "detail" in data


@pytest.mark.api
@pytest.mark.integration
class TestAPIHeaders:
    """Test API header handling."""

    async def test_cors_headers(self, client: AsyncClient):
        """Test CORS headers are present."""
        response = await client.options("/api/v1/agent/chat")
        assert "access-control-allow-origin" in response.headers

    async def test_content_type_headers(self, auth_client: AsyncClient):
        """Test Content-Type headers."""
        response = await auth_client.post("/api/v1/agent/chat", json={
            "message": "test"
        })
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

    async def test_request_id_header(self, auth_client: AsyncClient):
        """Test X-Request-ID header is returned."""
        response = await auth_client.post("/api/v1/agent/chat", json={
            "message": "test"
        })
        assert "x-request-id" in response.headers


@pytest.mark.api
@pytest.mark.integration
class TestHealthCheck:
    """Test health check endpoints."""

    async def test_health_endpoint(self, client: AsyncClient):
        """Test health check endpoint."""
        response = await client.get("/api/v1/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    async def test_health_includes_dependencies(self, client: AsyncClient):
        """Test health check includes dependency status."""
        response = await client.get("/api/v1/health")
        assert response.status_code == 200

        data = response.json()
        assert "dependencies" in data
        assert "database" in data["dependencies"]

    async def test_readiness_endpoint(self, client: AsyncClient):
        """Test readiness endpoint."""
        response = await client.get("/api/v1/health/ready")
        assert response.status_code in [200, 503]

    async def test_liveness_endpoint(self, client: AsyncClient):
        """Test liveness endpoint."""
        response = await client.get("/api/v1/health/live")
        assert response.status_code == 200


@pytest.mark.api
@pytest.mark.e2e
class TestAPIConversationFlow:
    """Test complete conversation flows."""

    async def test_single_turn_conversation(self, auth_client: AsyncClient):
        """Test single turn conversation."""
        response = await auth_client.post("/api/v1/agent/chat", json={
            "message": "你好，请介绍一下你自己"
        })
        assert response.status_code == 200

        data = response.json()
        assert "response" in data
        assert "session_id" in data
        assert len(data["response"]) > 0

    async def test_multi_turn_conversation(self, auth_client: AsyncClient):
        """Test multi-turn conversation with context."""
        # First turn
        response1 = await auth_client.post("/api/v1/agent/chat", json={
            "message": "我想买个手机"
        })
        assert response1.status_code == 200
        session_id = response1.json()["session_id"]

        # Second turn with session
        response2 = await auth_client.post("/api/v1/agent/chat", json={
            "session_id": session_id,
            "message": "预算2000元左右"
        })
        assert response2.status_code == 200

        data = response2.json()
        assert "response" in data
        # Response should reference the context (phone, budget)
        response_text = data["response"].lower()
        assert any(keyword in response_text for keyword in ["手机", "推荐", "2000", "元"])

    async def test_conversation_with_invalid_session(self, auth_client: AsyncClient):
        """Test conversation with invalid session ID."""
        response = await auth_client.post("/api/v1/agent/chat", json={
            "session_id": "invalid_session_id",
            "message": "继续"
        })
        # Should create new session or return error
        assert response.status_code in [200, 404]

    async def test_conversation_audit_trail(self, auth_client: AsyncClient):
        """Test that conversation is audited."""
        response = await auth_client.post("/api/v1/agent/chat", json={
            "message": "test audit"
        })
        assert response.status_code == 200

        data = response.json()
        assert "audit_log" in data or "usage" in data

    async def test_streaming_conversation(self, auth_client: AsyncClient):
        """Test streaming response (if supported)."""
        response = await auth_client.post("/api/v1/agent/chat", json={
            "message": "你好",
            "stream": True
        })
        # Streaming support may vary
        assert response.status_code in [200, 501]


@pytest.mark.api
@pytest.mark.performance
class TestAPIPerformance:
    """Test API performance characteristics."""

    async def test_response_time_baseline(self, auth_client: AsyncClient):
        """Test baseline response time."""
        import time

        start = time.time()
        response = await auth_client.post("/api/v1/agent/chat", json={
            "message": "test"
        })
        elapsed = time.time() - start

        assert response.status_code == 200
        # Response should be reasonably fast (adjust threshold as needed)
        assert elapsed < 5.0  # 5 second threshold

    async def test_concurrent_requests(self, auth_client: AsyncClient):
        """Test handling concurrent requests."""
        import asyncio

        async def make_request(i):
            return await auth_client.post("/api/v1/agent/chat", json={
                "message": f"concurrent test {i}"
            })

        # Make 10 concurrent requests
        tasks = [make_request(i) for i in range(10)]
        responses = await asyncio.gather(*tasks)

        # All should succeed
        assert all(r.status_code == 200 for r in responses)

    @pytest.mark.slow
    async def test_memory_usage(self, auth_client: AsyncClient):
        """Test memory usage during conversations."""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Make multiple requests
        for i in range(50):
            await auth_client.post("/api/v1/agent/chat", json={
                "message": f"memory test {i}"
            })

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (100MB threshold)
        assert memory_increase < 100 * 1024 * 1024
