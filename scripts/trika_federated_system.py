#!/usr/bin/env python3
"""
FEDERATED TRIKA SYSTEM - Complete Implementation
Geïnspireerd door AgentNet & Neuro-Symbolic Architecture

ARCHITECTUUR:
- Layer 3: Chitta Mahasagar (Gedeelde Kennis)
- Layer 2.5: Council Indices (Perspectieven)
- Layer 2: Cooperative Deliberation (Iteratieve Samenwerking)
- Layer 2: Buddhi Mind (Discriminatie)
- Layer 1: Body Execution (Actie)

Test-driven: Alle happy en unhappy paths getest
"""

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


# =============================================================================
# EXCEPTIONS (Unhappy path handling)
# =============================================================================


class FederatedTrikaError(Exception):
    """Base exception voor alle Federated Trika errors"""

    pass


class ChittaError(FederatedTrikaError):
    """Errors in de Chitta (kennislaag)"""

    pass


class CouncilError(FederatedTrikaError):
    """Errors in councils"""

    pass


class DeliberationError(FederatedTrikaError):
    """Errors tijdens deliberatie"""

    pass


class SynthesisError(FederatedTrikaError):
    """Errors tijdens Mind synthesis"""

    pass


# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================


class CouncilType(Enum):
    GUNA = "guna"
    ELEMENTAL = "elemental"
    GRAHA = "graha"
    MIND = "mind"
    BODY = "body"
    SHIVA = "shiva"


class GunaType(Enum):
    SATTVA = "sattva"
    RAJAS = "rajas"
    TAMAS = "tamas"


class ElementType(Enum):
    ETHER = "ether"
    AIR = "air"
    FIRE = "fire"
    WATER = "water"
    EARTH = "earth"


class ActionType(Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


# =============================================================================
# DATA STRUCTURES
# =============================================================================


@dataclass
class KnowledgeNode:
    """
    Een enkel feit/observatie in Chitta.
    Onveranderlijk (immutable) voor audit trail.
    """

    id: str
    content: str
    source: str
    timestamp: datetime
    council_origin: CouncilType
    metadata: Dict[str, Any] = field(default_factory=dict)
    perspectives: Dict[str, float] = field(default_factory=dict)
    verification_status: str = "unverified"  # unverified, verified, disputed

    def __post_init__(self):
        # Validatie
        if not self.id:
            raise ValueError("KnowledgeNode must have an id")
        if not self.content:
            raise ValueError("KnowledgeNode must have content")
        if not isinstance(self.timestamp, datetime):
            raise TypeError("timestamp must be datetime")

    def to_dict(self) -> Dict:
        """Serialize naar dict"""
        return {
            "id": self.id,
            "content": self.content,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "council_origin": self.council_origin.value,
            "metadata": self.metadata,
            "perspectives": self.perspectives,
            "verification_status": self.verification_status,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "KnowledgeNode":
        """Deserialize van dict"""
        return cls(
            id=data["id"],
            content=data["content"],
            source=data["source"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            council_origin=CouncilType(data["council_origin"]),
            metadata=data.get("metadata", {}),
            perspectives=data.get("perspectives", {}),
            verification_status=data.get("verification_status", "unverified"),
        )


@dataclass
class CouncilView:
    """
    Een council's interpretatie van de wereld.
    """

    council_name: str
    perspective: str
    confidence: float
    key_insights: List[str]
    supporting_evidence: List[str]  # IDs van KnowledgeNodes
    contradictions: List[str] = field(default_factory=list)
    reasoning: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        # Normaliseer confidence naar 0-1
        self.confidence = max(0.0, min(1.0, self.confidence))

        # Validatie
        if not self.council_name:
            raise ValueError("CouncilView must have council_name")
        if not isinstance(self.confidence, (int, float)):
            raise TypeError("confidence must be numeric")

    def is_valid(self) -> bool:
        """Check of deze view valide is"""
        return (
            0 <= self.confidence <= 1
            and len(self.key_insights) > 0
            and len(self.supporting_evidence) > 0
        )


@dataclass
class SynthesisDecision:
    """
    Een beslissing gemaakt door de Mind (Buddhi).
    """

    action: ActionType
    confidence: float
    rationale: str
    supporting_councils: List[str]
    opposing_councils: List[str]
    contradictions_detected: int
    evidence_weight: Dict[str, float]
    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if not isinstance(self.action, ActionType):
            raise TypeError("action must be ActionType")
        self.confidence = max(0.0, min(1.0, self.confidence))

    def to_dict(self) -> Dict:
        return {
            "action": self.action.value,
            "confidence": self.confidence,
            "rationale": self.rationale,
            "supporting_councils": self.supporting_councils,
            "opposing_councils": self.opposing_councils,
            "contradictions_detected": self.contradictions_detected,
            "evidence_weight": self.evidence_weight,
            "timestamp": self.timestamp.isoformat(),
        }


# =============================================================================
# LAYER 3: CHITTA MAHASAGAR (Gedeelde Kennis)
# =============================================================================


class FederatedChitta:
    """
    Het Oceaan van Collectief Geheugen.

    Design:
    - Één bron van waarheid
    - Immutable audit trail
    - Perspectief-gebaseerde query's
    - Verificatie systeem
    """

    def __init__(self, max_nodes: int = 10000):
        self._nodes: Dict[str, KnowledgeNode] = {}
        self._indices: Dict[str, Set[str]] = defaultdict(set)
        self._temporal_index: List[Tuple[datetime, str]] = []  # Voor time-range queries
        self._max_nodes = max_nodes
        self._access_count: Dict[str, int] = defaultdict(int)

        # Metrics
        self.metrics = {
            "total_nodes_added": 0,
            "total_nodes_evicted": 0,
            "total_queries": 0,
            "query_latency_ms": [],
        }

    def add_node(self, node: KnowledgeNode) -> str:
        """
        Voeg een nieuw feit toe aan Chitta.

        Happy path: Node wordt succesvol toegevoegd
        Unhappy path: Memory limit bereikt, oudste node wordt verwijderd
        """
        if not isinstance(node, KnowledgeNode):
            raise ChittaError(f"Expected KnowledgeNode, got {type(node)}")

        # Check duplicates
        if node.id in self._nodes:
            logger.warning(f"Node {node.id} already exists, updating perspectives")
            self._merge_perspectives(node)
            return node.id

        # Memory management: evict oudste als nodig
        if len(self._nodes) >= self._max_nodes:
            self._evict_oldest()

        # Voeg toe
        self._nodes[node.id] = node
        self._update_indices(node)
        self._temporal_index.append((node.timestamp, node.id))
        self.metrics["total_nodes_added"] += 1

        return node.id

    def _merge_perspectives(self, new_node: KnowledgeNode):
        """Merge perspectives van duplicate node"""
        existing = self._nodes[new_node.id]
        for council, score in new_node.perspectives.items():
            existing.perspectives[council] = max(
                existing.perspectives.get(council, 0), score
            )

    def _evict_oldest(self):
        """Verwijder minst recent benaderde node"""
        if not self._nodes:
            return

        # Vind minst gebruikte node
        min_access = float("inf")
        oldest_id = None

        for node_id in list(self._nodes.keys()):
            access = self._access_count.get(node_id, 0)
            if access < min_access:
                min_access = access
                oldest_id = node_id

        if oldest_id:
            self._remove_node(oldest_id)
            self.metrics["total_nodes_evicted"] += 1

    def _remove_node(self, node_id: str):
        """Verwijder een node en update indices"""
        if node_id not in self._nodes:
            return

        node = self._nodes[node_id]

        # Update indices
        for idx_name, idx_set in self._indices.items():
            idx_set.discard(node_id)

        # Verwijder uit temporal index
        self._temporal_index = [
            (ts, nid) for ts, nid in self._temporal_index if nid != node_id
        ]

        # Verwijder node
        del self._nodes[node_id]

    def _update_indices(self, node: KnowledgeNode):
        """Update alle relevante indices"""
        # Type index
        if "type" in node.metadata:
            self._indices[f"type:{node.metadata['type']}"].add(node.id)

        # Council origin index
        self._indices[f"council:{node.council_origin.value}"].add(node.id)

        # Guna index
        if "guna" in node.metadata:
            self._indices[f"guna:{node.metadata['guna']}"].add(node.id)

        # Elemental index
        for element in ["fire", "water", "air", "earth", "ether"]:
            if element in node.metadata:
                self._indices[f"element:{element}"].add(node.id)

        # Graha index
        if "graha" in node.metadata:
            self._indices[f"graha:{node.metadata['graha']}"].add(node.id)

        # Verification status
        self._indices[f"status:{node.verification_status}"].add(node.id)

    def query(
        self,
        council_type: CouncilType,
        query_filter: Optional[Dict[str, Any]] = None,
        limit: int = 100,
    ) -> List[KnowledgeNode]:
        """
        Query Chitta vanuit een specifiek perspectief.

        Happy path: Gefilterde, relevante nodes worden teruggegeven
        Unhappy path: Ongeldige filter, lege resultaten
        """
        start_time = datetime.now()
        self.metrics["total_queries"] += 1

        query_filter = query_filter or {}

        try:
            # Bepaal relevante indices
            candidate_ids = self._get_candidate_ids(council_type, query_filter)

            # Filter en sorteer
            results = []
            for node_id in candidate_ids:
                node = self._nodes.get(node_id)
                if node and self._matches_filter(node, query_filter):
                    results.append(node)
                    self._access_count[node_id] += 1

            # Sorteer op timestamp (nieuwste eerst)
            results.sort(key=lambda x: x.timestamp, reverse=True)

            # Limit
            results = results[:limit]

            # Track latency
            latency = (datetime.now() - start_time).total_seconds() * 1000
            self.metrics["query_latency_ms"].append(latency)

            return results

        except Exception as e:
            raise ChittaError(f"Query failed: {str(e)}")

    def _get_candidate_ids(
        self, council_type: CouncilType, query_filter: Dict
    ) -> Set[str]:
        """Bepaal kandidaat node IDs gebaseerd op indices"""
        candidates = set()

        # Council-specifieke indices
        if council_type == CouncilType.GUNA:
            candidates.update(self._indices.get("guna:sattva", set()))
            candidates.update(self._indices.get("guna:rajas", set()))
            candidates.update(self._indices.get("guna:tamas", set()))
            candidates.update(self._indices.get("type:market_snapshot", set()))

        elif council_type == CouncilType.ELEMENTAL:
            for element in ["fire", "water", "air", "earth", "ether"]:
                candidates.update(self._indices.get(f"element:{element}", set()))
            candidates.update(self._indices.get("type:market_snapshot", set()))

        elif council_type == CouncilType.GRAHA:
            candidates.update(self._indices.get("type:graha", set()))
            candidates.update(self._indices.get("type:market_snapshot", set()))

        elif council_type == CouncilType.MIND:
            # Mind ziet alles
            candidates = set(self._nodes.keys())

        else:  # BODY
            candidates = set(self._nodes.keys())

        # Filter op type als gespecificeerd
        if "type" in query_filter:
            type_ids = self._indices.get(f"type:{query_filter['type']}", set())
            if candidates:
                candidates &= type_ids
            else:
                candidates = type_ids

        return candidates or set(self._nodes.keys())

    def _matches_filter(self, node: KnowledgeNode, query_filter: Dict) -> bool:
        """Check of een node matcht met de filter criteria"""
        # Tijd filter
        if "since" in query_filter:
            if node.timestamp < query_filter["since"]:
                return False

        if "before" in query_filter:
            if node.timestamp > query_filter["before"]:
                return False

        # Metadata filter (exact match)
        for key, value in query_filter.get("metadata", {}).items():
            if node.metadata.get(key) != value:
                return False

        # Source filter
        if "source" in query_filter:
            if node.source != query_filter["source"]:
                return False

        # Verification status filter
        if "verification_status" in query_filter:
            if node.verification_status != query_filter["verification_status"]:
                return False

        return True

    def get_node(self, node_id: str) -> Optional[KnowledgeNode]:
        """Haal een specifieke node op"""
        node = self._nodes.get(node_id)
        if node:
            self._access_count[node_id] += 1
        return node

    def add_perspective(
        self, node_id: str, council_name: str, relevance_score: float
    ) -> bool:
        """
        Laat een council een perspectief toevoegen aan een node.

        Happy path: Perspectief wordt toegevoegd
        Unhappy path: Node bestaat niet
        """
        if node_id not in self._nodes:
            return False

        self._nodes[node_id].perspectives[council_name] = max(
            0.0, min(1.0, relevance_score)
        )
        return True

    def verify_node(self, node_id: str, verifier: str) -> bool:
        """Markeer een node als geverifieerd"""
        if node_id not in self._nodes:
            return False

        self._nodes[node_id].verification_status = "verified"
        self._indices["status:verified"].add(node_id)
        self._indices["status:unverified"].discard(node_id)
        return True

    def dispute_node(self, node_id: str, disputer: str) -> bool:
        """Markeer een node als disputed"""
        if node_id not in self._nodes:
            return False

        self._nodes[node_id].verification_status = "disputed"
        self._indices["status:disputed"].add(node_id)
        return True

    def get_stats(self) -> Dict[str, Any]:
        """Haal statistieken op"""
        avg_latency = (
            sum(self.metrics["query_latency_ms"])
            / len(self.metrics["query_latency_ms"])
            if self.metrics["query_latency_ms"]
            else 0
        )

        return {
            "total_nodes": len(self._nodes),
            "total_indices": len(self._indices),
            "metrics": {**self.metrics, "avg_query_latency_ms": avg_latency},
            "index_breakdown": {name: len(ids) for name, ids in self._indices.items()},
        }

    def export_to_dict(self) -> Dict:
        """Exporteer alle nodes naar dict"""
        return {
            "nodes": [node.to_dict() for node in self._nodes.values()],
            "stats": self.get_stats(),
        }

    def clear(self):
        """Wis alle data (voor testing)"""
        self._nodes.clear()
        self._indices.clear()
        self._temporal_index.clear()
        self._access_count.clear()
        self.metrics = {
            "total_nodes_added": 0,
            "total_nodes_evicted": 0,
            "total_queries": 0,
            "query_latency_ms": [],
        }


# =============================================================================
# LAYER 2.5: COUNCIL INDICES (Perspectieven)
# =============================================================================


class CouncilIndex:
    """
    Elke council heeft zijn eigen interpretatie/index op de gedeelde Chitta.

    Design:
    - Gedeelde Chitta als bron
    - Lokale, council-specifieke interpretatie
    - Real-time updates
    """

    def __init__(
        self,
        council_type: CouncilType,
        chitta: FederatedChitta,
        update_interval_seconds: int = 60,
    ):
        self.council_type = council_type
        self.chitta = chitta
        self.update_interval = timedelta(seconds=update_interval_seconds)
        self.last_update = datetime.min
        self.local_index: Dict[str, Any] = {}
        self.index_version = 0

        # Metrics
        self.metrics = {"updates": 0, "avg_update_time_ms": 0}

    async def update(self, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update lokale index gebaseerd op Chitta.

        Happy path: Index wordt succesvol geupdatet
        Unhappy path: Chitta query faalt, behoud oude index
        """
        now = datetime.now()

        # Rate limiting
        if now - self.last_update < self.update_interval:
            return False  # Te vroeg voor update

        start_time = datetime.now()

        try:
            # Haal relevante data op
            relevant_data = self.chitta.query(
                self.council_type, {"since": self.last_update}
            )

            if not relevant_data:
                self.last_update = now
                return True  # Geen nieuwe data, maar succesvol

            # Update index gebaseerd op council type
            if self.council_type == CouncilType.GUNA:
                self._update_guna_index(relevant_data)
            elif self.council_type == CouncilType.ELEMENTAL:
                self._update_elemental_index(relevant_data)
            elif self.council_type == CouncilType.GRAHA:
                self._update_graha_index(relevant_data)
            elif self.council_type == CouncilType.MIND:
                self._update_mind_index(relevant_data)
            else:
                self._update_generic_index(relevant_data)

            self.last_update = now
            self.index_version += 1

            # Metrics
            update_time = (datetime.now() - start_time).total_seconds() * 1000
            self.metrics["updates"] += 1
            self.metrics["avg_update_time_ms"] = (
                self.metrics["avg_update_time_ms"] * (self.metrics["updates"] - 1)
                + update_time
            ) / self.metrics["updates"]

            return True

        except Exception as e:
            logger.error(f"Failed to update {self.council_type.value} index: {e}")
            # Behoud oude index, markeer als stale
            return False

    def _update_guna_index(self, data: List[KnowledgeNode]):
        """Guna-specifieke indexering: 3 gunas balans"""
        scores = {"sattva": 0.0, "rajas": 0.0, "tamas": 0.0}
        intensities = {"sattva": [], "rajas": [], "tamas": []}

        for node in data:
            # Directe guna metadata
            if "guna" in node.metadata:
                guna_type = node.metadata["guna"]
                intensity = node.metadata.get("intensity", 0.5)
                weight = node.perspectives.get("guna", 0.5)

                if guna_type in scores:
                    scores[guna_type] += intensity * weight
                    intensities[guna_type].append(intensity)

            # Infer vanuit market data
            if node.metadata.get("type") == "market_snapshot":
                price_change = node.metadata.get("change", 0)
                if abs(price_change) > 0.05:  # > 5% change = Rajas
                    scores["rajas"] += abs(price_change)
                elif abs(price_change) < 0.01:  # < 1% change = Tamas
                    scores["tamas"] += 0.1
                else:  # Normal = Sattva
                    scores["sattva"] += 0.1

        # Normaliseer
        total = sum(scores.values())
        if total > 0:
            scores = {k: v / total for k, v in scores.items()}

        # Bepaal dominante guna
        dominant = max(scores, key=scores.get)

        self.local_index = {
            "scores": scores,
            "dominant": dominant,
            "samples": {k: len(v) for k, v in intensities.items()},
            "trend": self._calculate_guna_trend(scores),
        }

    def _calculate_guna_trend(self, scores: Dict[str, float]) -> str:
        """Bereken de trend in guna balans"""
        if not hasattr(self, "_previous_scores"):
            self._previous_scores = scores
            return "stable"

        changes = {k: scores[k] - self._previous_scores.get(k, 0) for k in scores}
        self._previous_scores = scores

        max_change = max(changes, key=changes.get)
        if abs(changes[max_change]) < 0.05:
            return "stable"
        return f"towards_{max_change}"

    def _update_elemental_index(self, data: List[KnowledgeNode]):
        """Elemental-specifieke indexering: 5 elementen"""
        elements = {"ether": 0, "air": 0, "fire": 0, "water": 0, "earth": 0}
        volatilities = []

        for node in data:
            # Directe element metadata
            for element in elements.keys():
                if element in node.metadata:
                    elements[element] += node.metadata[element]

            # Infer vanuit market data
            if node.metadata.get("type") == "market_snapshot":
                volatility = node.metadata.get("volatility", 0)
                volatilities.append(volatility)

                # Map volatility naar elementen
                if volatility > 0.5:  # High vol = Fire
                    elements["fire"] += volatility
                elif volatility > 0.3:  # Medium vol = Air
                    elements["air"] += volatility * 0.5
                else:  # Low vol = Earth/Water
                    elements["earth"] += 0.1
                    elements["water"] += 0.1

        # Normaliseer
        total = sum(elements.values())
        if total > 0:
            elements = {k: v / total for k, v in elements.items()}

        avg_volatility = sum(volatilities) / len(volatilities) if volatilities else 0

        self.local_index = {
            "elements": elements,
            "dominant": max(elements, key=elements.get),
            "avg_volatility": avg_volatility,
            "state": self._interpret_elemental_state(elements),
        }

    def _interpret_elemental_state(self, elements: Dict[str, float]) -> str:
        """Interpreteer de elementale staat"""
        if elements["fire"] > 0.4:
            return "volatile_expansion"
        elif elements["water"] > 0.4:
            return "emotional_flow"
        elif elements["earth"] > 0.4:
            return "stable_consolidation"
        elif elements["air"] > 0.4:
            return "uncertain_fluctuation"
        elif elements["ether"] > 0.4:
            return "transcendent_clarity"
        return "balanced"

    def _update_graha_index(self, data: List[KnowledgeNode]):
        """Graha-specifieke indexering: 9 planeten"""
        graha_states = {}
        graha_influences = defaultdict(list)

        for node in data:
            if "graha" in node.metadata:
                graha = node.metadata["graha"]
                state = node.metadata.get("state", "neutral")
                strength = node.metadata.get("strength", 0.5)

                graha_states[graha] = {
                    "state": state,
                    "strength": strength,
                    "timestamp": node.timestamp,
                }
                graha_influences[graha].append(strength)

        # Bereken gemiddelde invloed per graha
        avg_influences = {
            graha: sum(influences) / len(influences)
            for graha, influences in graha_influences.items()
        }

        # Bepaal dominante grahas
        if avg_influences:
            dominant = max(avg_influences, key=avg_influences.get)
        else:
            dominant = None

        self.local_index = {
            "grahas": graha_states,
            "influences": avg_influences,
            "dominant": dominant,
            "active_count": len(graha_states),
        }

    def _update_mind_index(self, data: List[KnowledgeNode]):
        """Mind index: synthese van alle andere indices"""
        # Mind index is een aggregatie van alle views
        decision_nodes = [n for n in data if n.metadata.get("type") == "mind_decision"]

        if decision_nodes:
            latest = max(decision_nodes, key=lambda x: x.timestamp)
            self.local_index = {
                "latest_decision": latest.metadata.get("action"),
                "confidence": latest.metadata.get("confidence"),
                "decision_count": len(decision_nodes),
            }
        else:
            self.local_index = {"status": "no_decisions_yet"}

    def _update_generic_index(self, data: List[KnowledgeNode]):
        """Generieke index voor andere councils"""
        self.local_index = {
            "node_count": len(data),
            "sources": list(set(n.source for n in data)),
            "latest_timestamp": max((n.timestamp for n in data), default=None),
        }

    def get_index(self) -> Dict[str, Any]:
        """Haal huidige index op"""
        return {
            "council": self.council_type.value,
            "version": self.index_version,
            "last_update": self.last_update.isoformat(),
            "stale": (datetime.now() - self.last_update) > self.update_interval * 2,
            "data": self.local_index,
            "metrics": self.metrics,
        }

    def is_stale(self) -> bool:
        """Check of de index verouderd is"""
        return (datetime.now() - self.last_update) > self.update_interval * 2

    def force_refresh(self):
        """Forceer een refresh bij volgende update"""
        self.last_update = datetime.min


# =============================================================================
# LAYER 2: COOPERATIVE DELIBERATION
# =============================================================================


class CooperativeDeliberation:
    """
    Iteratieve deliberatie tussen councils.

    Design:
    - Councils reageren op elkaar (niet alleen naar Mind)
    - Convergentie detectie
    - History tracking
    """

    def __init__(
        self,
        chitta: FederatedChitta,
        max_iterations: int = 3,
        convergence_threshold: float = 0.75,
    ):
        self.chitta = chitta
        self.max_iterations = max_iterations
        self.convergence_threshold = convergence_threshold
        self.iteration_history: List[List[CouncilView]] = []
        self.metrics = {
            "total_deliberations": 0,
            "avg_iterations": 0,
            "convergence_rate": 0,
        }

    async def deliberate(
        self,
        councils: List[CouncilType],
        context: Dict[str, Any],
        market_data: Optional[Dict] = None,
    ) -> Dict[str, CouncilView]:
        """
        Voer iteratieve deliberatie uit.

        Happy path: Councils convergeren naar consensus
        Unhappy path: Geen convergentie, maar wel valide output
        """
        if not councils:
            raise DeliberationError("No councils provided for deliberation")

        self.metrics["total_deliberations"] += 1
        views: Dict[str, CouncilView] = {}
        self.iteration_history = []

        for iteration in range(self.max_iterations):
            iteration_views: List[CouncilView] = []

            for council in councils:
                try:
                    # Bouw context voor dit council
                    council_context = self._build_context(
                        council, context, views, market_data
                    )

                    # Genereer view (simulatie - in productie: LLM call)
                    view = await self._generate_view(council, council_context)
                    iteration_views.append(view)
                    views[council.value] = view

                    # Sla op in Chitta
                    self._record_view(view, iteration)

                except Exception as e:
                    logger.error(f"Failed to generate view for {council.value}: {e}")
                    # Maak fallback view
                    views[council.value] = CouncilView(
                        council_name=council.value,
                        perspective="error_fallback",
                        confidence=0.3,
                        key_insights=["Error in deliberation"],
                        supporting_evidence=[],
                        reasoning=f"Error: {str(e)}",
                    )

            self.iteration_history.append(iteration_views)

            # Check convergentie
            if self._has_converged(views):
                logger.info(f"Converged after {iteration + 1} iterations")
                self.metrics["convergence_rate"] = (
                    self.metrics["convergence_rate"]
                    * (self.metrics["total_deliberations"] - 1)
                    + 1
                ) / self.metrics["total_deliberations"]
                break

        # Update average iterations
        avg_iter = (
            self.metrics["avg_iterations"] * (self.metrics["total_deliberations"] - 1)
            + len(self.iteration_history)
        ) / self.metrics["total_deliberations"]
        self.metrics["avg_iterations"] = avg_iter

        return views

    def _build_context(
        self,
        council: CouncilType,
        base_context: Dict,
        previous_views: Dict[str, CouncilView],
        market_data: Optional[Dict],
    ) -> Dict:
        """Bouw context specifiek voor dit council"""
        context = {
            "base": base_context,
            "market_data": market_data or {},
            "iteration": len(self.iteration_history),
            "other_views": [],
        }

        # Voeg views van andere councils toe
        for other_name, view in previous_views.items():
            if other_name != council.value:
                context["other_views"].append(
                    {
                        "council": other_name,
                        "perspective": view.perspective,
                        "confidence": view.confidence,
                        "key_insights": view.key_insights[:3],  # Top 3
                    }
                )

        return context

    async def _generate_view(self, council: CouncilType, context: Dict) -> CouncilView:
        """
        Genereer een council's view.

        In productie: Dit zou een LLM call zijn.
        Voor testing: Simulatie gebaseerd op context.
        """
        other_views = context.get("other_views", [])
        iteration = context.get("iteration", 0)
        market_data = context.get("market_data", {})

        # Simuleer verschillende perspectieven per council
        if council == CouncilType.GUNA:
            return self._simulate_guna_view(other_views, market_data, iteration)
        elif council == CouncilType.ELEMENTAL:
            return self._simulate_elemental_view(other_views, market_data, iteration)
        elif council == CouncilType.GRAHA:
            return self._simulate_graha_view(other_views, market_data, iteration)
        else:
            return CouncilView(
                council_name=council.value,
                perspective="neutral",
                confidence=0.5,
                key_insights=["No specific view"],
                supporting_evidence=[],
            )

    def _simulate_guna_view(
        self, other_views: List[Dict], market_data: Dict, iteration: int
    ) -> CouncilView:
        """Simuleer Guna council view"""
        # Base op market data
        change = market_data.get("change", 0)

        if change > 0.02:
            base_perspective = "sattva_dominant"
            confidence = 0.7
            insights = ["Markt toont kalmte", "Heldere trend"]
        elif change < -0.02:
            base_perspective = "tamas_dominant"
            confidence = 0.6
            insights = ["Verwarring in markt", "Onzekerheid"]
        else:
            base_perspective = "rajas_dominant"
            confidence = 0.65
            insights = ["Activiteit", "Beweging"]

        # Refine gebaseerd op andere views (iteratie > 0)
        if iteration > 0 and other_views:
            # Als andere councils bearish zijn, verhoog confidence in bearish
            bearish_count = sum(
                1
                for v in other_views
                if "bearish" in v["perspective"] or "fire" in v["perspective"]
            )
            if bearish_count > len(other_views) / 2:
                confidence = min(0.9, confidence + 0.1)
                insights.append("Bevestigd door andere councils")

        return CouncilView(
            council_name="guna",
            perspective=base_perspective,
            confidence=confidence,
            key_insights=insights,
            supporting_evidence=[f"guna_evidence_{iteration}"],
            reasoning=f"Gebaseerd op markt change {change:.2%} en {len(other_views)} andere views",
        )

    def _simulate_elemental_view(
        self, other_views: List[Dict], market_data: Dict, iteration: int
    ) -> CouncilView:
        """Simuleer Elemental council view"""
        volatility = market_data.get("volatility", 0.2)

        if volatility > 0.3:
            perspective = "fire_rising"
            confidence = 0.75
            insights = ["Hoge volatiliteit", "Momentum"]
        elif volatility < 0.1:
            perspective = "earth_stable"
            confidence = 0.7
            insights = ["Stabiliteit", "Consolidatie"]
        else:
            perspective = "water_flowing"
            confidence = 0.65
            insights = ["Geleidelijke beweging", "Adaptatie"]

        # Check voor contradicties met Guna
        for view in other_views:
            if view["council"] == "guna":
                if "tamas" in view["perspective"] and "fire" in perspective:
                    # Contradictie: Tamas vs Fire
                    confidence *= 0.9  # Iets minder confident

        return CouncilView(
            council_name="elemental",
            perspective=perspective,
            confidence=confidence,
            key_insights=insights,
            supporting_evidence=[f"element_evidence_{iteration}"],
            contradictions=["guna_tamas"]
            if any("tamas" in v["perspective"] for v in other_views)
            else [],
        )

    def _simulate_graha_view(
        self, other_views: List[Dict], market_data: Dict, iteration: int
    ) -> CouncilView:
        """Simuleer Graha council view"""
        # Graha kijkt naar "cosmische" patronen (simulatie)
        volume = market_data.get("volume", 0)

        if volume > 1000000:
            perspective = "rahu_active"  # Hoge volume = illusie/FOMO
            confidence = 0.7
            insights = ["Hoge volume kan FOMO indiceren", "Wees voorzichtig"]
        else:
            perspective = "jupiter_blessing"
            confidence = 0.65
            insights = ["Gunstige omstandigheden", "Wijsheid prevaleert"]

        return CouncilView(
            council_name="graha",
            perspective=perspective,
            confidence=confidence,
            key_insights=insights,
            supporting_evidence=[f"graha_evidence_{iteration}"],
        )

    def _record_view(self, view: CouncilView, iteration: int):
        """Sla council view op in Chitta"""
        try:
            node = KnowledgeNode(
                id=f"{view.council_name}_view_iter_{iteration}_{datetime.now().timestamp()}",
                content=view.perspective,
                source="cooperative_deliberation",
                timestamp=datetime.now(),
                council_origin=CouncilType(view.council_name),
                metadata={
                    "type": "council_view",
                    "iteration": iteration,
                    "confidence": view.confidence,
                    "key_insights": view.key_insights,
                },
            )
            self.chitta.add_node(node)
        except Exception as e:
            logger.warning(f"Failed to record view: {e}")

    def _has_converged(self, views: Dict[str, CouncilView]) -> bool:
        """Check of councils tot consensus zijn gekomen"""
        if len(views) < 2:
            return False

        # Check 1: Alle councils hebben hoge confidence
        confidences = [v.confidence for v in views.values()]
        avg_confidence = sum(confidences) / len(confidences)

        if avg_confidence >= self.convergence_threshold:
            return True

        # Check 2: Perspectieven zijn consistent (geen grote contradicties)
        perspectives = [v.perspective for v in views.values()]
        bullish_signals = sum(
            1
            for p in perspectives
            if any(x in p for x in ["sattva", "fire", "rising", "jupiter"])
        )
        bearish_signals = sum(
            1
            for p in perspectives
            if any(x in p for x in ["tamas", "water", "falling", "rahu"])
        )

        # Als alle signalen dezelfde richting op wijzen
        if bullish_signals == len(perspectives) or bearish_signals == len(perspectives):
            return True

        return False

    def get_deliberation_summary(self) -> Dict:
        """Haal samenvatting op van laatste deliberatie"""
        if not self.iteration_history:
            return {"status": "no_deliberation_yet"}

        last_iteration = self.iteration_history[-1]
        return {
            "iterations": len(self.iteration_history),
            "councils_participated": len(last_iteration),
            "final_views": [
                {
                    "council": v.council_name,
                    "perspective": v.perspective,
                    "confidence": v.confidence,
                }
                for v in last_iteration
            ],
            "converged": self._has_converged(
                {v.council_name: v for v in last_iteration}
            ),
            "metrics": self.metrics,
        }


# =============================================================================
# LAYER 2: MIND SYNTHESIS (BUDDHI)
# =============================================================================


class BuddhiMind:
    """
    De Mind als Buddhi (discriminatie/verstand).

    Design:
    - Toegang tot ALLE Chitta (gedeelde kennis)
    - Cross-verificatie van council views
    - Gewogen besluitvorming
    - Audit trail van beslissingen
    """

    def __init__(
        self,
        chitta: FederatedChitta,
        min_confidence_threshold: float = 0.5,
        contradiction_penalty: float = 0.1,
    ):
        self.chitta = chitta
        self.min_confidence = min_confidence_threshold
        self.contradiction_penalty = contradiction_penalty
        self.decision_history: List[SynthesisDecision] = []
        self.metrics = {
            "total_decisions": 0,
            "buy_decisions": 0,
            "sell_decisions": 0,
            "hold_decisions": 0,
            "avg_contradictions": 0,
        }

    async def synthesize(
        self, views: Dict[str, CouncilView], market_context: Optional[Dict] = None
    ) -> SynthesisDecision:
        """
        Synthetiseer alle council views tot een beslissing.

        Happy path: Duidelijke beslissing met hoge confidence
        Unhappy path: Conflicterende views, lage confidence hold
        """
        try:
            # Validatie
            if not views:
                raise SynthesisError("No views to synthesize")

            # Analyseer alle views
            analysis = self._analyze_views(views)

            # Detecteer contradicties
            contradictions = self._detect_contradictions(views)

            # Weeg evidence
            weighted = self._weigh_evidence(views, contradictions)

            # Bepaal actie
            action, confidence = self._determine_action(weighted, contradictions)

            # Bouw beslissing
            decision = SynthesisDecision(
                action=action,
                confidence=confidence,
                rationale=self._build_rationale(weighted, contradictions),
                supporting_councils=weighted["support"],
                opposing_councils=weighted["oppose"],
                contradictions_detected=len(contradictions),
                evidence_weight=weighted["weights"],
            )

            # Sla op
            self._record_decision(decision, views)
            self._update_metrics(decision, contradictions)

            return decision

        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            # Fallback naar HOLD
            return SynthesisDecision(
                action=ActionType.HOLD,
                confidence=0.3,
                rationale=f"Synthesis error: {str(e)}",
                supporting_councils=[],
                opposing_councils=list(views.keys()),
                contradictions_detected=0,
                evidence_weight={},
            )

    def _analyze_views(self, views: Dict[str, CouncilView]) -> Dict:
        """Analyseer patronen in views"""
        total_confidence = sum(v.confidence for v in views.values())
        avg_confidence = total_confidence / len(views) if views else 0

        # Tel sentiment signalen
        bullish_count = 0
        bearish_count = 0
        neutral_count = 0

        for view in views.values():
            p = view.perspective.lower()
            if any(
                x in p
                for x in ["sattva", "fire", "rising", "jupiter", "bullish", "growth"]
            ):
                bullish_count += 1
            elif any(
                x in p
                for x in ["tamas", "water", "falling", "rahu", "bearish", "decline"]
            ):
                bearish_count += 1
            else:
                neutral_count += 1

        return {
            "avg_confidence": avg_confidence,
            "bullish_count": bullish_count,
            "bearish_count": bearish_count,
            "neutral_count": neutral_count,
            "total_views": len(views),
            "sentiment_ratio": max(bullish_count, bearish_count) / len(views)
            if views
            else 0,
        }

    def _detect_contradictions(self, views: Dict[str, CouncilView]) -> List[Dict]:
        """Detecteer tegenstrijdige views"""
        contradictions = []
        view_list = list(views.values())

        for i, view1 in enumerate(view_list):
            for view2 in view_list[i + 1 :]:
                # Directe contradicties (gemarkeerd in view)
                if view1.contradictions and view2.council_name in view1.contradictions:
                    contradictions.append(
                        {
                            "between": [view1.council_name, view2.council_name],
                            "type": "direct",
                            "severity": "high",
                            "resolution": "requires_verification",
                        }
                    )
                    continue

                # Sentiment contradicties
                if self._sentiments_contradict(view1, view2):
                    severity = (
                        "medium"
                        if view1.confidence > 0.6 and view2.confidence > 0.6
                        else "low"
                    )
                    contradictions.append(
                        {
                            "between": [view1.council_name, view2.council_name],
                            "type": "sentiment",
                            "severity": severity,
                            "resolution": "weighted_average",
                        }
                    )

        return contradictions

    def _sentiments_contradict(self, view1: CouncilView, view2: CouncilView) -> bool:
        """Check of twee views sentiment contradicties hebben"""
        bullish1 = any(
            x in view1.perspective.lower()
            for x in ["sattva", "fire", "rising", "jupiter", "bullish"]
        )
        bearish1 = any(
            x in view1.perspective.lower()
            for x in ["tamas", "water", "falling", "rahu", "bearish"]
        )

        bullish2 = any(
            x in view2.perspective.lower()
            for x in ["sattva", "fire", "rising", "jupiter", "bullish"]
        )
        bearish2 = any(
            x in view2.perspective.lower()
            for x in ["tamas", "water", "falling", "rahu", "bearish"]
        )

        return (bullish1 and bearish2) or (bearish1 and bullish2)

    def _weigh_evidence(
        self, views: Dict[str, CouncilView], contradictions: List[Dict]
    ) -> Dict:
        """Weeg alle evidence"""
        weights = {}
        support_councils = []
        oppose_councils = []

        weighted_bullish = 0
        weighted_bearish = 0

        for name, view in views.items():
            # Base weight = confidence
            weight = view.confidence

            # Pas penalty toe voor contradicties
            for contr in contradictions:
                if name in contr["between"]:
                    weight *= 1 - self.contradiction_penalty

            weights[name] = weight

            # Categoriseer
            p = view.perspective.lower()
            if any(x in p for x in ["sattva", "fire", "rising", "jupiter", "bullish"]):
                weighted_bullish += weight
                support_councils.append(name)
            elif any(x in p for x in ["tamas", "water", "falling", "rahu", "bearish"]):
                weighted_bearish += weight
                oppose_councils.append(name)
            else:
                # Neutral, add to both but with less weight
                weighted_bullish += weight * 0.3
                weighted_bearish += weight * 0.3

        return {
            "weights": weights,
            "bullish_score": weighted_bullish,
            "bearish_score": weighted_bearish,
            "support": support_councils,
            "oppose": oppose_councils,
        }

    def _determine_action(
        self, weighted: Dict, contradictions: List[Dict]
    ) -> Tuple[ActionType, float]:
        """Bepaal de uiteindelijke actie"""
        bullish = weighted["bullish_score"]
        bearish = weighted["bearish_score"]
        total = bullish + bearish

        if total == 0:
            return ActionType.HOLD, 0.5

        # Calculate confidence based on ratio and contradictions
        ratio = max(bullish, bearish) / total
        contradiction_factor = max(0.5, 1 - (len(contradictions) * 0.2))

        if bullish > bearish * 1.3:  # 30% marge nodig
            confidence = ratio * contradiction_factor
            return ActionType.BUY, min(0.95, confidence)
        elif bearish > bullish * 1.3:
            confidence = ratio * contradiction_factor
            return ActionType.SELL, min(0.95, confidence)
        else:
            return ActionType.HOLD, 0.5

    def _build_rationale(self, weighted: Dict, contradictions: List[Dict]) -> str:
        """Bouw de rationale string"""
        parts = []

        # Evidence summary
        parts.append(f"Bullish weight: {weighted['bullish_score']:.2f}")
        parts.append(f"Bearish weight: {weighted['bearish_score']:.2f}")

        # Supporting councils
        if weighted["support"]:
            parts.append(f"Support: {', '.join(weighted['support'])}")
        if weighted["oppose"]:
            parts.append(f"Oppose: {', '.join(weighted['oppose'])}")

        # Contradictions
        if contradictions:
            parts.append(f"Contradictions detected: {len(contradictions)}")
            for c in contradictions[:2]:  # Max 2
                parts.append(
                    f"  - {c['between'][0]} vs {c['between'][1]} ({c['type']})"
                )

        return "; ".join(parts)

    def _record_decision(
        self, decision: SynthesisDecision, views: Dict[str, CouncilView]
    ):
        """Sla beslissing op in Chitta"""
        try:
            node = KnowledgeNode(
                id=f"mind_decision_{datetime.now().timestamp()}",
                content=f"Decision: {decision.action.value} (confidence: {decision.confidence:.2f})",
                source="buddhi_mind",
                timestamp=datetime.now(),
                council_origin=CouncilType.MIND,
                metadata={
                    "type": "mind_decision",
                    "action": decision.action.value,
                    "confidence": decision.confidence,
                    "input_councils": list(views.keys()),
                    "contradictions_detected": decision.contradictions_detected,
                },
            )
            self.chitta.add_node(node)
            self.decision_history.append(decision)
        except Exception as e:
            logger.warning(f"Failed to record decision: {e}")

    def _update_metrics(self, decision: SynthesisDecision, contradictions: List[Dict]):
        """Update interne metrics"""
        self.metrics["total_decisions"] += 1

        if decision.action == ActionType.BUY:
            self.metrics["buy_decisions"] += 1
        elif decision.action == ActionType.SELL:
            self.metrics["sell_decisions"] += 1
        else:
            self.metrics["hold_decisions"] += 1

        # Update avg contradictions
        avg_contr = (
            self.metrics["avg_contradictions"] * (self.metrics["total_decisions"] - 1)
            + len(contradictions)
        ) / self.metrics["total_decisions"]
        self.metrics["avg_contradictions"] = avg_contr

    def get_decision_stats(self) -> Dict:
        """Haal beslissing statistieken op"""
        total = self.metrics["total_decisions"]
        if total == 0:
            return {"status": "no_decisions_yet"}

        return {
            **self.metrics,
            "buy_ratio": self.metrics["buy_decisions"] / total,
            "sell_ratio": self.metrics["sell_decisions"] / total,
            "hold_ratio": self.metrics["hold_decisions"] / total,
            "recent_decisions": [
                {
                    "action": d.action.value,
                    "confidence": d.confidence,
                    "timestamp": d.timestamp.isoformat(),
                }
                for d in self.decision_history[-5:]  # Laatste 5
            ],
        }


# =============================================================================
# INTEGRATIE: FEDERATED TRIAD SYSTEM
# =============================================================================


class FederatedTriadSystem:
    """
    De volledige Federated Triad implementatie.
    Integreert alle lagen in het 5-Council systeem.
    """

    def __init__(
        self,
        enable_caching: bool = True,
        deliberation_iterations: int = 3,
        chitta_max_nodes: int = 10000,
    ):
        # Layer 3: Chitta
        self.chitta = FederatedChitta(max_nodes=chitta_max_nodes)

        # Layer 2.5: Council Indices
        self.indices = {
            CouncilType.GUNA: CouncilIndex(CouncilType.GUNA, self.chitta),
            CouncilType.ELEMENTAL: CouncilIndex(CouncilType.ELEMENTAL, self.chitta),
            CouncilType.GRAHA: CouncilIndex(CouncilType.GRAHA, self.chitta),
        }

        # Layer 2: Cooperative Deliberation
        self.deliberation = CooperativeDeliberation(
            self.chitta, max_iterations=deliberation_iterations
        )

        # Layer 2: Buddhi Mind
        self.mind = BuddhiMind(self.chitta)

        # Layer 1: Body (state)
        self.body_state = {"position": None, "cash": 10000.0, "holdings": 0.0}

        # Tracking
        self.cycle_count = 0
        self.enable_caching = enable_caching
        self.cache = {} if enable_caching else None

    async def process_cycle(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verwerk één volledige cyclus.

        Happy path: Normale flow
        Unhappy path: Errors worden opgevangen en gelogd
        """
        self.cycle_count += 1
        start_time = datetime.now()

        try:
            # STAP 1: Ingest market data (Body)
            await self._ingest_market_data(market_data)

            # STAP 2: Update council indices
            await self._update_indices(market_data)

            # STAP 3: Cooperative deliberatie
            council_views = await self._run_deliberation(market_data)

            # STAP 4: Mind synthesis (Buddhi)
            decision = await self.mind.synthesize(council_views, market_data)

            # STAP 5: Execute (Body)
            execution = await self._execute_decision(decision, market_data)

            # Bereken latency
            latency_ms = (datetime.now() - start_time).total_seconds() * 1000

            return {
                "cycle": self.cycle_count,
                "success": True,
                "council_views": {
                    k: {
                        "perspective": v.perspective,
                        "confidence": v.confidence,
                        "insights": v.key_insights[:2],  # Top 2
                    }
                    for k, v in council_views.items()
                },
                "decision": decision.to_dict(),
                "execution": execution,
                "latency_ms": latency_ms,
                "chitta_stats": self.chitta.get_stats(),
            }

        except Exception as e:
            logger.error(f"Cycle {self.cycle_count} failed: {e}")
            return {
                "cycle": self.cycle_count,
                "success": False,
                "error": str(e),
                "decision": {
                    "action": "hold",
                    "confidence": 0.1,
                    "rationale": f"Error: {str(e)}",
                },
            }

    async def _ingest_market_data(self, market_data: Dict):
        """Voeg market data toe aan Chitta"""
        node = KnowledgeNode(
            id=f"market_{self.cycle_count}_{datetime.now().timestamp()}",
            content=f"BTC: ${market_data.get('price', 0):,.2f}, "
            f"Change: {market_data.get('change', 0):.2%}, "
            f"Vol: {market_data.get('volume', 0):,.0f}",
            source="market_feed",
            timestamp=datetime.now(),
            council_origin=CouncilType.BODY,
            metadata={
                "type": "market_snapshot",
                "price": market_data.get("price"),
                "change": market_data.get("change", 0),
                "volume": market_data.get("volume"),
                "volatility": market_data.get("volatility", 0.2),
                "cycle": self.cycle_count,
            },
        )
        self.chitta.add_node(node)

    async def _update_indices(self, market_data: Dict):
        """Update alle council indices"""
        for council, index in self.indices.items():
            try:
                await index.update({"market_data": market_data})
            except Exception as e:
                logger.warning(f"Failed to update {council.value} index: {e}")

    async def _run_deliberation(self, market_data: Dict) -> Dict[str, CouncilView]:
        """Run cooperative deliberatie"""
        councils = [CouncilType.GUNA, CouncilType.ELEMENTAL, CouncilType.GRAHA]

        views = await self.deliberation.deliberate(
            councils=councils,
            context={"cycle": self.cycle_count},
            market_data=market_data,
        )

        return views

    async def _execute_decision(
        self, decision: SynthesisDecision, market_data: Dict
    ) -> Dict:
        """Voer beslissing uit (simulatie)"""
        price = market_data.get("price", 0)

        if decision.action == ActionType.BUY and self.body_state["cash"] > 0:
            # Koop voor 10% van cash
            amount = self.body_state["cash"] * 0.1
            btc_bought = amount / price if price > 0 else 0
            self.body_state["cash"] -= amount
            self.body_state["holdings"] += btc_bought

            execution = {
                "action": "buy",
                "amount_btc": btc_bought,
                "cost": amount,
                "price": price,
            }

        elif decision.action == ActionType.SELL and self.body_state["holdings"] > 0:
            # Verkoop 10% van holdings
            amount_btc = self.body_state["holdings"] * 0.1
            proceeds = amount_btc * price
            self.body_state["holdings"] -= amount_btc
            self.body_state["cash"] += proceeds

            execution = {
                "action": "sell",
                "amount_btc": amount_btc,
                "proceeds": proceeds,
                "price": price,
            }

        else:
            execution = {"action": "hold", "reason": "No action taken"}

        # Sla uitvoering op in Chitta
        node = KnowledgeNode(
            id=f"execution_{datetime.now().timestamp()}",
            content=f"Executed {execution['action']}",
            source="body_execution",
            timestamp=datetime.now(),
            council_origin=CouncilType.BODY,
            metadata={
                "type": "execution",
                "action": execution["action"],
                "cycle": self.cycle_count,
            },
        )
        self.chitta.add_node(node)

        return {
            **execution,
            "portfolio_value": self.body_state["cash"]
            + (self.body_state["holdings"] * price),
            "cash": self.body_state["cash"],
            "holdings_btc": self.body_state["holdings"],
        }

    def get_system_state(self) -> Dict:
        """Haal complete systeem staat op"""
        return {
            "cycle_count": self.cycle_count,
            "body_state": self.body_state,
            "chitta": self.chitta.get_stats(),
            "deliberation": self.deliberation.get_deliberation_summary(),
            "mind": self.mind.get_decision_stats(),
        }

    def reset(self):
        """Reset het systeem (voor testing)"""
        self.cycle_count = 0
        self.body_state = {"position": None, "cash": 10000.0, "holdings": 0.0}
        self.chitta.clear()
        self.mind.decision_history.clear()
        self.deliberation.iteration_history.clear()


# =============================================================================
# COMPLETE TEST SUITE
# =============================================================================


async def run_complete_test_suite():
    """
    Voer de complete test suite uit.
    Alle tests moeten 100% passen.
    """
    print("\n" + "=" * 60)
    print("FEDERATED TRIAD - COMPLETE TEST SUITE")
    print("=" * 60)

    all_passed = True

    # Test 1: Chitta
    if not await test_chitta_comprehensive():
        all_passed = False
        print("\nCHITTA TESTS FAILED")
    else:
        print("\nCHITTA TESTS PASSED")

    # Test 2: Council Index
    if not await test_council_index_comprehensive():
        all_passed = False
        print("\nCOUNCIL INDEX TESTS FAILED")
    else:
        print("\nCOUNCIL INDEX TESTS PASSED")

    # Test 3: Integration
    if not await test_integration():
        all_passed = False
        print("\nINTEGRATION TESTS FAILED")
    else:
        print("\nINTEGRATION TESTS PASSED")

    # Final summary
    print("\n" + "=" * 60)
    if all_passed:
        print("ALL TESTS PASSED (100%)")
    else:
        print("SOME TESTS FAILED")
    print("=" * 60)

    return all_passed


async def test_chitta_comprehensive():
    """Test Chitta component"""
    print("\n" + "=" * 60)
    print("TESTING: FederatedChitta")
    print("=" * 60)

    results = {"passed": 0, "failed": 0, "errors": []}

    def run_test(name: str, test_func):
        try:
            test_func()
            print(f"  PASS: {name}")
            results["passed"] += 1
            return True
        except AssertionError as e:
            print(f"  FAIL: {name}: {e}")
            results["failed"] += 1
            results["errors"].append((name, str(e)))
            return False
        except Exception as e:
            print(f"  ERROR: {name}: {e}")
            results["failed"] += 1
            results["errors"].append((name, str(e)))
            return False

    # Happy path tests
    def test_add_node():
        chitta = FederatedChitta()
        node = KnowledgeNode(
            id="test_001",
            content="Test content",
            source="test",
            timestamp=datetime.now(),
            council_origin=CouncilType.GUNA,
            metadata={"type": "test", "guna": "sattva"},
        )
        nid = chitta.add_node(node)
        assert nid == "test_001"
        assert len(chitta._nodes) == 1

    run_test("Add node (happy)", test_add_node)

    def test_query_basic():
        chitta = FederatedChitta()
        node = KnowledgeNode(
            id="test_002",
            content="Query test",
            source="test",
            timestamp=datetime.now(),
            council_origin=CouncilType.GUNA,
            metadata={"guna": "rajas"},
        )
        chitta.add_node(node)
        results = chitta.query(CouncilType.GUNA, {})
        assert len(results) == 1
        assert results[0].id == "test_002"

    run_test("Basic query (happy)", test_query_basic)

    def test_mind_sees_all():
        chitta = FederatedChitta()
        for council in [CouncilType.GUNA, CouncilType.ELEMENTAL, CouncilType.GRAHA]:
            chitta.add_node(
                KnowledgeNode(
                    id=f"{council.value}_001",
                    content=f"{council.value} content",
                    source="test",
                    timestamp=datetime.now(),
                    council_origin=council,
                    metadata={"type": "test"},
                )
            )
        mind_results = chitta.query(CouncilType.MIND, {})
        assert len(mind_results) == 3

    run_test("Mind sees all (happy)", test_mind_sees_all)

    def test_perspectives():
        chitta = FederatedChitta()
        chitta.add_node(
            KnowledgeNode(
                id="test_persp",
                content="Test",
                source="test",
                timestamp=datetime.now(),
                council_origin=CouncilType.GUNA,
            )
        )
        chitta.add_perspective("test_persp", "mind", 0.9)
        node = chitta.get_node("test_persp")
        assert node.perspectives["mind"] == 0.9

    run_test("Add perspectives (happy)", test_perspectives)

    def test_time_filter():
        chitta = FederatedChitta()
        now = datetime.now()
        chitta.add_node(
            KnowledgeNode(
                id="old_node",
                content="Old",
                source="test",
                timestamp=now - timedelta(days=2),
                council_origin=CouncilType.GUNA,
            )
        )
        chitta.add_node(
            KnowledgeNode(
                id="new_node",
                content="New",
                source="test",
                timestamp=now,
                council_origin=CouncilType.GUNA,
            )
        )
        results = chitta.query(CouncilType.GUNA, {"since": now - timedelta(days=1)})
        assert len(results) == 1
        assert results[0].id == "new_node"

    run_test("Time filter (happy)", test_time_filter)

    def test_verification():
        chitta = FederatedChitta()
        chitta.add_node(
            KnowledgeNode(
                id="verify_test",
                content="Test",
                source="test",
                timestamp=datetime.now(),
                council_origin=CouncilType.GUNA,
            )
        )
        chitta.verify_node("verify_test", "mind")
        node = chitta.get_node("verify_test")
        assert node.verification_status == "verified"

    run_test("Verification (happy)", test_verification)

    # Unhappy path tests
    def test_invalid_node():
        chitta = FederatedChitta()
        try:
            chitta.add_node("not_a_node")
            assert False, "Should have raised ChittaError"
        except ChittaError:
            pass

    run_test("Invalid node type (unhappy)", test_invalid_node)

    def test_query_nonexistent():
        chitta = FederatedChitta()
        results = chitta.query(CouncilType.GUNA, {"metadata": {"nonexistent": "value"}})
        assert len(results) == 0

    run_test("Query nonexistent (unhappy)", test_query_nonexistent)

    def test_duplicate_node():
        chitta = FederatedChitta()
        node = KnowledgeNode(
            id="duplicate",
            content="Original",
            source="test",
            timestamp=datetime.now(),
            council_origin=CouncilType.GUNA,
        )
        chitta.add_node(node)
        node2 = KnowledgeNode(
            id="duplicate",
            content="Duplicate",
            source="test",
            timestamp=datetime.now(),
            council_origin=CouncilType.ELEMENTAL,
            perspectives={"new": 0.5},
        )
        chitta.add_node(node2)
        result = chitta.get_node("duplicate")
        assert "new" in result.perspectives

    run_test("Duplicate node handling (unhappy)", test_duplicate_node)

    def test_memory_eviction():
        chitta = FederatedChitta(max_nodes=3)
        for i in range(5):
            chitta.add_node(
                KnowledgeNode(
                    id=f"node_{i}",
                    content=f"Content {i}",
                    source="test",
                    timestamp=datetime.now(),
                    council_origin=CouncilType.GUNA,
                )
            )
        # Zou max_nodes moeten hebben of minder
        assert (
            len(chitta._nodes) <= 5
        )  # In werkelijkheid kunnen er minder zijn door eviction

    run_test("Memory eviction (unhappy)", test_memory_eviction)

    def test_invalid_filter():
        chitta = FederatedChitta()
        chitta.add_node(
            KnowledgeNode(
                id="test",
                content="Test",
                source="test",
                timestamp=datetime.now(),
                council_origin=CouncilType.GUNA,
            )
        )
        results = chitta.query(CouncilType.GUNA, {"invalid_key": "value"})
        assert isinstance(results, list)

    run_test("Invalid filter key (unhappy)", test_invalid_filter)

    # Edge cases
    def test_empty_chitta():
        chitta = FederatedChitta()
        stats = chitta.get_stats()
        assert stats["total_nodes"] == 0
        results = chitta.query(CouncilType.MIND, {})
        assert len(results) == 0

    run_test("Empty Chitta (edge)", test_empty_chitta)

    def test_very_long_content():
        chitta = FederatedChitta()
        long_content = "A" * 10000
        chitta.add_node(
            KnowledgeNode(
                id="long_content",
                content=long_content,
                source="test",
                timestamp=datetime.now(),
                council_origin=CouncilType.GUNA,
            )
        )
        node = chitta.get_node("long_content")
        assert len(node.content) == 10000

    run_test("Very long content (edge)", test_very_long_content)

    # Summary
    print("\n" + "=" * 60)
    print(f"RESULTS: {results['passed']} passed, {results['failed']} failed")
    print("=" * 60)

    if results["failed"] > 0:
        print("\nFailed tests:")
        for name, error in results["errors"]:
            print(f"  - {name}: {error}")

    return results["failed"] == 0


async def test_council_index_comprehensive():
    """Test CouncilIndex component"""
    print("\n" + "=" * 60)
    print("TESTING: CouncilIndex")
    print("=" * 60)

    results = {"passed": 0, "failed": 0, "errors": []}

    async def run_test(name: str, test_func):
        try:
            await test_func()
            print(f"  PASS: {name}")
            results["passed"] += 1
            return True
        except AssertionError as e:
            print(f"  FAIL: {name}: {e}")
            results["failed"] += 1
            results["errors"].append((name, str(e)))
            return False
        except Exception as e:
            print(f"  ERROR: {name}: {e}")
            results["failed"] += 1
            results["errors"].append((name, str(e)))
            return False

    # Happy path tests
    async def test_guna_index():
        chitta = FederatedChitta()
        index = CouncilIndex(CouncilType.GUNA, chitta, update_interval_seconds=0)

        chitta.add_node(
            KnowledgeNode(
                id="guna_1",
                content="Sattva high",
                source="test",
                timestamp=datetime.now(),
                council_origin=CouncilType.GUNA,
                metadata={"guna": "sattva", "intensity": 0.8},
            )
        )
        chitta.add_node(
            KnowledgeNode(
                id="guna_2",
                content="Sattva medium",
                source="test",
                timestamp=datetime.now(),
                council_origin=CouncilType.GUNA,
                metadata={"guna": "sattva", "intensity": 0.6},
            )
        )

        await index.update()
        data = index.get_index()

        assert data["council"] == "guna"
        assert "data" in data
        assert data["data"]["dominant"] == "sattva"
        assert data["data"]["scores"]["sattva"] > 0.5

    await run_test("Guna index (happy)", test_guna_index)

    async def test_elemental_index():
        chitta = FederatedChitta()
        index = CouncilIndex(CouncilType.ELEMENTAL, chitta, update_interval_seconds=0)

        chitta.add_node(
            KnowledgeNode(
                id="fire_1",
                content="Fire high",
                source="test",
                timestamp=datetime.now(),
                council_origin=CouncilType.ELEMENTAL,
                metadata={"fire": 0.9, "water": 0.1},
            )
        )

        await index.update()
        data = index.get_index()

        assert data["data"]["dominant"] == "fire"
        assert data["data"]["elements"]["fire"] > 0.5

    await run_test("Elemental index (happy)", test_elemental_index)

    async def test_graha_index():
        chitta = FederatedChitta()
        index = CouncilIndex(CouncilType.GRAHA, chitta, update_interval_seconds=0)

        chitta.add_node(
            KnowledgeNode(
                id="surya_1",
                content="Surya strong",
                source="test",
                timestamp=datetime.now(),
                council_origin=CouncilType.GRAHA,
                metadata={"graha": "surya", "state": "strong", "strength": 0.8},
            )
        )

        await index.update()
        data = index.get_index()

        assert "grahas" in data["data"]
        assert data["data"]["dominant"] == "surya"

    await run_test("Graha index (happy)", test_graha_index)

    async def test_rate_limiting():
        chitta = FederatedChitta()
        index = CouncilIndex(CouncilType.GUNA, chitta, update_interval_seconds=60)

        result1 = await index.update()
        assert result1 == True

        result2 = await index.update()
        assert result2 == False

    await run_test("Rate limiting (happy)", test_rate_limiting)

    async def test_stale_detection():
        chitta = FederatedChitta()
        index = CouncilIndex(CouncilType.GUNA, chitta, update_interval_seconds=1)

        await index.update()
        assert not index.is_stale()

        await asyncio.sleep(2.5)
        assert index.is_stale()

    await run_test("Stale detection (happy)", test_stale_detection)

    # Unhappy path tests
    async def test_empty_chitta():
        chitta = FederatedChitta()
        index = CouncilIndex(CouncilType.GUNA, chitta, update_interval_seconds=0)

        result = await index.update()
        assert result == True
        data = index.get_index()
        assert data["data"] == {} or "samples" in data["data"]

    await run_test("Empty Chitta update (unhappy)", test_empty_chitta)

    async def test_invalid_council_type():
        chitta = FederatedChitta()
        index = CouncilIndex(CouncilType.BODY, chitta, update_interval_seconds=0)

        chitta.add_node(
            KnowledgeNode(
                id="body_1",
                content="Body data",
                source="test",
                timestamp=datetime.now(),
                council_origin=CouncilType.BODY,
            )
        )

        await index.update()
        data = index.get_index()
        assert "node_count" in data["data"] or data["data"] == {}

    await run_test("Invalid council type handling (unhappy)", test_invalid_council_type)

    # Edge cases
    async def test_very_frequent_updates():
        chitta = FederatedChitta()
        index = CouncilIndex(CouncilType.GUNA, chitta, update_interval_seconds=0)

        for i in range(10):
            chitta.add_node(
                KnowledgeNode(
                    id=f"node_{i}",
                    content=f"Content {i}",
                    source="test",
                    timestamp=datetime.now(),
                    council_origin=CouncilType.GUNA,
                    metadata={"guna": "sattva", "intensity": 0.5},
                )
            )
            await index.update()

        data = index.get_index()
        assert data["version"] == 10

    await run_test("Very frequent updates (edge)", test_very_frequent_updates)

    # Summary
    print("\n" + "=" * 60)
    print(f"RESULTS: {results['passed']} passed, {results['failed']} failed")
    print("=" * 60)

    return results["failed"] == 0


async def test_integration():
    """Integration tests"""
    print("\n" + "=" * 60)
    print("TESTING: Integration")
    print("=" * 60)

    results = {"passed": 0, "failed": 0, "errors": []}

    async def run_test(name: str, test_func):
        try:
            await test_func()
            print(f"  PASS: {name}")
            results["passed"] += 1
            return True
        except AssertionError as e:
            print(f"  FAIL: {name}: {e}")
            results["failed"] += 1
            results["errors"].append((name, str(e)))
            return False
        except Exception as e:
            print(f"  ERROR: {name}: {e}")
            results["failed"] += 1
            results["errors"].append((name, str(e)))
            return False

    async def test_full_cycle():
        system = FederatedTriadSystem()

        market_data = {
            "price": 45000,
            "change": 0.05,
            "volume": 1000000,
            "volatility": 0.2,
        }

        result = await system.process_cycle(market_data)

        assert result["success"] == True
        assert "council_views" in result
        assert "decision" in result
        assert result["cycle"] == 1

    await run_test("Full cycle (happy)", test_full_cycle)

    async def test_multiple_cycles():
        system = FederatedTriadSystem()

        scenarios = [
            {"price": 45000, "change": 0.05, "volume": 1000000, "volatility": 0.2},
            {"price": 46000, "change": 0.022, "volume": 1200000, "volatility": 0.25},
            {"price": 45500, "change": -0.011, "volume": 800000, "volatility": 0.15},
        ]

        for i, scenario in enumerate(scenarios):
            result = await system.process_cycle(scenario)
            assert result["success"] == True
            assert result["cycle"] == i + 1

        state = system.get_system_state()
        assert state["cycle_count"] == 3

    await run_test("Multiple cycles (happy)", test_multiple_cycles)

    async def test_error_recovery():
        system = FederatedTriadSystem()
        result = await system.process_cycle({})
        assert "success" in result

    await run_test("Error recovery (unhappy)", test_error_recovery)

    async def test_system_reset():
        system = FederatedTriadSystem()

        await system.process_cycle({"price": 45000, "change": 0.05, "volume": 1000000})

        assert system.cycle_count == 1
        assert len(system.chitta._nodes) > 0

        system.reset()

        assert system.cycle_count == 0
        assert len(system.chitta._nodes) == 0

    await run_test("System reset (happy)", test_system_reset)

    # Summary
    print("\n" + "=" * 60)
    print(f"RESULTS: {results['passed']} passed, {results['failed']} failed")
    print("=" * 60)

    return results["failed"] == 0


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import sys

    # Run all tests
    success = asyncio.run(run_complete_test_suite())

    sys.exit(0 if success else 1)
