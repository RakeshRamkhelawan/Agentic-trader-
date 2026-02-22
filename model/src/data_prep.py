import glob
import json
import os
from typing import Dict


def format_log_to_instruction(entry: Dict) -> Dict:
    """Format a single structured backtest entry into an instruction-tuning pair."""
    # Handle nested logic from STRUCTURED.json format found in backtest_logs
    agent_decisions = entry.get("agent_decisions", [])
    if not agent_decisions:
        return None

    # We take the decision for training
    decision = agent_decisions[0]
    symbol = decision.get("symbol", "Unknown")
    indicators = decision.get("technical_indicators", {})
    sentiment = decision.get("sentiment_score", 0)
    vedic = decision.get("vedic_harmony", 0)

    instruction = (
        f"Analyze the market for {symbol}. "
        f"Technical Indicators: {indicators}. "
        f"Sentiment Score: {sentiment}. "
        f"Vedic Harmony: {vedic}."
    )

    thought = (
        f"Confidence: {decision.get('confidence')}. "
        f"Primary Motivation: {decision.get('primary_motivation')}. "
        f"Market Analysis: {decision.get('market_analysis')}."
    )

    action = f"ACTION: {decision.get('decision')}"

    return {
        "instruction": instruction,
        "input": "",
        "output": f"THOUGHT: {thought}\n{action}",
    }


def prepare_dataset(input_dir: str, output_file: str, max_samples: int = 1000):
    """Scan backtest logs and generate training jsonl."""
    samples = []
    log_files = glob.glob(os.path.join(input_dir, "*STRUCTURED.json"))

    print(f"Found {len(log_files)} log files.")

    for log_path in log_files:
        try:
            with open(log_path, "r") as f:
                data = json.load(f)
                # Check if it's a list or dict
                if isinstance(data, list):
                    batch = data
                else:
                    batch = [data]

                for entry in batch:
                    formatted = format_log_to_instruction(entry)
                    if formatted:
                        samples.append(formatted)
                    if len(samples) >= max_samples:
                        break
        except Exception as e:
            print(f"Error processing {log_path}: {e}")

        if len(samples) >= max_samples:
            break

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(samples, f, indent=2)

    print(f"Dataset saved to {output_file} with {len(samples)} samples.")


if __name__ == "__main__":
    prepare_dataset(
        input_dir="./backtest_logs",
        output_file="./data/processed/agent_train_data.json",
    )
