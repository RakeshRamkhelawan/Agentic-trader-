/**
 * EvolutionaryTuningPanel - Automated Hyperparameter Tuning (AHT) Visualization
 *
 * Displays the current 'Auto-Pilot' agent weights and their expected win-rates
 * across different market regimes (Expansion, Contraction, Neutral).
 * 
 * Visualizes the Thompson Sampling bandit states (alpha/beta) as confidence bars.
 */

import { useEffect, useState, useCallback } from 'react';
import { 
  Zap, 
  BarChart3, 
  TrendingUp, 
  TrendingDown, 
  Minus,
  Info,
  RefreshCw,
  Trophy,
  AlertTriangle
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { 
  paperTradingApi, 
  type TuningStatsResponse,
  type RegimeTuning
} from '@/lib/api/paper-trading';

// ============================================================================
// AGENT CONFIG
// ============================================================================

const AGENT_COLORS: Record<string, string> = {
  vedastro: 'bg-purple-500',
  earth: 'bg-green-500',
  fire: 'bg-red-500',
  water: 'bg-blue-500',
};

const AGENT_LABELS: Record<string, string> = {
  vedastro: 'VedAstro',
  earth: 'Earth (Risk)',
  fire: 'Fire (Momentum)',
  water: 'Water (Regime)',
};

// ============================================================================
// REGIME SUB-COMPONENT
// ============================================================================

function RegimeWeights({ data }: { data: RegimeTuning }) {
  const sortedAgents = Object.entries(data.weights)
    .filter(([key]) => key !== 'threshold')
    .sort(([, a], [, b]) => b - a);

  const threshold = data.weights.threshold || 0.35;

  return (
    <div className="space-y-4 animate-fade-in">
      {/* Threshold indicator */}
      <div className="flex items-center justify-between p-2 rounded-lg bg-white/5 border border-white/10">
        <div className="flex items-center gap-2">
          <Info className="w-3 h-3 text-cyan-400" />
          <span className="text-[11px] text-gray-400 uppercase tracking-wider">Consensus Threshold</span>
        </div>
        <Badge variant="outline" className="font-mono text-cyan-400 border-cyan-500/30">
          {threshold.toFixed(2)}
        </Badge>
      </div>

      {/* Slippage indicator */}
      {data.avg_slippage !== undefined && (
        <div className="flex items-center justify-between p-2 rounded-lg bg-orange-500/5 border border-orange-500/10">
          <div className="flex items-center gap-2">
            <RefreshCw className="w-3 h-3 text-orange-400" />
            <span className="text-[11px] text-gray-400 uppercase tracking-wider">Avg Slippage</span>
          </div>
          <Badge variant="outline" className={cn(
            "font-mono border-orange-500/30",
            data.avg_slippage > 0.002 ? "text-red-400" : "text-orange-400"
          )}>
            {(data.avg_slippage * 100).toFixed(3)}%
          </Badge>
        </div>
      )}

      {/* Weights list */}
      <div className="space-y-3">
        {sortedAgents.map(([agent, weight]) => {
          const stats = data.bandit_stats[agent];
          const winRate = stats ? stats.expected_winrate * 100 : 50;
          const totalTrades = stats ? (stats.alpha + stats.beta - 1) : 0; // -1 because of 0.5 priors

          return (
            <div key={agent} className="space-y-1.5 focus-within:ring-1 focus-within:ring-white/20 p-1 rounded transition-all">
              <div className="flex items-center justify-between text-[11px]">
                <div className="flex items-center gap-2">
                  <div className={cn("w-1.5 h-1.5 rounded-full", AGENT_COLORS[agent.toLowerCase()] || 'bg-gray-500')} />
                  <span className="font-medium text-gray-200">
                    {AGENT_LABELS[agent.toLowerCase()] || agent}
                  </span>
                </div>
                <div className="flex items-center gap-3 font-mono">
                  <span className="text-white">{(weight * 100).toFixed(1)}%</span>
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <span className={cn(
                          "cursor-help",
                          winRate > 55 ? "text-green-400" : winRate < 45 ? "text-red-400" : "text-gray-400"
                        )}>
                          {winRate.toFixed(1)}%
                        </span>
                      </TooltipTrigger>
                      <TooltipContent className="bg-black border-[#333] text-[10px]">
                        Exp. Accuracy ({totalTrades} samples)
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Progress 
                  value={weight * 100} 
                  className={cn("h-1.5 bg-white/5", AGENT_COLORS[agent.toLowerCase()] || 'bg-gray-500')} 
                />
              </div>
            </div>
          );
        })}
      </div>
      
      {/* Top Agent Badge */}
      {sortedAgents.length > 0 && (
        <div className="pt-2 flex justify-center">
          <Badge className="bg-purple-500/20 text-purple-400 border-purple-500/30 text-[10px] gap-1 px-3">
            <Trophy className="w-3 h-3" />
            Dominant: {AGENT_LABELS[sortedAgents[0][0].toLowerCase()] || sortedAgents[0][0]}
          </Badge>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export function EvolutionaryTuningPanel() {
  const [data, setData] = useState<TuningStatsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<string | null>(null);

  const fetchStats = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await paperTradingApi.getTuningStats();
      setData(response);
      setLastUpdate(new Date().toLocaleTimeString('nl-NL'));
    } catch (err) {
      console.error("[TUNER-UI] Failed to fetch tuning stats", err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStats();
    const id = setInterval(fetchStats, 60000); // 1 min sync
    return () => clearInterval(id);
  }, [fetchStats]);

  if (!data) return null;

  return (
    <Card className="bg-[#111111] border-[#262626] overflow-hidden">
      {/* Animated accent bar */}
      <div className="h-[2px] bg-gradient-to-r from-cyan-500 via-blue-500 to-indigo-500 animate-pulse" />

      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-white text-sm">
            <Zap className="h-4 w-4 text-cyan-400" />
            Auto-Pilot: Agent Tuning
            {data && (
              <Badge variant="outline" className="text-[10px] bg-cyan-500/10 text-cyan-400 border-cyan-500/30">
                Agressief
              </Badge>
            )}
          </CardTitle>
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={fetchStats}
            disabled={isLoading}
            className="h-7 w-7 p-0 text-[#666666] hover:text-white"
          >
            <RefreshCw className={cn("h-3 w-3", isLoading && "animate-spin")} />
          </Button>
        </div>
        <p className="text-[11px] text-[#444444] leading-relaxed">
          Zelflerende Bayesian Thompson Sampling. Optimaliseert wegingen per marktregime op basis van bewezen win-rate.
        </p>
      </CardHeader>

      <CardContent className="pt-2">
        <Tabs defaultValue="expansion" className="w-full">
          <TabsList className="grid grid-cols-3 bg-black/40 h-8 p-1 mb-4">
            <TabsTrigger value="expansion" className="text-[10px] data-[state=active]:bg-green-500/20 data-[state=active]:text-green-400">
              <TrendingUp className="w-3 h-3 mr-1" />
              Expansion
            </TabsTrigger>
            <TabsTrigger value="contraction" className="text-[10px] data-[state=active]:bg-red-500/20 data-[state=active]:text-red-400">
              <TrendingDown className="w-3 h-3 mr-1" />
              Contraction
            </TabsTrigger>
            <TabsTrigger value="neutral" className="text-[10px] data-[state=active]:bg-gray-500/20 data-[state=active]:text-gray-400">
              <Minus className="w-3 h-3 mr-1" />
              Neutral
            </TabsTrigger>
          </TabsList>

          {Object.entries(data.regimes).map(([regime, tuning]) => (
            <TabsContent key={regime} value={regime}>
              <RegimeWeights data={tuning} />
            </TabsContent>
          ))}
        </Tabs>

        {/* Footer info */}
        <div className="mt-4 pt-3 border-t border-white/5 flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-[9px] text-yellow-500/70 uppercase font-mono">
            <AlertTriangle className="w-3 h-3" />
            Learning Rate: High
          </div>
          <span className="text-[10px] text-[#444444] font-mono">
            {lastUpdate ? `SYNC: ${lastUpdate}` : 'SYNCING...'}
          </span>
        </div>
      </CardContent>
    </Card>
  );
}

export default EvolutionaryTuningPanel;
