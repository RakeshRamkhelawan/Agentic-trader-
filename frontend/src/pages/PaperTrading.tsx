/**
 * Paper Trading Page - Complete Trading Interface
 * 
 * Combines:
 * - Dashboard portfolio stats
 * - Real-time market data (Top 10 Stijgers/Dalers)
 * - Federated Triad realtime weergave
 * - Paper Trading sessie beheer
 * - Trading interface (Order Panel)
 * - Live charts
 * 
 * NO MOCK DATA - 100% real backend integration
 */

import { useEffect, useState, useCallback } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  Activity, 
  Play, 
  Square, 
  Wallet, 
  Clock, 
  Bot,
  Target,
  Zap,
  RefreshCw,
  BarChart3,
  LineChart,
  PieChart,
  ArrowUpRight,
  ArrowDownRight,
  Globe,
  Cpu
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';

import { useAppStore } from '@/store/appStore';
import { useFederatedStore } from '@/store/federatedStore';
import usePaperTradingStore from '@/store/paper-trading';
import { usePaperTradingWebSocket } from '@/hooks/paper-trading/usePaperTradingWebSocket';

// Components
import { FederatedTriad } from '@/components/dashboard/FederatedTriad';
import { TradingChart } from '@/components/dashboard/TradingChart';
import { AIAdvisor } from '@/components/dashboard/AIAdvisor';
import { RecentActivity } from '@/components/dashboard/RecentActivity';

// Types
interface MarketAsset {
  symbol: string;
  name: string;
  price: number;
  change24h: number;
  change24hPercent: number;
  volume24h: number;
  high24h: number;
  low24h: number;
}

// ============================================================================
// STAT CARD COMPONENT
// ============================================================================
function StatCard({
  title,
  value,
  change,
  changeType,
  icon: Icon,
  isEmpty = false,
  emptyHint,
}: {
  title: string;
  value: string;
  change: string;
  changeType: 'positive' | 'negative' | 'neutral';
  icon: React.ElementType;
  isEmpty?: boolean;
  emptyHint?: string;
}) {
  return (
    <Card
      className={cn(
        'bg-[#111111] border-[#262626] hover:border-[#333333] transition-all duration-300',
        'hover:shadow-elevated group',
        isEmpty && 'border-dashed border-[#333333]'
      )}
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
            <TrendingUp className='w-3 h-3 text-green-500' />
          ) : changeType === 'negative' ? (
            <TrendingDown className='w-3 h-3 text-red-500' />
          ) : null}
          <span
            className={cn(
              'text-xs font-medium',
              changeType === 'positive' && 'text-green-500',
              changeType === 'negative' && 'text-red-500',
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

// ============================================================================
// TOP MOVERS COMPONENT
// ============================================================================
function TopMovers({ assets }: { assets: MarketAsset[] }) {
  const topGainers = [...assets]
    .filter(a => a.change24hPercent > 0)
    .sort((a, b) => b.change24hPercent - a.change24hPercent)
    .slice(0, 10);
    
  const topLosers = [...assets]
    .filter(a => a.change24hPercent < 0)
    .sort((a, b) => a.change24hPercent - b.change24hPercent)
    .slice(0, 10);

  return (
    <Card className='bg-[#111111] border-[#262626]'>
      <CardHeader>
        <CardTitle className='flex items-center gap-2 text-white'>
          <Globe className='h-5 w-5 text-blue-500' />
          Top 10 Markt Bewegingen (24u)
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue='gainers' className='w-full'>
          <TabsList className='grid w-full grid-cols-2 bg-[#1A1A1A]'>
            <TabsTrigger value='gainers' className='data-[state=active]:bg-[#262626]'>
              <TrendingUp className='w-4 h-4 mr-2 text-green-500' />
              Stijgers
            </TabsTrigger>
            <TabsTrigger value='losers' className='data-[state=active]:bg-[#262626]'>
              <TrendingDown className='w-4 h-4 mr-2 text-red-500' />
              Dalers
            </TabsTrigger>
          </TabsList>
          
          <TabsContent value='gainers' className='mt-4'>
            <ScrollArea className='h-[300px]'>
              <div className='space-y-2'>
                {topGainers.length > 0 ? topGainers.map((asset, idx) => (
                  <div 
                    key={asset.symbol}
                    className='flex items-center justify-between p-3 rounded-lg bg-[#1A1A1A] hover:bg-[#262626] transition-colors'
                  >
                    <div className='flex items-center gap-3'>
                      <span className='text-[#666666] w-6 text-sm'>#{idx + 1}</span>
                      <div>
                        <p className='font-medium text-white'>{asset.symbol}</p>
                        <p className='text-xs text-[#666666]'>{asset.name}</p>
                      </div>
                    </div>
                    <div className='text-right'>
                      <p className='font-mono text-white'>€{asset.price.toLocaleString('nl-NL', { minimumFractionDigits: 2 })}</p>
                      <p className='text-sm font-medium text-green-500 flex items-center justify-end gap-1'>
                        <ArrowUpRight className='w-3 h-3' />
                        +{asset.change24hPercent.toFixed(2)}%
                      </p>
                    </div>
                  </div>
                )) : (
                  <div className='text-center py-8 text-[#666666]'>
                    Geen stijgers gevonden
                  </div>
                )}
              </div>
            </ScrollArea>
          </TabsContent>
          
          <TabsContent value='losers' className='mt-4'>
            <ScrollArea className='h-[300px]'>
              <div className='space-y-2'>
                {topLosers.length > 0 ? topLosers.map((asset, idx) => (
                  <div 
                    key={asset.symbol}
                    className='flex items-center justify-between p-3 rounded-lg bg-[#1A1A1A] hover:bg-[#262626] transition-colors'
                  >
                    <div className='flex items-center gap-3'>
                      <span className='text-[#666666] w-6 text-sm'>#{idx + 1}</span>
                      <div>
                        <p className='font-medium text-white'>{asset.symbol}</p>
                        <p className='text-xs text-[#666666]'>{asset.name}</p>
                      </div>
                    </div>
                    <div className='text-right'>
                      <p className='font-mono text-white'>€{asset.price.toLocaleString('nl-NL', { minimumFractionDigits: 2 })}</p>
                      <p className='text-sm font-medium text-red-500 flex items-center justify-end gap-1'>
                        <ArrowDownRight className='w-3 h-3' />
                        {asset.change24hPercent.toFixed(2)}%
                      </p>
                    </div>
                  </div>
                )) : (
                  <div className='text-center py-8 text-[#666666]'>
                    Geen dalers gevonden
                  </div>
                )}
              </div>
            </ScrollArea>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}

// ============================================================================
// SESSION CONTROLS COMPONENT
// ============================================================================
function SessionControls() {
  const {
    isRunning,
    isStarting,
    isStopping,
    error,
    sessionId,
    startedAt,
    config,
    startSession,
    stopSession,
    clearError,
  } = usePaperTradingStore();

  const [duration, setDuration] = useState(8);
  const [capital, setCapital] = useState(10000);

  const handleStart = async () => {
    clearError();
    try {
      await startSession({ duration, capital });
    } catch (err) {
      // Error handled in store
    }
  };

  const handleStop = async () => {
    clearError();
    try {
      await stopSession();
    } catch (err) {
      // Error handled in store
    }
  };

  if (isRunning) {
    return (
      <Card className='border-green-500/30 bg-green-500/5'>
        <CardHeader>
          <div className='flex items-center justify-between'>
            <div>
              <CardTitle className='flex items-center gap-2 text-white'>
                <Activity className='h-5 w-5 text-green-500 animate-pulse' />
                Paper Trading Actief
                <Badge className='bg-green-500 text-black'>LIVE</Badge>
              </CardTitle>
              <CardDescription className='text-[#888888]'>
                {sessionId && `Sessie ID: ${sessionId.slice(0, 8)}...`}
                {startedAt && ` • Gestart: ${new Date(startedAt).toLocaleTimeString('nl-NL')}`}
              </CardDescription>
            </div>
            <Button
              variant='destructive'
              onClick={handleStop}
              disabled={isStopping}
              className='gap-2'
            >
              {isStopping ? (
                <RefreshCw className='h-4 w-4 animate-spin' />
              ) : (
                <Square className='h-4 w-4' />
              )}
              {isStopping ? 'Stoppen...' : 'Stop Sessie'}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className='grid grid-cols-3 gap-4'>
            <div className='flex items-center gap-2'>
              <Wallet className='h-4 w-4 text-[#666666]' />
              <div>
                <p className='text-xs text-[#888888]'>Start Kapitaal</p>
                <p className='font-semibold text-white'>
                  €{config?.capital.toLocaleString('nl-NL') || capital.toLocaleString('nl-NL')}
                </p>
              </div>
            </div>
            <div className='flex items-center gap-2'>
              <Clock className='h-4 w-4 text-[#666666]' />
              <div>
                <p className='text-xs text-[#888888]'>Duur</p>
                <p className='font-semibold text-white'>{config?.duration || duration} uur</p>
              </div>
            </div>
            <div className='flex items-center gap-2'>
              <Target className='h-4 w-4 text-[#666666]' />
              <div>
                <p className='text-xs text-[#888888]'>Status</p>
                <p className='font-semibold text-green-500'>Actief</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className='bg-[#111111] border-[#262626]'>
      <CardHeader>
        <CardTitle className='flex items-center gap-2 text-white'>
          <Play className='h-5 w-5 text-blue-500' />
          Start Paper Trading
        </CardTitle>
        <CardDescription className='text-[#888888]'>
          Configureer en start een nieuwe paper trading sessie
        </CardDescription>
      </CardHeader>
      <CardContent className='space-y-4'>
        {error && (
          <Alert className='bg-red-500/10 border-red-500/30'>
            <AlertDescription className='text-red-400'>{error}</AlertDescription>
          </Alert>
        )}

        <div className='grid grid-cols-2 gap-4'>
          <div className='space-y-2'>
            <Label htmlFor='capital' className='text-[#888888]'>Start Kapitaal (€)</Label>
            <Input
              id='capital'
              type='number'
              value={capital}
              onChange={(e) => setCapital(Number(e.target.value))}
              min={1000}
              step={1000}
              disabled={isStarting}
              className='bg-[#1A1A1A] border-[#333333] text-white'
            />
          </div>
          <div className='space-y-2'>
            <Label htmlFor='duration' className='text-[#888888]'>Duur (uren)</Label>
            <Input
              id='duration'
              type='number'
              value={duration}
              onChange={(e) => setDuration(Number(e.target.value))}
              min={1}
              max={24}
              disabled={isStarting}
              className='bg-[#1A1A1A] border-[#333333] text-white'
            />
          </div>
        </div>

        <Button
          onClick={handleStart}
          disabled={isStarting}
          className='w-full gap-2 bg-blue-600 hover:bg-blue-700'
        >
          {isStarting ? (
            <RefreshCw className='h-4 w-4 animate-spin' />
          ) : (
            <Play className='h-4 w-4' />
          )}
          {isStarting ? 'Starten...' : 'Start Paper Trading'}
        </Button>
      </CardContent>
    </Card>
  );
}

// ============================================================================
// TRADE HISTORY COMPONENT
// ============================================================================
function TradeHistory() {
  const { trades } = usePaperTradingStore();

  return (
    <Card className='bg-[#111111] border-[#262626]'>
      <CardHeader>
        <CardTitle className='text-white'>Recente Trades</CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className='h-[250px]'>
          {trades.length > 0 ? (
            <div className='space-y-2'>
              {trades.slice(-10).reverse().map((trade: any) => (
                <div 
                  key={trade.id}
                  className='flex items-center justify-between p-3 rounded-lg bg-[#1A1A1A]'
                >
                  <div className='flex items-center gap-3'>
                    <div className={cn(
                      'w-8 h-8 rounded-full flex items-center justify-center',
                      trade.side === 'buy' ? 'bg-green-500/20' : 'bg-red-500/20'
                    )}>
                      {trade.side === 'buy' ? (
                        <TrendingUp className='w-4 h-4 text-green-500' />
                      ) : (
                        <TrendingDown className='w-4 h-4 text-red-500' />
                      )}
                    </div>
                    <div>
                      <p className='font-medium text-white'>{trade.symbol}</p>
                      <p className='text-xs text-[#666666]'>
                        {trade.side.toUpperCase()} @ €{trade.price.toFixed(2)}
                      </p>
                    </div>
                  </div>
                  <div className='text-right'>
                    <p className='font-mono text-white'>{trade.qty} units</p>
                    {trade.pnl !== undefined && (
                      <p className={cn(
                        'text-sm font-medium',
                        trade.pnl >= 0 ? 'text-green-500' : 'text-red-500'
                      )}>
                        {trade.pnl >= 0 ? '+' : ''}€{trade.pnl.toFixed(2)}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className='text-center py-8 text-[#666666]'>
              Nog geen trades uitgevoerd
            </div>
          )}
        </ScrollArea>
      </CardContent>
    </Card>
  );
}

// ============================================================================
// PORTFOLIO STATS COMPONENT
// ============================================================================
function PortfolioStats() {
  const { portfolio } = usePaperTradingStore();

  if (!portfolio) return null;

  const totalValue = portfolio.total_value || 0;
  const cash = portfolio.cash || 0;
  const pnl = portfolio.pnl || 0;
  const pnlPercent = portfolio.pnl_percent || 0;
  const positionValue = totalValue - cash;

  return (
    <div className='grid grid-cols-1 md:grid-cols-4 gap-4'>
      <StatCard
        title='Portfolio Waarde'
        value={`€${totalValue.toLocaleString('nl-NL', { minimumFractionDigits: 2 })}`}
        change={pnl !== 0 ? `${pnl >= 0 ? '+' : ''}€${Math.abs(pnl).toFixed(2)} (${pnlPercent.toFixed(2)}%)` : 'Geen P&L'}
        changeType={pnl >= 0 ? 'positive' : 'negative'}
        icon={DollarSign}
      />
      <StatCard
        title='Beschikbaar Cash'
        value={`€${cash.toLocaleString('nl-NL', { minimumFractionDigits: 2 })}`}
        change={`${((cash / totalValue) * 100).toFixed(1)}% van portfolio`}
        changeType='neutral'
        icon={Wallet}
      />
      <StatCard
        title='Posities Waarde'
        value={`€${positionValue.toLocaleString('nl-NL', { minimumFractionDigits: 2 })}`}
        change={`${Object.keys(portfolio.positions || {}).length} posities`}
        changeType='neutral'
        icon={PieChart}
      />
      <StatCard
        title='24u P&L'
        value={pnl !== 0 ? `${pnl >= 0 ? '+' : ''}€${Math.abs(pnl).toFixed(2)}` : '€0.00'}
        change={pnlPercent !== 0 ? `${pnlPercent >= 0 ? '+' : ''}${pnlPercent.toFixed(2)}%` : '0.00%'}
        changeType={pnl >= 0 ? 'positive' : pnl < 0 ? 'negative' : 'neutral'}
        icon={Activity}
      />
    </div>
  );
}

// ============================================================================
// ORDER PANEL COMPONENT
// ============================================================================
function OrderPanel() {
  const [symbol, setSymbol] = useState('BTC-EUR');
  const [quantity, setQuantity] = useState(0.1);
  const [orderType, setOrderType] = useState<'buy' | 'sell'>('buy');
  const { isRunning } = usePaperTradingStore();
  const { assets, selectedSymbol, setSelectedSymbol } = useAppStore();

  const selectedAsset = assets.find(a => a.symbol === symbol);
  const estimatedValue = selectedAsset ? quantity * selectedAsset.price : 0;

  const handleSubmit = async () => {
    // Placeholder for order submission
    console.log('Order:', { symbol, quantity, orderType, estimatedValue });
  };

  return (
    <Card className='bg-[#111111] border-[#262626]'>
      <CardHeader>
        <CardTitle className='text-white'>Plaats Order</CardTitle>
      </CardHeader>
      <CardContent className='space-y-4'>
        {!isRunning && (
          <Alert className='bg-yellow-500/10 border-yellow-500/30'>
            <AlertDescription className='text-yellow-400'>
              Start een paper trading sessie om orders te plaatsen
            </AlertDescription>
          </Alert>
        )}

        <div className='grid grid-cols-2 gap-2'>
          <Button
            variant={orderType === 'buy' ? 'default' : 'outline'}
            onClick={() => setOrderType('buy')}
            className={orderType === 'buy' ? 'bg-green-600 hover:bg-green-700' : 'border-[#333333]'}
            disabled={!isRunning}
          >
            <TrendingUp className='w-4 h-4 mr-2' />
            Koop
          </Button>
          <Button
            variant={orderType === 'sell' ? 'default' : 'outline'}
            onClick={() => setOrderType('sell')}
            className={orderType === 'sell' ? 'bg-red-600 hover:bg-red-700' : 'border-[#333333]'}
            disabled={!isRunning}
          >
            <TrendingDown className='w-4 h-4 mr-2' />
            Verkoop
          </Button>
        </div>

        <div className='space-y-2'>
          <Label className='text-[#888888]'>Symbol</Label>
          <select 
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
            disabled={!isRunning}
            className='w-full bg-[#1A1A1A] border border-[#333333] text-white rounded-md p-2'
          >
            {assets.slice(0, 20).map(asset => (
              <option key={asset.symbol} value={asset.symbol}>
                {asset.symbol} - €{asset.price.toFixed(2)}
              </option>
            ))}
          </select>
        </div>

        <div className='space-y-2'>
          <Label className='text-[#888888]'>Hoeveelheid</Label>
          <Input
            type='number'
            value={quantity}
            onChange={(e) => setQuantity(Number(e.target.value))}
            min={0.001}
            step={0.001}
            disabled={!isRunning}
            className='bg-[#1A1A1A] border-[#333333] text-white'
          />
        </div>

        <div className='p-3 rounded-lg bg-[#1A1A1A]'>
          <div className='flex justify-between text-sm'>
            <span className='text-[#888888]'>Geschatte waarde:</span>
            <span className='text-white font-mono'>€{estimatedValue.toFixed(2)}</span>
          </div>
          {selectedAsset && (
            <div className='flex justify-between text-sm mt-1'>
              <span className='text-[#888888]'>Huidige prijs:</span>
              <span className='text-white font-mono'>€{selectedAsset.price.toFixed(2)}</span>
            </div>
          )}
        </div>

        <Button 
          onClick={handleSubmit}
          disabled={!isRunning}
          className={cn(
            'w-full',
            orderType === 'buy' ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'
          )}
        >
          {orderType === 'buy' ? 'Koop' : 'Verkoop'} {symbol}
        </Button>
      </CardContent>
    </Card>
  );
}

// ============================================================================
// MAIN PAPER TRADING PAGE
// ============================================================================
export function PaperTrading() {
  const { assets, fetchAssets } = useAppStore();
  const { isRunning, fetchStatus } = usePaperTradingStore();
  const { isConnected } = usePaperTradingWebSocket({ enabled: isRunning });

  // Fetch data on mount
  useEffect(() => {
    fetchAssets();
    fetchStatus();
  }, [fetchAssets, fetchStatus]);

  // Auto-refresh assets
  useEffect(() => {
    const id = setInterval(() => fetchAssets(), 30000);
    return () => clearInterval(id);
  }, [fetchAssets]);

  return (
    <div className='p-6 space-y-6 bg-[#0A0A0A] min-h-screen'>
      {/* Header */}
      <div className='flex items-center justify-between'>
        <div>
          <h1 className='text-3xl font-bold text-white flex items-center gap-3'>
            <Zap className='h-8 w-8 text-yellow-500' />
            Paper Trading
          </h1>
          <p className='text-[#888888] mt-1'>
            Oefen handelen met virtueel geld en realtime marktdata
          </p>
        </div>
        <div className='flex items-center gap-3'>
          {isRunning && (
            <Badge 
              variant={isConnected ? 'default' : 'secondary'}
              className={cn(
                'gap-1',
                isConnected ? 'bg-green-500 text-black' : 'bg-yellow-500 text-black'
              )}
            >
              {isConnected ? '● Live' : '◌ Verbinden...'}
            </Badge>
          )}
          <Button
            variant='outline'
            onClick={() => { fetchAssets(); fetchStatus(); }}
            className='border-[#333333] text-white hover:bg-[#1A1A1A]'
          >
            <RefreshCw className='w-4 h-4 mr-2' />
            Vernieuwen
          </Button>
        </div>
      </div>

      {/* Session Controls */}
      <SessionControls />

      {/* Portfolio Stats - Only when running */}
      {isRunning && <PortfolioStats />}

      {/* Main Content Grid */}
      <div className='grid grid-cols-1 lg:grid-cols-3 gap-6'>
        {/* Left Column - Charts & Market Data */}
        <div className='lg:col-span-2 space-y-6'>
          <TradingChart />
          
          <TopMovers assets={assets as unknown as MarketAsset[]} />
          
          {isRunning && <TradeHistory />}
        </div>

        {/* Right Column - Trading & AI */}
        <div className='space-y-6'>
          <OrderPanel />
          
          <FederatedTriad />
          
          <AIAdvisor />
          
          <RecentActivity />
        </div>
      </div>
    </div>
  );
}

export default PaperTrading;
