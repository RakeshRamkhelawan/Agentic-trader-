import asyncio
import logging
import uuid
from collections import deque
from datetime import datetime, timezone
from typing import Optional

import tiktoken

logger = logging.getLogger(__name__)


class TokenCounter:
    def __init__(self):
        self.encoders = {}
        try:
            self.encoders["gpt-4"] = tiktoken.encoding_for_model("gpt-4")
            self.encoders["gpt-3.5-turbo"] = tiktoken.encoding_for_model(
                "gpt-3.5-turbo"
            )
            self.encoders["default"] = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            logger.warning(f"Failed to initialize tiktoken encoders: {e}")

    def count_tokens(self, text: str, model: str) -> int:
        if not text:
            return 0

        encoder = self.encoders.get(model)
        if not encoder:
            # Fallback to default encoding or approximation
            encoder = self.encoders.get("default")

        if not encoder:
            # Ultimate fallback: estimate 1 token = 4 characters
            return len(text) // 4

        try:
            return len(encoder.encode(text))
        except Exception:
            return len(text) // 4

    def calculate_cost(
        self, prompt_tokens: int, completion_tokens: int, model: str
    ) -> float:
        # Pricing as of Feb 2026 (update periodically)
        # Using approximated standard pricing for major models
        pricing = {
            "gpt-4": {"prompt": 0.03 / 1000, "completion": 0.06 / 1000},
            "gpt-4-turbo": {"prompt": 0.01 / 1000, "completion": 0.03 / 1000},
            "gpt-3.5-turbo": {"prompt": 0.0005 / 1000, "completion": 0.0015 / 1000},
            "gemini-1.5-pro": {
                "prompt": 0.00125 / 1000,
                "completion": 0.005 / 1000,
            },  # Approximate
            "gemini-1.0-pro": {"prompt": 0.0005 / 1000, "completion": 0.0015 / 1000},
        }

        # Normalize model name for pricing lookup
        pricing_model = model
        if "gpt-4" in model and "turbo" not in model:
            pricing_model = "gpt-4"
        elif "gpt-4" in model and "turbo" in model:
            pricing_model = "gpt-4-turbo"
        elif "gpt-3.5" in model:
            pricing_model = "gpt-3.5-turbo"
        elif "gemini-1.5" in model:
            pricing_model = "gemini-1.5-pro"
        elif "gemini" in model:
            pricing_model = "gemini-1.0-pro"

        if pricing_model not in pricing:
            return 0.0  # Assumed free or unknown

        rates = pricing[pricing_model]
        return (prompt_tokens * rates["prompt"]) + (
            completion_tokens * rates["completion"]
        )


class UsageTracker:
    def __init__(
        self, clickhouse_client=None, batch_size: int = 10, flush_interval: int = 5
    ):
        self.clickhouse = clickhouse_client
        self.buffer = deque(maxlen=10000)
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self._flush_task = None
        self._running = False
        self.token_counter = TokenCounter()

    async def start(self):
        if self._running:
            return
        self._running = True
        self._flush_task = asyncio.create_task(self._periodic_flush())
        logger.info("UsageTracker started")

    async def stop(self):
        self._running = False
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        # Final flush
        await self._flush()
        logger.info("UsageTracker stopped")

    async def log_usage(
        self,
        tenant_id: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost_usd: float,
        agent_name: str = "unknown",
        request_id: Optional[str] = None,
    ):
        if not request_id:
            request_id = str(uuid.uuid4())

        entry = {
            "tenant_id": tenant_id,
            "timestamp": datetime.now(timezone.utc),
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "cost_usd": cost_usd,
            "agent_name": agent_name,
            "request_id": request_id,
        }

        self.buffer.append(entry)

        if len(self.buffer) >= self.batch_size:
            await self._flush()

    async def _periodic_flush(self):
        while self._running:
            await asyncio.sleep(self.flush_interval)
            await self._flush()

    async def _flush(self):
        if not self.buffer or not self.clickhouse:
            return

        batch = []
        while (
            self.buffer and len(batch) < self.batch_size * 2
        ):  # Flush up to 2x batch size
            batch.append(self.buffer.popleft())

        if not batch:
            return

        try:
            # Prepare data for ClickHouse
            # Assuming clickhouse_client has an insert method
            # If implementation differs, this needs adaptation
            await self.clickhouse.insert("llm_usage_logs", batch)
            logger.debug(f"Flushed {len(batch)} usage logs to ClickHouse")
        except Exception as e:
            logger.error(f"Failed to flush usage logs: {e}")
            # Re-queue failed items (optional, careful with infinite loops)
            # For now, we drop to avoid blocking/memory leak, but log error

    async def get_daily_usage(self, tenant_id: str) -> float:
        """
        Fetch total usage cost for a tenant for the current day (UTC).
        """
        if not self.clickhouse:
            logger.warning("ClickHouse client not initialized, returning 0.0 usage")
            return 0.0

        try:
            # Query ClickHouse for today's usage
            # toYYYYMMDD(timestamp) = toYYYYMMDD(now('UTC'))
            query = f"""
                SELECT sum(cost_usd) as total_cost
                FROM llm_usage_logs
                WHERE tenant_id = '{tenant_id}'
                  AND toYYYYMMDD(timestamp) = toYYYYMMDD(now('UTC'))
            """
            # Use execute directly or query method if available
            # self.clickhouse is TenantAwareClickHouseClient which has execute/query
            # We need to query.
            result = await self.clickhouse.execute(query)

            # Result formatting depends on clickhouse-connect (usually list of tuples)
            # result.result_rows might be the way, or just result if it returns rows
            # checking clickhouse_client.py: execute returns await self.client.query(query)
            # clickhouse_connect async client query returns a QueryResult

            if result and result.result_rows:
                return float(result.result_rows[0][0])
            return 0.0
        except Exception as e:
            logger.error(f"Failed to fetch daily usage: {e}")
            return 0.0
