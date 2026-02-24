import pytest

from backend.schemas.agent_messages import AgentMessage, AgentProtocol


def test_create_valid_message():
    """Happy Path: Geldig bericht."""
    msg = AgentMessage(source="agent_a", target="agent_b", type="SIGNAL", payload={"buy": True})
    assert msg.source == "agent_a"


def test_serialize_deserialize():
    """Happy Path: JSON conversie."""
    msg = AgentMessage(
        source="agent_a", target="all", type="BROADCAST", payload={"alert": "high_vol"}
    )
    json_str = msg.to_json()
    msg2 = AgentProtocol.parse(json_str)

    assert msg2.payload["alert"] == "high_vol"
    assert msg2.timestamp is not None


def test_invalid_message_type():
    """Unhappy Path: Onbekend message type."""
    with pytest.raises(ValueError):
        AgentMessage(source="a", target="b", type="UNKNOWN_TYPE", payload={})  # FOUT
