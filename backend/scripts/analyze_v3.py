"""Analyze v3 backtest results to diagnose poor performance."""

import csv
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
RESULTS = ROOT / "backend" / "data" / "backtest_results"
LOGS = ROOT / "backend" / "data" / "backtest_logs"

# 1. Symbol-level analysis
with open(RESULTS / "unified_per_symbol.csv") as f:
    rows = list(csv.DictReader(f))

total_trades = sum(int(r["trades"]) for r in rows)
total_wins = sum(int(r["wins"]) for r in rows)
total_losses = sum(int(r["losses"]) for r in rows)
winners = [r for r in rows if float(r["total_pnl"]) > 0]
losers = [r for r in rows if float(r["total_pnl"]) <= 0]
total_pnl = sum(float(r["total_pnl"]) for r in rows)

print("=" * 60)
print("PROBLEEM DIAGNOSE v3 BACKTEST")
print("=" * 60)
print(f"Capital deployed: ${100000 * len(rows):,.0f}")
print(f"Total PnL: ${total_pnl:,.0f}")
ret = total_pnl / (100000 * len(rows)) * 100
print(f"Return: {ret:.2f}%")
print()
print(f"Total trades: {total_trades}")
avg_trades = total_trades / len(rows)
print(f"Avg trades per symbol: {avg_trades:.0f}")
wr = total_wins / total_trades * 100
print(f"Win rate: {wr:.1f}%")
print()
print(f"Profitable symbols: {len(winners)} ({len(winners)/len(rows)*100:.0f}%)")
print(f"Losing symbols: {len(losers)} ({len(losers)/len(rows)*100:.0f}%)")
if winners:
    avg_w = sum(float(r["total_pnl"]) for r in winners) / len(winners)
    print(f"Avg profit on winners: ${avg_w:,.0f}")
if losers:
    avg_l = sum(float(r["total_pnl"]) for r in losers) / len(losers)
    print(f"Avg loss on losers: ${avg_l:,.0f}")

# 2. Buddhi decision distribution
print()
print("=" * 60)
print("BUDDHI DECISIONS")
print("=" * 60)
decisions = {}
exec_count = 0
blocked_count = 0
entry_confidences = []

with open(LOGS / "unified_decisions.jsonl") as f:
    for line in f:
        d = json.loads(line)
        agent = d.get("agent", "")
        if agent == "BuddhiMind":
            dec = d.get("decision", "?")
            decisions[dec] = decisions.get(dec, 0) + 1
            if d.get("executable"):
                exec_count += 1
            elif dec in ("bullish", "bearish"):
                blocked_count += 1
        elif agent == "TraderExecution" and d.get("action") == "open":
            conf = d.get("buddhi_conf", 0)
            entry_confidences.append(conf)

total_decisions = sum(decisions.values())
for k, v in sorted(decisions.items(), key=lambda x: -x[1]):
    pct = v / total_decisions * 100
    print(f"  {k}: {v:,} ({pct:.1f}%)")
print(f"  Executable signals: {exec_count:,} ({exec_count/total_decisions*100:.1f}%)")
print(f"  Blocked (direction but not executable): {blocked_count:,}")

if entry_confidences:
    print()
    avg_conf = sum(entry_confidences) / len(entry_confidences)
    print(f"  Avg entry confidence: {avg_conf:.3f}")
    print(f"  Min entry confidence: {min(entry_confidences):.3f}")
    print(f"  Max entry confidence: {max(entry_confidences):.3f}")

# 3. Exit reasons
print()
print("=" * 60)
print("EXIT REASON ANALYSIS")
print("=" * 60)
pnl_by_reason = {}
count_by_reason = {}
wins_by_reason = {}

with open(LOGS / "unified_decisions.jsonl") as f:
    for line in f:
        d = json.loads(line)
        if d.get("agent") == "PositionTracker" and d.get("action") == "close":
            reason = d.get("reason", "unknown")
            pnl = d.get("pnl", 0)
            pnl_by_reason[reason] = pnl_by_reason.get(reason, 0) + pnl
            count_by_reason[reason] = count_by_reason.get(reason, 0) + 1
            if pnl > 0:
                wins_by_reason[reason] = wins_by_reason.get(reason, 0) + 1

for reason in sorted(count_by_reason.keys(), key=lambda r: -count_by_reason[r]):
    cnt = count_by_reason[reason]
    total = pnl_by_reason[reason]
    avg = total / cnt
    w = wins_by_reason.get(reason, 0)
    wrr = w / cnt * 100
    print(f"  {reason}:")
    print(f"    Count: {cnt:,} ({cnt/sum(count_by_reason.values())*100:.1f}%)")
    print(f"    Total PnL: ${total:,.0f}")
    print(f"    Avg PnL: ${avg:,.2f}")
    print(f"    Win Rate: {wrr:.0f}%")

# 4. Position size analysis
print()
print("=" * 60)
print("POSITION SIZE ANALYSIS")
print("=" * 60)
sizes = []
with open(LOGS / "unified_decisions.jsonl") as f:
    for line in f:
        d = json.loads(line)
        if d.get("agent") == "TraderExecution" and d.get("action") == "open":
            sizes.append(d.get("size_usd", 0))

if sizes:
    avg_size = sum(sizes) / len(sizes)
    print(f"  Avg position size: ${avg_size:,.0f}")
    print(f"  Min position size: ${min(sizes):,.0f}")
    print(f"  Max position size: ${max(sizes):,.0f}")
    print(f"  Avg % of capital: {avg_size/100000*100:.1f}%")
    print(f"  Max % of capital: {max(sizes)/100000*100:.1f}%")
