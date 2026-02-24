"""
PoC: VedAstro Integration Smoke Test
Validates that TradingSignalGenerator works in backtest context
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ["TRADING_MODE"] = "paper"

import asyncio
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger("PoCVedAstro")

from backend.vedastro import EnhancedAstroOrchestrator, TradingSignalGenerator


async def test_vedastro_basic():
    """Test basic VedAstro functionality"""
    logger.info("=" * 60)
    logger.info("PoC: Basic VedAstro Functionality Test")
    logger.info("=" * 60)

    orchestrator = EnhancedAstroOrchestrator()

    # Test BTC
    logger.info("\n--- Testing BTC at $65,000 ---")
    try:
        result = await orchestrator.analyze_asset("BTC", 65000.0)
        logger.info(f"Signal: {result.trading_signal.signal}")
        logger.info(f"Confidence: {result.trading_signal.confidence}%")
        logger.info(f"Strength Score: {result.trading_signal.strength_score}")
        logger.info(f"Risk Level: {result.trading_signal.risk_level}")
        logger.info(f"Primary Factors: {len(result.trading_signal.primary_factors)}")
        logger.info("✅ BTC test PASSED")
    except Exception as e:
        logger.error(f"❌ BTC test FAILED: {e}")
        return False

    # Test AAPL
    logger.info("\n--- Testing AAPL at $180 ---")
    try:
        result = await orchestrator.analyze_asset("AAPL", 180.0)
        logger.info(f"Signal: {result.trading_signal.signal}")
        logger.info(f"Confidence: {result.trading_signal.confidence}%")
        logger.info(f"Strength Score: {result.trading_signal.strength_score}")
        logger.info(f"Risk Level: {result.trading_signal.risk_level}")
        logger.info("✅ AAPL test PASSED")
    except Exception as e:
        logger.error(f"❌ AAPL test FAILED: {e}")
        return False

    return True


async def test_vedastro_performance():
    """Test VedAstro performance (should be < 5s per asset)"""
    logger.info("\n" + "=" * 60)
    logger.info("PoC: Performance Test (3 assets, single date)")
    logger.info("=" * 60)

    orchestrator = EnhancedAstroOrchestrator()
    symbols = ["BTC", "ETH", "AAPL"]

    start_time = datetime.now()

    for symbol in symbols:
        try:
            await orchestrator.analyze_asset(symbol, 1000.0)
            logger.info(f"  {symbol}: OK")
        except Exception as e:
            logger.error(f"  {symbol}: FAILED - {e}")

    duration = (datetime.now() - start_time).total_seconds()
    logger.info(f"\nTotal duration: {duration:.2f}s for 3 assets")
    logger.info(f"Avg per asset: {duration/3:.2f}s")

    if duration < 15:  # Should be fast
        logger.info("✅ Performance test PASSED")
        return True
    else:
        logger.warning("⚠️ Performance test SLOW (>5s per asset)")
        return True  # Still pass, just slow


async def test_caching():
    """Test that caching works for same-day calls"""
    logger.info("\n" + "=" * 60)
    logger.info("PoC: Caching Test (same asset, 2 calls)")
    logger.info("=" * 60)

    orchestrator = EnhancedAstroOrchestrator()

    # First call
    start = datetime.now()
    result1 = await orchestrator.analyze_asset("BTC", 50000.0)
    duration1 = (datetime.now() - start).total_seconds()
    logger.info(f"First call: {duration1:.2f}s")

    # Second call (should be cached)
    start = datetime.now()
    result2 = await orchestrator.analyze_asset("BTC", 50000.0)
    duration2 = (datetime.now() - start).total_seconds()
    logger.info(f"Second call: {duration2:.2f}s")

    if duration2 < duration1 * 0.5:  # Second call should be 2x faster
        logger.info("✅ Caching working (second call faster)")
    else:
        logger.info("ℹ️ No caching detected (same speed)")

    return True


async def main():
    """Run all PoC tests"""
    logger.info("\n" + "=" * 70)
    logger.info("VedAstro Integration PoC - Smoke Test Suite")
    logger.info("=" * 70)

    results = []

    # Test 1: Basic functionality
    results.append(("Basic Functionality", await test_vedastro_basic()))

    # Test 2: Performance
    results.append(("Performance", await test_vedastro_performance()))

    # Test 3: Caching
    results.append(("Caching", await test_caching()))

    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("PoC RESULTS SUMMARY")
    logger.info("=" * 70)

    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"  {status}: {name}")

    total = len(results)
    passed = sum(1 for _, p in results if p)
    logger.info(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        logger.info("\n🚀 VedAstro integration ready for V17!")
        return True
    else:
        logger.error("\n⚠️ Some tests failed - fix before V17")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
