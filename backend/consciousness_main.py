"""
Multi-Frequency Consciousness Architecture - Standalone Entry Point
Simplified version that runs only the 3-layer system without full infrastructure
"""

import asyncio
import logging
import os

from backend.core.config.settings import settings
from backend.core.telemetry.tracing import setup_tracing


async def start_consciousness_architecture():
    """Start the Multi-Frequency Consciousness Architecture"""
    logging.basicConfig(level=logging.INFO)
    setup_tracing("consciousness-architecture")

    logger = logging.getLogger("ConsciousnessArch")
    logger.info("Starting Multi-Frequency Consciousness Architecture...")

    # Import and initialize metrics BEFORE starting HTTP server
    from backend.core.telemetry.metrics import PrometheusMetrics

    # Initialize metrics for each component (this registers them)
    PrometheusMetrics("eternal_soul")
    PrometheusMetrics("cognitive_mind")
    PrometheusMetrics("reflex_executor")

    # Start Prometheus Metrics Server with the custom registry
    from prometheus_client import start_http_server

    metrics_port = int(os.getenv("METRICS_SERVER_PORT", 8000))
    try:
        # Start HTTP server on a separate thread using PrometheusMetrics registry
        metrics_registry = PrometheusMetrics._registry
        start_http_server(metrics_port, registry=metrics_registry)
        logger.info(f"✓ Prometheus Metrics Server started on port {metrics_port}")
    except Exception as e:
        logger.error(f"Failed to start Prometheus Metrics Server: {e}")

    logger.info(f"Environment: {settings.ENV}, Debug: {settings.DEBUG}")

    # Layer 1: Eternal Soul (Cosmic constraints)
    from backend.core.eternal_soul_service import EternalSoulService

    eternal_soul = EternalSoulService()
    try:
        await eternal_soul.start()
        logger.info("✓ Layer 1: Eternal Soul Service started (frequency: ~1 minute)")
    except Exception as e:
        logger.error(f"Layer 1 startup error: {e}")
        raise

    # Layer 2: Cognitive Mind (Decision making)
    from backend.core.cognitive_mind_service import CognitiveMindService

    cognitive_mind = CognitiveMindService(shm_name="trading_intents_v2")
    try:
        await cognitive_mind.start()
        logger.info("✓ Layer 2: Cognitive Mind Service started (frequency: 50-200ms)")
    except Exception as e:
        logger.error(f"Layer 2 startup error: {e}")
        raise

    # Layer 3: Reflex Body (Order execution)
    from backend.execution.reflex_executor import ReflexExecutor

    reflex_body = ReflexExecutor(
        shm_name="trading_intents_v2", market_shm_name="market_data_v2"
    )
    try:
        await reflex_body.start()
        logger.info("✓ Layer 3: Reflex Body Service started (frequency: <10ms)")
    except Exception as e:
        logger.error(f"Layer 3 startup error: {e}")
        raise

    logger.info("=" * 80)
    logger.info("Multi-Frequency Consciousness Architecture initialized successfully!")
    logger.info("=" * 80)
    logger.info("Running indefinitely. Press Ctrl+C to stop.")

    # Keep running
    try:
        while True:
            await asyncio.sleep(60)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        await eternal_soul.stop()
        await cognitive_mind.stop()
        await reflex_body.stop()
        logger.info("Consciousness Architecture stopped.")


if __name__ == "__main__":
    asyncio.run(start_consciousness_architecture())
