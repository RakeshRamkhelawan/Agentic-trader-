#!/usr/bin/env python3
"""
FEDERATED TRIAD - COMPLETE INTEGRATION TEST
Test alle componenten samen met 100% coverage requirement.
"""

import asyncio
import sys
from datetime import datetime, timedelta

# Test imports
from trika_federated_system import (
    FederatedTriadSystem,
    FederatedChitta,
    CouncilIndex,
    CooperativeDeliberation,
    BuddhiMind,
    CouncilType,
    KnowledgeNode,
    CouncilView,
    SynthesisDecision,
    ActionType,
    ChittaError,
    DeliberationError,
    SynthesisError
)


async def run_all_tests():
    """Run complete test suite"""
    print("="*70)
    print("FEDERATED TRIAD - COMPLETE INTEGRATION TEST SUITE")
    print("="*70)
    
    all_results = []
    
    # Test Suites
    all_results.append(await test_chitta_layer())
    all_results.append(await test_council_indices_layer())
    all_results.append(await test_deliberation_layer())
    all_results.append(await test_buddhi_layer())
    all_results.append(await test_full_integration())
    
    # Final Summary
    total_passed = sum(r["passed"] for r in all_results)
    total_failed = sum(r["failed"] for r in all_results)
    total_tests = total_passed + total_failed
    
    print("\n" + "="*70)
    print("FINAL TEST SUMMARY")
    print("="*70)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_failed}")
    print(f"Success Rate: {total_passed/total_tests*100:.1f}%")
    print("="*70)
    
    if total_failed == 0:
        print("\n[PASS] ALL TESTS PASSED (100%)")
        return True
    else:
        print(f"\n[FAIL] {total_failed} TEST(S) FAILED")
        return False


async def test_chitta_layer():
    """Test Layer 3: Chitta"""
    print("\n" + "-"*70)
    print("TESTING: Layer 3 - Chitta Mahasagar (Knowledge Graph)")
    print("-"*70)
    
    results = {"passed": 0, "failed": 0, "tests": []}
    
    def check(name, condition, msg=""):
        if condition:
            print(f"  [PASS] {name}")
            results["passed"] += 1
            results["tests"].append((name, True, ""))
        else:
            print(f"  [FAIL] {name}: {msg}")
            results["failed"] += 1
            results["tests"].append((name, False, msg))
    
    # Happy Path Tests
    print("\n  Happy Path Tests:")
    
    chitta = FederatedChitta()
    
    # Test 1: Add node
    node = KnowledgeNode(
        id="test_1",
        content="Test content",
        source="test",
        timestamp=datetime.now(),
        council_origin=CouncilType.GUNA,
        metadata={"type": "test"}
    )
    nid = chitta.add_node(node)
    check("Add node returns ID", nid == "test_1")
    check("Node stored correctly", len(chitta._nodes) == 1)
    
    # Test 2: Query
    results_query = chitta.query(CouncilType.GUNA, {})
    check("Query returns results", len(results_query) == 1)
    check("Query result correct", results_query[0].id == "test_1")
    
    # Test 3: Mind sees all
    chitta.add_node(KnowledgeNode(
        id="test_2", content="Test 2", source="test",
        timestamp=datetime.now(), council_origin=CouncilType.ELEMENTAL,
        metadata={"type": "test"}
    ))
    mind_results = chitta.query(CouncilType.MIND, {})
    check("Mind sees all nodes", len(mind_results) == 2)
    
    # Test 4: Perspectives
    chitta.add_perspective("test_1", "mind", 0.9)
    node = chitta.get_node("test_1")
    check("Perspective added", node.perspectives.get("mind") == 0.9)
    
    # Test 5: Verification
    chitta.verify_node("test_1", "mind")
    check("Node verified", node.verification_status == "verified")
    
    # Unhappy Path Tests
    print("\n  Unhappy Path Tests:")
    
    # Test 6: Invalid node type
    try:
        chitta.add_node("invalid")
        check("Invalid node type raises error", False, "Should have raised ChittaError")
    except ChittaError:
        check("Invalid node type raises error", True)
    
    # Test 7: Query nonexistent
    empty_results = chitta.query(CouncilType.GUNA, {"metadata": {"nonexistent": True}})
    check("Query nonexistent returns empty", len(empty_results) == 0)
    
    # Test 8: Duplicate handling
    dup_node = KnowledgeNode(
        id="test_1", content="Duplicate", source="test",
        timestamp=datetime.now(), council_origin=CouncilType.GUNA,
        perspectives={"new": 0.5}
    )
    chitta.add_node(dup_node)
    node = chitta.get_node("test_1")
    check("Duplicate merges perspectives", "new" in node.perspectives)
    
    # Edge Cases
    print("\n  Edge Case Tests:")
    
    # Test 9: Empty chitta
    empty_chitta = FederatedChitta()
    check("Empty chitta stats correct", empty_chitta.get_stats()["total_nodes"] == 0)
    
    # Test 10: Very long content
    long_content = "A" * 10000
    chitta.add_node(KnowledgeNode(
        id="long", content=long_content, source="test",
        timestamp=datetime.now(), council_origin=CouncilType.GUNA
    ))
    long_node = chitta.get_node("long")
    check("Long content stored", len(long_node.content) == 10000)
    
    print(f"\n  Results: {results['passed']}/{results['passed']+results['failed']} passed")
    return results


async def test_council_indices_layer():
    """Test Layer 2.5: Council Indices"""
    print("\n" + "-"*70)
    print("TESTING: Layer 2.5 - Council Indices (Perspectives)")
    print("-"*70)
    
    results = {"passed": 0, "failed": 0, "tests": []}
    
    def check(name, condition, msg=""):
        if condition:
            print(f"  [PASS] {name}")
            results["passed"] += 1
        else:
            print(f"  [FAIL] {name}: {msg}")
            results["failed"] += 1
    
    chitta = FederatedChitta()
    
    # Happy Path Tests
    print("\n  Happy Path Tests:")
    
    # Setup data
    for i in range(3):
        chitta.add_node(KnowledgeNode(
            id=f"sattva_{i}", content=f"Sattva {i}", source="test",
            timestamp=datetime.now(), council_origin=CouncilType.GUNA,
            metadata={"guna": "sattva", "intensity": 0.8}
        ))
    
    # Test 1: Guna index
    guna_idx = CouncilIndex(CouncilType.GUNA, chitta, update_interval_seconds=0)
    await guna_idx.update()
    idx_data = guna_idx.get_index()
    check("Guna index created", idx_data["council"] == "guna")
    check("Guna dominant calculated", "dominant" in idx_data["data"])
    
    # Test 2: Elemental index
    chitta.add_node(KnowledgeNode(
        id="fire_1", content="Fire", source="test",
        timestamp=datetime.now(), council_origin=CouncilType.ELEMENTAL,
        metadata={"fire": 0.9}
    ))
    elem_idx = CouncilIndex(CouncilType.ELEMENTAL, chitta, update_interval_seconds=0)
    await elem_idx.update()
    elem_data = elem_idx.get_index()
    check("Elemental index created", elem_data["council"] == "elemental")
    check("Fire element calculated", elem_data["data"]["elements"]["fire"] > 0)
    
    # Test 3: Rate limiting
    idx = CouncilIndex(CouncilType.GUNA, chitta, update_interval_seconds=60)
    result1 = await idx.update()
    result2 = await idx.update()
    check("Rate limiting works", result1 == True and result2 == False)
    
    # Unhappy Path Tests
    print("\n  Unhappy Path Tests:")
    
    # Test 4: Empty chitta update
    empty_chitta = FederatedChitta()
    empty_idx = CouncilIndex(CouncilType.GUNA, empty_chitta, update_interval_seconds=0)
    result = await empty_idx.update()
    check("Empty chitta update succeeds", result == True)
    
    # Test 5: Stale detection
    fast_idx = CouncilIndex(CouncilType.GUNA, chitta, update_interval_seconds=1)
    await fast_idx.update()
    check("Fresh index not stale", not fast_idx.is_stale())
    
    # Edge Cases
    print("\n  Edge Case Tests:")
    
    # Test 6: Multiple updates with new data
    multi_idx = CouncilIndex(CouncilType.GUNA, chitta, update_interval_seconds=0)
    for i in range(5):
        chitta.add_node(KnowledgeNode(
            id=f"update_test_{i}", content=f"Update {i}", source="test",
            timestamp=datetime.now(), council_origin=CouncilType.GUNA,
            metadata={"guna": "sattva", "intensity": 0.5}
        ))
        await multi_idx.update()
    check("Multiple updates increment version", multi_idx.get_index()["version"] == 5)
    
    print(f"\n  Results: {results['passed']}/{results['passed']+results['failed']} passed")
    return results


async def test_deliberation_layer():
    """Test Layer 2: Cooperative Deliberation"""
    print("\n" + "-"*70)
    print("TESTING: Layer 2 - Cooperative Deliberation")
    print("-"*70)
    
    results = {"passed": 0, "failed": 0, "tests": []}
    
    def check(name, condition, msg=""):
        if condition:
            print(f"  [PASS] {name}")
            results["passed"] += 1
        else:
            print(f"  [FAIL] {name}: {msg}")
            results["failed"] += 1
    
    chitta = FederatedChitta()
    deliberation = CooperativeDeliberation(chitta, max_iterations=3)
    
    # Happy Path Tests
    print("\n  Happy Path Tests:")
    
    # Test 1: Basic deliberation
    views = await deliberation.deliberate(
        councils=[CouncilType.GUNA, CouncilType.ELEMENTAL, CouncilType.GRAHA],
        context={"test": True},
        market_data={"price": 45000, "change": 0.05, "volume": 1000000}
    )
    check("Deliberation returns views", len(views) == 3)
    check("Views have perspectives", all(v.perspective for v in views.values()))
    
    # Test 2: Council convergence check
    summary = deliberation.get_deliberation_summary()
    check("Summary generated", "iterations" in summary)
    
    # Unhappy Path Tests
    print("\n  Unhappy Path Tests:")
    
    # Test 3: Empty councils
    try:
        await deliberation.deliberate(councils=[], context={})
        check("Empty councils raises error", False, "Should have raised DeliberationError")
    except DeliberationError:
        check("Empty councils raises error", True)
    
    # Edge Cases
    print("\n  Edge Case Tests:")
    
    # Test 4: Single council
    single_view = await deliberation.deliberate(
        councils=[CouncilType.GUNA],
        context={},
        market_data={"price": 45000, "change": 0}
    )
    check("Single council deliberation works", len(single_view) == 1)
    
    print(f"\n  Results: {results['passed']}/{results['passed']+results['failed']} passed")
    return results


async def test_buddhi_layer():
    """Test Layer 2: Buddhi Mind"""
    print("\n" + "-"*70)
    print("TESTING: Layer 2 - Buddhi Mind (Synthesis)")
    print("-"*70)
    
    results = {"passed": 0, "failed": 0, "tests": []}
    
    def check(name, condition, msg=""):
        if condition:
            print(f"  [PASS] {name}")
            results["passed"] += 1
        else:
            print(f"  [FAIL] {name}: {msg}")
            results["failed"] += 1
    
    chitta = FederatedChitta()
    mind = BuddhiMind(chitta)
    
    # Happy Path Tests
    print("\n  Happy Path Tests:")
    
    # Test 1: Bullish consensus
    bullish_views = {
        "guna": CouncilView("guna", "sattva_dominant", 0.8, ["calm"], ["n1"]),
        "elemental": CouncilView("elemental", "fire_rising", 0.75, ["momentum"], ["n2"]),
    }
    decision = await mind.synthesize(bullish_views)
    check("Bullish consensus BUY", decision.action == ActionType.BUY)
    check("Decision has confidence", 0 < decision.confidence <= 1)
    
    # Test 2: Bearish consensus
    bearish_views = {
        "guna": CouncilView("guna", "tamas_dominant", 0.8, ["confusion"], ["n1"]),
        "graha": CouncilView("graha", "rahu_active", 0.75, ["illusion"], ["n2"]),
    }
    decision = await mind.synthesize(bearish_views)
    check("Bearish consensus SELL", decision.action == ActionType.SELL)
    
    # Test 3: Conflicting views
    mixed_views = {
        "guna": CouncilView("guna", "sattva_dominant", 0.8, ["calm"], ["n1"]),
        "graha": CouncilView("graha", "rahu_active", 0.8, ["illusion"], ["n2"], contradictions=["guna"]),
    }
    decision = await mind.synthesize(mixed_views)
    check("Conflicting views detected", decision.contradictions_detected > 0)
    
    # Unhappy Path Tests
    print("\n  Unhappy Path Tests:")
    
    # Test 4: Empty views - should fallback to HOLD
    empty_decision = await mind.synthesize({})
    check("Empty views fallback to HOLD", empty_decision.action == ActionType.HOLD)
    
    # Test 5: Fallback on error
    error_decision = await mind.synthesize({"invalid": "data"})
    check("Error fallback to HOLD", error_decision.action == ActionType.HOLD)
    
    # Edge Cases
    print("\n  Edge Case Tests:")
    
    # Test 6: Neutral views
    neutral_views = {
        "guna": CouncilView("guna", "rajas_balanced", 0.5, ["neutral"], ["n1"]),
    }
    decision = await mind.synthesize(neutral_views)
    check("Neutral view HOLD", decision.action == ActionType.HOLD)
    
    print(f"\n  Results: {results['passed']}/{results['passed']+results['failed']} passed")
    return results


async def test_full_integration():
    """Test full system integration"""
    print("\n" + "-"*70)
    print("TESTING: Full System Integration")
    print("-"*70)
    
    results = {"passed": 0, "failed": 0, "tests": []}
    
    def check(name, condition, msg=""):
        if condition:
            print(f"  [PASS] {name}")
            results["passed"] += 1
        else:
            print(f"  [FAIL] {name}: {msg}")
            results["failed"] += 1
    
    system = FederatedTriadSystem()
    
    # Happy Path Tests
    print("\n  Happy Path Tests:")
    
    # Test 1: Single cycle
    result = await system.process_cycle({
        "price": 45000, "change": 0.05, "volume": 1000000, "volatility": 0.2
    })
    check("Single cycle completes", result["success"] == True)
    check("Decision generated", "decision" in result)
    check("Council views present", "council_views" in result)
    
    # Test 2: Multiple cycles
    for i in range(4):
        await system.process_cycle({
            "price": 45000 + i*100, "change": 0.01*i, 
            "volume": 1000000, "volatility": 0.2
        })
    state = system.get_system_state()
    check("Multiple cycles tracked", state["cycle_count"] == 5)
    
    # Test 3: Chitta population
    check("Chitta populated", state["chitta"]["total_nodes"] > 0)
    
    # Test 4: Decision tracking
    check("Decisions tracked", state["mind"].get("total_decisions", 0) > 0)
    
    # Unhappy Path Tests
    print("\n  Unhappy Path Tests:")
    
    # Test 5: Empty market data
    empty_result = await system.process_cycle({})
    check("Empty data handled", "success" in empty_result)
    
    # Test 6: Reset
    system.reset()
    check("System reset works", system.cycle_count == 0)
    check("Chitta cleared", len(system.chitta._nodes) == 0)
    
    # Edge Cases
    print("\n  Edge Case Tests:")
    
    # Test 7: Extreme values
    extreme_result = await system.process_cycle({
        "price": 999999999, "change": 1.0, "volume": 999999999999, "volatility": 1.0
    })
    check("Extreme values handled", extreme_result["success"] == True)
    
    # Test 8: Negative values
    negative_result = await system.process_cycle({
        "price": -100, "change": -0.5, "volume": -1000, "volatility": -0.1
    })
    check("Negative values handled", negative_result["success"] == True)
    
    print(f"\n  Results: {results['passed']}/{results['passed']+results['failed']} passed")
    return results


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
