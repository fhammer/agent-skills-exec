"""Security tests for the Agent Framework."""

import pytest
from httpx import AsyncClient


@pytest.mark.security
class TestSQLInjection:
    """Test SQL injection protection."""

    @pytest.mark.parametrize("payload", [
        "'; DROP TABLE users; --",
        "' OR '1'='1",
        "' UNION SELECT * FROM users --",
        "1'; EXEC xp_cmdshell('dir'); --",
        "admin'--",
        "admin'/*",
        "' or 1=1#",
        "' or 1=1--",
        "' or 1=1/*",
        "') or '1'='1--",
        "admin' or '1'='1'--"
    ])
    async def test_sql_injection_in_message(
        self,
        auth_client: AsyncClient,
        payload: str
    ):
        """Test SQL injection in user message."""
        response = await auth_client.post("/api/v1/agent/chat", json={
            "message": payload
        })
        # Should not cause error
        assert response.status_code in [200, 400]
        # Response should not contain SQL fragments
        if response.status_code == 200:
            assert "DROP TABLE" not in response.text
            assert "UNION SELECT" not in response.text

    async def test_sql_injection_in_tenant_name(
        self,
        client: AsyncClient
    ):
        """Test SQL injection in tenant name."""
        response = await client.post("/api/v1/tenants", json={
            "name": "'; DROP TABLE tenants; --"
        })
        # Should be rejected or sanitized
        assert response.status_code in [201, 400]

    async def test_sql_injection_in_skill_name(
        self,
        auth_client: AsyncClient
    ):
        """Test SQL injection in skill name."""
        response = await auth_client.post("/api/v1/skills", json={
            "name": "'; DROP TABLE skills; --",
            "description": "test"
        })
        # Should be rejected or sanitized
        assert response.status_code in [201, 400]


@pytest.mark.security
class TestXSSProtection:
    """Test XSS protection."""

    @pytest.mark.parametrize("payload", [
        "<script>alert('xss')</script>",
        "<img src=x onerror=alert('xss')>",
        "javascript:alert('xss')",
        "<svg onload=alert('xss')>",
        '"><script>alert(String.fromCharCode(88,83,83))</script>',
        "<iframe src='javascript:alert(xss)'>",
        "<body onload=alert('xss')>",
        "<input onfocus=alert('xss') autofocus>",
        "<select onfocus=alert('xss') autofocus>",
        "<textarea onfocus=alert('xss') autofocus>"
    ])
    async def test_xss_in_message(
        self,
        auth_client: AsyncClient,
        payload: str
    ):
        """Test XSS in user message."""
        response = await auth_client.post("/api/v1/agent/chat", json={
            "message": payload
        })
        assert response.status_code == 200

        # Response should not contain unescaped scripts
        text = response.text
        # Scripts should be escaped or removed
        assert "<script>" not in text or "&lt;script&gt;" in text

    async def test_xss_in_tenant_name(
        self,
        client: AsyncClient
    ):
        """Test XSS in tenant name."""
        response = await client.post("/api/v1/tenants", json={
            "name": "<script>alert('xss')</script>"
        })
        assert response.status_code in [201, 400]

        if response.status_code == 201:
            # Name should be escaped
            assert "<script>" not in response.json()["name"] or \
                   "&lt;" in response.json()["name"]


@pytest.mark.security
class TestCrossTenantIsolation:
    """Test cross-tenant isolation security."""

    async def test_cannot_access_other_tenant_data(
        self,
        multi_tenant_clients: dict
    ):
        """Test that one tenant cannot access another's data."""
        client1 = multi_tenant_clients["tenant1"]
        client2 = multi_tenant_clients["tenant2"]

        # Tenant1 creates skill
        skill_response = await client1.post("/api/v1/skills", json={
            "name": "secret_skill",
            "description": "Tenant1 secret"
        })
        skill_id = skill_response.json().get("skill_id")

        # Tenant2 tries to access directly
        if skill_id:
            response = await client2.get(f"/api/v1/skills/{skill_id}")
            assert response.status_code == 404

        # Tenant2 cannot list tenant1's skills
        response = await client2.get("/api/v1/skills")
        assert response.status_code == 200
        skills = response.json().get("skills", [])
        assert not any(s.get("name") == "secret_skill" for s in skills)

    async def test_cannot_modify_other_tenant_data(
        self,
        multi_tenant_clients: dict
    ):
        """Test that one tenant cannot modify another's data."""
        client1 = multi_tenant_clients["tenant1"]
        client2 = multi_tenant_clients["tenant2"]

        # Tenant1 creates skill
        skill_response = await client1.post("/api/v1/skills", json={
            "name": "protected_skill"
        })
        skill_id = skill_response.json().get("skill_id")

        # Tenant2 tries to modify
        if skill_id:
            response = await client2.put(f"/api/v1/skills/{skill_id}", json={
                "name": "hacked"
            })
            assert response.status_code == 404

            # Verify original is unchanged
            response = await client1.get(f"/api/v1/skills/{skill_id}")
            assert response.status_code == 200
            assert response.json()["name"] == "protected_skill"

    async def test_cannot_delete_other_tenant_data(
        self,
        multi_tenant_clients: dict
    ):
        """Test that one tenant cannot delete another's data."""
        client1 = multi_tenant_clients["tenant1"]
        client2 = multi_tenant_clients["tenant2"]

        # Tenant1 creates skill
        skill_response = await client1.post("/api/v1/skills", json={
            "name": "important_skill"
        })
        skill_id = skill_response.json().get("skill_id")

        # Tenant2 tries to delete
        if skill_id:
            response = await client2.delete(f"/api/v1/skills/{skill_id}")
            assert response.status_code == 404

            # Verify still exists for tenant1
            response = await client1.get(f"/api/v1/skills/{skill_id}")
            assert response.status_code == 200


@pytest.mark.security
class TestAuthenticationSecurity:
    """Test authentication security."""

    async def test_api_key_is_not_guessable(self, client: AsyncClient):
        """Test that API keys are sufficiently random."""
        # Create multiple tenants
        api_keys = []
        for i in range(10):
            response = await client.post("/api/v1/tenants", json={
                "name": f"Tenant{i}"
            })
            api_keys.append(response.json()["api_key"])

        # All keys should be unique
        assert len(set(api_keys)) == 10

        # Keys should be sufficiently long (at least 32 chars)
        assert all(len(key) >= 32 for key in api_keys)

        # Keys should not contain predictable patterns
        assert all("tenant" not in key.lower() for key in api_keys)

    async def test_api_key_not_exposed_in_logs(
        self,
        auth_client: AsyncClient,
        caplog
    ):
        """Test that API keys are not exposed in logs."""
        import logging

        with caplog.at_level(logging.DEBUG):
            response = await auth_client.post("/api/v1/agent/chat", json={
                "message": "test"
            })

        # API key should not appear in logs
        api_key = auth_client.headers.get("X-API-Key")
        assert api_key not in caplog.text

    async def test_expired_api_key_is_rejected(
        self,
        client: AsyncClient
    ):
        """Test that expired API keys are rejected."""
        # Create tenant
        response = await client.post("/api/v1/tenants", json={
            "name": "Expired Tenant"
        })
        tenant_id = response.json()["tenant_id"]

        # Manually expire the tenant (this would need admin API)
        # For now, test with invalid key
        client.headers.update({
            "X-Tenant-ID": tenant_id,
            "X-API-Key": "expired_key_12345"
        })

        response = await client.post("/api/v1/agent/chat", json={
            "message": "test"
        })
        assert response.status_code == 401


@pytest.mark.security
class TestInputValidation:
    """Test input validation security."""

    async def test_oversized_input_rejected(
        self,
        auth_client: AsyncClient
    ):
        """Test that oversized input is rejected."""
        # Create a very large message
        large_message = "a" * 100000  # 100KB

        response = await auth_client.post("/api/v1/agent/chat", json={
            "message": large_message
        })
        # Should be rejected
        assert response.status_code == 422

    async def test_invalid_json_rejected(
        self,
        auth_client: AsyncClient
    ):
        """Test that invalid JSON is rejected."""
        response = await auth_client.post(
            "/api/v1/agent/chat",
            content="not json at all",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    async def test_missing_required_fields_rejected(
        self,
        auth_client: AsyncClient
    ):
        """Test that missing required fields are rejected."""
        response = await auth_client.post("/api/v1/agent/chat", json={})
        assert response.status_code == 422

    async def test_invalid_content_type_rejected(
        self,
        auth_client: AsyncClient
    ):
        """Test that invalid content type is rejected."""
        response = await auth_client.post(
            "/api/v1/agent/chat",
            content="message=test",
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        # Should reject or handle gracefully
        assert response.status_code in [415, 422]


@pytest.mark.security
class TestRateLimitingSecurity:
    """Test rate limiting for security."""

    async def test_brute_force_protection(
        self,
        client: AsyncClient
    ):
        """Test brute force protection is in place."""
        # Try multiple requests with invalid keys
        client.headers.update({"X-API-Key": "wrong_key"})

        blocked = False
        for i in range(20):
            response = await client.post("/api/v1/agent/chat", json={
                "message": "test"
            })
            if response.status_code == 429:
                blocked = True
                break

        # Should be rate limited after failed attempts
        assert blocked, "Should be rate limited after multiple failed attempts"

    async def test_dos_protection(
        self,
        auth_client: AsyncClient
    ):
        """Test basic DoS protection."""
        import asyncio

        # Send many concurrent requests
        async def make_request():
            return await auth_client.post("/api/v1/agent/chat", json={
                "message": "test"
            })

        # Try 50 concurrent requests
        tasks = [make_request() for _ in range(50)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # At least some should be rate limited or handled gracefully
        success_count = sum(
            1 for r in responses
            if not isinstance(r, Exception) and r.status_code == 200
        )
        assert success_count < 50, "Should have some rate limiting"


@pytest.mark.security
class TestDataLeakagePrevention:
    """Test data leakage prevention."""

    async def test_sensitive_fields_not_exposed(
        self,
        auth_client: AsyncClient
    ):
        """Test sensitive fields are not exposed in API responses."""
        response = await auth_client.get("/api/v1/tenants/self")
        assert response.status_code == 200

        data = response.json()
        # Should not contain sensitive fields
        assert "api_key_secret" not in data
        assert "internal_id" not in data
        assert "password" not in data

    async def test_error_messages_do_not_leak_info(
        self,
        client: AsyncClient
    ):
        """Test error messages don't leak sensitive information."""
        response = await client.get("/api/v1/tenants/nonexistent")
        assert response.status_code == 404

        data = response.json()
        # Should not contain database info, stack traces, etc.
        assert "database" not in str(data).lower()
        assert "sql" not in str(data).lower()
        assert "traceback" not in str(data).lower()

    async def test_audit_logs_dont_contain_secrets(
        self,
        auth_client: AsyncClient
    ):
        """Test audit logs don't contain sensitive information."""
        response = await auth_client.post("/api/v1/agent/chat", json={
            "message": "test"
        })
        assert response.status_code == 200

        data = response.json()
        if "audit_log" in data:
            for entry in data["audit_log"]:
                # Should not contain API keys or secrets
                assert "api_key" not in str(entry)
                assert "secret" not in str(entry)


@pytest.mark.security
class TestCSRFProtection:
    """Test CSRF protection."""

    async def test_state_changing_requires_proper_method(
        self,
        auth_client: AsyncClient
    ):
        """Test state changes require proper HTTP methods."""
        # Try to create with GET (should fail)
        response = await auth_client.get("/api/v1/skills?name=test")
        assert response.status_code == 405  # Method Not Allowed

    async def test_origin_validation(
        self,
        auth_client: AsyncClient
    ):
        """Test origin validation for state-changing requests."""
        # Try with different origin
        response = await auth_client.post(
            "/api/v1/skills",
            json={"name": "test"},
            headers={"Origin": "https://malicious-site.com"}
        )
        # Should either accept or reject based on CORS config
        assert response.status_code in [201, 403]
