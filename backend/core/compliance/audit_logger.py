import asyncio
import uuid
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from collections import deque

logger = logging.getLogger(__name__)

class AuditLogger:
    def __init__(self, clickhouse_client=None, batch_size: int = 50, flush_interval: int = 5):
        self.clickhouse = clickhouse_client
        self.buffer = deque(maxlen=5000)
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self._flush_task = None
        self._running = False

    async def start(self):
        if self._running:
            return
        self._running = True
        self._flush_task = asyncio.create_task(self._periodic_flush())
        logger.info("AuditLogger started")

    async def stop(self):
        self._running = False
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        await self._flush()
        logger.info("AuditLogger stopped")

    async def log_event(self,
                        tenant_id: str,
                        action: str,
                        resource_type: str,
                        resource_id: str,
                        actor_id: str = "system",
                        details: Optional[Dict[str, Any]] = None,
                        status: str = "SUCCESS",
                        ip_address: str = "",
                        user_agent: str = ""):
        
        entry = {
            'tenant_id': tenant_id,
            'audit_id': str(uuid.uuid4()),
            'timestamp': datetime.now(timezone.utc),
            'actor_id': actor_id,
            'action': action,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'details': json.dumps(details, default=str) if details else "{}",
            'status': status,
            'ip_address': ip_address,
            'user_agent': user_agent
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
        while self.buffer and len(batch) < self.batch_size * 2:
            batch.append(self.buffer.popleft())

        if not batch:
            return

        try:
            await self.clickhouse.insert('audit_trail', batch)
            logger.debug(f"Flushed {len(batch)} audit logs to ClickHouse")
        except Exception as e:
            logger.error(f"Failed to flush audit logs: {e}")
            # Re-queue strategy or fallback logging could go here
