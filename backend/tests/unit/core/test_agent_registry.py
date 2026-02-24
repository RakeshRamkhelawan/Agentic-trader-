import pytest

from backend.core.agent_registry import AgentProfile, AgentRegistry


# --- FIXTURES ---
@pytest.fixture
def agent_registry():
    """Returns an AgentRegistry instance loaded with the sample profiles."""
    return AgentRegistry(config_path="backend/config/agent_profiles.yaml")


# --- TESTS ---
def test_load_all_agent_profiles(agent_registry):
    """Happy Path: Alle profielen worden geladen."""
    assert len(agent_registry.profiles) == 5
    assert "orchestrator_v1" in agent_registry.profiles
    assert "research_v1" in agent_registry.profiles


def test_get_specific_agent_profile(agent_registry):
    """Happy Path: Specifiek profiel ophalen."""
    orchestrator = agent_registry.get_profile("orchestrator_v1")
    assert orchestrator.name == "Cognitive Core"
    assert orchestrator.element == "ether"
    assert orchestrator.guna_composition.sattva == 0.8
    assert "You are the manifestation of Sattva" in orchestrator.system_directive


def test_non_existent_profile(agent_registry):
    """Unhappy Path: Ongeldig ID."""
    assert agent_registry.get_profile("unknown_agent") is None


def test_agent_profile_validation():
    """Unhappy Path: Invalid profile data should raise error."""
    # Simuleer een ongeldig profiel (bijv. missing field)
    with pytest.raises(Exception):  # Pydantic ValidationError
        AgentProfile(
            id="test",
            name="Test",
            element="invalid",
            guna_composition={"sattva": 1.0, "rajas": 0.0, "tamas": 0.0},
            # Missing system_directive and allowed_tools
        )
