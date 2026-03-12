"""
Pytest fixtures and helpers for testing.
"""

import pytest
import asyncio
from typing import Dict, Any, Optional
from unittest.mock import Mock, MagicMock
from dataclasses import dataclass


class TestHelpers:
    """Helper methods for testing."""

    @staticmethod
    def create_mock_llm_client(response: Optional[str] = None):
        """Create a mock LLM client."""
        mock_client = Mock()
        if response:
            mock_client.complete = Mock(return_value=response)
        return mock_client

    @staticmethod
    def create_mock_skill(name: str = "test_skill", version: str = "1.0.0"):
        """Create a mock skill."""
        mock_skill = Mock()
        mock_skill.name = name
        mock_skill.version = version
        mock_skill.execute = Mock(return_value={"status": "success"})
        return mock_skill

    @staticmethod
    async def run_async_test(coro):
        """Run an async test coroutine."""
        return await coro

    @staticmethod
    def create_sample_tenant_data() -> Dict[str, Any]:
        """Create sample tenant data for testing."""
        return {
            "name": "Test Tenant",
            "description": "A test tenant",
            "api_quota": 1000,
            "contact_email": "test@example.com"
        }


@pytest.fixture
def test_helpers():
    """Provide TestHelpers instance."""
    return TestHelpers


@pytest.fixture
def sample_tenant_data():
    """Provide sample tenant data."""
    return TestHelpers.create_sample_tenant_data()


@pytest.fixture
def mock_llm_client():
    """Provide a mock LLM client."""
    return TestHelpers.create_mock_llm_client()


@pytest.fixture(scope="session")
def event_loop():
    """Provide an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
