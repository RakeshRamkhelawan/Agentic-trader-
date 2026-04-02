import json
import logging
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class CognitiveLogger:
    """Logs the cognitive decision making process for total transparency.

    Features:
    - In-memory ring buffer (50 most recent decisions) for instant API access
    - Async file persistence to JSONL for long-term audit trail
    - Correct metadata extraction from ChromaDB RAG results
    """

    def __init__(self, log_dir: str = "backend/data/audit_logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / f"cognitive_audit_{datetime.now().strftime('%Y%m')}.jsonl"
        # In-memory ring buffer for fast endpoint access (no file I/O needed)
        self._recent_decisions: deque = deque(maxlen=50)

    def get_recent_decisions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Return the most recent cognitive decisions from the in-memory buffer."""
        items = list(self._recent_decisions)
        items.reverse()  # Most recent first
        return items[:limit]

    async def log_decision(
        self,
        symbol: str,
        regime: str,
        engine_signal: str,
        rag_insights: List[Dict[str, Any]],
        vedastro_vote: float,
        rag_adjustment: float,
        final_decision: str,
    ) -> None:
        """Append a cognitive decision snapshot."""
        try:
            record = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "symbol": symbol,
                "regime": regime,
                "engine_signal": engine_signal,
                "vedastro_vote": vedastro_vote,
                "rag_adjustment": rag_adjustment,
                "final_decision": final_decision,
                "rag_evidence": [
                    {
                        # ChromaDB metadatas are stored flat in the metadata dict
                        "source": d.get("metadata", {}).get("source", "unknown"),
                        "symbol": d.get("metadata", {}).get("symbol", "unknown"),
                        "period": d.get("metadata", {}).get("period", "unknown"),
                        "regime": d.get("metadata", {}).get("regime", "unknown"),
                        "outcome": d.get("metadata", {}).get("outcome", "unknown"),
                        "return_pct": d.get("metadata", {}).get("return_pct", 0.0),
                        "mahadasha": d.get("metadata", {}).get("mahadasha", "Unknown"),
                        "antardasha": d.get("metadata", {}).get("antardasha", "Unknown"),
                        "distance": d.get("distance", 0.0),
                    }
                    for d in rag_insights
                ],
            }

            # 1. Store in ring buffer (instant access for API/WebSocket)
            self._recent_decisions.append(record)

            # 2. Persist to file (async, non-blocking)
            from anyio import Path as AsyncPath

            async_file = AsyncPath(self.log_file)
            async with await async_file.open("a", encoding="utf-8") as f:
                await f.write(json.dumps(record) + "\n")
        except Exception as e:
            logger.error(f"Failed to write cognitive audit log: {e}")
