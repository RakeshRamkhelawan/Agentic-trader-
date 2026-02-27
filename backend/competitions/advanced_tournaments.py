"""Advanced tournament types with special rules."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional, Dict, Any

from .models.tournament import Tournament, TournamentType, TournamentStatus
from .tournament_engine import TournamentEngine


class TournamentVariant(Enum):
    """Tournament variants with special rules."""
    CRYPTO_ONLY = "crypto_only"           # Crypto pairs only
    FOREX_ONLY = "forex_only"             # Forex pairs only
    STOCKS_ONLY = "stocks_only"           # Stock pairs only
    COMMODITIES_ONLY = "commodities_only" # Commodities only
    SHORT_ONLY = "short_only"             # Only short positions allowed
    LONG_ONLY = "long_only"               # Only long positions allowed
    HIGH_LEVERAGE = "high_leverage"       # Higher leverage allowed
    NO_LEVERAGE = "no_leverage"           # Spot trading only
    ALGORITHMIC = "algorithmic"           # Bot-only tournament
    SOLO = "solo"                         # Against bots only


@dataclass
class TournamentRules:
    """Special rules for tournament variants."""
    allowed_symbols: Optional[List[str]] = None
    blocked_symbols: Optional[List[str]] = None
    allowed_sides: Optional[List[str]] = None  # "buy", "sell"
    max_leverage: float = 1.0
    min_leverage: float = 1.0
    max_position_size: float = 0.2  # 20% of balance
    require_stop_loss: bool = False
    max_trades_per_day: Optional[int] = None
    allow_bots: bool = True
    allow_humans: bool = True
    entry_fee_multiplier: float = 1.0
    prize_multiplier: float = 1.0


class AdvancedTournamentEngine(TournamentEngine):
    """
    Extended tournament engine with variant support.
    
    Supports specialized tournaments like:
    - Crypto-only for digital asset specialists
    - Short-only for bear market strategies
    - Algorithmic for bot competitions
    """
    
    VARIANT_SYMBOLS: Dict[TournamentVariant, List[str]] = {
        TournamentVariant.CRYPTO_ONLY: [
            "BTC-EUR", "ETH-EUR", "XRP-EUR", "ADA-EUR", "SOL-EUR",
            "DOT-EUR", "LINK-EUR", "MATIC-EUR", "UNI-EUR", "AAVE-EUR",
        ],
        TournamentVariant.FOREX_ONLY: [
            "EUR-USD", "GBP-USD", "USD-JPY", "USD-CHF", "AUD-USD",
            "USD-CAD", "NZD-USD", "EUR-GBP", "EUR-JPY", "GBP-JPY",
        ],
        TournamentVariant.STOCKS_ONLY: [
            "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA",
            "META", "NVDA", "NFLX", "AMD", "INTC",
        ],
        TournamentVariant.COMMODITIES_ONLY: [
            "GOLD", "SILVER", "OIL", "NATGAS", "COPPER",
        ],
    }
    
    VARIANT_RULES: Dict[TournamentVariant, TournamentRules] = {
        TournamentVariant.SHORT_ONLY: TournamentRules(
            allowed_sides=["sell"],
            max_position_size=0.15,
        ),
        TournamentVariant.LONG_ONLY: TournamentRules(
            allowed_sides=["buy"],
            max_position_size=0.25,
        ),
        TournamentVariant.HIGH_LEVERAGE: TournamentRules(
            max_leverage=10.0,
            min_leverage=1.0,
            max_position_size=0.1,
            require_stop_loss=True,
        ),
        TournamentVariant.NO_LEVERAGE: TournamentRules(
            max_leverage=1.0,
            min_leverage=1.0,
            max_position_size=0.5,
        ),
        TournamentVariant.ALGORITHMIC: TournamentRules(
            allow_humans=False,
            allow_bots=True,
            prize_multiplier=1.5,
        ),
        TournamentVariant.SOLO: TournamentRules(
            allow_bots=True,
            allow_humans=True,  # One human + bots
            entry_fee_multiplier=0.5,
        ),
    }
    
    def __init__(self):
        super().__init__()
        self._tournament_variants: Dict[str, TournamentVariant] = {}
        self._tournament_rules: Dict[str, TournamentRules] = {}
    
    def create_variant_tournament(
        self,
        name: str,
        description: str,
        variant: TournamentVariant,
        base_rules: Optional[TournamentRules] = None,
        **kwargs
    ) -> Tournament:
        """Create a tournament with special rules."""
        # Create base tournament
        tournament = self.create_tournament(
            name=name,
            description=description,
            tournament_type=TournamentType.SPECIAL,
            **kwargs
        )
        
        # Store variant info
        self._tournament_variants[tournament.id] = variant
        
        # Merge rules
        rules = self._get_rules_for_variant(variant)
        if base_rules:
            # Override with provided rules
            for key, value in vars(base_rules).items():
                if value is not None:
                    setattr(rules, key, value)
        
        self._tournament_rules[tournament.id] = rules
        
        return tournament
    
    def _get_rules_for_variant(self, variant: TournamentVariant) -> TournamentRules:
        """Get default rules for variant."""
        if variant in self.VARIANT_RULES:
            return self.VARIANT_RULES[variant]
        
        # For symbol-only variants
        if variant in self.VARIANT_SYMBOLS:
            return TournamentRules(
                allowed_symbols=self.VARIANT_SYMBOLS[variant],
            )
        
        return TournamentRules()
    
    def validate_trade(
        self,
        tournament_id: str,
        symbol: str,
        side: str,
        leverage: float = 1.0,
        is_bot: bool = False,
    ) -> Dict[str, Any]:
        """Validate trade against tournament rules."""
        rules = self._tournament_rules.get(tournament_id)
        if not rules:
            return {"valid": True}
        
        # Check symbol restrictions
        if rules.allowed_symbols and symbol not in rules.allowed_symbols:
            return {
                "valid": False,
                "error": f"Symbol {symbol} not allowed in this tournament",
            }
        
        if rules.blocked_symbols and symbol in rules.blocked_symbols:
            return {
                "valid": False,
                "error": f"Symbol {symbol} is blocked in this tournament",
            }
        
        # Check side restrictions
        if rules.allowed_sides and side not in rules.allowed_sides:
            return {
                "valid": False,
                "error": f"Side {side} not allowed. Allowed: {', '.join(rules.allowed_sides)}",
            }
        
        # Check leverage
        if leverage > rules.max_leverage:
            return {
                "valid": False,
                "error": f"Leverage {leverage}x exceeds maximum {rules.max_leverage}x",
            }
        
        if leverage < rules.min_leverage:
            return {
                "valid": False,
                "error": f"Leverage {leverage}x below minimum {rules.min_leverage}x",
            }
        
        # Check bot/human restrictions
        if is_bot and not rules.allow_bots:
            return {
                "valid": False,
                "error": "Bots not allowed in this tournament",
            }
        
        if not is_bot and not rules.allow_humans:
            return {
                "valid": False,
                "error": "Human trading not allowed in this tournament (bot-only)",
            }
        
        return {"valid": True}
    
    def get_tournament_info(self, tournament_id: str) -> Dict[str, Any]:
        """Get tournament info including variant rules."""
        tournament = self._tournaments.get(tournament_id)
        if not tournament:
            return {"error": "Tournament not found"}
        
        variant = self._tournament_variants.get(tournament_id)
        rules = self._tournament_rules.get(tournament_id)
        
        info = {
            "id": tournament.id,
            "name": tournament.name,
            "description": tournament.description,
            "status": tournament.status.value,
            "variant": variant.value if variant else None,
            "participants": len(tournament.entries),
        }
        
        if rules:
            info["rules"] = {
                "allowed_symbols": rules.allowed_symbols,
                "blocked_symbols": rules.blocked_symbols,
                "allowed_sides": rules.allowed_sides,
                "max_leverage": rules.max_leverage,
                "min_leverage": rules.min_leverage,
                "max_position_size": rules.max_position_size,
                "require_stop_loss": rules.require_stop_loss,
                "allow_bots": rules.allow_bots,
                "allow_humans": rules.allow_humans,
            }
        
        return info
    
    def list_variant_types(self) -> List[Dict[str, Any]]:
        """List all available tournament variants."""
        variants = []
        
        for variant in TournamentVariant:
            rules = self._get_rules_for_variant(variant)
            symbols = self.VARIANT_SYMBOLS.get(variant, [])
            
            variants.append({
                "id": variant.value,
                "name": variant.value.replace("_", " ").title(),
                "description": self._get_variant_description(variant),
                "allowed_symbols": symbols[:5] if symbols else None,  # Show first 5
                "rules": {
                    "max_leverage": rules.max_leverage,
                    "allow_bots": rules.allow_bots,
                    "allow_humans": rules.allow_humans,
                },
            })
        
        return variants
    
    def _get_variant_description(self, variant: TournamentVariant) -> str:
        """Get human-readable description for variant."""
        descriptions = {
            TournamentVariant.CRYPTO_ONLY: "Trade only cryptocurrency pairs",
            TournamentVariant.FOREX_ONLY: "Trade only forex currency pairs",
            TournamentVariant.STOCKS_ONLY: "Trade only stock CFDs",
            TournamentVariant.COMMODITIES_ONLY: "Trade only commodities",
            TournamentVariant.SHORT_ONLY: "Only short positions allowed",
            TournamentVariant.LONG_ONLY: "Only long positions allowed",
            TournamentVariant.HIGH_LEVERAGE: "Higher leverage with stop-loss required",
            TournamentVariant.NO_LEVERAGE: "Spot trading only, no margin",
            TournamentVariant.ALGORITHMIC: "Bot-only competition",
            TournamentVariant.SOLO: "Practice against AI bots",
        }
        return descriptions.get(variant, "Standard tournament")
