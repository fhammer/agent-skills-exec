"""Tests for AgentContext."""

import pytest
from agent.context import AgentContext
from agent.audit import AuditLayer, AuditOp


class TestAgentContext:
    """Test AgentContext functionality."""

    def test_init(self):
        """Test context initialization."""
        context = AgentContext()
        assert context._layer1 is not None
        assert context._scratchpad is not None
        assert context._layer3 is not None

    def test_write_read_layer1(self):
        """Test writing and reading from Layer 1."""
        context = AgentContext()
        context.set_component("coordinator")

        context.write_layer1("test_key", "test_value", "test")
        value = context.read_layer1("test_key", "test")
        assert value == "test_value"

    def test_layer1_permissions(self):
        """Test Layer 1 permission control."""
        context = AgentContext()

        # Planner should be able to write to Layer 1
        context.set_component("planner")
        context.write_layer1("intent", "test", "planner")
        assert context.read_layer1("intent") == "test"

    def test_scratchpad_operations(self):
        """Test scratchpad operations."""
        context = AgentContext()
        context.set_component("executor")

        context.write_scratchpad(
            "test_skill",
            "test task",
            {"key": "value"},
            "test output"
        )

        result = context.read_scratchpad("test_skill")
        assert result is not None
        assert result.skill_name == "test_skill"

    def test_audit_logging(self):
        """Test audit logging."""
        context = AgentContext(enable_audit=True)
        context.set_component("coordinator")

        context.write_layer1("test", "value", "test_source")

        assert len(context.audit_log.entries) == 1
        entry = context.audit_log.entries[0]
        assert entry.layer == AuditLayer.USER_INPUT
        assert entry.op == AuditOp.WRITE
        assert entry.key == "test"

    def test_prepare_for_step(self):
        """Test step context preparation."""
        context = AgentContext()

        # Add some data
        context.write_layer1("raw_user_input", "test input", "coordinator")
        context.scratchpad.set_result("skill1", "task1", {"data": "result1"}, "output1")

        step = {"skill": "skill2", "sub_task": "do something"}
        prepared = context.prepare_for_step(step)

        assert "sub_task" in prepared
        assert "user_input" in prepared
        assert "previous_results" in prepared
