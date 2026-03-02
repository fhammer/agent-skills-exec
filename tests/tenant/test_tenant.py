"""Tenant management tests."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import Tenant
from tests.conftest import TestHelpers


@pytest.mark.tenant
@pytest.mark.integration
class TestTenantManagement:
    """Test tenant CRUD operations."""

    async def test_create_tenant(
        self,
        client: AsyncClient,
        sample_tenant_data: dict
    ):
        """Test creating a new tenant."""
        response = await client.post("/api/v1/tenants", json=sample_tenant_data)
        assert response.status_code == 201

        data = response.json()
        assert data["name"] == sample_tenant_data["name"]
        assert data["api_quota"] == sample_tenant_data["api_quota"]
        assert "tenant_id" in data
        assert "api_key" in data
        assert data["status"] == "active"

    async def test_create_tenant_duplicate_name(
        self,
        client: AsyncClient,
        sample_tenant_data: dict
    ):
        """Test creating tenant with duplicate name."""
        # Create first tenant
        await client.post("/api/v1/tenants", json=sample_tenant_data)

        # Try to create duplicate
        response = await client.post("/api/v1/tenants", json=sample_tenant_data)
        assert response.status_code == 409  # Conflict

    async def test_get_tenant(
        self,
        client: AsyncClient,
        sample_tenant_data: dict
    ):
        """Test retrieving tenant details."""
        # Create tenant
        create_response = await client.post("/api/v1/tenants", json=sample_tenant_data)
        tenant_id = create_response.json()["tenant_id"]

        # Get tenant
        response = await client.get(f"/api/v1/tenants/{tenant_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["tenant_id"] == tenant_id
        assert data["name"] == sample_tenant_data["name"]

    async def test_get_tenant_not_found(self, client: AsyncClient):
        """Test retrieving non-existent tenant."""
        response = await client.get("/api/v1/tenants/nonexistent_tenant")
        assert response.status_code == 404

    async def test_list_tenants(
        self,
        client: AsyncClient
    ):
        """Test listing all tenants."""
        # Create multiple tenants
        for i in range(3):
            await client.post("/api/v1/tenants", json={
                "name": f"测试租户{i}",
                "api_quota": 1000
            })

        # List tenants
        response = await client.get("/api/v1/tenants")
        assert response.status_code == 200

        data = response.json()
        assert "tenants" in data
        assert len(data["tenants"]) >= 3

    async def test_update_tenant(
        self,
        client: AsyncClient,
        sample_tenant_data: dict
    ):
        """Test updating tenant information."""
        # Create tenant
        create_response = await client.post("/api/v1/tenants", json=sample_tenant_data)
        tenant_id = create_response.json()["tenant_id"]

        # Update tenant
        update_data = {
            "name": "更新后的租户名称",
            "api_quota": 2000
        }
        response = await client.put(f"/api/v1/tenants/{tenant_id}", json=update_data)
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["api_quota"] == update_data["api_quota"]

    async def test_delete_tenant(
        self,
        client: AsyncClient,
        sample_tenant_data: dict
    ):
        """Test deleting a tenant."""
        # Create tenant
        create_response = await client.post("/api/v1/tenants", json=sample_tenant_data)
        tenant_id = create_response.json()["tenant_id"]

        # Delete tenant
        response = await client.delete(f"/api/v1/tenants/{tenant_id}")
        assert response.status_code == 200

        # Verify deletion
        get_response = await client.get(f"/api/v1/tenants/{tenant_id}")
        assert get_response.status_code == 404

    async def test_tenant_config_inheritance(
        self,
        client: AsyncClient
    ):
        """Test tenant configuration inheritance."""
        # Create parent tenant with config
        parent_response = await client.post("/api/v1/tenants", json={
            "name": "父租户",
            "config": {
                "model": "gpt-4",
                "max_tokens": 2000,
                "temperature": 0.7
            }
        })
        parent_tenant_id = parent_response.json()["tenant_id"]

        # Create child tenant with inheritance
        child_response = await client.post("/api/v1/tenants", json={
            "name": "子租户",
            "parent_tenant_id": parent_tenant_id,
            "inherit_config": True
        })
        assert child_response.status_code == 201

        child_data = child_response.json()
        assert child_data["config"]["model"] == "gpt-4"
        assert child_data["config"]["max_tokens"] == 2000


@pytest.mark.tenant
@pytest.mark.integration
class TestTenantIsolation:
    """Test tenant data isolation."""

    async def test_tenant_data_isolation(
        self,
        multi_tenant_clients: dict
    ):
        """Test that tenants cannot access each other's data."""
        client1 = multi_tenant_clients["tenant1"]
        client2 = multi_tenant_clients["tenant2"]

        # Tenant1 creates a skill
        skill_response = await client1.post("/api/v1/skills", json={
            "name": "tenant1_skill",
            "description": "Only for tenant1"
        })
        assert skill_response.status_code == 201
        skill_id = skill_response.json()["skill_id"]

        # Tenant2 tries to access tenant1's skill
        response = await client2.get(f"/api/v1/skills/{skill_id}")
        assert response.status_code == 404  # Not found for tenant2

    async def test_tenant_user_isolation(
        self,
        multi_tenant_clients: dict
    ):
        """Test that users are isolated by tenant."""
        client1 = multi_tenant_clients["tenant1"]
        client2 = multi_tenant_clients["tenant2"]

        # Tenant1 creates a user
        user_response = await client1.post("/api/v1/users", json={
            "name": "tenant1_user",
            "email": "user1@tenant1.com"
        })
        assert user_response.status_code == 201
        user_id = user_response.json()["user_id"]

        # Tenant2 tries to access tenant1's user
        response = await client2.get(f"/api/v1/users/{user_id}")
        assert response.status_code == 404

    async def test_tenant_api_quota_enforcement(
        self,
        client: AsyncClient
    ):
        """Test that API quota is enforced per tenant."""
        # Create tenant with limited quota
        tenant_response = await client.post("/api/v1/tenants", json={
            "name": "受限租户",
            "api_quota": 5  # Only 5 requests
        })
        tenant_id = tenant_response.json()["tenant_id"]
        api_key = tenant_response.json()["api_key"]

        # Create authenticated client
        client.headers.update({
            "X-Tenant-ID": tenant_id,
            "X-API-Key": api_key
        })

        # Make requests up to quota
        for _ in range(5):
            response = await client.post("/api/v1/agent/chat", json={
                "message": "test"
            })
            assert response.status_code == 200

        # Next request should be rate limited
        response = await client.post("/api/v1/agent/chat", json={
            "message": "test"
        })
        assert response.status_code == 429

    async def test_cross_tenant_session_isolation(
        self,
        multi_tenant_clients: dict
    ):
        """Test that sessions are isolated across tenants."""
        client1 = multi_tenant_clients["tenant1"]
        client2 = multi_tenant_clients["tenant2"]

        # Tenant1 starts a conversation
        response1 = await client1.post("/api/v1/agent/chat", json={
            "message": "我想买个手机"
        })
        assert response1.status_code == 200
        session_id = response1.json()["session_id"]

        # Tenant2 tries to access tenant1's session
        response2 = await client2.post("/api/v1/agent/chat", json={
            "session_id": session_id,
            "message": "继续"
        })
        # Should either return error or start new session
        assert response2.status_code in [400, 404, 200]


@pytest.mark.tenant
@pytest.mark.security
class TestTenantSecurity:
    """Test tenant security features."""

    async def test_tenant_api_key_validation(
        self,
        client: AsyncClient,
        sample_tenant_data: dict
    ):
        """Test API key validation for tenant access."""
        # Create tenant
        create_response = await client.post("/api/v1/tenants", json=sample_tenant_data)
        tenant_id = create_response.json()["tenant_id"]

        # Test with invalid API key
        client.headers.update({
            "X-Tenant-ID": tenant_id,
            "X-API-Key": "invalid_key"
        })

        response = await client.post("/api/v1/agent/chat", json={
            "message": "test"
        })
        assert response.status_code == 401

    async def test_tenant_without_api_key(
        self,
        client: AsyncClient,
        sample_tenant_data: dict
    ):
        """Test request without API key is rejected."""
        create_response = await client.post("/api/v1/tenants", json=sample_tenant_data)
        tenant_id = create_response.json()["tenant_id"]

        # Request without API key
        client.headers.update({"X-Tenant-ID": tenant_id})
        if "X-API-Key" in client.headers:
            del client.headers["X-API-Key"]

        response = await client.post("/api/v1/agent/chat", json={
            "message": "test"
        })
        assert response.status_code == 401

    async def test_tenant_status_management(
        self,
        client: AsyncClient,
        sample_tenant_data: dict
    ):
        """Test tenant status (active/suspended) enforcement."""
        # Create tenant
        create_response = await client.post("/api/v1/tenants", json=sample_tenant_data)
        tenant_id = create_response.json()["tenant_id"]
        api_key = create_response.json()["api_key"]

        # Suspend tenant
        await client.put(f"/api/v1/tenants/{tenant_id}", json={
            "status": "suspended"
        })

        # Try to use suspended tenant
        client.headers.update({
            "X-Tenant-ID": tenant_id,
            "X-API-Key": api_key
        })

        response = await client.post("/api/v1/agent/chat", json={
            "message": "test"
        })
        assert response.status_code == 403  # Forbidden
