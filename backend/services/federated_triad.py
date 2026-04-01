"""
FEDERATED TRIAD SYSTEM - Production Implementation
Integrates 5-Council architecture into the trading platform.

Architecture:
- Layer 3: Chitta Mahasagar (Shared Knowledge)
- Layer 2.5: Council Indices (Perspectives)
- Layer 2: Cooperative Deliberation (Iterative Collaboration)
- Layer 2: Buddhi Mind (Discrimination/Decision)
- Layer 1: Body Execution (Action)
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from sqlalchemy import Boolean, Column, DateTime, Float, Index, Integer, String, Text, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import declarative_base

from backend.core.database import system_admin_session

logger = logging.getLogger(__name__)
Base = declarative_base()


# =============================================================================
# DATABASE MODELS
# =============================================================================


class ChittaNodeDB(Base):
    """Database model for Chitta knowledge nodes."""

    __tablename__ = "chitta_nodes"

    id = Column(Integer, primary_key=True)
    node_id = Column(String(64), unique=True, nullable=False, index=True)
    content = Column(Text, nullable=False)
    source = Column(String(50), nullable=False)
    council = Column(String(50), nullable=False)
    element = Column(String(20), nullable=True)
    confidence = Column(Float, default=0.5)
    verified = Column(Boolean, default=False)
    metadata_json = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    expires_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_chitta_council", "council"),
        Index("idx_chitta_element", "element"),
        Index("idx_chitta_created", "created_at"),
    )


class DeliberationRecordDB(Base):
    """Database model for deliberation history."""

    __tablename__ = "deliberation_records"

    id = Column(Integer, primary_key=True)
    cycle_id = Column(String(64), nullable=False, index=True)
    iteration = Column(Integer, nullable=False)
    council = Column(String(50), nullable=False)
    perspective = Column(String(50), nullable=False)
    confidence = Column(Float, nullable=False)
    insights = Column(JSONB, default=[])
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class BuddhiDecisionDB(Base):
    """Database model for Buddhi decisions."""

    __tablename__ = "buddhi_decisions"

    id = Column(Integer, primary_key=True)
    decision_id = Column(String(64), unique=True, nullable=False, index=True)
    action = Column(String(20), nullable=False)  # buy, sell, hold
    confidence = Column(Float, nullable=False)
    rationale = Column(Text, nullable=False)
    supporting = Column(JSONB, default=[])
    opposing = Column(JSONB, default=[])
    contradictions = Column(Integer, default=0)
    council_views = Column(JSONB, default={})
    market_context = Column(JSONB, default={})
    executed = Column(Boolean, default=False)
    execution_result = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


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
class ChittaNode:
    """Knowledge node in Chitta (shared memory)."""

    id: str
    content: str
    source: str
    council: str
    element: str | None = None
    confidence: float = 0.5
    verified: bool = False
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "source": self.source,
            "council": self.council,
            "element": self.element,
            "confidence": self.confidence,
            "verified": self.verified,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class CouncilView:
    """View from a council perspective."""

    council_type: CouncilType
    perspective: str  # bullish, bearish, neutral
    confidence: float
    key_insights: list[str] = field(default_factory=list)
    risk_assessment: str | None = None
    opportunity_score: float = 0.5
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "council_type": self.council_type.value,
            "perspective": self.perspective,
            "confidence": self.confidence,
            "key_insights": self.key_insights,
            "risk_assessment": self.risk_assessment,
            "opportunity_score": self.opportunity_score,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class BuddhiDecision:
    """Decision from Buddhi mind."""

    action: str  # buy, sell, hold
    confidence: float
    rationale: str
    supporting: list[str] = field(default_factory=list)
    opposing: list[str] = field(default_factory=list)
    contradictions: int = 0
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "confidence": self.confidence,
            "rationale": self.rationale,
            "supporting": self.supporting,
            "opposing": self.opposing,
            "contradictions": self.contradictions,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class DeliberationStep:
    """Single step in deliberation process."""

    iteration: int
    council: str
    perspective: str
    confidence: float
    insights: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "iteration": self.iteration,
            "council": self.council,
            "perspective": self.perspective,
            "confidence": self.confidence,
            "insights": self.insights,
        }


# =============================================================================
# CHITTA (Shared Knowledge)
# =============================================================================


class FederatedChitta:
    """
    Chitta Mahasagar - Shared knowledge layer.
    All councils read from and write to this shared memory.
    """

    def __init__(self, max_nodes: int = 10000):
        self.max_nodes = max_nodes
        self._nodes: dict[str, ChittaNode] = {}
        self._by_council: dict[str, set[str]] = defaultdict(set)
        self._by_element: dict[str, set[str]] = defaultdict(set)
        self._initialized = False

    async def initialize(self):
        """Load nodes from database."""
        if self._initialized:
            return

        async with system_admin_session() as session:
            result = await session.execute(
                select(ChittaNodeDB).order_by(ChittaNodeDB.created_at.desc()).limit(self.max_nodes)
            )
            rows = result.scalars().all()

            for row in rows:
                node = ChittaNode(
                    id=row.node_id,
                    content=row.content,
                    source=row.source,
                    council=row.council,
                    element=row.element,
                    confidence=row.confidence,
                    verified=row.verified,
                    timestamp=row.created_at,
                    metadata=row.metadata_json or {},
                )
                self._add_to_memory(node)

        self._initialized = True
        logger.info(f"Chitta initialized with {len(self._nodes)} nodes")

    def _add_to_memory(self, node: ChittaNode):
        """Add node to in-memory indices."""
        self._nodes[node.id] = node
        self._by_council[node.council].add(node.id)
        if node.element:
            self._by_element[node.element].add(node.id)

    async def add_node(self, node: ChittaNode, session: AsyncSession | None = None) -> str:
        """Add a knowledge node to Chitta."""
        # Add to memory
        self._add_to_memory(node)

        # Prune if too many nodes
        if len(self._nodes) > self.max_nodes:
            self._prune_oldest()

        # Persist to database
        if session is None:
            async with system_admin_session() as db_session:
                await self._persist_node(node, db_session)
        else:
            await self._persist_node(node, session)

        return node.id

    async def _persist_node(self, node: ChittaNode, session: AsyncSession):
        """Persist node to database."""
        db_node = ChittaNodeDB(
            node_id=node.id,
            content=node.content,
            source=node.source,
            council=node.council,
            element=node.element,
            confidence=node.confidence,
            verified=node.verified,
            metadata_json=node.metadata,
            created_at=node.timestamp,
        )
        session.add(db_node)
        await session.commit()

    def _prune_oldest(self):
        """Remove oldest unverified nodes."""
        sorted_nodes = sorted(self._nodes.values(), key=lambda n: (n.verified, n.timestamp))
        to_remove = len(self._nodes) - self.max_nodes
        for node in sorted_nodes[:to_remove]:
            del self._nodes[node.id]
            self._by_council[node.council].discard(node.id)
            if node.element:
                self._by_element[node.element].discard(node.id)

    def query(
        self,
        council: str | None = None,
        element: str | None = None,
        verified_only: bool = False,
        limit: int = 100,
    ) -> list[ChittaNode]:
        """Query nodes by filters."""
        if council and council in self._by_council:
            ids = self._by_council[council]
        elif element and element in self._by_element:
            ids = self._by_element[element]
        else:
            ids = set(self._nodes.keys())

        nodes = [self._nodes[i] for i in ids]

        if verified_only:
            nodes = [n for n in nodes if n.verified]

        # Sort by confidence and timestamp
        nodes.sort(key=lambda n: (n.confidence, n.timestamp), reverse=True)
        return nodes[:limit]

    def get_stats(self) -> dict[str, Any]:
        """Get Chitta statistics."""
        verified = sum(1 for n in self._nodes.values() if n.verified)
        return {
            "total_nodes": len(self._nodes),
            "verified_nodes": verified,
            "by_council": {k: len(v) for k, v in self._by_council.items()},
            "by_element": {k: len(v) for k, v in self._by_element.items()},
        }


# =============================================================================
# COUNCIL INDEX
# =============================================================================


class CouncilIndex:
    """
    Index for a specific council type.
    Provides fast access to relevant Chitta nodes.
    """

    def __init__(self, council_type: CouncilType, chitta: FederatedChitta):
        self.council_type = council_type
        self.chitta = chitta
        self.cache: dict[str, Any] = {}

    async def update(self, market_data: dict[str, Any]):
        """Update index based on new market data."""
        # Query relevant nodes for this council
        nodes = self.chitta.query(council=self.council_type.value, limit=50)

        # Build index
        self.cache = {
            "last_update": datetime.now(UTC).isoformat(),
            "node_count": len(nodes),
            "avg_confidence": (sum(n.confidence for n in nodes) / len(nodes) if nodes else 0),
            "insights": [n.content for n in nodes[:10]],
        }

    def get_perspective(self, market_data: dict[str, Any]) -> CouncilView:
        """Generate perspective for this council."""
        # Default implementation - override per council type
        trend = market_data.get("trend", "neutral")
        confidence = self.cache.get("avg_confidence", 0.5)

        return CouncilView(
            council_type=self.council_type,
            perspective=(trend if trend in ["bullish", "bearish", "neutral"] else "neutral"),
            confidence=confidence,
            key_insights=self.cache.get("insights", []),
        )


# =============================================================================
# BUDDHI MIND (Decision)
# =============================================================================


class BuddhiMind:
    """
    Buddhi - The discriminating/decision mind.
    Synthesizes council views into a final decision.
    """

    def __init__(self, chitta: FederatedChitta):
        self.chitta = chitta
        self.decision_history: list[BuddhiDecision] = []

    async def synthesize(
        self, council_views: list[CouncilView], market_data: dict[str, Any]
    ) -> BuddhiDecision:
        """
        Synthesize council views into a decision.

        Logic:
        1. Weight views by confidence
        2. Check for contradictions
        3. Make decision based on weighted consensus
        """
        if not council_views:
            return BuddhiDecision(
                action="hold",
                confidence=0.5,
                rationale="No council views available",
            )

        # Calculate weighted signals
        buy_score = 0.0
        sell_score = 0.0
        total_confidence = 0.0
        supporting = []
        opposing = []

        for view in council_views:
            weight = view.confidence
            total_confidence += weight

            if view.perspective == "bullish":
                buy_score += weight
                supporting.append(
                    f"{view.council_type.value}: {view.key_insights[0] if view.key_insights else 'bullish'}"
                )
            elif view.perspective == "bearish":
                sell_score += weight
                opposing.append(
                    f"{view.council_type.value}: {view.key_insights[0] if view.key_insights else 'bearish'}"
                )

        # Normalize
        if total_confidence > 0:
            buy_score /= total_confidence
            sell_score /= total_confidence

        # Count contradictions
        contradictions = min(len(supporting), len(opposing))

        # Make decision
        if buy_score > sell_score + 0.2:
            action = "buy"
            confidence = buy_score
        elif sell_score > buy_score + 0.2:
            action = "sell"
            confidence = sell_score
        else:
            action = "hold"
            confidence = 1.0 - abs(buy_score - sell_score)

        # Build rationale
        rationale = f"Synthesized {len(council_views)} council views. "
        if action == "buy":
            rationale += f"Buy signal dominant ({buy_score:.2f} vs {sell_score:.2f})."
        elif action == "sell":
            rationale += f"Sell signal dominant ({sell_score:.2f} vs {buy_score:.2f})."
        else:
            rationale += "No clear consensus, holding position."

        decision = BuddhiDecision(
            action=action,
            confidence=round(confidence, 2),
            rationale=rationale,
            supporting=supporting[:5],
            opposing=opposing[:5],
            contradictions=contradictions,
        )

        self.decision_history.append(decision)
        return decision

    async def persist_decision(
        self,
        decision: BuddhiDecision,
        council_views: list[CouncilView],
        market_data: dict[str, Any],
        session: AsyncSession,
    ):
        """Persist decision to database."""
        db_decision = BuddhiDecisionDB(
            decision_id=f"dec_{int(datetime.now(UTC).timestamp() * 1000)}",
            action=decision.action,
            confidence=decision.confidence,
            rationale=decision.rationale,
            supporting=decision.supporting,
            opposing=decision.opposing,
            contradictions=decision.contradictions,
            council_views={v.council_type.value: v.to_dict() for v in council_views},
            market_context=market_data,
        )
        session.add(db_decision)
        await session.commit()


# =============================================================================
# COOPERATIVE DELIBERATION
# =============================================================================


class CooperativeDeliberation:
    """
    Cooperative deliberation between councils.
    Iterative process where councils refine their views.
    """

    def __init__(self, chitta: FederatedChitta, max_iterations: int = 3):
        self.chitta = chitta
        self.max_iterations = max_iterations

    async def run(
        self, indices: dict[CouncilType, CouncilIndex], market_data: dict[str, Any]
    ) -> tuple[list[CouncilView], list[DeliberationStep]]:
        """
        Run deliberation cycle.

        Returns:
            Tuple of (final views, deliberation steps)
        """
        steps = []
        views = []

        for iteration in range(self.max_iterations):
            iteration_views = []

            for council_type, index in indices.items():
                # Update index with latest data
                await index.update(market_data)

                # Get perspective
                view = index.get_perspective(market_data)
                iteration_views.append(view)

                # Record step
                steps.append(
                    DeliberationStep(
                        iteration=iteration + 1,
                        council=council_type.value,
                        perspective=view.perspective,
                        confidence=view.confidence,
                        insights=view.key_insights[:3],
                    )
                )

            views = iteration_views

        return views, steps

    async def persist_steps(
        self, steps: list[DeliberationStep], cycle_id: str, session: AsyncSession
    ):
        """Persist deliberation steps."""
        for step in steps:
            db_step = DeliberationRecordDB(
                cycle_id=cycle_id,
                iteration=step.iteration,
                council=step.council,
                perspective=step.perspective,
                confidence=step.confidence,
                insights=step.insights,
            )
            session.add(db_step)
        await session.commit()


# =============================================================================
# FEDERATED TRIAD SYSTEM
# =============================================================================


class FederatedTriadSystem:
    """
    Complete Federated Triad implementation.
    Integrates all layers in the 5-Council system.
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
            CouncilType.MIND: CouncilIndex(CouncilType.MIND, self.chitta),
            CouncilType.BODY: CouncilIndex(CouncilType.BODY, self.chitta),
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
        self._initialized = False

    async def initialize(self):
        """Initialize the system."""
        if self._initialized:
            return

        await self.chitta.initialize()
        self._initialized = True
        logger.info("FederatedTriadSystem initialized")

    async def process_cycle(self, market_data: dict[str, Any]) -> dict[str, Any]:
        """
        Process one complete cycle.

        Returns:
            Complete cycle result with decision and metadata
        """
        if not self._initialized:
            await self.initialize()

        self.cycle_count += 1
        cycle_id = f"cycle_{self.cycle_count}_{int(datetime.now(UTC).timestamp())}"
        start_time = datetime.now(UTC)

        try:
            # STAP 1: Ingest market data (Body)
            await self._ingest_market_data(market_data)

            # STAP 2: Update council indices
            for index in self.indices.values():
                await index.update(market_data)

            # STAP 3: Cooperative deliberation
            council_views, deliberation_steps = await self.deliberation.run(
                self.indices, market_data
            )

            # STAP 4: Mind synthesis (Buddhi)
            decision = await self.mind.synthesize(council_views, market_data)

            # STAP 5: Persist to database
            async with system_admin_session() as session:
                await self.deliberation.persist_steps(deliberation_steps, cycle_id, session)
                await self.mind.persist_decision(decision, council_views, market_data, session)

                # Add decision node to Chitta
                node = ChittaNode(
                    id=f"chitta_dec_{cycle_id}",
                    content=decision.rationale,
                    source="buddhi",
                    council="mind",
                    confidence=decision.confidence,
                    metadata={"action": decision.action, "cycle": self.cycle_count},
                )
                await self.chitta.add_node(node, session)

            # Calculate latency
            latency_ms = (datetime.now(UTC) - start_time).total_seconds() * 1000

            return {
                "cycle": self.cycle_count,
                "cycle_id": cycle_id,
                "success": True,
                "council_views": [v.to_dict() for v in council_views],
                "decision": decision.to_dict(),
                "deliberation_steps": [s.to_dict() for s in deliberation_steps],
                "chitta_stats": self.chitta.get_stats(),
                "latency_ms": round(latency_ms, 2),
            }

        except Exception as e:
            logger.error(f"Cycle {self.cycle_count} failed: {e}", exc_info=True)
            return {
                "cycle": self.cycle_count,
                "cycle_id": cycle_id,
                "success": False,
                "error": str(e),
            }

    async def _ingest_market_data(self, market_data: dict[str, Any]):
        """Ingest market data into Chitta."""
        # Create node from market data
        trend = market_data.get("trend", "neutral")
        node = ChittaNode(
            id=f"market_{int(datetime.now(UTC).timestamp() * 1000)}",
            content=f"Market trend: {trend}",
            source="market_data",
            council="body",
            element="earth",
            confidence=0.8,
            metadata=market_data,
        )

        async with system_admin_session() as session:
            await self.chitta.add_node(node, session)

    def get_state(self) -> dict[str, Any]:
        """Get current system state."""
        return {
            "cycle_count": self.cycle_count,
            "initialized": self._initialized,
            "chitta": self.chitta.get_stats(),
            "councils": [ct.value for ct in self.indices.keys()],
        }
