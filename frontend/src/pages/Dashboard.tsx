import { useEffect } from 'react';
import { TrendingUp, TrendingDown, DollarSign, Activity, Zap, Bot } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAppStore } from '@/store/appStore';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { MarketOverview } from '@/components/dashboard/MarketOverview';
import { TradingChart } from '@/components/dashboard/TradingChart';
import { OrderPanel } from '@/components/dashboard/OrderPanel';
import { ActiveOrders } from '@/components/dashboard/ActiveOrders';
import { AIAgentStatus } from '@/components/dashboard/AIAgentStatus';
import { AIAdvisor } from '@/components/dashboard/AIAdvisor';
import { RecentActivity } from '@/components/dashboard/RecentActivity';
import { TopMovers } from '@/components/dashboard/TopMovers';

function StatCard({
  title,
  value,
  change,
  changeType,
  icon: Icon,
  delay,
  isEmpty = false,
  emptyHint,
}:  {
  title: string;
  value: string;
  change: string;
  changeType: 'positive' | 'negative' | 'neutral';
  icon: React.ElementType;
  delay: number;
  isEmpty?: boolean;
  emptyHint?: string;
}) {
  return (
    <Card
      className={cn(
        'bg-[#111111] border-[#262626] hover:border-[#333333] transition-all duration-300',
        'hover:shadow-elevated group',
        'animate-fade-in opacity-0',
        isEmpty && 'border-dashed border-[#333333]'
      )}
      style={{ animationDelay: `${delay}ms`, animationFillMode: 'forwards' }}
    >
      <CardHeader className='flex flex-row items-center justify-between pb-2'>
        <CardTitle className='text-sm font-medium text-[#888888]'>{title}</CardTitle>
        <div className={cn(
          'w-8 h-8 rounded-lg flex items-center justify-center transition-colors',
          isEmpty ? 'bg-[#0A0A0A]' : 'bg-[#1A1A1A] group-hover:bg-[#262626]'
        )}>
          <Icon className={cn('w-4 h-4', isEmpty ? 'text-[#444444]' : 'text-[#888888]')} />
        </div>
      </CardHeader>
      <CardContent>
        <div className={cn('text-2xl font-bold font-mono', isEmpty ? 'text-[#444444]' : 'text-white')}>
          {value}
        </div>
        <div className='flex items-center gap-1 mt-1'>
          {changeType === 'positive' ? (
            <TrendingUp className='w-3 h-3 text-trade-green' />
          ) : changeType === 'negative' ? (
            <TrendingDown className='w-3 h-3 text-trade-red' />
          ) : null}
          <span
            className={cn(
              'text-xs font-medium',
              changeType === 'positive' && 'text-trade-green',
              changeType === 'negative' && 'text-trade-red',
              changeType === 'neutral' && (isEmpty ? 'text-[#555555]' : 'text-[#888888]')
            )}
          >
            {change}
          </span>
        </div>
        {isEmpty && emptyHint && (
          <p className='text-[10px] text-[#555555] mt-2 italic'>{emptyHint}</p>
        )}
      </CardContent>
    </Card>
  );
}

export function Dashboard() {
  const {
    portfolioValue,
    portfolioPnl,
    portfolioPnlPercent,
    dailyPnl,
    orders,
    agentsStatus,
    agentsCoherence,
    fetchPortfolio,
    fetchOrders,
    fetchAssets,
    fetchAgentsStatus,
  } = useAppStore();

  // Fetch data when the dashboard mounts
  useEffect(() => {
    fetchPortfolio();
    fetchOrders();
    fetchAssets();
    fetchAgentsStatus();
  }, [fetchPortfolio, fetchOrders, fetchAssets, fetchAgentsStatus]);

  // Auto-refresh market prices every 30 seconds
  useEffect(() => {
    const id = setInterval(() => fetchAssets(), 30_000);
    return () => clearInterval(id);
  }, [fetchAssets]);
  
  // Top Movers refresh every 60 seconds (1 minute)
  useEffect(() => {
    const id = setInterval(() => {
      fetchAssets(); // This updates topGainer/topLoser
    }, 60_000);
    return () => clearInterval(id);
  }, [fetchAssets]);

  const activeOrderCount = orders.filter((o) => o.status === 'open' || o.status === 'partial').length;
  const runningAgents = agentsStatus.filter((a) => a.status === 'running').length;

  const dailyPnlChange = dailyPnl !== 0
    ? `${dailyPnl >= 0 ? '+' : ''}$${Math.abs(dailyPnl).toLocaleString('en-US', { minimumFractionDigits: 2 })}`
    : '—';
  const dailyPnlType: 'positive' | 'negative' | 'neutral' =
    dailyPnl > 0 ? 'positive' : dailyPnl < 0 ? 'negative' : 'neutral';

  return (
    <div className='p-6 space-y-6'>
      <div
        className='flex items-center justify-between animate-fade-in opacity-0'
        style={{ animationFillMode: 'forwards' }}
      >
        <div>
          <h2 className='text-2xl font-bold text-white'>Welcome back, Trader</h2>
          <p className='text-muted-foreground mt-1'>Here's what's happening with your portfolio today</p>
        </div>
        <div className='flex items-center gap-3'>
          <Button
            variant='outline'
            className='border-[#262626] bg-transparent text-white hover:bg-[#1A1A1A] hover:border-[#333333]'
          >
            <Activity className='w-4 h-4 mr-2' />
            Analytics
          </Button>
          <Button className='bg-trade-blue hover:bg-trade-blue/90 text-white shadow-glow-blue'>
            <Zap className='w-4 h-4 mr-2' />
            Quick Trade
          </Button>
        </div>
      </div>

      <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4'>
        <StatCard
          title='Portfolio Value'
          value={portfolioValue > 0 ? `$${portfolioValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '$0.00'}
          change={
            portfolioPnl !== 0
              ? `${portfolioPnl >= 0 ? '+' : ''}$${Math.abs(portfolioPnl).toLocaleString('en-US', { minimumFractionDigits: 2 })} (${portfolioPnlPercent.toFixed(2)}%)`
              : 'No trades yet'
          }
          changeType={portfolioPnl >= 0 ? 'positive' : 'negative'}
          icon={DollarSign}
          delay={100}
          isEmpty={portfolioValue === 0}
          emptyHint="Fund your account to start trading"
        />
        <StatCard
          title='24h Profit / Loss'
          value={dailyPnl !== 0 ? dailyPnlChange : '$0.00'}
          change={dailyPnl !== 0 ? `${dailyPnlType === 'positive' ? '+' : ''}${(dailyPnl / Math.max(portfolioValue - dailyPnl, 1) * 100).toFixed(2)}%` : 'No trades today'}
          changeType={dailyPnlType}
          icon={TrendingUp}
          delay={150}
          isEmpty={dailyPnl === 0}
          emptyHint="Place your first trade to see P&L"
        />
        <StatCard
          title='Active Orders'
          value={activeOrderCount.toString()}
          change={activeOrderCount > 0 ? `${activeOrderCount} open` : 'No open orders'}
          changeType='neutral'
          icon={Activity}
          delay={200}
          isEmpty={activeOrderCount === 0}
          emptyHint="Use the order panel to place trades"
        />
        <StatCard
          title='AI Agent Status'
          value={runningAgents > 0 ? 'Active' : agentsStatus.length > 0 ? 'Paused' : '—'}
          change={`${runningAgents} agent${runningAgents !== 1 ? 's' : ''} running${agentsCoherence > 0 ? ` · ${(Math.min(agentsCoherence, 1) * 100).toFixed(0)}% coherence` : ''}`}
          changeType={runningAgents > 0 ? 'positive' : 'neutral'}
          icon={Bot}
          delay={250}
        />
      </div>

      <div className='grid grid-cols-1 lg:grid-cols-3 gap-6'>
        <div className='lg:col-span-2 space-y-6'>
          <TradingChart />
          <ActiveOrders />
          <TopMovers />
          <MarketOverview />
        </div>
        <div className='space-y-6'>
          <OrderPanel />
          <AIAdvisor />
          <AIAgentStatus />
          <RecentActivity />
        </div>
      </div>
    </div>
  );
}
