"""
VedAstro Cloud Connector - Official API Integration.

Provides access to the official VedAstro Cloud API (api.vedastro.org)
for advanced features like Vimshottari Dasha and pre-calculated signals.
"""

import logging
from datetime import datetime
from typing import Any, Optional

import httpx

from backend.core.config.settings import settings

logger = logging.getLogger(__name__)


class VedAstroCloudConnector:
    """
    Connector for the official VedAstro Cloud API.

    Uses the x-api-key header for authenticated requests.
    """

    BASE_URL = "https://api.vedastro.org"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the cloud connector.

        Args:
            api_key: Official VedAstro API key (defaults to settings)
        """
        self.api_key = api_key or settings.VEDASTRO_API_KEY
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={"x-api-key": self.api_key} if self.api_key else {},
            timeout=10.0,
        )

        if self.api_key:
            logger.info("VedAstro Cloud Connector initialized with API key")
        else:
            logger.warning("VedAstro Cloud Connector initialized WITHOUT API key (limited access)")

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def get_dasha(self, birth_date: datetime, location: dict[str, float]) -> dict[str, Any]:
        """
        Get Vimshottari Dasha from VedAstro Cloud.

        Args:
            birth_date: ISO format datetime
            location: dict with 'lat' and 'lon'

        Returns:
            Dasha information or error dict
        """
        if not self.api_key:
            return {"error": "API key required for Cloud Dasha"}

        try:
            # Example path based on VedAstro API docs: /Calculate/VimshottariDasha/Location/12.3,45.6/Time/00:00/01/01/2000/+00:00
            # Note: VedAstro API uses a specific URL structure for GET requests.
            # We will use the structured path format.

            lat = location.get("lat", settings.LATITUDE)
            lon = location.get("lon", settings.LONGITUDE)

            # Format: DD/MM/YYYY
            date_str = birth_date.strftime("%d/%m/%Y")
            time_str = birth_date.strftime("%H:%M")
            tz_str = birth_date.strftime("%z") or "+00:00"

            path = f"/Calculate/VimshottariDasha/Location/{lat},{lon}/Time/{time_str}/{date_str}/{tz_str}"

            response = await self.client.get(path)
            response.raise_for_status()

            return response.json().get("Payload", {})

        except Exception as e:
            logger.error(f"Cloud Dasha calculation failed: {e}")
            return {"error": str(e)}

    async def get_trading_signal(self, symbol: str) -> dict[str, Any]:
        """
        Get official trading signal from VedAstro Cloud if available.
        """
        # Placeholder for future official signal endpoints
        return {"note": "Use local signal generator combined with Cloud Dasha for best results"}
