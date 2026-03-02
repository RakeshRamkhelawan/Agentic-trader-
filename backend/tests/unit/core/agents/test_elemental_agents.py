
from backend.core.agents.base import ElementType
from backend.core.agents.elements import AgniAgent, AkashaAgent, JalaAgent, PrithviAgent, VayuAgent


class TestElementalAgents:

    def test_prithvi_agent_initialization(self):
        agent = PrithviAgent()
        assert agent.name == "Prithvi"
        assert agent.element == ElementType.EARTH
        assert agent.prana == 1.0
        assert agent.is_active == True

    def test_jala_agent_initialization(self):
        agent = JalaAgent()
        assert agent.name == "Jala"
        assert agent.element == ElementType.WATER

    def test_agni_agent_initialization(self):
        agent = AgniAgent()
        assert agent.name == "Agni"
        assert agent.element == ElementType.FIRE

    def test_vayu_agent_initialization(self):
        agent = VayuAgent()
        assert agent.name == "Vayu"
        assert agent.element == ElementType.AIR

    def test_akasha_agent_initialization(self):
        agent = AkashaAgent()
        assert agent.name == "Akasha"
        assert agent.element == ElementType.ETHER

    def test_prana_mechanics(self):
        agent = PrithviAgent()

        # Test expenditure
        agent.expend_prana(0.5)
        assert agent.prana == 0.5

        # Test regeneration
        agent.regenerate_prana(0.2)
        assert agent.prana == 0.7

        # Test max cap
        agent.regenerate_prana(1.0)
        assert agent.prana == 1.0

        # Test exhaustion
        agent.expend_prana(0.95)  # 1.0 - 0.95 = 0.05
        assert agent.prana < 0.1
        assert agent.is_active == False

        # Test wake up
        agent.regenerate_prana(0.2)
        assert agent.prana > 0.2
        agent.wake_up()
        assert agent.is_active == True

    def test_prithvi_process_cycle_high_risk(self):
        agent = PrithviAgent()
        perception = {"risk_metrics": {"exposure": 0.8}}  # High risk
        decision = agent.process_cycle(perception, {})

        assert decision["action"] == "hold"
        assert decision["veto"] == True
        assert agent.prana < 1.0  # Expended energy to hold

    def test_jala_process_cycle_flow(self):
        agent = JalaAgent()
        perception = {"flow_metrics": {"momentum": 0.6}}  # High momentum
        decision = agent.process_cycle(perception, {})

        assert decision["action"] == "flow"
        assert decision["direction"] == "long"
        assert agent.prana == 1.0  # Max prana (regenerated)

    def test_agni_process_cycle_opportunity(self):
        agent = AgniAgent()
        perception = {"opportunity_score": 0.9}  # High opportunity
        decision = agent.process_cycle(perception, {})

        assert decision["action"] == "execute"
        assert decision["urgency"] == "high"
        assert agent.prana < 1.0  # Expended energy

    def test_vayu_process_cycle_volatility(self):
        agent = VayuAgent()
        perception = {"volatility": 0.6}
        decision = agent.process_cycle(perception, {})

        assert decision["action"] == "adjust"
        assert decision["strategy"] == "dynamic"
        assert agent.prana == 1.0

    def test_akasha_process_cycle_network(self):
        agent = AkashaAgent()
        perception = {"system_health": {"network": 0.5}}  # Bad network
        decision = agent.process_cycle(perception, {})

        assert decision["action"] == "warn"
        assert agent.prana < 1.0
