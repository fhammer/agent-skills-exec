"""Tests for BaseTool abstract base class."""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock
from typing import Dict, Any, Optional
from agent_core.base.tool import BaseTool, ToolConfig, ToolStatus, ToolContext, ToolResult


class SimpleTool(BaseTool):
    """A simple test tool."""

    async def _on_initialize(self) -> bool:
        return True

    async def _execute(self, context: ToolContext) -> ToolResult:
        return ToolResult.success(
            tool_name=self.name,
            structured={"input": context.user_input, "parameters": context.parameters},
            text=f"Executed tool with input: {context.user_input}"
        )

    async def _on_shutdown(self) -> bool:
        return True


class FailingTool(BaseTool):
    """A tool that always fails during execution."""

    async def _on_initialize(self) -> bool:
        return True

    async def _execute(self, context: ToolContext) -> ToolResult:
        raise Exception("Intentional tool failure")

    async def _on_shutdown(self) -> bool:
        return True


class TestBaseTool:
    """Tests for BaseTool abstract base class."""

    @pytest.fixture
    def tool_config(self):
        """Create a tool configuration."""
        return ToolConfig(
            name="test_tool",
            version="1.0.0",
            description="Test tool",
            author="Test Author",
            tags=["test", "example"],
            requires_authentication=False,
            timeout_seconds=30,
            max_retries=3,
            rate_limit_per_minute=60,
            custom_settings={"key": "value"}
        )

    @pytest.fixture
    def simple_tool(self, tool_config):
        """Create a SimpleTool instance."""
        return SimpleTool(tool_config)

    @pytest.fixture
    def failing_tool(self):
        """Create a FailingTool instance."""
        config = ToolConfig(name="failing_tool")
        return FailingTool(config)

    @pytest.fixture
    def tool_context(self):
        """Create a tool execution context."""
        return ToolContext(
            request_id="req-123",
            tool_name="test_tool",
            parameters={"param1": "value1", "param2": 123},
            user_input="test input",
            environment={"env": "test"},
            tenant_id="tenant-789",
            user_id="user-123",
            session_id="session-456",
            metadata={"key": "value"}
        )

    def test_initialization(self, simple_tool, tool_config):
        """Test tool initialization."""
        assert simple_tool.name == "test_tool"
        assert simple_tool.version == "1.0.0"
        assert simple_tool.config.description == "Test tool"
        assert simple_tool.config.author == "Test Author"
        assert simple_tool.config.tags == ["test", "example"]
        assert simple_tool.config.requires_authentication is False
        assert simple_tool.status == ToolStatus.INACTIVE
        assert simple_tool.created_at is not None
        assert simple_tool.last_executed_at is None
        assert simple_tool.execution_count == 0
        assert simple_tool.success_count == 0
        assert simple_tool.error_count == 0
        assert simple_tool.avg_execution_time_ms == 0.0

    @pytest.mark.asyncio
    async def test_tool_initialize(self, simple_tool):
        """Test tool initialization sequence."""
        assert simple_tool.status == ToolStatus.INACTIVE

        result = await simple_tool.initialize()

        assert result is True
        assert simple_tool.status == ToolStatus.READY

    @pytest.mark.asyncio
    async def test_successful_execution(self, simple_tool, tool_context):
        """Test successful tool execution."""
        await simple_tool.initialize()

        result = await simple_tool.execute(tool_context)

        assert isinstance(result, ToolResult)
        assert result.success is True
        assert result.tool_name == "test_tool"
        assert result.structured["input"] == "test input"
        assert result.structured["parameters"] == {"param1": "value1", "param2": 123}
        assert "Executed tool with input: test input" in result.text
        assert result.error is None
        assert result.execution_time_ms > 0

        assert simple_tool.execution_count == 1
        assert simple_tool.success_count == 1
        assert simple_tool.error_count == 0
        assert simple_tool.last_executed_at is not None
        assert simple_tool.avg_execution_time_ms > 0

    @pytest.mark.asyncio
    async def test_execution_with_error(self, failing_tool, tool_context):
        """Test tool execution with error."""
        await failing_tool.initialize()

        result = await failing_tool.execute(tool_context)

        assert result.success is False
        assert result.tool_name == "failing_tool"
        assert "Intentional tool failure" in result.error
        assert result.execution_time_ms > 0

        assert failing_tool.execution_count == 1
        assert failing_tool.success_count == 0
        assert failing_tool.error_count == 1
        assert failing_tool.status == ToolStatus.ERROR

    @pytest.mark.asyncio
    async def test_multiple_executions(self, simple_tool, tool_context):
        """Test multiple tool executions accumulate statistics."""
        await simple_tool.initialize()

        # First execution
        result1 = await simple_tool.execute(tool_context)
        assert result1.success is True

        # Second execution
        context2 = ToolContext(
            request_id="req-456",
            tool_name="test_tool",
            parameters={"param": "new_value"},
            user_input="new input"
        )
        result2 = await simple_tool.execute(context2)
        assert result2.success is True

        assert simple_tool.execution_count == 2
        assert simple_tool.success_count == 2
        assert simple_tool.error_count == 0
        assert simple_tool.avg_execution_time_ms > 0

    @pytest.mark.asyncio
    async def test_tool_shutdown(self, simple_tool):
        """Test tool shutdown sequence."""
        await simple_tool.initialize()
        assert simple_tool.status == ToolStatus.READY

        result = await simple_tool.shutdown()

        assert result is True
        assert simple_tool.status == ToolStatus.INACTIVE

    @pytest.mark.asyncio
    async def test_tool_lifecycle(self):
        """Test complete tool lifecycle."""
        config = ToolConfig(name="lifecycle_tool")
        tool = SimpleTool(config)

        assert tool.status == ToolStatus.INACTIVE

        await tool.initialize()
        assert tool.status == ToolStatus.READY

        context = ToolContext(tool_name="lifecycle_tool", user_input="test")
        result = await tool.execute(context)
        assert result.success is True

        await tool.shutdown()
        assert tool.status == ToolStatus.INACTIVE

    def test_tool_metadata(self, simple_tool):
        """Test get_metadata returns correct information."""
        metadata = simple_tool.get_metadata()

        assert metadata["name"] == "test_tool"
        assert metadata["version"] == "1.0.0"
        assert metadata["description"] == "Test tool"
        assert metadata["author"] == "Test Author"
        assert metadata["tags"] == ["test", "example"]
        assert metadata["requires_authentication"] is False
        assert metadata["status"] == "inactive"
        assert metadata["created_at"] == simple_tool.created_at
        assert metadata["last_executed_at"] is None
        assert metadata["execution_count"] == 0
        assert metadata["success_count"] == 0
        assert metadata["error_count"] == 0
        assert metadata["avg_execution_time_ms"] == 0.0

    @pytest.mark.asyncio
    async def test_metadata_updates_after_execution(self, simple_tool, tool_context):
        """Test metadata updates after execution."""
        await simple_tool.initialize()
        await simple_tool.execute(tool_context)

        metadata = simple_tool.get_metadata()

        assert metadata["status"] == "ready"
        assert metadata["execution_count"] == 1
        assert metadata["success_count"] == 1
        assert metadata["error_count"] == 0
        assert metadata["last_executed_at"] is not None
        assert metadata["avg_execution_time_ms"] > 0

    def test_tool_config_defaults(self):
        """Test ToolConfig default values."""
        config = ToolConfig(name="minimal_tool")

        assert config.name == "minimal_tool"
        assert config.version == "1.0.0"
        assert config.description == ""
        assert config.author == ""
        assert config.tags == []
        assert config.requires_authentication is False
        assert config.timeout_seconds == 30
        assert config.max_retries == 3
        assert config.rate_limit_per_minute == 60
        assert config.custom_settings == {}

    @pytest.mark.asyncio
    async def test_validate_parameters(self, simple_tool):
        """Test validate parameters method."""
        errors = await simple_tool.validate_parameters({"param1": "value1"})
        assert errors == []

    @pytest.mark.asyncio
    async def test_before_after_execute_hooks(self):
        """Test before and after execute hooks."""
        class HookTool(BaseTool):
            def __init__(self, config: ToolConfig):
                super().__init__(config)
                self.before_called = False
                self.after_called = False

            async def _on_initialize(self) -> bool:
                return True

            async def _execute(self, context: ToolContext) -> ToolResult:
                return ToolResult.success(tool_name=self.name, text="Executed")

            async def _before_execute(self, context: ToolContext) -> None:
                self.before_called = True

            async def _after_execute(self, context: ToolContext, result: ToolResult) -> None:
                self.after_called = True

            async def _on_shutdown(self) -> bool:
                return True

        config = ToolConfig(name="hook_tool")
        tool = HookTool(config)
        await tool.initialize()

        context = ToolContext(tool_name="hook_tool", user_input="test")
        await tool.execute(context)

        assert tool.before_called is True
        assert tool.after_called is True

    def test_string_representation(self, simple_tool):
        """Test __str__ and __repr__ methods."""
        str_repr = str(simple_tool)
        repr_repr = repr(simple_tool)

        assert "test_tool" in str_repr
        assert "1.0.0" in str_repr
        assert "inactive" in str_repr

        assert "SimpleTool" in repr_repr
        assert "test_tool" in repr_repr
        assert "1.0.0" in repr_repr
        assert "inactive" in repr_repr


class TestToolContext:
    """Tests for ToolContext."""

    def test_context_initialization(self):
        """Test context initialization with all parameters."""
        context = ToolContext(
            request_id="req-123",
            tool_name="test_tool",
            parameters={"param1": "value1", "param2": 123},
            user_input="user input",
            environment={"env": "test"},
            tenant_id="tenant-789",
            user_id="user-123",
            session_id="session-456",
            metadata={"key": "value"}
        )

        assert context.request_id == "req-123"
        assert context.tool_name == "test_tool"
        assert context.parameters == {"param1": "value1", "param2": 123}
        assert context.user_input == "user input"
        assert context.environment == {"env": "test"}
        assert context.tenant_id == "tenant-789"
        assert context.user_id == "user-123"
        assert context.session_id == "session-456"
        assert context.metadata == {"key": "value"}
        assert context.started_at is not None

    def test_context_defaults(self):
        """Test context with default values."""
        context = ToolContext()

        assert context.request_id is not None
        assert context.tool_name == ""
        assert context.parameters == {}
        assert context.user_input == ""
        assert context.environment == {}
        assert context.tenant_id is None
        assert context.user_id is None
        assert context.session_id is None
        assert context.metadata == {}
        assert context.started_at is not None

    def test_context_to_dict(self):
        """Test to_dict method."""
        context = ToolContext(
            request_id="req-123",
            tool_name="test_tool",
            user_input="test input"
        )

        context_dict = context.to_dict()

        assert isinstance(context_dict, dict)
        assert context_dict["request_id"] == "req-123"
        assert context_dict["tool_name"] == "test_tool"
        assert context_dict["user_input"] == "test input"
        assert "started_at" in context_dict


class TestToolResult:
    """Tests for ToolResult."""

    def test_success_result_creation(self):
        """Test creating a success result."""
        result = ToolResult.success(
            tool_name="test_tool",
            structured={"key": "value", "number": 123},
            text="Success message",
            execution_time_ms=100.5,
            metadata={"meta": "data"}
        )

        assert result.success is True
        assert result.tool_name == "test_tool"
        assert result.structured == {"key": "value", "number": 123}
        assert result.text == "Success message"
        assert result.error is None
        assert result.execution_time_ms == 100.5
        assert result.metadata == {"meta": "data"}
        assert result.started_at is not None
        assert result.completed_at is not None

    def test_failure_result_creation(self):
        """Test creating a failure result."""
        result = ToolResult.failure(
            tool_name="test_tool",
            error="Something went wrong",
            execution_time_ms=50.0,
            metadata={"meta": "data"}
        )

        assert result.success is False
        assert result.tool_name == "test_tool"
        assert result.structured == {}
        assert result.text == ""
        assert result.error == "Something went wrong"
        assert result.execution_time_ms == 50.0
        assert result.metadata == {"meta": "data"}

    def test_result_to_dict(self):
        """Test to_dict method."""
        result = ToolResult.success(
            tool_name="test_tool",
            structured={"key": "value"},
            text="Success"
        )

        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert result_dict["success"] is True
        assert result_dict["tool_name"] == "test_tool"
        assert result_dict["structured"] == {"key": "value"}
        assert result_dict["text"] == "Success"
        assert result_dict["error"] is None
        assert "execution_time_ms" in result_dict
        assert "started_at" in result_dict
        assert "completed_at" in result_dict


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
