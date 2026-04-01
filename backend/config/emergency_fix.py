"""
Emergency Fix for V12 Backtest - Addressing 100% BUY Bias

Problem: Agents stuck in BUY mode with 0% confidence/harmony
Solution: Reset weights, lower thresholds, force action diversity
"""

# Emergency Weights - Reset to balanced
FIXED_WEIGHTS = {
    "Water_Trend": 1.0,  # Reduced from 1.5 (was causing BUY overdrive)
    "Air_Regime": 1.2,  # Boosted (needs to detect regime changes)
    "Earth_Execution": 1.0,  # Restored to neutral
    "Fire_Momentum": 0.8,  # Calmed (prevent FOMO)
    "ElementalConsensus": 1.5,  # Reduced but still primary
}

# Emergency Thresholds - Lowered to allow decisions
EMERGENCY_THRESHOLDS = {
    "confidence": 0.50,  # Lowered from 0.75
    "harmony": 0.15,  # Accept low harmony initially
    "vedastro": 40,  # Back to baseline
    "prana_min": 0.3,  # Minimum prana level
}

# Force Action Diversity
ACTION_BALANCE_CONFIG = {
    "target_buy_pct": 0.33,  # 33% BUY
    "target_sell_pct": 0.33,  # 33% SELL
    "target_hold_pct": 0.34,  # 34% HOLD
    "max_bias_pct": 0.60,  # Force counter-signal if bias > 60%
    "counter_signal_strength": 0.4,
}

# Prompt Fix - Force diversity
PROMPT_ADDENDUM = """

EMERGENCY BALANCE PROTOCOL:
You MUST maintain 33% BUY / 33% SELL / 34% HOLD ratio across all decisions.
If your recent actions show >60% bias toward any single action,
you MUST counter-balance with opposite signal (confidence 0.4).

Current bias check: {buy_pct}% BUY, {sell_pct}% SELL, {hold_pct}% HOLD
Bias status: {bias_status}
Forced adjustment: {forced_action}
"""


def apply_emergency_fix(meta_orchestrator):
    """Apply emergency fix to running orchestrator."""
    print("[EMERGENCY] Applying fix to MetaOrchestrator...")

    # Reset weights
    meta_orchestrator.agent_weights = FIXED_WEIGHTS.copy()
    print(f"[EMERGENCY] Weights reset: {FIXED_WEIGHTS}")

    # Reset thresholds
    meta_orchestrator.config = {
        **getattr(meta_orchestrator, "config", {}),
        **EMERGENCY_THRESHOLDS,
    }
    print(f"[EMERGENCY] Thresholds lowered: {EMERGENCY_THRESHOLDS}")

    # Reset agent Chitta biases
    for agent in meta_orchestrator.agents:
        if hasattr(agent, "action_history"):
            agent.action_history.clear()
        # Reset prana to full
        if hasattr(agent, "prana_level"):
            agent.prana_level = 100

    print("[EMERGENCY] Agent memories cleared, prana restored")
    return True


def calculate_bias(actions: list) -> dict:
    """Calculate action bias percentage."""
    if not actions:
        return {"buy": 0.33, "sell": 0.33, "hold": 0.34, "bias_detected": False}

    total = len(actions)
    buy_pct = sum(1 for a in actions if a == "BUY") / total
    sell_pct = sum(1 for a in actions if a == "SELL") / total
    hold_pct = sum(1 for a in actions if a == "HOLD") / total

    max_bias = max(buy_pct, sell_pct, hold_pct)
    bias_detected = max_bias > ACTION_BALANCE_CONFIG["max_bias_pct"]

    # Determine forced counter-action
    forced_action = None
    if bias_detected:
        if buy_pct > ACTION_BALANCE_CONFIG["max_bias_pct"]:
            forced_action = "SELL"
        elif sell_pct > ACTION_BALANCE_CONFIG["max_bias_pct"]:
            forced_action = "BUY"
        else:
            forced_action = "HOLD"

    return {
        "buy": buy_pct,
        "sell": sell_pct,
        "hold": hold_pct,
        "max_bias": max_bias,
        "bias_detected": bias_detected,
        "forced_action": forced_action,
    }


def get_forced_action_if_needed(agent_name: str, action_history: list) -> tuple:
    """
    Check if agent needs forced action to maintain balance.

    Returns:
        (should_force, action, confidence) tuple
    """
    bias = calculate_bias(action_history)

    if bias["bias_detected"]:
        forced = bias["forced_action"]
        conf = ACTION_BALANCE_CONFIG["counter_signal_strength"]
        print(
            f"[BIAS-CORRECTION] {agent_name}: Forcing {forced} (was {bias['max_bias']:.0%} biased)"
        )
        return True, forced, conf

    return False, None, 0.0
