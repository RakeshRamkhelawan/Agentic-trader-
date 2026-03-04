/**
 * PaperPortfolioStats Component
 * 
 * Displays portfolio statistics with real-time updates.
 * Shows portfolio value, P&L, cash, and position count.
 */

import { DollarSign, TrendingUp, TrendingDown, Wallet, Package } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';
import usePaperTradingStore from '@/store/paper-trading';

interface StatCardProps {
  title: string;
  value: string;
  change?: string;
  changeType?: 'positive' | 'negative' | 'neutral';
  icon: React.ElementType;
  isLoading?: boolean;
}

function StatCard({ title, value, change, changeType, icon: Icon, isLoading }: StatCardProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-4 w-4" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-8 w-32 mb-2" data-testid="skeleton" />
          <Skeleton className="h-4 w-20" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {change && (
          <div className="flex items-center gap-1 mt-1">
            {changeType === 'positive' && <TrendingUp className="h-3 w-3 text-green-500" />}
            {changeType === 'negative' && <TrendingDown className="h-3 w-3 text-red-500" />}
            <span
              className={cn(
                'text-xs font-medium',
                changeType === 'positive' && 'text-green-500',
                changeType === 'negative' && 'text-red-500',
                changeType === 'neutral' && 'text-muted-foreground'
              )}
            >
              {change}
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export function PaperPortfolioStats() {
  const { portfolio, isLoading } = usePaperTradingStore();

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard title="Portfolio Value" value="" icon={DollarSign} isLoading />
        <StatCard title="P&L" value="" icon={TrendingUp} isLoading />
        <StatCard title="Cash" value="" icon={Wallet} isLoading />
        <StatCard title="Positions" value="" icon={Package} isLoading />
      </div>
    );
  }

  if (!portfolio) {
    return (
      <Card className="border-dashed">
        <CardContent className="flex flex-col items-center justify-center py-8">
          <Wallet className="h-12 w-12 text-muted-foreground mb-4" />
          <p className="text-lg font-medium">No portfolio data</p>
          <p className="text-sm text-muted-foreground">
            Start a trading session to see your portfolio
          </p>
        </CardContent>
      </Card>
    );
  }

  const pnlType: 'positive' | 'negative' | 'neutral' =
    portfolio.pnl > 0 ? 'positive' : portfolio.pnl < 0 ? 'negative' : 'neutral';

  const activePositions = Object.keys(portfolio.positions).length;

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <StatCard
        title="Portfolio Value"
        value={`€${portfolio.total_value.toLocaleString('en-US', {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        })}`}
        icon={DollarSign}
      />
      
      <StatCard
        title="P&L"
        value={`${portfolio.pnl >= 0 ? '+' : ''}€${Math.abs(portfolio.pnl).toLocaleString('en-US', {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        })}`}
        change={`${portfolio.pnl >= 0 ? '+' : ''}${portfolio.pnl_percent.toFixed(2)}%`}
        changeType={pnlType}
        icon={TrendingUp}
      />
      
      <StatCard
        title="Cash"
        value={`€${portfolio.cash.toLocaleString('en-US', {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        })}`}
        icon={Wallet}
      />
      
      <StatCard
        title="Active Positions"
        value={activePositions.toString()}
        icon={Package}
      />
    </div>
  );
}

export default PaperPortfolioStats;
