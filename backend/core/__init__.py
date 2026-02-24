"""
Core cognitive system components.

Mathematical implementation of mind (Manas, Buddhi, Chitta, Ahamkara)
without philosophical terminology - pure signal processing and computation.
"""

from backend.core.decision_discriminator import DecisionDiscriminator
from backend.core.frequency_analysis import FrequencyDecomposition, VibrationalAnalyzer
from backend.core.memory_system import MemoryCluster, MemorySystem, MemoryTrace
from backend.core.sensory_processor import SensoryProcessor
from backend.core.system_identity import SystemIdentity

__all__ = [
    "VibrationalAnalyzer",
    "FrequencyDecomposition",
    "SensoryProcessor",
    "MemorySystem",
    "MemoryTrace",
    "MemoryCluster",
    "DecisionDiscriminator",
    "SystemIdentity",
]
