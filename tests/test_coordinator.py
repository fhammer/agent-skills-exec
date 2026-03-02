"""Tests for Coordinator module."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from agent.coordinator import Coordinator
from agent.context import AgentContext
from agent.errors import AgentError
from config import Config


class TestCoordinator:
    """Test Coordinator functionality."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration."""
        config = Mock(spec=Config)

        # Create mock budget
        mock_budget = Mock()
        mock_budget.total_limit = 100000
        mock_budget.warning_threshold = 0.8
        mock_budget.enable_compression = True
        config.budget = mock_budget

        # Create mock execution
        mock_execution = Mock()
        mock_execution.enable_audit_log = True
        mock_execution.confidence_threshold = 0.7
        config.execution = mock_execution

        # Create mock llm
        mock_llm = Mock()
        mock_llm.provider = "openai"
        mock_llm.api_key = "test_key"
        mock_llm.model = "test_model"
        mock_llm.base_url = None
        config.llm = mock_llm

        config.skills_dir = Mock()
        config.skills_dir.__str__ = Mock(return_value="/tmp/skills")
        return config

    @pytest.fixture
    def coordinator(self, mock_config):
        """Create a Coordinator instance with mocked dependencies."""
        with patch('agent.coordinator.LLMClient'), \
             patch('agent.coordinator.SkillRegistry'), \
             patch.object(Coordinator, '_create_llm_provider') as mock_create_provider:

            # Create mock LLM provider
            mock_provider = Mock()
            mock_create_provider.return_value = mock_provider

            coord = Coordinator(mock_config)
            return coord

    def test_coordinator_initialization(self, coordinator):
        """Test coordinator initializes all components."""
        assert coordinator.llm_client is not None
        assert coordinator.tools is not None
        assert coordinator.context is not None
        assert coordinator.planner is not None
        assert coordinator.executor is not None
        assert coordinator.synthesizer is not None

    def test_process_basic_request(self, coordinator):
        """Test basic request processing."""
        # Mock the planner to return a simple plan
        coordinator.planner.generate_plan = MagicMock(return_value=[
            {"skill": "test_skill", "sub_task": "test task"}
        ])

        # Mock the executor to return a result
        coordinator.executor.execute_step = MagicMock(return_value={
            "structured": {"result": "test"},
            "text": "Test output"
        })

        # Mock the synthesizer
        coordinator.synthesizer.synthesize = MagicMock(return_value={
            "final_response": "Test complete"
        })

        result = coordinator.process("test input")

        assert result is not None
        assert "final_response" in result

    def test_process_with_empty_input(self, coordinator):
        """Test processing with empty input."""
        coordinator.planner.generate_plan = MagicMock(return_value=[])

        result = coordinator.process("")

        # Verify that an error is returned
        assert result["success"] is False
        assert "error" in result

    def test_metrics_tracking(self, coordinator):
        """Test that metrics are tracked correctly."""
        initial_requests = coordinator._metrics["total_requests"]

        coordinator.planner.generate_plan = MagicMock(return_value=[
            {"skill": "test", "sub_task": "test"}
        ])
        coordinator.executor.execute_step = MagicMock(return_value={"text": "test"})
        coordinator.synthesizer.synthesize = MagicMock(return_value={
            "final_response": "done"
        })

        coordinator.process("test")

        assert coordinator._metrics["total_requests"] == initial_requests + 1

    def test_audit_log_enabled(self, mock_config):
        """Test audit logging is enabled when configured."""
        mock_config.execution.enable_audit_log = True
        with patch('agent.coordinator.LLMClient'), \
             patch('agent.coordinator.SkillRegistry'), \
             patch.object(Coordinator, '_create_llm_provider') as mock_create_provider:

            # Create mock LLM provider
            mock_provider = Mock()
            mock_create_provider.return_value = mock_provider

            coord = Coordinator(mock_config)
            assert coord.context.audit_log is not None

    def test_get_audit_trail(self, coordinator):
        """Test retrieving audit trail."""
        trail = coordinator.get_audit_trail()
        assert isinstance(trail, list)


class TestCoordinatorIntegration:
    """Integration tests for Coordinator with skills."""

    @pytest.fixture
    def mock_config_with_skills(self):
        """Config with mocked skill registry."""
        config = Mock(spec=Config)

        # Create mock budget
        mock_budget = Mock()
        mock_budget.total_limit = 100000
        mock_budget.warning_threshold = 0.8
        mock_budget.enable_compression = False

        # Ensure that budget.used and budget.total are numeric
        mock_budget.used = 0
        mock_budget.total = 100000

        config.budget = mock_budget

        # Create mock execution
        mock_execution = Mock()
        mock_execution.enable_audit_log = False
        mock_execution.confidence_threshold = 0.7
        config.execution = mock_execution

        # Create mock llm
        mock_llm = Mock()
        mock_llm.provider = "openai"
        mock_llm.api_key = "test_key"
        mock_llm.model = "test_model"
        mock_llm.base_url = None
        config.llm = mock_llm

        config.skills_dir = Mock()
        config.skills_dir.__str__ = Mock(return_value="/tmp/skills")
        return config

    def test_multi_step_execution(self, mock_config_with_skills):
        """Test coordinator handling multi-step execution."""
        with patch('agent.coordinator.LLMClient'), \
             patch('agent.coordinator.SkillRegistry'), \
             patch.object(Coordinator, '_create_llm_provider') as mock_create_provider:

            # Create mock LLM provider
            mock_provider = Mock()
            mock_create_provider.return_value = mock_provider

            coordinator = Coordinator(mock_config_with_skills)

            # Mock a multi-step plan
            # 确保 token budget 不会导致执行停止 - 更全面的模拟
            # 直接替换整个 budget 对象，确保所有方法都能正确响应
            mock_budget = Mock()
            mock_budget.used = 0
            mock_budget.total = 10000
            mock_budget.usage_ratio.return_value = 0.0  # 0% 使用率，确保不会触发限制
            mock_budget.get_compression_ratio.return_value = 0.0
            mock_budget.check_budget.return_value = True
            mock_budget.consume_tokens.return_value = None
            mock_budget.get_summary.return_value = {"used": 0, "total": 10000}
            mock_budget.can_compress.return_value = False

            coordinator.llm_client.budget = mock_budget

            from agent.planner import ExecutionPlan
            mock_plan = ExecutionPlan(
                intent="multi_step_intent",
                steps=[
                    {"skill": "skill1", "sub_task": "step 1"},
                    {"skill": "skill2", "sub_task": "step 2"},
                    {"skill": "skill3", "sub_task": "step 3"}
                ]
            )
            coordinator.planner.generate_plan = MagicMock(return_value=mock_plan)

            # Mock executor responses
            coordinator.executor.execute = MagicMock(side_effect=[
                {"structured": {"step": 1}, "text": "Step 1 complete", "success": True},
                {"structured": {"step": 2}, "text": "Step 2 complete", "success": True},
                {"structured": {"step": 3}, "text": "Step 3 complete", "success": True}
            ])

            coordinator.synthesizer.synthesize = MagicMock(return_value={
                "final_response": "All steps complete"
            })

            result = None
            try:
                result = coordinator.process("multi-step request")
                print(f"Result: {result}")
                print(f"Number of executed steps: {coordinator.executor.execute.call_count}")
                if coordinator.executor.execute.called:
                    print(f"Call arguments: {coordinator.executor.execute.call_args_list}")
            except Exception as e:
                import traceback
                print(f"Error: {e}")
                print(f"Stack trace: {traceback.format_exc()}")

            # Verify all steps were executed
            print(f"Expected steps: 3, Executed steps: {coordinator.executor.execute.call_count}")
            assert coordinator.executor.execute.call_count == 3
            assert result["final_response"]["final_response"] == "All steps complete"

    def test_error_handling_in_execution(self, mock_config_with_skills):
        """Test coordinator handles executor errors gracefully."""
        with patch('agent.coordinator.LLMClient'), \
             patch('agent.coordinator.SkillRegistry'), \
             patch.object(Coordinator, '_create_llm_provider') as mock_create_provider:

            # Create mock LLM provider
            mock_provider = Mock()
            mock_create_provider.return_value = mock_provider

            coordinator = Coordinator(mock_config_with_skills)

            from agent.planner import ExecutionPlan
            mock_plan = ExecutionPlan(
                intent="failing_intent",
                steps=[{"skill": "failing_skill", "sub_task": "this will fail"}]
            )
            coordinator.planner.generate_plan = MagicMock(return_value=mock_plan)

            # Mock executor to raise an error
            coordinator.executor.execute_step = MagicMock(
                side_effect=Exception("Skill execution failed")
            )

            coordinator.synthesizer.synthesize = MagicMock(return_value={
                "final_response": "Error handled"
            })

            # Coordinator should handle the error
            result = coordinator.process("failing request")

            # Should still return a response
            assert result is not None
