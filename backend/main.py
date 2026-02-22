import asyncio
import logging
import signal
from datetime import datetime

from backend.core.config.settings import settings
from backend.core.telemetry.tracing import setup_tracing
from backend.llm.usage_tracker import UsageTracker
from backend.schemas.agent_messages import AgentMessage
from backend.services.cognitive_orchestrator import CognitiveOrchestrator

# ═══════════════════════════════════════════════════════════════════════════
# ENTERPRISE: Graceful Shutdown Handler
# ═══════════════════════════════════════════════════════════════════════════
_shutdown_event = asyncio.Event()
_active_services = []


async def graceful_shutdown(signal_name: str, logger):
    """
    Enterprise-grade graceful shutdown — sluit alle resources netjes.
    """
    logger.info(f"🔴 Shutdown signaal ontvangen: {signal_name}")
    logger.info("🔄 Start graceful shutdown sequence...")

    # 1. Stop accepting new trading cycles
    _shutdown_event.set()

    # 2. Stop services in omgekeerde volgorde (Body → Mind → Soul)
    for service_name, service in reversed(_active_services):
        try:
            logger.info(f"  → Stopping {service_name}...")
            if hasattr(service, "stop"):
                await service.stop()
            logger.info(f"  ✓ {service_name} stopped")
        except Exception as e:
            logger.error(f"  ✗ Error stopping {service_name}: {e}")

    # 3. Save any active paper trading session
    try:
        from backend.services.paper_trading_live import \
            paper_trading_broadcaster

        await paper_trading_broadcaster.broadcast_session_end(
            {
                "reason": f"graceful_shutdown:{signal_name}",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
        logger.info("  ✓ Session end broadcasted")
    except Exception as e:
        logger.warning(f"  ✗ Could not broadcast session end: {e}")

    logger.info("✅ Graceful shutdown complete")


def setup_signal_handlers(loop, logger):
    """Setup signal handlers for graceful shutdown."""
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(
            sig, lambda s=sig: asyncio.create_task(graceful_shutdown(s.name, logger))
        )
    logger.info("✓ Signal handlers registered (SIGTERM, SIGINT)")


async def start_services():
    import os

    # ═══════════════════════════════════════════════════════════════════════
    # ENTERPRISE SAFETY: TRADING_MODE VERIFICATIE
    # ═══════════════════════════════════════════════════════════════════════
    TRADING_MODE = os.getenv("TRADING_MODE", "paper")
    if TRADING_MODE != "paper":
        raise SystemExit(
            f"\n{'='*60}\n"
            f"🚫 STARTUP ABORTED: TRADING_MODE='{TRADING_MODE}' is not 'paper'\n"
            f"{'='*60}\n"
            f"This system is ONLY configured for paper trading.\n"
            f"Set TRADING_MODE=paper in your .env file:\n\n"
            f"    TRADING_MODE=paper\n\n"
            f"Refusing to start to prevent any risk of live orders.\n"
            f"{'='*60}\n"
        )

    # ═══════════════════════════════════════════════════════════════════════
    # Initialize logging en tracing
    # ═══════════════════════════════════════════════════════════════════════
    logging.basicConfig(level=logging.INFO)
    setup_tracing("main-application")

    logger = logging.getLogger("MainApp")
    logger.info("Starting Agentic Trader Platform...")
    logger.info(f"✓ SAFETY CHECK: TRADING_MODE={TRADING_MODE} (verified)")

    # Setup signal handlers voor graceful shutdown
    loop = asyncio.get_event_loop()
    setup_signal_handlers(loop, logger)

    # Start Prometheus Metrics Server
    import os

    from prometheus_client import start_http_server

    metrics_port = int(os.getenv("METRICS_SERVER_PORT", 8000))
    try:
        start_http_server(metrics_port)
        logger.info(f"✓ Prometheus Metrics Server started on port {metrics_port}")
    except Exception as e:
        logger.error(f"Failed to start Prometheus Metrics Server: {e}")

    logger.info(f"Environment: {settings.ENV}, Debug: {settings.DEBUG}")

    logger.info(f"Environment: {settings.ENV}, Debug: {settings.DEBUG}")

    # Initialize Usage Infrastructure
    import os

    from backend.core.compliance.audit_logger import AuditLogger
    from backend.core.compliance.decorators import set_global_audit_logger
    from backend.storage.tenant_aware_clickhouse import \
        TenantAwareClickHouseClient

    clickhouse_client = TenantAwareClickHouseClient(
        host=os.getenv("CLICKHOUSE_HOST", "localhost"),
        port=int(os.getenv("CLICKHOUSE_PORT", 8123)),
        enforce_tenant=True,
    )
    usage_tracker = UsageTracker(clickhouse_client=clickhouse_client)
    await usage_tracker.start()

    # Initialize Audit Logger
    audit_logger = AuditLogger(clickhouse_client=clickhouse_client)
    await audit_logger.start()
    set_global_audit_logger(audit_logger)

    # Initialize FastConfig (Hot Path Bridge)
    from backend.execution.fast_config import FastConfig

    config_path = os.getenv("FAST_CONFIG_PATH", "data/config/fast_config.bin")
    FastConfig.initialize(config_path)
    logger.info(f"FastConfig initialized at {config_path}")

    # Start the Cognitive Orchestrator
    orchestrator = CognitiveOrchestrator(
        usage_tracker=usage_tracker, audit_logger=audit_logger
    )

    # Initialize Multi-Frequency Consciousness Architecture (Phase 1-3)
    from backend.core.cognitive_mind_service import CognitiveMindService
    from backend.core.eternal_soul_service import EternalSoulService
    from backend.execution.reflex_executor import ReflexExecutor

    # Layer 1: Eternal Soul (Cosmic constraints)
    eternal_soul = EternalSoulService()
    try:
        await eternal_soul.start()
        logger.info("✓ Layer 1: Eternal Soul Service started (frequency: ~1 minute)")
        _active_services.append(("EternalSoul", eternal_soul))
    except Exception as e:
        logger.warning(f"Eternal Soul Service startup warning: {e}")

    # Layer 2: Cognitive Mind (Decision making)
    cognitive_mind = CognitiveMindService(shm_name="trading_intents_v2")
    try:
        await cognitive_mind.start()
        logger.info("✓ Layer 2: Cognitive Mind Service started (frequency: 50-200ms)")
        _active_services.append(("CognitiveMind", cognitive_mind))
    except Exception as e:
        logger.warning(f"Cognitive Mind Service startup warning: {e}")

    # Layer 3: Reflex Body (Order execution)
    # SAFETY: trading_mode=paper is hardcoded - no live orders possible
    reflex_body = ReflexExecutor(
        shm_name="trading_intents_v2",
        market_shm_name="market_data_v2",
        trading_mode="paper",  # ← HARDcoded voor veiligheid
    )
    try:
        await reflex_body.start()
        logger.info("✓ Layer 3: Reflex Body Service started (frequency: <10ms)")
        logger.info("  ✓ PAPER MODE: All orders are simulated - no real exchange calls")
        _active_services.append(("ReflexBody", reflex_body))
    except Exception as e:
        logger.warning(f"Reflex Body Service startup warning: {e}")

    # In a production setup, each agent would be its own service.
    # For now, orchestrator manages them internally.

    # Start periodic timer tick for all agents
    async def timer_loop():
        """Send TIMER_TICK_1MIN to all agents every minute."""
        while True:
            await asyncio.sleep(60)  # Every minute

            # Get current market data for context
            from backend.core.cache_layer import get_cache

            cache = get_cache()
            market_data = await cache.get("markets:all") or []

            # Calculate top movers for payload
            if market_data:
                sorted_markets = sorted(
                    market_data, key=lambda x: x.get("change_24h", 0), reverse=True
                )
                top_gainers = sorted_markets[:3]
                top_losers = sorted_markets[-3:]

                payload = {
                    "top_gainers": [
                        {"symbol": m["symbol"], "change": m["change_24h"]}
                        for m in top_gainers
                    ],
                    "top_losers": [
                        {"symbol": m["symbol"], "change": m["change_24h"]}
                        for m in top_losers
                    ],
                    "market_count": len(market_data),
                    "timestamp": datetime.now().isoformat(),
                }
            else:
                payload = {}

            # Send tick to all agents
            for agent_id in orchestrator.agents.keys():
                if agent_id != "orchestrator_v1":  # Don't send to self
                    try:
                        await orchestrator.handle_message(
                            AgentMessage(
                                source="orchestrator",
                                target=agent_id,
                                type="TIMER_TICK_1MIN",
                                payload=payload,
                            )
                        )
                    except Exception as e:
                        logger.warning(f"Failed to send timer tick to {agent_id}: {e}")

            logger.debug(
                f"TIMER_TICK_1MIN sent to {len(orchestrator.agents) - 1} agents"
            )

    # Start timer loop as background task
    timer_task = asyncio.create_task(timer_loop())

    # Send initial tick immediately
    for agent_id in orchestrator.agents.keys():
        if agent_id != "orchestrator_v1":
            try:
                await orchestrator.handle_message(
                    AgentMessage(
                        source="orchestrator",
                        target=agent_id,
                        type="TIMER_TICK_1MIN",
                        payload={},
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to send initial tick to {agent_id}: {e}")

    logger.info("Platform initialized. Keeping services alive...")
    try:
        while True:
            await asyncio.sleep(60)  # Keep main loop running
    finally:
        timer_task.cancel()
        try:
            await timer_task
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    # Ensure ChromaDB host/port are picked from settings
    # (Though MemoryAgent will use it directly)
    asyncio.run(start_services())
