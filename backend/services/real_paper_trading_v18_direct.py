"""
REAL Paper Trading V18 - Direct Tool Edition with ANALYTICS LOGGING

Exact copy of Backtest V18 logic maar met directe tool calls (geen MCP client).
Dit is sneller en betrouwbaarder voor live trading.

LOGGING LEVELS:
- INFO: High-level events (trades, cycles, status)
- DEBUG: Detailed agent decisions
- ANALYTICS: Structured data for analysis (JSON format)
"""

import asyncio
import json
import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv

load_dotenv()

from backend.core.telemetry.cognitive_logger import CognitiveLogger
from backend.execution.execution_guard import ExecutionGuard

# Direct imports van tools (sneller dan MCP)
from backend.execution.shadow_portfolio import ShadowPortfolioManager
from backend.mcp_broker.tools.elemental_tools import (
    elemental_earth_entry_check,
    elemental_earth_exit_check,
    elemental_fire_position_size,
    elemental_water_regime_check,
)
from backend.mcp_broker.tools.execution_tools import execution_execute_paper_trade
from backend.mcp_broker.tools.vedastro_tools import vedastro_generate_signal
from backend.services.data_prefetch_agent import DataPreFetchAgent, get_data_agent
from backend.services.paper_trading_ws_broadcast import (
    broadcast_agent_decision,
    broadcast_stats,
    broadcast_trade,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("RealPaperTradingV18Direct")


@dataclass
class PaperTradingConfig:
    """Configuration matching Backtest V18."""

    initial_cash: float = 10000.0
    account_id: str = "paper_v18"

    # V17/V18 constraints
    max_position_pct: float = 0.02  # 2% of portfolio
    max_position_eur: float = 2000.0  # €2k cap

    # VedAstro settings
    min_vedastro_confidence: float = 50.0
    min_vedastro_score: float = 45.0

    # Live Mode (Phase 5)
    live_mode: bool = True
    max_slippage_allowed: float = 0.005  # 0.5% max slippage for live
    min_profit_to_slippage_ratio: float = 2.0  # Profit must be 2x slippage

    # Trading cycle settings - OPTIMIZED
    # DataPreFetchAgent updates all 400+ symbols continuously
    # We analyze ALL symbols every cycle, prioritizing those with VedAstro signals
    cycle_interval_seconds: int = 5  # Reduced from 30s for faster response
    symbols_per_cycle: int = 400  # Analyze all symbols every cycle


@dataclass
class PaperTradingState:
    """Current state of paper trading."""

    cash: float
    total_value: float
    open_positions: dict[str, dict[str, Any]] = field(default_factory=dict)
    trades: list[dict[str, Any]] = field(default_factory=list)
    total_trades: int = 0
    daily_pnl: float = 0.0
    total_pnl: float = 0.0


class RealPaperTradingV18:
    """
    V18 Paper Trading Engine - Direct Tool Calls.

    Gebruikt directe Python imports i.p.v. MCP client voor snellere executie.
    Supports both paper (simulation) and live (real Bitvavo orders) modes.
    """

    def __init__(
        self, initial_capital: float = 10000.0, use_database: bool = True, mode: str = "paper"
    ):
        self.initial_capital = initial_capital
        self.mode = mode  # "paper" or "live"
        self.config = PaperTradingConfig(initial_cash=initial_capital, live_mode=(mode == "live"))
        self.state = PaperTradingState(cash=initial_capital, total_value=initial_capital)

        # Portfolio and Data
        self.portfolio = ShadowPortfolioManager(initial_cash=initial_capital)
        self.data_agent: DataPreFetchAgent | None = None
        self.all_symbols: list[str] = []

        # Track trade history voor Earth element 3-loss rule
        self.trade_history: dict[str, list[dict]] = {}
        self.peak_prices: dict[str, float] = {}

        # State
        self.running = False
        self.start_time: datetime | None = None
        self.end_time: datetime | None = None
        self._cycle_count = 0

        # Session management
        self.session_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        self.peak_portfolio = initial_capital
        self._checkpoint_cycles = 60  # Every 60 cycles = 30 min
        self._prev_vedastro_signals: dict[str, str] = {}  # For wakeup detection

        # Circuit breaker state
        self._circuit_breaker_active = False
        self._circuit_breaker_until: datetime | None = None

        # Database integration
        self.use_database = use_database
        self.db: Optional[Any] = None
        self.db_session_id: Optional[int] = None
        self._cycle_analytics = []  # Batch analytics storage

        # Chitta Memory integration
        self.use_chitta = use_database  # Use same flag for now
        self.chitta: Optional[Any] = None

        # RAG Vector Memory integration (ChromaDB)
        self.use_rag = use_database  # Use same flag for now
        self.chroma_client: Optional[Any] = None
        self.chroma_collection: Optional[Any] = None
        self.rag_embedding_model = None

        mode_banner = (
            "LIVE TRADING - REAL BITVAVO ORDERS" if mode == "live" else "PAPER TRADING - SIMULATION"
        )
        print("=" * 80)
        print(f"     V18 {mode_banner}")
        print("=" * 80)
        print(f"\nInitial Capital: EUR {initial_capital:,.2f}")
        print(
            f"Max Position: {self.config.max_position_pct:.0%} or EUR {self.config.max_position_eur:,.0f}"
        )
        print(f"VedAstro Min Confidence: {self.config.min_vedastro_confidence}%")
        print(f"VedAstro Min Score: {self.config.min_vedastro_score}")
        print(f"Cycle Interval: {self.config.cycle_interval_seconds}s")
        print(f"Database: {'ENABLED' if use_database else 'DISABLED'}")
        print(f"Mode: {mode.upper()} {'(€5 REAL orders)' if mode == 'live' else '(simulated)'}")

        # Initialize Execution Guard (Taak 2.1)
        self.guard = ExecutionGuard(initial_capital=initial_capital)
        print("Execution Guard: READY (Daily Limit: 5%)")
        print()

        # Initialize Cognitive Logger (Taak 9.1)
        self.cognitive_logger = CognitiveLogger()
        print("Cognitive Logger: READY")

    async def initialize(self):
        """Initialize Data Agent and Database."""
        logger.info("Initializing Paper Trading V18 Direct...")

        # Initialize Database
        if self.use_database:
            try:
                from backend.services.paper_trading_db import PaperTradingDB

                self.db = PaperTradingDB()

                async with self.db:
                    session = await self.db.create_session(
                        session_id=self.session_id,
                        initial_capital=self.initial_capital,
                        duration_hours=8,
                        account_id=self.config.account_id,
                    )
                    self.db_session_id = session.id
                    logger.info(f"[DB] Session {self.session_id} created in database")
            except Exception as e:
                logger.error(f"[DB] Failed to initialize database: {e}")
                logger.warning("[DB] Continuing without database persistence")
                self.use_database = False

        # Initialize Chitta Memory
        if self.use_chitta:
            try:
                from backend.core.conscious.chitta_memory import ChittaMemory

                self.chitta = ChittaMemory(agent_id="V18_Elemental")
                logger.info("[CHITTA] Memory system initialized")
            except Exception as e:
                logger.error(f"[CHITTA] Failed to initialize: {e}")
                self.use_chitta = False

        # Initialize RAG Vector Memory (ChromaDB)
        if self.use_rag:
            try:
                import chromadb
                from chromadb.config import Settings

                # Connect to ChromaDB
                self.chroma_client = chromadb.HttpClient(
                    host="localhost",
                    port=8100,
                    settings=Settings(allow_reset=False, anonymized_telemetry=False),
                )

                # Get or create collection
                try:
                    self.chroma_collection = self.chroma_client.get_collection("trading_knowledge")
                    logger.info("[RAG] ChromaDB connected, collection 'trading_knowledge' loaded")
                except Exception:
                    logger.warning("[RAG] Collection 'trading_knowledge' not found, RAG disabled")
                    self.use_rag = False

                # Try to load sentence transformer for embeddings
                if self.use_rag:
                    try:
                        from sentence_transformers import SentenceTransformer

                        self.rag_embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
                        logger.info("[RAG] Embedding model loaded")
                    except ImportError:
                        logger.warning("[RAG] sentence-transformers not installed, using fallback")
                        self.rag_embedding_model = None
                    except Exception as e:
                        logger.warning(f"[RAG] Failed to load embedding model: {e}")
                        self.rag_embedding_model = None

            except Exception as e:
                logger.error(f"[RAG] Failed to initialize ChromaDB: {e}")
                self.use_rag = False

        # Initialize Data Pre-fetch Agent
        from backend.services.data_prefetch_agent import DataPreFetchAgent, get_data_agent

        self.data_agent = await get_data_agent()
        await self.data_agent.start()

        # DYNAMIC SYMBOL LOADING (Phase 5)
        if self.config.live_mode:
            try:
                from backend.execution.bitvavo_adapter import BitvavoAdapter

                bitvavo = BitvavoAdapter()
                if await bitvavo.initialize():
                    self.all_symbols = bitvavo.get_eur_pairs()
                    logger.info(f"[LIVE] Loaded {len(self.all_symbols)} EUR pairs from Bitvavo API")
                    await bitvavo.close()
                else:
                    self.all_symbols = DataPreFetchAgent.PRIORITY_SYMBOLS
            except Exception as e:
                logger.error(f"[LIVE] Failed to load Bitvavo symbols: {e}")
                self.all_symbols = DataPreFetchAgent.PRIORITY_SYMBOLS
        else:
            self.all_symbols = DataPreFetchAgent.PRIORITY_SYMBOLS

        logger.info(f"Data agent initialized with {len(self.all_symbols)} symbols")

        # Warm up data
        logger.info("Warming up data cache...")
        await asyncio.sleep(3)

        logger.info("Paper Trading V18 Direct ready")

    async def close(self):
        """Cleanup resources and close database."""
        self.running = False

        # Close database session
        if self.use_database and self.db:
            try:
                async with self.db:
                    # Calculate final portfolio value
                    if self.data_agent:
                        prices = await self.data_agent.get_all_prices()
                        final_value = await self._calculate_portfolio_value(prices)
                    else:
                        final_value = self.state.total_value

                    # Determine stop reason
                    if self._circuit_breaker_active:
                        reason = "circuit_breaker"
                    elif self.state.total_pnl < 0:
                        reason = "negative_pnl"
                    else:
                        reason = "completed"

                    await self.db.end_session(
                        session_id=self.session_id,
                        final_capital=final_value,
                        reason=reason,
                    )
                    logger.info(f"[DB] Session {self.session_id} closed in database")
            except Exception as e:
                logger.error(f"[DB] Error closing session: {e}")

        # Close RAG (ChromaDB doesn't need explicit close for HttpClient)
        if self.use_rag and self.chroma_client:
            try:
                # ChromaDB HttpClient doesn't require explicit close
                logger.info("[RAG] ChromaDB client ready for cleanup")
            except Exception as e:
                logger.error(f"[RAG] Error with ChromaDB: {e}")

        if self.data_agent:
            try:
                await asyncio.wait_for(self.data_agent.stop(), timeout=5.0)
            except:
                pass

        logger.info("Paper Trading V18 Direct closed")

    async def run(self, duration_hours: int = 8):
        """Run paper trading session."""
        self.start_time = datetime.utcnow()
        self.end_time = self.start_time + timedelta(hours=duration_hours)
        self.running = True

        print(f"[START] {self.start_time}")
        print(f"[END]   {self.end_time}")
        print(
            f"[CYCLE] Every {self.config.cycle_interval_seconds}s, {self.config.symbols_per_cycle} symbols"
        )
        print(
            f"[CHECKPOINT] Every {self._checkpoint_cycles} cycles ({self._checkpoint_cycles * self.config.cycle_interval_seconds // 60} min)"
        )
        print("[CIRCUIT BREAKER] 5% portfolio drawdown = 2h pause")
        print()

        # Start status reporter
        reporter = asyncio.create_task(self._status_reporter(interval=60))

        try:
            while datetime.utcnow() < self.end_time and self.running:
                # Check Execution Guard (Taak 2.2)
                if self.guard.is_emergency():
                    logger.critical("[GUARD] Emergency Stop detected! Shutting down loop.")
                    self.running = False
                    break

                # Check internal manual circuit breaker
                if self._circuit_breaker_active:
                    if datetime.utcnow() < self._circuit_breaker_until:
                        logger.info(f"[CIRCUIT BREAKER] Paused until {self._circuit_breaker_until}")
                        await asyncio.sleep(60)
                        continue
                    else:
                        logger.info("[CIRCUIT BREAKER] Resumed")
                        self._circuit_breaker_active = False

                await self._trading_cycle()

                # Checkpoint state every N cycles
                if self._cycle_count % self._checkpoint_cycles == 0:
                    await self._checkpoint_state()

                await asyncio.sleep(self.config.cycle_interval_seconds)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Trading loop error: {e}")
        finally:
            self.running = False
            reporter.cancel()
            try:
                await reporter
            except asyncio.CancelledError:
                pass
            # Final checkpoint
            await self._checkpoint_state()

        await self._final_status()

    async def _checkpoint_state(self):
        """Save session state to JSON for recovery."""
        try:
            checkpoint_dir = Path("checkpoints")
            checkpoint_dir.mkdir(exist_ok=True)

            state = {
                "session_id": self.session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "cycle": self._cycle_count,
                "cash": self.state.cash,
                "total_value": self.state.total_value,
                "total_pnl": self.state.total_pnl,
                "peak_portfolio": self.peak_portfolio,
                "open_positions": self.state.open_positions,
                "trades_count": len(self.state.trades),
                "recent_trades": self.state.trades[-20:] if self.state.trades else [],
            }

            checkpoint_file = checkpoint_dir / f"session_{self.session_id}.json"
            with open(checkpoint_file, "w") as f:
                json.dump(state, f, indent=2, default=str)

            logger.info(f"[CHECKPOINT] Cycle {self._cycle_count} saved to {checkpoint_file}")
        except Exception as e:
            logger.error(f"[CHECKPOINT] Error: {e}")

    def _check_portfolio_circuit_breaker(self):
        """Check if portfolio drawdown exceeds 5% threshold."""
        if self.state.total_value > self.peak_portfolio:
            self.peak_portfolio = self.state.total_value

        drawdown = (self.peak_portfolio - self.state.total_value) / self.peak_portfolio

        if drawdown > 0.05 and not self._circuit_breaker_active:  # 5% drawdown
            self._circuit_breaker_active = True
            self._circuit_breaker_until = datetime.utcnow() + timedelta(hours=2)
            logger.warning(
                f"[CIRCUIT BREAKER] 5% portfolio drawdown ({drawdown:.1%}) - Pausing 2h until {self._circuit_breaker_until}"
            )
            return True
        return False

    async def _trading_cycle(self):
        """Execute one trading cycle - OPTIMIZED for all 400+ symbols."""
        self._cycle_count += 1

        # --- PERIODIC TUNING BROADCAST (Every 10 cycles / ~50s) ---
        if self._cycle_count % 10 == 0:
            try:
                from backend.services.evolutionary_tuner import tuner
                from backend.services.paper_trading_ws_broadcast import broadcast_tuning_update

                tuning_stats = {
                    "regimes": {
                        r: {
                            "weights": tuner.current_weights.get(r, {}),
                            "bandit_stats": b.get_stats(),
                        }
                        for r, b in tuner.bandits.items()
                    },
                    "agents": tuner.agents,
                }
                await broadcast_tuning_update(tuning_stats)
            except Exception as e:
                logger.debug(f"[TUNER-WS] Broadcast failed: {e}")

        if not self.data_agent:
            return

        # Get fresh prices for ALL symbols
        prices = await self.data_agent.get_all_prices()

        if len(prices) < 10:
            logger.warning(f"Limited fresh prices: {len(prices)}")
            return

        # Update portfolio value
        self.state.total_value = await self._calculate_portfolio_value(prices)

        # Check portfolio-level circuit breaker
        if self._check_portfolio_circuit_breaker():
            return  # Skip this cycle

        # OPTIMIZED: Prioritize symbols
        # 1. Symbols with open positions (exit check) - ALWAYS check these
        # 2. Other symbols (entry check) - prioritize by VedAstro potential
        open_position_symbols = [s for s in self.state.open_positions.keys() if s in prices]
        other_symbols = [s for s in prices.keys() if s not in self.state.open_positions]

        # Limit other symbols to analyze per cycle to prevent overload
        # But rotate through them faster (every symbol gets checked every few cycles)
        max_new_symbols_per_cycle = 100
        cycle_offset = (self._cycle_count * max_new_symbols_per_cycle) % max(1, len(other_symbols))
        new_symbols_to_check = []
        for i in range(min(max_new_symbols_per_cycle, len(other_symbols))):
            idx = (cycle_offset + i) % len(other_symbols)
            new_symbols_to_check.append(other_symbols[idx])

        # Combine: open positions first (critical), then new opportunities
        to_analyze = open_position_symbols + new_symbols_to_check

        trades_this_cycle = 0

        logger.debug(
            f"Cycle {self._cycle_count}: Checking {len(open_position_symbols)} positions + {len(new_symbols_to_check)} new symbols"
        )

        for symbol in to_analyze:
            try:
                price_data = prices[symbol]
                current_price = price_data.price

                # Check if we have an open position
                if symbol in self.state.open_positions:
                    # Exit check - always do this for positions
                    exit_triggered = await self._evaluate_exit(symbol, current_price)
                    if exit_triggered:
                        trades_this_cycle += 1
                else:
                    # Entry check - get price history only when needed
                    price_history_data = await self.data_agent.get_price_history(
                        symbol, lookback=30
                    )
                    price_history = [p.price for p in price_history_data]

                    entry_triggered = await self._evaluate_entry(
                        symbol, current_price, price_history
                    )
                    if entry_triggered:
                        trades_this_cycle += 1

            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
                continue

        if trades_this_cycle > 0:
            logger.info(f"Cycle {self._cycle_count}: {trades_this_cycle} trades executed")

        # Persist buffered analytics (Taak 1.2)
        await self._persist_cycle_analytics()

        await self._broadcast_stats()

    async def _persist_cycle_analytics(self):
        """Batch save all analytics from the current cycle to the database."""
        if not self.use_database or not self.db or not self._cycle_analytics:
            return

        try:
            async with self.db:
                await self.db.save_analytics_batch(self._cycle_analytics)
            logger.debug(
                f"[DB-BATCH] Cycle {self._cycle_count}: Persisted {len(self._cycle_analytics)} records"
            )
            self._cycle_analytics = []  # Clear for next cycle
        except Exception as e:
            logger.error(f"[DB-BATCH] Failed to persist analytics: {e}")

    async def _evaluate_entry(
        self, symbol: str, current_price: float, price_history: list[float]
    ) -> bool:
        """Evaluate entry - EXACT Backtest V18 Logic met ANALYTICS LOGGING."""
        analysis = {
            "timestamp": datetime.utcnow().isoformat(),
            "symbol": symbol,
            "cycle": self._cycle_count,
            "current_price": current_price,
            "price_history_length": len(price_history),
            "portfolio_value": self.state.total_value,
            "cash": self.state.cash,
            "vedastro": {},
            "elemental": {},
            "consensus": {},
            "decision": {},
        }

        try:
            # ============================================================
            # 1. VEDASTRO ANALYSIS (Navagrahas - 9 Planets)
            # ============================================================
            vedastro_result = await vedastro_generate_signal(
                symbol=symbol, current_price=current_price
            )

            confidence = vedastro_result.get("confidence", 0)
            strength_score = vedastro_result.get("strength_score", 0)
            signal = vedastro_result.get("signal", "HOLD")
            dominant_planet = (
                vedastro_result.get("primary_factors", ["UNKNOWN"])[0]
                if vedastro_result.get("primary_factors")
                else "UNKNOWN"
            )

            analysis["vedastro"] = {
                "signal": signal,
                "confidence": confidence,
                "strength_score": strength_score,
                "dominant_planet": dominant_planet,
                "dasha_context": vedastro_result.get("dasha_context", ""),
                "risk_level": vedastro_result.get("risk_level", "unknown"),
            }

            logger.info(
                f"[VEDASTRO] {symbol}: {signal} (conf={confidence:.1f}, score={strength_score:.1f}, planet={dominant_planet})"
            )

            # ============================================================
            # 1b. ELEMENTAL WATER ANALYSIS (Jala - Regime/Momentum)
            # ============================================================
            # Must run BEFORE RAG so we know exactly what regime to search for
            water_vote = 0.0
            regime = "unknown"
            risk_on_score = 0.5

            if len(price_history) >= 20:
                try:
                    water_result = await elemental_water_regime_check(
                        symbol=symbol, prices=price_history
                    )
                    regime = water_result.get("regime", "unknown")
                    risk_on_score = water_result.get("risk_on_score", 0.5)

                    # Water vote based on regime favorability
                    if regime == "expansion":
                        water_vote = 0.4
                    elif regime == "contraction":
                        water_vote = -0.2 if risk_on_score < 0.35 else 0.1
                    else:  # neutral
                        water_vote = 0.2

                    logger.debug(
                        f"[WATER] {symbol}: Regime={regime}, risk_on={risk_on_score:.2f}, vote={water_vote:.2f}"
                    )
                except Exception as e:
                    logger.warning(f"[WATER] {symbol}: Regime check failed ({e})")
                    water_vote = 0.0
            else:
                logger.debug(
                    f"[WATER] {symbol}: Insufficient history ({len(price_history)} points)"
                )
                water_vote = 0.0

            analysis["elemental"]["water"] = {
                "vote": water_vote,
                "regime": regime,
                "risk_on_score": risk_on_score,
            }

            # ============================================================
            # 1c. RAG ORIENT PHASE - Metadata-Driven Retrieval
            # ============================================================
            rag_insights = []
            rag_adjustment = 0.0
            if self.use_rag and self.chroma_collection:
                try:
                    # Advanced Query: Focus on Symbol, exact Regime and VedAstro Lord matching
                    mahadasha = (
                        vedastro_result.get("dasha_context", "").split("-")[0].strip()
                        if "-" in vedastro_result.get("dasha_context", "")
                        else "Unknown"
                    )
                    antardasha = (
                        vedastro_result.get("dasha_context", "").split("-")[1].strip()
                        if "-" in vedastro_result.get("dasha_context", "")
                        else "Unknown"
                    )

                    query_text = (
                        f"{symbol} {regime.upper()} {mahadasha}-{antardasha} {dominant_planet}"
                    )

                    # Semantic Search on the 10,125 episodes
                    results = self.chroma_collection.query(
                        query_texts=[query_text],
                        n_results=5,
                    )

                    if results and results.get("documents") and results["documents"][0]:
                        documents = results["documents"][0]
                        metadatas = results["metadatas"][0]
                        distances = results["distances"][0]

                        rag_insights = [
                            {"content": doc, "metadata": meta, "distance": dist}
                            for doc, meta, dist in zip(documents, metadatas, distances)
                        ]

                        logger.info(
                            f"[RAG-COGNITIVE] {symbol}: Found {len(rag_insights)} strategic episodes"
                        )

                        # Dynamic weighting based on historical returns
                        for insight in rag_insights:
                            meta = insight["metadata"]
                            # Bonus multiplier if symbol matches identically
                            symbol_match_multiplier = 1.5 if meta.get("symbol") == symbol else 1.0
                            # Bonus multiplier if Dasha matches identically
                            dasha_match_multiplier = (
                                1.5 if meta.get("mahadasha") == mahadasha else 1.0
                            )

                            historical_return = float(meta.get("return_pct", 0.0))

                            # Scaling the return into an adjustment bounded by (-0.10 to +0.10) per insight
                            if historical_return > 0:
                                weight = (
                                    min(0.05, historical_return / 500)
                                    * symbol_match_multiplier
                                    * dasha_match_multiplier
                                )
                                rag_adjustment += weight
                            else:
                                weight = (
                                    max(-0.05, historical_return / 500)
                                    * symbol_match_multiplier
                                    * dasha_match_multiplier
                                )
                                rag_adjustment += weight

                        # Clamp final adjustment strictly
                        rag_adjustment = max(-0.25, min(0.25, rag_adjustment))

                        analysis["rag"] = {
                            "insights_count": len(rag_insights),
                            "adjustment": float(rag_adjustment),
                            "top_scenario": (
                                rag_insights[0]["content"][:100] if rag_insights else None
                            ),
                        }

                except Exception as e:
                    logger.warning(f"[RAG-COGNITIVE] {symbol}: Failed to retrieve insights: {e}")

            # VedAstro vote berekening (EERST!)
            signal_upper = signal.upper() if signal else "HOLD"

            # VEDASTRO WAKEUP DETECTION (NA signal_upper definitie!)
            prev_signal = self._prev_vedastro_signals.get(symbol, "HOLD")
            if prev_signal == "HOLD" and signal_upper in ["BUY", "STRONG_BUY"]:
                logger.info(
                    f"[VEDASTRO WAKEUP] {symbol} | Planet: {dominant_planet} | Conf: {confidence:.1f} | "
                    f"Previous {prev_signal} -> Now {signal_upper} | Cycle: {self._cycle_count}"
                )
            self._prev_vedastro_signals[symbol] = signal_upper
            if signal_upper == "STRONG_BUY":
                vedastro_vote = 1.0 * (confidence / 100)
            elif signal_upper == "BUY":
                vedastro_vote = 0.8 * (confidence / 100)
            elif signal_upper == "HOLD":
                vedastro_vote = 0.0
            else:  # SELL
                vedastro_vote = -0.5 * (confidence / 100)

            # Apply RAG adjustment to VedAstro vote
            vedastro_vote_adjusted = vedastro_vote + rag_adjustment
            vedastro_vote_adjusted = max(-1.0, min(1.0, vedastro_vote_adjusted))  # Clamp

            analysis["vedastro"]["vote"] = vedastro_vote_adjusted
            analysis["vedastro"]["rag_adjustment"] = rag_adjustment

            # ============================================================
            # 2. ELEMENTAL EARTH ANALYSIS (Prithvi - Stabiliteit/Risk)
            # ============================================================
            earth_vote = 0.5  # Default neutraal-positief
            earth_blocking_reason = None
            earth_can_enter = True

            try:
                trade_history = self.trade_history.get(symbol, [])
                recent_losses = sum(1 for t in trade_history[-5:] if not t.get("win", True))

                earth_result = await elemental_earth_entry_check(
                    symbol=symbol, trade_history=trade_history
                )
                earth_can_enter = earth_result.get("can_enter", True)

                if earth_can_enter:
                    earth_vote = 0.5
                else:
                    earth_vote = -0.3
                    earth_blocking_reason = earth_result.get("blocking_reason", "Unknown")
                    logger.info(f"[EARTH] {symbol}: Concerns - {earth_blocking_reason}")
            except Exception as e:
                logger.warning(f"[EARTH] {symbol}: Check failed ({e}), neutral")
                earth_vote = 0.0

            analysis["elemental"]["earth"] = {
                "vote": earth_vote,
                "can_enter": earth_can_enter,
                "blocking_reason": earth_blocking_reason,
                "recent_losses": recent_losses if "recent_losses" in locals() else 0,
            }

            # ============================================================
            # 3. ELEMENTAL FIRE ANALYSIS (Agni - Positie Sizing/Transformatie)
            # ============================================================
            current_dominant_planet = self._get_dominant_planet(datetime.utcnow())
            fire_vote = 0.0
            position_size = 0
            fire_sizing_factors = {}

            try:
                fire_result = await elemental_fire_position_size(
                    symbol=symbol,
                    portfolio_value=self.state.total_value,
                    vedastro_score=strength_score,
                    dominant_planet=current_dominant_planet,
                    price_history=price_history,
                )
                position_size = fire_result.get("position_size_eur", 0)
                fire_sizing_factors = fire_result.get("sizing_factors", {})

                # Fire confidence based on position size vs max allowed
                max_fire_size = self.state.total_value * 0.02
                fire_vote = (
                    min(1.0, position_size / max_fire_size) * 0.5 if max_fire_size > 0 else 0
                )

                logger.debug(f"[FIRE] {symbol}: Size=€{position_size:.2f}, vote={fire_vote:.2f}")
            except Exception as e:
                logger.warning(f"[FIRE] {symbol}: Sizing failed ({e}), using default")
                position_size = self.state.total_value * 0.005
                fire_vote = 0.1
                fire_sizing_factors = {"error": str(e)}

            analysis["elemental"]["fire"] = {
                "vote": fire_vote,
                "position_size_raw": position_size,
                "dominant_planet": current_dominant_planet,
                "sizing_factors": fire_sizing_factors,
            }

            # ============================================================
            # 5. GUNA ANALYSIS (3 Gunas - VedAstro Multiplier)
            # ============================================================
            # Gunas bepalen de kwaliteit van VedAstro signalen:
            # - Sattva (helderheid): VedAstro betrouwbaarder (+10%)
            # - Rajas (activiteit): Normale VedAstro (0%)
            # - Tamas (traagheid): VedAstro minder betrouwbaar (-30%)

            guna_multiplier = 1.0  # Default: geen effect
            dominant_guna = "rajas"

            if len(price_history) >= 5:
                # Calculate volatility over laatste 5 periodes
                recent_returns = [
                    (price_history[i] - price_history[i - 1]) / price_history[i - 1]
                    for i in range(-5, 0)
                ]
                volatility = sum(abs(r) for r in recent_returns) / len(recent_returns)

                # Guna classificatie obv volatiliteit + trend consistentie
                price_direction_changes = sum(
                    1
                    for i in range(1, len(recent_returns))
                    if recent_returns[i] * recent_returns[i - 1] < 0
                )

                if volatility > 0.03 and price_direction_changes >= 2:
                    # High vol + veel richtingwisselingen = Rajas (chaos)
                    sattva, rajas, tamas = 0.2, 0.6, 0.2
                    guna_multiplier = 0.9  # VedAstro iets minder betrouwbaar
                    dominant_guna = "rajas"
                elif volatility < 0.01 and price_direction_changes <= 1:
                    # Low vol + consistente trend = Sattva (helderheid)
                    sattva, rajas, tamas = 0.6, 0.2, 0.2
                    guna_multiplier = 1.1  # VedAstro betrouwbaarder
                    dominant_guna = "sattva"
                else:
                    # Gemiddeld = mix
                    sattva, rajas, tamas = 0.3, 0.4, 0.3
                    guna_multiplier = 1.0
                    dominant_guna = "balanced"

                analysis["gunas"] = {
                    "sattva": sattva,
                    "rajas": rajas,
                    "tamas": tamas,
                    "volatility": volatility,
                    "direction_changes": price_direction_changes,
                    "multiplier": guna_multiplier,
                    "dominant_guna": dominant_guna,
                }

            # Pas Gunas multiplier toe op VedAstro vote
            vedastro_vote_adjusted = vedastro_vote * guna_multiplier
            logger.debug(
                f"[GUNAS] {symbol}: {dominant_guna} (mult={guna_multiplier:.2f}) | "
                f"VedAstro: {vedastro_vote:.2f} → {vedastro_vote_adjusted:.2f}"
            )

            # ============================================================
            # 6. VAYU (Lucht) - Sentiment Dampener
            # ============================================================
            # Vayu draagt informatie en kan de gehele consensus dempen
            # bij extreme marktcondities (panic, FOMO, extreme volatiliteit)

            vayu_dampener = 1.0  # Default: geen demping
            vayu_sentiment = "neutral"

            if len(price_history) >= 10:
                # Bereken recente volatiliteit
                recent_returns = [
                    (price_history[i] - price_history[i - 1]) / price_history[i - 1]
                    for i in range(1, min(10, len(price_history)))
                ]
                recent_vol = (
                    sum(abs(r) for r in recent_returns) / len(recent_returns)
                    if recent_returns
                    else 0
                )

                # Vayu demping bij extreme volatiliteit
                if recent_vol > 0.05:  # >5% gemiddelde beweging
                    vayu_dampener = 0.7  # 30% demping
                    vayu_sentiment = "extreme_volatility"
                    logger.debug(
                        f"[VAYU] {symbol}: Extreme volatility detected ({recent_vol:.1%}) - damping 30%"
                    )
                elif recent_vol > 0.03:  # >3%
                    vayu_dampener = 0.85  # 15% demping
                    vayu_sentiment = "high_volatility"
                    logger.debug(
                        f"[VAYU] {symbol}: High volatility ({recent_vol:.1%}) - damping 15%"
                    )

                analysis["vayu"] = {
                    "dampener": vayu_dampener,
                    "sentiment": vayu_sentiment,
                    "recent_volatility": recent_vol,
                }

            # ============================================================
            # 7. JALA-DYNAMISCHE GEWICHTEN (Marktregime bepaalt balans)
            # ============================================================
            # Water/Jala bepaalt de stroming en verschuift de focus:
            # - EXPANSIE (bull): Meer VedAstro (kosmische timing is key)
            # - CONTRACTIE (bear): Meer Earth (kapitaalbescherming is key)
            # - NEUTRAAL: Gebalanceerd

            # GEWICHTEN (sum = 1.0, zonder guna als aparte stem)
            # VERHOGEN DREMPELS voor conservatievere trading (V18.1)
            # --- ADAPTIVE WEIGHTS (Auto-Pilot / Evolutionary Tuner) ---
            try:
                from backend.services.evolutionary_tuner import tuner

                adaptive_config = tuner.get_weights(regime)
                weights = {
                    "vedastro": adaptive_config.get("vedastro", 0.30),
                    "earth": adaptive_config.get("earth", 0.30),
                    "fire": adaptive_config.get("fire", 0.25),
                    "water": adaptive_config.get("water", 0.15),
                }
                base_threshold = adaptive_config.get("threshold", 0.35)

                logger.debug(
                    f"[TUNER] {symbol}: Using adaptive weights for {regime} | "
                    f"V:{weights['vedastro']:.2f} E:{weights['earth']:.2f} F:{weights['fire']:.2f} W:{weights['water']:.2f} | "
                    f"Threshold:{base_threshold:.2f}"
                )
            except Exception as tuner_err:
                logger.warning(
                    f"[TUNER] Failed to load adaptive weights, using fallback: {tuner_err}"
                )
                # Fallback to defaults if tuner fails
                if regime == "expansion":
                    weights = {"vedastro": 0.40, "earth": 0.25, "fire": 0.25, "water": 0.10}
                    base_threshold = 0.35
                elif regime == "contraction":
                    weights = {"vedastro": 0.20, "earth": 0.45, "fire": 0.15, "water": 0.20}
                    base_threshold = 0.40
                else:
                    weights = {"vedastro": 0.30, "earth": 0.30, "fire": 0.25, "water": 0.15}
                    base_threshold = 0.35

            # Pas Vayu demping toe op drempel
            effective_threshold = base_threshold * vayu_dampener

            # BEREKEN TOTALE CONSENSUS met dynamische gewichten
            # Gebruik vedastro_vote_adjusted (met Gunas multiplier)!
            raw_consensus = (
                (vedastro_vote_adjusted * weights["vedastro"])
                + (earth_vote * weights["earth"])
                + (fire_vote * weights["fire"])
                + (water_vote * weights["water"])
            )

            # Pas Vayu demping toe op consensus
            total_vote = raw_consensus * vayu_dampener

            # ============================================================
            # 7b. CHITTA EXPERIENCE ADJUSTMENT (Learning from past)
            # ============================================================
            chitta_adjustment = 0.0
            chitta_threshold_adj = 0.0

            if self.use_chitta and self.chitta:
                try:
                    # Get similar past experiences
                    similar_experiences = await self.chitta.get_similar_experiences(
                        symbol=symbol,
                        regime=regime,
                        dominant_planet=current_dominant_planet,
                        limit=10,
                    )

                    if similar_experiences:
                        # Calculate win rate from similar experiences
                        wins = sum(
                            1
                            for exp in similar_experiences
                            if hasattr(exp, "is_win") and exp.is_win()
                        )
                        total = len(similar_experiences)
                        win_rate = wins / total if total > 0 else 0.5

                        # Taak 3.1: Dynamic threshold adjustment
                        if total >= 3:
                            if win_rate < 0.40:
                                chitta_threshold_adj = 0.05  # Raise threshold (be more cautious)
                                logger.info(
                                    f"[CHITTA] {symbol}: Raising threshold by 0.05 due to low win-rate ({win_rate:.1%})"
                                )
                            elif win_rate > 0.60:
                                chitta_threshold_adj = -0.03  # Lower threshold (be more confident)
                                logger.debug(
                                    f"[CHITTA] {symbol}: Lowering threshold by 0.03 due to high win-rate ({win_rate:.1%})"
                                )

                        # Adjust consensus based on past performance
                        # More wins = boost confidence, more losses = reduce confidence
                        confidence_factor = 0.8 + (win_rate * 0.4)  # 0.8 to 1.2

                        # Scale adjustment based on samples
                        sample_impact = min(1.0, total / 5)
                        chitta_adjustment = (confidence_factor - 1.0) * sample_impact * 0.1

                        logger.debug(
                            f"[CHITTA] {symbol}: Vote adj {chitta_adjustment:+.3f}, Threshold adj {chitta_threshold_adj:+.3f} "
                            f"(WR: {win_rate:.1%}, n={total})"
                        )
                except Exception as e:
                    logger.warning(f"[CHITTA] Failed to adjust based on experiences: {e}")

            # Apply Chitta adjustments
            total_vote += chitta_adjustment
            effective_threshold += chitta_threshold_adj

            # ============================================================
            # 7c. RAG PLAYBOOK INJECTION (Taak 3.2)
            # ============================================================
            rag_adjustment = 0.0
            rag_context = ""

            if self.use_rag and self.chroma_collection:
                try:
                    rag_adjustment, rag_context = await self._query_rag_playbook(symbol, regime)
                    total_vote += rag_adjustment

                    if abs(rag_adjustment) > 0.01:
                        logger.info(
                            f"[RAG] {symbol}: Adjusted by {rag_adjustment:+.3f} based on playbook: {rag_context[:50]}..."
                        )
                except Exception as e:
                    logger.warning(f"[RAG] Failed to inject playbook context: {e}")

            # Bereken dominant agent (hoogste gewogen bijdrage)
            weighted_votes = {
                "VEDASTRO": vedastro_vote_adjusted * weights["vedastro"],
                "EARTH": earth_vote * weights["earth"],
                "FIRE": fire_vote * weights["fire"],
                "WATER": water_vote * weights["water"],
            }
            dominant_agent = max(weighted_votes, key=weighted_votes.get)

            analysis["consensus"] = {
                "vedastro_vote_raw": vedastro_vote,
                "vedastro_vote_adjusted": vedastro_vote_adjusted,
                "guna_multiplier": guna_multiplier,
                "earth_vote": earth_vote,
                "fire_vote": fire_vote,
                "water_vote": water_vote,
                "weights": weights,
                "regime": regime,
                "raw_consensus": raw_consensus,
                "vayu_dampener": vayu_dampener,
                "total_vote": total_vote,
                "threshold": effective_threshold,
                "base_threshold": base_threshold,
                "passed": total_vote >= effective_threshold,
                "dominant_agent": dominant_agent,
                "weighted_votes": weighted_votes,
            }

            logger.info(
                f"[CONSENSUS] {symbol}: {total_vote:.2f} (raw:{raw_consensus:.2f}) | "
                f"Regime:{regime} | Threshold:{effective_threshold:.2f} | "
                f"Dominant:{dominant_agent} | Vayu:{vayu_dampener:.1f}"
            )

            # --- COGNITIVE AUDIT LOGGING ---
            if hasattr(self, "cognitive_logger"):
                cog_decision = "BUY" if total_vote >= effective_threshold else "SKIP"
                await self.cognitive_logger.log_decision(
                    symbol=symbol,
                    regime=regime,
                    engine_signal=signal,
                    rag_insights=rag_insights,
                    vedastro_vote=vedastro_vote,
                    rag_adjustment=rag_adjustment,
                    final_decision=cog_decision,
                )

                # Broadcast to frontend via WebSocket (non-blocking)
                try:
                    from backend.services.paper_trading_ws_broadcast import (
                        broadcast_cognitive_insight,
                    )

                    recent = self.cognitive_logger.get_recent_decisions(limit=1)
                    if recent:
                        await broadcast_cognitive_insight(recent[0])
                except Exception as ws_err:
                    logger.debug(f"[WS] Cognitive broadcast skipped: {ws_err}")

            # Check of consensus sterk genoeg is (gebruik effective_threshold!)
            if total_vote < effective_threshold:
                analysis["decision"] = {
                    "action": "SKIP",
                    "reason": f"Consensus too weak ({total_vote:.2f} < {effective_threshold:.2f})",
                    "entry_type": None,
                    "dominant_agent": dominant_agent,
                }
                await self._log_analysis(analysis)

                # Broadcast hold decision to frontend
                await broadcast_agent_decision(
                    agent="V18_Elemental",
                    strategy="vedastro_consensus",
                    symbol=symbol,
                    decision="HOLD",
                    confidence=total_vote,
                    reason=f"Consensus {total_vote:.2f} < threshold {effective_threshold:.2f} | VedAstro:{vedastro_vote:.2f} | Earth:{earth_vote:.2f} | Fire:{fire_vote:.2f} | Regime:{regime}",
                    executed=False,
                )
                return False

            # ============================================================
            # 7. SLIPPAGE & EXECUTION CHECK (Phase 5)
            # ============================================================
            intended_price = current_price
            expected_slippage_pct = 0.001  # Default 0.1% for liquid pairs

            # If live, try to get real spread for better slippage estimation
            if self.config.live_mode:
                try:
                    from backend.execution.bitvavo_adapter import BitvavoAdapter

                    bitvavo = BitvavoAdapter()
                    if await bitvavo.initialize():
                        book = await bitvavo.fetch_order_book(symbol, limit=5)
                        if book and book["bids"] and book["asks"]:
                            spread = (book["asks"][0][0] - book["bids"][0][0]) / intended_price
                            # We use a 1.5x multiplier for spread to estimate slippage
                            expected_slippage_pct = max(0.001, (spread / 2) * 1.5)
                        await bitvavo.close()
                except Exception as e:
                    logger.warning(f"[SLIPPAGE] Could not fetch real book for {symbol}: {e}")

            # CALCULATE PROFIT TO SLIPPAGE RATIO
            # We assume a base profit target of 1.5% for V18 elemental entries
            expected_profit_pct = 0.015
            if strength_score > 70:
                expected_profit_pct = 0.025

            if expected_profit_pct < (
                expected_slippage_pct * self.config.min_profit_to_slippage_ratio
            ):
                logger.warning(
                    f"[SKIP-SLIPPAGE] {symbol}: Profit ({expected_profit_pct:.2%}) "
                    f"< Slippage ({expected_slippage_pct:.2%}) * {self.config.min_profit_to_slippage_ratio}"
                )
                analysis["decision"] = {"action": "SKIP", "reason": "high_slippage_risk"}
                await self._log_analysis(analysis)
                return False

            # ============================================================
            # 7. POSITION SIZING met Constraints
            # ============================================================
            max_position = min(
                self.state.total_value * self.config.max_position_pct,  # 2%
                self.config.max_position_eur,  # €2000
            )

            # Scale by consensus strength
            position_size = min(position_size, max_position)
            position_size = position_size * min(1.0, total_vote)

            # Apply minimum
            if position_size < 50:
                analysis["decision"] = {
                    "action": "SKIP",
                    "reason": f"Position too small (€{position_size:.2f} < €50)",
                }
                await self._log_analysis(analysis)

                # Broadcast hold decision to frontend
                await broadcast_agent_decision(
                    agent="V18_Elemental",
                    strategy="vedastro_consensus",
                    symbol=symbol,
                    decision="HOLD",
                    confidence=total_vote,
                    reason=f"Position too small (€{position_size:.2f} < €50)",
                    executed=False,
                )
                return False

            analysis["position_sizing"] = {
                "raw_size": (
                    fire_result.get("position_size_eur", 0) if "fire_result" in locals() else 0
                ),
                "max_allowed": max_position,
                "consensus_scaled": position_size,
                "final_size": position_size,
            }

            # ============================================================
            # 8. EXECUTE TRADE - DIRECT CALL
            # ============================================================
            # Check Execution Guard (Taak 2.2)
            allowed, reason = self.guard.check_order(
                symbol=symbol,
                side="BUY",
                size_eur=position_size,
                current_portfolio_value=self.state.total_value,
                open_positions_count=len(self.state.open_positions),
            )

            if not allowed:
                analysis["decision"] = {
                    "action": "GUARD_BLOCK",
                    "reason": f"Execution Guard rejected: {reason}",
                }
                await self._log_analysis(analysis)
                logger.warning(f"[GUARD] {symbol}: ORDER REJECTED - {reason}")
                return False

            # POSITION SIZING - Hardcoded to €5 for Live Mode per user instructions
            if self.config.live_mode:
                final_size_eur = 5.0
            else:
                final_size_eur = position_size

            quantity = final_size_eur / intended_price

            if self.config.live_mode:
                # REAL BITVAVO EXECUTION
                try:
                    from backend.execution.bitvavo_adapter import BitvavoAdapter

                    bitvavo = BitvavoAdapter()
                    if await bitvavo.initialize():
                        # Market orders on Bitvavo
                        res = await bitvavo.create_market_order(symbol, "buy", quantity)
                        if res:
                            actual_price = res.get("price") or intended_price
                            quantity = res.get("amount") or quantity
                            actual_slippage = (actual_price - intended_price) / intended_price
                            result = {
                                "status": "FILLED",
                                "price": actual_price,
                                "amount": quantity,
                                "slippage": actual_slippage,
                                "commission": res.get("fee", final_size_eur * 0.0025),
                            }
                        else:
                            result = {"status": "FAILED"}
                        await bitvavo.close()
                    else:
                        result = {"status": "FAILED"}
                except Exception as e:
                    logger.error(f"[LIVE-ERR] {e}")
                    result = {"status": "ERROR", "message": str(e)}
            else:
                # SHADOW EXECUTION
                result = await execution_execute_paper_trade(
                    symbol=symbol,
                    action="BUY",
                    quantity=quantity,
                    current_price=intended_price,
                    account_id=self.config.account_id,
                )

            if result.get("status") != "FILLED":
                analysis["decision"] = {
                    "action": "SKIP",
                    "reason": f"Trade not filled ({result.get('status', 'UNKNOWN')})",
                }
                await self._log_analysis(analysis)
                logger.warning(f"{symbol}: Trade not filled - {result.get('status')}")
                return False

            # 9. UPDATE STATE & LOG ANALYTICS
            # ============================================================
            current_price = result.get("price", intended_price)
            actual_slippage = result.get("slippage") or (
                (current_price - intended_price) / intended_price if intended_price > 0 else 0
            )

            cost = quantity * current_price
            commission = result.get("commission", cost * 0.0025)

            self.state.cash -= cost + commission
            self.state.open_positions[symbol] = {
                "entry_date": datetime.utcnow().isoformat(),
                "entry_price": current_price,
                "intended_price": intended_price,
                "slippage_pct": actual_slippage,
                "quantity": quantity,
                "position_size": final_size_eur,
                "commission": commission,
            }
            self.peak_prices[symbol] = current_price

            trade = {
                "timestamp": datetime.utcnow().isoformat(),
                "symbol": symbol,
                "side": "buy",
                "qty": quantity,
                "price": current_price,
                "intended_price": intended_price,
                "slippage_pct": actual_slippage,
                "value": final_size_eur,
                "agent": "V18_Elemental",
                "exchange": "Bitvavo",
                "commission": commission,
                "vedastro_confidence": confidence,
                "vedastro_score": strength_score,
                "dominant_planet": dominant_planet,
                "type": "entry",
            }

            self.state.trades.append(trade)
            self.state.total_trades += 1

            # Save to database if enabled
            if self.use_database and self.db:
                try:
                    async with self.db:
                        db_trade = {
                            "session_id": self.session_id,
                            "symbol": symbol,
                            "side": "buy",
                            "quantity": quantity,
                            "price": current_price,
                            "intended_price": trade.get("intended_price"),
                            "slippage_pct": trade.get("slippage_pct"),
                            "value": position_size,
                            "commission": commission,
                            "agent": "V18_Elemental",
                            "strategy": "vedastro_consensus",
                            "consensus_score": total_vote,
                            "dominant_agent": dominant_agent,
                            "entry_type": entry_type,
                            "vedastro_signal": signal_upper,
                            "vedastro_confidence": confidence,
                            "vedastro_score": strength_score,
                            "dominant_planet": dominant_planet,
                            "elemental_votes": {
                                "earth": earth_vote,
                                "fire": fire_vote,
                                "water": water_vote,
                            },
                            "regime": regime,
                            "trade_type": "entry",
                            "exchange": "Bitvavo",
                            "rag_context": analysis.get("rag", {}),
                            "analysis_data": analysis,
                        }
                        await self.db.save_trade(db_trade)
                        logger.debug(f"[DB] Saved entry trade for {symbol}")
                except Exception as e:
                    logger.error(f"[DB] Failed to save entry trade: {e}")

            # Record for Earth element tracking
            if symbol not in self.trade_history:
                self.trade_history[symbol] = []

            # Finalize analysis log met entry type en dominant agent
            # Entry type bepalen: HARD = consensus > 0.6, SOFT = 0.3-0.6
            entry_type = "HARD" if total_vote >= 0.6 else "SOFT"

            analysis["decision"] = {
                "action": "BUY",
                "entry_type": entry_type,
                "dominant_agent": dominant_agent,
                "quantity": quantity,
                "entry_price": current_price,
                "position_size": position_size,
                "commission": commission,
                "consensus": total_vote,
                "raw_consensus": raw_consensus,
                "vayu_dampener": vayu_dampener,
                "regime": regime,
            }
            await self._log_analysis(analysis)

            # ============================================================
            # 10. BROADCAST RESULTS
            # ============================================================
            await broadcast_trade(trade)
            await broadcast_agent_decision(
                agent="V18_Elemental",
                strategy="vedastro_consensus",
                symbol=symbol,
                decision="BUY",
                confidence=confidence / 100,
                reason=f"Consensus {total_vote:.2f} | VedAstro:{vedastro_vote:.2f} | Earth:{earth_vote:.2f} | Fire:{fire_vote:.2f} | {dominant_planet}",
                executed=True,
            )

            logger.info(
                f"[ENTRY] {symbol} {quantity:.4f} @ EUR {current_price:.2f} (Size: EUR {position_size:.2f}, Consensus: {total_vote:.2f})"
            )

            return True

        except Exception as e:
            logger.error(f"Error evaluating entry for {symbol}: {e}", exc_info=True)
            analysis["error"] = str(e)
            await self._log_analysis(analysis)
            return False

    async def _evaluate_exit(self, symbol: str, current_price: float) -> bool:
        """Evaluate exit - AGENTIC CONSENSUS met EARTH HARD VETO.

        Exit filosofie:
        1. EARTH heeft ABSOLUUTE VETO op -7% stop loss (kapitaalbescherming)
        2. Daarnaast: multi-agent consensus voor "soft" exits (take profit, trailing stop)
        3. VedAstro kan adviseren maar niet blokkeren (anders blijf je eeuig zitten)
        """
        try:
            position = self.state.open_positions.get(symbol)
            if not position:
                return False

            entry_price = position["entry_price"]
            quantity = position["quantity"]
            position_size = position["position_size"]

            # Update peak price
            if symbol not in self.peak_prices:
                self.peak_prices[symbol] = entry_price

            if current_price > self.peak_prices[symbol]:
                self.peak_prices[symbol] = current_price

            peak_price = self.peak_prices[symbol]
            unrealized_pnl_pct = (current_price - entry_price) / entry_price

            # ============================================================
            # 1. EARTH HARD VETO (-7% stop loss is ABSOLUUT)
            # ============================================================
            if unrealized_pnl_pct <= -0.07:
                logger.warning(
                    f"[EXIT-HARD] {symbol}: STOP LOSS triggered ({unrealized_pnl_pct*100:+.1f}%) - Earth VETO"
                )
                reason_str = f"HARD_STOP_LOSS ({unrealized_pnl_pct*100:+.1f}%)"
                return await self._execute_exit(
                    symbol,
                    current_price,
                    quantity,
                    position_size,
                    reason_str,
                    is_hard_exit=True,
                )

            # ============================================================
            # 2. EARTH SOFT CHECK (trailing stop, time stop)
            # ============================================================
            earth_result = await elemental_earth_exit_check(
                symbol=symbol,
                entry_date=position["entry_date"],
                current_date=datetime.utcnow().isoformat(),
                entry_price=entry_price,
                current_price=current_price,
                peak_price=peak_price,
            )

            earth_exit_vote = 0.5 if earth_result.get("should_exit", False) else 0.0
            earth_reasons = earth_result.get("exit_reasons", [])

            # ============================================================
            # 3. VEDASTRO EXIT ADVIES (maar geen veto!)
            # ============================================================
            vedastro_exit_vote = 0.0
            try:
                vedastro_result = await vedastro_generate_signal(
                    symbol=symbol, current_price=current_price
                )
                signal = vedastro_result.get("signal", "HOLD").upper()
                confidence = vedastro_result.get("confidence", 0)

                # VedAstro adviseert exit bij SELL/STRONG_SELL
                if "SELL" in signal:
                    vedastro_exit_vote = 0.6 * (confidence / 100)
                elif signal == "HOLD" and unrealized_pnl_pct > 0.05:
                    # Neutrale VedAstro + winst = consider exit
                    vedastro_exit_vote = 0.2

                logger.debug(f"[EXIT-VEDASTRO] {symbol}: {signal} (vote={vedastro_exit_vote:.2f})")
            except Exception as e:
                logger.warning(f"[EXIT-VEDASTRO] {symbol}: Failed ({e})")
                vedastro_exit_vote = 0.0

            # ============================================================
            # 4. FIRE EXIT (momentum/heat verdwijnt)
            # ============================================================
            fire_exit_vote = 0.0
            try:
                # Als prijs >5% van peak teruggevallen = momentum verdwijnt
                drawdown_from_peak = (
                    (peak_price - current_price) / peak_price if peak_price > 0 else 0
                )
                if drawdown_from_peak > 0.05:
                    fire_exit_vote = min(0.8, drawdown_from_peak * 10)  # 5% = 0.5, 10% = 0.8
                    logger.debug(
                        f"[EXIT-FIRE] {symbol}: Momentum loss {drawdown_from_peak*100:.1f}% (vote={fire_exit_vote:.2f})"
                    )
            except Exception as e:
                logger.warning(f"[EXIT-FIRE] {symbol}: Failed ({e})")

            # ============================================================
            # 5. EXIT CONSENSUS BEREKENEN
            # ============================================================
            # Get regime for analytics and performance tracking
            regime = "unknown"
            if len(price_history) >= 20:
                try:
                    water_result = await elemental_water_regime_check(
                        symbol=symbol, prices=price_history
                    )
                    regime = water_result.get("regime", "unknown")
                except Exception as e:
                    logger.warning(f"[EXIT-regime] {symbol}: Failed ({e})")

            # Earth heeft meer gewicht bij exits (40%) - kapitaalbescherming!
            # VedAstro heeft minder (25%) - mag adviseren maar niet blokkeren
            exit_consensus = (
                (earth_exit_vote * 0.40) + (vedastro_exit_vote * 0.25) + (fire_exit_vote * 0.35)
            )

            logger.info(
                f"[EXIT-CONSENSUS] {symbol}: {exit_consensus:.2f} (E:{earth_exit_vote:.2f}|V:{vedastro_exit_vote:.2f}|F:{fire_exit_vote:.2f}) | Regime: {regime}"
            )

            if exit_consensus < 0.4:  # Hogere drempel voor exit dan entry
                return False

            reason_str = f"CONSENSUS_EXIT ({exit_consensus:.2f}) | Earth: {', '.join(earth_reasons) if earth_reasons else 'OK'}"
            return await self._execute_exit(
                symbol,
                current_price,
                quantity,
                position_size,
                reason_str,
                is_hard_exit=False,
                regime=regime,
            )

        except Exception as e:
            logger.error(f"Error evaluating exit for {symbol}: {e}", exc_info=True)
            return False

    async def _execute_exit(
        self,
        symbol: str,
        intended_price: float,
        quantity: float,
        position_size: float,
        reason: str,
        is_hard_exit: bool = False,
        regime: str = "unknown",
    ) -> bool:
        """Execute exit trade and update state."""
        try:
            if self.config.live_mode:
                # REAL BITVAVO EXIT
                try:
                    from backend.execution.bitvavo_adapter import BitvavoAdapter

                    bitvavo = BitvavoAdapter()
                    if await bitvavo.initialize():
                        # Close the entire position on Bitvavo
                        res = await bitvavo.create_market_order(symbol, "sell", quantity)
                        if res:
                            executed_price = res.get("price") or intended_price
                            quantity = res.get("amount") or quantity
                            actual_slippage = (
                                (intended_price - executed_price) / intended_price
                                if intended_price > 0
                                else 0
                            )
                            result = {
                                "status": "FILLED",
                                "price": executed_price,
                                "amount": quantity,
                                "slippage": actual_slippage,
                                "commission": res.get("fee", (quantity * executed_price) * 0.0025),
                            }
                        else:
                            result = {"status": "FAILED"}
                        await bitvavo.close()
                    else:
                        result = {"status": "FAILED"}
                except Exception as e:
                    logger.error(f"[LIVE-EXIT-ERR] {e}")
                    result = {"status": "ERROR"}
            else:
                # SHADOW EXIT
                result = await execution_execute_paper_trade(
                    symbol=symbol,
                    action="SELL",
                    quantity=quantity,
                    current_price=intended_price,
                    account_id=self.config.account_id,
                )

            if result.get("status") != "FILLED":
                logger.warning(
                    f"[EXIT] {symbol}: Trade not filled - {result.get('status', 'UNKNOWN')}"
                )
                return False

            current_price = result.get("price", intended_price)
            actual_slippage = result.get("slippage") or (
                (intended_price - current_price) / intended_price if intended_price > 0 else 0
            )

            # Calculate P&L
            proceeds = quantity * current_price
            commission = result.get("commission", proceeds * 0.0005)
            net_proceeds = proceeds - commission

            cost_basis = position_size + (position_size * 0.0005)  # Approx commission
            pnl = net_proceeds - cost_basis
            pnl_pct = pnl / cost_basis if cost_basis > 0 else 0

            # Update state
            self.state.cash += net_proceeds
            del self.state.open_positions[symbol]
            if symbol in self.peak_prices:
                del self.peak_prices[symbol]

            trade = {
                "timestamp": datetime.utcnow().isoformat(),
                "symbol": symbol,
                "side": "sell",
                "qty": quantity,
                "price": current_price,
                "value": proceeds,
                "agent": "V18_Elemental",
                "exchange": "Bitvavo",
                "commission": commission,
                "pnl": pnl,
                "pnl_pct": pnl_pct,
                "reason": reason,
                "type": "exit",
                "hard_exit": is_hard_exit,
                "regime": regime,
            }

            self.state.trades.append(trade)
            self.state.total_trades += 1
            self.state.total_pnl += pnl

            # Update Execution Guard with result (Taak 2.2)
            self.guard.record_trade_result(pnl)

            # Record Experience in Chitta (Taak 3.3)
            if self.use_chitta and self.chitta:
                try:
                    from backend.core.conscious.chitta_memory import TradeExperience

                    experience = TradeExperience(
                        trade_id=str(result.get("order_id", datetime.utcnow().timestamp())),
                        timestamp=datetime.utcnow().isoformat(),
                        symbol=symbol,
                        side="sell",
                        entry_price=cost_basis / quantity if quantity > 0 else 0,
                        exit_price=current_price,
                        size=quantity,
                        net_pnl=pnl,
                        return_pct=pnl_pct,
                        bars_held=0,  # Simplified
                        market_regime=regime,
                        trend_1d=0.0,  # Placeholder
                        adx=0.0,
                        rsi=0.0,
                        volatility=0.0,
                        harmony_score=0.0,
                        confidence=0.0,
                        coherence=0.0,
                        dominant_element="unknown",
                        guna_dominant="unknown",
                        is_maya=False,
                        exit_reason=reason,
                    )
                    await self.chitta.record_experience(experience)
                    logger.info(f"[CHITTA] {symbol}: Experience recorded (PnL: {pnl:+.2f})")
                except Exception as e:
                    logger.warning(f"[CHITTA] Failed to record experience: {e}")

            # Record for Earth element
            win = pnl > 0
            if symbol not in self.trade_history:
                self.trade_history[symbol] = []
            self.trade_history[symbol].append(
                {"pnl": pnl_pct, "win": win, "timestamp": datetime.utcnow().isoformat()}
            )

            # Save to database if enabled
            if self.use_database and self.db:
                try:
                    async with self.db:
                        # Save exit trade
                        db_trade = {
                            "session_id": self.session_id,
                            "symbol": symbol,
                            "side": "sell",
                            "quantity": quantity,
                            "price": current_price,
                            "value": proceeds,
                            "commission": commission,
                            "pnl": pnl,
                            "pnl_pct": pnl_pct,
                            "agent": "V18_Elemental",
                            "strategy": "exit_manager",
                            "trade_type": "exit",
                            "exit_reason": reason,
                            "is_hard_exit": is_hard_exit,
                            "exchange": "Bitvavo",
                            "regime": regime,
                        }
                        await self.db.save_trade(db_trade)

                        # Update agent performance
                        await self.db.update_agent_performance(
                            agent="V18_Elemental",
                            symbol=symbol,
                            regime=regime,
                            pnl=pnl,
                            was_win=win,
                        )

                        # Save experience for Chitta learning
                        if self.use_chitta and self.chitta:
                            try:
                                from backend.core.conscious.chitta_memory import TradeExperience

                                experience = TradeExperience(
                                    trade_id=f"{self.session_id}_{symbol}_{datetime.utcnow().timestamp()}",
                                    timestamp=datetime.utcnow().isoformat(),
                                    symbol=symbol,
                                    side="sell",
                                    entry_price=(position_size / quantity if quantity > 0 else 0),
                                    exit_price=current_price,
                                    size=quantity,
                                    net_pnl=pnl,
                                    return_pct=pnl_pct,
                                    bars_held=0,  # Could calculate this
                                    market_regime="unknown",
                                    trend_1d=0.0,
                                    adx=0.0,
                                    rsi=0.0,
                                    volatility=0.0,
                                    harmony_score=0.5,
                                    confidence=0.9 if is_hard_exit else 0.7,
                                    coherence=0.5,
                                    dominant_element=("EARTH" if is_hard_exit else "CONSENSUS"),
                                    guna_dominant="rajas",
                                    is_maya=False,
                                    exit_reason=reason,
                                    max_favorable_excursion=0.0,
                                    max_adverse_excursion=(-0.07 if is_hard_exit else 0.0),
                                )
                                await self.chitta.add_experience(experience)
                                logger.debug(f"[CHITTA] Saved experience for {symbol}")
                            except Exception as e:
                                logger.error(f"[CHITTA] Failed to save experience: {e}")

                        logger.debug(f"[DB] Saved exit trade for {symbol}")
                except Exception as e:
                    logger.error(f"[DB] Failed to save exit trade: {e}")

            # Log exit analytics
            exit_log = {
                "timestamp": datetime.utcnow().isoformat(),
                "symbol": symbol,
                "type": "EXIT",
                "exit_type": "HARD" if is_hard_exit else "CONSENSUS",
                "price": current_price,
                "pnl": pnl,
                "pnl_pct": pnl_pct,
                "reason": reason,
                "portfolio_value": self.state.total_value,
                "cash": self.state.cash,
            }
            await self._log_analysis(exit_log)

            # Broadcast
            await broadcast_trade(trade)
            await broadcast_agent_decision(
                agent="V18_Elemental",
                strategy="exit_manager",
                symbol=symbol,
                decision="SELL",
                confidence=0.9 if is_hard_exit else 0.7,
                reason=reason,
                executed=True,
            )

            exit_type_str = "HARD" if is_hard_exit else "SOFT"
            logger.info(
                f"[EXIT-{exit_type_str}] {symbol} {quantity:.4f} @ EUR {current_price:.2f} (P&L: {pnl_pct*100:+.2f}%) [{reason}]"
            )

            return True

        except Exception as e:
            logger.error(f"[EXIT] Error executing exit for {symbol}: {e}", exc_info=True)
            return False

    async def _calculate_portfolio_value(self, prices: dict[str, Any]) -> float:
        """Calculate total portfolio value."""
        value = self.state.cash

        for symbol, position in self.state.open_positions.items():
            if symbol in prices:
                price = prices[symbol].price
                qty = position["quantity"]
                value += qty * price

        return value

    def _get_dominant_planet(self, date: datetime) -> str:
        """Get dominant planet for date."""
        planets = ["SUN", "MOON", "MARS", "MERCURY", "JUPITER", "VENUS", "SATURN"]
        return planets[date.day % 7]

    def _create_fallback_embedding(self, text: str, dim: int = 384) -> list[float]:
        """
        Create a simple deterministic embedding from text.
        Used when sentence-transformers is not available.
        """
        import hashlib

        # Create deterministic hash-based embedding
        hash_val = hashlib.md5(text.encode(), usedforsecurity=False).hexdigest()

        # Generate embedding values from hash
        embedding = []
        for i in range(dim):
            # Use different parts of hash for each dimension
            hash_byte = int(hash_val[i % 32], 16)
            # Normalize to [-1, 1] range
            val = (hash_byte / 15.0) * 2 - 1
            # Add some variation based on position
            val += (i / dim) * 0.1
            embedding.append(float(val))

        # Normalize to unit vector
        import math

        norm = math.sqrt(sum(x**2 for x in embedding))
        if norm > 0:
            embedding = [x / norm for x in embedding]

        return embedding

    async def _status_reporter(self, interval: int = 60):
        """Periodically report status."""
        while self.running:
            try:
                await asyncio.sleep(interval)

                if not self.data_agent:
                    continue

                prices = await self.data_agent.get_all_prices()
                portfolio_value = await self._calculate_portfolio_value(prices)
                elapsed = datetime.utcnow() - self.start_time if self.start_time else timedelta(0)

                pnl = portfolio_value - self.config.initial_cash
                pnl_pct = (pnl / self.config.initial_cash) * 100

                print()
                print("=" * 80)
                print(f"STATUS | Elapsed: {elapsed} | Cycles: {self._cycle_count}")
                print(
                    f"       | Trades: {self.state.total_trades} | Positions: {len(self.state.open_positions)}"
                )
                print(
                    f"       | Portfolio: EUR {portfolio_value:,.2f} | P&L: EUR {pnl:+,.2f} ({pnl_pct:+.2f}%)"
                )
                print(f"       | Cash: EUR {self.state.cash:,.2f} | Cache: {len(prices)} prices")
                print("=" * 80)

            except Exception as e:
                logger.error(f"Status reporter error: {e}")

    async def _broadcast_stats(self):
        """Broadcast current stats."""
        try:
            await broadcast_stats(
                {
                    "total_trades": self.state.total_trades,
                    "open_positions": len(self.state.open_positions),
                    "cash": self.state.cash,
                    "portfolio_value": self.state.total_value,
                    "total_pnl": self.state.total_pnl,
                    "cycle": self._cycle_count,
                }
            )
        except Exception as e:
            logger.debug(f"Broadcast error: {e}")

    async def _query_rag_playbook(self, symbol: str, regime: str) -> tuple[float, str]:
        """
        Query ChromaDB for strategic playbooks and return adjustment factor.
        Taak 3.2: RAG Playbook Injection
        """
        if not self.chroma_collection:
            return 0.0, ""

        try:
            query_text = f"Trading playbook and strategy for {symbol} in {regime} market regime"

            # Generate embedding
            if self.rag_embedding_model:
                query_embeddings = [self.rag_embedding_model.encode(query_text).tolist()]
                results = self.chroma_collection.query(
                    query_embeddings=query_embeddings, n_results=2
                )
            else:
                # Fallback to simple query if no model
                results = self.chroma_collection.query(query_texts=[query_text], n_results=2)

            if not results or not results["documents"] or not results["documents"][0]:
                return 0.0, ""

            adjustment = 0.0
            contexts = []

            for doc in results["documents"][0]:
                doc_upper = doc.upper()
                contexts.append(doc[:100])  # Store snippet

                # Simple sentiment/instruction check
                if any(
                    k in doc_upper for k in ["BULLISH", "BUY", "STRONG", "GROWTH", "ACCUMULATE"]
                ):
                    adjustment += 0.03
                if any(
                    k in doc_upper
                    for k in ["BEARISH", "SELL", "AVOID", "RISK", "DANGER", "DOWNTREND"]
                ):
                    adjustment -= 0.03
                if "DO NOT TRADE" in doc_upper or "STAY AWAY" in doc_upper:
                    adjustment -= 0.1

            # Cap the RAG adjustment to ±0.06 (two strong signals)
            adjustment = max(-0.1, min(0.1, adjustment))

            return adjustment, " | ".join(contexts)

        except Exception as e:
            logger.error(f"[RAG-QUERY] Failed for {symbol}: {e}")
            return 0.0, ""

    async def _log_analysis(self, analysis: dict[str, Any]):
        """Log detailed analysis for post-session analytics.

        Writes to:
        - JSONL files (for quick access)
        - Database (for querying and aggregation)
        """
        try:
            # Create analytics directory if not exists
            log_dir = Path("paper_trading_analytics")
            log_dir.mkdir(exist_ok=True)

            # Get session date for filename
            session_date = (
                self.start_time.strftime("%Y%m%d")
                if self.start_time
                else datetime.utcnow().strftime("%Y%m%d")
            )

            # Write to both detailed and summary logs
            detailed_file = log_dir / f"v18_analytics_{session_date}.jsonl"
            summary_file = log_dir / f"v18_summary_{session_date}.json"

            # Append detailed analysis (JSONL format)
            with open(detailed_file, "a") as f:
                f.write(json.dumps(analysis, default=str) + "\n")

            # Also save to database if enabled
            if self.use_database and self.db:
                try:
                    # Filter: only save relevant signals to database (Taak 1.2)
                    # 1. Any trade execution (entry/exit)
                    # 2. Consensus > 0
                    # 3. "Almost-pass" (threshold - 0.1)
                    total_vote = analysis.get("consensus", {}).get("total_vote", 0)
                    threshold = analysis.get("consensus", {}).get("threshold", 0.35)
                    action = analysis.get("decision", {}).get("action")
                    is_trade = action in ["BUY", "SELL", "EXIT"]
                    is_relevant = total_vote > 0 or total_vote >= (threshold - 0.1)

                    if is_trade or is_relevant:
                        # Prepare analytics data for database
                        db_analysis = {
                            "session_id": self.session_id,
                            "cycle": analysis.get("cycle", self._cycle_count),
                            "symbol": analysis.get("symbol", "UNKNOWN"),
                            "analysis_type": (
                                "entry" if action == "BUY" else "exit" if is_trade else "analysis"
                            ),
                            "current_price": analysis.get("current_price", 0),
                            "vedastro_signal": analysis.get("vedastro", {}).get("signal"),
                            "vedastro_confidence": analysis.get("vedastro", {}).get("confidence"),
                            "vedastro_score": analysis.get("vedastro", {}).get("strength_score"),
                            "vedastro_vote": analysis.get("vedastro", {}).get("vote"),
                            "dominant_planet": analysis.get("vedastro", {}).get("dominant_planet"),
                            "earth_vote": analysis.get("elemental", {})
                            .get("earth", {})
                            .get("vote"),
                            "earth_can_enter": analysis.get("elemental", {})
                            .get("earth", {})
                            .get("can_enter"),
                            "fire_vote": analysis.get("elemental", {}).get("fire", {}).get("vote"),
                            "fire_position_size": analysis.get("elemental", {})
                            .get("fire", {})
                            .get("position_size_raw"),
                            "water_vote": analysis.get("elemental", {})
                            .get("water", {})
                            .get("vote"),
                            "water_regime": analysis.get("elemental", {})
                            .get("water", {})
                            .get("regime"),
                            "sattva": analysis.get("gunas", {}).get("sattva"),
                            "rajas": analysis.get("gunas", {}).get("rajas"),
                            "tamas": analysis.get("gunas", {}).get("tamas"),
                            "guna_multiplier": analysis.get("gunas", {}).get("multiplier"),
                            "vayu_dampener": analysis.get("vayu", {}).get("dampener"),
                            "vayu_sentiment": analysis.get("vayu", {}).get("sentiment"),
                            "total_vote": total_vote,
                            "raw_consensus": analysis.get("consensus", {}).get("raw_consensus"),
                            "threshold": threshold,
                            "passed": analysis.get("consensus", {}).get("passed", False),
                            "dominant_agent": analysis.get("consensus", {}).get("dominant_agent"),
                            "portfolio_value": self.state.total_value,
                            "cash": self.state.cash,
                            "open_positions_count": len(self.state.open_positions),
                            "action": action,
                            "decision_reason": analysis.get("decision", {}).get("reason"),
                            "full_analysis": analysis,
                        }
                        # Add to batch list for Taak 1.2
                        self._cycle_analytics.append(db_analysis)

                except Exception as e:
                    logger.error(f"[DB-BUFFER] Failed to buffer analytics: {e}")

            # Update summary stats
            summary = {}
            if summary_file.exists():
                with open(summary_file) as f:
                    try:
                        summary = json.load(f)
                    except json.JSONDecodeError:
                        summary = {}

            # Update counters
            symbol = analysis.get("symbol", "UNKNOWN")
            decision = analysis.get("decision", {}).get("action", "UNKNOWN")
            consensus = analysis.get("consensus", {})

            if "symbols" not in summary:
                summary["symbols"] = {}
            if symbol not in summary["symbols"]:
                summary["symbols"][symbol] = {"evaluations": 0, "trades": 0}

            summary["symbols"][symbol]["evaluations"] += 1
            if decision == "BUY":
                summary["symbols"][symbol]["trades"] += 1

            # Track consensus distribution
            if "consensus_distribution" not in summary:
                summary["consensus_distribution"] = {
                    "total": 0,
                    "strong_buy": 0,  # >= 0.6
                    "buy": 0,  # 0.3 - 0.6
                    "neutral": 0,  # -0.3 - 0.3
                    "sell": 0,  # < -0.3
                }

            total_vote = consensus.get("total_vote", 0)
            summary["consensus_distribution"]["total"] += 1
            if total_vote >= 0.6:
                summary["consensus_distribution"]["strong_buy"] += 1
            elif total_vote >= 0.3:
                summary["consensus_distribution"]["buy"] += 1
            elif total_vote >= -0.3:
                summary["consensus_distribution"]["neutral"] += 1
            else:
                summary["consensus_distribution"]["sell"] += 1

            # Track agent contributions
            if "agent_contributions" not in summary:
                summary["agent_contributions"] = {
                    "vedastro": {"buy": 0, "neutral": 0, "sell": 0},
                    "earth": {"allow": 0, "block": 0},
                    "fire": {"sizing_avg": 0, "count": 0},
                    "water": {"expansion": 0, "contraction": 0, "neutral": 0},
                }

            vedastro = analysis.get("vedastro", {})
            earth = analysis.get("elemental", {}).get("earth", {})
            fire = analysis.get("elemental", {}).get("fire", {})
            water = analysis.get("elemental", {}).get("water", {})

            # VedAstro signal tracking
            v_signal = vedastro.get("signal", "HOLD").upper()
            if "BUY" in v_signal:
                summary["agent_contributions"]["vedastro"]["buy"] += 1
            elif "SELL" in v_signal:
                summary["agent_contributions"]["vedastro"]["sell"] += 1
            else:
                summary["agent_contributions"]["vedastro"]["neutral"] += 1

            # Earth tracking
            if earth.get("can_enter", True):
                summary["agent_contributions"]["earth"]["allow"] += 1
            else:
                summary["agent_contributions"]["earth"]["block"] += 1

            # Fire tracking
            pos_size = fire.get("position_size_raw", 0)
            if pos_size > 0:
                current_avg = summary["agent_contributions"]["fire"]["sizing_avg"]
                current_count = summary["agent_contributions"]["fire"]["count"]
                new_count = current_count + 1
                new_avg = ((current_avg * current_count) + pos_size) / new_count
                summary["agent_contributions"]["fire"]["sizing_avg"] = new_avg
                summary["agent_contributions"]["fire"]["count"] = new_count

            # Water tracking
            regime = water.get("regime", "neutral")
            if regime == "expansion":
                summary["agent_contributions"]["water"]["expansion"] += 1
            elif regime == "contraction":
                summary["agent_contributions"]["water"]["contraction"] += 1
            else:
                summary["agent_contributions"]["water"]["neutral"] += 1

            # Track dominant agent performance
            if "dominant_agent_performance" not in summary:
                summary["dominant_agent_performance"] = {
                    "VEDASTRO": {"trades": 0, "evaluations": 0},
                    "EARTH": {"trades": 0, "evaluations": 0},
                    "FIRE": {"trades": 0, "evaluations": 0},
                    "WATER": {"trades": 0, "evaluations": 0},
                    "GUNA": {"trades": 0, "evaluations": 0},
                }

            dominant_agent = analysis.get("consensus", {}).get("dominant_agent", "UNKNOWN")
            if dominant_agent in summary["dominant_agent_performance"]:
                summary["dominant_agent_performance"][dominant_agent]["evaluations"] += 1
                if decision == "BUY":
                    summary["dominant_agent_performance"][dominant_agent]["trades"] += 1

            # Track entry types
            if "entry_types" not in summary:
                summary["entry_types"] = {"HARD": 0, "SOFT": 0, "UNKNOWN": 0}

            entry_type = analysis.get("decision", {}).get("entry_type", "UNKNOWN")
            if entry_type in summary["entry_types"]:
                summary["entry_types"][entry_type] += 1

            # Track regime performance
            if "regime_performance" not in summary:
                summary["regime_performance"] = {
                    "expansion": {"evaluations": 0, "trades": 0},
                    "contraction": {"evaluations": 0, "trades": 0},
                    "neutral": {"evaluations": 0, "trades": 0},
                }

            regime_key = analysis.get("consensus", {}).get("regime", "neutral")
            if regime_key in summary["regime_performance"]:
                summary["regime_performance"][regime_key]["evaluations"] += 1
                if decision == "BUY":
                    summary["regime_performance"][regime_key]["trades"] += 1

            # Track Vayu dampening
            if "vayu_stats" not in summary:
                summary["vayu_stats"] = {
                    "total_evaluations": 0,
                    "dampened_evaluations": 0,
                    "avg_dampener": 0.0,
                }

            vayu_dampener = analysis.get("vayu", {}).get("dampener", 1.0)
            summary["vayu_stats"]["total_evaluations"] += 1
            if vayu_dampener < 1.0:
                summary["vayu_stats"]["dampened_evaluations"] += 1

            # Update running average
            current_avg = summary["vayu_stats"]["avg_dampener"]
            total_count = summary["vayu_stats"]["total_evaluations"]
            summary["vayu_stats"]["avg_dampener"] = (
                (current_avg * (total_count - 1)) + vayu_dampener
            ) / total_count

            # Write summary
            with open(summary_file, "w") as f:
                json.dump(summary, f, indent=2, default=str)

        except Exception as e:
            logger.debug(f"Analytics logging error: {e}")

    async def _final_status(self):
        """Print final status."""
        elapsed = datetime.utcnow() - self.start_time if self.start_time else timedelta(0)

        print()
        print("=" * 80)
        print("     SESSION COMPLETE")
        print("=" * 80)
        print(f"Duration: {elapsed}")
        print(f"Total Trades: {self.state.total_trades}")
        print(f"Final Portfolio: EUR {self.state.total_value:,.2f}")
        print(f"Total P&L: EUR {self.state.total_pnl:+,.2f}")
        print("=" * 80)


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=int, default=8)
    parser.add_argument("--capital", type=float, default=10000.0)
    args = parser.parse_args()

    engine = RealPaperTradingV18(initial_capital=args.capital)

    try:
        await engine.initialize()
        await engine.run(duration_hours=args.duration)
    finally:
        await engine.close()


if __name__ == "__main__":
    asyncio.run(main())
