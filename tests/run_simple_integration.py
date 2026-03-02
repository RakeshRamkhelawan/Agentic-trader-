#!/usr/bin/env python3
"""Simple integration test runner without unicode issues."""

import sys
import asyncio
sys.path.insert(0, '.')

def test_guna_council():
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

        print(f"   Sattva: {guna['sattva']:.1%}")
        print(f"   Rajas: {guna['rajas']:.1%}")
        print(f"   Tamas: {guna['tamas']:.1%}")
        print(f"   Dominant: {guna['dominant']}")
        print(f"   Perspective: {result['perspective']}")
        print("   Status: PASS")
        return True
    except Exception as e:
        print(f"   Status: FAIL - {e}")
        return False


def test_mind_council():
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

        print(f"   Fear/Greed: {fg:.0f}")
        print(f"   Perspective: {result['perspective']}")
        print("   Status: PASS")
        return True
    except Exception as e:
        print(f"   Status: FAIL - {e}")
        return False


def test_calibrated_thresholds():
    print("\n3. Testing Calibrated Thresholds...")
    try:
        from backend.core.market_data.calibrated_thresholds import get_thresholds
        cal = get_thresholds()

        thresholds = cal.get_thresholds()

        print(f"   Capitulation vol: {thresholds['capitulation_vol']:.4f}")
        print(f"   Euphoria vol: {thresholds['euphoria_vol']:.4f}")
        print(f"   Sample size: {thresholds['sample_size']}")
        print("   Status: PASS")
        return True
    except Exception as e:
        print(f"   Status: FAIL - {e}")
        return False


async def test_orchestrator():
    print("\n4. Testing Council Orchestrator...")
    try:
        from backend.councils.council_orchestrator import get_orchestrator

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

        print(f"   Final perspective: {result['final_perspective']}")
        print(f"   Coherence: {result['coherence']:.2f}")
        print(f"   Councils: {len(result['council_views'])}")
        for view in result['council_views']:
            print(f"     {view['council']}: {view['perspective']} (conf: {view['confidence']:.2f})")
        print("   Status: PASS")
        return True
    except Exception as e:
        print(f"   Status: FAIL - {e}")
        return False


async def main():
    print("=" * 60)
    print("PHASE 2 & 3 INTEGRATION TESTS")
    print("=" * 60)

    results = []

    results.append(("Guna Council", test_guna_council()))
    results.append(("Mind Council", test_mind_council()))
    results.append(("Calibrated Thresholds", test_calibrated_thresholds()))
    results.append(("Orchestrator", await test_orchestrator()))

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {name}: {status}")

    print(f"\nTotal: {passed}/{total} passed")

    if passed == total:
        print("\nAll integration tests passed!")
        return 0
    else:
        print(f"\n{total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
