"""
V12 Signal Performance Analyzer
Koppelt signals aan trade outcomes en berekent adaptive weights.
"""
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta


def analyze_v12_performance(signals_path: str, exits_path: str,
                            time_window_min: int = 60,
                            output_weights: str = "agent_weights_v2.csv",
                            output_analysis: str = "signal_analysis_v2.csv"):
    """
    Link v12 signals aan trade outcomes en bereken adaptive weights.

    Args:
        signals_path: Path naar signals CSV (v12_all_agents_signals.csv)
        exits_path: Path naar trade exits CSV
        time_window_min: Max tijd tussen signaal en exit
    """

    print("="*80)
    print("V12 SIGNAL PERFORMANCE ANALYZER")
    print("="*80)

    # Load data
    print(f"\n[LOAD] Signals: {signals_path}")
    signals_df = pd.read_csv(signals_path)

    print(f"[LOAD] Exits: {exits_path}")
    exits_df = pd.read_csv(exits_path)

    # Parse timestamps
    signals_df['timestamp_dt'] = pd.to_datetime(signals_df['timestamp'])
    exits_df['timestamp_dt'] = pd.to_datetime(exits_df['timestamp'])

    print(f"\n[DATA] Signals: {len(signals_df)} records")
    print(f"[DATA] Exits: {len(exits_df)} records")

    # Link signals to outcomes
    print("\n[PROCESS] Linking signals to outcomes...")
    linked_records = []

    for _, signal in signals_df.iterrows():
        signal_time = signal['timestamp_dt']
        symbol = signal['symbol']

        # Find matching exits (same symbol, within time window, after signal)
        matching_exits = exits_df[
            (exits_df['symbol'] == symbol) &
            (exits_df['timestamp_dt'] > signal_time) &
            ((exits_df['timestamp_dt'] - signal_time).dt.total_seconds() / 60 <= time_window_min)
        ]

        if not matching_exits.empty:
            # Take first exit
            exit_row = matching_exits.iloc[0]

            linked_records.append({
                'timestamp': signal['timestamp'],
                'agent_name': signal['agent_name'],
                'symbol': signal['symbol'],
                'action': signal['action'],
                'confidence': signal['confidence'],
                'reasoning': signal['reasoning'],
                'weight': signal['weight'],
                # Parse features
                'rsi': parse_rsi(signal['reasoning']),
                'adx': parse_adx(signal['reasoning']),
                'regime': parse_regime(signal['reasoning']),
                # Outcome
                'exit_time': exit_row['timestamp'],
                'pnl': exit_row.get('pnl', 0),
                'exit_price': exit_row.get('exit_price', 0),
                'exit_reason': exit_row.get('exit_reason', 'unknown'),
                'was_correct': exit_row.get('pnl', 0) > 0
            })

    if not linked_records:
        print("[ERROR] No matching signals and exits found!")
        return None, None

    linked_df = pd.DataFrame(linked_records)
    print(f"[DONE] Linked {len(linked_df)} signals with outcomes")

    # Performance analysis per agent-symbol
    print("\n[ANALYZE] Calculating performance metrics...")

    perf_analysis = linked_df.groupby(['agent_name', 'symbol']).agg({
        'pnl': ['count', 'mean', 'sum', 'std'],
        'confidence': 'mean',
        'weight': 'mean',
        'was_correct': 'mean'
    }).round(4)

    perf_analysis.columns = ['trades', 'avg_pnl', 'total_pnl', 'pnl_std',
                            'avg_confidence', 'avg_weight', 'winrate']
    perf_analysis = perf_analysis.reset_index()

    # Calculate new adaptive weights
    print("\n[CALCULATE] Computing adaptive weights...")

    def calc_new_weight(row):
        """Calculate new weight based on performance."""
        base = 1.0

        # Winrate bonus (0.5 is neutral)
        winrate_bonus = (row['winrate'] - 0.5) * 0.8

        # PnL bonus (scaled)
        pnl_bonus = row['avg_pnl'] * 5

        # Consistency bonus (inverse of std)
        if row['pnl_std'] > 0:
            consistency_bonus = 0.1 / (1 + row['pnl_std'])
        else:
            consistency_bonus = 0

        new_weight = base + winrate_bonus + pnl_bonus + consistency_bonus
        return np.clip(new_weight, 0.1, 3.0)

    perf_analysis['new_weight'] = perf_analysis.apply(calc_new_weight, axis=1)
    perf_analysis['weight_change'] = perf_analysis['new_weight'] - perf_analysis['avg_weight']

    # Regime analysis
    print("\n[ANALYZE] Regime-specific performance...")
    regime_analysis = linked_df.groupby(['agent_name', 'regime']).agg({
        'pnl': ['count', 'mean'],
        'was_correct': 'mean'
    }).round(4)
    regime_analysis.columns = ['trades', 'avg_pnl', 'winrate']
    regime_analysis = regime_analysis.reset_index()

    # Save outputs
    print(f"\n[EXPORT] Saving to {output_weights}...")
    perf_analysis.to_csv(output_weights, index=False)

    print(f"[EXPORT] Saving detailed analysis to {output_analysis}...")
    linked_df.to_csv(output_analysis, index=False)

    # Print summary
    print("\n" + "="*80)
    print("TOP 10 PERFORMERS (by total PnL)")
    print("="*80)
    top_performers = perf_analysis.nlargest(10, 'total_pnl')[
        ['agent_name', 'symbol', 'trades', 'winrate', 'avg_pnl', 'total_pnl', 'new_weight']
    ]
    print(top_performers.to_string(index=False))

    print("\n" + "="*80)
    print("WORST 10 PERFORMERS (by total PnL)")
    print("="*80)
    worst_performers = perf_analysis.nsmallest(10, 'total_pnl')[
        ['agent_name', 'symbol', 'trades', 'winrate', 'avg_pnl', 'total_pnl', 'new_weight']
    ]
    print(worst_performers.to_string(index=False))

    print("\n" + "="*80)
    print("REGIME ANALYSIS")
    print("="*80)
    regime_summary = regime_analysis.groupby('regime').agg({
        'avg_pnl': 'mean',
        'winrate': 'mean',
        'trades': 'sum'
    }).round(4)
    print(regime_summary.to_string())

    # Agent divergence analysis
    print("\n" + "="*80)
    print("AGENT CONFLICT ANALYSIS")
    print("="*80)
    analyze_conflicts(linked_df)

    return perf_analysis, linked_df


def parse_rsi(reasoning: str) -> float:
    """Parse RSI from reasoning string."""
    try:
        if "RSI:" in reasoning:
            part = reasoning.split("RSI:")[1].split(",")[0].strip()
            return float(part)
    except:
        pass
    return np.nan


def parse_adx(reasoning: str) -> float:
    """Parse ADX from reasoning string."""
    try:
        if "ADX:" in reasoning:
            part = reasoning.split("ADX:")[1].split(",")[0].strip()
            return float(part)
    except:
        pass
    return np.nan


def parse_regime(reasoning: str) -> str:
    """Parse regime from reasoning string."""
    try:
        if "Regime:" in reasoning:
            part = reasoning.split("Regime:")[1].strip().lower()
            return part.split(",")[0].split(".")[0].strip()
    except:
        pass
    return "unknown"


def analyze_conflicts(df: pd.DataFrame):
    """Analyze when agents disagree."""
    # Find symbols where Sentiment and Analyst disagree
    conflicts = []

    for symbol in df['symbol'].unique():
        symbol_df = df[df['symbol'] == symbol]

        # Group by timestamp (approximate)
        for ts in symbol_df['timestamp'].unique():
            ts_df = symbol_df[symbol_df['timestamp'] == ts]

            if len(ts_df) > 1:
                actions = ts_df['action'].unique()
                if len(actions) > 1:  # Conflict!
                    sentiment = ts_df[ts_df['agent_name'] == 'SentimentAgentV2']
                    analyst = ts_df[ts_df['agent_name'] == 'Analyst']

                    if not sentiment.empty and not analyst.empty:
                        s_action = sentiment.iloc[0]['action']
                        a_action = analyst.iloc[0]['action']
                        pnl = analyst.iloc[0]['pnl']  # Outcome

                        conflicts.append({
                            'symbol': symbol,
                            'sentiment_action': s_action,
                            'analyst_action': a_action,
                            'outcome_pnl': pnl,
                            'analyst_won': pnl > 0 if a_action != 'HOLD' else None
                        })

    if conflicts:
        conflicts_df = pd.DataFrame(conflicts)
        print(f"Found {len(conflicts)} conflicts between Sentiment and Analyst")

        # Who wins?
        analyst_wins = conflicts_df['analyst_won'].sum()
        total_resolved = conflicts_df['analyst_won'].notna().sum()

        if total_resolved > 0:
            print(f"Analyst wins: {analyst_wins}/{total_resolved} ({analyst_wins/total_resolved*100:.1f}%)")
            print(f"Sentiment wins: {total_resolved - analyst_wins}/{total_resolved} ({(total_resolved-analyst_wins)/total_resolved*100:.1f}%)")
    else:
        print("No conflicts found in data")


def apply_weights_to_orchestrator(weights_path: str, orchestrator):
    """Apply calculated weights to running orchestrator."""
    weights_df = pd.read_csv(weights_path)

    for _, row in weights_df.iterrows():
        agent = row['agent_name']
        symbol = row['symbol']
        new_weight = row['new_weight']

        orchestrator.symbol_weights[symbol][agent] = new_weight

    print(f"Applied {len(weights_df)} adaptive weights to orchestrator")


if __name__ == "__main__":
    import sys

    # Default paths
    signals_file = "v12_all_agents_signals.csv"
    exits_file = "backend/data/backtest_results/trade_exits.csv"

    if len(sys.argv) > 1:
        signals_file = sys.argv[1]
    if len(sys.argv) > 2:
        exits_file = sys.argv[2]

    analyze_v12_performance(signals_file, exits_file)
