"""Tests for BaseSkill abstract class."""

import pytest
import asyncio
import time
from unittest.mock import Mock, MagicMock
from typing import Dict, Any, Optional

from agent_core.base.skill import (
    BaseSkill,
    SkillConfig,
    SkillStatus,
    SkillExecutionContext,
    SkillExecutionResult,
)


class TestSkill(BaseSkill):
    """Test implementation of BaseSkill."""

    def __init__(self, config: Optional[SkillConfig] = None):
        super().__init__(config or SkillConfig(name="test_skill"))
        self.last_context: Optional[SkillExecutionContext] = None
        self.before_execute_called = False
        self.after_execute_called = False

    async def _on_initialize(self) -> bool:
        """Initialization hook."""
        return True

    async def _execute(self, context: SkillExecutionContext) -> SkillExecutionResult:
        """Core execution logic."""
        self.last_context = context
        return SkillExecutionResult.success(
            skill_name=self.name,
            sub_task=context.sub_task,
            structured={
                "echo": context.user_input,
                "task_id": context.task_id
            },
            text=f"Executed: {context.user_input}"
        )

    async def _before_execute(self, context: SkillExecutionContext) -> None:
        """Before execute hook."""
        self.before_execute_called = True

    async def _after_execute(
        self,
        context: SkillExecutionContext,
        result: SkillExecutionResult
    ) -> None:
        """After execute hook."""
        self.after_execute_called = True

    async def _on_shutdown(self) -> bool:
        """Shutdown hook."""
        return True


class FailingSkill(BaseSkill):
    """A skill that always fails during execution."""

    async def _on_initialize(self) -> bool:
        return True

    async def _execute(self, context: SkillExecutionContext) -> SkillExecutionResult:
        raise Exception("Intentional execution failure")

    async def _on_shutdown(self) -> bool:
        return True


class TestBaseSkill:
    """Tests for BaseSkill abstract class."""

    @pytest.fixture
    def skill_config(self):
        """Create a basic skill configuration."""
        return SkillConfig(
            name="test_skill",
            version="1.0.0",
            description="Test skill",
            author="Test Author",
            tags=["test", "example"],
            triggers=["test_trigger", "example_trigger"],
            timeout_seconds=30,
            max_retries=3,
        )

    @pytest.fixture
    def test_skill(self, skill_config):
        """Create a TestSkill instance."""
        return TestSkill(skill_config)

    @pytest.fixture
    def execution_context(self):
        """Create an execution context."""
        return SkillExecutionContext(
            task_id="test-task-001",
            sub_task="test_subtask",
            user_input="test user input",
            conversation_history=[],
            previous_results={},
            environment={"env": "test"},
            user_id="user123",
            session_id="session456",
        )

    def test_initialization(self, test_skill, skill_config):
        """Test that skill initializes correctly."""
        assert test_skill.name == "test_skill"
        assert test_skill.version == "1.0.0"
        assert test_skill.config.description == "Test skill"
        assert test_skill.config.author == "Test Author"
        assert test_skill.config.tags == ["test", "example"]
        assert test_skill.config.triggers == ["test_trigger", "example_trigger"]
        assert test_skill.status == SkillStatus.INACTIVE
        assert test_skill.created_at is not None
        assert test_skill.last_executed_at is None
        assert test_skill.execution_count == 0
        assert test_skill.success_count == 0
        assert test_skill.error_count == 0
        assert test_skill.avg_execution_time_ms == 0.0

    @pytest.mark.asyncio
    async def test_skill_initialize(self, test_skill):
        """Test skill initialization."""
        assert test_skill.status == SkillStatus.INACTIVE

        result = await test_skill.initialize()

        assert result is True
        assert test_skill.status == SkillStatus.READY

    @pytest.mark.asyncio
    async def test_successful_execution(self, test_skill, execution_context):
        """Test successful skill execution."""
        await test_skill.initialize()

        result = await test_skill.execute(execution_context)

        assert isinstance(result, SkillExecutionResult)
        assert result.success is True
        assert result.skill_name == "test_skill"
        assert result.sub_task == "test_subtask"
        assert result.structured["echo"] == "test user input"
        assert result.structured["task_id"] == "test-task-001"
        assert result.text == "Executed: test user input"
        assert result.error is None
        assert result.execution_time_ms > 0
        assert test_skill.last_context == execution_context
        assert test_skill.before_execute_called is True
        assert test_skill.after_execute_called is True
        assert test_skill.execution_count == 1
        assert test_skill.success_count == 1
        assert test_skill.error_count == 0
        assert test_skill.last_executed_at is not None

    @pytest.mark.asyncio
    async def test_execution_with_error(self):
        """Test error handling in execute method."""
        config = SkillConfig(name="failing_skill")
        skill = FailingSkill(config)
        await skill.initialize()

        context = SkillExecutionContext(sub_task="fail_task", user_input="test")
        result = await skill.execute(context)

        assert result.success is False
        assert result.skill_name == "failing_skill"
        assert result.sub_task == "fail_task"
        assert result.error == "Intentional execution failure"
        assert skill.execution_count == 1
        assert skill.success_count == 0
        assert skill.error_count == 1
        assert skill.status == SkillStatus.ERROR

    @pytest.mark.asyncio
    async def test_multiple_executions(self, test_skill, execution_context):
        """Test multiple executions accumulate statistics."""
        await test_skill.initialize()

        # First execution
        result1 = await test_skill.execute(execution_context)
        assert result1.success is True

        # Second execution
        execution_context2 = SkillExecutionContext(
            task_id="test-task-002",
            sub_task="task2",
            user_input="input2"
        )
        result2 = await test_skill.execute(execution_context2)
        assert result2.success is True

        # Third execution
        execution_context3 = SkillExecutionContext(
            task_id="test-task-003",
            sub_task="task3",
            user_input="input3"
        )
        result3 = await test_skill.execute(execution_context3)
        assert result3.success is True

        assert test_skill.execution_count == 3
        assert test_skill.success_count == 3
        assert test_skill.error_count == 0
        assert test_skill.avg_execution_time_ms > 0

    @pytest.mark.asyncio
    async def test_skill_shutdown(self, test_skill):
        """Test skill shutdown."""
        await test_skill.initialize()
        assert test_skill.status == SkillStatus.READY

        result = await test_skill.shutdown()

        assert result is True
        assert test_skill.status == SkillStatus.INACTIVE

    @pytest.mark.asyncio
    async def test_skill_status_transitions(self, test_skill):
        """Test skill status transitions through lifecycle."""
        # Initial state
        assert test_skill.status == SkillStatus.INACTIVE

        # After initialize
        await test_skill.initialize()
        assert test_skill.status == SkillStatus.READY

        # During execution (status should be RUNNING during execution)
        # We can't easily test the running status since it's internal,
        # but we can verify the final status
        context = SkillExecutionContext(sub_task="test", user_input="test")
        await test_skill.execute(context)
        assert test_skill.status == SkillStatus.READY

        # After shutdown
        await test_skill.shutdown()
        assert test_skill.status == SkillStatus.INACTIVE

    def test_can_handle_trigger(self, test_skill):
        """Test can_handle with triggers."""
        assert test_skill.can_handle("test_trigger") is True
        assert test_skill.can_handle("example_trigger") is True
        assert test_skill.can_handle("unknown_trigger") is False
        assert test_skill.can_handle("TEST_TRIGGER") is True  # Case insensitive
        assert test_skill.can_handle("This is a test_trigger for you") is True

    def test_can_handle_without_triggers(self):
        """Test can_handle when no triggers are configured."""
        config = SkillConfig(name="skill_no_triggers", triggers=[])
        skill = TestSkill(config)

        assert skill.can_handle("anything") is False
        assert skill.can_handle("test") is False

    def test_get_metadata(self, test_skill):
        """Test get_metadata returns complete metadata."""
        metadata = test_skill.get_metadata()

        assert metadata["name"] == "test_skill"
        assert metadata["version"] == "1.0.0"
        assert metadata["description"] == "Test skill"
        assert metadata["author"] == "Test Author"
        assert metadata["tags"] == ["test", "example"]
        assert metadata["triggers"] == ["test_trigger", "example_trigger"]
        assert metadata["status"] == "inactive"
        assert metadata["created_at"] == test_skill.created_at
        assert metadata["last_executed_at"] is None
        assert metadata["execution_count"] == 0
        assert metadata["success_count"] == 0
        assert metadata["error_count"] == 0
        assert metadata["avg_execution_time_ms"] == 0.0

    @pytest.mark.asyncio
    async def test_metadata_updates_after_execution(self, test_skill, execution_context):
        """Test that metadata updates after execution."""
        await test_skill.initialize()
        await test_skill.execute(execution_context)

        metadata = test_skill.get_metadata()

        assert metadata["status"] == "ready"
        assert metadata["execution_count"] == 1
        assert metadata["success_count"] == 1
        assert metadata["error_count"] == 0
        assert metadata["last_executed_at"] is not None
        assert metadata["avg_execution_time_ms"] > 0

    def test_string_representation(self, test_skill):
        """Test __str__ and __repr__ methods."""
        str_repr = str(test_skill)
        repr_repr = repr(test_skill)

        assert "test_skill" in str_repr
        assert "1.0.0" in str_repr
        assert "inactive" in str_repr

        assert "TestSkill" in repr_repr
        assert "test_skill" in repr_repr
        assert "1.0.0" in repr_repr
        assert "inactive" in repr_repr

    def test_skill_config_defaults(self):
        """Test SkillConfig default values."""
        config = SkillConfig(name="minimal_skill")

        assert config.name == "minimal_skill"
        assert config.version == "1.0.0"
        assert config.description == ""
        assert config.author == ""
        assert config.tags == []
        assert config.triggers == []
        assert config.timeout_seconds == 60
        assert config.max_retries == 3
        assert config.requires_approval is False
        assert config.custom_settings == {}


class TestSkillExecutionContext:
    """Tests for SkillExecutionContext."""

    def test_context_initialization(self):
        """Test execution context initialization."""
        context = SkillExecutionContext(
            request_id="req-123",
            task_id="task-456",
            sub_task="test_subtask",
            user_input="user input",
            conversation_history=[{"role": "user", "content": "hello"}],
            previous_results={"skill1": {"data": "value"}},
            environment={"env": "test"},
            tenant_id="tenant-789",
            user_id="user-001",
            session_id="session-001",
            metadata={"key": "value"},
        )

        assert context.request_id == "req-123"
        assert context.task_id == "task-456"
        assert context.sub_task == "test_subtask"
        assert context.user_input == "user input"
        assert len(context.conversation_history) == 1
        assert "skill1" in context.previous_results
        assert context.environment["env"] == "test"
        assert context.tenant_id == "tenant-789"
        assert context.user_id == "user-001"
        assert context.session_id == "session-001"
        assert context.metadata["key"] == "value"
        assert context.started_at is not None

    def test_context_defaults(self):
        """Test context default values."""
        context = SkillExecutionContext()

        assert context.request_id is not None
        assert context.task_id is not None
        assert context.sub_task == ""
        assert context.user_input == ""
        assert context.conversation_history == []
        assert context.previous_results == {}
        assert context.environment == {}
        assert context.tenant_id is None
        assert context.user_id is None
        assert context.session_id is None
        assert context.metadata == {}
        assert context.started_at is not None

    def test_context_to_dict(self):
        """Test context to_dict conversion."""
        context = SkillExecutionContext(
            request_id="req-123",
            task_id="task-456",
            sub_task="test_subtask",
            user_input="user input",
        )

        context_dict = context.to_dict()

        assert isinstance(context_dict, dict)
        assert context_dict["request_id"] == "req-123"
        assert context_dict["task_id"] == "task-456"
        assert context_dict["sub_task"] == "test_subtask"
        assert context_dict["user_input"] == "user input"
        assert "started_at" in context_dict
        assert "metadata" in context_dict


class TestSkillExecutionResult:
    """Tests for SkillExecutionResult."""

    def test_success_creation(self):
        """Test creating a success result."""
        result = SkillExecutionResult.success(
            skill_name="test_skill",
            sub_task="test_task",
            structured={"key": "value"},
            text="Success message",
            execution_time_ms=100.5,
            metadata={"meta": "data"},
        )

        assert result.success is True
        assert result.skill_name == "test_skill"
        assert result.sub_task == "test_task"
        assert result.structured["key"] == "value"
        assert result.text == "Success message"
        assert result.error is None
        assert result.execution_time_ms == 100.5
        assert result.metadata["meta"] == "data"
        assert result.started_at is not None
        assert result.completed_at is not None

    def test_failure_creation(self):
        """Test creating a failure result."""
        result = SkillExecutionResult.failure(
            skill_name="test_skill",
            sub_task="test_task",
            error="Something went wrong",
            execution_time_ms=50.0,
            metadata={"meta": "data"},
        )

        assert result.success is False
        assert result.skill_name == "test_skill"
        assert result.sub_task == "test_task"
        assert result.structured == {}
        assert result.text == ""
        assert result.error == "Something went wrong"
        assert result.execution_time_ms == 50.0
        assert result.metadata["meta"] == "data"

    def test_result_to_dict(self):
        """Test result to_dict conversion."""
        result = SkillExecutionResult.success(
            skill_name="test_skill",
            sub_task="test_task",
            structured={"key": "value"},
            text="Success",
        )

        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert result_dict["success"] is True
        assert result_dict["skill_name"] == "test_skill"
        assert result_dict["sub_task"] == "test_task"
        assert result_dict["structured"]["key"] == "value"
        assert result_dict["text"] == "Success"
        assert result_dict["error"] is None
        assert "execution_time_ms" in result_dict
        assert "started_at" in result_dict
        assert "completed_at" in result_dict
        assert "metadata" in result_dict


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
