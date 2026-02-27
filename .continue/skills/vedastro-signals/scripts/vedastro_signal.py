#!/usr/bin/env python3
"""
VedAstro Signal Generator - Generate Vedic astrological trading signals.

Usage:
    python vedastro_signal.py --symbol BTC --date today
    python vedastro_signal.py --symbol XAU --planet JUPITER --aspect
    python vedastro_signal.py --element fire --assets BTC,SOL,NVDA
    python vedastro_signal.py --batch --assets BTC,ETH,SOL --output report.json
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


async def generate_signal(symbol: str, date_str: str, verbose: bool = False):
    """Generate VedAstro signal for a symbol."""

    print(f"\n{'='*70}")
    print(f"VedAstro Signal: {symbol}")
    print(f"{'='*70}")

    # Parse date
    if date_str.lower() == 'today':
        date = datetime.now()
    else:
        date = datetime.strptime(date_str, '%Y-%m-%d')

    print(f"Date: {date.strftime('%Y-%m-%d')}")

    try:
        # Try to import VedAstro components
        from backend.vedastro import TattvaOrchestrator

        orchestrator = TattvaOrchestrator()
        await orchestrator.initialize(assets=[symbol])

        # Mock tick data for signal generation
        tick = {
            'symbol': symbol,
            'price': 0.0,  # Price doesn't affect VedAstro calculation
            'volume': 0
        }

        result = await orchestrator.process_market_tick(symbol, tick)

        print(f"\n[SIGNAL RESULT]")
        print(f"   Action:     {result['decision']['action'].upper()}")
        print(f"   Confidence: {result['decision']['confidence']:.2f}")
        print(f"   Alignment:  {result.get('alignment_score', 0):.2f}")

        if verbose and 'vedastro_data' in result:
            print(f"\n🔮 VedAstro Data:")
            print(f"   {json.dumps(result['vedastro_data'], indent=2)}")

        return result

    except ImportError as e:
        print(f"[WARNING] VedAstro not available: {e}")
        print(f"   Generating mock signal for demonstration...")

        # Mock signal for demo
        mock_result = {
            'decision': {
                'action': 'buy' if hash(symbol) % 2 == 0 else 'hold',
                'confidence': 0.65
            },
            'alignment_score': 0.72,
            'vedastro_data': {
                'dominant_planet': 'JUPITER',
                'dasha_lord': 'VENUS',
                'yogas': ['Gaja Kesari', 'Dhana Yoga'],
                'tattva_balance': {'sattva': 0.4, 'rajas': 0.4, 'tamas': 0.2}
            }
        }

        print(f"\n[MOCK SIGNAL]")
        print(f"   Action:     {mock_result['decision']['action'].upper()}")
        print(f"   Confidence: {mock_result['decision']['confidence']:.2f}")
        print(f"   Alignment:  {mock_result['alignment_score']:.2f}")
        print(f"   Planet:     {mock_result['vedastro_data']['dominant_planet']}")

        return mock_result


def check_planetary_aspect(symbol: str, planet: str, aspect_type: Optional[str] = None):
    """Check planetary aspects for a symbol."""

    print(f"\n{'='*70}")
    print(f"Planetary Aspect: {planet} → {symbol}")
    print(f"{'='*70}")

    # Asset affinities
    affinities = {
        'SUN': ['BTC', 'SPX500', 'XAU', 'AAPL'],
        'MOON': ['ETH', 'EUR/USD', 'XAG', 'NFLX'],
        'MARS': ['BTC', 'SOL', 'OIL', 'NVDA'],
        'MERCURY': ['EUR/USD', 'LINK', 'NAS100', 'CRM'],
        'JUPITER': ['SPX500', 'GER40', 'DOT', 'MSFT'],
        'VENUS': ['ETH', 'EUR/GBP', 'XAG', 'JNJ'],
        'SATURN': ['ADA', 'GBP/USD', 'GER40', 'JPM'],
    }

    planet_upper = planet.upper()
    favored = affinities.get(planet_upper, [])

    is_favored = symbol.upper() in [s.upper() for s in favored]

    print(f"\n[PLANET] {planet_upper} Analysis:")
    print(f"   Trading Style: {get_planet_style(planet_upper)}")
    print(f"   {symbol} favored: {'✅ Yes' if is_favored else '⚠️ No'}")

    if favored:
        print(f"   Favored assets: {', '.join(favored[:5])}")

    if aspect_type:
        print(f"   Aspect: {aspect_type}")
        print(f"   Signal: {'Bullish' if is_favored else 'Neutral/Caution'}")

    return {'favored': is_favored, 'planet': planet_upper, 'symbol': symbol}


def get_planet_style(planet: str) -> str:
    """Get trading style for a planet."""
    styles = {
        'SUN': 'Trend following',
        'MOON': 'Sentiment/Sentiment',
        'MARS': 'Momentum/Breakout',
        'MERCURY': 'Scalping/Quick trades',
        'JUPITER': 'Value/Growth',
        'VENUS': 'Value/Income',
        'SATURN': 'Disciplined/Long-term',
        'RAHU': 'Speculative (avoid)',
        'KETU': 'Exit-focused'
    }
    return styles.get(planet, 'Unknown')


def elemental_filter(element: str, assets: list[str], min_score: float = 0.5):
    """Filter assets by elemental alignment."""

    print(f"\n{'='*70}")
    print(f"Elemental Filter: {element.upper()}")
    print(f"{'='*70}")

    # Element definitions
    elements = {
        'fire': {'assets': ['BTC', 'SOL', 'NVDA', 'MSTR'], 'style': 'Aggressive/Trend'},
        'water': {'assets': ['ETH', 'EUR/USD', 'XAG', 'TLT'], 'style': 'Adaptive/Sentiment'},
        'earth': {'assets': ['ADA', 'JPM', 'PG', 'XLU'], 'style': 'Stable/Value'},
        'air': {'assets': ['LINK', 'EUR/GBP', 'CRM', 'XLK'], 'style': 'Volatile/Momentum'},
        'ether': {'assets': ['DOT', 'MSFT', 'SPX500', 'QQQ'], 'style': 'Growth/Expansion'}
    }

    elem = element.lower()
    if elem not in elements:
        print(f"[ERROR] Unknown element: {element}")
        print(f"   Valid: fire, water, earth, air, ether")
        return []

    print(f"\n[ELEMENT] {elem.upper()} Characteristics:")
    print(f"   Style: {elements[elem]['style']}")

    # Check alignment
    element_assets = elements[elem]['assets']
    aligned = [a for a in assets if a.upper() in [ea.upper() for ea in element_assets]]

    print(f"\n[FILTER RESULTS] (min score: {min_score}):")
    for asset in assets:
        score = 0.85 if asset in aligned else 0.35
        status = '✅' if score >= min_score else '❌'
        print(f"   {status} {asset:<10} Score: {score:.2f}")

    return aligned


async def batch_analysis(assets: list[str], output: Optional[str] = None):
    """Analyze multiple assets."""

    print(f"\n{'='*70}")
    print(f"Batch Analysis: {len(assets)} assets")
    print(f"{'='*70}")

    results = {}
    for asset in assets:
        result = await generate_signal(asset, 'today')
        results[asset] = result

    # Summary
    print(f"\n[SUMMARY]:")
    print(f"   {'Asset':<10} {'Signal':<8} {'Conf':<6} {'Align':<6}")
    print(f"   {'-'*35}")
    for asset, result in results.items():
        sig = result['decision']['action']
        conf = result['decision']['confidence']
        align = result.get('alignment_score', 0)
        print(f"   {asset:<10} {sig:<8} {conf:<6.2f} {align:<6.2f}")

    if output:
        with open(output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n[SAVED] Results to: {output}")

    return results


async def main():
    parser = argparse.ArgumentParser(
        description='Generate VedAstro trading signals'
    )
    parser.add_argument('--symbol', '-s', help='Asset symbol (BTC, ETH, etc.)')
    parser.add_argument('--date', '-d', default='today',
                       help='Date (YYYY-MM-DD or "today")')
    parser.add_argument('--planet', '-p',
                       help='Planet to check (JUPITER, SATURN, etc.)')
    parser.add_argument('--aspect', '-a', action='store_true',
                       help='Show planetary aspects')
    parser.add_argument('--element', '-e',
                       help='Filter by element (fire, water, earth, air, ether)')
    parser.add_argument('--assets',
                       help='Comma-separated asset list')
    parser.add_argument('--min-score', type=float, default=0.5,
                       help='Minimum alignment score')
    parser.add_argument('--batch', '-b', action='store_true',
                       help='Batch analysis mode')
    parser.add_argument('--output', '-o', help='Output file (JSON)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')

    args = parser.parse_args()

    if args.batch and args.assets:
        assets = [a.strip() for a in args.assets.split(',')]
        await batch_analysis(assets, args.output)

    elif args.element and args.assets:
        assets = [a.strip() for a in args.assets.split(',')]
        elemental_filter(args.element, assets, args.min_score)

    elif args.symbol and args.planet:
        check_planetary_aspect(args.symbol, args.planet,
                              'conjunction' if args.aspect else None)

    elif args.symbol:
        await generate_signal(args.symbol, args.date, args.verbose)

    else:
        parser.print_help()
        print("\n💡 Examples:")
        print("   python vedastro_signal.py --symbol BTC")
        print("   python vedastro_signal.py --symbol BTC --planet JUPITER")
        print("   python vedastro_signal.py --element fire --assets BTC,SOL,NVDA")
        print("   python vedastro_signal.py --batch --assets BTC,ETH,SOL --output report.json")


if __name__ == '__main__':
    asyncio.run(main())
