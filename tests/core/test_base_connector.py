"""Tests for BaseConnector abstract base class."""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any, Optional, List
from agent_core.base.connector import (
    BaseConnector,
    ConnectorConfig,
    ConnectorStatus,
    ConnectionStats,
    QueryResult,
)


class SimpleConnector(BaseConnector):
    """A simple test connector."""

    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self.connected = False
        self.execute_log = []

    async def _connect(self) -> bool:
        self.connected = True
        return True

    async def _disconnect(self) -> bool:
        self.connected = False
        return True

    async def _execute(self, operation: str, parameters: Dict[str, Any]) -> QueryResult:
        self.execute_log.append((operation, parameters))

        if operation == "query":
            return QueryResult.success(
                connector_name=self.name,
                records=[{"id": 1, "data": "test"}, {"id": 2, "data": "test2"}],
                total_count=2
            )
        elif operation == "insert":
            return QueryResult.success(
                connector_name=self.name,
                records=[{"id": parameters.get("id", 3), "data": parameters.get("data")}],
                total_count=1
            )
        else:
            return QueryResult.success(
                connector_name=self.name,
                records=[],
                total_count=0
            )


class FailingConnector(BaseConnector):
    """A connector that fails operations."""

    async def _connect(self) -> bool:
        return False

    async def _disconnect(self) -> bool:
        return False

    async def _execute(self, operation: str, parameters: Dict[str, Any]) -> QueryResult:
        raise Exception("Intentional connector failure")


class ErrorConnector(BaseConnector):
    """A connector that throws errors during connect."""

    async def _connect(self) -> bool:
        raise Exception("Connection error")

    async def _disconnect(self) -> bool:
        raise Exception("Disconnect error")

    async def _execute(self, operation: str, parameters: Dict[str, Any]) -> QueryResult:
        raise Exception("Execute error")


class HookConnector(BaseConnector):
    """Connector with hook tracking."""

    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self.hook_calls = []

    async def _connect(self) -> bool:
        self.hook_calls.append("_connect")
        return True

    async def _disconnect(self) -> bool:
        self.hook_calls.append("_disconnect")
        return True

    async def _execute(self, operation: str, parameters: Dict[str, Any]) -> QueryResult:
        self.hook_calls.append(f"_execute:{operation}")
        return QueryResult.success(connector_name=self.name, records=[])

    async def _before_connect(self) -> None:
        self.hook_calls.append("_before_connect")

    async def _after_connect(self) -> None:
        self.hook_calls.append("_after_connect")

    async def _before_disconnect(self) -> None:
        self.hook_calls.append("_before_disconnect")

    async def _after_disconnect(self) -> None:
        self.hook_calls.append("_after_disconnect")

    async def _before_execute(self, operation: str, parameters: Dict[str, Any]) -> None:
        self.hook_calls.append(f"_before_execute:{operation}")

    async def _after_execute(self, operation: str, parameters: Dict[str, Any], result: QueryResult) -> None:
        self.hook_calls.append(f"_after_execute:{operation}")


class TestBaseConnector:
    """Tests for BaseConnector abstract base class."""

    @pytest.fixture
    def connector_config(self):
        """Create a connector configuration."""
        return ConnectorConfig(
            name="test_connector",
            type="database",
            version="1.0.0",
            description="Test database connector",
            connection_string="sqlite://:memory:",
            timeout_seconds=30,
            max_retries=3,
            retry_delay_seconds=0.1,
            enable_heartbeat=False,
            heartbeat_interval_seconds=60,
            auto_reconnect=True,
            max_reconnect_attempts=2,
            custom_settings={"pool_size": 5}
        )

    @pytest.fixture
    def simple_connector(self, connector_config):
        """Create a SimpleConnector instance."""
        return SimpleConnector(connector_config)

    @pytest.fixture
    def failing_connector(self):
        """Create a FailingConnector instance."""
        config = ConnectorConfig(name="failing_connector", type="test")
        return FailingConnector(config)

    @pytest.fixture
    def error_connector(self):
        """Create an ErrorConnector instance."""
        config = ConnectorConfig(name="error_connector", type="test")
        return ErrorConnector(config)

    @pytest.fixture
    def hook_connector(self):
        """Create a HookConnector instance."""
        config = ConnectorConfig(name="hook_connector", type="test")
        return HookConnector(config)

    def test_initialization(self, simple_connector, connector_config):
        """Test connector initialization."""
        assert simple_connector.name == "test_connector"
        assert simple_connector.type == "database"
        assert simple_connector.version == "1.0.0"
        assert simple_connector.config.description == "Test database connector"
        assert simple_connector.status == ConnectorStatus.DISCONNECTED
        assert simple_connector.created_at is not None
        assert simple_connector.connected_since is None
        assert simple_connector.is_connected is False

        # Check initial stats
        assert simple_connector.stats.connection_count == 0
        assert simple_connector.stats.successful_connections == 0
        assert simple_connector.stats.failed_connections == 0
        assert simple_connector.stats.total_requests == 0
        assert simple_connector.stats.successful_requests == 0
        assert simple_connector.stats.failed_requests == 0

    @pytest.mark.asyncio
    async def test_connect_success(self, simple_connector):
        """Test successful connection."""
        assert simple_connector.status == ConnectorStatus.DISCONNECTED

        result = await simple_connector.connect()

        assert result is True
        assert simple_connector.status == ConnectorStatus.CONNECTED
        assert simple_connector.is_connected is True
        assert simple_connector.connected_since is not None
        assert simple_connector.stats.connection_count == 1
        assert simple_connector.stats.successful_connections == 1
        assert simple_connector.stats.failed_connections == 0
        assert simple_connector.stats.last_connected_at is not None

    @pytest.mark.asyncio
    async def test_connect_failure(self, failing_connector):
        """Test connection failure."""
        result = await failing_connector.connect()

        assert result is False
        assert failing_connector.status == ConnectorStatus.ERROR
        assert failing_connector.is_connected is False
        assert failing_connector.stats.connection_count == 1
        assert failing_connector.stats.successful_connections == 0
        assert failing_connector.stats.failed_connections == 1

    @pytest.mark.asyncio
    async def test_connect_with_exception(self, error_connector):
        """Test connection with exception."""
        result = await error_connector.connect()

        assert result is False
        assert error_connector.status == ConnectorStatus.ERROR
        assert error_connector.stats.failed_connections == 1
        assert len(error_connector.stats.errors) == 1
        assert error_connector.stats.errors[0]["operation"] == "connect"

    @pytest.mark.asyncio
    async def test_disconnect_success(self, simple_connector):
        """Test successful disconnect."""
        await simple_connector.connect()

        result = await simple_connector.disconnect()

        assert result is True
        assert simple_connector.status == ConnectorStatus.DISCONNECTED
        assert simple_connector.is_connected is False
        assert simple_connector.connected_since is None
        assert simple_connector.stats.last_disconnected_at is not None
        assert simple_connector.stats.total_connection_time_ms > 0

    @pytest.mark.asyncio
    async def test_disconnect_failure(self, failing_connector):
        """Test disconnect failure."""
        result = await failing_connector.disconnect()

        assert result is False
        assert failing_connector.status == ConnectorStatus.ERROR

    @pytest.mark.asyncio
    async def test_execute_query(self, simple_connector):
        """Test execute query operation."""
        await simple_connector.connect()

        result = await simple_connector.execute(
            "query",
            {"query": "SELECT * FROM test"}
        )

        assert isinstance(result, QueryResult)
        assert result.success is True
        assert result.connector_name == "test_connector"
        assert len(result.records) == 2
        assert result.total_count == 2
        assert result.records[0]["id"] == 1
        assert result.error is None
        assert result.execution_time_ms > 0

        assert simple_connector.stats.total_requests == 1
        assert simple_connector.stats.successful_requests == 1
        assert simple_connector.stats.failed_requests == 0

    @pytest.mark.asyncio
    async def test_execute_insert(self, simple_connector):
        """Test execute insert operation."""
        await simple_connector.connect()

        result = await simple_connector.execute(
            "insert",
            {"id": 42, "data": "new record"}
        )

        assert result.success is True
        assert len(result.records) == 1
        assert result.records[0]["id"] == 42
        assert result.records[0]["data"] == "new record"

    @pytest.mark.asyncio
    async def test_query_method(self, simple_connector):
        """Test the query shortcut method."""
        await simple_connector.connect()

        result = await simple_connector.query("SELECT * FROM test")

        assert result.success is True
        assert len(simple_connector.execute_log) == 1
        assert simple_connector.execute_log[0][0] == "query"

    @pytest.mark.asyncio
    async def test_execute_not_connected(self, simple_connector):
        """Test execute when not connected."""
        config = ConnectorConfig(
            name="no_reconnect",
            type="test",
            auto_reconnect=False
        )
        connector = SimpleConnector(config)

        result = await connector.execute("query", {})

        assert result.success is False
        assert "Not connected" in result.error

    @pytest.mark.asyncio
    async def test_execute_with_exception(self, error_connector):
        """Test execute with exception."""
        error_connector._status = ConnectorStatus.CONNECTED

        result = await error_connector.execute("query", {})

        assert result.success is False
        assert "Intentional connector failure" not in result.error  # Should be our execute error
        assert len(error_connector.stats.errors) == 1

    @pytest.mark.asyncio
    async def test_connect_hooks(self, hook_connector):
        """Test connect hooks are called."""
        await hook_connector.connect()

        expected_hooks = [
            "_before_connect",
            "_connect",
            "_after_connect"
        ]
        assert hook_connector.hook_calls == expected_hooks

    @pytest.mark.asyncio
    async def test_disconnect_hooks(self, hook_connector):
        """Test disconnect hooks are called."""
        await hook_connector.connect()
        hook_connector.hook_calls.clear()

        await hook_connector.disconnect()

        expected_hooks = [
            "_before_disconnect",
            "_disconnect",
            "_after_disconnect"
        ]
        assert hook_connector.hook_calls == expected_hooks

    @pytest.mark.asyncio
    async def test_execute_hooks(self, hook_connector):
        """Test execute hooks are called."""
        await hook_connector.connect()
        hook_connector.hook_calls.clear()

        await hook_connector.execute("test_op", {})

        expected_hooks = [
            "_before_execute:test_op",
            "_execute:test_op",
            "_after_execute:test_op"
        ]
        assert hook_connector.hook_calls == expected_hooks

    @pytest.mark.asyncio
    async def test_reconnect(self, simple_connector):
        """Test reconnect functionality."""
        await simple_connector.connect()
        await simple_connector.disconnect()

        result = await simple_connector.reconnect()

        assert result is True
        assert simple_connector.is_connected is True

    @pytest.mark.asyncio
    async def test_check_connection(self, simple_connector):
        """Test check_connection method."""
        await simple_connector.connect()

        result = await simple_connector.check_connection()

        assert result is True

    @pytest.mark.asyncio
    async def test_heartbeat(self, simple_connector):
        """Test heartbeat method."""
        await simple_connector.connect()

        result = await simple_connector.heartbeat()

        assert result is True

    def test_get_metadata(self, simple_connector):
        """Test get_metadata method."""
        metadata = simple_connector.get_metadata()

        assert metadata["name"] == "test_connector"
        assert metadata["type"] == "database"
        assert metadata["version"] == "1.0.0"
        assert metadata["description"] == "Test database connector"
        assert metadata["status"] == "disconnected"
        assert metadata["is_connected"] is False
        assert metadata["created_at"] == simple_connector.created_at
        assert "stats" in metadata
        assert metadata["stats"]["connection_count"] == 0

    @pytest.mark.asyncio
    async def test_metadata_updates_after_connect(self, simple_connector):
        """Test metadata updates after connection."""
        await simple_connector.connect()

        metadata = simple_connector.get_metadata()

        assert metadata["status"] == "connected"
        assert metadata["is_connected"] is True
        assert metadata["stats"]["connection_count"] == 1
        assert metadata["stats"]["successful_connections"] == 1

    def test_connector_config_defaults(self):
        """Test ConnectorConfig default values."""
        config = ConnectorConfig(name="minimal_connector", type="test")

        assert config.name == "minimal_connector"
        assert config.type == "test"
        assert config.version == "1.0.0"
        assert config.description == ""
        assert config.connection_string == ""
        assert config.timeout_seconds == 30
        assert config.max_retries == 3
        assert config.retry_delay_seconds == 1.0
        assert config.enable_heartbeat is False
        assert config.heartbeat_interval_seconds == 60
        assert config.auto_reconnect is True
        assert config.max_reconnect_attempts == 5
        assert config.custom_settings == {}

    def test_string_representation(self, simple_connector):
        """Test __str__ and __repr__ methods."""
        str_repr = str(simple_connector)
        repr_repr = repr(simple_connector)

        assert "test_connector" in str_repr
        assert "database" in str_repr
        assert "disconnected" in str_repr

        assert "SimpleConnector" in repr_repr
        assert "test_connector" in repr_repr
        assert "database" in repr_repr


class TestQueryResult:
    """Tests for QueryResult."""

    def test_success_result_creation(self):
        """Test creating a success result."""
        result = QueryResult.success(
            connector_name="test_connector",
            records=[{"id": 1, "name": "test"}, {"id": 2, "name": "test2"}],
            total_count=10,
            execution_time_ms=100.5,
            metadata={"page": 1}
        )

        assert result.success is True
        assert result.connector_name == "test_connector"
        assert len(result.records) == 2
        assert result.total_count == 10
        assert result.error is None
        assert result.execution_time_ms == 100.5
        assert result.metadata == {"page": 1}
        assert result.started_at is not None
        assert result.completed_at is not None

    def test_success_result_default_total_count(self):
        """Test success result with default total_count."""
        result = QueryResult.success(
            connector_name="test_connector",
            records=[{"id": 1}, {"id": 2}, {"id": 3}]
        )

        assert result.total_count == 3

    def test_failure_result_creation(self):
        """Test creating a failure result."""
        result = QueryResult.failure(
            connector_name="test_connector",
            error="Query failed",
            execution_time_ms=50.0,
            metadata={"query": "SELECT ..."}
        )

        assert result.success is False
        assert result.connector_name == "test_connector"
        assert result.records == []
        assert result.total_count == 0
        assert result.error == "Query failed"
        assert result.execution_time_ms == 50.0
        assert result.metadata == {"query": "SELECT ..."}

    def test_result_to_dict(self):
        """Test to_dict method."""
        result = QueryResult.success(
            connector_name="test_connector",
            records=[{"id": 1, "data": "test"}],
            total_count=1
        )

        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert result_dict["success"] is True
        assert result_dict["connector_name"] == "test_connector"
        assert result_dict["records"] == [{"id": 1, "data": "test"}]
        assert result_dict["total_count"] == 1
        assert result_dict["error"] is None
        assert "execution_time_ms" in result_dict
        assert "started_at" in result_dict
        assert "completed_at" in result_dict


class TestConnectionStats:
    """Tests for ConnectionStats."""

    def test_default_values(self):
        """Test default stats values."""
        stats = ConnectionStats()

        assert stats.connection_count == 0
        assert stats.successful_connections == 0
        assert stats.failed_connections == 0
        assert stats.total_requests == 0
        assert stats.successful_requests == 0
        assert stats.failed_requests == 0
        assert stats.total_bytes_sent == 0
        assert stats.total_bytes_received == 0
        assert stats.total_connection_time_ms == 0.0
        assert stats.last_connected_at is None
        assert stats.last_disconnected_at is None
        assert stats.errors == []

    def test_error_recording(self):
        """Test error recording."""
        stats = ConnectionStats()
        stats.errors.append({
            "operation": "connect",
            "error": "Failed",
            "timestamp": 1234567890.0
        })

        assert len(stats.errors) == 1
        assert stats.errors[0]["operation"] == "connect"
        assert stats.errors[0]["error"] == "Failed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
