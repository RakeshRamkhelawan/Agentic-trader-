from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, computed_field, field_validator


class PlanetName(str, Enum):
    SUN = "Sun"
    MOON = "Moon"
    MARS = "Mars"
    MERCURY = "Mercury"
    JUPITER = "Jupiter"
    VENUS = "Venus"
    SATURN = "Saturn"
    RAHU = "Rahu"
    KETU = "Ketu"


class GunaType(str, Enum):
    SATTVA = "sattva"
    RAJAS = "rajas"
    TAMAS = "tamas"


class PlanetState(BaseModel):
    name: PlanetName = Field(..., description="Planet identifier from Navagraha")
    longitude: float = Field(
        ..., ge=0.0, lt=360.0, description="Ecliptic longitude in degrees [0, 360)"
    )
    latitude: float = Field(
        ..., ge=-90.0, le=90.0, description="Ecliptic latitude in degrees [-90, 90]"
    )
    speed: float = Field(..., description="Daily motion in degrees per day")
    is_retrograde: bool = Field(
        ..., description="True if planet is in retrograde motion (speed < 0)"
    )
    distance_au: Optional[float] = Field(
        None, ge=0.0, description="Distance from Earth in Astronomical Units"
    )
    calculated_at: datetime = Field(..., description="UTC timestamp of calculation")

    @field_validator("is_retrograde")
    @classmethod
    def validate_retrograde(cls, v: bool, info) -> bool:
        name = info.data.get("name")
        speed = info.data.get("speed")

        if name == PlanetName.RAHU or name == PlanetName.KETU:
            if not v:
                raise ValueError(f"{name.value} must always be retrograde")
            if speed is not None and speed >= 0:
                raise ValueError(f"{name.value} speed must be negative (retrograde)")

        if speed is not None:
            computed_retro = speed < 0
            if v != computed_retro:
                raise ValueError(f"is_retrograde={v} inconsistent with speed={speed}")

        return v

    @computed_field
    @property
    def zodiac_sign(self) -> str:
        signs = [
            "Aries",
            "Taurus",
            "Gemini",
            "Cancer",
            "Leo",
            "Virgo",
            "Libra",
            "Scorpio",
            "Sagittarius",
            "Capricorn",
            "Aquarius",
            "Pisces",
        ]
        sign_index = int(self.longitude // 30)
        return signs[sign_index]

    @computed_field
    @property
    def nakshatra(self) -> str:
        nakshatras = [
            "Ashwini",
            "Bharani",
            "Krittika",
            "Rohini",
            "Mrigashira",
            "Ardra",
            "Punarvasu",
            "Pushya",
            "Ashlesha",
            "Magha",
            "Purva Phalguni",
            "Uttara Phalguni",
            "Hasta",
            "Chitra",
            "Swati",
            "Vishakha",
            "Anuradha",
            "Jyeshtha",
            "Mula",
            "Purva Ashadha",
            "Uttara Ashadha",
            "Shravana",
            "Dhanishta",
            "Shatabhisha",
            "Purva Bhadrapada",
            "Uttara Bhadrapada",
            "Revati",
        ]
        nakshatra_index = int((self.longitude % 360) / 13.333333333333334)
        return nakshatras[min(nakshatra_index, 26)]

    class Config:
        frozen = True


class GunaDistribution(BaseModel):
    sattva: float = Field(
        ..., ge=0.0, le=1.0, description="Sattva (harmony, wisdom) proportion [0, 1]"
    )
    rajas: float = Field(
        ..., ge=0.0, le=1.0, description="Rajas (activity, passion) proportion [0, 1]"
    )
    tamas: float = Field(
        ..., ge=0.0, le=1.0, description="Tamas (inertia, darkness) proportion [0, 1]"
    )
    calculated_at: datetime = Field(..., description="UTC timestamp of calculation")

    @field_validator("tamas")
    @classmethod
    def validate_sum_to_one(cls, v: float, info) -> float:
        sattva = info.data.get("sattva", 0.0)
        rajas = info.data.get("rajas", 0.0)
        total = sattva + rajas + v

        if not (0.9999 <= total <= 1.0001):
            raise ValueError(
                f"Guna distribution must sum to 1.0 (got {total:.6f}). "
                f"sattva={sattva}, rajas={rajas}, tamas={v}"
            )

        return v

    @computed_field
    @property
    def dominant_guna(self) -> GunaType:
        if self.sattva >= self.rajas and self.sattva >= self.tamas:
            return GunaType.SATTVA
        elif self.rajas >= self.tamas:
            return GunaType.RAJAS
        else:
            return GunaType.TAMAS

    @computed_field
    @property
    def balance_score(self) -> float:
        ideal = 1.0 / 3.0
        deviation = (
            abs(self.sattva - ideal) + abs(self.rajas - ideal) + abs(self.tamas - ideal)
        )
        return 1.0 - (deviation / 2.0)

    class Config:
        frozen = True


class AspectType(str, Enum):
    CONJUNCTION = "conjunction"
    OPPOSITION = "opposition"
    TRINE = "trine"
    SQUARE = "square"
    SEXTILE = "sextile"


class PlanetaryAspect(BaseModel):
    planet1: PlanetName = Field(..., description="First planet in aspect")
    planet2: PlanetName = Field(..., description="Second planet in aspect")
    aspect_type: AspectType = Field(..., description="Type of aspect")
    angle: float = Field(
        ..., ge=0.0, lt=360.0, description="Actual angle between planets"
    )
    orb: float = Field(
        ..., ge=0.0, description="Deviation from exact aspect in degrees"
    )
    is_applying: bool = Field(
        ..., description="True if planets are moving toward exact aspect"
    )
    strength: float = Field(
        ..., ge=0.0, le=1.0, description="Aspect strength [0, 1] based on orb"
    )

    class Config:
        frozen = True


class NavagrahaState(BaseModel):
    planets: Dict[PlanetName, PlanetState] = Field(
        ...,
        description="State of all 9 Grahas at calculation time",
        min_length=9,
        max_length=9,
    )
    guna_distribution: GunaDistribution = Field(
        ..., description="Current Guna modulation"
    )
    aspects: List[PlanetaryAspect] = Field(
        default_factory=list, description="Active planetary aspects"
    )
    rahu_kala_active: bool = Field(
        ..., description="True if currently in Rahu Kala period"
    )
    current_dasha: Optional[PlanetName] = Field(
        None, description="Current Mahadasha period lord"
    )
    calculated_at: datetime = Field(
        ..., description="UTC timestamp of state calculation"
    )
    location_lat: float = Field(..., ge=-90.0, le=90.0, description="Observer latitude")
    location_lon: float = Field(
        ..., ge=-180.0, le=180.0, description="Observer longitude"
    )

    @field_validator("planets")
    @classmethod
    def validate_nine_planets(
        cls, v: Dict[PlanetName, PlanetState]
    ) -> Dict[PlanetName, PlanetState]:
        if len(v) != 9:
            raise ValueError(f"Must have exactly 9 planets, got {len(v)}")

        required = set(PlanetName)
        present = set(v.keys())
        if required != present:
            missing = required - present
            extra = present - required
            raise ValueError(f"Invalid planet set. Missing: {missing}, Extra: {extra}")

        rahu = v.get(PlanetName.RAHU)
        ketu = v.get(PlanetName.KETU)
        if rahu and ketu:
            rahu_lon = rahu.longitude
            ketu_lon = ketu.longitude
            angle_diff = abs(rahu_lon - ketu_lon)
            if angle_diff > 180:
                angle_diff = 360 - angle_diff

            if not (179.0 <= angle_diff <= 181.0):
                raise ValueError(
                    f"Rahu-Ketu must be 180 degrees apart (±1 degree). "
                    f"Rahu={rahu_lon:.2f} degrees, Ketu={ketu_lon:.2f} degrees, diff={angle_diff:.2f} degrees"
                )

        return v

    @computed_field
    @property
    def trading_gate_open(self) -> bool:
        if self.rahu_kala_active:
            return False

        if self.guna_distribution.tamas > 0.6:
            return False

        return True

    @computed_field
    @property
    def consciousness_level(self) -> str:
        sattva = self.guna_distribution.sattva
        if sattva >= 0.6:
            return "Pure Awareness"
        elif sattva >= 0.4:
            return "Discriminative Intelligence"
        elif sattva >= 0.25:
            return "Active Manifestation"
        else:
            return "Material Density"

    class Config:
        frozen = True
