import asyncio
import logging
from backend.services.cognitive_orchestrator import CognitiveOrchestrator
from backend.core.telemetry.tracing import setup_tracing
from backend.core.config.settings import settings
from backend.schemas.agent_messages import AgentMessage

async def start_services():
    logging.basicConfig(level=logging.INFO)
    setup_tracing("main-application")
    
    logger = logging.getLogger("MainApp")
    logger.info("Starting Agentic Trader Platform...")
    logger.info(f"Environment: {settings.ENV}, Debug: {settings.DEBUG}")

    logger.info(f"Environment: {settings.ENV}, Debug: {settings.DEBUG}")

    # Initialize Usage Infrastructure
    from backend.storage.tenant_aware_clickhouse import TenantAwareClickHouseClient
    from backend.core.compliance.audit_logger import AuditLogger
    from backend.core.compliance.decorators import set_global_audit_logger
    import os

    clickhouse_client = TenantAwareClickHouseClient(
        host=os.getenv("CLICKHOUSE_HOST", "localhost"),
        port=int(os.getenv("CLICKHOUSE_PORT", 8123)),
        enforce_tenant=True
    )
    usage_tracker = UsageTracker(clickhouse_client=clickhouse_client)
    await usage_tracker.start()

    # Initialize Audit Logger
    audit_logger = AuditLogger(clickhouse_client=clickhouse_client)
    await audit_logger.start()
    set_global_audit_logger(audit_logger)

    # Start the Cognitive Orchestrator
    orchestrator = CognitiveOrchestrator(usage_tracker=usage_tracker, audit_logger=audit_logger)

    # In a production setup, each agent would be its own service.
    # For now, orchestrator manages them internally.
    
    # Start any periodic tasks, e.g., Research Agent cycle
    if "research_v1" in orchestrator.agents:
        research_agent = orchestrator.agents["research_v1"]
        # Trigger the research agent cycle to start the flow
        await orchestrator.handle_message(
            AgentMessage(source="orchestrator", target="research_v1", type="TIMER_TICK_1MIN", payload={})
        )
    
    logger.info("Platform initialized. Keeping services alive...")
    while True:
        await asyncio.sleep(60) # Keep main loop running

if __name__ == "__main__":
    # Ensure ChromaDB host/port are picked from settings
    # (Though MemoryAgent will use it directly)
    asyncio.run(start_services())
