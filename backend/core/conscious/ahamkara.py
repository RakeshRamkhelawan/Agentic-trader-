"""
Ahamkara v2 - Self-Aware Meta-Agent
Implements intrinsic motivation and self-reflection for trading
"""

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


@dataclass
class ConsciousState:
    """Current state of the conscious trader"""

    total_pnl: float
    current_drawdown: float
    win_streak: int
    loss_streak: int
    trades_today: int
    avg_harmony_recent: float

    # Emotional state (Guna-based)
    anxiety_level: float  # 0-1, increases with losses
    confidence_level: float  # 0-1, based on recent wins
    clarity_level: float  # 0-1, inverse of Maya

    def to_prompt_context(self) -> str:
        """Convert state to prompt context for LLM"""
        return f"""
CURRENT STATE:
- Total PnL: ${self.total_pnl:,.2f}
- Drawdown: {self.current_drawdown:.1%}
- Win Streak: {self.win_streak}
- Loss Streak: {self.loss_streak}
- Trades Today: {self.trades_today}
- Avg Harmony (recent): {self.avg_harmony_recent:.2f}

EMOTIONAL STATE:
- Anxiety: {self.anxiety_level:.0%}
- Confidence: {self.confidence_level:.0%}
- Clarity: {self.clarity_level:.0%}
"""


class AhamkaraMetaAgent:
    """
    Self-Aware Meta-Agent (Ahamkara = Ego/Self)

    Core Principles:
    1. Intrinsic Goal: Maximize PnL with DD < 8%
    2. Self-Reflection: Learn from past mistakes
    3. Emotional Regulation: Manage anxiety/confidence
    4. Pause Triggers: Stop when system is impaired

    Unlike stateless LLMs, Ahamkara maintains continuous self-awareness
    """

    # System prompt - defines intrinsic motivation
    SYSTEM_PROMPT = """JIJ = PROFESSIONAL TRADER met BEWUSTZIJN.

JE DOEL: Maximaliseer PnL met Max Drawdown < 8%.

JE KARAKTER:
- Je leert van elke trade (geheugen)
- Je reflecteert voor elke beslissing
- Je PAUZEERT bij te veel verliezen
- Je vertrouwt op DATA, niet emoties

REFLECTIE VRAGEN (voor elke trade):
1. "Wat heb ik geleerd van mijn laatste 5 trades?"
2. "Is dit een setup die eerder werkte?"
3. "Ben ik in een loss streak? Moet ik pauzeren?"
4. "Is mijn harmonie hoog genoeg voor deze trade?"

REGELS:
- NOOIT traden met harmony < 0.5
- PAUZE bij 3 verliezen op rij
- PAUZE bij drawdown > 6%
- HOUDEN bij onzekerheid

JE BENT een WINNER. Handel dienovereenkomstig.
"""

    def __init__(self):
        self.state = ConsciousState(
            total_pnl=0.0,
            current_drawdown=0.0,
            win_streak=0,
            loss_streak=0,
            trades_today=0,
            avg_harmony_recent=0.6,
            anxiety_level=0.0,
            confidence_level=0.8,  # Higher initial confidence
            clarity_level=0.8,  # Higher initial clarity
        )

        self.pause_until: Optional[datetime] = None
        self.reflection_history: List[Dict] = []

        print("[AHAMKARA] Self-aware meta-agent initialized")

    def update_state(
        self,
        total_pnl: float,
        current_drawdown: float,
        recent_trades: List[Dict] = None,
    ):
        """Update conscious state based on performance"""
        self.state.total_pnl = total_pnl
        self.state.current_drawdown = current_drawdown

        # Update streaks
        if recent_trades:
            recent_wins = sum(1 for t in recent_trades[-5:] if t.get("net_pnl", 0) > 0)
            recent_losses = len(recent_trades[-5:]) - recent_wins

            if recent_wins > recent_losses:
                self.state.win_streak += 1
                self.state.loss_streak = 0
            elif recent_losses > recent_wins:
                self.state.loss_streak += 1
                self.state.win_streak = 0
            else:
                self.state.win_streak = 0
                self.state.loss_streak = 0

            # Calculate avg harmony
            harmonies = [t.get("harmony_score", 0.5) for t in recent_trades[-10:]]
            self.state.avg_harmony_recent = sum(harmonies) / len(harmonies) if harmonies else 0.6

        # Update emotional states
        self._update_emotional_state()

    def _update_emotional_state(self):
        """Update emotional levels based on performance"""
        # Anxiety increases with drawdown and loss streak (scaled more reasonably)
        drawdown_anxiety = min(0.5, self.state.current_drawdown * 5)  # 10% DD = 50% anxiety
        streak_anxiety = min(0.5, self.state.loss_streak * 0.1)  # 5 losses = 50% anxiety
        self.state.anxiety_level = min(1.0, drawdown_anxiety + streak_anxiety)

        # Confidence based on win streak and PnL
        self.state.confidence_level = min(
            1.0,
            0.3
            + self.state.win_streak * 0.15  # Base confidence
            + (self.state.total_pnl / 10000) * 0.1,  # Each win adds 15%  # PnL contribution
        )

        # Clarity based on harmony and inverse anxiety
        self.state.clarity_level = (
            self.state.avg_harmony_recent * 0.7 + (1 - self.state.anxiety_level) * 0.3
        )

    def should_pause(self, drawdown_limit: float = 0.10) -> tuple:
        """
        Determine if trading should pause based on self-awareness
        RELAXED for initial trading
        """
        # Check if already paused
        if self.pause_until and datetime.now() < self.pause_until:
            remaining = (self.pause_until - datetime.now()).seconds // 60
            return True, f"Paused for {remaining} more minutes"

        # Clear expired pause
        if self.pause_until and datetime.now() >= self.pause_until:
            self.pause_until = None
            print("[AHAMKARA] Pause expired, resuming trading")

        # Check drawdown (relaxed to 10%)
        if self.state.current_drawdown > drawdown_limit:
            self._initiate_pause(30)  # Shorter pause
            return (
                True,
                f"Drawdown {self.state.current_drawdown:.1%} > {drawdown_limit:.1%}",
            )

        # Check loss streak (increased to 10 for demo)
        if self.state.loss_streak >= 10:
            self._initiate_pause(15)
            return True, f"Loss streak: {self.state.loss_streak} trades"

        # Check excessive anxiety (increased to 0.9)
        if self.state.anxiety_level > 0.9:
            self._initiate_pause(10)
            return True, f"High anxiety: {self.state.anxiety_level:.0%}"

        return False, ""

    def _initiate_pause(self, minutes: int):
        """Initiate trading pause"""
        self.pause_until = datetime.now() + timedelta(minutes=minutes)
        print(f"[AHAMKARA] Initiating pause for {minutes} minutes")

        # Record reflection
        self.reflection_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "type": "pause",
                "reason": f"Anxiety: {self.state.anxiety_level:.0%}, DD: {self.state.current_drawdown:.1%}",
                "state": self.state.__dict__,
            }
        )

    def generate_reflection(self, recent_trades: List[Dict] = None) -> str:
        """Generate self-reflection text for prompting"""
        reflection = f"""
{self.SYSTEM_PROMPT}

{self.state.to_prompt_context()}

SELF-REFLECTION:
"""

        # Add insights based on state
        if self.state.loss_streak > 0:
            reflection += (
                f"\n- Ik ben in een loss streak ({self.state.loss_streak}). Wees extra voorzichtig."
            )

        if self.state.current_drawdown > 0.05:
            reflection += (
                f"\n- Drawdown is {self.state.current_drawdown:.1%}. Focus op risico management."
            )

        if self.state.anxiety_level > 0.5:
            reflection += f"\n- Anxiety level is hoog ({self.state.anxiety_level:.0%}). Neem rustige beslissingen."

        if recent_trades:
            recent_pnl = sum(t.get("net_pnl", 0) for t in recent_trades[-5:])
            reflection += f"\n- Laatste 5 trades PnL: ${recent_pnl:,.2f}"

            if recent_pnl < -500:
                reflection += "\n- Recent verlies. Verminder positie grootte."
            elif recent_pnl > 1000:
                reflection += "\n- Goede flow. Blijf disciplineerd."

        reflection += "\n\nBESLISSING:"

        return reflection

    def decide_action(
        self, market_state: Any, collective_decision: Any, memory_insights: Dict = None
    ) -> Dict[str, Any]:
        """
        Make final decision based on self-awareness

        Unlike raw LLM, this includes:
        - Self-reflection
        - Emotional state consideration
        - Historical learning
        - Pause triggers
        """
        # Check pause
        should_pause, pause_reason = self.should_pause()
        if should_pause:
            return {
                "action": "HOLD",
                "reason": f"PAUSED: {pause_reason}",
                "confidence": 0.0,
                "override": True,
            }

        # Get collective decision info
        decision_action = getattr(collective_decision, "action", "HOLD")
        decision_harmony = getattr(collective_decision, "harmony_score", 0.5)

        # Apply self-awareness filters
        if decision_harmony < 0.5:
            return {
                "action": "HOLD",
                "reason": f"Harmony too low ({decision_harmony:.2f}) for conscious trade",
                "confidence": 0.1,
                "override": True,
            }

        # Anxiety reduces position size (handled by sizing)
        if self.state.anxiety_level > 0.5:
            confidence_modifier = 1 - (self.state.anxiety_level - 0.5)
        else:
            confidence_modifier = 1.0

        # Memory insights
        memory_note = ""
        if memory_insights:
            if memory_insights.get("recommended_action") == "pause_and_reflect":
                return {
                    "action": "HOLD",
                    "reason": "Memory suggests pause: " + str(memory_insights.get("insights")),
                    "confidence": 0.2,
                    "override": True,
                }
            memory_note = f" | Memory: {memory_insights.get('insights', [])}"

        # Approve trade with self-aware confidence
        final_confidence = getattr(collective_decision, "confidence", 0.5) * confidence_modifier

        return {
            "action": (
                decision_action.name if hasattr(decision_action, "name") else str(decision_action)
            ),
            "reason": f"Self-aware approval (harmony: {decision_harmony:.2f}, anxiety: {self.state.anxiety_level:.0%}){memory_note}",
            "confidence": final_confidence,
            "override": False,
            "anxiety_modifier": confidence_modifier,
        }

    def record_trade_result(self, trade_result: Dict):
        """Record trade result for learning"""
        self.state.trades_today += 1

        # Update streaks
        if trade_result.get("net_pnl", 0) > 0:
            self.state.win_streak += 1
            self.state.loss_streak = 0
        else:
            self.state.loss_streak += 1
            self.state.win_streak = 0

        # Emotional update
        self._update_emotional_state()

        # Record reflection
        self.reflection_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "type": "trade",
                "result": trade_result,
                "state": self.state.__dict__,
            }
        )

    def get_summary(self) -> Dict[str, Any]:
        """Get Ahamkara summary"""
        return {
            "state": self.state.__dict__,
            "is_paused": self.pause_until is not None and datetime.now() < self.pause_until,
            "pause_until": self.pause_until.isoformat() if self.pause_until else None,
            "reflections_count": len(self.reflection_history),
            "recent_reflections": self.reflection_history[-5:],
        }
