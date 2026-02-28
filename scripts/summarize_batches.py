"""Summarize all batch results."""
import json
import numpy as np
from pathlib import Path

files = sorted(Path('backtest_results').glob('ml_batch_*.json'))
print(f"Total files: {len(files)}")
print()

total_features = 0
total_trades = 0
win_rates = []

for f in files:
    with open(f) as fp:
        data = json.load(fp)
    total_features += data['feature_count']
    total_trades += data['total_trades']
    win_rates.append(data['win_rate'])
    print(f"{f.stem}: {data['feature_count']} features, {data['total_trades']} trades, {data['win_rate']*100:.1f}% win")

print()
print("=" * 50)
print(f"TOTAL: {total_features:,} ML features")
print(f"TOTAL: {total_trades} trades")
print(f"AVG WIN RATE: {np.mean(win_rates)*100:.1f}%")
print(f"MIN WIN RATE: {np.min(win_rates)*100:.1f}%")
print(f"MAX WIN RATE: {np.max(win_rates)*100:.1f}%")
print("=" * 50)

# Check which batches have good win rates (>50%)
good_batches = [i+1 for i, wr in enumerate(win_rates) if wr > 0.50]
print(f"\nBatches with >50% win rate: {good_batches}")
