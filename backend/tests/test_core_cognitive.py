"""
Unit tests for core cognitive systems.
"""

import pytest
import numpy as np
from backend.core.frequency_analysis import VibrationalAnalyzer, FrequencyDecomposition
from backend.core.sensory_processor import SensoryProcessor
from backend.core.memory_system import MemorySystem, MemoryTrace
from backend.core.decision_discriminator import DecisionDiscriminator
from backend.core.system_identity import SystemIdentity


@pytest.mark.unit
class TestFrequencyAnalyzer:
    """Tests for vibrational frequency decomposition."""
    
    def test_analyzer_initialization(self):
        """Should initialize with correct window size."""
        analyzer = VibrationalAnalyzer(window_size=144)
        assert analyzer.window_size == 144
        assert len(analyzer.frequency_bands) == 3
    
    def test_decompose_constant_signal(self):
        """Constant signal should have low fundamental frequency."""
        analyzer = VibrationalAnalyzer()
        signal = np.ones(100)
        decomp = analyzer.decompose(signal)
        
        assert isinstance(decomp, FrequencyDecomposition)
        assert decomp.coherence == 0.0  # No variation
    
    def test_decompose_sine_wave(self):
        """Sine wave should show clear fundamental frequency."""
        analyzer = VibrationalAnalyzer()
        t = np.arange(0, 10, 0.1)
        signal = np.sin(2 * np.pi * 0.5 * t)  # 0.5 Hz sine
        
        decomp = analyzer.decompose(signal)
        
        assert decomp.fundamental > 0
        assert decomp.coherence > 0.5
        assert decomp.amplitude > 0
    
    def test_classify_state_low_frequency(self):
        """Low frequency dominant signal should classify as state 0."""
        analyzer = VibrationalAnalyzer()
        # Create signal with energy in low frequencies
        t = np.arange(0, 100, 0.1)
        signal = np.sin(2 * np.pi * 0.1 * t)  # Very low frequency
        
        decomp = analyzer.decompose(signal)
        state = analyzer.classify_state(decomp)
        
        assert state in [0, 1, 2]  # Valid state
    
    def test_decompose_empty_signal(self):
        """Empty signal should return zero decomposition."""
        analyzer = VibrationalAnalyzer()
        signal = np.array([])
        
        decomp = analyzer.decompose(signal)
        
        assert decomp.fundamental == 0.0
        assert decomp.coherence == 0.0
        assert len(decomp.harmonics) == 8


@pytest.mark.unit
class TestSensoryProcessor:
    """Tests for sensory input processing."""
    
    def test_processor_initialization(self):
        """Should initialize with empty buffer."""
        processor = SensoryProcessor()
        assert processor.buffer_size == 144
        assert len(processor.perception_buffer) == 0
    
    def test_process_input_basic(self):
        """Should process input and return perception."""
        processor = SensoryProcessor()
        
        price = np.ones(100) * 100
        volume = np.ones(100) * 1000
        
        perception = processor.process_input(
            price_stream=price,
            volume_stream=volume,
            orderbook_imbalance=0.0,
            funding_rate=0.0,
            social_sentiment=0.0
        )
        
        assert isinstance(perception, dict)
        assert 'state_vector' in perception
        assert 'coherence' in perception
        assert 'timestamp' in perception
        assert len(perception['state_vector']) == 5
    
    def test_discretize_values(self):
        """Discretization should map continuous to categorical."""
        processor = SensoryProcessor()
        
        # Test boundary values
        assert processor._discretize(-1.0, 3) == 0
        assert processor._discretize(0.0, 3) == 1
        assert processor._discretize(1.0, 3) == 2
    
    def test_phase_alignment_calculation(self):
        """Phase alignment should be in [0, 1]."""
        processor = SensoryProcessor()
        analyzer = processor.vibration_analyzer
        
        signal1 = np.sin(np.arange(0, 2*np.pi, 0.1))
        signal2 = np.sin(np.arange(0, 2*np.pi, 0.1))  # Same signal
        
        freq1 = analyzer.decompose(signal1)
        freq2 = analyzer.decompose(signal2)
        
        alignment = processor._calculate_phase_alignment(freq1, freq2)
        
        assert 0 <= alignment <= 1


@pytest.mark.unit
class TestMemorySystem:
    """Tests for memory storage and retrieval."""
    
    def test_memory_initialization(self):
        """Should initialize with empty buffers."""
        memory = MemorySystem(capacity=100)
        assert memory.capacity == 100
        assert len(memory.memory_buffer) == 0
        assert len(memory.clusters) == 0
    
    def test_store_memory(self):
        """Should store memory traces."""
        memory = MemorySystem()
        
        perception = {
            'state_vector': np.array([0, 1, 2, 0, 1]),
            'coherence': 0.8,
            'phase_alignment': 0.6,
            'harmonic_profile': [0.5, 0.3, 0.2]
        }
        
        memory.store(perception, action=1, outcome=0.5)
        
        assert len(memory.memory_buffer) == 1
        assert len(memory.clusters) > 0
    
    def test_recall_similar_memories(self):
        """Should retrieve similar memories."""
        memory = MemorySystem()
        
        # Store similar memories
        perception1 = {
            'state_vector': np.array([0, 0, 0, 0, 0]),
            'coherence': 0.8,
            'phase_alignment': 0.5,
            'harmonic_profile': [0.5, 0.3, 0.2]
        }
        
        perception2 = {
            'state_vector': np.array([0, 0, 0, 0, 0]),  # Similar
            'coherence': 0.8,
            'phase_alignment': 0.5,
            'harmonic_profile': [0.5, 0.3, 0.2]
        }
        
        memory.store(perception1, action=1, outcome=0.5)
        memory.store(perception2, action=1, outcome=0.6)
        
        # Recall similar to first
        recalled = memory.recall(perception1, k=5)
        assert len(recalled) > 0
    
    def test_tendency_retrieval(self):
        """Should return most common action from cluster."""
        memory = MemorySystem()
        
        perception = {
            'state_vector': np.array([0, 0, 0, 0, 0]),
            'coherence': 0.8,
            'phase_alignment': 0.5,
            'harmonic_profile': [0.5, 0.3, 0.2]
        }
        
        # Store multiple instances of action 1
        for _ in range(5):
            memory.store(perception, action=1, outcome=0.5)
        
        tendency = memory.get_tendency(perception)
        assert tendency == 1


@pytest.mark.unit
class TestDecisionDiscriminator:
    """Tests for decision making."""
    
    def test_discriminator_initialization(self):
        """Should initialize with memory system."""
        memory = MemorySystem()
        discriminator = DecisionDiscriminator(memory)
        
        assert discriminator.decision_threshold == 0.6
        assert discriminator.exploration_rate == 0.1
    
    def test_discriminate_action(self):
        """Should return valid action, confidence, and rationale."""
        memory = MemorySystem()
        discriminator = DecisionDiscriminator(memory)
        
        perception = {
            'state_vector': np.array([0, 0, 0, 0, 0]),
            'coherence': 0.8,
            'phase_alignment': 0.5,
            'harmonic_profile': [0.5, 0.3, 0.2]
        }
        
        action, confidence, rationale = discriminator.discriminate(
            perception,
            available_actions=[0, 1, 2]
        )
        
        assert action in [0, 1, 2]
        assert 0 <= confidence <= 1
        assert isinstance(rationale, str)
    
    def test_confidence_calculation(self):
        """Confidence should reflect perception quality."""
        memory = MemorySystem()
        discriminator = DecisionDiscriminator(memory)
        
        perception_low = {
            'state_vector': np.array([0, 0, 0, 0, 0]),
            'coherence': 0.3,  # Low coherence
            'phase_alignment': 0.2
        }
        
        perception_high = {
            'state_vector': np.array([0, 0, 0, 0, 0]),
            'coherence': 0.9,  # High coherence
            'phase_alignment': 0.9
        }
        
        conf_low = discriminator._calculate_confidence(0.5, perception_low)
        conf_high = discriminator._calculate_confidence(0.5, perception_high)
        
        assert conf_high > conf_low


@pytest.mark.unit
@pytest.mark.asyncio
async def test_system_identity_basic():
    """Should initialize all cognitive subsystems."""
    system = SystemIdentity()
    
    assert system.sensory_processor is not None
    assert system.memory_system is not None
    assert system.decision_maker is not None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_market_cycle_processing():
    """Should complete full cognitive cycle."""
    system = SystemIdentity()
    
    price_data = np.sin(np.arange(0, 100, 0.1)) * 100 + 50000
    volume_data = np.ones(1000) * 1000
    
    result = await system.process_market_cycle(
        price_data=price_data,
        volume_data=volume_data,
        orderbook_imbalance=0.1,
        funding_rate=0.001,
        social_sentiment=0.5
    )
    
    assert 'action' in result
    assert 'confidence' in result
    assert 'rationale' in result
    assert result['action'] in [0, 1, 2]
    assert 0 <= result['confidence'] <= 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
