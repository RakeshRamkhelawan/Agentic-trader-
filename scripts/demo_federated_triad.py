#!/usr/bin/env python3
"""
FEDERATED TRIAD DEMONSTRATIE
Laat zien hoe het nieuwe systeem werkt in vergelijking met het oude.
"""

import asyncio
from datetime import datetime

from trika_federated_system import (CouncilType, FederatedChitta,
                                    FederatedTriadSystem, KnowledgeNode)


async def demo_chitta_knowledge_graph():
    """Demonstratie van Chitta als gedeelde kennisbron"""
    print("\n" + "=" * 60)
    print("DEMO 1: Chitta Mahasagar (Gedeelde Kennis)")
    print("=" * 60)

    chitta = FederatedChitta()

    # Simuleer market data ingesmeten door Body
    print("\n1. Body ingesmeten ruwe market data:")
    for i in range(3):
        chitta.add_node(
            KnowledgeNode(
                id=f"market_{i}",
                content=f"BTC prijs: ${45000 + i*500}",
                source="exchange_api",
                timestamp=datetime.now(),
                council_origin=CouncilType.BODY,
                metadata={
                    "type": "market_snapshot",
                    "price": 45000 + i * 500,
                    "change": 0.02 + i * 0.01,
                    "volume": 1000000 + i * 100000,
                },
            )
        )
    print(f"   [OK] {len(chitta._nodes)} market data nodes toegevoegd")

    # Guna Council analyseert vanuit eigen perspectief
    print("\n2. Guna Council analyseert (alleen guna/market data zichtbaar):")
    chitta.add_node(
        KnowledgeNode(
            id="guna_analysis_1",
            content="Sattva dominant: markt toont kalmte",
            source="guna_llm",
            timestamp=datetime.now(),
            council_origin=CouncilType.GUNA,
            metadata={"guna": "sattva", "intensity": 0.8, "type": "analysis"},
        )
    )

    guna_view = chitta.query(CouncilType.GUNA, {})
    print(f"   [OK] Guna ziet {len(guna_view)} nodes (eigen analyse + market data)")

    # Elemental Council analyseert
    print("\n3. Elemental Council analyseert (alleen element/market data zichtbaar):")
    chitta.add_node(
        KnowledgeNode(
            id="element_analysis_1",
            content="Fire element rising: volatiliteit neemt toe",
            source="elemental_llm",
            timestamp=datetime.now(),
            council_origin=CouncilType.ELEMENTAL,
            metadata={"fire": 0.8, "water": 0.2, "type": "analysis"},
        )
    )

    elem_view = chitta.query(CouncilType.ELEMENTAL, {})
    print(f"   [OK] Elemental ziet {len(elem_view)} nodes")

    # Mind Council ziet ALLES
    print("\n4. Mind Council (Buddhi) ziet ALLE perspectives:")
    mind_view = chitta.query(CouncilType.MIND, {})
    print(f"   [OK] Mind ziet {len(mind_view)} nodes (alle councils)")

    for node in mind_view:
        print(f"      - {node.council_origin.value}: {node.content[:50]}...")

    # Cross-verificatie
    print("\n5. Mind kan cross-verifieren:")
    guna_node = chitta.get_node("guna_analysis_1")
    elemental_node = chitta.get_node("element_analysis_1")

    print(f"   [OK] Guna zegt: {guna_node.content}")
    print(f"   [OK] Elemental zegt: {elemental_node.content}")
    print("   [OK] Mind kan zien dat 'Sattva' (kalmte) en 'Fire' (volatiliteit)")
    print("      contradictorisch lijken - dit vereist discriminatie!")


async def demo_council_indices():
    """Demonstratie van council-specifieke indices"""
    print("\n" + "=" * 60)
    print("DEMO 2: Council Indices (Perspectieven)")
    print("=" * 60)

    from trika_federated_system import CouncilIndex

    chitta = FederatedChitta()

    # Voeg diverse data toe
    print("\n1. Toevoegen diverse markt data:")

    # Bullish data (Sattva)
    for i in range(5):
        chitta.add_node(
            KnowledgeNode(
                id=f"sattva_{i}",
                content=f"Bullish signal {i}",
                source="market",
                timestamp=datetime.now(),
                council_origin=CouncilType.GUNA,
                metadata={"guna": "sattva", "intensity": 0.7},
            )
        )

    # Bearish data (Tamas)
    for i in range(2):
        chitta.add_node(
            KnowledgeNode(
                id=f"tamas_{i}",
                content=f"Bearish signal {i}",
                source="market",
                timestamp=datetime.now(),
                council_origin=CouncilType.GUNA,
                metadata={"guna": "tamas", "intensity": 0.6},
            )
        )

    print("   [OK] 5 Sattva (bullish) + 2 Tamas (bearish) signals")

    # Guna Index update
    print("\n2. Guna Index analyseert balans:")
    guna_index = CouncilIndex(CouncilType.GUNA, chitta, update_interval_seconds=0)
    await guna_index.update()

    idx_data = guna_index.get_index()
    scores = idx_data["data"]["scores"]
    print(f"   [OK] Sattva: {scores['sattva']:.1%}")
    print(f"   [OK] Rajas:  {scores['rajas']:.1%}")
    print(f"   [OK] Tamas:  {scores['tamas']:.1%}")
    print(f"   [OK] Dominant: {idx_data['data']['dominant']}")

    # Elemental Index
    print("\n3. Elemental Index analyseert:")

    chitta.add_node(
        KnowledgeNode(
            id="fire_signal",
            content="High volatility",
            source="market",
            timestamp=datetime.now(),
            council_origin=CouncilType.ELEMENTAL,
            metadata={
                "fire": 0.9,
                "water": 0.1,
                "type": "market_snapshot",
                "volatility": 0.4,
            },
        )
    )

    elem_index = CouncilIndex(CouncilType.ELEMENTAL, chitta, update_interval_seconds=0)
    await elem_index.update()

    elem_data = elem_index.get_index()
    elements = elem_data["data"]["elements"]
    print(f"   [OK] Fire:  {elements['fire']:.1%}")
    print(f"   [OK] Water: {elements['water']:.1%}")
    print(f"   [OK] Earth: {elements['earth']:.1%}")
    print(f"   [OK] State: {elem_data['data']['state']}")


async def demo_cooperative_deliberation():
    """Demonstratie van iteratieve deliberatie"""
    print("\n" + "=" * 60)
    print("DEMO 3: Cooperative Deliberation (Iteratieve Samenwerking)")
    print("=" * 60)

    from trika_federated_system import CooperativeDeliberation

    chitta = FederatedChitta()
    deliberation = CooperativeDeliberation(chitta, max_iterations=3)

    print("\n1. Start deliberatie met 3 councils:")
    print("   - Guna Council (3 gunas)")
    print("   - Elemental Council (5 elementen)")
    print("   - Graha Council (9 planeten)")

    market_data = {
        "price": 45000,
        "change": 0.05,  # +5%
        "volume": 1500000,  # Hoog volume
        "volatility": 0.35,  # Hoge volatiliteit
    }

    print("\n2. Market context:")
    print(f"   - Price: ${market_data['price']:,}")
    print(f"   - Change: {market_data['change']:+.1%}")
    print(f"   - Volume: {market_data['volume']:,}")
    print(f"   - Volatility: {market_data['volatility']:.1%}")

    views = await deliberation.deliberate(
        councils=[CouncilType.GUNA, CouncilType.ELEMENTAL, CouncilType.GRAHA],
        context={"cycle": 1},
        market_data=market_data,
    )

    print("\n3. Iteratieve deliberatie resultaten:")

    for name, view in views.items():
        print(f"\n   {name.upper()}:")
        print(f"      Perspective: {view.perspective}")
        print(f"      Confidence:  {view.confidence:.0%}")
        print(f"      Insights:    {', '.join(view.key_insights[:2])}")
        if view.contradictions:
            print(f"      !! Contradictions: {view.contradictions}")

    summary = deliberation.get_deliberation_summary()
    print("\n4. Deliberatie summary:")
    print(f"   [OK] Iteraties: {summary['iterations']}")
    print(f"   [OK] Converged: {summary['converged']}")
    print(f"   [OK] Councils:  {summary['councils_participated']}")


async def demo_buddhi_synthesis():
    """Demonstratie van Buddhi (Mind) synthesis"""
    print("\n" + "=" * 60)
    print("DEMO 4: Buddhi Mind (Discriminatie & Synthese)")
    print("=" * 60)

    from trika_federated_system import BuddhiMind, CouncilView

    chitta = FederatedChitta()
    mind = BuddhiMind(chitta)

    print("\n1. Buddhi ontvangt views van alle councils:")

    # Simuleer conflicting views
    views = {
        "guna": CouncilView(
            council_name="guna",
            perspective="sattva_dominant",  # Bullish (kalmte)
            confidence=0.8,
            key_insights=["Markt toont kalmte", "Heldere trend"],
            supporting_evidence=["node_1"],
        ),
        "elemental": CouncilView(
            council_name="elemental",
            perspective="fire_rising",  # Ook bullish (momentum)
            confidence=0.75,
            key_insights=["Hoge volatiliteit", "Momentum neemt toe"],
            supporting_evidence=["node_2"],
        ),
        "graha": CouncilView(
            council_name="graha",
            perspective="rahu_active",  # Bearish (illusie/FOMO)
            confidence=0.7,
            key_insights=["Hoge volume = FOMO", "Wees voorzichtig"],
            supporting_evidence=["node_3"],
            contradictions=["guna_sattva"],  # Directe contradictie!
        ),
    }

    for name, view in views.items():
        print(f"\n   {name}:")
        print(f"      -> {view.perspective} (confidence: {view.confidence:.0%})")

    print("\n2. Buddhi analyseert contradicties:")
    print("   !! Guna (Sattva/kalmte) vs Graha (Rahu/FOMO) = CONFLICT")

    decision = await mind.synthesize(views)

    print("\n3. Buddhi's beslissing:")
    print(f"   [OK] Action: {decision.action.value.upper()}")
    print(f"   [OK] Confidence: {decision.confidence:.0%}")
    print(f"   [OK] Rationale: {decision.rationale}")
    print(f"   [OK] Supporting: {', '.join(decision.supporting_councils)}")
    print(f"   [OK] Opposing: {', '.join(decision.opposing_councils)}")
    print(f"   [OK] Contradictions detected: {decision.contradictions_detected}")

    print("\n4. Beslissing wordt opgeslagen in Chitta voor audit:")
    decisions_in_chitta = chitta.query(
        CouncilType.MIND, {"metadata": {"type": "mind_decision"}}
    )
    print(f"   [OK] {len(decisions_in_chitta)} decision(s) in Chitta")


async def demo_full_system():
    """Demonstratie van het volledige systeem"""
    print("\n" + "=" * 60)
    print("DEMO 5: Volledig Federated Triad System")
    print("=" * 60)

    system = FederatedTriadSystem(
        enable_caching=True, deliberation_iterations=3, chitta_max_nodes=1000
    )

    print("\n1. Initialisatie:")
    print("   [OK] Chitta Mahasagar (gedeelde kennis)")
    print("   [OK] 3 Council Indices (Guna, Elemental, Graha)")
    print("   [OK] Cooperative Deliberation")
    print("   [OK] Buddhi Mind (synthese)")
    print("   [OK] Body Execution")

    # Simuleer 5 market cycles
    print("\n2. Running 5 market cycles:")

    scenarios = [
        {"price": 45000, "change": 0.05, "volume": 1000000, "volatility": 0.20},
        {"price": 46500, "change": 0.033, "volume": 1200000, "volatility": 0.25},
        {"price": 46000, "change": -0.011, "volume": 800000, "volatility": 0.15},
        {"price": 47000, "change": 0.022, "volume": 1500000, "volatility": 0.30},
        {"price": 46800, "change": -0.004, "volume": 900000, "volatility": 0.18},
    ]

    for i, scenario in enumerate(scenarios):
        print(f"\n   Cycle {i+1}:")
        print(f"      BTC: ${scenario['price']:,} ({scenario['change']:+.1%})")

        result = await system.process_cycle(scenario)

        decision = result["decision"]
        print(
            f"      -> Decision: {decision['action'].upper()} "
            f"(confidence: {decision['confidence']:.0%})"
        )
        print(f"      -> Latency: {result['latency_ms']:.1f}ms")

        if result.get("execution"):
            exec_data = result["execution"]
            if exec_data["action"] in ["buy", "sell"]:
                print(
                    f"      -> Executed: {exec_data['action']} "
                    f"@ ${exec_data.get('price', 0):,}"
                )

    print("\n3. Systeem state:")
    state = system.get_system_state()

    print(f"   [OK] Total cycles: {state['cycle_count']}")
    print(f"   [OK] Chitta nodes: {state['chitta']['total_nodes']}")
    print(f"   [OK] Decisions: {state['mind'].get('total_decisions', 0)}")
    print(
        f"   [OK] Portfolio value: ${state['body_state']['cash'] + state['body_state']['holdings'] * scenarios[-1]['price']:,.2f}"
    )
    print(f"   [OK] Cash: ${state['body_state']['cash']:,.2f}")
    print(f"   [OK] BTC: {state['body_state']['holdings']:.6f}")


async def main():
    """Hoofd demonstratie"""
    print("\n" + "=" * 60)
    print("FEDERATED TRIAD ARCHITECTURE")
    print("Demonstratie van het 5-Council Trika Systeem")
    print("=" * 60)

    await demo_chitta_knowledge_graph()
    await demo_council_indices()
    await demo_cooperative_deliberation()
    await demo_buddhi_synthesis()
    await demo_full_system()

    print("\n" + "=" * 60)
    print("DEMONSTRATIE VOLTOOID")
    print("=" * 60)
    print("\nKey Takeaways:")
    print("1. Chitta = Één gedeelde kennisbron (geen silo's)")
    print("2. Councils hebben perspectieven, niet aparte RAGs")
    print("3. Mind (Buddhi) kan ALLES zien en cross-verifieren")
    print("4. Iteratieve deliberatie = cooperatie, niet concurrentie")
    print("5. Audit trail = volledige transparantie")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
