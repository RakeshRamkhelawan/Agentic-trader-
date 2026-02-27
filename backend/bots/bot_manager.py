"""Manager for AI trading bots."""

import asyncio
from typing import Dict, List, Optional, Type
from datetime import datetime

from .base_bot import BaseTradingBot, BotConfig, BotDifficulty, BotPersonality
from .trend_bot import TrendFollowerBot
from .mean_reversion_bot import MeanReversionBot
from .momentum_bot import MomentumBot
from .random_bot import RandomBot


class BotManager:
    """
    Manages AI trading bots for tournaments.
    
    Features:
    - Spawn bots for solo tournaments
    - Run bot simulations
    - Track bot performance
    - Balance bot difficulty
    """
    
    BOT_TYPES: Dict[str, Type[BaseTradingBot]] = {
        "trend": TrendFollowerBot,
        "mean_reversion": MeanReversionBot,
        "momentum": MomentumBot,
        "random": RandomBot,
    }
    
    def __init__(self):
        self._bots: Dict[str, BaseTradingBot] = {}
        self._tournament_bots: Dict[str, List[str]] = {}  # tournament_id -> bot_ids
        self._running_simulations: Dict[str, asyncio.Task] = {}
    
    def create_bot(
        self,
        bot_type: str,
        name: Optional[str] = None,
        difficulty: BotDifficulty = BotDifficulty.MEDIUM,
    ) -> BaseTradingBot:
        """Create a new bot."""
        bot_class = self.BOT_TYPES.get(bot_type, RandomBot)
        
        # Generate name if not provided
        if name is None:
            name = f"{bot_type.title()}Bot_{len(self._bots) + 1}"
        
        config = BotConfig(
            name=name,
            difficulty=difficulty,
            personality=self._get_personality_for_bot_type(bot_type),
        )
        
        bot = bot_class(config)
        self._bots[bot.competitor.id] = bot
        
        return bot
    
    def _get_personality_for_bot_type(self, bot_type: str) -> BotPersonality:
        """Get default personality for bot type."""
        personalities = {
            "trend": BotPersonality.BALANCED,
            "mean_reversion": BotPersonality.CONSERVATIVE,
            "momentum": BotPersonality.AGGRESSIVE,
            "random": BotPersonality.BALANCED,
        }
        return personalities.get(bot_type, BotPersonality.BALANCED)
    
    def spawn_tournament_bots(
        self,
        tournament_id: str,
        count: int = 5,
        difficulty_mix: Optional[Dict[BotDifficulty, int]] = None,
    ) -> List[BaseTradingBot]:
        """
        Spawn bots for a tournament.
        
        Args:
            tournament_id: Tournament to join
            count: Number of bots to spawn
            difficulty_mix: Distribution of difficulties
            
        Returns:
            List of created bots
        """
        if difficulty_mix is None:
            # Default mix
            difficulty_mix = {
                BotDifficulty.EASY: count // 3,
                BotDifficulty.MEDIUM: count // 3,
                BotDifficulty.HARD: count - 2 * (count // 3),
            }
        
        bots = []
        bot_types = list(self.BOT_TYPES.keys())
        
        for difficulty, num_bots in difficulty_mix.items():
            for i in range(num_bots):
                bot_type = bot_types[len(bots) % len(bot_types)]
                bot = self.create_bot(
                    bot_type=bot_type,
                    difficulty=difficulty,
                )
                bots.append(bot)
                
                # Track tournament membership
                if tournament_id not in self._tournament_bots:
                    self._tournament_bots[tournament_id] = []
                self._tournament_bots[tournament_id].append(bot.competitor.id)
        
        return bots
    
    async def run_bot_simulation(
        self,
        tournament_id: str,
        symbol: str = "BTC-EUR",
        price_feed: Optional[List[float]] = None,
    ) -> None:
        """
        Run simulation for all bots in a tournament.
        
        Args:
            tournament_id: Tournament to simulate
            symbol: Trading symbol
            price_feed: Optional price data feed
        """
        bot_ids = self._tournament_bots.get(tournament_id, [])
        
        if not bot_ids:
            return
        
        # Generate mock price data if not provided
        if price_feed is None:
            price_feed = self._generate_mock_prices()
        
        # Run each bot
        for bot_id in bot_ids:
            bot = self._bots.get(bot_id)
            if bot:
                await bot.run_simulation_step(
                    symbol=symbol,
                    price_data=price_feed,
                    current_price=price_feed[-1],
                )
    
    def _generate_mock_prices(self, length: int = 100) -> List[float]:
        """Generate mock price data for simulation."""
        prices = [50000.0]  # Start price
        
        for _ in range(length - 1):
            # Random walk with slight upward bias
            change = prices[-1] * (random.uniform(-0.02, 0.025))
            prices.append(prices[-1] + change)
        
        return prices
    
    async def start_continuous_simulation(
        self,
        tournament_id: str,
        interval_seconds: int = 60,
    ) -> None:
        """Start continuous simulation loop."""
        async def simulation_loop():
            while True:
                await self.run_bot_simulation(tournament_id)
                await asyncio.sleep(interval_seconds)
        
        task = asyncio.create_task(simulation_loop())
        self._running_simulations[tournament_id] = task
    
    def stop_simulation(self, tournament_id: str) -> None:
        """Stop simulation for a tournament."""
        task = self._running_simulations.get(tournament_id)
        if task:
            task.cancel()
            del self._running_simulations[tournament_id]
    
    def get_bot(self, bot_id: str) -> Optional[BaseTradingBot]:
        """Get bot by ID."""
        return self._bots.get(bot_id)
    
    def get_tournament_bots(self, tournament_id: str) -> List[BaseTradingBot]:
        """Get all bots in a tournament."""
        bot_ids = self._tournament_bots.get(tournament_id, [])
        return [self._bots[bid] for bid in bot_ids if bid in self._bots]
    
    def get_bot_rankings(self, tournament_id: str) -> List[Dict]:
        """Get bot rankings for a tournament."""
        bots = self.get_tournament_bots(tournament_id)
        
        rankings = [
            {
                "bot_id": bot.competitor.id,
                "name": bot.competitor.name,
                "balance": bot.balance,
                "pnl": bot.balance - 10000.0,
                "return_pct": ((bot.balance - 10000.0) / 10000.0) * 100,
                "total_trades": bot.total_trades,
                "win_rate": (bot.winning_trades / bot.total_trades * 100) if bot.total_trades > 0 else 0,
            }
            for bot in bots
        ]
        
        # Sort by balance
        rankings.sort(key=lambda x: x["balance"], reverse=True)
        
        # Add rank
        for i, rank in enumerate(rankings, 1):
            rank["rank"] = i
        
        return rankings
    
    def remove_bot(self, bot_id: str) -> bool:
        """Remove a bot."""
        if bot_id in self._bots:
            del self._bots[bot_id]
            
            # Remove from tournament tracking
            for tournament_id, bot_ids in self._tournament_bots.items():
                if bot_id in bot_ids:
                    bot_ids.remove(bot_id)
            
            return True
        return False
    
    def cleanup_tournament(self, tournament_id: str) -> None:
        """Clean up all bots for a tournament."""
        # Stop simulation
        self.stop_simulation(tournament_id)
        
        # Remove bots
        bot_ids = self._tournament_bots.get(tournament_id, [])
        for bot_id in bot_ids:
            self.remove_bot(bot_id)
        
        # Remove tournament tracking
        if tournament_id in self._tournament_bots:
            del self._tournament_bots[tournament_id]
    
    def get_stats(self) -> Dict:
        """Get bot manager statistics."""
        return {
            "total_bots": len(self._bots),
            "active_tournaments": len(self._tournament_bots),
            "running_simulations": len(self._running_simulations),
            "bots_by_type": self._count_bots_by_type(),
        }
    
    def _count_bots_by_type(self) -> Dict[str, int]:
        """Count bots by type."""
        counts = {}
        for bot in self._bots.values():
            bot_type = type(bot).__name__
            counts[bot_type] = counts.get(bot_type, 0) + 1
        return counts


import random
