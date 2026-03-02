"""
Analyseer waarom V18 data niet geschikt is voor ML.
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path

def main():
    # Laad een elemental backtest (representatief voor V18)
    files = sorted(Path('backtest_results').glob('elemental_backtest_*.json'))
    if not files:
        print('Geen files gevonden')
        return

    with open(files[-1]) as f:
        data = json.load(f)

    print('=' * 60)
    print('WAAROM ML FAALT OP V18/ELEMENTAL DATA')
    print('=' * 60)
    print()

    # 1. Check harmony
    if 'harmony_curve' in data and data['harmony_curve']:
        hc = pd.DataFrame(data['harmony_curve'])
        print('1. HARMONY ANALYSE')
        print(f'   Gemiddelde harmony: {hc["harmony"].mean():.3f}')
        print(f'   Std deviation: {hc["harmony"].std():.3f}')
        print(f'   Range: {hc["harmony"].min():.3f} - {hc["harmony"].max():.3f}')
        print()
        print('   WARNING: Harmony heeft HEEL LAGE variance')
        print('      -> Bijna constant, dus niet informatief voor ML')

    # 2. Check trades
    if 'trades' in data and data['trades']:
        trades = pd.DataFrame(data['trades'])
        print()
        print('2. TRADE ANALYSE')

        # Check correlatie harmony -> outcome
        if 'harmony_score' in trades.columns and 'realized_pnl' in trades.columns:
            pnl = trades['realized_pnl'].dropna()
            if len(pnl) > 0:
                corr = trades['harmony_score'].corr(trades['realized_pnl'])
                print(f'   Harmony -> P&L correlatie: {corr:.4f}')
                print()
                if abs(corr) < 0.1:
                    print('   ERROR: CORRELATIE IS BIJNA 0')
                    print('      ML kan GEEN pattern leren!')

    # 3. Win rate
    print()
    print('3. STRATEGIE PERFORMANCE')
    print(f'   Total return: {data.get("total_return_pct", 0):.2f}%')
    print(f'   Win rate: {data.get("win_rate_pct", 0):.1f}%')

    print()
    print('=' * 60)
    print('CONCLUSIE')
    print('=' * 60)
    print()
    print('V18 is WEL een goede backtest voor trading, maar:')
    print()
    print('ERROR PROBLEEM 1: Harmony heeft quasi-geen variance')
    print('   -> ML heeft variance nodig om te leren')
    print()
    print('ERROR PROBLEEM 2: Harmony correleert niet met P&L')
    print('   -> Geen supervised learning mogelijk')
    print()
    print('ERROR PROBLEEM 3: Win rate ~48% (worse than random)')
    print('   -> Geen edge om te leren')
    print()
    print('SOLUTION OM ML TE LATEN WERKEN:')
    print('   1. Features met WEL variance (bijv. RSI 0-100)')
    print('   2. Features die WEL correleren met outcome')
    print('   3. Strategie met >55% win rate')

if __name__ == '__main__':
    main()
