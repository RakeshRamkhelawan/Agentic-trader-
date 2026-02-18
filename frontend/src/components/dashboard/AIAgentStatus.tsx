import { useState, useEffect } from 'react';
import { Bot, Activity, TrendingUp, Brain, ChevronDown, ChevronUp, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAppStore } from '@/store/appStore';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';

export function AIAgentStatus() {
  const [expanded, setExpanded] = useState(false);
  const { agentsStatus, agentsCoherence, isLoadingAgents, fetchAgentsStatus, tradeHistory } = useAppStore();

  useEffect(() => {
    fetchAgentsStatus();
    const interval = setInterval(fetchAgentsStatus, 30000);
    return () => clearInterval(interval);
  }, [fetchAgentsStatus]);

  const activeCount = agentsStatus.filter((s) => s.status === 'running').length;
  const avgPerformance =
    agentsStatus.length > 0
      ? agentsStatus.reduce((acc, s) => acc + s.performance, 0) / agentsStatus.length
      : 0;
  const totalTrades = agentsStatus.reduce((acc, s) => acc + s.trades, 0);

  // Use real trade history for activity log (last 5 entries)
  const recentLogs = tradeHistory.slice(0, 5).map((t) => ({
    id: t.id,
    timestamp: new Date(t.timestamp),
    type: t.side === 'buy' ? 'success' : 'info',
    message: `${t.side === 'buy' ? 'Buy' : 'Sell'} order filled: ${t.amount} ${t.symbol} @ $${t.price.toLocaleString()}`,
  }));

  const logColors: Record<string, string> = {
    info: 'text-trade-blue',
    success: 'text-trade-green',
    warning: 'text-trade-orange',
    error: 'text-trade-red',
  };

  if (isLoadingAgents && agentsStatus.length === 0) {
    return (
      <Card className='bg-[#111111] border-[#262626] animate-fade-in opacity-0' style={{ animationFillMode: 'forwards', animationDelay: '350ms' }}>
        <CardContent className='flex items-center justify-center py-10'>
          <Loader2 className='w-6 h-6 text-trade-blue animate-spin' />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card
      className={cn('bg-[#111111] border-[#262626] overflow-hidden', 'animate-fade-in opacity-0')}
      style={{ animationFillMode: 'forwards', animationDelay: '350ms' }}
    >
      <CardHeader className='pb-3'>
        <div className='flex items-center justify-between'>
          <div className='flex items-center gap-2'>
            <div className='relative'>
              <div className='w-10 h-10 rounded-xl bg-gradient-to-br from-trade-purple to-trade-blue flex items-center justify-center'>
                <Bot className='w-5 h-5 text-white' />
              </div>
              {activeCount > 0 && (
                <span className='absolute -top-1 -right-1 w-3 h-3 bg-trade-green rounded-full animate-pulse' />
              )}
            </div>
            <div>
              <CardTitle className='text-lg font-semibold text-white'>AI Agents</CardTitle>
              <div className='flex items-center gap-2'>
                <span
                  className={cn(
                    'text-xs px-2 py-0.5 rounded-full border',
                    activeCount > 0
                      ? 'bg-trade-green/10 text-trade-green border-trade-green/20'
                      : 'bg-muted/10 text-muted-foreground border-muted/20'
                  )}
                >
                  {activeCount > 0 ? 'Active' : 'Idle'}
                </span>
                <span className='text-xs text-muted-foreground'>{activeCount} running</span>
              </div>
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent className='space-y-4'>
        <div className='grid grid-cols-2 gap-3'>
          <div className='bg-[#0A0A0A] rounded-xl p-3'>
            <div className='flex items-center gap-2 text-muted-foreground mb-1'>
              <TrendingUp className='w-4 h-4' />
              <span className='text-xs'>Coherence</span>
            </div>
            <p className='text-xl font-bold font-mono text-trade-blue'>
              {(agentsCoherence * 100).toFixed(1)}%
            </p>
          </div>
          <div className='bg-[#0A0A0A] rounded-xl p-3'>
            <div className='flex items-center gap-2 text-muted-foreground mb-1'>
              <Activity className='w-4 h-4' />
              <span className='text-xs'>Total Trades</span>
            </div>
            <p className='text-xl font-bold text-white font-mono'>{totalTrades}</p>
          </div>
        </div>

        {agentsStatus.length > 0 && (
          <div className='space-y-2'>
            <p className='text-sm text-muted-foreground'>Active Agents</p>
            <div className='space-y-2'>
              {agentsStatus.slice(0, expanded ? undefined : 3).map((agent) => (
                <div
                  key={agent.id}
                  className='flex items-center justify-between p-2 rounded-lg bg-[#0A0A0A] hover:bg-[#1A1A1A] transition-colors'
                >
                  <div className='flex items-center gap-2'>
                    <Brain className='w-4 h-4 text-trade-purple' />
                    <span className='text-sm text-white'>{agent.name}</span>
                  </div>
                  <div className='flex items-center gap-2'>
                    <span
                      className={cn(
                        'text-sm font-mono',
                        agent.performance >= 0 ? 'text-trade-green' : 'text-trade-red'
                      )}
                    >
                      {agent.prana !== undefined ? `${agent.prana.toFixed(1)}p` : '—'}
                    </span>
                    <span
                      className={cn(
                        'w-2 h-2 rounded-full',
                        agent.status === 'running' && 'bg-trade-green',
                        agent.status === 'paused' && 'bg-trade-orange',
                        agent.status === 'error' && 'bg-trade-red'
                      )}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {agentsStatus.length === 0 && !isLoadingAgents && (
          <p className='text-sm text-muted-foreground text-center py-4'>No agents registered</p>
        )}

        {agentsStatus.length > 3 && (
          <Button
            variant='ghost'
            size='sm'
            onClick={() => setExpanded(!expanded)}
            className='w-full text-muted-foreground hover:text-white hover:bg-[#1A1A1A]'
          >
            {expanded ? (
              <> Show Less <ChevronUp className='w-4 h-4 ml-1' /></>
            ) : (
              <> Show All ({agentsStatus.length}) <ChevronDown className='w-4 h-4 ml-1' /></>
            )}
          </Button>
        )}

        {recentLogs.length > 0 && (
          <div className='pt-2 border-t border-[#262626]'>
            <p className='text-sm text-muted-foreground mb-2'>Recent Activity</p>
            <ScrollArea className='h-[120px]'>
              <div className='space-y-2'>
                {recentLogs.map((log) => (
                  <div key={log.id} className='flex items-start gap-2 text-sm'>
                    <span className='text-xs text-muted-foreground whitespace-nowrap'>
                      {log.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                    <span className={cn('font-medium', logColors[log.type])}>{log.message}</span>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
