import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Activity, Brain, TrendingUp, Users, Pause, Play } from 'lucide-react';

interface AgentStats {
  name: string;
  winrate: number;
  trades: number;
  pnl: number;
  harmony: number;
}

interface ConsciousnessState {
  globalHarmony: number;
  collectiveConfidence: number;
  activeAgents: number;
  totalTrades: number;
  agentRankings: AgentStats[];
  isPaused: boolean;
  pauseReason?: string;
}

export function ConsciousnessDashboard() {
  const [state, setState] = useState<ConsciousnessState>({
    globalHarmony: 0.64,
    collectiveConfidence: 0.71,
    activeAgents: 27,
    totalTrades: 122324,
    agentRankings: [
      { name: 'ElementalConsensusAgent', winrate: 0.68, trades: 30581, pnl: 0.15, harmony: 0.72 },
      { name: 'RiskCheckAgent', winrate: 0.65, trades: 28500, pnl: 0.12, harmony: 0.70 },
      { name: 'Water_Trend', winrate: 0.62, trades: 30581, pnl: 0.11, harmony: 0.68 },
      { name: 'SentimentAgentV2', winrate: 0.59, trades: 15200, pnl: 0.08, harmony: 0.65 },
      { name: 'Fire_Momentum', winrate: 0.58, trades: 30581, pnl: 0.07, harmony: 0.63 },
    ],
    isPaused: false,
  });

  // Poll for updates
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch('/api/v1/consciousness/state');
        if (response.ok) {
          const data = await response.json();
          setState(data);
        }
      } catch (e) {
        // Use mock data if API fails
      }
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const getHarmonyColor = (score: number) => {
    if (score >= 0.7) return 'text-green-500';
    if (score >= 0.5) return 'text-yellow-500';
    return 'text-red-500';
  };

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <Brain className="w-8 h-8 text-purple-500" />
          Collective Consciousness Dashboard
        </h1>
        {state.isPaused ? (
          <Badge variant="destructive" className="flex items-center gap-1">
            <Pause className="w-4 h-4" />
            Trading Paused: {state.pauseReason}
          </Badge>
        ) : (
          <Badge variant="default" className="flex items-center gap-1 bg-green-500">
            <Play className="w-4 h-4" />
            Trading Active
          </Badge>
        )}
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Global Harmony</CardTitle>
            <Brain className="w-4 h-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${getHarmonyColor(state.globalHarmony)}`}>
              {(state.globalHarmony * 100).toFixed(0)}%
            </div>
            <Progress value={state.globalHarmony * 100} className="mt-2" />
            <p className="text-xs text-muted-foreground mt-2">
              Collective alignment score
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Confidence</CardTitle>
            <TrendingUp className="w-4 h-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {(state.collectiveConfidence * 100).toFixed(0)}%
            </div>
            <Progress value={state.collectiveConfidence * 100} className="mt-2" />
            <p className="text-xs text-muted-foreground mt-2">
              High-confidence trade rate
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Active Agents</CardTitle>
            <Users className="w-4 h-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{state.activeAgents}</div>
            <p className="text-xs text-muted-foreground mt-2">
              With Chitta + LLM enabled
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Trades</CardTitle>
            <Activity className="w-4 h-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{state.totalTrades.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground mt-2">
              Across all agents
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Agent Rankings */}
      <Card>
        <CardHeader>
          <CardTitle>Agent Performance Rankings</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {state.agentRankings.map((agent, index) => (
              <div key={agent.name} className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center font-bold">
                    {index + 1}
                  </div>
                  <div>
                    <p className="font-medium">{agent.name}</p>
                    <p className="text-sm text-muted-foreground">
                      {agent.trades.toLocaleString()} trades
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-6">
                  <div className="text-right">
                    <p className={`font-bold ${getHarmonyColor(agent.harmony)}`}>
                      {(agent.winrate * 100).toFixed(0)}% Winrate
                    </p>
                    <p className="text-sm text-muted-foreground">
                      PnL: {(agent.pnl * 100).toFixed(1)}%
                    </p>
                  </div>
                  <div className="w-32">
                    <Progress value={agent.harmony * 100} className="h-2" />
                    <p className="text-xs text-muted-foreground text-center mt-1">
                      Harmony: {(agent.harmony * 100).toFixed(0)}%
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Live Deliberation Feed */}
      <Card>
        <CardHeader>
          <CardTitle>Live Collective Deliberation</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 text-sm">
            <div className="flex items-center gap-2 p-2 bg-green-500/10 rounded">
              <Badge variant="default">BUY</Badge>
              <span>BTC consensus from 15 agents (78% confidence)</span>
              <span className="text-muted-foreground ml-auto">2s ago</span>
            </div>
            <div className="flex items-center gap-2 p-2 bg-muted rounded">
              <Badge variant="secondary">HOLD</Badge>
              <span>ETH waiting for macro signal</span>
              <span className="text-muted-foreground ml-auto">5s ago</span>
            </div>
            <div className="flex items-center gap-2 p-2 bg-green-500/10 rounded">
              <Badge variant="default">BUY</Badge>
              <span>SOL breakout detected (Water_Trend leading)</span>
              <span className="text-muted-foreground ml-auto">12s ago</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default ConsciousnessDashboard;
