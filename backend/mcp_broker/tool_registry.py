"""
Tool Registry - Semantic search and discovery for MCP tools.

Provides natural language tool discovery and intelligent tool recommendations.
"""

import logging
from typing import Any

# Try to import ChromaDB for embeddings
# If not available, use simple keyword matching fallback
try:
    import chromadb
    from chromadb.utils import embedding_functions

    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logging.warning("ChromaDB not available. Using fallback keyword matching.")

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Registry for MCP tools with semantic search capabilities.

    Features:
    - Natural language tool discovery
    - Tool description embeddings
    - Category-based organization
    - Tool recommendation based on context
    """

    def __init__(self, use_embeddings: bool = True):
        """
        Initialize tool registry.

        Args:
            use_embeddings: Whether to use vector embeddings (requires ChromaDB)
        """
        self.tools: dict[str, dict[str, Any]] = {}
        self.categories: dict[str, list[str]] = {}
        self.use_embeddings = use_embeddings and CHROMADB_AVAILABLE
        self.chroma_client = None
        self.collection = None

        if self.use_embeddings:
            try:
                self.chroma_client = chromadb.Client()
                self.collection = self.chroma_client.create_collection(
                    name="mcp_tools",
                    embedding_function=embedding_functions.DefaultEmbeddingFunction(),
                )
                logger.info("ToolRegistry initialized with ChromaDB embeddings")
            except Exception as e:
                logger.warning(f"Failed to initialize ChromaDB: {e}. Using fallback.")
                self.use_embeddings = False
        else:
            logger.info("ToolRegistry initialized with keyword fallback")

    def register_tool(
        self,
        name: str,
        description: str,
        category: str,
        parameters: dict[str, Any] | None = None,
        examples: list[dict] | None = None,
    ) -> None:
        """
        Register a tool in the registry.

        Args:
            name: Tool name (e.g., "vedastro__generate_signal")
            description: Human-readable description
            category: Tool category (e.g., "vedastro", "elemental", "execution")
            parameters: Parameter schema
            examples: Usage examples
        """
        tool_info = {
            "name": name,
            "description": description,
            "category": category,
            "parameters": parameters or {},
            "examples": examples or [],
            "search_text": f"{name} {description} {category}".lower(),
        }

        self.tools[name] = tool_info

        # Add to category
        if category not in self.categories:
            self.categories[category] = []
        if name not in self.categories[category]:
            self.categories[category].append(name)

        # Add to vector DB if available
        if self.use_embeddings and self.collection:
            try:
                self.collection.add(
                    documents=[description],
                    metadatas=[{"name": name, "category": category}],
                    ids=[name],
                )
            except Exception as e:
                logger.warning(f"Failed to add tool to embeddings: {e}")

        logger.debug(f"Registered tool: {name} (category: {category})")

    def unregister_tool(self, name: str) -> bool:
        """
        Remove a tool from the registry.

        Args:
            name: Tool name to remove

        Returns:
            True if removed, False if not found
        """
        if name not in self.tools:
            return False

        tool_info = self.tools.pop(name)
        category = tool_info["category"]

        # Remove from category
        if category in self.categories and name in self.categories[category]:
            self.categories[category].remove(name)

        # Remove from vector DB
        if self.use_embeddings and self.collection:
            try:
                self.collection.delete(ids=[name])
            except Exception as e:
                logger.warning(f"Failed to remove tool from embeddings: {e}")

        logger.debug(f"Unregistered tool: {name}")
        return True

    def find_tool(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        """
        Find tools matching a natural language query.

        Args:
            query: Natural language query (e.g., "get astrology signal")
            top_k: Maximum number of results

        Returns:
            List of matching tools with scores
        """
        if self.use_embeddings and self.collection:
            return self._search_embeddings(query, top_k)
        else:
            return self._search_keywords(query, top_k)

    def _search_embeddings(self, query: str, top_k: int) -> list[dict[str, Any]]:
        """Search using vector embeddings."""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=min(top_k, len(self.tools)),
                include=["metadatas", "distances"],
            )

            matches = []
            for i, name in enumerate(results["ids"][0]):
                metadata = results["metadatas"][0][i]
                distance = results["distances"][0][i]

                # Convert distance to similarity score (0-1)
                similarity = 1.0 / (1.0 + distance)

                tool_info = self.tools.get(name, {})
                matches.append(
                    {
                        "name": name,
                        "category": metadata.get("category", "unknown"),
                        "description": tool_info.get("description", ""),
                        "similarity": round(similarity, 3),
                        "match_type": "semantic",
                    }
                )

            return matches

        except Exception as e:
            logger.error(f"Embedding search failed: {e}")
            return self._search_keywords(query, top_k)

    def _search_keywords(self, query: str, top_k: int) -> list[dict[str, Any]]:
        """Fallback keyword search."""
        query_words = query.lower().split()
        scores = []

        for name, tool_info in self.tools.items():
            search_text = tool_info["search_text"]

            # Calculate score based on word matches
            score = 0
            for word in query_words:
                if len(word) < 3:  # Skip very short words
                    continue

                if word in search_text:
                    score += 1

                    # Bonus for exact matches in name
                    if word in name.lower():
                        score += 2

            if score > 0:
                scores.append((name, score))

        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)

        # Format results
        matches = []
        for name, score in scores[:top_k]:
            tool_info = self.tools[name]
            matches.append(
                {
                    "name": name,
                    "category": tool_info["category"],
                    "description": tool_info["description"],
                    "similarity": round(min(score / 5, 1.0), 3),  # Normalize to 0-1
                    "match_type": "keyword",
                }
            )

        return matches

    def get_tools_by_category(self, category: str) -> list[dict[str, Any]]:
        """
        Get all tools in a category.

        Args:
            category: Tool category

        Returns:
            List of tools in the category
        """
        tool_names = self.categories.get(category, [])
        return [self.tools[name] for name in tool_names if name in self.tools]

    def get_all_categories(self) -> list[str]:
        """Get list of all categories."""
        return list(self.categories.keys())

    def get_tool_info(self, name: str) -> dict[str, Any] | None:
        """
        Get detailed information about a tool.

        Args:
            name: Tool name

        Returns:
            Tool information or None if not found
        """
        return self.tools.get(name)

    def recommend_tools(self, context: dict[str, Any], top_k: int = 3) -> list[dict[str, Any]]:
        """
        Recommend tools based on current context.

        Args:
            context: Context dict with keys like:
                    - "intent": Trading intent ("buy", "sell", "analyze")
                    - "asset_type": Type of asset ("crypto", "stock", "forex")
                    - "timeframe": Trading timeframe ("scalp", "swing", "longterm")
                    - "indicators": Available technical indicators
        Returns:
            List of recommended tools
        """
        recommendations = []

        # Build query from context
        query_parts = []

        if "intent" in context:
            intent_queries = {
                "buy": "buy entry signal",
                "sell": "sell exit signal",
                "analyze": "analyze research",
                "hedge": "hedge risk protection",
            }
            query_parts.append(intent_queries.get(context["intent"], context["intent"]))

        if "asset_type" in context:
            query_parts.append(context["asset_type"])

        if "timeframe" in context:
            timeframe_queries = {
                "scalp": "short term quick",
                "day": "intraday daily",
                "swing": "swing medium term",
                "longterm": "long term investment",
            }
            query_parts.append(timeframe_queries.get(context["timeframe"], context["timeframe"]))

        if "needs_risk_check" in context and context["needs_risk_check"]:
            query_parts.append("risk management position sizing")

        if "needs_astrology" in context and context["needs_astrology"]:
            query_parts.append("vedic astrology")

        query = " ".join(query_parts)

        # Search for matching tools
        matches = self.find_tool(query, top_k=top_k * 2)  # Get more for diversity

        # Ensure diversity across categories
        seen_categories = set()
        for match in matches:
            if len(recommendations) >= top_k:
                break

            cat = match["category"]
            if cat not in seen_categories or len(seen_categories) >= 3:
                recommendations.append(match)
                seen_categories.add(cat)

        return recommendations

    def list_all_tools(self) -> list[dict[str, Any]]:
        """List all registered tools."""
        return list(self.tools.values())

    def get_stats(self) -> dict[str, Any]:
        """Get registry statistics."""
        return {
            "total_tools": len(self.tools),
            "categories": len(self.categories),
            "tools_per_category": {cat: len(tools) for cat, tools in self.categories.items()},
            "embedding_enabled": self.use_embeddings,
        }


# Global registry instance
_global_registry: ToolRegistry | None = None


def get_tool_registry(use_embeddings: bool = True) -> ToolRegistry:
    """Get or create global tool registry."""
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry(use_embeddings=use_embeddings)
    return _global_registry


def register_default_tools(registry: ToolRegistry | None = None) -> ToolRegistry:
    """
    Register default MCP tools in the registry.

    Args:
        registry: ToolRegistry instance (creates new if None)

    Returns:
        Registry with default tools
    """
    if registry is None:
        registry = get_tool_registry()

    # VedAstro tools
    registry.register_tool(
        name="vedastro__generate_signal",
        description="Generate trading signal from Vedic astrology analysis including planetary positions, aspects, and dasha periods",
        category="vedastro",
        parameters={
            "symbol": {"type": "string", "description": "Asset symbol"},
            "current_price": {"type": "number", "description": "Current market price"},
        },
        examples=[{"symbol": "BTC", "current_price": 45000}],
    )

    registry.register_tool(
        name="vedastro__get_dasha",
        description="Get Vimshottari Dasha planetary period information for timing analysis",
        category="vedastro",
        parameters={"symbol": {"type": "string", "description": "Asset symbol"}},
    )

    registry.register_tool(
        name="vedastro__get_transits",
        description="Get current planetary transits (Gochara) for market timing",
        category="vedastro",
        parameters={"symbol": {"type": "string", "description": "Asset symbol"}},
    )

    registry.register_tool(
        name="vedic__calculate_vimshottari_dasha",
        description="Calculate complete Vimshottari Dasha cycle for birth chart analysis",
        category="vedastro",
        parameters={
            "birth_nakshatra": {"type": "string", "description": "Birth nakshatra name"},
            "birth_nakshatra_pad": {"type": "integer", "description": "Nakshatra pad (1-4)"},
            "birth_date": {"type": "string", "description": "Birth date (YYYY-MM-DD)"},
        },
    )

    registry.register_tool(
        name="vedic__get_nakshatra_analysis",
        description="Analyze nakshatra (lunar mansion) characteristics and trading implications",
        category="vedastro",
        parameters={
            "nakshatra": {"type": "string", "description": "Nakshatra name"},
            "pada": {"type": "integer", "description": "Pad/quarter (1-4)"},
        },
    )

    registry.register_tool(
        name="vedic__calculate_transits",
        description="Calculate planetary transits for a specific date with market predictions",
        category="vedastro",
        parameters={
            "date": {"type": "string", "description": "Date (YYYY-MM-DD)"},
            "symbols": {"type": "array", "description": "List of asset symbols"},
        },
    )

    # Elemental tools
    registry.register_tool(
        name="elemental__fire_position_size",
        description="Calculate position size using Fire element (Agni) - momentum and aggressive sizing",
        category="elemental",
        parameters={
            "symbol": {"type": "string"},
            "portfolio_value": {"type": "number"},
            "vedastro_score": {"type": "number"},
            "dominant_planet": {"type": "string"},
        },
    )

    registry.register_tool(
        name="elemental__earth_entry_check",
        description="Check if entry is allowed using Earth element (Prithvi) - stability and timing",
        category="elemental",
        parameters={"symbol": {"type": "string"}, "trade_history": {"type": "array"}},
    )

    registry.register_tool(
        name="elemental__earth_exit_check",
        description="Check if position should be exited using Earth element - trailing stops and hold limits",
        category="elemental",
        parameters={
            "symbol": {"type": "string"},
            "entry_date": {"type": "string"},
            "current_date": {"type": "string"},
            "entry_price": {"type": "number"},
            "current_price": {"type": "number"},
            "peak_price": {"type": "number"},
        },
    )

    registry.register_tool(
        name="elemental__water_regime_check",
        description="Check market regime using Water element (Apas) - trend following and adaptability",
        category="elemental",
        parameters={"symbol": {"type": "string"}, "recent_closes": {"type": "array"}},
    )

    registry.register_tool(
        name="elemental__ether_consensus",
        description="Calculate final consensus from all four elements (Akasha) - integration and balance",
        category="elemental",
        parameters={
            "fire_vote": {"type": "number", "description": "Fire element score (-1 to 1)"},
            "earth_vote": {"type": "number", "description": "Earth element score (-1 to 1)"},
            "water_vote": {"type": "number", "description": "Water element score (-1 to 1)"},
            "air_vote": {"type": "number", "description": "Air element score (-1 to 1)"},
        },
    )

    # Execution tools
    registry.register_tool(
        name="execution__execute_paper_trade",
        description="Execute a paper/simulated trade for testing strategies",
        category="execution",
        parameters={
            "symbol": {"type": "string"},
            "side": {"type": "string", "enum": ["buy", "sell"]},
            "quantity": {"type": "number"},
            "price": {"type": "number"},
        },
    )

    registry.register_tool(
        name="execution__get_open_positions",
        description="Get all currently open positions in portfolio",
        category="execution",
    )

    registry.register_tool(
        name="execution__get_trade_history",
        description="Get historical trade execution records",
        category="execution",
    )

    registry.register_tool(
        name="execution__close_position",
        description="Close an existing open position",
        category="execution",
        parameters={"position_id": {"type": "string"}},
    )

    # Data tools
    registry.register_tool(
        name="data__get_historical_prices",
        description="Get historical price data for backtesting and analysis",
        category="data",
        parameters={
            "symbol": {"type": "string"},
            "start_date": {"type": "string"},
            "end_date": {"type": "string"},
            "timeframe": {"type": "string", "enum": ["1m", "5m", "15m", "1h", "4h", "1d"]},
        },
    )

    registry.register_tool(
        name="data__get_portfolio_status",
        description="Get current portfolio status including positions and P&L",
        category="data",
    )

    registry.register_tool(
        name="data__get_market_regime",
        description="Analyze current market regime (trending, ranging, volatile)",
        category="data",
        parameters={"symbol": {"type": "string"}},
    )

    logger.info(f"Registered {len(registry.list_all_tools())} default tools")
    return registry
