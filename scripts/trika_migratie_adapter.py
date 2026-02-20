#!/usr/bin/env python3
"""
TRIKA MIGRATIE ADAPTER
Verbindt oude trika_pure_system.py met nieuwe trika_federated_system.py

Doel:
- Behoud backward compatibility
- Graduele migratie mogelijk
- Beide systemen kunnen naast elkaar draaien
- Feature flags voor nieuwe functionaliteit
"""

import asyncio
import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

# Add scripts directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Probeert oude systeem te importeren
try:
    from trika_pure_system import (BodyCouncil, ElementalCouncil, GrahaCouncil,
                                   GunaCouncil, MindCouncil, Shiva)
    from trika_pure_system import TrikaSystem as OldTrikaSystem

    OLD_SYSTEM_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Old trika_pure_system not available: {e}")
    OLD_SYSTEM_AVAILABLE = False

# Nieuw systeem
from trika_federated_system import FederatedTriadSystem

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================


class MigrationMode(Enum):
    """Verschillende migratie modi"""

    LEGACY_ONLY = "legacy_only"  # Alleen oude systeem
    FEDERATED_ONLY = "federated_only"  # Alleen nieuwe systeem
    HYBRID = "hybrid"  # Beide, met adapter
    SHADOW = "shadow"  # Beide, vergelijk outputs


@dataclass
class AdapterConfig:
    """Configuratie voor de migratie adapter"""

    mode: MigrationMode = MigrationMode.HYBRID
    use_chitta: bool = True
    use_cooperative_deliberation: bool = True
    use_buddhi_synthesis: bool = True
    deliberation_iterations: int = 3
    chitta_max_nodes: int = 10000
    enable_cache: bool = True
    fallback_on_error: bool = True  # Fallback naar oude systeem bij error


# =============================================================================
# MIGRATIE ADAPTER
# =============================================================================


class TrikaMigrationAdapter:
    """
    Adapter die oude en nieuwe Trika systemen verbindt.

    Features:
    - Unified API voor beide systemen
    - Feature flags voor geleidelijke migratie
    - Output vergelijking in shadow mode
    - Automatische fallback bij errors
    """

    def __init__(self, config: Optional[AdapterConfig] = None):
        self.config = config or AdapterConfig()
        self.old_system = None
        self.new_system = None
        self.metrics = {
            "cycles_run": 0,
            "old_system_calls": 0,
            "new_system_calls": 0,
            "errors_old": 0,
            "errors_new": 0,
            "fallbacks": 0,
            "comparisons": [],
        }

        self._initialize_systems()

    def _initialize_systems(self):
        """Initialiseer systemen gebaseerd op mode"""
        if self.config.mode in [
            MigrationMode.LEGACY_ONLY,
            MigrationMode.HYBRID,
            MigrationMode.SHADOW,
        ]:
            if OLD_SYSTEM_AVAILABLE:
                try:
                    self.old_system = OldTrikaSystem()
                    logger.info("Old TrikaSystem initialized")
                except Exception as e:
                    logger.error(f"Failed to initialize old system: {e}")
                    if self.config.mode == MigrationMode.LEGACY_ONLY:
                        raise
            else:
                logger.warning(
                    "Old system not available, falling back to federated only"
                )
                if self.config.mode == MigrationMode.LEGACY_ONLY:
                    raise RuntimeError(
                        "Legacy mode requested but old system not available"
                    )

        if self.config.mode in [
            MigrationMode.FEDERATED_ONLY,
            MigrationMode.HYBRID,
            MigrationMode.SHADOW,
        ]:
            try:
                self.new_system = FederatedTriadSystem(
                    enable_caching=self.config.enable_cache,
                    deliberation_iterations=self.config.deliberation_iterations,
                    chitta_max_nodes=self.config.chitta_max_nodes,
                )
                logger.info("New FederatedTriadSystem initialized")
            except Exception as e:
                logger.error(f"Failed to initialize new system: {e}")
                if self.config.mode == MigrationMode.FEDERATED_ONLY:
                    raise

    async def process_cycle(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verwerk één cyclus met het geconfigureerde systeem.

        Unified API die werkt voor beide systemen.
        """
        self.metrics["cycles_run"] += 1

        if self.config.mode == MigrationMode.LEGACY_ONLY:
            return await self._run_legacy(market_data)

        elif self.config.mode == MigrationMode.FEDERATED_ONLY:
            return await self._run_federated(market_data)

        elif self.config.mode == MigrationMode.HYBRID:
            return await self._run_hybrid(market_data)

        elif self.config.mode == MigrationMode.SHADOW:
            return await self._run_shadow(market_data)

        else:
            raise ValueError(f"Unknown migration mode: {self.config.mode}")

    async def _run_legacy(self, market_data: Dict) -> Dict:
        """Run alleen oude systeem"""
        if not self.old_system:
            raise RuntimeError("Old system not available")

        try:
            self.metrics["old_system_calls"] += 1

            # Oude systeem aanroepen
            result = await self.old_system.cycle(market_data)

            # Normalizeer output naar nieuw formaat
            return self._normalize_legacy_output(result, market_data)

        except Exception as e:
            self.metrics["errors_old"] += 1
            logger.error(f"Legacy system error: {e}")
            raise

    async def _run_federated(self, market_data: Dict) -> Dict:
        """Run alleen nieuwe systeem"""
        if not self.new_system:
            raise RuntimeError("New system not available")

        try:
            self.metrics["new_system_calls"] += 1
            return await self.new_system.process_cycle(market_data)

        except Exception as e:
            self.metrics["errors_new"] += 1
            logger.error(f"Federated system error: {e}")

            if self.config.fallback_on_error and self.old_system:
                logger.info("Falling back to legacy system")
                self.metrics["fallbacks"] += 1
                return await self._run_legacy(market_data)
            raise

    async def _run_hybrid(self, market_data: Dict) -> Dict:
        """Run hybride: nieuw systeem met fallback naar oud"""
        if self.new_system:
            try:
                return await self._run_federated(market_data)
            except Exception:
                if self.config.fallback_on_error and self.old_system:
                    return await self._run_legacy(market_data)
                raise
        elif self.old_system:
            return await self._run_legacy(market_data)
        else:
            raise RuntimeError("No system available")

    async def _run_shadow(self, market_data: Dict) -> Dict:
        """Run beide systemen en vergelijk outputs"""
        results = {}

        # Run oude systeem
        if self.old_system:
            try:
                old_result = await self._run_legacy(market_data)
                results["old"] = old_result
            except Exception as e:
                results["old_error"] = str(e)

        # Run nieuwe systeem
        if self.new_system:
            try:
                new_result = await self._run_federated(market_data)
                results["new"] = new_result
            except Exception as e:
                results["new_error"] = str(e)

        # Vergelijk outputs
        if "old" in results and "new" in results:
            comparison = self._compare_outputs(results["old"], results["new"])
            self.metrics["comparisons"].append(comparison)

            # Log significante verschillen
            if not comparison["actions_match"]:
                logger.warning(
                    f"Action mismatch: old={comparison['old_action']}, "
                    f"new={comparison['new_action']}"
                )

        # Gebruik nieuw systeem output (of oud als fallback)
        return results.get("new", results.get("old", {"error": "Both systems failed"}))

    def _normalize_legacy_output(self, legacy_result: Dict, market_data: Dict) -> Dict:
        """Normaliseer oude systeem output naar nieuw formaat"""
        # Extract actie uit legacy result
        action = legacy_result.get("action", "hold")

        return {
            "cycle": legacy_result.get("cycle", 0),
            "success": True,
            "source": "legacy_system",
            "council_views": legacy_result.get("council_views", {}),
            "decision": {
                "action": action,
                "confidence": legacy_result.get("confidence", 0.5),
                "rationale": legacy_result.get("rationale", "Legacy system decision"),
                "supporting_councils": [],
                "opposing_councils": [],
                "contradictions_detected": 0,
                "evidence_weight": {},
                "timestamp": datetime.now().isoformat(),
            },
            "execution": {"action": action, "price": market_data.get("price", 0)},
            "latency_ms": legacy_result.get("latency_ms", 0),
            "chitta_stats": {
                "source": "legacy",
                "note": "Chitta not available in legacy system",
            },
        }

    def _compare_outputs(self, old: Dict, new: Dict) -> Dict:
        """Vergelijk outputs van oude en nieuwe systeem"""
        old_action = old.get("decision", {}).get("action", "unknown")
        new_action = new.get("decision", {}).get("action", "unknown")

        old_conf = old.get("decision", {}).get("confidence", 0)
        new_conf = new.get("decision", {}).get("confidence", 0)

        return {
            "timestamp": datetime.now().isoformat(),
            "old_action": old_action,
            "new_action": new_action,
            "actions_match": old_action == new_action,
            "old_confidence": old_conf,
            "new_confidence": new_conf,
            "confidence_diff": abs(old_conf - new_conf),
            "old_latency": old.get("latency_ms", 0),
            "new_latency": new.get("latency_ms", 0),
        }

    def get_metrics(self) -> Dict:
        """Haal adapter metrics op"""
        return {
            **self.metrics,
            "mode": self.config.mode.value,
            "old_system_available": self.old_system is not None,
            "new_system_available": self.new_system is not None,
            "fallback_rate": (
                self.metrics["fallbacks"] / self.metrics["cycles_run"]
                if self.metrics["cycles_run"] > 0
                else 0
            ),
        }

    def enable_feature(self, feature: str):
        """Schakel een feature in (voor runtime configuratie)"""
        if feature == "chitta":
            self.config.use_chitta = True
        elif feature == "cooperative_deliberation":
            self.config.use_cooperative_deliberation = True
        elif feature == "buddhi_synthesis":
            self.config.use_buddhi_synthesis = True
        else:
            raise ValueError(f"Unknown feature: {feature}")

    def switch_mode(self, mode: MigrationMode):
        """Wissel van migratie mode (runtime)"""
        old_mode = self.config.mode
        self.config.mode = mode

        # Her-initialiseer indien nodig
        if mode == MigrationMode.LEGACY_ONLY and not self.old_system:
            self._initialize_systems()
        elif mode == MigrationMode.FEDERATED_ONLY and not self.new_system:
            self._initialize_systems()

        logger.info(f"Switched mode from {old_mode.value} to {mode.value}")


# =============================================================================
# BACKWARD COMPATIBILITY LAYER
# =============================================================================


class TrikaSystemFacade:
    """
    Facade die de oude TrikaSystem API emuleert.

    Gebruik dit voor drop-in replacement van oude systeem.
    """

    def __init__(self, use_federated: bool = True, **kwargs):
        """
        Initialize met backward compatible API.

        Args:
            use_federated: Gebruik nieuw systeem indien True
            **kwargs: Doorgegeven aan adapter config
        """
        mode = (
            MigrationMode.FEDERATED_ONLY if use_federated else MigrationMode.LEGACY_ONLY
        )
        config = AdapterConfig(mode=mode, **kwargs)
        self._adapter = TrikaMigrationAdapter(config)
        self._cycle_count = 0

    async def cycle(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Legacy API: cycle() methode.

        Args:
            market_data: Market data dictionary

        Returns:
            Result dictionary (backward compatible formaat)
        """
        self._cycle_count += 1
        result = await self._adapter.process_cycle(market_data)

        # Zorg voor backward compatible output
        return {
            "cycle": result.get("cycle", self._cycle_count),
            "action": result.get("decision", {}).get("action", "hold"),
            "confidence": result.get("decision", {}).get("confidence", 0.5),
            "rationale": result.get("decision", {}).get("rationale", ""),
            "council_views": result.get("council_views", {}),
            "latency_ms": result.get("latency_ms", 0),
            "federated": result.get("source") != "legacy_system",
        }

    def get_state(self) -> Dict:
        """Legacy API: get state"""
        return self._adapter.get_metrics()


# =============================================================================
# TEST SUITE
# =============================================================================


async def test_migration_adapter():
    """Test de migratie adapter"""
    print("\n" + "=" * 60)
    print("TESTING: Migration Adapter")
    print("=" * 60)

    results = {"passed": 0, "failed": 0, "errors": []}

    async def run_test(name: str, test_func):
        try:
            await test_func()
            print(f"  PASS: {name}")
            results["passed"] += 1
            return True
        except AssertionError as e:
            print(f"  FAIL: {name}: {e}")
            results["failed"] += 1
            results["errors"].append((name, str(e)))
            return False
        except Exception as e:
            print(f"  ERROR: {name}: {e}")
            results["failed"] += 1
            results["errors"].append((name, str(e)))
            return False

    # Test 1: Federated only mode
    async def test_federated_only():
        adapter = TrikaMigrationAdapter(
            AdapterConfig(mode=MigrationMode.FEDERATED_ONLY)
        )

        result = await adapter.process_cycle(
            {"price": 45000, "change": 0.05, "volume": 1000000}
        )

        assert result["success"] == True
        assert "decision" in result

    await run_test("Federated only mode", test_federated_only)

    # Test 2: Facade backward compatibility
    async def test_facade():
        facade = TrikaSystemFacade(use_federated=True)

        result = await facade.cycle({"price": 45000, "change": 0.05, "volume": 1000000})

        # Check backward compatible output
        assert "action" in result
        assert "confidence" in result
        assert "rationale" in result
        assert result["federated"] == True

    await run_test("Facade backward compatibility", test_facade)

    # Test 3: Mode switching
    async def test_mode_switching():
        adapter = TrikaMigrationAdapter(
            AdapterConfig(mode=MigrationMode.FEDERATED_ONLY)
        )

        # Start in federated mode
        result1 = await adapter.process_cycle(
            {"price": 45000, "change": 0.05, "volume": 1000000}
        )
        assert result1["success"] == True

        # Switch mode
        if OLD_SYSTEM_AVAILABLE:
            adapter.switch_mode(MigrationMode.LEGACY_ONLY)
            metrics = adapter.get_metrics()
            assert metrics["mode"] == "legacy_only"

    await run_test("Mode switching", test_mode_switching)

    # Test 4: Metrics
    async def test_metrics():
        adapter = TrikaMigrationAdapter(
            AdapterConfig(mode=MigrationMode.FEDERATED_ONLY)
        )

        # Run een paar cycles
        for _ in range(3):
            await adapter.process_cycle(
                {"price": 45000, "change": 0.05, "volume": 1000000}
            )

        metrics = adapter.get_metrics()

        assert metrics["cycles_run"] == 3
        assert metrics["new_system_available"] == True

    await run_test("Metrics collection", test_metrics)

    # Summary
    print("\n" + "=" * 60)
    print(f"RESULTS: {results['passed']} passed, {results['failed']} failed")
    print("=" * 60)

    return results["failed"] == 0


async def test_backward_compatibility():
    """Test backward compatibility met oude systeem"""
    print("\n" + "=" * 60)
    print("TESTING: Backward Compatibility")
    print("=" * 60)

    if not OLD_SYSTEM_AVAILABLE:
        print("  SKIP: Old system not available")
        return True

    results = {"passed": 0, "failed": 0, "errors": []}

    async def run_test(name: str, test_func):
        try:
            await test_func()
            print(f"  PASS: {name}")
            results["passed"] += 1
            return True
        except Exception as e:
            print(f"  FAIL: {name}: {e}")
            results["failed"] += 1
            results["errors"].append((name, str(e)))
            return False

    # Test: Output format consistency
    async def test_output_format():
        # Oude systeem
        old_system = OldTrikaSystem()
        old_result = await old_system.cycle(
            {"price": 45000, "change": 0.05, "volume": 1000000}
        )

        # Nieuwe facade
        facade = TrikaSystemFacade(use_federated=True)
        new_result = await facade.cycle(
            {"price": 45000, "change": 0.05, "volume": 1000000}
        )

        # Check dat beide dezelfde velden hebben
        required_fields = ["action", "confidence", "rationale"]
        for field in required_fields:
            assert field in old_result, f"Old system missing {field}"
            assert field in new_result, f"New system missing {field}"

    await run_test("Output format consistency", test_output_format)

    # Summary
    print("\n" + "=" * 60)
    print(f"RESULTS: {results['passed']} passed, {results['failed']} failed")
    print("=" * 60)

    return results["failed"] == 0


async def run_migration_tests():
    """Run alle migratie tests"""
    print("\n" + "=" * 60)
    print("MIGRATION ADAPTER TEST SUITE")
    print("=" * 60)

    all_passed = True

    if not await test_migration_adapter():
        all_passed = False

    if not await test_backward_compatibility():
        all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("ALL MIGRATION TESTS PASSED (100%)")
    else:
        print("SOME MIGRATION TESTS FAILED")
    print("=" * 60)

    return all_passed


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import sys

    success = asyncio.run(run_migration_tests())
    sys.exit(0 if success else 1)
