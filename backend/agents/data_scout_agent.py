"""
DataScout Agent - Observe Phase van OODA Loop.

Verzamelt en normaliseert marktdata tot gestandaardiseerde Observation objects.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, UTC

from backend.agents.base_agent import BaseAgent
from backend.core.schemas.ooda_types import Observation
from backend.governance.agent_gatekeeper import AgentRole

logger = logging.getLogger(__name__)


class DataScoutAgent(BaseAgent):
    """
    DataScout Agent - Observatie specialist.
    
    Rol in OODA: **OBSERVE**
    - Verzamelt live marktdata (ticks, orderbook, funding)
    - Normaliseert data naar Observation schema
    - Voegt audit logging toe met trace_id
    
    Data bronnen (read-only):
    - Market ticks (price, volume)
    - Orderbook snapshots
    - Funding rates (voor perpetuals)
    - Social sentiment (optioneel)
    """
    
    def __init__(
        self,
        llm_provider: Optional[Any] = None,
        event_bus: Optional[Any] = None,
        data_source: Optional[Any] = None,
    ):
        """
        Initialiseer DataScout.
        
        Args:
            llm_provider: LLM provider (optioneel, gebruikt voor anomalie detectie)
            event_bus: Event bus voor audit logging
            data_source: Data source adapter (bijv. exchange client)
        """
        super().__init__(
            agent_name="DataScout",
            llm_provider=llm_provider,
            event_bus=event_bus,
            agent_role=AgentRole.OBSERVER
        )
        self.data_source = data_source
        
        # Statistics
        self.observations_collected = 0
        self.anomalies_detected = 0
    
    async def observe(
        self,
        symbol: str,
        trace_id: str,
        include_orderbook: bool = True,
        include_funding: bool = True
    ) -> Observation:
        """
        Verzamel marktdata en retourneer gestandaardiseerde Observation.
        
        Args:
            symbol: Trading pair (bijv. 'BTC/USDT')
            trace_id: Audit trace ID voor end-to-end tracking
            include_orderbook: Fetch orderbook snapshot
            include_funding: Fetch funding rate (voor perpetuals)
        
        Returns:
            Observation object met genormaliseerde marktdata
        
        Raises:
            ValueError: Als data source niet beschikbaar is
        """
        self.heartbeat()
        
        try:
            # Fetch ticker data
            ticker = await self._fetch_ticker(symbol)
            
            # Build observation
            obs_data = {
                "symbol": symbol,
                "price": ticker['last'],
                "volume": ticker['volume'],
                "orderbook": {},
                "funding_rate": None,
                "social_sentiment": 0.0,
                "raw_ticker": ticker
            }
            
            # Optional: Fetch orderbook
            if include_orderbook:
                obs_data['orderbook'] = await self._fetch_orderbook(symbol)
            
            # Optional: Fetch funding rate
            if include_funding:
                obs_data['funding_rate'] = await self._fetch_funding_rate(symbol)
            
            # Create Observation (with validation)
            observation = Observation(**obs_data)
            
            # Audit logging
            await self._log_observation(trace_id, observation)
            
            # Statistics
            self.observations_collected += 1
            self.record_activity(success=True)
            
            logger.info(
                f"Observation collected: {symbol} @ {observation.price} "
                f"(trace_id={trace_id})"
            )
            
            return observation
            
        except Exception as e:
            logger.error(f"Failed to collect observation for {symbol}: {e}")
            self.record_activity(success=False)
            raise
    
    async def _fetch_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch ticker data van data source.
        
        Returns:
            Dict met keys: last, volume, bid, ask, timestamp
        """
        if self.data_source is None:
            # Mock data voor development
            logger.warning("No data source configured, using mock data")
            return {
                'last': 50000.0,
                'volume': 100.0,
                'bid': 49999.0,
                'ask': 50001.0,
                'timestamp': datetime.now(UTC).timestamp()
            }
        
        try:
            # Call data source adapter
            ticker = await self.data_source.fetch_ticker(symbol)
            return ticker
        except Exception as e:
            logger.error(f"Data source error for {symbol}: {e}")
            raise ValueError(f"Failed to fetch ticker: {e}")
    
    async def _fetch_orderbook(self, symbol: str, depth: int = 10) -> Dict[str, Any]:
        """
        Fetch orderbook snapshot.
        
        Args:
            symbol: Trading pair
            depth: Number of levels per side
        
        Returns:
            Dict met 'bids' en 'asks' arrays
        """
        if self.data_source is None:
            return {
                'bids': [[49999.0, 1.0], [49998.0, 0.5]],
                'asks': [[50001.0, 1.0], [50002.0, 0.5]]
            }
        
        try:
            orderbook = await self.data_source.fetch_orderbook(symbol, limit=depth)
            return {
                'bids': orderbook.get('bids', []),
                'asks': orderbook.get('asks', [])
            }
        except Exception as e:
            logger.warning(f"Failed to fetch orderbook for {symbol}: {e}")
            return {'bids': [], 'asks': []}
    
    async def _fetch_funding_rate(self, symbol: str) -> Optional[float]:
        """
        Fetch funding rate voor perpetual contracts.
        
        Returns:
            Funding rate of None als niet beschikbaar
        """
        if self.data_source is None:
            return 0.0001  # Mock value
        
        try:
            funding = await self.data_source.fetch_funding_rate(symbol)
            return funding
        except Exception as e:
            logger.debug(f"Funding rate not available for {symbol}: {e}")
            return None
    
    async def _log_observation(self, trace_id: str, observation: Observation):
        """
        Log observation naar audit systeem.
        
        Args:
            trace_id: Audit trace ID
            observation: Observation object
        """
        audit_data = {
            "trace_id": trace_id,
            "stage": "OBSERVE",
            "component": "DataScoutAgent",
            "symbol": observation.symbol,
            "price": observation.price,
            "volume": observation.volume,
            "timestamp": observation.timestamp
        }
        
        # Publish via EventBus als beschikbaar
        if self.event_bus:
            try:
                await self.event_bus.publish("audit_log", audit_data)
            except Exception as e:
                logger.warning(f"Failed to publish audit log: {e}")
        
        # Altijd local logging
        logger.debug(f"Audit log: {audit_data}")
    
    async def analyze(self, features: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        BaseAgent abstract method implementation.
        
        Voor DataScout is 'analyze' niet van toepassing - gebruik observe() direct.
        """
        logger.warning("analyze() called on DataScout - use observe() instead")
        return {
            "recommendation": "Use observe() method for DataScoutAgent",
            "confidence": 0.0
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Krijg DataScout statistieken.
        
        Returns:
            Dict met performance metrics
        """
        health = self.health_check()
        return {
            **health,
            "observations_collected": self.observations_collected,
            "anomalies_detected": self.anomalies_detected
        }
