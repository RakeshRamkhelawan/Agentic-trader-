"""
Integration Test Runner for Phase 2 & 3

Runs all integration tests and generates a report.
"""

import asyncio
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def run_pytest(test_file: str, verbose: bool = True) -> bool:
    """Run pytest on a specific test file."""
    cmd = ["python", "-m", "pytest", test_file, "-v"] if verbose else ["python", "-m", "pytest", test_file]

    print(f"\n{'='*60}")
    print(f"Running: {test_file}")
    print('='*60)

    result = subprocess.run(cmd, capture_output=False, text=True)

    return result.returncode == 0


def run_manual_tests():
    """Run manual tests directly."""
    print("\n" + "=" * 60)
    print("MANUAL INTEGRATION TESTS")
    print("=" * 60)

    # Import and run tests
    sys.path.insert(0, '.')

    results = {}

    # Test 1: Guna Council
    print("\n1. Testing Guna Council...")
    try:
        from backend.councils.dynamic_guna_council import get_guna_council
        council = get_guna_council()

        test_data = {
            "volatility_1m": 0.03,
            "momentum_1d": 0.02,
            "volume_ratio": 1.2,
            "bid_ask_spread": 0.001,
            "trend": 1
        }

        result = council.analyze(test_data)
        guna = result["guna_vector"]

        print(f"   ✓ Guna: S={guna['sattva']:.0%} R={guna['rajas']:.0%} T={guna['tamas']:.0%}")
        print(f"   ✓ Perspective: {result['perspective']}")
        results["guna_council"] = "PASS"
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        results["guna_council"] = "FAIL"

    # Test 2: Mind Council
    print("\n2. Testing Mind Council...")
    try:
        from backend.councils.mind_council import get_mind_council
        council = get_mind_council()

        test_data = {
            "momentum_1d": -0.05,
            "momentum_3d": -0.10,
            "volatility_1m": 0.06,
            "volume_ratio": 2.5,
            "bid_ask_spread": 0.003,
            "imbalance": -0.4
        }

        result = council.analyze(test_data)
        fg = result["fear_greed_index"]

        print(f"   ✓ Fear/Greed: {fg:.0f}")
        print(f"   ✓ Perspective: {result['perspective']}")
        results["mind_council"] = "PASS"
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        results["mind_council"] = "FAIL"

    # Test 3: Calibrated Thresholds
    print("\n3. Testing Calibrated Thresholds...")
    try:
        from backend.core.market_data.calibrated_thresholds import get_thresholds
        cal = get_thresholds()

        thresholds = cal.get_thresholds()

        print(f"   ✓ Capitulation vol: {thresholds['capitulation_vol']:.4f}")
        print(f"   ✓ Sample size: {thresholds['sample_size']}")
        results["calibrated_thresholds"] = "PASS"
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        results["calibrated_thresholds"] = "FAIL"

    # Test 4: Council Orchestrator
    print("\n4. Testing Council Orchestrator...")
    try:
        from backend.councils.council_orchestrator import get_orchestrator

        async def test_orchestrator():
            orch = get_orchestrator()

            test_data = {
                "volatility_1m": 0.03,
                "momentum_1d": 0.025,
                "volume_ratio": 1.3,
                "bid_ask_spread": 0.001,
                "trend": 1,
                "imbalance": 0.2
            }

            result = await orch.deliberate(test_data, "integration_test")

            print(f"   ✓ Final perspective: {result['final_perspective']}")
            print(f"   ✓ Coherence: {result['coherence']:.2f}")
            print(f"   ✓ Councils: {len(result['council_views'])}")

            return "PASS"

        result = asyncio.run(test_orchestrator())
        results["orchestrator"] = result
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        results["orchestrator"] = "FAIL"

    # Test 5: Event Bus (without Redis)
    print("\n5. Testing Event Bus structure...")
    try:
        from backend.events.triad_event_bus import CouncilDeliberation, BuddhiDecision
        from datetime import datetime

        # Test dataclasses
        d = CouncilDeliberation(
            council_type="guna",
            perspective="bullish",
            confidence=0.8,
            reasoning="Test",
            metadata={},
            timestamp=datetime.utcnow().isoformat()
        )

        print(f"   ✓ CouncilDeliberation: {d.council_type} - {d.perspective}")

        bd = BuddhiDecision(
            action="buy",
            confidence=0.75,
            coherence=0.7,
            rationale="Test",
            council_views=[],
            session_id="test",
            timestamp=datetime.utcnow().isoformat()
        )

        print(f"   ✓ BuddhiDecision: {bd.action} - coherence {bd.coherence}")
        results["event_bus_structure"] = "PASS"
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        results["event_bus_structure"] = "FAIL"

    return results


def generate_report(results: dict):
    """Generate test report."""
    print("\n" + "=" * 60)
    print("INTEGRATION TEST REPORT")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v == "PASS")
    failed = sum(1 for v in results.values() if v == "FAIL")
    total = len(results)

    print(f"\nResults: {passed}/{total} passed")
    print()

    for test_name, result in results.items():
        status = "✓" if result == "PASS" else "✗"
        print(f"{status} {test_name}: {result}")

    print()

    if failed == 0:
        print("🎉 All integration tests passed!")
        return 0
    else:
        print(f"⚠️  {failed} test(s) failed")
        return 1


def main():
    """Main test runner."""
    print("=" * 60)
    print("PHASE 2 & 3 INTEGRATION TESTS")
    print("=" * 60)
    print(f"Started: {datetime.now().isoformat()}")

    # Run manual tests
    results = run_manual_tests()

    # Generate report
    exit_code = generate_report(results)

    print(f"\nFinished: {datetime.now().isoformat()}")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
