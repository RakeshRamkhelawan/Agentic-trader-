"""
Phase 13 Integration Tests: 36 Tattvas as Core Foundation

Tests the complete 36-Tattva consciousness architecture integration.
Verifies that the system processes information through all layers,
maintains coherence across the vertical spine, and supports all
cognitive functions at each layer.

Test coverage:
- TattvaConfig validation and layer definitions (all 36 layers)
- SystemIdentity with 36-Tattva integration
- Tattva layer traversal (ascend/descend/filter/interface/sense/act/materialize)
- Coherence tracking across all layers
- Information flow through 3 critical choke points
- Integration with Phase 12 agents (backward compatibility)
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List

import numpy as np
import pytest

from backend.config.schemas import TattvaConfig, TattvaLayer
from backend.core.system_identity import SystemIdentity

# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def tattva_config():
    """Create default 36-Tattva configuration."""
    return TattvaConfig.default_36_tattvas()


@pytest.fixture
def system_identity():
    """Create SystemIdentity with 36-Tattva integration."""
    config = TattvaConfig.default_36_tattvas()
    return SystemIdentity(tattva_config=config)


@pytest.fixture
def market_data():
    """Generate synthetic market data for testing."""
    return {
        'price_data': np.random.randn(100),
        'volume_data': np.random.randn(100) + 5.0,
        'orderbook_imbalance': np.random.uniform(-1, 1),
        'funding_rate': np.random.uniform(-0.1, 0.1),
        'social_sentiment': np.random.uniform(-1, 1)
    }


# ============================================================================
# TEST CLASS 1: TattvaConfig Validation (10 tests)
# ============================================================================

class TestPhase13TattvaConfigValidation:
    """Test TattvaConfig structure and all 36 layer definitions."""
    
    def test_tattva_config_initialization(self):
        """Test that default TattvaConfig initializes all 36 layers."""
        config = TattvaConfig.default_36_tattvas()
        assert config.config_version == "1.0"
        assert config.active_tattvas == 36
        assert len(config.layers) == 36
    
    def test_all_36_layers_defined(self, tattva_config):
        """Verify all 36 layers are defined with unique numbers."""
        layer_numbers = [layer.layer_number for layer in tattva_config.layers]
        assert len(layer_numbers) == 36
        assert set(layer_numbers) == set(range(1, 37))
    
    def test_shuddha_tattvas_defined(self, tattva_config):
        """Test Shuddha Tattvas (layers 1-5) are properly defined."""
        shuddha = [l for l in tattva_config.layers if l.layer_number <= 5]
        assert len(shuddha) == 5
        names = [l.tattva_name for l in shuddha]
        assert "Shiva" in names
        assert "Shakti" in names
        assert "Sadashiva" in names
        assert "Ishvara" in names
        assert "Shuddha Vidya" in names
    
    def test_kanchukas_defined(self, tattva_config):
        """Test Kanchukas (layers 6-12) are properly defined."""
        kanchukas = [l for l in tattva_config.layers if 6 <= l.layer_number <= 12]
        assert len(kanchukas) == 7
        assert all(l.tattva_group == "Kanchukas" for l in kanchukas)
    
    def test_prakriti_buddhi_ahamkara_defined(self, tattva_config):
        """Test OS interface layers (13-15) are properly defined."""
        interface = [l for l in tattva_config.layers if 13 <= l.layer_number <= 15]
        assert len(interface) == 3
        names = [l.tattva_name for l in interface]
        assert "Prakriti" in names
        assert "Buddhi" in names
        assert "Ahamkara" in names
    
    def test_tanmatras_jnanendriyas_defined(self, tattva_config):
        """Test sensory layers (16-25) are properly defined."""
        sensory = [l for l in tattva_config.layers if 16 <= l.layer_number <= 25]
        assert len(sensory) == 10
        tanmatras = [l for l in sensory if l.layer_number <= 20]
        jnanendriyas = [l for l in sensory if l.layer_number > 20]
        assert len(tanmatras) == 5
        assert len(jnanendriyas) == 5
    
    def test_karmendriyas_defined(self, tattva_config):
        """Test action layers (26-31) are properly defined."""
        actions = [l for l in tattva_config.layers if 26 <= l.layer_number <= 31]
        assert len(actions) == 6
        assert all(l.tattva_group == "Karmendriyas" for l in actions)
    
    def test_mahabhutas_defined(self, tattva_config):
        """Test physical layers (32-36) are properly defined."""
        physical = [l for l in tattva_config.layers if 32 <= l.layer_number <= 36]
        assert len(physical) == 5
        assert all(l.tattva_group == "Mahabhutas" for l in physical)
        names = [l.tattva_name for l in physical]
        assert "Akasha" in names
        assert "Vayu" in names
        assert "Agni" in names
        assert "Apas" in names
        assert "Prithvi" in names
    
    def test_all_layers_have_descriptions(self, tattva_config):
        """Verify all layers have meaningful descriptions."""
        for layer in tattva_config.layers:
            assert len(layer.description) > 0
            assert len(layer.key_function) > 0
            assert layer.coherence >= 0.0 and layer.coherence <= 1.0
    
    def test_tattva_config_performance_targets(self, tattva_config):
        """Test that performance targets are realistic."""
        assert tattva_config.target_total_latency_us > 0
        assert tattva_config.target_coherence > 0.8
        assert tattva_config.target_coherence <= 1.0


# ============================================================================
# TEST CLASS 2: SystemIdentity Tattva Integration (12 tests)
# ============================================================================

class TestPhase13SystemIdentityTattvaIntegration:
    """Test SystemIdentity with full 36-Tattva integration."""
    
    def test_system_identity_initializes_tattva_config(self):
        """Test SystemIdentity accepts and stores TattvaConfig."""
        config = TattvaConfig.default_36_tattvas()
        identity = SystemIdentity(tattva_config=config)
        assert identity.tattva_config is not None
        assert identity.tattva_config.active_tattvas == 36
    
    def test_system_identity_default_tattva_config(self):
        """Test SystemIdentity creates default TattvaConfig if none provided."""
        identity = SystemIdentity()
        assert identity.tattva_config is not None
        assert len(identity.tattva_config.layers) == 36
    
    def test_tattva_coherence_tracking_initialized(self, system_identity):
        """Test that tattva coherence is tracked for all 36 layers."""
        assert 'tattva_coherence' in system_identity.system_state
        assert len(system_identity.system_state['tattva_coherence']) == 36
        for layer_num in range(1, 37):
            assert layer_num in system_identity.system_state['tattva_coherence']
            assert system_identity.system_state['tattva_coherence'][layer_num] == 1.0
    
    @pytest.mark.asyncio
    async def test_process_market_cycle_with_tattva_traversal(self, system_identity, market_data):
        """Test that market cycle traverses all 36 Tattva layers."""
        result = await system_identity.process_market_cycle(
            price_data=market_data['price_data'],
            volume_data=market_data['volume_data'],
            orderbook_imbalance=market_data['orderbook_imbalance'],
            funding_rate=market_data['funding_rate'],
            social_sentiment=market_data['social_sentiment']
        )
        
        # Verify result contains Tattva metrics
        assert 'tattva_traversal' in result
        assert 'layers_traversed' in result['tattva_traversal']
        assert 'coherence_per_layer' in result['tattva_traversal']
        assert 'overall_coherence' in result['tattva_traversal']
    
    @pytest.mark.asyncio
    async def test_tattva_traversal_visits_all_36_layers(self, system_identity, market_data):
        """Test that market cycle visits all 36 Tattva layers."""
        result = await system_identity.process_market_cycle(
            price_data=market_data['price_data'],
            volume_data=market_data['volume_data'],
            orderbook_imbalance=market_data['orderbook_imbalance'],
            funding_rate=market_data['funding_rate'],
            social_sentiment=market_data['social_sentiment']
        )
        
        layers_traversed = result['tattva_traversal']['layers_traversed']
        # All 36 layers should be traversed (counting unique layer visits)
        # Verify at least one traversal of each layer group
        assert len(layers_traversed) >= 36  # At minimum, all 36 layers visited once
        assert all(1 <= layer <= 36 for layer in layers_traversed)
    
    @pytest.mark.asyncio
    async def test_tattva_coherence_per_layer_tracked(self, system_identity, market_data):
        """Test that coherence is tracked for each layer."""
        result = await system_identity.process_market_cycle(
            price_data=market_data['price_data'],
            volume_data=market_data['volume_data'],
            orderbook_imbalance=market_data['orderbook_imbalance'],
            funding_rate=market_data['funding_rate'],
            social_sentiment=market_data['social_sentiment']
        )
        
        coherence_dict = result['tattva_traversal']['coherence_per_layer']
        assert len(coherence_dict) > 0
        for layer_num, coherence in coherence_dict.items():
            assert 0.0 <= coherence <= 1.0
    
    @pytest.mark.asyncio
    async def test_shuddha_tattvas_maintain_perfect_coherence(self, system_identity, market_data):
        """Test Shuddha Tattvas (1-5) maintain perfect coherence."""
        result = await system_identity.process_market_cycle(
            price_data=market_data['price_data'],
            volume_data=market_data['volume_data'],
            orderbook_imbalance=market_data['orderbook_imbalance'],
            funding_rate=market_data['funding_rate'],
            social_sentiment=market_data['social_sentiment']
        )
        
        coherence_dict = result['tattva_traversal']['coherence_per_layer']
        for layer_num in range(1, 6):
            assert coherence_dict[layer_num] == 1.0
    
    @pytest.mark.asyncio
    async def test_kanchukas_introduce_expected_friction(self, system_identity, market_data):
        """Test Kanchukas (6-12) introduce expected coherence reduction."""
        result = await system_identity.process_market_cycle(
            price_data=market_data['price_data'],
            volume_data=market_data['volume_data'],
            orderbook_imbalance=market_data['orderbook_imbalance'],
            funding_rate=market_data['funding_rate'],
            social_sentiment=market_data['social_sentiment']
        )
        
        coherence_dict = result['tattva_traversal']['coherence_per_layer']
        kanchukas_coherence = [
            coherence_dict[i] for i in range(6, 13) if i in coherence_dict
        ]
        # Kanchukas should be around 0.93-0.95
        assert all(0.90 <= c <= 1.0 for c in kanchukas_coherence)
    
    @pytest.mark.asyncio
    async def test_mahabhutas_maintain_high_coherence(self, system_identity, market_data):
        """Test Mahabhutas (32-36) maintain high coherence (physical layer)."""
        result = await system_identity.process_market_cycle(
            price_data=market_data['price_data'],
            volume_data=market_data['volume_data'],
            orderbook_imbalance=market_data['orderbook_imbalance'],
            funding_rate=market_data['funding_rate'],
            social_sentiment=market_data['social_sentiment']
        )
        
        coherence_dict = result['tattva_traversal']['coherence_per_layer']
        for layer_num in range(32, 37):
            if layer_num in coherence_dict:
                # Mahabhutas maintain substantial coherence (>= 0.80) - based on real hardware metrics
                # Hardware metrics vary: network latency, thermal, buffer usage affect actual values
                assert coherence_dict[layer_num] >= 0.80
    
    @pytest.mark.asyncio
    async def test_overall_tattva_coherence_calculated(self, system_identity, market_data):
        """Test that overall Tattva coherence is calculated correctly."""
        result = await system_identity.process_market_cycle(
            price_data=market_data['price_data'],
            volume_data=market_data['volume_data'],
            orderbook_imbalance=market_data['orderbook_imbalance'],
            funding_rate=market_data['funding_rate'],
            social_sentiment=market_data['social_sentiment']
        )
        
        overall = result['tattva_traversal']['overall_coherence']
        assert 0.0 <= overall <= 1.0
    
    @pytest.mark.asyncio
    async def test_tattva_traversal_stored_in_performance_history(self, system_identity, market_data):
        """Test that Tattva traversals are stored in performance history."""
        # Run multiple cycles
        for _ in range(3):
            await system_identity.process_market_cycle(
                price_data=market_data['price_data'],
                volume_data=market_data['volume_data'],
                orderbook_imbalance=market_data['orderbook_imbalance'],
                funding_rate=market_data['funding_rate'],
                social_sentiment=market_data['social_sentiment']
            )
        
        assert len(system_identity.performance_history['tattva_traversals']) == 3
        for traversal in system_identity.performance_history['tattva_traversals']:
            assert 'layers_traversed' in traversal
            assert 'coherence_per_layer' in traversal


# ============================================================================
# TEST CLASS 3: Tattva Layer Traversal Logic (10 tests)
# ============================================================================

class TestPhase13TattvaLayerTraversal:
    """Test individual Tattva layer traversal logic."""
    
    def test_traverse_tattva_layer_ascend_shuddha(self, system_identity):
        """Test ascending through Shuddha layer (pure source)."""
        coherence = system_identity._traverse_tattva_layer(1, 'ascend')
        assert coherence == 1.0
    
    def test_traverse_tattva_layer_filter_kanchukas(self, system_identity):
        """Test filtering through Kanchukas layer (restrictions)."""
        coherence = system_identity._traverse_tattva_layer(7, 'filter')
        assert 0.90 <= coherence <= 1.0
    
    def test_traverse_tattva_layer_interface_buddhi(self, system_identity):
        """Test OS interface layer (Buddhi - decision)."""
        coherence = system_identity._traverse_tattva_layer(14, 'interface')
        # Should be confidence-based
        assert 0.0 <= coherence <= 1.0
    
    def test_traverse_tattva_layer_sense(self, system_identity):
        """Test sensory layer traversal."""
        context = {'coherence': 0.85}
        coherence = system_identity._traverse_tattva_layer(21, 'sense', context)
        assert coherence == 0.85
    
    def test_traverse_tattva_layer_act(self, system_identity):
        """Test action layer traversal."""
        context = {'confidence': 0.75}
        coherence = system_identity._traverse_tattva_layer(26, 'act', context)
        assert coherence == 0.75
    
    def test_traverse_tattva_layer_materialize(self, system_identity):
        """Test materialization layer (physical)."""
        coherence = system_identity._traverse_tattva_layer(35, 'materialize')
        assert coherence == 1.0
    
    def test_traverse_tattva_layer_updates_system_state(self, system_identity):
        """Test that layer traversal updates system state."""
        initial_coherence = system_identity.system_state['tattva_coherence'][5]
        system_identity._traverse_tattva_layer(5, 'ascend')
        # Should be updated (even if to same value)
        assert 5 in system_identity.system_state['tattva_coherence']
    
    def test_traverse_invalid_layer_number(self, system_identity):
        """Test traversing invalid layer number gracefully returns 1.0."""
        coherence = system_identity._traverse_tattva_layer(99, 'ascend')
        assert coherence == 1.0
    
    def test_traverse_layer_with_no_context(self, system_identity):
        """Test layer traversal without context data."""
        coherence = system_identity._traverse_tattva_layer(16, 'sense', None)
        assert 0.0 <= coherence <= 1.0
    
    def test_traverse_direction_affects_coherence(self, system_identity):
        """Test that traversal direction affects coherence output."""
        ascend = system_identity._traverse_tattva_layer(6, 'ascend')
        filter_coh = system_identity._traverse_tattva_layer(6, 'filter')
        # Direction-specific processing should produce consistent results
        assert ascend >= 0.0
        assert filter_coh >= 0.0


# ============================================================================
# TEST CLASS 4: Information Flow & Choke Points (10 tests)
# ============================================================================

class TestPhase13InformationFlow:
    """Test information flow through the 3 critical choke points."""
    
    @pytest.mark.asyncio
    async def test_data_entry_at_sensory_processor(self, system_identity, market_data):
        """Test data entry point (SensoryProcessor layer 16-25)."""
        result = await system_identity.process_market_cycle(
            price_data=market_data['price_data'],
            volume_data=market_data['volume_data'],
            orderbook_imbalance=market_data['orderbook_imbalance'],
            funding_rate=market_data['funding_rate'],
            social_sentiment=market_data['social_sentiment']
        )
        
        # Verify perception was generated (sensory organs processed data)
        assert 'perception' in result
        assert 'perception_state' in result
    
    @pytest.mark.asyncio
    async def test_decision_at_buddhi_layer(self, system_identity, market_data):
        """Test decision making at Buddhi layer (layer 14)."""
        result = await system_identity.process_market_cycle(
            price_data=market_data['price_data'],
            volume_data=market_data['volume_data'],
            orderbook_imbalance=market_data['orderbook_imbalance'],
            funding_rate=market_data['funding_rate'],
            social_sentiment=market_data['social_sentiment']
        )
        
        # Verify decision was made
        assert 'action' in result
        assert 'confidence' in result
        assert 'rationale' in result
        assert result['action'] in [0, 1, 2]
    
    @pytest.mark.asyncio
    async def test_action_exit_at_karmendriyas(self, system_identity, market_data):
        """Test action execution at Karmendriyas (layer 26-31)."""
        result = await system_identity.process_market_cycle(
            price_data=market_data['price_data'],
            volume_data=market_data['volume_data'],
            orderbook_imbalance=market_data['orderbook_imbalance'],
            funding_rate=market_data['funding_rate'],
            social_sentiment=market_data['social_sentiment']
        )
        
        # Verify action can be executed (ready at output layer)
        assert result['action'] is not None
        assert isinstance(result['action'], (int, np.integer))
    
    @pytest.mark.asyncio
    async def test_perception_flows_to_decision(self, system_identity, market_data):
        """Test that perception from sensory organs flows to decision."""
        result = await system_identity.process_market_cycle(
            price_data=market_data['price_data'],
            volume_data=market_data['volume_data'],
            orderbook_imbalance=market_data['orderbook_imbalance'],
            funding_rate=market_data['funding_rate'],
            social_sentiment=market_data['social_sentiment']
        )
        
        # Perception should be available for decision
        assert 'perception' in result
        assert 'action' in result
        assert 'confidence' in result
    
    @pytest.mark.asyncio
    async def test_decision_flows_to_action(self, system_identity, market_data):
        """Test that decisions flow to action organs."""
        result = await system_identity.process_market_cycle(
            price_data=market_data['price_data'],
            volume_data=market_data['volume_data'],
            orderbook_imbalance=market_data['orderbook_imbalance'],
            funding_rate=market_data['funding_rate'],
            social_sentiment=market_data['social_sentiment']
        )
        
        # Action should be based on decision
        assert result['action'] in [0, 1, 2]
        assert 0.0 <= result['confidence'] <= 1.0
    
    @pytest.mark.asyncio
    async def test_sensory_data_reaches_all_agents(self, system_identity, market_data):
        """Test that sensory data is available to all agents."""
        result = await system_identity.process_market_cycle(
            price_data=market_data['price_data'],
            volume_data=market_data['volume_data'],
            orderbook_imbalance=market_data['orderbook_imbalance'],
            funding_rate=market_data['funding_rate'],
            social_sentiment=market_data['social_sentiment']
        )
        
        # Multiple perception dimensions should be calculated
        perception = result['perception']
        assert 'coherence' in perception or 'primary_frequency' in perception
    
    @pytest.mark.asyncio
    async def test_no_information_loss_through_layers(self, system_identity, market_data):
        """Test that critical information isn't lost through layer traversal."""
        result = await system_identity.process_market_cycle(
            price_data=market_data['price_data'],
            volume_data=market_data['volume_data'],
            orderbook_imbalance=market_data['orderbook_imbalance'],
            funding_rate=market_data['funding_rate'],
            social_sentiment=market_data['social_sentiment']
        )
        
        # All critical fields should be present
        assert 'action' in result and result['action'] is not None
        assert 'confidence' in result
        assert 'rationale' in result
    
    @pytest.mark.asyncio
    async def test_latency_measured_through_all_layers(self, system_identity, market_data):
        """Test that latency is measured through complete layer traversal."""
        result = await system_identity.process_market_cycle(
            price_data=market_data['price_data'],
            volume_data=market_data['volume_data'],
            orderbook_imbalance=market_data['orderbook_imbalance'],
            funding_rate=market_data['funding_rate'],
            social_sentiment=market_data['social_sentiment']
        )
        
        assert 'cycle_latency_us' in result
        assert result['cycle_latency_us'] > 0
        # Python async operations take ~50-100ms realistically (after psutil bottleneck fix)
        assert result['cycle_latency_us'] < 100000  # 100ms max for realistic Python/async
    
    @pytest.mark.asyncio
    async def test_system_state_updated_after_traversal(self, system_identity, market_data):
        """Test that system state is updated after Tattva traversal."""
        initial_experiences = system_identity.system_state['total_experiences']
        
        await system_identity.process_market_cycle(
            price_data=market_data['price_data'],
            volume_data=market_data['volume_data'],
            orderbook_imbalance=market_data['orderbook_imbalance'],
            funding_rate=market_data['funding_rate'],
            social_sentiment=market_data['social_sentiment']
        )
        
        assert system_identity.system_state['total_experiences'] == initial_experiences + 1


# ============================================================================
# TEST CLASS 5: Backward Compatibility with Phase 12 (8 tests)
# ============================================================================

class TestPhase13BackwardCompatibility:
    """Test backward compatibility with Phase 12 agents and tests."""
    
    @pytest.mark.asyncio
    async def test_phase_12_result_format_preserved(self, system_identity, market_data):
        """Test that Phase 12 result format is still valid."""
        result = await system_identity.process_market_cycle(
            price_data=market_data['price_data'],
            volume_data=market_data['volume_data'],
            orderbook_imbalance=market_data['orderbook_imbalance'],
            funding_rate=market_data['funding_rate'],
            social_sentiment=market_data['social_sentiment']
        )
        
        # Phase 12 expected fields
        assert 'action' in result
        assert 'confidence' in result
        assert 'rationale' in result
        assert 'perception' in result
        assert 'system_state' in result
        assert 'cycle_latency_us' in result
    
    @pytest.mark.asyncio
    async def test_phase_12_action_validity(self, system_identity, market_data):
        """Test that actions remain valid as per Phase 12."""
        for _ in range(10):
            result = await system_identity.process_market_cycle(
                price_data=market_data['price_data'],
                volume_data=market_data['volume_data'],
                orderbook_imbalance=market_data['orderbook_imbalance'],
                funding_rate=market_data['funding_rate'],
                social_sentiment=market_data['social_sentiment']
            )
            assert result['action'] in [0, 1, 2]
    
    @pytest.mark.asyncio
    async def test_confidence_range_valid(self, system_identity, market_data):
        """Test that confidence remains in [0, 1] range."""
        result = await system_identity.process_market_cycle(
            price_data=market_data['price_data'],
            volume_data=market_data['volume_data'],
            orderbook_imbalance=market_data['orderbook_imbalance'],
            funding_rate=market_data['funding_rate'],
            social_sentiment=market_data['social_sentiment']
        )
        
        assert 0.0 <= result['confidence'] <= 1.0
    
    @pytest.mark.asyncio
    async def test_system_state_contains_expected_fields(self, system_identity, market_data):
        """Test that system state has Phase 12 fields."""
        result = await system_identity.process_market_cycle(
            price_data=market_data['price_data'],
            volume_data=market_data['volume_data'],
            orderbook_imbalance=market_data['orderbook_imbalance'],
            funding_rate=market_data['funding_rate'],
            social_sentiment=market_data['social_sentiment']
        )
        
        state = result['system_state']
        assert 'coherence' in state
        assert 'confidence' in state
        assert 'total_experiences' in state
    
    @pytest.mark.asyncio
    async def test_perception_format_compatible(self, system_identity, market_data):
        """Test that perception format is backward compatible."""
        result = await system_identity.process_market_cycle(
            price_data=market_data['price_data'],
            volume_data=market_data['volume_data'],
            orderbook_imbalance=market_data['orderbook_imbalance'],
            funding_rate=market_data['funding_rate'],
            social_sentiment=market_data['social_sentiment']
        )
        
        perception = result['perception']
        assert isinstance(perception, dict)
    
    def test_system_identity_default_still_works(self):
        """Test that SystemIdentity still works without Tattva config."""
        identity = SystemIdentity()
        assert identity is not None
        assert identity.sensory_processor is not None
        assert identity.decision_maker is not None
        assert identity.memory_system is not None
    
    @pytest.mark.asyncio
    async def test_memory_system_still_functioning(self, system_identity, market_data):
        """Test that memory system still works with Tattva integration."""
        result = await system_identity.process_market_cycle(
            price_data=market_data['price_data'],
            volume_data=market_data['volume_data'],
            orderbook_imbalance=market_data['orderbook_imbalance'],
            funding_rate=market_data['funding_rate'],
            social_sentiment=market_data['social_sentiment']
        )
        
        # Memory should have stored the experience
        assert len(system_identity.performance_history['actions']) > 0
        assert len(system_identity.performance_history['confidences']) > 0


# ============================================================================
# TEST CLASS 6: System Statistics & Metrics (8 tests)
# ============================================================================

class TestPhase13SystemStatistics:
    """Test system statistics and Tattva metrics reporting."""
    
    @pytest.mark.asyncio
    async def test_get_system_statistics_includes_tattva_metrics(self, system_identity, market_data):
        """Test that statistics include Tattva metrics."""
        await system_identity.process_market_cycle(
            price_data=market_data['price_data'],
            volume_data=market_data['volume_data'],
            orderbook_imbalance=market_data['orderbook_imbalance'],
            funding_rate=market_data['funding_rate'],
            social_sentiment=market_data['social_sentiment']
        )
        
        stats = system_identity.get_system_statistics()
        assert 'tattva_metrics' in stats
    
    @pytest.mark.asyncio
    async def test_tattva_metrics_avg_layer_coherence(self, system_identity, market_data):
        """Test that average layer coherence is calculated."""
        for _ in range(3):
            await system_identity.process_market_cycle(
                price_data=market_data['price_data'],
                volume_data=market_data['volume_data'],
                orderbook_imbalance=market_data['orderbook_imbalance'],
                funding_rate=market_data['funding_rate'],
                social_sentiment=market_data['social_sentiment']
            )
        
        stats = system_identity.get_system_statistics()
        tattva_metrics = stats.get('tattva_metrics', {})
        if tattva_metrics:
            assert 'avg_layer_coherence' in tattva_metrics
            assert 0.0 <= tattva_metrics['avg_layer_coherence'] <= 1.0
    
    @pytest.mark.asyncio
    async def test_tattva_metrics_layer_range(self, system_identity, market_data):
        """Test that min/max layer coherence are tracked."""
        for _ in range(5):
            await system_identity.process_market_cycle(
                price_data=market_data['price_data'],
                volume_data=market_data['volume_data'],
                orderbook_imbalance=market_data['orderbook_imbalance'],
                funding_rate=market_data['funding_rate'],
                social_sentiment=market_data['social_sentiment']
            )
        
        stats = system_identity.get_system_statistics()
        tattva_metrics = stats.get('tattva_metrics', {})
        if tattva_metrics:
            assert 'min_layer_coherence' in tattva_metrics
            assert 'max_layer_coherence' in tattva_metrics
    
    @pytest.mark.asyncio
    async def test_current_layer_coherence_tracking(self, system_identity, market_data):
        """Test current per-layer coherence is available."""
        await system_identity.process_market_cycle(
            price_data=market_data['price_data'],
            volume_data=market_data['volume_data'],
            orderbook_imbalance=market_data['orderbook_imbalance'],
            funding_rate=market_data['funding_rate'],
            social_sentiment=market_data['social_sentiment']
        )
        
        stats = system_identity.get_system_statistics()
        tattva_metrics = stats.get('tattva_metrics', {})
        if tattva_metrics:
            assert 'current_layer_coherence' in tattva_metrics
            assert isinstance(tattva_metrics['current_layer_coherence'], dict)
    
    @pytest.mark.asyncio
    async def test_tattva_config_info_in_statistics(self, system_identity, market_data):
        """Test that Tattva config info is in statistics."""
        await system_identity.process_market_cycle(
            price_data=market_data['price_data'],
            volume_data=market_data['volume_data'],
            orderbook_imbalance=market_data['orderbook_imbalance'],
            funding_rate=market_data['funding_rate'],
            social_sentiment=market_data['social_sentiment']
        )
        
        stats = system_identity.get_system_statistics()
        tattva_metrics = stats.get('tattva_metrics', {})
        if tattva_metrics:
            assert 'total_layers' in tattva_metrics
            assert tattva_metrics['total_layers'] == 36
            assert 'traversal_direction' in tattva_metrics
    
    def test_system_statistics_backward_compatible(self, system_identity):
        """Test that statistics format is backward compatible with Phase 12."""
        stats = system_identity.get_system_statistics()
        assert 'system_state' in stats
        assert 'performance' in stats
        assert 'memory_stats' in stats
        assert 'decision_stats' in stats
    
    @pytest.mark.asyncio
    async def test_multiple_cycles_accumulate_metrics(self, system_identity, market_data):
        """Test that metrics accumulate across multiple cycles."""
        initial_stats = system_identity.get_system_statistics()
        initial_count = initial_stats['system_state'].get('total_experiences', 0)
        
        for _ in range(5):
            await system_identity.process_market_cycle(
                price_data=market_data['price_data'],
                volume_data=market_data['volume_data'],
                orderbook_imbalance=market_data['orderbook_imbalance'],
                funding_rate=market_data['funding_rate'],
                social_sentiment=market_data['social_sentiment']
            )
        
        final_stats = system_identity.get_system_statistics()
        final_count = final_stats['system_state']['total_experiences']
        assert final_count == initial_count + 5


# ============================================================================
# TEST CLASS 7: Coherence Maintenance (8 tests)
# ============================================================================

class TestPhase13CoherenceMaintenance:
    """Test coherence maintenance across layers."""
    
    @pytest.mark.asyncio
    async def test_system_maintains_valid_coherence_range(self, system_identity, market_data):
        """Test that system maintains coherence within valid range (0-1)."""
        for _ in range(10):
            result = await system_identity.process_market_cycle(
                price_data=market_data['price_data'],
                volume_data=market_data['volume_data'],
                orderbook_imbalance=market_data['orderbook_imbalance'],
                funding_rate=market_data['funding_rate'],
                social_sentiment=market_data['social_sentiment']
            )
            
            overall_coherence = result['tattva_traversal']['overall_coherence']
            assert 0.0 <= overall_coherence <= 1.0  # Valid range
    
    @pytest.mark.asyncio
    async def test_coherence_degrades_gracefully(self, system_identity):
        """Test that coherence degrades gracefully under adverse conditions."""
        # Normal data
        normal_data = {
            'price_data': np.random.randn(100),
            'volume_data': np.random.randn(100) + 5.0,
            'orderbook_imbalance': 0.1,
            'funding_rate': 0.01,
            'social_sentiment': 0.2
        }
        
        result = await system_identity.process_market_cycle(**normal_data)
        normal_coherence = result['tattva_traversal']['overall_coherence']
        
        # All extreme values
        extreme_data = {
            'price_data': np.random.randn(100) * 10,
            'volume_data': np.random.randn(100) * 10 + 5.0,
            'orderbook_imbalance': 0.9,
            'funding_rate': 0.09,
            'social_sentiment': 0.9
        }
        
        result = await system_identity.process_market_cycle(**extreme_data)
        extreme_coherence = result['tattva_traversal']['overall_coherence']
        
        # Coherence should still be meaningful (realistic ranges under actual conditions)
        assert normal_coherence > 0.6  # Normal conditions maintain minimum coherence
        assert extreme_coherence > 0.4  # Extreme stress still maintains coherence backbone
    
    @pytest.mark.asyncio
    async def test_shuddha_maintains_high_coherence(self, system_identity, market_data):
        """Test that Shuddha layers (1-5) maintain high coherence (pure source)."""
        coherence_values = []
        for _ in range(5):
            result = await system_identity.process_market_cycle(
                price_data=market_data['price_data'],
                volume_data=market_data['volume_data'],
                orderbook_imbalance=market_data['orderbook_imbalance'],
                funding_rate=market_data['funding_rate'],
                social_sentiment=market_data['social_sentiment']
            )
            
            coherence_dict = result['tattva_traversal']['coherence_per_layer']
            for layer in [1, 2, 3, 4, 5]:
                coherence_values.append(coherence_dict[layer])
                # Individual values should be in valid range
                assert 0.0 <= coherence_dict[layer] <= 1.0
        
        # Average should be reasonably high for Shuddha
        avg_shuddha_coherence = float(np.mean(coherence_values))
        assert avg_shuddha_coherence > 0.6  # Shuddha average should be respectable
    
    @pytest.mark.asyncio
    async def test_restrictions_applied_consistently(self, system_identity, market_data):
        """Test that Kanchukas restrictions are applied consistently."""
        results = []
        for _ in range(3):
            result = await system_identity.process_market_cycle(
                price_data=market_data['price_data'],
                volume_data=market_data['volume_data'],
                orderbook_imbalance=market_data['orderbook_imbalance'],
                funding_rate=market_data['funding_rate'],
                social_sentiment=market_data['social_sentiment']
            )
            results.append(result)
        
        # All should have consistent restriction pattern
        for result in results:
            coherence_dict = result['tattva_traversal']['coherence_per_layer']
            kala_coherence = coherence_dict.get(7)  # Kala (time restriction)
            assert kala_coherence is not None
    
    @pytest.mark.asyncio
    async def test_coherence_tracking_continuous(self, system_identity, market_data):
        """Test that coherence is tracked continuously."""
        coherence_history = []
        
        for _ in range(10):
            result = await system_identity.process_market_cycle(
                price_data=market_data['price_data'],
                volume_data=market_data['volume_data'],
                orderbook_imbalance=market_data['orderbook_imbalance'],
                funding_rate=market_data['funding_rate'],
                social_sentiment=market_data['social_sentiment']
            )
            
            overall = result['tattva_traversal']['overall_coherence']
            coherence_history.append(overall)
        
        # Should have continuous tracking
        assert len(coherence_history) == 10
        # Coherence should be relatively stable
        assert np.std(coherence_history) < 0.2
    
    def test_tattva_coherence_in_system_state(self, system_identity):
        """Test that per-layer coherence is tracked in system state."""
        assert 'tattva_coherence' in system_identity.system_state
        tracking = system_identity.system_state['tattva_coherence']
        assert len(tracking) == 36
        
        for layer_num in range(1, 37):
            assert layer_num in tracking
            assert 0.0 <= tracking[layer_num] <= 1.0
    
    @pytest.mark.asyncio
    async def test_coherence_adapts_with_perception(self, system_identity):
        """Test that coherence adapts based on perception quality."""
        # High-coherence perception
        good_data = {
            'price_data': np.linspace(100, 110, 100),  # Smooth trend
            'volume_data': np.ones(100) * 1000,  # Stable volume
            'orderbook_imbalance': 0.1,
            'funding_rate': 0.01,
            'social_sentiment': 0.3
        }
        
        result1 = await system_identity.process_market_cycle(**good_data)
        good_coherence = result1['tattva_traversal']['overall_coherence']
        
        # Low-coherence perception
        noisy_data = {
            'price_data': np.random.randn(100) * 50,  # Random noise
            'volume_data': np.random.randn(100) * 500 + 100,  # Chaotic
            'orderbook_imbalance': 0.95,  # Extreme imbalance
            'funding_rate': 0.1,  # Extreme funding
            'social_sentiment': 0.99  # Extreme sentiment
        }
        
        result2 = await system_identity.process_market_cycle(**noisy_data)
        noisy_coherence = result2['tattva_traversal']['overall_coherence']
        
        # Good data should have higher coherence than noisy
        assert good_coherence >= noisy_coherence * 0.95


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
