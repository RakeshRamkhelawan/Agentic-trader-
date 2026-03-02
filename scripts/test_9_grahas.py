#!/usr/bin/env python3
"""Test all 9 Navagrahas together"""

import asyncio
import sys
sys.path.insert(0, '/app')

from scripts.nava_graha_agents import NavaGrahaFactory
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')

async def test():
    print("=" * 70)
    print("🪐 TESTING ALL 9 NAVAGRAHAS")
    print("=" * 70)
    
    # Create full council
    council = NavaGrahaFactory.create_council()
    
    # Test market data
    test_data = {
        "symbol": "BTC-EUR",
        "price": 56789.50,
        "sma_20": 54321.00,
        "sma_50": 52345.00,
        "rsi": 58.5,
        "volatility": 28.5,
        "volume": 1500000,
        "volume_spike": True,
        "trend": "UP",
        "bb_position": 0.65,
        "recent_news": "Bitcoin ETF approval expected"
    }
    
    portfolio = {
        "cash": 100000,
        "BTC-EUR": {"quantity": 0.5, "entry_price": 52000}
    }
    
    print("\nConvening the full council of 9...")
    print("(This will make 9 parallel API calls to DeepSeek)\n")
    
    result = await council.convene("BTC-EUR", test_data, portfolio)
    
    print("\n" + "=" * 70)
    print("🪐 COUNCIL RESULTS")
    print("=" * 70)
    
    print(f"\nConsensus: {result['consensus']}")
    print(f"Confidence: {result['confidence']:.2f}")
    print(f"\nVote Distribution:")
    for view, count in result['vote_count'].items():
        bar = "█" * count + "░" * (9 - count)
        print(f"  {view.capitalize():10s}: {bar} ({count})")
    
    print(f"\nIndividual Graha Analysis:")
    print("-" * 70)
    
    # Group by view
    bullish = []
    bearish = []
    neutral = []
    
    for graha, opinion in result['opinions'].items():
        view = opinion.get('view', 'neutral').lower()
        conf = opinion.get('confidence', 0)
        strength = opinion.get('strength', 0)
        
        info = f"{graha} (conf:{conf:.2f}, str:{strength:.2f})"
        
        if view == 'bullish':
            bullish.append(info)
        elif view == 'bearish':
            bearish.append(info)
        else:
            neutral.append(info)
    
    if bullish:
        print(f"\n🟢 BULLISH ({len(bullish)}):")
        for g in bullish:
            print(f"   • {g}")
    
    if bearish:
        print(f"\n🔴 BEARISH ({len(bearish)}):")
        for g in bearish:
            print(f"   • {g}")
    
    if neutral:
        print(f"\n⚪ NEUTRAL ({len(neutral)}):")
        for g in neutral:
            print(f"   • {g}")
    
    # Special alerts
    print(f"\n" + "=" * 70)
    print("⚠️  SPECIAL ALERTS")
    print("=" * 70)
    
    alerts = result['special_alerts']
    
    if alerts['rahu_warnings']:
        print(f"\n🌑 RAHU (Illusion/Bubble) Warnings:")
        for w in alerts['rahu_warnings']:
            print(f"   ⚡ {w}")
    
    if alerts['ketu_exit_signal']:
        print(f"\n🔥 KETU (Exit) Signal: TRUE")
        print(f"   Consider exiting position!")
    
    if alerts['shukra_value_gap']:
        print(f"\n💎 SHUKRA (Value) Signals:")
        for s in alerts['shukra_value_gap']:
            print(f"   💠 {s}")
    
    print(f"\n" + "=" * 70)
    print("🕉️  TATTVA BALANCE")
    print("=" * 70)
    
    # Extract tattvas from opinions
    elements = {"ether": 0, "air": 0, "fire": 0, "water": 0, "earth": 0}
    gunas = {"sattva": 0, "rajas": 0, "tamas": 0}
    
    for opinion in result['opinions'].values():
        tattvas = opinion.get('tattvas_aligned', [])
        for t in tattvas:
            if t in elements:
                elements[t] += 1
            elif t in gunas:
                gunas[t] += 1
    
    print(f"\nElements:")
    for elem, count in elements.items():
        bar = "█" * count + "░" * (9 - count)
        print(f"  {elem.capitalize():10s}: {bar} ({count})")
    
    print(f"\nGunas:")
    for guna, count in gunas.items():
        bar = "█" * count + "░" * (9 - count)
        print(f"  {guna.capitalize():10s}: {bar} ({count})")
    
    print(f"\n" + "=" * 70)

if __name__ == "__main__":
    asyncio.run(test())
