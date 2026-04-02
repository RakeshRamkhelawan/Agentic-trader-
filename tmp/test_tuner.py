import asyncio
import logging
import json
from pathlib import Path
from backend.services.evolutionary_tuner import tuner

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TunerTest")

async def test_aggressive_tuning():
    print("=" * 60)
    print("   COGNITIVE EVOLUTIONARY TUNER - AGGRESSIVE TEST")
    print("=" * 60)

    # Reset / Ensure clean state for test
    regime = "expansion"
    print(f"\nInitial Weights ({regime}):")
    print(json.dumps(tuner.get_weights(regime), indent=2))

    # Scenario: VedAstro is performing exceptionally well, others are failing
    print(f"\n--- Simulating 20 Trades (VedAstro Success, Others Fail) ---")

    for i in range(20):
        # VedAstro wins, Earth/Fire/Water are just 'along for the ride' but we let them fail
        # In this simulation, we'll just say the decision (based on all 4) resulted in outcome
        # If we want to see VedAstro win specifically, we need to show the tuner that VedAstro's
        # contribution is valid.

        # Simuleer een winst-reeks voor het systeem
        tuner.update_performance(
            regime=regime,
            outcome=5.0, # 5% profit
            agents_involved=["vedastro", "earth", "fire", "water"]
        )

    print(f"\nWeights after 20 Wins:")
    print(json.dumps(tuner.get_weights(regime), indent=2))

    # Scenario: Massive failure for Earth element
    print(f"\n--- Simulating 10 Massive Losses specifically attributed to Earth/Fire ---")
    for i in range(10):
        tuner.update_performance(
            regime=regime,
            outcome=-10.0, # 10% loss
            agents_involved=["earth", "fire"]
        )

    print(f"\nFinal Weights after Losses:")
    final_weights = tuner.get_weights(regime)
    print(json.dumps(final_weights, indent=2))

    # Verification
    if final_weights["vedastro"] > final_weights["earth"]:
        print("\n✅ SUCCESS: VedAstro weight is now higher than Earth after Earth failures.")
    else:
        print("\n❌ FAILURE: Weights did not shift as expected.")

if __name__ == "__main__":
    asyncio.run(test_aggressive_tuning())
