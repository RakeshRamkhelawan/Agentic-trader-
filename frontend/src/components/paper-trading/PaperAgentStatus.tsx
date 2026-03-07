/**
 * PaperAgentStatus Component
 * 
 * Shows AI agent status and performance for paper trading.
 */

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';
import { Bot, TrendingUp, Activity } from 'lucide-react';
import { agentsApi, type AgentStrategy } from '@/lib/api';
import usePaperTradingStore from '@/store/paper-trading';

interface AgentWithPerformance extends AgentStrategy {
  last_trade?: string;
  pnl?: number;
}

export function PaperAgentStatus() {
  const { isRunning } = usePaperTradingStore();
  const [agents, setAgents] = useState<AgentWithPerformance[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!isRunning) {
      setAgents([]);
      return;
    }

    const fetchAgents = async () => {
      setIsLoading(true);
      try {
        const data = await agentsApi.getStatus();
        const agentsList: AgentWithPerformance[] = Object.entries(data.agents || {}).map(([id, agent]: [string, any]) => ({
          id,
          name: agent.name || agent.type || id,
          type: agent.type || 'unknown',
          status: agent.is_active ? 'running' : 'paused' as 'running' | 'paused' | 'error',
          performance: agent.performance || 0,
          trades: agent.state?.total_trades || 0,
          prana: agent.prana || 0,
          pnl: agent.pnl || 0,
        }));
        setAgents(agentsList);
      } catch (err) {
        console.error('Failed to fetch agents:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchAgents();
    const interval = setInterval(fetchAgents, 10000);
    return () => clearInterval(interval);
  }, [isRunning]);

  if (!isRunning) {
    return (
      <Card className="border-dashed">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bot className="h-5 w-5" />
            Agent Status
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col items-center justify-center py-8">
          <Activity className="h-12 w-12 text-muted-foreground mb-4" />
          <p className="text-lg font-medium">Agents Ready</p>
          <p className="text-sm text-muted-foreground">
            Start a session to see agent status
          </p>
        </CardContent>
      </Card>
    );
  }

  if (isLoading && agents.length === 0) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-32" />
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-16 w-full" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Bot className="h-5 w-5" />
          Agent Status
          <Badge variant="secondary" className="ml-2">{agents.length}</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {agents.map((agent) => (
            <div
              key={agent.id}
              className="flex items-center justify-between p-3 bg-muted rounded-lg"
            >
              <div className="flex items-center gap-3">
                <div className={`w-2 h-2 rounded-full ${
                  agent.status === 'running' ? 'bg-green-500' : 'bg-yellow-500'
                }`} />
                <div>
                  <p className="font-medium text-sm">{agent.name}</p>
                  <p className="text-xs text-muted-foreground capitalize">
                    {agent.type} • {agent.trades} trades
                  </p>
                </div>
              </div>
              <div className="text-right">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted-foreground">Performance</span>
                  <span className="text-sm font-medium">
                    {agent.performance.toFixed(1)}%
                  </span>
                </div>
                <Progress 
                  value={agent.performance} 
                  className="w-24 h-1.5 mt-1"
                />
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

export default PaperAgentStatus;
