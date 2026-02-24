"""
Vibrational frequency decomposition for market data.
All manifestation can be reduced to frequency patterns.
Uses FFT for spectral analysis without explicit symbolic terminology.
"""

from dataclasses import dataclass

import numpy as np


@dataclass
class FrequencyDecomposition:
    """
    Decompose any signal into frequency components.
    Based on: Every phenomenon is vibration at different frequencies.
    """

    fundamental: float  # Base frequency (primary oscillation)
    harmonics: list[float]  # Overtone magnitudes (1st through 8th)
    phase: float  # Phase alignment in radians
    amplitude: float  # Peak magnitude intensity
    coherence: float  # Pattern stability [0, 1]


class VibrationalAnalyzer:
    """
    Analyze market data as vibrational patterns.
    Pure signal processing - frequency domain analysis.
    """

    def __init__(self, window_size: int = 144):
        """
        Initialize analyzer.

        Args:
            window_size: FFT window (144 = 12²) for harmonic analysis
        """
        self.window_size = window_size
        self.frequency_bands = self._init_frequency_bands()

    def _init_frequency_bands(self) -> dict[str, tuple[float, float]]:
        """
        Define frequency bands for analysis.

        Band structure:
        - Band 0: 0-3 Hz   (low frequency = slow trends)
        - Band 1: 3-6 Hz   (mid frequency = cycles)
        - Band 2: 6-9 Hz   (high frequency = noise/volatility)
        """
        return {
            "band_0": (0, 3),
            "band_1": (3, 6),
            "band_2": (6, 9),
        }

    def decompose(self, price_series: np.ndarray) -> FrequencyDecomposition:
        """
        Decompose price series into frequency components using FFT.

        Args:
            price_series: 1D array of price data

        Returns:
            FrequencyDecomposition with fundamental, harmonics, phase, etc.
        """
        # Normalize input
        price_series = np.array(price_series, dtype=np.float64)
        if len(price_series) == 0:
            return FrequencyDecomposition(
                fundamental=0.0,
                harmonics=[0.0] * 8,
                phase=0.0,
                amplitude=0.0,
                coherence=0.0,
            )

        # Remove mean (detrend)
        detrended = price_series - np.mean(price_series)

        # FFT decomposition
        fft_result = np.fft.rfft(detrended)
        frequencies = np.fft.rfftfreq(len(detrended))
        magnitudes = np.abs(fft_result)

        # Find dominant frequency (skip DC at index 0)
        if len(magnitudes) > 1:
            dominant_idx = int(np.argmax(magnitudes[1:])) + 1
        else:
            dominant_idx = 0

        fundamental_freq = frequencies[dominant_idx] if dominant_idx < len(frequencies) else 0.0

        # Extract harmonics (integer multiples of fundamental)
        harmonics = []
        for n in range(2, 10):  # Up to 9th harmonic
            if fundamental_freq > 0:
                harmonic_freq = fundamental_freq * n
                # Find closest frequency bin
                idx = int(np.argmin(np.abs(frequencies - harmonic_freq)))
            else:
                idx = min(n, len(magnitudes) - 1)

            if idx < len(magnitudes):
                harmonics.append(float(magnitudes[idx]))
            else:
                harmonics.append(0.0)

        # Calculate phase of dominant frequency
        phase = float(np.angle(fft_result[dominant_idx])) if dominant_idx < len(fft_result) else 0.0

        # Calculate coherence (stability of pattern)
        coherence = self._calculate_coherence(magnitudes)

        # Dominant amplitude
        amplitude = float(magnitudes[dominant_idx]) if dominant_idx < len(magnitudes) else 0.0

        return FrequencyDecomposition(
            fundamental=float(fundamental_freq),
            harmonics=harmonics,
            phase=phase,
            amplitude=amplitude,
            coherence=coherence,
        )

    def _calculate_coherence(self, magnitudes: np.ndarray) -> float:
        """
        Measure coherence (stability) of frequency pattern.
        High coherence = clear pattern, Low coherence = noise

        Returns: [0, 1] where 1 = perfectly coherent
        """
        total_power = np.sum(magnitudes**2)
        if total_power < 1e-10:
            return 0.0

        dominant_power = np.max(magnitudes) ** 2
        coherence = dominant_power / total_power

        return float(np.clip(coherence, 0, 1))

    def classify_state(self, decomp: FrequencyDecomposition) -> int:
        """
        Classify market state based on frequency profile.

        Returns:
            0: Low frequency dominance (slow trends)
            1: Mid frequency dominance (cyclic patterns)
            2: High frequency dominance (noise/volatility)
        """
        band_energies = self._calculate_band_energies(decomp)

        max_energy = max(band_energies)
        if max_energy == 0:
            return 1  # Default to mid-frequency

        max_idx = band_energies.index(max_energy)

        # If high frequency dominates but low coherence, return mid-freq
        if max_idx == 2 and decomp.coherence < 0.5:
            return 1

        return max_idx

    def _calculate_band_energies(self, decomp: FrequencyDecomposition) -> list[float]:
        """
        Calculate energy in each frequency band.

        Returns: [band_0_energy, band_1_energy, band_2_energy]
        """
        # Distribute harmonics across bands
        band_0_energy = decomp.harmonics[0] if len(decomp.harmonics) > 0 else 0.0
        band_1_energy = sum(decomp.harmonics[1:3]) if len(decomp.harmonics) > 2 else 0.0
        band_2_energy = sum(decomp.harmonics[3:]) if len(decomp.harmonics) > 3 else 0.0

        return [band_0_energy, band_1_energy, band_2_energy]
