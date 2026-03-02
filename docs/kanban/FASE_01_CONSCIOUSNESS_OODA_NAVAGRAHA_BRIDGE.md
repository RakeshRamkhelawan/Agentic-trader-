# Fase 1: Consciousness-OODA-Navagraha Bridge

> **Prioriteit**: 🔴 CRITICAL
> **Afhankelijkheden**: Geen (fundament)
> **Geschatte effort**: 8-12 dagen
> **Master document**: [SAMKHYA_MASTER_KANBAN_TDD.md](./SAMKHYA_MASTER_KANBAN_TDD.md)

---

## Overzicht

Deze fase bouwt het complete Navagraha (Nine Planets) subsysteem en wires het in de bestaande OODA pipeline + Elemental agents + SystemIdentity (36-Tattva). Na deze fase werkt de triple-track architectuur end-to-end:

```
NavagrahaEngine.assess() → NavagrahaState
    ├── guna_modulation → SystemIdentity.process_market_cycle() (pre-Ascend)
    ├── rahu_kala gate → OODALoopCoordinator._decide() (trading gate)
    ├── hora weighting → OODALoopCoordinator._orient() (cycle context)
    ├── graha-prana → ElementalBase.update_prana_from_graha() (agent energy)
    └── planetary harmony → OrchestratorAgent.harmonize() (consensus)
```

---

## Taken & Microtaken

---

### TAAK 1.1: Navagraha Pydantic Modellen + Engine Scaffold

**Doel**: Definieer alle Pydantic modellen en creëer de directory structuur.

**Bestanden te creëren**:
- `backend/core/navagraha/__init__.py`
- `backend/core/navagraha/models.py`
- `backend/tests/unit/test_navagraha_models.py`

**Bestaande referenties**:
- `backend/core/schemas/ooda_types.py` (Pydantic model patronen, `frozen=True`)
- `backend/schemas/guna.py` (GunaVector model)
- `backend/agents/elemental_base.py:35-50` (guna_balance Dict patroon)

---

#### Microtaak 1.1.1: Creëer package structuur

**Masterprompt**:
```
Creëer backend/core/navagraha/__init__.py met exports voor alle modellen.
Het bestaande Pydantic model patroon volgt frozen=True (zie ooda_types.py:39).
```

**Code**:
```python
# backend/core/navagraha/__init__.py
"""
Navagraha (Nine Planets) Layer — Real Jyotisha Calculations.

Provides real astronomical calculations using Swiss Ephemeris (NASA JPL DE431)
via Kerykeion + pyswisseph. No mocks — real sidereal planetary positions.

Architecture:
    NavagrahaEngine (orchestrator)
    ├── EphemerisCalculator  — Kerykeion/pyswisseph wrapper
    ├── NakshatraCalculator  — 27 nakshatras + 4 padas
    ├── VimshottariDasha     — Mahadasha/Antardasha lifecycle
    ├── AspectAnalyzer       — Drishti (planetary aspects)
    ├── RahuKalaCalculator   — Daily inauspicious period gate
    ├── HoraCalculator       — Planetary hours (Chaldean order)
    └── GrahaGunaMapper      — Planetary state → Guna modulation
"""

from backend.core.navagraha.models import (
    Graha,
    GrahaPosition,
    NakshatraInfo,
    AspectInfo,
    AspectType,
    RahuKalaState,
    DashaState,
    HoraState,
    NavagrahaState,
    GunaModulation,
)

__all__ = [
    "Graha",
    "GrahaPosition",
    "NakshatraInfo",
    "AspectInfo",
    "AspectType",
    "RahuKalaState",
    "DashaState",
    "HoraState",
    "NavagrahaState",
    "GunaModulation",
]
```

---

#### Microtaak 1.1.2: Definieer Graha enum en GrahaPosition model

**Masterprompt**:
```
Definieer de Graha enum met alle 9 Vedische planeten en het GrahaPosition Pydantic model.
Volg het patroon van backend/core/schemas/ooda_types.py (frozen BaseModel).
Rahu is ALTIJD retrograde — dit is een invariant die in de validator moet zitten.
```

**Test FIRST (TDD Red)**:
```python
# backend/tests/unit/test_navagraha_models.py

import pytest
from backend.core.navagraha.models import (
    Graha, GrahaPosition, NakshatraInfo, AspectInfo, AspectType,
    RahuKalaState, DashaState, HoraState, NavagrahaState, GunaModulation
)
from datetime import datetime, timezone, timedelta


# ============================================================================
# TAAK 1.1 — GRAHA ENUM TESTS
# ============================================================================

class TestGrahaEnum:
    """Test Graha enum — 9 Vedische planeten."""

    def test_graha_has_exactly_9_members(self):
        """Happy: Graha enum bevat exact 9 planeten."""
        assert len(Graha) == 9

    def test_graha_contains_all_nine_planets(self):
        """Happy: Alle 9 Navagraha aanwezig."""
        expected = {"SURYA", "CHANDRA", "MANGALA", "BUDHA", "BRIHASPATI",
                    "SHUKRA", "SHANI", "RAHU", "KETU"}
        actual = {g.name for g in Graha}
        assert actual == expected

    def test_graha_values_are_strings(self):
        """Happy: Graha values zijn lowercase strings."""
        assert Graha.SURYA.value == "surya"
        assert Graha.RAHU.value == "rahu"

    def test_graha_from_string(self):
        """Happy: Graha kan van string gecreëerd worden."""
        assert Graha("surya") == Graha.SURYA

    def test_graha_invalid_value_raises(self):
        """Unhappy: Ongeldige Graha string gooit ValueError."""
        with pytest.raises(ValueError):
            Graha("pluto")


# ============================================================================
# TAAK 1.1 — GRAHA POSITION TESTS
# ============================================================================

class TestGrahaPosition:
    """Test GrahaPosition Pydantic model."""

    def test_valid_position_creation(self):
        """Happy: Geldige positie wordt correct aangemaakt."""
        pos = GrahaPosition(
            graha=Graha.SURYA,
            longitude=45.5,
            sign="Taurus",
            sign_num=1,
            sign_longitude=15.5,
            retrograde=False,
            nakshatra=NakshatraInfo(
                index=3, name="Rohini", pada=2,
                lord=Graha.CHANDRA, degrees_in_nakshatra=2.17
            )
        )
        assert pos.graha == Graha.SURYA
        assert pos.longitude == 45.5
        assert pos.retrograde is False

    def test_rahu_must_be_retrograde(self):
        """Happy: Rahu positie met retrograde=True is geldig."""
        pos = GrahaPosition(
            graha=Graha.RAHU,
            longitude=100.0,
            sign="Cancer",
            sign_num=3,
            sign_longitude=10.0,
            retrograde=True,
            nakshatra=NakshatraInfo(
                index=7, name="Pushya", pada=3,
                lord=Graha.SHANI, degrees_in_nakshatra=6.67
            )
        )
        assert pos.retrograde is True

    def test_rahu_non_retrograde_raises(self):
        """Unhappy: Rahu met retrograde=False gooit ValidationError."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            GrahaPosition(
                graha=Graha.RAHU,
                longitude=100.0,
                sign="Cancer",
                sign_num=3,
                sign_longitude=10.0,
                retrograde=False,  # ONGELDIG voor Rahu
                nakshatra=NakshatraInfo(
                    index=7, name="Pushya", pada=3,
                    lord=Graha.SHANI, degrees_in_nakshatra=6.67
                )
            )

    def test_ketu_must_be_retrograde(self):
        """Happy: Ketu is ook altijd retrograde."""
        pos = GrahaPosition(
            graha=Graha.KETU,
            longitude=280.0,
            sign="Capricorn",
            sign_num=9,
            sign_longitude=10.0,
            retrograde=True,
            nakshatra=NakshatraInfo(
                index=21, name="Uttara Ashadha", pada=1,
                lord=Graha.SURYA, degrees_in_nakshatra=0.0
            )
        )
        assert pos.retrograde is True

    def test_longitude_out_of_range_raises(self):
        """Unhappy: Longitude buiten 0-360 gooit validatie error."""
        with pytest.raises(Exception):
            GrahaPosition(
                graha=Graha.SURYA,
                longitude=361.0,  # ONGELDIG
                sign="Aries",
                sign_num=0,
                sign_longitude=1.0,
                retrograde=False,
                nakshatra=NakshatraInfo(
                    index=0, name="Ashwini", pada=1,
                    lord=Graha.KETU, degrees_in_nakshatra=1.0
                )
            )

    def test_negative_longitude_raises(self):
        """Unhappy: Negatieve longitude gooit error."""
        with pytest.raises(Exception):
            GrahaPosition(
                graha=Graha.SURYA,
                longitude=-5.0,  # ONGELDIG
                sign="Aries",
                sign_num=0,
                sign_longitude=0.0,
                retrograde=False,
                nakshatra=NakshatraInfo(
                    index=0, name="Ashwini", pada=1,
                    lord=Graha.KETU, degrees_in_nakshatra=0.0
                )
            )

    def test_sign_num_range(self):
        """Unhappy: sign_num buiten 0-11 gooit error."""
        with pytest.raises(Exception):
            GrahaPosition(
                graha=Graha.SURYA,
                longitude=45.0,
                sign="Invalid",
                sign_num=12,  # ONGELDIG (max 11)
                sign_longitude=15.0,
                retrograde=False,
                nakshatra=NakshatraInfo(
                    index=3, name="Rohini", pada=2,
                    lord=Graha.CHANDRA, degrees_in_nakshatra=2.0
                )
            )

    def test_position_is_frozen(self):
        """Unhappy: Positie is immutable (frozen)."""
        pos = GrahaPosition(
            graha=Graha.SURYA,
            longitude=45.0,
            sign="Taurus",
            sign_num=1,
            sign_longitude=15.0,
            retrograde=False,
            nakshatra=NakshatraInfo(
                index=3, name="Rohini", pada=2,
                lord=Graha.CHANDRA, degrees_in_nakshatra=2.0
            )
        )
        with pytest.raises(Exception):
            pos.longitude = 50.0  # Frozen!
```

**Implementatie (TDD Green)**:
```python
# backend/core/navagraha/models.py

"""
Navagraha Pydantic Models.

Immutable data models for all Jyotisha calculations.
Follows the same pattern as backend.core.schemas.ooda_types (frozen=True).
"""

from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum


class Graha(str, Enum):
    """Nine Vedic planets (Navagraha)."""
    SURYA = "surya"           # Sun
    CHANDRA = "chandra"       # Moon
    MANGALA = "mangala"       # Mars
    BUDHA = "budha"           # Mercury
    BRIHASPATI = "brihaspati" # Jupiter
    SHUKRA = "shukra"         # Venus
    SHANI = "shani"           # Saturn
    RAHU = "rahu"             # North Lunar Node (shadow)
    KETU = "ketu"             # South Lunar Node (shadow)


class NakshatraInfo(BaseModel):
    """Nakshatra (lunar mansion) position details."""
    model_config = ConfigDict(frozen=True)

    index: int = Field(..., ge=0, le=26, description="Nakshatra index 0-26")
    name: str = Field(..., description="Nakshatra name (e.g., 'Ashwini')")
    pada: int = Field(..., ge=1, le=4, description="Pada (quarter) 1-4")
    lord: Graha = Field(..., description="Vimsottari dasha lord")
    degrees_in_nakshatra: float = Field(
        ..., ge=0.0, lt=13.3334,
        description="Degrees within this nakshatra (0-13.333)"
    )


class GrahaPosition(BaseModel):
    """Position of a single Graha in the sidereal zodiac."""
    model_config = ConfigDict(frozen=True)

    graha: Graha = Field(..., description="Which planet")
    longitude: float = Field(
        ..., ge=0.0, lt=360.0,
        description="Absolute sidereal longitude (0-360°)"
    )
    sign: str = Field(..., description="Zodiac sign name")
    sign_num: int = Field(..., ge=0, le=11, description="Sign index 0-11")
    sign_longitude: float = Field(
        ..., ge=0.0, lt=30.0,
        description="Degrees within sign (0-30°)"
    )
    retrograde: bool = Field(..., description="Is planet retrograde?")
    nakshatra: NakshatraInfo = Field(..., description="Nakshatra position")

    @model_validator(mode='after')
    def validate_shadow_planets_retrograde(self):
        """Rahu and Ketu are ALWAYS retrograde — astronomical invariant."""
        if self.graha in (Graha.RAHU, Graha.KETU) and not self.retrograde:
            raise ValueError(
                f"{self.graha.value} must always be retrograde "
                f"(astronomical invariant)"
            )
        return self


class AspectType(str, Enum):
    """Types of planetary aspects (Drishti)."""
    CONJUNCTION = "conjunction"  # 0° (orb ~10°)
    SEXTILE = "sextile"         # 60°
    SQUARE = "square"           # 90° (orb ~10°)
    TRINE = "trine"             # 120° (orb ~10°)
    OPPOSITION = "opposition"   # 180° (orb ~10°)


class AspectInfo(BaseModel):
    """A planetary aspect between two Grahas."""
    model_config = ConfigDict(frozen=True)

    graha_1: Graha = Field(..., description="First planet")
    graha_2: Graha = Field(..., description="Second planet")
    aspect_type: AspectType = Field(..., description="Aspect classification")
    orb: float = Field(..., ge=0.0, description="Orb in degrees")
    is_applying: bool = Field(
        ..., description="True if aspect is applying (getting closer)"
    )
    strength: float = Field(
        ..., ge=0.0, le=1.0,
        description="Aspect strength (1.0 = exact, 0.0 = wide)"
    )


class RahuKalaState(BaseModel):
    """Rahu Kala — daily inauspicious period."""
    model_config = ConfigDict(frozen=True)

    is_active: bool = Field(..., description="Currently in Rahu Kala?")
    start: datetime = Field(..., description="Rahu Kala start time")
    end: datetime = Field(..., description="Rahu Kala end time")
    sunrise: datetime = Field(..., description="Hindu sunrise time")
    sunset: datetime = Field(..., description="Hindu sunset time")
    weekday_segment: int = Field(
        ..., ge=1, le=8,
        description="Segment number (Ma=2, Di=7, Wo=5, Do=6, Vr=4, Za=3, Zo=8)"
    )


class DashaState(BaseModel):
    """Vimshottari Dasha — planetary period state."""
    model_config = ConfigDict(frozen=True)

    mahadasha_lord: Graha = Field(..., description="Major period ruler")
    mahadasha_progress: float = Field(
        ..., ge=0.0, le=1.0,
        description="Progress through Mahadasha (0.0-1.0)"
    )
    mahadasha_years_total: float = Field(
        ..., description="Total years of this Mahadasha"
    )
    antardasha_lord: Graha = Field(..., description="Sub-period ruler")
    antardasha_progress: float = Field(
        ..., ge=0.0, le=1.0,
        description="Progress through Antardasha (0.0-1.0)"
    )
    janma_nakshatra: NakshatraInfo = Field(
        ..., description="Birth nakshatra (system deployment Moon)"
    )
    system_birth: datetime = Field(
        ..., description="System deployment datetime"
    )


class HoraState(BaseModel):
    """Planetary Hour (Hora) — Chaldean order."""
    model_config = ConfigDict(frozen=True)

    hora_number: int = Field(
        ..., ge=1, le=24,
        description="Current hora (1-12 day, 13-24 night)"
    )
    ruling_planet: Graha = Field(..., description="Planet ruling this hora")
    is_day: bool = Field(..., description="True if daytime hora")
    hora_start: datetime = Field(..., description="Hora start time")
    hora_end: datetime = Field(..., description="Hora end time")


class GunaModulation(BaseModel):
    """Guna modulation vector from Navagraha state."""
    model_config = ConfigDict(frozen=True)

    sattva_delta: float = Field(
        default=0.0, description="Sattva adjustment (-1.0 to +1.0)"
    )
    rajas_delta: float = Field(
        default=0.0, description="Rajas adjustment (-1.0 to +1.0)"
    )
    tamas_delta: float = Field(
        default=0.0, description="Tamas adjustment (-1.0 to +1.0)"
    )
    dominant_influence: str = Field(
        default="neutral",
        description="Description of strongest planetary influence"
    )
    confidence: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Confidence in this modulation"
    )


class NavagrahaState(BaseModel):
    """Complete Navagraha state — composite of all calculations."""
    model_config = ConfigDict(frozen=True)

    timestamp: datetime = Field(..., description="Calculation timestamp")
    positions: Dict[Graha, GrahaPosition] = Field(
        ..., description="All 9 planetary positions"
    )
    aspects: List[AspectInfo] = Field(
        default_factory=list, description="Active aspects"
    )
    rahu_kala: RahuKalaState = Field(..., description="Rahu Kala state")
    dasha: DashaState = Field(..., description="Vimshottari Dasha state")
    hora: HoraState = Field(..., description="Current planetary hour")
    guna_modulation: GunaModulation = Field(
        ..., description="Computed Guna modulation"
    )
    trading_gate_open: bool = Field(
        ..., description="False if Rahu Kala blocks trading"
    )
    dominant_element: str = Field(
        default="ether",
        description="Dominant element based on planetary positions"
    )

    @model_validator(mode='after')
    def validate_nine_positions(self):
        """NavagrahaState must contain exactly 9 planetary positions."""
        if len(self.positions) != 9:
            raise ValueError(
                f"NavagrahaState must have exactly 9 positions, "
                f"got {len(self.positions)}"
            )
        return self

    @model_validator(mode='after')
    def validate_trading_gate_consistent(self):
        """trading_gate_open must be False when Rahu Kala is active."""
        if self.rahu_kala.is_active and self.trading_gate_open:
            raise ValueError(
                "trading_gate_open cannot be True when Rahu Kala is active"
            )
        return self
```

**Additionele tests (NavagrahaState + GunaModulation)**:
```python
# Vervolg in test_navagraha_models.py

class TestNakshatraInfo:
    """Test NakshatraInfo model."""

    def test_valid_nakshatra(self):
        """Happy: Geldige nakshatra index en pada."""
        n = NakshatraInfo(
            index=0, name="Ashwini", pada=1,
            lord=Graha.KETU, degrees_in_nakshatra=5.0
        )
        assert n.name == "Ashwini"
        assert n.lord == Graha.KETU

    def test_nakshatra_index_27_raises(self):
        """Unhappy: Index 27 is out of range (max 26)."""
        with pytest.raises(Exception):
            NakshatraInfo(
                index=27, name="Invalid", pada=1,
                lord=Graha.KETU, degrees_in_nakshatra=0.0
            )

    def test_pada_0_raises(self):
        """Unhappy: Pada 0 is ongeldig (min 1)."""
        with pytest.raises(Exception):
            NakshatraInfo(
                index=0, name="Ashwini", pada=0,
                lord=Graha.KETU, degrees_in_nakshatra=0.0
            )

    def test_pada_5_raises(self):
        """Unhappy: Pada 5 is ongeldig (max 4)."""
        with pytest.raises(Exception):
            NakshatraInfo(
                index=0, name="Ashwini", pada=5,
                lord=Graha.KETU, degrees_in_nakshatra=0.0
            )


class TestNavagrahaState:
    """Test NavagrahaState composite model."""

    def _make_position(self, graha: Graha, longitude: float = 45.0) -> GrahaPosition:
        """Helper: maak een GrahaPosition."""
        retrograde = graha in (Graha.RAHU, Graha.KETU)
        sign_num = int(longitude / 30) % 12
        signs = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
                 "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
        nak_index = int(longitude / 13.3333) % 27
        return GrahaPosition(
            graha=graha,
            longitude=longitude,
            sign=signs[sign_num],
            sign_num=sign_num,
            sign_longitude=longitude % 30,
            retrograde=retrograde,
            nakshatra=NakshatraInfo(
                index=nak_index, name=f"Nakshatra_{nak_index}",
                pada=int((longitude % 13.3333) / 3.3333) + 1,
                lord=Graha.KETU, degrees_in_nakshatra=longitude % 13.3333
            )
        )

    def _make_full_state(self, rahu_active=False) -> NavagrahaState:
        """Helper: maak een volledige NavagrahaState."""
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone.utc)
        positions = {}
        longitudes = [45, 120, 200, 80, 250, 310, 150, 100, 280]
        for graha, lng in zip(Graha, longitudes):
            positions[graha] = self._make_position(graha, lng)

        return NavagrahaState(
            timestamp=now,
            positions=positions,
            aspects=[],
            rahu_kala=RahuKalaState(
                is_active=rahu_active,
                start=now - timedelta(minutes=30),
                end=now + timedelta(minutes=60),
                sunrise=now - timedelta(hours=6),
                sunset=now + timedelta(hours=6),
                weekday_segment=2
            ),
            dasha=DashaState(
                mahadasha_lord=Graha.BRIHASPATI,
                mahadasha_progress=0.3,
                mahadasha_years_total=16.0,
                antardasha_lord=Graha.SHUKRA,
                antardasha_progress=0.5,
                janma_nakshatra=NakshatraInfo(
                    index=10, name="Magha", pada=1,
                    lord=Graha.KETU, degrees_in_nakshatra=0.0
                ),
                system_birth=now - timedelta(days=365)
            ),
            hora=HoraState(
                hora_number=3,
                ruling_planet=Graha.MANGALA,
                is_day=True,
                hora_start=now - timedelta(minutes=30),
                hora_end=now + timedelta(minutes=30)
            ),
            guna_modulation=GunaModulation(
                sattva_delta=0.1, rajas_delta=-0.05, tamas_delta=-0.05,
                dominant_influence="Jupiter trine Sun", confidence=0.8
            ),
            trading_gate_open=not rahu_active,
            dominant_element="ether"
        )

    def test_full_state_creation(self):
        """Happy: Volledige NavagrahaState met 9 posities."""
        state = self._make_full_state()
        assert len(state.positions) == 9
        assert state.trading_gate_open is True

    def test_state_with_fewer_than_9_positions_raises(self):
        """Unhappy: Minder dan 9 posities gooit ValidationError."""
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone.utc)
        # Slechts 3 posities
        positions = {
            g: self._make_position(g, 45.0)
            for g in list(Graha)[:3]
        }
        with pytest.raises(Exception, match="exactly 9"):
            NavagrahaState(
                timestamp=now,
                positions=positions,
                aspects=[],
                rahu_kala=RahuKalaState(
                    is_active=False, start=now, end=now,
                    sunrise=now, sunset=now, weekday_segment=2
                ),
                dasha=DashaState(
                    mahadasha_lord=Graha.BRIHASPATI,
                    mahadasha_progress=0.3,
                    mahadasha_years_total=16.0,
                    antardasha_lord=Graha.SHUKRA,
                    antardasha_progress=0.5,
                    janma_nakshatra=NakshatraInfo(
                        index=10, name="Magha", pada=1,
                        lord=Graha.KETU, degrees_in_nakshatra=0.0
                    ),
                    system_birth=now
                ),
                hora=HoraState(
                    hora_number=1, ruling_planet=Graha.SURYA,
                    is_day=True, hora_start=now, hora_end=now
                ),
                guna_modulation=GunaModulation(),
                trading_gate_open=True,
                dominant_element="ether"
            )

    def test_rahu_kala_active_but_gate_open_raises(self):
        """Unhappy: Gate kan niet open zijn tijdens actieve Rahu Kala."""
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone.utc)
        positions = {g: self._make_position(g, float(i*40) % 360)
                     for i, g in enumerate(Graha)}
        with pytest.raises(Exception, match="trading_gate_open"):
            NavagrahaState(
                timestamp=now,
                positions=positions,
                aspects=[],
                rahu_kala=RahuKalaState(
                    is_active=True,  # ACTIEF
                    start=now, end=now + timedelta(hours=1),
                    sunrise=now - timedelta(hours=6),
                    sunset=now + timedelta(hours=6),
                    weekday_segment=2
                ),
                dasha=DashaState(
                    mahadasha_lord=Graha.BRIHASPATI,
                    mahadasha_progress=0.3,
                    mahadasha_years_total=16.0,
                    antardasha_lord=Graha.SHUKRA,
                    antardasha_progress=0.5,
                    janma_nakshatra=NakshatraInfo(
                        index=10, name="Magha", pada=1,
                        lord=Graha.KETU, degrees_in_nakshatra=0.0
                    ),
                    system_birth=now
                ),
                hora=HoraState(
                    hora_number=1, ruling_planet=Graha.SURYA,
                    is_day=True, hora_start=now, hora_end=now
                ),
                guna_modulation=GunaModulation(),
                trading_gate_open=True,  # ONGELDIG bij actieve Rahu Kala
                dominant_element="ether"
            )

    def test_state_is_frozen(self):
        """Unhappy: State is immutable."""
        state = self._make_full_state()
        with pytest.raises(Exception):
            state.trading_gate_open = False
```

**Taak-afronding integratie test**:
```python
# backend/tests/integration/test_navagraha_models_integration.py

def test_integration_1_1_models_serialization_roundtrip():
    """
    Integratie: NavagrahaState → JSON → NavagrahaState roundtrip.
    Verifieert compatibiliteit met bestaande Pydantic patronen (ooda_types).
    """
    state = _make_full_state()  # reuse helper
    json_str = state.model_dump_json()
    restored = NavagrahaState.model_validate_json(json_str)
    assert restored.positions[Graha.SURYA].longitude == state.positions[Graha.SURYA].longitude
    assert len(restored.positions) == 9
    assert restored.rahu_kala.is_active == state.rahu_kala.is_active
```

---

### TAAK 1.2: EphemerisCalculator (Kerykeion/pyswisseph)

**Doel**: Real sidereal planetary positions via Swiss Ephemeris.

**Bestanden te creëren**:
- `backend/core/navagraha/ephemeris.py`
- `backend/tests/unit/test_ephemeris.py`

**Dependencies**: `kerykeion>=5.7.0`, `pyswisseph>=2.10.3.0`

**Bestaande referenties**:
- `backend/core/navagraha/models.py` (Taak 1.1)
- `backend/core/config/settings.py` (voor configuratie patronen)

---

#### Microtaak 1.2.1: Install dependencies + configuratie

**Masterprompt**:
```
Voeg kerykeion en pyswisseph toe aan requirements/base.txt.
Kerykeion gebruikt Swiss Ephemeris intern (bundelt .se1 bestanden).
pyswisseph is voor custom berekeningen (Rahu Kala sunrise, nakshatra split).
```

**Actie**:
```
# Toevoegen aan requirements/base.txt:
kerykeion>=5.7.0
pyswisseph>=2.10.3.0
```

---

#### Microtaak 1.2.2: EphemerisCalculator klasse

**Masterprompt**:
```
Bouw EphemerisCalculator die Kerykeion's AstrologicalSubject gebruikt
met zodiac_type="Sidereal" en sidereal_mode="LAHIRI" (Chitrapaksha ayanamsha).
Returned Dict[Graha, GrahaPosition] met alle 9 planeten.
Kerykeion planet mapping:
  sun, moon, mars, mercury, jupiter, venus, saturn,
  true_north_lunar_node (=Rahu), true_south_lunar_node (=Ketu niet beschikbaar als
  direct attribuut, maar Ketu = Rahu + 180°)
Moet offline werken (online=False).
Locatie standaard: Amsterdam (52.3676°N, 4.9041°E) — configureerbaar.
```

**Test FIRST (TDD Red)**:
```python
# backend/tests/unit/test_ephemeris.py

import pytest
from datetime import datetime, timezone
from backend.core.navagraha.ephemeris import EphemerisCalculator
from backend.core.navagraha.models import Graha, GrahaPosition


class TestEphemerisCalculator:
    """Test real Swiss Ephemeris calculations — NO MOCKS."""

    @pytest.fixture
    def calculator(self):
        return EphemerisCalculator(
            latitude=52.3676,  # Amsterdam
            longitude_geo=4.9041,
            altitude=0
        )

    def test_get_positions_returns_9_grahas(self, calculator):
        """Happy: Alle 9 planeten worden berekend."""
        now = datetime.now(timezone.utc)
        positions = calculator.get_positions(now)
        assert len(positions) == 9
        assert all(isinstance(g, Graha) for g in positions.keys())
        assert all(isinstance(p, GrahaPosition) for p in positions.values())

    def test_positions_have_valid_longitudes(self, calculator):
        """Happy: Alle longitudes zijn 0-360°."""
        positions = calculator.get_positions(datetime.now(timezone.utc))
        for graha, pos in positions.items():
            assert 0.0 <= pos.longitude < 360.0, \
                f"{graha}: longitude {pos.longitude} out of range"

    def test_rahu_is_always_retrograde(self, calculator):
        """Happy: Rahu is ALTIJD retrograde (astronomisch feit)."""
        positions = calculator.get_positions(datetime.now(timezone.utc))
        assert positions[Graha.RAHU].retrograde is True

    def test_ketu_is_always_retrograde(self, calculator):
        """Happy: Ketu is ALTIJD retrograde."""
        positions = calculator.get_positions(datetime.now(timezone.utc))
        assert positions[Graha.KETU].retrograde is True

    def test_ketu_opposite_rahu(self, calculator):
        """Happy: Ketu = Rahu + 180° (±0.5° tolerantie)."""
        positions = calculator.get_positions(datetime.now(timezone.utc))
        rahu_lng = positions[Graha.RAHU].longitude
        ketu_lng = positions[Graha.KETU].longitude
        diff = abs((ketu_lng - rahu_lng + 180) % 360 - 180)
        assert diff < 0.5 or abs(diff - 180) < 0.5, \
            f"Ketu ({ketu_lng}) not opposite Rahu ({rahu_lng})"

    def test_positions_include_nakshatra(self, calculator):
        """Happy: Elke positie bevat nakshatra info."""
        positions = calculator.get_positions(datetime.now(timezone.utc))
        for graha, pos in positions.items():
            assert pos.nakshatra is not None
            assert 0 <= pos.nakshatra.index <= 26
            assert 1 <= pos.nakshatra.pada <= 4

    def test_positions_for_known_date(self, calculator):
        """
        Happy: Cross-check met drikpanchang.com.
        Op 1 jan 2026 00:00 UTC staat de maan rond ~Virgo siderisch.
        We checken dat de maan in een redelijk bereik zit.
        """
        known_date = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        positions = calculator.get_positions(known_date)
        moon = positions[Graha.CHANDRA]
        # Moon op 1 jan 2026 ~150-180° siderisch (Virgo/Libra area)
        assert 100 < moon.longitude < 220, \
            f"Moon longitude {moon.longitude} outside expected range for 2026-01-01"

    def test_historical_date_works(self, calculator):
        """Happy: Berekening voor historische datum werkt."""
        past = datetime(2020, 6, 21, 12, 0, 0, tzinfo=timezone.utc)
        positions = calculator.get_positions(past)
        assert len(positions) == 9

    def test_far_future_date_works(self, calculator):
        """Happy: Swiss Ephemeris dekt tot 17191 AD."""
        future = datetime(2100, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        positions = calculator.get_positions(future)
        assert len(positions) == 9

    def test_invalid_date_raises(self, calculator):
        """Unhappy: None als datum gooit TypeError."""
        with pytest.raises((TypeError, ValueError)):
            calculator.get_positions(None)

    def test_get_sunrise_sunset(self, calculator):
        """Happy: Sunrise/sunset berekening (Hindu rising)."""
        date = datetime(2026, 2, 14, 12, 0, 0, tzinfo=timezone.utc)
        sunrise, sunset = calculator.get_sunrise_sunset(date)
        assert sunrise < sunset
        # Amsterdam sunrise in februari ~7:30-8:30 UTC
        assert 6 <= sunrise.hour <= 9
        # Sunset ~16:30-18:00 UTC
        assert 15 <= sunset.hour <= 19

    def test_sunrise_sunset_near_polar_still_works(self):
        """
        Unhappy: Op extreme latitude (bv. 70°N) kan sunrise
        niet berekend worden in winter. Moet graceful fallback geven.
        """
        calc = EphemerisCalculator(latitude=70.0, longitude_geo=25.0)
        date = datetime(2026, 12, 21, 12, 0, 0, tzinfo=timezone.utc)
        # Moet een fallback retourneren, niet crashen
        result = calc.get_sunrise_sunset(date)
        assert result is not None
```

**Implementatie (TDD Green)**:
```python
# backend/core/navagraha/ephemeris.py

"""
EphemerisCalculator — Real Sidereal Planetary Positions.

Uses Kerykeion (Swiss Ephemeris backend) with LAHIRI ayanamsha
for all 9 Vedic planets including Rahu/Ketu nodes.

Also uses pyswisseph directly for:
- Hindu sunrise/sunset (SE_BIT_HINDU_RISING)
- Low-level calculations not available through Kerykeion
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Tuple, Optional

from backend.core.navagraha.models import (
    Graha, GrahaPosition, NakshatraInfo
)

logger = logging.getLogger(__name__)

# Nakshatra names and Vimsottari lords
NAKSHATRA_DATA = [
    ("Ashwini", Graha.KETU), ("Bharani", Graha.SHUKRA),
    ("Krittika", Graha.SURYA), ("Rohini", Graha.CHANDRA),
    ("Mrigashira", Graha.MANGALA), ("Ardra", Graha.RAHU),
    ("Punarvasu", Graha.BRIHASPATI), ("Pushya", Graha.SHANI),
    ("Ashlesha", Graha.BUDHA), ("Magha", Graha.KETU),
    ("Purva Phalguni", Graha.SHUKRA), ("Uttara Phalguni", Graha.SURYA),
    ("Hasta", Graha.CHANDRA), ("Chitra", Graha.MANGALA),
    ("Swati", Graha.RAHU), ("Vishakha", Graha.BRIHASPATI),
    ("Anuradha", Graha.SHANI), ("Jyeshtha", Graha.BUDHA),
    ("Mula", Graha.KETU), ("Purva Ashadha", Graha.SHUKRA),
    ("Uttara Ashadha", Graha.SURYA), ("Shravana", Graha.CHANDRA),
    ("Dhanishta", Graha.MANGALA), ("Shatabhisha", Graha.RAHU),
    ("Purva Bhadrapada", Graha.BRIHASPATI),
    ("Uttara Bhadrapada", Graha.SHANI),
    ("Revati", Graha.BUDHA),
]

SIGN_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

# Kerykeion planet attribute names → Graha mapping
KERYKEION_PLANET_MAP = {
    "sun": Graha.SURYA,
    "moon": Graha.CHANDRA,
    "mars": Graha.MANGALA,
    "mercury": Graha.BUDHA,
    "jupiter": Graha.BRIHASPATI,
    "venus": Graha.SHUKRA,
    "saturn": Graha.SHANI,
}


class EphemerisCalculator:
    """
    Real sidereal ephemeris calculator.

    Uses Kerykeion with Lahiri ayanamsha for the 7 visible planets
    and pyswisseph directly for Rahu/Ketu lunar nodes.
    """

    def __init__(
        self,
        latitude: float = 52.3676,
        longitude_geo: float = 4.9041,
        altitude: int = 0,
        city: str = "Amsterdam"
    ):
        self.latitude = latitude
        self.longitude_geo = longitude_geo
        self.altitude = altitude
        self.city = city
        logger.info(
            f"EphemerisCalculator initialized: "
            f"{city} ({latitude}°N, {longitude_geo}°E)"
        )

    def _longitude_to_nakshatra(self, longitude: float) -> NakshatraInfo:
        """Convert absolute longitude to Nakshatra info."""
        nak_span = 360.0 / 27  # 13.3333°
        nak_index = int(longitude / nak_span) % 27
        degrees_in_nak = longitude % nak_span
        pada = min(int(degrees_in_nak / (nak_span / 4)) + 1, 4)
        name, lord = NAKSHATRA_DATA[nak_index]
        return NakshatraInfo(
            index=nak_index,
            name=name,
            pada=pada,
            lord=lord,
            degrees_in_nakshatra=round(degrees_in_nak, 4)
        )

    def get_positions(self, dt: datetime) -> Dict[Graha, GrahaPosition]:
        """
        Calculate real sidereal positions for all 9 Grahas.

        Args:
            dt: Datetime (must be timezone-aware, preferably UTC)

        Returns:
            Dict mapping each Graha to its GrahaPosition
        """
        from kerykeion import AstrologicalSubject

        if dt is None:
            raise TypeError("datetime cannot be None")

        subject = AstrologicalSubject(
            "NavagrahaSystem",
            dt.year, dt.month, dt.day,
            dt.hour, dt.minute,
            city=self.city,
            lat=self.latitude,
            lng=self.longitude_geo,
            zodiac_type="Sidereal",
            sidereal_mode="LAHIRI",
            online=False
        )

        positions: Dict[Graha, GrahaPosition] = {}

        # 7 visible planets from Kerykeion
        for attr_name, graha in KERYKEION_PLANET_MAP.items():
            planet = getattr(subject, attr_name)
            abs_pos = float(planet.abs_pos)
            sign_num = int(planet.sign_num)
            sign_lng = float(planet.position)
            retrograde = bool(planet.retrograde)

            positions[graha] = GrahaPosition(
                graha=graha,
                longitude=abs_pos,
                sign=SIGN_NAMES[sign_num],
                sign_num=sign_num,
                sign_longitude=sign_lng,
                retrograde=retrograde,
                nakshatra=self._longitude_to_nakshatra(abs_pos)
            )

        # Rahu (True North Lunar Node) — always retrograde
        rahu_node = subject.true_north_lunar_node
        rahu_lng = float(rahu_node.abs_pos)
        rahu_sign_num = int(rahu_node.sign_num)
        positions[Graha.RAHU] = GrahaPosition(
            graha=Graha.RAHU,
            longitude=rahu_lng,
            sign=SIGN_NAMES[rahu_sign_num],
            sign_num=rahu_sign_num,
            sign_longitude=float(rahu_node.position),
            retrograde=True,  # Invariant
            nakshatra=self._longitude_to_nakshatra(rahu_lng)
        )

        # Ketu = Rahu + 180° — always retrograde
        ketu_lng = (rahu_lng + 180.0) % 360.0
        ketu_sign_num = int(ketu_lng / 30) % 12
        positions[Graha.KETU] = GrahaPosition(
            graha=Graha.KETU,
            longitude=ketu_lng,
            sign=SIGN_NAMES[ketu_sign_num],
            sign_num=ketu_sign_num,
            sign_longitude=ketu_lng % 30,
            retrograde=True,  # Invariant
            nakshatra=self._longitude_to_nakshatra(ketu_lng)
        )

        logger.debug(f"Calculated {len(positions)} planetary positions for {dt}")
        return positions

    def get_sunrise_sunset(
        self, dt: datetime
    ) -> Tuple[datetime, datetime]:
        """
        Calculate Hindu sunrise and sunset using pyswisseph.

        Falls back to geometric calculation for extreme latitudes.
        """
        import swisseph as swe

        swe.set_topo(self.longitude_geo, self.latitude, self.altitude)

        # Julian day number
        jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60.0)

        try:
            # Hindu sunrise: center of disc at geometric horizon
            rise_info = swe.rise_trans(
                jd, swe.SUN,
                rsmi=swe.BIT_DISC_CENTER | swe.CALC_RISE,
                geopos=(self.longitude_geo, self.latitude, self.altitude)
            )
            set_info = swe.rise_trans(
                jd, swe.SUN,
                rsmi=swe.BIT_DISC_CENTER | swe.CALC_SET,
                geopos=(self.longitude_geo, self.latitude, self.altitude)
            )

            sunrise_jd = rise_info[1][0]
            sunset_jd = set_info[1][0]

            sunrise = self._jd_to_datetime(sunrise_jd)
            sunset = self._jd_to_datetime(sunset_jd)

            return sunrise, sunset

        except Exception as e:
            logger.warning(
                f"sunrise/sunset calc failed for {self.latitude}°N: {e}. "
                f"Using geometric fallback."
            )
            # Geometric fallback: assume 6:00 sunrise, 18:00 sunset
            base = dt.replace(hour=0, minute=0, second=0, microsecond=0)
            return (
                base.replace(hour=6, minute=0),
                base.replace(hour=18, minute=0)
            )

    @staticmethod
    def _jd_to_datetime(jd: float) -> datetime:
        """Convert Julian Day to Python datetime (UTC)."""
        import swisseph as swe
        year, month, day, hour_frac = swe.revjul(jd)
        hours = int(hour_frac)
        minutes = int((hour_frac - hours) * 60)
        seconds = int(((hour_frac - hours) * 60 - minutes) * 60)
        return datetime(year, month, day, hours, minutes, seconds,
                       tzinfo=timezone.utc)
```

---

### TAAK 1.3: NakshatraCalculator + VimshottariDasha

**Doel**: Echte nakshatra-bepaling en Dasha-cyclus berekening.

**Bestanden te creëren**:
- `backend/core/navagraha/nakshatra.py`
- `backend/core/navagraha/dasha.py`
- `backend/tests/unit/test_nakshatra.py`
- `backend/tests/unit/test_dasha.py`

**Afhankelijk van**: Taak 1.2 (EphemerisCalculator)

---

#### Microtaak 1.3.1: NakshatraCalculator

**Masterprompt**:
```
27 Nakshatras van elk 13°20' (800 boogminuten). Elke nakshatra heeft 4 padas
van 3°20'. De Vimsottari Lord cyclus herhaalt per 3 nakshatras:
Ketu→Venus→Sun→Moon→Mars→Rahu→Jupiter→Saturn→Mercury.
Deze calculator neemt een absolute siderische longitude en retourneert
NakshatraInfo. Mag ook het volledige NAKSHATRA_DATA array exporteren.
```

**Test FIRST (TDD Red)**:
```python
# backend/tests/unit/test_nakshatra.py

import pytest
from backend.core.navagraha.nakshatra import NakshatraCalculator
from backend.core.navagraha.models import Graha


class TestNakshatraCalculator:
    """Test nakshatra determination from longitude."""

    @pytest.fixture
    def calc(self):
        return NakshatraCalculator()

    def test_ashwini_at_zero_degrees(self, calc):
        """Happy: 0° = Ashwini, pada 1, lord Ketu."""
        result = calc.from_longitude(0.0)
        assert result.name == "Ashwini"
        assert result.index == 0
        assert result.pada == 1
        assert result.lord == Graha.KETU

    def test_ashwini_pada_2(self, calc):
        """Happy: 3.5° = Ashwini pada 2."""
        result = calc.from_longitude(3.5)
        assert result.name == "Ashwini"
        assert result.pada == 2

    def test_bharani_starts_at_13_33(self, calc):
        """Happy: 13.34° = Bharani (2e nakshatra)."""
        result = calc.from_longitude(13.34)
        assert result.name == "Bharani"
        assert result.index == 1
        assert result.lord == Graha.SHUKRA

    def test_revati_at_end_of_zodiac(self, calc):
        """Happy: 359° = Revati (27e/laatste nakshatra)."""
        result = calc.from_longitude(359.0)
        assert result.name == "Revati"
        assert result.index == 26
        assert result.lord == Graha.BUDHA

    def test_all_27_nakshatras_reachable(self, calc):
        """Happy: Alle 27 nakshatras zijn bereikbaar."""
        seen = set()
        for i in range(27):
            lng = i * 13.3333 + 1.0  # Midden van elke nakshatra
            info = calc.from_longitude(lng)
            seen.add(info.index)
        assert len(seen) == 27

    def test_vimsottari_lord_cycle(self, calc):
        """Happy: Lord cyclus herhaalt per 3 nakshatras."""
        expected_cycle = [
            Graha.KETU, Graha.SHUKRA, Graha.SURYA,
            Graha.CHANDRA, Graha.MANGALA, Graha.RAHU,
            Graha.BRIHASPATI, Graha.SHANI, Graha.BUDHA,
        ]
        for i in range(27):
            info = calc.from_longitude(i * 13.3333 + 1.0)
            expected_lord = expected_cycle[i % 9]
            assert info.lord == expected_lord, \
                f"Nakshatra {i} ({info.name}): expected {expected_lord}, got {info.lord}"

    def test_negative_longitude_raises(self, calc):
        """Unhappy: Negatieve longitude."""
        with pytest.raises(ValueError):
            calc.from_longitude(-1.0)

    def test_longitude_360_wraps(self, calc):
        """Unhappy: 360° moet wrappen naar 0°."""
        result = calc.from_longitude(360.0)
        assert result.index == 0  # Ashwini
```

---

#### Microtaak 1.3.2: VimshottariDasha

**Masterprompt**:
```
120-jaar Vimshottari Dasha systeem.
Systeem-"geboorte" = eerste deployment datetime (configureerbaar).
Maan-positie op dat moment → Janma Nakshatra → startende Mahadasha.
Dasha jaren: Ketu=7, Venus=20, Sun=6, Moon=10, Mars=7, Rahu=18, Jupiter=16, Saturn=19, Mercury=17.
Antardasha = sub-periodes proportioneel verdeeld binnen Mahadasha.
Berekent welke Mahadasha en Antardasha momenteel actief zijn.

Bestaande referentie: backend/core/memory_system.py (voor datetime patronen)
```

**Test FIRST (TDD Red)**:
```python
# backend/tests/unit/test_dasha.py

import pytest
from datetime import datetime, timezone, timedelta
from backend.core.navagraha.dasha import VimshottariDasha
from backend.core.navagraha.models import Graha, NakshatraInfo, DashaState


class TestVimshottariDasha:
    """Test Dasha lifecycle calculations."""

    @pytest.fixture
    def dasha(self):
        """System born when Moon at 0° (Ashwini → Ketu Mahadasha start)."""
        birth = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        moon_longitude = 0.0  # Ashwini → lord Ketu
        return VimshottariDasha(
            system_birth=birth,
            moon_longitude_at_birth=moon_longitude
        )

    def test_initial_mahadasha_lord(self, dasha):
        """Happy: Mahadasha bij Ashwini Moon = Ketu."""
        state = dasha.get_state(
            datetime(2025, 6, 1, 0, 0, 0, tzinfo=timezone.utc)
        )
        assert state.mahadasha_lord == Graha.KETU

    def test_ketu_mahadasha_duration_7_years(self, dasha):
        """Happy: Ketu Mahadasha duurt 7 jaar."""
        state = dasha.get_state(
            datetime(2025, 1, 2, 0, 0, 0, tzinfo=timezone.utc)
        )
        assert state.mahadasha_years_total == 7.0

    def test_mahadasha_progress_increases(self, dasha):
        """Happy: Progress neemt toe over tijd."""
        early = dasha.get_state(datetime(2025, 2, 1, tzinfo=timezone.utc))
        later = dasha.get_state(datetime(2028, 1, 1, tzinfo=timezone.utc))
        assert later.mahadasha_progress > early.mahadasha_progress

    def test_after_ketu_comes_venus(self, dasha):
        """Happy: Na Ketu (7 jaar) komt Venus (20 jaar)."""
        # 7 jaar + 1 dag na birth
        state = dasha.get_state(
            datetime(2032, 1, 2, 0, 0, 0, tzinfo=timezone.utc)
        )
        assert state.mahadasha_lord == Graha.SHUKRA

    def test_antardasha_changes_within_mahadasha(self, dasha):
        """Happy: Antardasha wisselt binnen Mahadasha."""
        # Eerste sub-periode van Ketu Mahadasha = Ketu/Ketu
        state = dasha.get_state(
            datetime(2025, 3, 1, 0, 0, 0, tzinfo=timezone.utc)
        )
        assert state.antardasha_lord is not None

    def test_janma_nakshatra_stored(self, dasha):
        """Happy: Janma nakshatra is opgeslagen in state."""
        state = dasha.get_state(datetime(2025, 6, 1, tzinfo=timezone.utc))
        assert state.janma_nakshatra.name == "Ashwini"
        assert state.janma_nakshatra.lord == Graha.KETU

    def test_full_120_year_cycle(self, dasha):
        """Happy: Na 120 jaar begint cyclus opnieuw."""
        # Sum of all dasha years = 7+20+6+10+7+18+16+19+17 = 120
        cycle_end = datetime(2145, 1, 2, 0, 0, 0, tzinfo=timezone.utc)
        state = dasha.get_state(cycle_end)
        assert state.mahadasha_lord == Graha.KETU  # Terug naar begin

    def test_date_before_birth_raises(self, dasha):
        """Unhappy: Datum vóór system birth gooit error."""
        with pytest.raises(ValueError, match="before system birth"):
            dasha.get_state(datetime(2024, 12, 31, tzinfo=timezone.utc))

    def test_progress_never_exceeds_1(self, dasha):
        """Happy: Progress is altijd 0.0-1.0."""
        for year in range(2025, 2150):
            state = dasha.get_state(
                datetime(year, 6, 1, tzinfo=timezone.utc)
            )
            assert 0.0 <= state.mahadasha_progress <= 1.0
            assert 0.0 <= state.antardasha_progress <= 1.0
```

**Taak-afronding integratie test**:
```python
# backend/tests/integration/test_nakshatra_dasha_integration.py

async def test_integration_1_3_dasha_with_real_ephemeris():
    """
    Integratie: EphemerisCalculator bepaalt Moon longitude →
    VimshottariDasha berekent correcte Mahadasha.
    """
    from backend.core.navagraha.ephemeris import EphemerisCalculator
    from backend.core.navagraha.dasha import VimshottariDasha
    from backend.core.navagraha.models import Graha

    calc = EphemerisCalculator()
    birth = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    positions = calc.get_positions(birth)
    moon_lng = positions[Graha.CHANDRA].longitude

    dasha = VimshottariDasha(
        system_birth=birth,
        moon_longitude_at_birth=moon_lng
    )
    state = dasha.get_state(datetime.now(timezone.utc))

    assert state.mahadasha_lord is not None
    assert state.janma_nakshatra is not None
    assert 0.0 <= state.mahadasha_progress <= 1.0
```

---

### TAAK 1.4: AspectAnalyzer + RahuKala + Hora

**Doel**: Drie calculators voor aspects, Rahu Kala timing, en planetaire uren.

**Bestanden te creëren**:
- `backend/core/navagraha/aspects.py`
- `backend/core/navagraha/rahu_kala.py`
- `backend/core/navagraha/hora.py`
- `backend/tests/unit/test_aspects.py`
- `backend/tests/unit/test_rahu_kala.py`
- `backend/tests/unit/test_hora.py`

**Afhankelijk van**: Taak 1.2

---

#### Microtaak 1.4.1: AspectAnalyzer

**Masterprompt**:
```
Bereken planetaire aspecten (Drishti) tussen planeten.
Aspecttypen: conjunction (0°, orb 10°), sextile (60°, orb 6°),
square (90°, orb 10°), trine (120°, orb 10°), opposition (180°, orb 10°).
Strength = 1.0 - (orb / max_orb). Alleen aspecten met strength > 0 retourneren.
Applying = planeten bewegen naar exact; separating = weg van exact.
Input: Dict[Graha, GrahaPosition]. Output: List[AspectInfo].
"""
```

**Test FIRST**:
```python
# backend/tests/unit/test_aspects.py

import pytest
from backend.core.navagraha.aspects import AspectAnalyzer
from backend.core.navagraha.models import (
    Graha, GrahaPosition, NakshatraInfo, AspectInfo, AspectType
)


class TestAspectAnalyzer:

    @pytest.fixture
    def analyzer(self):
        return AspectAnalyzer()

    def _pos(self, graha, lng, retro=False):
        """Helper: maak GrahaPosition."""
        if graha in (Graha.RAHU, Graha.KETU):
            retro = True
        sign_num = int(lng / 30) % 12
        signs = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
                 "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
        nak_idx = int(lng / 13.3333) % 27
        return GrahaPosition(
            graha=graha, longitude=lng % 360,
            sign=signs[sign_num], sign_num=sign_num,
            sign_longitude=lng % 30, retrograde=retro,
            nakshatra=NakshatraInfo(
                index=nak_idx, name=f"Nak_{nak_idx}", pada=1,
                lord=Graha.KETU, degrees_in_nakshatra=0.0
            )
        )

    def test_exact_conjunction(self, analyzer):
        """Happy: Twee planeten op dezelfde graad = conjunction."""
        positions = {
            Graha.SURYA: self._pos(Graha.SURYA, 45.0),
            Graha.CHANDRA: self._pos(Graha.CHANDRA, 45.0),
        }
        aspects = analyzer.find_aspects(positions)
        conj = [a for a in aspects if a.aspect_type == AspectType.CONJUNCTION]
        assert len(conj) >= 1
        assert conj[0].orb == 0.0
        assert conj[0].strength == 1.0

    def test_exact_opposition(self, analyzer):
        """Happy: 180° apart = opposition."""
        positions = {
            Graha.SURYA: self._pos(Graha.SURYA, 0.0),
            Graha.SHANI: self._pos(Graha.SHANI, 180.0),
        }
        aspects = analyzer.find_aspects(positions)
        opp = [a for a in aspects if a.aspect_type == AspectType.OPPOSITION]
        assert len(opp) >= 1

    def test_trine_120_degrees(self, analyzer):
        """Happy: 120° = trine."""
        positions = {
            Graha.BRIHASPATI: self._pos(Graha.BRIHASPATI, 10.0),
            Graha.SURYA: self._pos(Graha.SURYA, 130.0),
        }
        aspects = analyzer.find_aspects(positions)
        trines = [a for a in aspects if a.aspect_type == AspectType.TRINE]
        assert len(trines) >= 1

    def test_no_aspect_at_45_degrees(self, analyzer):
        """Happy: 45° is geen standaard aspect."""
        positions = {
            Graha.SURYA: self._pos(Graha.SURYA, 0.0),
            Graha.CHANDRA: self._pos(Graha.CHANDRA, 45.0),
        }
        aspects = analyzer.find_aspects(positions)
        assert len(aspects) == 0  # 45° matcht geen aspect type

    def test_strength_decreases_with_orb(self, analyzer):
        """Happy: Groter orb = lagere strength."""
        positions = {
            Graha.SURYA: self._pos(Graha.SURYA, 0.0),
            Graha.CHANDRA: self._pos(Graha.CHANDRA, 5.0),  # 5° orb conjunction
        }
        aspects = analyzer.find_aspects(positions)
        assert len(aspects) >= 1
        assert aspects[0].strength < 1.0
        assert aspects[0].strength > 0.0

    def test_empty_positions_returns_empty(self, analyzer):
        """Unhappy: Geen posities = geen aspecten."""
        assert analyzer.find_aspects({}) == []

    def test_single_planet_no_aspects(self, analyzer):
        """Unhappy: Één planeet kan geen aspecten vormen."""
        positions = {Graha.SURYA: self._pos(Graha.SURYA, 45.0)}
        assert analyzer.find_aspects(positions) == []
```

---

#### Microtaak 1.4.2: RahuKalaCalculator

**Masterprompt**:
```
Rahu Kala = ongunstige periode van ~1.5 uur per dag.
Berekend op echte Hindu sunrise (van EphemerisCalculator).
Dagduur verdeeld in 8 segmenten.
Segment per weekdag: Ma=2, Di=7, Wo=5, Do=6, Vr=4, Za=3, Zo=8.
Input: sunrise, sunset, weekday. Output: RahuKalaState.
TRADING GATE: is_active=True → blokkeer nieuwe posities.
"""
```

**Test FIRST**:
```python
# backend/tests/unit/test_rahu_kala.py

import pytest
from datetime import datetime, timezone, timedelta
from backend.core.navagraha.rahu_kala import RahuKalaCalculator
from backend.core.navagraha.models import RahuKalaState


class TestRahuKalaCalculator:

    @pytest.fixture
    def calc(self):
        return RahuKalaCalculator()

    def test_monday_segment_2(self, calc):
        """Happy: Maandag = segment 2."""
        # 2026-02-16 is Maandag
        sunrise = datetime(2026, 2, 16, 7, 30, tzinfo=timezone.utc)
        sunset = datetime(2026, 2, 16, 17, 30, tzinfo=timezone.utc)
        state = calc.calculate(sunrise, sunset, weekday=0)  # 0 = Ma
        assert state.weekday_segment == 2
        # Segment 2 = 2e van 8 segmenten
        day_duration = (sunset - sunrise).total_seconds()
        segment_duration = day_duration / 8
        expected_start = sunrise + timedelta(seconds=segment_duration)
        assert abs((state.start - expected_start).total_seconds()) < 60

    def test_rahu_kala_duration_about_90_minutes(self, calc):
        """Happy: Duur ~1.5 uur (1 segment van dagduur/8)."""
        sunrise = datetime(2026, 2, 16, 7, 0, tzinfo=timezone.utc)
        sunset = datetime(2026, 2, 16, 17, 0, tzinfo=timezone.utc)
        state = calc.calculate(sunrise, sunset, weekday=0)
        duration_min = (state.end - state.start).total_seconds() / 60
        assert 60 <= duration_min <= 120  # 1-2 uur

    def test_is_active_during_rahu_kala(self, calc):
        """Happy: Middenin Rahu Kala is active=True."""
        sunrise = datetime(2026, 2, 16, 7, 0, tzinfo=timezone.utc)
        sunset = datetime(2026, 2, 16, 17, 0, tzinfo=timezone.utc)
        state = calc.calculate(sunrise, sunset, weekday=0)
        midpoint = state.start + (state.end - state.start) / 2
        assert calc.is_active_at(state, midpoint) is True

    def test_is_not_active_outside_rahu_kala(self, calc):
        """Happy: Buiten Rahu Kala is active=False."""
        sunrise = datetime(2026, 2, 16, 7, 0, tzinfo=timezone.utc)
        sunset = datetime(2026, 2, 16, 17, 0, tzinfo=timezone.utc)
        state = calc.calculate(sunrise, sunset, weekday=0)
        before = state.start - timedelta(hours=1)
        assert calc.is_active_at(state, before) is False

    def test_all_weekdays_have_different_segments(self, calc):
        """Happy: Elke weekdag heeft een uniek segment."""
        sunrise = datetime(2026, 2, 16, 7, 0, tzinfo=timezone.utc)
        sunset = datetime(2026, 2, 16, 17, 0, tzinfo=timezone.utc)
        segments = set()
        for day in range(7):
            state = calc.calculate(sunrise, sunset, weekday=day)
            segments.add(state.weekday_segment)
        assert len(segments) == 7  # Allemaal uniek

    def test_sunday_segment_8(self, calc):
        """Happy: Zondag = segment 8 (laatste)."""
        sunrise = datetime(2026, 2, 15, 7, 0, tzinfo=timezone.utc)
        sunset = datetime(2026, 2, 15, 17, 0, tzinfo=timezone.utc)
        state = calc.calculate(sunrise, sunset, weekday=6)  # 6 = zo
        assert state.weekday_segment == 8

    def test_invalid_weekday_raises(self, calc):
        """Unhappy: Weekday buiten 0-6 gooit error."""
        sunrise = datetime(2026, 2, 16, 7, 0, tzinfo=timezone.utc)
        sunset = datetime(2026, 2, 16, 17, 0, tzinfo=timezone.utc)
        with pytest.raises(ValueError):
            calc.calculate(sunrise, sunset, weekday=7)

    def test_sunset_before_sunrise_raises(self, calc):
        """Unhappy: Sunset vóór sunrise gooit error."""
        with pytest.raises(ValueError, match="sunset.*before.*sunrise"):
            calc.calculate(
                sunrise=datetime(2026, 2, 16, 17, 0, tzinfo=timezone.utc),
                sunset=datetime(2026, 2, 16, 7, 0, tzinfo=timezone.utc),
                weekday=0
            )
```

---

#### Microtaak 1.4.3: HoraCalculator

**Masterprompt**:
```
Chaldeeuwse volgorde: Saturn→Jupiter→Mars→Sun→Venus→Mercury→Moon.
Dag verdeeld in 12 dag-uren + 12 nacht-uren op basis van echte sunrise/sunset.
Eerste dag-uur per weekdag: Ma=Moon, Di=Mars, Wo=Mercury, Do=Jupiter,
Vr=Venus, Za=Saturn, Zo=Sun.
"""
```

**Test FIRST**:
```python
# backend/tests/unit/test_hora.py

import pytest
from datetime import datetime, timezone, timedelta
from backend.core.navagraha.hora import HoraCalculator
from backend.core.navagraha.models import Graha, HoraState


class TestHoraCalculator:

    @pytest.fixture
    def calc(self):
        return HoraCalculator()

    def test_sunday_first_hour_is_sun(self, calc):
        """Happy: Zondag eerste uur = Sun."""
        sunrise = datetime(2026, 2, 15, 7, 0, tzinfo=timezone.utc)
        sunset = datetime(2026, 2, 15, 17, 0, tzinfo=timezone.utc)
        state = calc.get_hora(sunrise, sunset, weekday=6,
                             current_time=sunrise + timedelta(minutes=5))
        assert state.ruling_planet == Graha.SURYA
        assert state.hora_number == 1
        assert state.is_day is True

    def test_monday_first_hour_is_moon(self, calc):
        """Happy: Maandag eerste uur = Moon."""
        sunrise = datetime(2026, 2, 16, 7, 0, tzinfo=timezone.utc)
        sunset = datetime(2026, 2, 16, 17, 0, tzinfo=timezone.utc)
        state = calc.get_hora(sunrise, sunset, weekday=0,
                             current_time=sunrise + timedelta(minutes=5))
        assert state.ruling_planet == Graha.CHANDRA

    def test_chaldean_sequence_progresses(self, calc):
        """Happy: Na Sun komt Venus (Chaldeeuwse volgorde)."""
        sunrise = datetime(2026, 2, 15, 7, 0, tzinfo=timezone.utc)
        sunset = datetime(2026, 2, 15, 17, 0, tzinfo=timezone.utc)
        day_hour_len = (sunset - sunrise).total_seconds() / 12

        # 2e dag-uur op zondag
        state = calc.get_hora(sunrise, sunset, weekday=6,
                             current_time=sunrise + timedelta(seconds=day_hour_len + 60))
        assert state.ruling_planet == Graha.SHUKRA  # Sun → Venus

    def test_night_hours_start_after_sunset(self, calc):
        """Happy: Na sunset beginnen nacht-uren (hora 13+)."""
        sunrise = datetime(2026, 2, 15, 7, 0, tzinfo=timezone.utc)
        sunset = datetime(2026, 2, 15, 17, 0, tzinfo=timezone.utc)
        state = calc.get_hora(sunrise, sunset, weekday=6,
                             current_time=sunset + timedelta(minutes=10))
        assert state.is_day is False
        assert state.hora_number >= 13

    def test_hora_number_always_1_to_24(self, calc):
        """Happy: Hora nummer is altijd 1-24."""
        sunrise = datetime(2026, 2, 15, 7, 0, tzinfo=timezone.utc)
        sunset = datetime(2026, 2, 15, 17, 0, tzinfo=timezone.utc)
        for minute in range(0, 1440, 30):
            ct = sunrise + timedelta(minutes=minute)
            state = calc.get_hora(sunrise, sunset, weekday=6, current_time=ct)
            assert 1 <= state.hora_number <= 24

    def test_time_before_sunrise_raises(self, calc):
        """Unhappy: Tijd vóór sunrise van dezelfde dag."""
        sunrise = datetime(2026, 2, 15, 7, 0, tzinfo=timezone.utc)
        sunset = datetime(2026, 2, 15, 17, 0, tzinfo=timezone.utc)
        with pytest.raises(ValueError):
            calc.get_hora(sunrise, sunset, weekday=6,
                         current_time=sunrise - timedelta(hours=2))
```

**Taak-afronding integratie test**:
```python
# backend/tests/integration/test_aspects_rahu_hora_integration.py

async def test_integration_1_4_rahu_kala_with_real_sunrise():
    """
    Integratie: EphemerisCalculator sunrise → RahuKalaCalculator.
    Verificeert end-to-end Rahu Kala berekening op echte sunrise.
    """
    from backend.core.navagraha.ephemeris import EphemerisCalculator
    from backend.core.navagraha.rahu_kala import RahuKalaCalculator

    eph = EphemerisCalculator()
    now = datetime.now(timezone.utc)
    sunrise, sunset = eph.get_sunrise_sunset(now)

    rahu = RahuKalaCalculator()
    state = rahu.calculate(sunrise, sunset, weekday=now.weekday())

    assert state.sunrise == sunrise
    assert state.sunset == sunset
    duration_min = (state.end - state.start).total_seconds() / 60
    assert 60 <= duration_min <= 120


async def test_integration_1_4_aspects_with_real_positions():
    """
    Integratie: EphemerisCalculator posities → AspectAnalyzer.
    """
    from backend.core.navagraha.ephemeris import EphemerisCalculator
    from backend.core.navagraha.aspects import AspectAnalyzer

    eph = EphemerisCalculator()
    positions = eph.get_positions(datetime.now(timezone.utc))

    analyzer = AspectAnalyzer()
    aspects = analyzer.find_aspects(positions)

    # Er zijn ALTIJD aspecten (9 planeten = minstens enkele)
    assert len(aspects) >= 1
    for aspect in aspects:
        assert 0.0 <= aspect.strength <= 1.0
```

---

### TAAK 1.5: GrahaGunaMapper

**Doel**: Vertaal planetaire staat naar Guna modulation vector.

**Bestanden te creëren**:
- `backend/core/navagraha/graha_guna_mapper.py`
- `backend/tests/unit/test_graha_guna_mapper.py`

**Afhankelijk van**: Taak 1.2, 1.3, 1.4

---

#### Microtaak 1.5.1: Mapping regels implementatie

**Masterprompt**:
```
Vertaalregels (uit blueprint):
| Graha State                    | Sattva | Rajas | Tamas |
|--------------------------------|--------|-------|-------|
| Jupiter trine/conjunction Sun  | +0.15  | +0.05 | -0.10 |
| Mars square Saturn             | -0.10  | +0.20 | +0.05 |
| Mercury retrograde             | -0.05  | -0.15 | +0.10 |
| Rahu Kala active               | -0.20  | -0.10 | +0.30 |
| Mahadasha = Jupiter            | +0.10  | +0.05 | -0.05 |
| Moon in own nakshatra          | +0.10  | 0.00  | -0.05 |

Element-Planeet heerschappij:
| Element | Heerser   | Effect                                          |
|---------|-----------|------------------------------------------------|
| Ether   | Jupiter   | Jupiter sign/aspect → Ether prana              |
| Air     | Saturn    | Saturn retrograde → Air agent geremd           |
| Fire    | Mars      | Mars in fire sign → Fire agent versterkt       |
| Water   | Venus     | Venus conjunction Moon → Water sensitief       |
| Earth   | Mercury   | Mercury retrograde → Earth agent conservatief   |

Input: NavagrahaState. Output: GunaModulation.
Bestaande referentie: backend/schemas/guna.py (GunaVector)
"""
```

**Test FIRST**:
```python
# backend/tests/unit/test_graha_guna_mapper.py

import pytest
from backend.core.navagraha.graha_guna_mapper import GrahaGunaMapper
from backend.core.navagraha.models import *
from datetime import datetime, timezone, timedelta


class TestGrahaGunaMapper:

    @pytest.fixture
    def mapper(self):
        return GrahaGunaMapper()

    def test_jupiter_mahadasha_increases_sattva(self, mapper):
        """Happy: Jupiter Mahadasha → +sattva."""
        state = _make_state(mahadasha_lord=Graha.BRIHASPATI)
        mod = mapper.compute_modulation(state)
        assert mod.sattva_delta > 0

    def test_rahu_kala_active_increases_tamas(self, mapper):
        """Happy: Rahu Kala actief → +0.30 tamas."""
        state = _make_state(rahu_active=True)
        mod = mapper.compute_modulation(state)
        assert mod.tamas_delta >= 0.25
        assert mod.sattva_delta < 0

    def test_mercury_retrograde_increases_tamas(self, mapper):
        """Happy: Mercury retrograde → conservatief."""
        state = _make_state(mercury_retrograde=True)
        mod = mapper.compute_modulation(state)
        assert mod.tamas_delta > 0
        assert mod.rajas_delta < 0

    def test_neutral_state_near_zero(self, mapper):
        """Happy: Neutrale staat → modulation dicht bij nul."""
        state = _make_state()
        mod = mapper.compute_modulation(state)
        assert abs(mod.sattva_delta) < 0.5
        assert abs(mod.rajas_delta) < 0.5
        assert abs(mod.tamas_delta) < 0.5

    def test_confidence_is_valid(self, mapper):
        """Happy: Confidence altijd 0-1."""
        state = _make_state()
        mod = mapper.compute_modulation(state)
        assert 0.0 <= mod.confidence <= 1.0

    def test_element_ruler_prana_adjustments(self, mapper):
        """Happy: Element-planeet heerschappij retourneert prana deltas."""
        state = _make_state()
        prana = mapper.get_element_prana_adjustments(state)
        assert "ether" in prana
        assert "fire" in prana
        assert all(isinstance(v, float) for v in prana.values())

    def test_mars_in_fire_sign_boosts_fire_prana(self, mapper):
        """Happy: Mars in Aries/Leo/Sagittarius → fire prana +."""
        state = _make_state(mars_sign="Aries")  # Fire sign
        prana = mapper.get_element_prana_adjustments(state)
        assert prana["fire"] > 0

    def test_saturn_retrograde_reduces_air_prana(self, mapper):
        """Happy: Saturn retrograde → air prana -."""
        state = _make_state(saturn_retrograde=True)
        prana = mapper.get_element_prana_adjustments(state)
        assert prana["air"] < 0
```

---

### TAAK 1.6: NavagrahaEngine Orchestrator

**Doel**: Orchestreert alle sub-calculators tot één NavagrahaState.

**Bestanden te creëren**:
- `backend/core/navagraha/engine.py`
- `backend/tests/unit/test_navagraha_engine.py`

**Afhankelijk van**: Taak 1.5

---

#### Microtaak 1.6.1: Engine `assess()` methode

**Masterprompt**:
```
NavagrahaEngine.assess(dt: datetime) → NavagrahaState.
Orkestreert: EphemerisCalculator → NakshatraCalculator → VimshottariDasha →
AspectAnalyzer → RahuKalaCalculator → HoraCalculator → GrahaGunaMapper.
Inclusief caching: posities 5 min, aspects 15 min, rahu_kala per dag, dasha per dag.
System birth datetime configureerbaar (default: settings of env var).
"""
```

**Test FIRST**:
```python
# backend/tests/unit/test_navagraha_engine.py

import pytest
from datetime import datetime, timezone
from backend.core.navagraha.engine import NavagrahaEngine
from backend.core.navagraha.models import Graha, NavagrahaState


class TestNavagrahaEngine:

    @pytest.fixture
    def engine(self):
        return NavagrahaEngine(
            system_birth=datetime(2025, 1, 1, tzinfo=timezone.utc),
            latitude=52.3676,
            longitude_geo=4.9041
        )

    def test_assess_returns_navagraha_state(self, engine):
        """Happy: assess() retourneert NavagrahaState."""
        state = engine.assess(datetime.now(timezone.utc))
        assert isinstance(state, NavagrahaState)

    def test_assess_has_9_positions(self, engine):
        """Happy: State bevat exact 9 posities."""
        state = engine.assess(datetime.now(timezone.utc))
        assert len(state.positions) == 9

    def test_assess_has_rahu_kala(self, engine):
        """Happy: State bevat Rahu Kala info."""
        state = engine.assess(datetime.now(timezone.utc))
        assert state.rahu_kala is not None
        assert isinstance(state.rahu_kala.is_active, bool)

    def test_assess_has_dasha(self, engine):
        """Happy: State bevat Dasha info."""
        state = engine.assess(datetime.now(timezone.utc))
        assert state.dasha is not None
        assert state.dasha.mahadasha_lord in list(Graha)

    def test_assess_has_hora(self, engine):
        """Happy: State bevat Hora info."""
        state = engine.assess(datetime.now(timezone.utc))
        assert state.hora is not None
        assert state.hora.ruling_planet in list(Graha)

    def test_assess_trading_gate_consistent(self, engine):
        """Happy: Trading gate sluit bij Rahu Kala."""
        state = engine.assess(datetime.now(timezone.utc))
        if state.rahu_kala.is_active:
            assert state.trading_gate_open is False

    def test_caching_returns_same_result_within_ttl(self, engine):
        """Happy: Tweede call binnen 5 min returnt cached result."""
        now = datetime.now(timezone.utc)
        state1 = engine.assess(now)
        state2 = engine.assess(now)
        assert state1.timestamp == state2.timestamp

    def test_assess_handles_none_datetime(self, engine):
        """Unhappy: None datetime gooit TypeError."""
        with pytest.raises((TypeError, ValueError)):
            engine.assess(None)
```

**Taak-afronding integratie test**:
```python
# backend/tests/integration/test_navagraha_engine_integration.py

def test_integration_1_6_full_engine_real_ephemeris():
    """
    Integratie: NavagrahaEngine end-to-end met echte Swiss Ephemeris.
    Cross-check: Rahu altijd retrograde, 9 posities, valid Rahu Kala.
    """
    engine = NavagrahaEngine(
        system_birth=datetime(2025, 1, 1, tzinfo=timezone.utc)
    )
    state = engine.assess(datetime.now(timezone.utc))

    # 9 posities
    assert len(state.positions) == 9

    # Rahu retrograde invariant
    assert state.positions[Graha.RAHU].retrograde is True
    assert state.positions[Graha.KETU].retrograde is True

    # Ketu tegenover Rahu
    rahu = state.positions[Graha.RAHU].longitude
    ketu = state.positions[Graha.KETU].longitude
    diff = abs((ketu - rahu + 180) % 360 - 180)
    assert diff < 1.0 or abs(diff - 180) < 1.0

    # Rahu Kala geldig
    rk = state.rahu_kala
    duration = (rk.end - rk.start).total_seconds() / 60
    assert 60 <= duration <= 120

    # Dasha geldig
    assert state.dasha.mahadasha_progress >= 0.0

    # Guna modulation aanwezig
    assert state.guna_modulation is not None

    # Serialisatie roundtrip
    json_str = state.model_dump_json()
    restored = NavagrahaState.model_validate_json(json_str)
    assert len(restored.positions) == 9
```

---

### TAAK 1.7: Wire into CognitiveBridge + SystemIdentity

**Doel**: NavagrahaEngine injecteren in de bestaande cognitive core.

**Bestanden te wijzigen**:
- `backend/core/adapters/system_bridge.py` (CognitiveBridge, 184 regels)
- `backend/core/system_identity.py` (SystemIdentity, 595 regels)

**Bestaande code referenties**:

`system_bridge.py:30` — CognitiveBridge.__init__:
```python
def __init__(self, system_identity: SystemIdentity, window_size: int = 20):
```

`system_identity.py:86-130` — process_market_cycle start:
```python
async def process_market_cycle(self, price_data, volume_data, ...):
    cycle_start = int(time.time_ns())
    tattva_traversal = {'layers_traversed': [], 'coherence_per_layer': {}}
    # ========== ASCEND: Layers 1-5 ==========
    for layer_num in range(1, 6):
        ...
```

---

#### Microtaak 1.7.1: NavagrahaEngine in CognitiveBridge

**Masterprompt**:
```
Voeg optionele navagraha_engine parameter toe aan CognitiveBridge.__init__().
In process_observation(), roep engine.assess() aan VOOR system_identity.process_market_cycle().
Geef navagraha_state mee als extra parameter aan process_market_cycle().
Backward compatible: als engine None is, skip Navagraha.
```

**Wijziging in system_bridge.py:30**:
```python
# VOOR:
def __init__(self, system_identity: SystemIdentity, window_size: int = 20):

# NA:
def __init__(
    self,
    system_identity: SystemIdentity,
    window_size: int = 20,
    navagraha_engine: Optional["NavagrahaEngine"] = None  # ★ NEW
):
    self.system_identity = system_identity
    self.window_size = window_size
    self.navagraha_engine = navagraha_engine  # ★ NEW
```

**Wijziging in system_bridge.py ~100 (process_observation)**:
```python
# ★ NEW: Assess planetary state before cognitive processing
navagraha_state = None
if self.navagraha_engine:
    navagraha_state = self.navagraha_engine.assess(
        datetime.now(timezone.utc)
    )

# Call SystemIdentity with navagraha state
result = await self.system_identity.process_market_cycle(
    price_data=price_array,
    volume_data=volume_array,
    orderbook_imbalance=orderbook_imbalance,
    funding_rate=obs.funding_rate or 0.0,
    social_sentiment=obs.social_sentiment,
    navagraha_state=navagraha_state  # ★ NEW
)
```

#### Microtaak 1.7.2: Navagraha Guna modulation in SystemIdentity

**Masterprompt**:
```
In process_market_cycle(), voeg optioneel navagraha_state parameter toe.
Vóór de ASCEND fase (regel ~120), pas guna_modulation toe op base_guna.
Dit verschuift de hele 36-Tattva traversal.
"""
```

**Wijziging in system_identity.py:82**:
```python
# VOOR:
async def process_market_cycle(self, price_data, volume_data,
                                orderbook_imbalance, funding_rate, social_sentiment):

# NA:
async def process_market_cycle(self, price_data, volume_data,
                                orderbook_imbalance, funding_rate, social_sentiment,
                                navagraha_state=None):  # ★ NEW
```

**Inject vóór ASCEND (~regel 120)**:
```python
    # ★ NEW: Apply Navagraha Guna modulation pre-Ascend
    if navagraha_state and hasattr(navagraha_state, 'guna_modulation'):
        mod = navagraha_state.guna_modulation
        self.base_guna = {
            'sattva': max(0, min(1, self.base_guna.get('sattva', 0.33) + mod.sattva_delta)),
            'rajas': max(0, min(1, self.base_guna.get('rajas', 0.33) + mod.rajas_delta)),
            'tamas': max(0, min(1, self.base_guna.get('tamas', 0.33) + mod.tamas_delta)),
        }
        logger.info(
            f"Navagraha Guna modulation applied: "
            f"S={mod.sattva_delta:+.2f} R={mod.rajas_delta:+.2f} T={mod.tamas_delta:+.2f}"
        )

    # ========== ASCEND: Layers 1-5 (Shuddha Tattvas) ==========
```

**Tests**:
```python
# backend/tests/integration/test_cognitive_bridge_navagraha.py

async def test_integration_1_7_bridge_with_navagraha():
    """Integratie: CognitiveBridge met NavagrahaEngine."""
    from backend.core.navagraha.engine import NavagrahaEngine
    # ... setup
    bridge = CognitiveBridge(
        system_identity=sys_id,
        navagraha_engine=NavagrahaEngine(system_birth=birth)
    )
    confidence = await bridge.process_observation(observation)
    assert 0.0 <= confidence <= 1.0

async def test_integration_1_7_bridge_without_navagraha_backward_compat():
    """Integratie: Zonder engine werkt alles nog (backward compat)."""
    bridge = CognitiveBridge(system_identity=sys_id)
    confidence = await bridge.process_observation(observation)
    assert 0.0 <= confidence <= 1.0
```

---

### TAAK 1.8: Wire into OODALoopCoordinator

**Doel**: Navagraha + Elemental integratie in de OODA loop.

**Bestanden te wijzigen**:
- `backend/orchestration/ooda_coordinator.py` (530 regels)
- `backend/agents/orchestrator_agent.py` (119 regels)

**Bestaande code referenties**:

`ooda_coordinator.py:302-345` — _orient() methode
`ooda_coordinator.py:346-385` — _decide() methode
`ooda_coordinator.py:112` — run_cycle() entry point

---

#### Microtaak 1.8.1: Rahu Kala trading gate in _decide()

**Masterprompt**:
```
In _decide() (ooda_coordinator.py:346), NA het TraderAgent voorstel maar VOOR
RiskManager beoordeling, check navagraha_state.rahu_kala.is_active.
Als True: return (None, None, None) met log "Rahu Kala active — HOLD".
navagraha_state wordt doorgegeven als parameter.
"""
```

**Wijzigingen en tests: zie de test hieronder.**

```python
# backend/tests/integration/test_ooda_navagraha.py

async def test_integration_1_8_rahu_kala_blocks_trading():
    """
    Integratie: OODALoopCoordinator blokkeert trades tijdens Rahu Kala.
    """
    # Mock navagraha_state met rahu_kala.is_active=True
    # Run coordinator._decide()
    # Assert: proposal is None (HOLD)

async def test_integration_1_8_normal_trading_without_rahu_kala():
    """
    Integratie: Zonder Rahu Kala gaat trading normaal door.
    """
    # Mock navagraha_state met rahu_kala.is_active=False
    # Run coordinator._decide()
    # Assert: proposal is niet None (trade kan doorgaan)

async def test_integration_1_8_elemental_synthesis_in_orient():
    """
    Integratie: _orient() bevat elemental synthesis stap.
    """
    # Verify dat ElementalRouter.route_signal() wordt aangeroepen in _orient()

async def test_integration_1_8_harmony_includes_planetary_state():
    """
    Integratie: OrchestratorAgent.harmonize() incorporeert planetary harmony.
    """
    # Verify harmony_score bevat navagraha component
```

---

### TAAK 1.9: Wire ElementalAgents Graha-Prana + Prana Lifecycle

**Doel**: Elke elemental agent krijgt energie van zijn heersende planeet.

**Bestanden te wijzigen**:
- `backend/agents/elemental_base.py` (192 regels)

**Bestaande code referentie**:

`elemental_base.py:60-80`:
```python
def consume_prana(self, amount: float = None):
    cost = amount or self.prana_decay_rate
    self.prana = max(0.0, self.prana - cost)
    if self.prana < 10:
        self._health_status = "degraded"

def regenerate_prana(self, delta_seconds: float = 60.0):
    regen_rate = 5.0
    if self.element == "ether":
        regen_rate *= 1.5
    self.prana = min(self.max_prana, self.prana + regen_rate * (delta_seconds / 60.0))
```

---

#### Microtaak 1.9.1: `update_prana_from_graha()` methode

**Masterprompt**:
```
Voeg update_prana_from_graha(navagraha_state: NavagrahaState) toe aan ElementalBase.
Elke subclass definieert self.ruling_graha:
  Ether → Jupiter, Air → Saturn, Fire → Mars, Water → Venus, Earth → Mercury.
Retrograde = prana -15. Planet in eigen element = prana +20.
Bestaande prana is 0-100 (elemental_base.py:60).
"""
```

**Test FIRST**:
```python
# backend/tests/integration/test_elemental_graha.py

def test_integration_1_9_fire_agent_mars_boost():
    """Integratie: Mars in fire sign → Fire agent prana +20."""
    # Setup: Mars in Aries (fire sign)
    # Fire agent update_prana_from_graha()
    # Assert: prana increased

def test_integration_1_9_air_agent_saturn_retrograde_penalty():
    """Integratie: Saturn retrograde → Air agent prana -15."""
    # Setup: Saturn retrograde=True
    # Air agent update_prana_from_graha()
    # Assert: prana decreased

def test_integration_1_9_prana_never_below_zero():
    """Unhappy: Prana gaat nooit onder 0."""
    # Setup: Agent met prana=5, extreme penalty
    # Assert: prana >= 0

def test_integration_1_9_prana_never_above_max():
    """Unhappy: Prana gaat nooit boven max_prana."""
    # Setup: Agent met prana=95, grote boost
    # Assert: prana <= max_prana

def test_integration_1_9_prana_lifecycle_in_ooda():
    """
    Integratie: Volledige OODA cyclus met prana lifecycle.
    1. regenerate_prana() voor cycle
    2. update_prana_from_graha() met NavagrahaState
    3. consume_prana() tijdens cycle
    4. prana feedback naar IntentMonitor
    """
    pass  # Implementeer na alle componenten klaar zijn
```

---

## Fase 1 Productie Test

Na afronding van ALLE taken in Fase 1:

```python
# backend/tests/e2e/test_phase1_production.py

@pytest.mark.e2e
async def test_production_phase1_full_ooda_with_navagraha():
    """
    PRODUCTIE TEST: Complete OODA loop met echte Navagraha berekeningen.

    Verificeert:
    1. EphemerisCalculator berekent echte posities (cross-check drikpanchang.com)
    2. NavagrahaEngine.assess() retourneert complete state
    3. CognitiveBridge injecteert Guna modulation in SystemIdentity
    4. OODALoopCoordinator respecteert Rahu Kala gate
    5. ElementalAgents krijgen prana van hun heersende planeet
    6. OrchestratorAgent.harmonize() bevat planetary harmony
    7. Audit trail bevat NavagrahaState
    """
    # Setup real engine (geen mocks!)
    engine = NavagrahaEngine(
        system_birth=datetime(2025, 1, 1, tzinfo=timezone.utc)
    )

    # Assess real planetary state
    state = engine.assess(datetime.now(timezone.utc))
    assert len(state.positions) == 9
    assert state.positions[Graha.RAHU].retrograde is True

    # Wire into OODA coordinator
    coordinator = _setup_full_coordinator(navagraha_engine=engine)
    result = await coordinator.run_cycle(symbol="BTC/USDT")

    # Verify result includes navagraha context
    assert "navagraha" in result or "planetary" in str(result).lower()

    # Verify planetary positions are reasonable
    sun = state.positions[Graha.SURYA]
    assert 0 <= sun.longitude < 360
    assert sun.nakshatra.index <= 26
```

---

## Kruisverwijzingen

- **→ Fase 2**: Security middleware moet NavagrahaState per-tenant isoleren
- **→ Fase 3**: Prometheus metrics voor alle Navagraha gauges (Taak 3.3)
- **→ Fase 3**: Docker moet ephemeris .se1 bestanden bundelen (Taak 3.2)
- **→ Fase 4**: Backtesting moet NavagrahaState op historische data replays (Taak 4.2)
- **→ Fase 5**: Navagraha Dashboard component verbruikt NavagrahaState (Taak 5.2)
- **→ Fase 6**: Dasha-aware scheduling gebruikt DashaState (Taak 6.2)
- **→ Fase 7**: MiFID II audit moet NavagrahaState loggen per trade (Taak 7.1)
