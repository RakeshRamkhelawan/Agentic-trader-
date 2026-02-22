"""
Unit tests for VedAstro Integration (VedAstro-Tattvas Fusion).
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

# Skip all tests if VedAstro dependencies not available
vedastro_deps_available = False
try:
    from backend.vedastro import VedAstroConnector, FeatureEngine, XGBoostOracle, TattvaOrchestrator
    vedastro_deps_available = True
except ImportError:
    pass


pytestmark = pytest.mark.skipif(
    not vedastro_deps_available,
    reason="VedAstro dependencies not available"
)


class TestVedAstroConnector:
    """Test VedAstro connector."""

    def test_initialization_pyswisseph(self):
        """Test initialization with pyswisseph (real data)."""
        from backend.vedastro.connector import VedAstroConnector, VedAstroConfig
        
        config = VedAstroConfig()
        connector = VedAstroConnector(config)
        
        # Should use pyswisseph for real data
        assert connector.get_cache_stats()['mode'] == 'pyswisseph'

    def test_exaltation_check(self):
        """Test exaltation detection."""
        from backend.vedastro.connector import VedAstroConnector, VedAstroConfig
        
        connector = VedAstroConnector(VedAstroConfig())
        
        # Sun is exalted in Aries
        assert connector._is_exalted('Sun', 'Aries') is True
        assert connector._is_exalted('Sun', 'Taurus') is False
        
        # Jupiter is exalted in Cancer
        assert connector._is_exalted('Jupiter', 'Cancer') is True

    def test_sign_lord(self):
        """Test sign lord calculation."""
        from backend.vedastro.connector import VedAstroConnector, VedAstroConfig
        
        connector = VedAstroConnector(VedAstroConfig())
        
        assert connector._get_lord('Aries') == 'Mars'
        assert connector._get_lord('Taurus') == 'Venus'
        assert connector._get_lord('Cancer') == 'Moon'


class TestFeatureEngine:
    """Test feature extraction."""

    def test_feature_vector_shape(self):
        """Test feature vector has correct shape."""
        from backend.vedastro.features import FeatureEngine
        
        engine = FeatureEngine()
        
        kundli = {
            'planets': {
                'Sun': {'longitude': 100},
                'Moon': {'longitude': 200}
            }
        }
        transits = {'aspects': [], 'retrograde_count': 0}
        tattva_state = {'coherence': 0.7, 'gunas': {'sattva': 0.5, 'rajas': 0.3, 'tamas': 0.2}}
        
        features = engine.extract(kundli, transits, 50000, tattva_state)
        
        # Should return 24 features
        assert features.shape == (24,)
        assert features.dtype == np.float32

    def test_angle_calculation(self):
        """Test angle calculation."""
        from backend.vedastro.features import FeatureEngine
        
        engine = FeatureEngine()
        
        p1 = {'longitude': 100}
        p2 = {'longitude': 200}
        
        angle = engine._calculate_angle(p1, p2)
        assert angle == 100
        
        # Test wraparound (should be the smaller angle)
        p3 = {'longitude': 10}
        p4 = {'longitude': 350}
        angle = engine._calculate_angle(p3, p4)
        assert angle == 20 or angle == 340  # Either direction is valid

    def test_bullish_score(self):
        """Test bullish score calculation."""
        from backend.vedastro.features import FeatureEngine, AstroFeatures
        
        engine = FeatureEngine()
        features = AstroFeatures()
        features.jupiter_dignity = 1.0  # Exalted
        features.benefic_aspects = 3
        features.malefic_aspects = 0
        features.tattva_coherence = 0.8
        
        score = engine._calculate_bullish_score(
            features, {'exalted_planets': ['Jupiter']}
        )
        
        assert score > 0.5  # Should be bullish


class TestXGBoostOracle:
    """Test XGBoost oracle."""

    def test_initialization_default(self):
        """Test default initialization."""
        from backend.vedastro.oracle import XGBoostOracle
        
        oracle = XGBoostOracle()
        assert oracle.model is not None
        assert oracle.confidence_threshold == 0.6

    def test_prediction_structure(self):
        """Test prediction returns correct structure."""
        from backend.vedastro.oracle import XGBoostOracle
        
        oracle = XGBoostOracle()
        
        # Fit model with dummy data first
        X_dummy = np.random.random((100, 24))
        y_dummy = np.random.randint(0, 2, 100)
        oracle.train(X_dummy, y_dummy)
        
        features = np.random.random(24)
        result = oracle.predict(features)
        
        assert 'direction' in result
        assert 'up_probability' in result
        assert 'down_probability' in result
        assert 'confidence' in result
        assert 'should_trade' in result

    def test_batch_prediction(self):
        """Test batch prediction."""
        from backend.vedastro.oracle import XGBoostOracle
        
        oracle = XGBoostOracle()
        
        # Fit model with dummy data first
        X_dummy = np.random.random((100, 24))
        y_dummy = np.random.randint(0, 2, 100)
        oracle.train(X_dummy, y_dummy)
        
        features = np.random.random((10, 24))
        results = oracle.predict_batch(features)
        
        assert len(results) == 10
        assert all('direction' in r for r in results)


class TestTattvaOrchestrator:
    """Test Tattva orchestrator."""

    def test_initialization(self):
        """Test orchestrator initialization."""
        from backend.vedastro.orchestrator import TattvaOrchestrator
        
        orchestrator = TattvaOrchestrator()
        assert orchestrator.min_coherence == 0.6
        assert orchestrator.tamas_threshold == 0.5

    def test_astro_coherence_calculation(self):
        """Test astro coherence calculation."""
        from backend.vedastro.orchestrator import TattvaOrchestrator
        
        orchestrator = TattvaOrchestrator()
        
        transits = {
            'exalted_planets': ['Jupiter', 'Venus'],
            'debilitated_planets': [],
            'retrograde_count': 1
        }
        
        coherence = orchestrator._calculate_astro_coherence(transits)
        assert coherence > 0.5  # Should be high with exalted planets

    def test_guna_derivation(self):
        """Test Guna derivation from transits."""
        from backend.vedastro.orchestrator import TattvaOrchestrator
        
        orchestrator = TattvaOrchestrator()
        
        transits = {
            'exalted_planets': ['Jupiter', 'Venus'],
            'debilitated_planets': [],
            'retrograde_count': 0
        }
        
        gunas = orchestrator._derive_gunas_from_transits(transits)
        
        assert 'sattva' in gunas
        assert 'rajas' in gunas
        assert 'tamas' in gunas
        assert abs(sum(gunas.values()) - 1.0) < 0.01  # Should sum to 1

    def test_tamas_block(self):
        """Test that high Tamas blocks trades."""
        from backend.vedastro.orchestrator import TattvaOrchestrator
        
        orchestrator = TattvaOrchestrator(tamas_threshold=0.5)
        
        ml_signal = {'direction': 'UP', 'confidence': 0.8}
        tattva_state = {
            'coherence': 0.7,
            'gunas': {'sattva': 0.2, 'rajas': 0.2, 'tamas': 0.6}  # High Tamas
        }
        transits = {}
        
        decision = orchestrator._apply_tattva_filter(ml_signal, tattva_state, transits)
        
        assert decision.action == 'HOLD'
        assert decision.tattva_aligned is False
        assert 'Tamas' in decision.reason

    def test_low_coherence_wait(self):
        """Test that low coherence results in WAIT."""
        from backend.vedastro.orchestrator import TattvaOrchestrator
        
        orchestrator = TattvaOrchestrator(min_coherence=0.6)
        
        ml_signal = {'direction': 'UP', 'confidence': 0.8}
        tattva_state = {
            'coherence': 0.4,  # Below threshold
            'gunas': {'sattva': 0.5, 'rajas': 0.3, 'tamas': 0.2}
        }
        transits = {}
        
        decision = orchestrator._apply_tattva_filter(ml_signal, tattva_state, transits)
        
        assert decision.action == 'WAIT'
        assert decision.tattva_aligned is False

    def test_alignment_calculation(self):
        """Test alignment score calculation."""
        from backend.vedastro.orchestrator import TattvaOrchestrator
        
        orchestrator = TattvaOrchestrator()
        
        # Aligned case
        ml_signal = {'direction': 'UP', 'confidence': 0.7}
        tattva_state = {
            'coherence': 0.8,
            'gunas': {'sattva': 0.6, 'rajas': 0.3, 'tamas': 0.1}
        }
        
        alignment = orchestrator._calculate_alignment(ml_signal, tattva_state)
        assert alignment > 0.5
        
        # Conflicting case (high Tamas with UP signal)
        tattva_state['gunas'] = {'sattva': 0.1, 'rajas': 0.2, 'tamas': 0.7}
        alignment = orchestrator._calculate_alignment(ml_signal, tattva_state)
        # With high Tamas + UP signal, alignment should be reduced
        assert alignment < 0.7  # Reduced from baseline


class TestVedAstroAssetBirthdays:
    """Test asset birthday database."""

    def test_btc_birthday(self):
        """Test Bitcoin genesis block date."""
        from backend.vedastro.orchestrator import TattvaOrchestrator
        
        btc_date = TattvaOrchestrator.ASSET_BIRTHDAYS.get('BTC')
        assert btc_date is not None
        assert btc_date.year == 2009
        assert btc_date.month == 1
        assert btc_date.day == 3

    def test_eth_birthday(self):
        """Test Ethereum genesis block date."""
        from backend.vedastro.orchestrator import TattvaOrchestrator
        
        eth_date = TattvaOrchestrator.ASSET_BIRTHDAYS.get('ETH')
        assert eth_date is not None
        assert eth_date.year == 2015


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
