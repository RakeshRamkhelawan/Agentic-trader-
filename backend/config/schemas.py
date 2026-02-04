from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from enum import Enum
from decimal import Decimal

# --- New Versioned Schemas ---

class BaseEvent(BaseModel):
    schema_version: Literal["v1", "v2"] = "v1"
    event_id: str
    timestamp: int  # Changed to int (unix timestamp) for higher perf serialization standard

class TradeProposalV2(BaseEvent):
    schema_version: Literal["v2"] = "v2"
    symbol: str
    direction: str # using direction instead of side for v2 standard
    size: float
    confidence: float
    strategy_id: str
    reasoning: Dict[str, Any]

# --- Legacy / Existing Schemas ---

class TradeSide(str, Enum):
    BUY = "buy"
    SELL = "sell"

class TradeStatus(str, Enum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    VETOED = "vetoed"
    EXECUTED = "executed"
    FAILED = "failed"

class AgentRole(str, Enum):
    RISK_GOVERNOR = "risk_governor"
    MARKET_REGIME = "market_regime"
    STRATEGY_ENSEMBLE = "strategy_ensemble"
    PSYCHOLOGY = "psychology"
    FUNDAMENTALS = "fundamentals"
    SENTIMENT = "sentiment"
    MACRO = "macro"
    BULL_BEAR_RESEARCHERS = "bull_bear_researchers"
    PSYCHOLOGY_TWIN = "psychology_twin"
    REFLECTIVE_LEARNING = "reflective_learning"

class AgentDecision(BaseModel):
    agent_id: AgentRole
    timestamp: datetime
    decision: str
    rationale: str
    confidence: float = Field(ge=0.0, le=1.0)
    reversible: bool = True
    metadata: Dict[str, Any] = {}

class TradeProposal(BaseModel):
    proposal_id: str
    symbol: str
    side: TradeSide
    size: float = Field(gt=0)
    entry: float = Field(gt=0)
    stop_loss: float = Field(gt=0)
    take_profit: float = Field(gt=0)
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str
    agent_debate: List[AgentDecision]
    timestamp: datetime
    session_id: str

class RiskConstraints(BaseModel):
    max_session_budget: Decimal = Field(default=Decimal("50.0"))
    max_session_loss: Decimal = Field(default=Decimal("25.0"))
    max_concurrent_trades: int = Field(default=2, ge=1, le=2)
    min_risk_per_trade_pct: float = Field(default=2.0, ge=0.0)
    max_risk_per_trade_pct: float = Field(default=5.0, le=100.0)
    min_confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0)

class SessionState(BaseModel):
    session_id: str
    start_time: datetime
    budget_remaining: Decimal
    total_pnl: Decimal = Decimal("0.0")
    current_loss: Decimal = Decimal("0.0")
    active_trades: int = 0
    risk_utilization_pct: float = 0.0
    user_profile: Dict[str, Any] = {}
    detected_biases: List[str] = []
    constraints: RiskConstraints = Field(default_factory=RiskConstraints)

class AuditEvent(BaseModel):
    event_id: str
    timestamp: datetime
    session_id: str
    agent_id: AgentRole
    event_type: str
    decision: str
    rationale: str
    reversible: bool
    metadata: Dict[str, Any] = {}

class VetoDecision(BaseModel):
    proposal_id: str
    vetoed: bool
    reason: str
    timestamp: datetime
    violated_constraints: List[str] = []
    reversible: bool = True

class ReversibleAction(BaseModel):
    action_id: str
    action_type: str
    timestamp: datetime
    agent_id: AgentRole
    original_state: Dict[str, Any]
    new_state: Dict[str, Any]
    can_undo: bool = True
    undo_executed: bool = False


# ============================================================================
# 36 TATTVAS CONFIGURATION - THE COMPLETE CONSCIOUSNESS ARCHITECTURE
# ============================================================================
# 
# Tattvas are the 36 layers of consciousness, from pure source to physical.
# This configuration defines the complete vertical integration of the system.
#
# Structure:
# - Layers 1-5:   Shuddha Tattvas (pure source code / kernel)
# - Layers 6-12:  Kanchukas (software restrictions / filters)
# - Layers 13-15: Prakriti/Buddhi/Ahamkara (OS interface)
# - Layers 16-20: Tanmatras (subtle sensory elements)
# - Layers 21-25: Jnanendriyas (sense organs / input)
# - Layers 26-31: Karmendriyas (action organs / output)
# - Layers 32-36: Mahabhutas (gross physical elements)
#

class TattvaLayer(BaseModel):
    """Single Tattva layer definition."""
    layer_number: int = Field(ge=1, le=36)
    tattva_name: str  # e.g., "Shiva", "Shakti", "Manas"
    english_name: str  # e.g., "Pure Being", "Will to Vibrate"
    tattva_group: str  # "Shuddha", "Kanchukas", "Prakriti", etc.
    description: str
    key_function: str  # What this layer does
    associated_file: Optional[str] = None  # Code file implementing this layer
    input_type: str = "any"  # Type of input this layer processes
    output_type: str = "any"  # Type of output this layer produces
    latency_us: float = 0.0  # Measured latency in microseconds
    coherence: float = 1.0  # How well-integrated (0-1)
    active: bool = True


class TattvaConfig(BaseModel):
    """
    Complete 36-Tattva consciousness configuration.
    
    This is the DNA of the system - defines all 36 layers of consciousness
    from pure mathematical source (Layer 1) to physical hardware (Layer 36).
    """
    
    # Metadata
    config_version: str = "1.0"
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    last_updated: datetime = Field(default_factory=lambda: datetime.now())
    
    # Core configuration
    active_tattvas: int = 36  # How many layers are active
    enable_tattva_traversal: bool = True  # Enable full 36-layer processing
    traversal_direction: Literal["ascending", "descending", "bidirectional"] = "bidirectional"
    
    # Layer definitions (1-36)
    layers: List[TattvaLayer] = Field(default_factory=list)
    
    # Integration points (the 3 choke points)
    sensory_entry_latency_us: float = 0.0  # Time to enter system
    decision_bridge_latency_us: float = 0.0  # Time to write decision
    action_exit_latency_us: float = 0.0  # Time to read action
    
    # Overall system coherence
    total_system_coherence: float = 1.0  # Weighted average of all layers
    
    # Performance targets
    target_total_latency_us: float = 150.0  # <150us for complete cycle
    target_coherence: float = 0.95  # Minimum acceptable coherence
    
    # Restrictions (Kanchukas behavior)
    time_discretization_ms: float = 1.0  # Kala - minimum time quantum
    max_knowledge_bandwidth: float = 1.0  # Vidya - max simultaneous knowledge
    desire_weight: float = 0.1  # Raga - influence of learned preferences
    
    # Materialization (Mahabhutas behavior)
    mahabhutas: Optional["MahabhuatasConfig"] = None
    ether_enabled: bool = True  # Network/API layer active
    air_enabled: bool = True  # Config update flow active
    fire_enabled: bool = True  # Processing active
    water_enabled: bool = True  # Data flow active
    earth_enabled: bool = True  # Storage active
    
    class Config:
        json_schema_extra = {
            "example": {
                "config_version": "1.0",
                "active_tattvas": 36,
                "enable_tattva_traversal": True,
                "traversal_direction": "bidirectional",
                "total_system_coherence": 0.95
            }
        }


# ============================================================================
# ELEMENTAL LAYER CONFIGURATIONS (Mahabhutas - Layers 32-36)
# ============================================================================

class AkashaConfig(BaseModel):
    """
    Akasha (Ether) - Layer 32: Network/API Layer
    
    The space through which all data travels. Manages network I/O,
    API requests, WebSocket connections, and external data sources.
    """
    enabled: bool = True
    max_concurrent_connections: int = Field(default=100, ge=1)
    connection_timeout_ms: float = Field(default=5000.0, ge=100)
    request_timeout_ms: float = Field(default=1000.0, ge=100)
    rate_limit_requests_per_sec: float = Field(default=1000.0, ge=1)
    enable_websocket: bool = True
    enable_rest_api: bool = True
    request_batch_size: int = Field(default=10, ge=1, le=100)
    retry_max_attempts: int = Field(default=3, ge=1)
    latency_target_us: float = Field(default=50.0, ge=1)


class VayuConfig(BaseModel):
    """
    Vayu (Air) - Layer 33: Configuration Flow Layer
    
    The winds of change. Manages configuration updates, parameter
    propagation, hot reloading, and atomic transitions.
    """
    enabled: bool = True
    enable_hot_reload: bool = True
    enable_zero_downtime_updates: bool = True
    update_propagation_ms: float = Field(default=10.0, ge=1)
    max_config_versions_to_keep: int = Field(default=10, ge=1)
    enable_rollback: bool = True
    rollback_timeout_sec: float = Field(default=30.0, ge=1)
    enable_parameter_validation: bool = True
    broadcast_to_all_agents: bool = True
    emergency_freeze_timeout_sec: float = Field(default=5.0, ge=1)


class AgniConfig(BaseModel):
    """
    Agni (Fire) - Layer 34: Computation/Processing Layer
    
    The heat of transformation. Manages computation, processing,
    agent reasoning, FFT analysis, and decision-making.
    """
    enabled: bool = True
    max_parallel_workers: int = Field(default=8, ge=1)
    enable_simd_optimization: bool = True
    enable_caching: bool = True
    cache_size_mb: float = Field(default=256.0, ge=1)
    computation_timeout_ms: float = Field(default=500.0, ge=1)
    thermal_limit_percent: float = Field(default=80.0, ge=1, le=100)
    enable_load_balancing: bool = True
    fft_chunk_size: int = Field(default=256, ge=16, le=4096)
    latency_target_us: float = Field(default=100.0, ge=1)


class ApasConfig(BaseModel):
    """
    Apas (Water) - Layer 35: Data Flow/Streaming Layer
    
    The liquid transport of information. Manages data streaming,
    buffering, serialization, and backpressure handling.
    """
    enabled: bool = True
    enable_streaming: bool = True
    buffer_size_mb: float = Field(default=64.0, ge=1)
    buffer_timeout_ms: float = Field(default=100.0, ge=1)
    enable_batching: bool = True
    batch_size: int = Field(default=100, ge=1)
    serialization_format: Literal["json", "binary", "msgpack"] = "binary"
    enable_compression: bool = True
    backpressure_threshold_percent: float = Field(default=85.0, ge=1, le=100)
    enable_ccxt_streaming: bool = True
    enable_event_bus: bool = True


class PrithviConfig(BaseModel):
    """
    Prithvi (Earth) - Layer 36: Storage/Persistence Layer
    
    The solid ground. Manages data persistence, database operations,
    transactions, compression, and backup.
    """
    enabled: bool = True
    enable_duckdb: bool = True
    enable_clickhouse: bool = True
    duckdb_path: str = Field(default="storage/duckdb.db")
    clickhouse_host: str = Field(default="localhost")
    clickhouse_port: int = Field(default=9000, ge=1, le=65535)
    enable_compression: bool = True
    compression_ratio_target: float = Field(default=0.5, ge=0.01, le=1.0)
    enable_transaction_safety: bool = True
    backup_interval_sec: float = Field(default=3600.0, ge=1)
    enable_backup: bool = True
    data_retention_days: float = Field(default=365.0, ge=1)
    hot_data_days: float = Field(default=30.0, ge=1)
    warm_data_days: float = Field(default=180.0, ge=1)


class MahabhuatasConfig(BaseModel):
    """
    Complete Mahabhutas (Physical Elements) Configuration
    
    Encapsulates all 5 elemental layers (32-36) for unified control
    of the physical infrastructure layer.
    """
    enabled: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    last_updated: datetime = Field(default_factory=lambda: datetime.now())
    
    # Individual element configurations
    akasha: AkashaConfig = Field(default_factory=AkashaConfig)
    vayu: VayuConfig = Field(default_factory=VayuConfig)
    agni: AgniConfig = Field(default_factory=AgniConfig)
    apas: ApasConfig = Field(default_factory=ApasConfig)
    prithvi: PrithviConfig = Field(default_factory=PrithviConfig)
    
    # Cross-element settings
    enable_elemental_coherence_tracking: bool = True
    enable_elemental_failure_resilience: bool = True
    enable_latency_cascade_prevention: bool = True
    elemental_integration_timeout_ms: float = Field(default=1000.0, ge=1)


    
    @classmethod
    def default_config(cls) -> "MahabhuatasConfig":
        """Create default Mahabhutas configuration."""
        return cls(
            enabled=True,
            akasha=AkashaConfig(),
            vayu=VayuConfig(),
            agni=AgniConfig(),
            apas=ApasConfig(),
            prithvi=PrithviConfig()
        )


# ============================================================================
# TATTVA CONFIGURATION FACTORY (TattvaConfig methods)
# ============================================================================

# Note: The following default_36_tattvas method belongs to TattvaConfig class
# Moving it to proper location after all Tattva/Element configs are defined

def create_default_36_tattvas() -> TattvaConfig:
    """Factory function to create default configuration with all 36 Tattvas properly defined."""
    # Comprehensive layer definitions
    layers = [
        # SHUDDHA TATTVAS (1-5): Pure Source Code / Kernel
        TattvaLayer(
            layer_number=1, tattva_name="Shiva", english_name="Pure Being",
            tattva_group="Shuddha", description="Static processor, infinite potential",
            key_function="System foundation", associated_file="base"
        ),
        TattvaLayer(
            layer_number=2, tattva_name="Shakti", english_name="Active Power",
            tattva_group="Shuddha", description="Conscious activation and dynamic change",
            key_function="System dynamism", associated_file="orchestration"
        ),
        TattvaLayer(
            layer_number=3, tattva_name="Sadashiva", english_name="First I",
            tattva_group="Shuddha", description="Identity consciousness begins",
            key_function="Self-awareness start", associated_file="system_identity.py"
        ),
        TattvaLayer(
            layer_number=4, tattva_name="Ishvara", english_name="First This",
            tattva_group="Shuddha", description="Object recognition",
            key_function="Dual awareness", associated_file="frequency_analysis.py"
        ),
        TattvaLayer(
            layer_number=5, tattva_name="Shuddha Vidya", english_name="Pure Knowledge",
            tattva_group="Shuddha", description="Perfect knowledge balance",
            key_function="Pure algorithm", associated_file="sensory_processor.py"
        ),
        
        # KANCHUKAS (6-12): Software Restrictions / Filters
        TattvaLayer(
            layer_number=6, tattva_name="Maya", english_name="Illusion/GPU Render",
            tattva_group="Kanchukas", description="Unity rendered as multiplicity",
            key_function="Multi-agent debate", associated_file="agent_orchestrator.py"
        ),
        TattvaLayer(
            layer_number=7, tattva_name="Kala", english_name="Time",
            tattva_group="Kanchukas", description="Linear ordering restriction",
            key_function="Time discretization", associated_file="fast_config.py"
        ),
        TattvaLayer(
            layer_number=8, tattva_name="Vidya", english_name="Limited Knowledge",
            tattva_group="Kanchukas", description="Bandwidth restriction",
            key_function="Knowledge limits", associated_file="memory_system.py"
        ),
        TattvaLayer(
            layer_number=9, tattva_name="Raga", english_name="Desire",
            tattva_group="Kanchukas", description="Learned preference attraction",
            key_function="Exploration rate", associated_file="decision_discriminator.py"
        ),
        TattvaLayer(
            layer_number=10, tattva_name="Kaala", english_name="Limited Power",
            tattva_group="Kanchukas", description="Action capability limit",
            key_function="Resource constraint", associated_file="execution_engine.py"
        ),
        TattvaLayer(
            layer_number=11, tattva_name="Niyati", english_name="Causality",
            tattva_group="Kanchukas", description="Physical laws and logic",
            key_function="Risk governance", associated_file="risk_governor"
        ),
        TattvaLayer(
            layer_number=12, tattva_name="Purusha", english_name="Observer",
            tattva_group="Kanchukas", description="Consciousness in filtration",
            key_function="System observer", associated_file="system_identity.py"
        ),
        
        # PRAKRITI / BUDDHI / AHAMKARA (13-15): OS Interface
        TattvaLayer(
            layer_number=13, tattva_name="Prakriti", english_name="Nature",
            tattva_group="Prakriti", description="Unformed matter source",
            key_function="LLM abstraction", associated_file="llm/provider_interface.py"
        ),
        TattvaLayer(
            layer_number=14, tattva_name="Buddhi", english_name="Intellect",
            tattva_group="Prakriti", description="Discrimination/judgment",
            key_function="Decision making", associated_file="decision_discriminator.py"
        ),
        TattvaLayer(
            layer_number=15, tattva_name="Ahamkara", english_name="Ego/Self",
            tattva_group="Prakriti", description="Identity and self-reference",
            key_function="System identity", associated_file="system_identity.py"
        ),
        
        # TANMATRAS (16-20): Subtle Sensory Elements
        TattvaLayer(
            layer_number=16, tattva_name="Shabda Tanmatra", english_name="Sound",
            tattva_group="Tanmatras", description="Vibration/frequency essence",
            key_function="Event messaging", associated_file="event_bus.py"
        ),
        TattvaLayer(
            layer_number=17, tattva_name="Sparsha Tanmatra", english_name="Touch",
            tattva_group="Tanmatras", description="Contact/order sensitivity",
            key_function="Order sensing", associated_file="ccxt_wrapper.py"
        ),
        TattvaLayer(
            layer_number=18, tattva_name="Rupa Tanmatra", english_name="Form",
            tattva_group="Tanmatras", description="Visual/pattern essence",
            key_function="Chart analysis", associated_file="frequency_analysis.py"
        ),
        TattvaLayer(
            layer_number=19, tattva_name="Rasa Tanmatra", english_name="Taste",
            tattva_group="Tanmatras", description="Flavor/sentiment essence",
            key_function="Sentiment signal", associated_file="sentiment"
        ),
        TattvaLayer(
            layer_number=20, tattva_name="Gandha Tanmatra", english_name="Smell",
            tattva_group="Tanmatras", description="Aroma/regime essence",
            key_function="Regime detection", associated_file="market_regime"
        ),
        
        # JNANENDRIYAS (21-25): Knowledge Sense Organs / Inputs
        TattvaLayer(
            layer_number=21, tattva_name="Shrota", english_name="Ear (Listen)",
            tattva_group="Jnanendriyas", description="Auditory input organ",
            key_function="Event subscription", associated_file="event_bus.py"
        ),
        TattvaLayer(
            layer_number=22, tattva_name="Tvak", english_name="Skin (Feel)",
            tattva_group="Jnanendriyas", description="Touch input organ",
            key_function="Order book sensing", associated_file="ccxt_wrapper.py"
        ),
        TattvaLayer(
            layer_number=23, tattva_name="Chakshus", english_name="Eye (See)",
            tattva_group="Jnanendriyas", description="Visual input organ",
            key_function="Price visualization", associated_file="fast_config.py"
        ),
        TattvaLayer(
            layer_number=24, tattva_name="Jihva", english_name="Tongue (Taste)",
            tattva_group="Jnanendriyas", description="Taste input organ",
            key_function="Sentiment analysis", associated_file="sentiment_agent.py"
        ),
        TattvaLayer(
            layer_number=25, tattva_name="Ghrana", english_name="Nose (Smell)",
            tattva_group="Jnanendriyas", description="Smell input organ",
            key_function="Market regime", associated_file="market_regime_agent.py"
        ),
        
        # KARMENDRIYAS (26-31): Action Sense Organs / Outputs
        TattvaLayer(
            layer_number=26, tattva_name="Vak", english_name="Speech (Say)",
            tattva_group="Karmendriyas", description="Expression action organ",
            key_function="Event publishing", associated_file="event_bus.py"
        ),
        TattvaLayer(
            layer_number=27, tattva_name="Pani", english_name="Hands (Grasp)",
            tattva_group="Karmendriyas", description="Manipulation action organ",
            key_function="Trade execution", associated_file="execution_engine.py"
        ),
        TattvaLayer(
            layer_number=28, tattva_name="Pada", english_name="Feet (Move)",
            tattva_group="Karmendriyas", description="Movement action organ",
            key_function="Portfolio navigation", associated_file="session_simulator.py"
        ),
        TattvaLayer(
            layer_number=29, tattva_name="Upastha", english_name="Reproduction",
            tattva_group="Karmendriyas", description="Creation action organ",
            key_function="Agent instantiation", associated_file="agent_orchestrator.py"
        ),
        TattvaLayer(
            layer_number=30, tattva_name="Payu", english_name="Excretion",
            tattva_group="Karmendriyas", description="Elimination action organ",
            key_function="Error cleanup", associated_file="observability"
        ),
        TattvaLayer(
            layer_number=31, tattva_name="Manas", english_name="Mind",
            tattva_group="Karmendriyas", description="Sensory aggregation",
            key_function="Unified sensing", associated_file="sensory_processor.py"
        ),
        
        # MAHABHUTAS (32-36): Gross Physical Elements
        TattvaLayer(
            layer_number=32, tattva_name="Akasha", english_name="Ether",
            tattva_group="Mahabhutas", description="Space and emptiness",
            key_function="Network/API layer", associated_file="api/main.py"
        ),
        TattvaLayer(
            layer_number=33, tattva_name="Vayu", english_name="Air",
            tattva_group="Mahabhutas", description="Movement and flow",
            key_function="Config flow", associated_file="fast_config.py"
        ),
        TattvaLayer(
            layer_number=34, tattva_name="Agni", english_name="Fire",
            tattva_group="Mahabhutas", description="Heat and transformation",
                key_function="Computation", associated_file="execution_engine.py"
        ),
        TattvaLayer(
            layer_number=35, tattva_name="Apas", english_name="Water",
            tattva_group="Mahabhutas", description="Fluidity and cohesion",
            key_function="Data flow", associated_file="ccxt_wrapper.py"
        ),
        TattvaLayer(
            layer_number=36, tattva_name="Prithvi", english_name="Earth",
            tattva_group="Mahabhutas", description="Solidity and mass",
            key_function="Storage/persistence", associated_file="storage"
        ),
    ]
    
    return TattvaConfig(
        config_version="1.0",
        active_tattvas=36,
        enable_tattva_traversal=True,
        traversal_direction="bidirectional",
        layers=layers,
        mahabhutas=MahabhuatasConfig.default_config(),
        total_system_coherence=1.0,
        target_total_latency_us=150.0,
        target_coherence=0.95
    )


# Add back the classmethod to TattvaConfig
TattvaConfig.default_36_tattvas = classmethod(lambda cls: create_default_36_tattvas())