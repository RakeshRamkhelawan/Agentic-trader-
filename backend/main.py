import asyncio
import logging

from backend.core.config.settings import settings
from backend.core.telemetry.tracing import setup_tracing
from backend.llm.usage_tracker import UsageTracker
from backend.schemas.agent_messages import AgentMessage
from backend.services.cognitive_orchestrator import CognitiveOrchestrator


async def start_services():
    logging.basicConfig(level=logging.INFO)
    setup_tracing("main-application")

    logger = logging.getLogger("MainApp")
    logger.info("Starting Agentic Trader Platform...")

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
    except Exception as e:
        logger.warning(f"Eternal Soul Service startup warning: {e}")

    # Layer 2: Cognitive Mind (Decision making)
    cognitive_mind = CognitiveMindService(shm_name="trading_intents_v2")
    try:
        await cognitive_mind.start()
        logger.info("✓ Layer 2: Cognitive Mind Service started (frequency: 50-200ms)")
    except Exception as e:
        logger.warning(f"Cognitive Mind Service startup warning: {e}")

    # Layer 3: Reflex Body (Order execution)
    reflex_body = ReflexExecutor(
        shm_name="trading_intents_v2", market_shm_name="market_data_v2"
    )
    try:
        await reflex_body.start()
        logger.info("✓ Layer 3: Reflex Body Service started (frequency: <10ms)")
    except Exception as e:
        logger.warning(f"Reflex Body Service startup warning: {e}")

    # In a production setup, each agent would be its own service.
    # For now, orchestrator manages them internally.

    # Start any periodic tasks, e.g., Research Agent cycle
    if "research_v1" in orchestrator.agents:
        # Trigger the research agent cycle to start the flow
        await orchestrator.handle_message(
            AgentMessage(
                source="orchestrator",
                target="research_v1",
                type="TIMER_TICK_1MIN",
                payload={},
            )
        )

    logger.info("Platform initialized. Keeping services alive...")
    while True:
        await asyncio.sleep(60)  # Keep main loop running


if __name__ == "__main__":
    # Ensure ChromaDB host/port are picked from settings
    # (Though MemoryAgent will use it directly)
    asyncio.run(start_services())
