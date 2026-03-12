"""Tests for Agent abstract base class."""

import pytest
from unittest.mock import Mock, MagicMock
from typing import Dict, Any, Optional, List
from agent_core.base.agent import Agent, AgentConfig, AgentState


class SimpleAgent(Agent):
    """A simple concrete agent implementation for testing."""

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self._skills: Dict[str, Any] = {}
        self._tools: Dict[str, Any] = {}
        self._connectors: Dict[str, Any] = {}
        self._audit_trail: List[Dict[str, Any]] = []

    async def initialize(self) -> bool:
        self._state = AgentState.READY
        self._last_activity_at = self._created_at
        return True

    async def process(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        self._last_activity_at = self._created_at
        self._metrics["total_tasks"] += 1
        self._metrics["successful_tasks"] += 1
        return {
            "success": True,
            "input": user_input,
            "context": context
        }

    async def pause(self) -> bool:
        self._state = AgentState.PAUSED
        self._last_activity_at = self._created_at
        return True

    async def resume(self) -> bool:
        self._state = AgentState.READY
        self._last_activity_at = self._created_at
        return True

    async def shutdown(self) -> bool:
        self._state = AgentState.SHUTDOWN
        self._last_activity_at = self._created_at
        return True

    def get_audit_trail(self) -> List[Dict[str, Any]]:
        return self._audit_trail.copy()

    def get_config(self) -> Dict[str, Any]:
        return self.config.__dict__.copy()

    def add_skill(self, skill: Any) -> None:
        self._skills[skill.name] = skill

    def add_tool(self, tool: Any) -> None:
        self._tools[tool.name] = tool

    def add_connector(self, connector: Any) -> None:
        self._connectors[connector.name] = connector

    def get_skill(self, name: str) -> Optional[Any]:
        return self._skills.get(name)

    def get_tool(self, name: str) -> Optional[Any]:
        return self._tools.get(name)

    def get_connector(self, name: str) -> Optional[Any]:
        return self._connectors.get(name)

    def remove_skill(self, name: str) -> None:
        if name in self._skills:
            del self._skills[name]

    def remove_tool(self, name: str) -> None:
        if name in self._tools:
            del self._tools[name]

    def remove_connector(self, name: str) -> None:
        if name in self._connectors:
            del self._connectors[name]

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def version(self) -> str:
        return self.config.version

    @property
    def id(self) -> str:
        return f"agent_{id(self)}"

    @property
    def skills(self) -> List[Any]:
        return list(self._skills.values())

    @property
    def tools(self) -> List[Any]:
        return list(self._tools.values())

    @property
    def connectors(self) -> List[Any]:
        return list(self._connectors.values())


class MockSkill:
    """A mock skill for testing."""
    def __init__(self, name: str = "test_skill"):
        self.name = name
        self.status = "ready"


class MockTool:
    """A mock tool for testing."""
    def __init__(self, name: str = "test_tool"):
        self.name = name
        self.status = "ready"


class MockConnector:
    """A mock connector for testing."""
    def __init__(self, name: str = "test_connector"):
        self.name = name
        self.status = "ready"


class TestAgent:
    """Tests for Agent abstract base class."""

    @pytest.fixture
    def agent_config(self):
        """Create an agent configuration."""
        return AgentConfig(
            name="test_agent",
            version="1.0.0",
            description="Test agent",
            max_concurrent_tasks=5,
            timeout_seconds=60,
            custom_settings={"key": "value"}
        )

    @pytest.fixture
    def simple_agent(self, agent_config):
        """Create a SimpleAgent instance."""
        return SimpleAgent(agent_config)

    @pytest.fixture
    async def initialized_agent(self, simple_agent):
        """Create an initialized agent."""
        await simple_agent.initialize()
        yield simple_agent
        await simple_agent.shutdown()

    @pytest.fixture
    def mock_skill(self):
        """Create a mock skill."""
        return MockSkill(name="simple_skill")

    @pytest.fixture
    def mock_tool(self):
        """Create a mock tool."""
        return MockTool(name="simple_tool")

    @pytest.fixture
    def mock_connector(self):
        """Create a mock connector."""
        return MockConnector(name="simple_connector")

    def test_agent_initial_state(self, simple_agent, agent_config):
        """Test agent initial state."""
        assert simple_agent.config == agent_config
        assert simple_agent.state == AgentState.INITIALIZING
        assert simple_agent.name == "test_agent"
        assert simple_agent.version == "1.0.0"
        assert simple_agent.id is not None
        assert simple_agent.created_at is not None
        assert simple_agent.last_activity_at is not None
        assert simple_agent.metrics["total_tasks"] == 0
        assert simple_agent.metrics["successful_tasks"] == 0
        assert simple_agent.metrics["failed_tasks"] == 0

    @pytest.mark.asyncio
    async def test_agent_initialize(self, simple_agent):
        """Test agent initialization."""
        assert simple_agent.state == AgentState.INITIALIZING

        result = await simple_agent.initialize()

        assert result is True
        assert simple_agent.state == AgentState.READY

    @pytest.mark.asyncio
    async def test_agent_process(self, initialized_agent):
        """Test agent process method."""
        result = await initialized_agent.process("test input", {"context_key": "value"})

        assert result["success"] is True
        assert result["input"] == "test input"
        assert result["context"] == {"context_key": "value"}
        assert initialized_agent.metrics["total_tasks"] == 1
        assert initialized_agent.metrics["successful_tasks"] == 1

    @pytest.mark.asyncio
    async def test_agent_pause_resume(self, initialized_agent):
        """Test agent pause and resume."""
        assert initialized_agent.state == AgentState.READY

        result = await initialized_agent.pause()
        assert result is True
        assert initialized_agent.state == AgentState.PAUSED

        result = await initialized_agent.resume()
        assert result is True
        assert initialized_agent.state == AgentState.READY

    @pytest.mark.asyncio
    async def test_agent_shutdown(self, initialized_agent):
        """Test agent shutdown."""
        result = await initialized_agent.shutdown()

        assert result is True
        assert initialized_agent.state == AgentState.SHUTDOWN

    def test_agent_get_config(self, simple_agent):
        """Test get_config method."""
        config = simple_agent.get_config()

        assert config["name"] == "test_agent"
        assert config["version"] == "1.0.0"
        assert config["description"] == "Test agent"
        assert config["max_concurrent_tasks"] == 5
        assert config["timeout_seconds"] == 60

    def test_agent_get_audit_trail(self, simple_agent):
        """Test get_audit_trail method."""
        trail = simple_agent.get_audit_trail()
        assert isinstance(trail, list)
        assert len(trail) == 0

    def test_agent_update_metrics(self, simple_agent):
        """Test update_metrics method."""
        simple_agent._metrics["total_tasks"] = 1
        simple_agent.update_metrics(True, 100.0)

        assert simple_agent.metrics["successful_tasks"] == 1
        assert simple_agent.metrics["total_execution_time_ms"] == 100.0
        assert simple_agent.metrics["avg_execution_time_ms"] == 100.0

    def test_add_remove_skill(self, simple_agent, mock_skill):
        """Test adding and removing skills."""
        assert len(simple_agent.skills) == 0

        simple_agent.add_skill(mock_skill)
        assert len(simple_agent.skills) == 1
        assert simple_agent.get_skill("simple_skill") == mock_skill

        simple_agent.remove_skill("simple_skill")
        assert len(simple_agent.skills) == 0
        assert simple_agent.get_skill("simple_skill") is None

    def test_add_remove_tool(self, simple_agent, mock_tool):
        """Test adding and removing tools."""
        assert len(simple_agent.tools) == 0

        simple_agent.add_tool(mock_tool)
        assert len(simple_agent.tools) == 1
        assert simple_agent.get_tool("simple_tool") == mock_tool

        simple_agent.remove_tool("simple_tool")
        assert len(simple_agent.tools) == 0
        assert simple_agent.get_tool("simple_tool") is None

    def test_add_remove_connector(self, simple_agent, mock_connector):
        """Test adding and removing connectors."""
        assert len(simple_agent.connectors) == 0

        simple_agent.add_connector(mock_connector)
        assert len(simple_agent.connectors) == 1
        assert simple_agent.get_connector("simple_connector") == mock_connector

        simple_agent.remove_connector("simple_connector")
        assert len(simple_agent.connectors) == 0
        assert simple_agent.get_connector("simple_connector") is None

    @pytest.mark.asyncio
    async def test_agent_lifecycle(self, simple_agent):
        """Test complete agent lifecycle."""
        agent = simple_agent

        assert agent.state == AgentState.INITIALIZING

        await agent.initialize()
        assert agent.state == AgentState.READY

        await agent.pause()
        assert agent.state == AgentState.PAUSED

        await agent.resume()
        assert agent.state == AgentState.READY

        await agent.shutdown()
        assert agent.state == AgentState.SHUTDOWN

    def test_agent_with_multiple_skills(self, simple_agent):
        """Test agent with multiple skills."""
        for i in range(3):
            skill = MockSkill(name=f"skill_{i}")
            simple_agent.add_skill(skill)

        assert len(simple_agent.skills) == 3

        for i in range(3):
            assert simple_agent.get_skill(f"skill_{i}") is not None

    def test_agent_with_resources(self, simple_agent, mock_skill, mock_tool, mock_connector):
        """Test agent with all resources."""
        simple_agent.add_skill(mock_skill)
        simple_agent.add_tool(mock_tool)
        simple_agent.add_connector(mock_connector)

        assert len(simple_agent.skills) == 1
        assert len(simple_agent.tools) == 1
        assert len(simple_agent.connectors) == 1

        assert simple_agent.get_skill("simple_skill") is not None
        assert simple_agent.get_tool("simple_tool") is not None
        assert simple_agent.get_connector("simple_connector") is not None

    def test_string_representation(self, simple_agent):
        """Test __str__ and __repr__ methods."""
        str_repr = str(simple_agent)
        repr_repr = repr(simple_agent)

        assert "test_agent" in str_repr
        assert "1.0.0" in str_repr
        assert "initializing" in str_repr

        assert "SimpleAgent" in repr_repr
        assert "test_agent" in repr_repr
        assert "1.0.0" in repr_repr
        assert "initializing" in repr_repr


class TestAgentState:
    """Tests for AgentState enum."""

    def test_agent_state_values(self):
        """Test AgentState enum values."""
        assert AgentState.INITIALIZING.value == "initializing"
        assert AgentState.READY.value == "ready"
        assert AgentState.RUNNING.value == "running"
        assert AgentState.PAUSED.value == "paused"
        assert AgentState.ERROR.value == "error"
        assert AgentState.SHUTTING_DOWN.value == "shutting_down"
        assert AgentState.SHUTDOWN.value == "shutdown"

    def test_agent_state_comparison(self):
        """Test AgentState comparison."""
        state1 = AgentState.READY
        state2 = AgentState.READY
        state3 = AgentState.PAUSED

        assert state1 == state2
        assert state1 != state3
        assert state1.value == "ready"


class TestAgentConfig:
    """Tests for AgentConfig dataclass."""

    def test_agent_config_defaults(self):
        """Test AgentConfig default values."""
        config = AgentConfig()

        assert config.name == "default_agent"
        assert config.version == "1.0.0"
        assert config.description == "Default agent configuration"
        assert config.max_concurrent_tasks == 10
        assert config.timeout_seconds == 300
        assert config.enable_audit is True
        assert config.enable_metrics is True
        assert config.custom_settings == {}

    def test_agent_config_custom(self):
        """Test AgentConfig with custom values."""
        config = AgentConfig(
            name="custom_agent",
            version="2.0.0",
            description="My custom agent",
            max_concurrent_tasks=20,
            timeout_seconds=600,
            enable_audit=False,
            enable_metrics=False,
            custom_settings={"custom_key": "custom_value"}
        )

        assert config.name == "custom_agent"
        assert config.version == "2.0.0"
        assert config.description == "My custom agent"
        assert config.max_concurrent_tasks == 20
        assert config.timeout_seconds == 600
        assert config.enable_audit is False
        assert config.enable_metrics is False
        assert config.custom_settings == {"custom_key": "custom_value"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
