#!/usr/bin/env python3
"""
Test Runner for Unified Consciousness Integration Tests.

Voert alle tests uit per fase:
1. Unit tests per fase
2. Integration tests per fase
3. E2E tests

Usage:
    python run_unified_consciousness_tests.py
    python run_unified_consciousness_tests.py --phase A
    python run_unified_consciousness_tests.py --type unit
"""

import argparse
import subprocess
import sys
from pathlib import Path

# Test configuration
TEST_CONFIG = {
    "phase_a": {
        "unit": ["tests/unit/test_phase_a_orchestration_unification.py"],
        "integration": ["tests/integration/test_phase_a_integration.py"],
    },
    "phase_b": {
        "unit": ["tests/unit/test_phase_b_connect_consciousness.py"],
        "integration": ["tests/integration/test_phase_b_integration.py"],
    },
    "phase_c": {
        "unit": ["tests/unit/test_phase_c_risk_pipeline.py"],
        "integration": ["tests/integration/test_phase_cd_integration.py"],
    },
    "phase_d": {
        "unit": ["tests/unit/test_phase_d_strategy_integration.py"],
        "integration": ["tests/integration/test_phase_cd_integration.py"],
    },
    "phase_e": {
        "unit": ["tests/unit/test_phase_e_learning_loop.py"],
        "integration": ["tests/integration/test_phase_e_integration.py"],
    },
    "phase_f": {
        "unit": [],  # Frontend tests
        "integration": [],  # Frontend integration tests
    },
    "e2e": {
        "e2e": ["tests/e2e/test_unified_consciousness_e2e.py"],
    },
}


def run_pytest(test_files, verbose=True):
    """Run pytest with given test files."""
    if not test_files:
        print("⚠️  No test files found for this phase/type")
        return 0

    cmd = ["python", "-m", "pytest"]
    if verbose:
        cmd.append("-v")
    cmd.extend(test_files)

    print(f"\n{'='*80}")
    print(f"Running: {' '.join(cmd)}")
    print("=" * 80)

    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
    return result.returncode


def run_phase_tests(phase):
    """Run tests for a specific phase."""
    phase_key = f"phase_{phase.lower()}"

    if phase_key not in TEST_CONFIG:
        print(f"❌ Unknown phase: {phase}")
        return 1

    config = TEST_CONFIG[phase_key]
    exit_code = 0

    # Run unit tests
    if config.get("unit"):
        print(f"\n{'='*80}")
        print(f"PHASE {phase.upper()} - UNIT TESTS")
        print("=" * 80)
        exit_code |= run_pytest(config["unit"])

    # Run integration tests
    if config.get("integration"):
        print(f"\n{'='*80}")
        print(f"PHASE {phase.upper()} - INTEGRATION TESTS")
        print("=" * 80)
        exit_code |= run_pytest(config["integration"])

    return exit_code


def run_all_tests():
    """Run all tests for all phases."""
    phases = ["A", "B", "C", "D", "E"]
    exit_code = 0

    print("\n" + "=" * 80)
    print("UNIFIED CONSCIOUSNESS INTEGRATION - COMPLETE TEST SUITE")
    print("=" * 80)

    for phase in phases:
        exit_code |= run_phase_tests(phase)

    # Run E2E tests
    print(f"\n{'='*80}")
    print("END-TO-END TESTS")
    print("=" * 80)
    exit_code |= run_pytest(TEST_CONFIG["e2e"]["e2e"])

    return exit_code


def main():
    parser = argparse.ArgumentParser(
        description="Run Unified Consciousness Integration Tests"
    )
    parser.add_argument(
        "--phase",
        type=str,
        choices=["A", "B", "C", "D", "E", "F", "all"],
        default="all",
        help="Which phase to test (default: all)",
    )
    parser.add_argument(
        "--type",
        type=str,
        choices=["unit", "integration", "e2e", "all"],
        default="all",
        help="Type of tests to run (default: all)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", default=True, help="Verbose output"
    )

    args = parser.parse_args()

    if args.phase == "all":
        exit_code = run_all_tests()
    else:
        exit_code = run_phase_tests(args.phase)

    # Print summary
    print("\n" + "=" * 80)
    if exit_code == 0:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 80 + "\n")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
