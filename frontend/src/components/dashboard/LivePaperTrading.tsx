import { useState, useEffect, useRef } from 'react';
import { API_URL, WS_URL } from '@/lib/config';

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

import { Alert, AlertDescription } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Play,
  Square,
  TrendingUp,
  TrendingDown,
  Wallet,
  Activity,
  Brain,
  Network,
  AlertCircle,
  Wifi,
  WifiOff,
} from 'lucide-react';
import { AgentDecisions } from './AgentDecisions';
import { FederatedTriad } from './FederatedTriad';
import { VedicContextPanel } from './VedicContextPanel';

interface Trade {
  timestamp: string;
  symbol: string;
  side: 'buy' | 'sell';
  qty: number;
  price: number;
  value: number;
  agent: string;
  exchange: string;
}

interface Portfolio {
  cash: number;
  positions: Record<string, { qty: number; avg_price: number; value: number }>;
  total_value: number;
  pnl: number;
  pnl_pct: number;
}

interface Stats {
  total_trades: number;
  buy_trades: number;
  sell_trades: number;
  avg_trade_value: number;
  uptime_seconds: number;
}

export function LivePaperTrading() {

  const [isRunning, setIsRunning] = useState(false);
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [wsConnected, setWsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const hasShownConnectedRef = useRef(false);

  const getWsUrl = () => {
    const baseUrl = WS_URL.replace(/\/$/, '');
    const result = baseUrl.includes('/ws') ? `${baseUrl}/paper-trading` : `${baseUrl}/ws/paper-trading`;
    console.log('[DEBUG] WS_URL:', WS_URL, '-> Result:', result);
    return result;
  };

  useEffect(() => {
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  useEffect(() => {
    if (!isRunning) return;

    const connectWS = () => {
      const wsUrl = getWsUrl();
      console.log('Connecting to WebSocket:', wsUrl);
      
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected');
        setWsConnected(true);
        setError(null);
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          console.log('WebSocket message:', message.type);

          switch (message.type) {
            case 'trade':
              setTrades((prev) => [message.data, ...prev].slice(0, 50));
              break;
            case 'portfolio':
              setPortfolio(message.data);
              break;
            case 'stats':
              setStats(message.data);
              break;
            case 'connected':
              console.log('WebSocket connection confirmed');
              break;
            case 'soul_update':
            case 'prana_update':
            case 'harmony_update':
            case 'cosmic_block':
              // Vedic context messages - handled by VedicContextPanel
              break;
          }
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      ws.onclose = () => {
        console.log('WebSocket closed');
        setWsConnected(false);
        reconnectTimeoutRef.current = setTimeout(connectWS, 3000);
      };

      ws.onerror = (err) => {
        console.error('WebSocket error:', err);
        setWsConnected(false);
      };
    };

    connectWS();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [isRunning]);

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const res = await fetch(`${API_URL}/api/v1/paper-trading/status`);
        const data = await res.json();
        
        // If already running, show message (only once)
        if (data.is_running && !hasShownConnectedRef.current) {
          console.log('[INFO] Active session found! Joining existing session...');
          setError('Connected to existing 8-hour session (started at ' + new Date().toLocaleTimeString() + ')');
          setTimeout(() => setError(null), 5000); // Clear after 5s
          hasShownConnectedRef.current = true;
        }
        
        setIsRunning(data.is_running);
        
        // Use portfolio positions to generate trades if no trades available
        if (data.portfolio?.positions && trades.length === 0) {
          const positionTrades: Trade[] = [];
          Object.entries(data.portfolio.positions).forEach(([symbol, pos]: [string, any]) => {
            if (pos.quantity > 0) {
              positionTrades.push({
                timestamp: pos.entry_date || new Date().toISOString(),
                symbol: symbol,
                side: 'buy',
                qty: pos.quantity,
                price: pos.entry_price,
                value: pos.position_size || (pos.quantity * pos.entry_price),
                agent: 'V18_Elemental',
                exchange: 'Bitvavo'
              });
            }
          });
          // Sort by timestamp descending
          positionTrades.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
          if (positionTrades.length > 0) {
            setTrades(positionTrades.slice(0, 50));
          }
        }
        
        // Use trades from API if available
        if (data.trades && Array.isArray(data.trades) && data.trades.length > 0) {
          setTrades(data.trades.slice(0, 50));
        }
        
        // Use stats from API or calculate from data
        const totalTrades = data.total_trades || data.stats?.total_trades || trades.length || 0;
        const buyTrades = trades.filter((t: Trade) => t.side === 'buy').length;
        const sellTrades = trades.filter((t: Trade) => t.side === 'sell').length;
        
        setStats({
          total_trades: totalTrades,
          buy_trades: buyTrades,
          sell_trades: sellTrades,
          avg_trade_value: data.stats?.avg_trade_value || 0,
          uptime_seconds: data.stats?.uptime_seconds || 0
        });
        
        // Update portfolio if available
        if (data.portfolio) {
          setPortfolio({
            cash: data.portfolio.cash || data.cash || 0,
            total_value: data.portfolio.total_value || data.current_value || 0,
            pnl: data.portfolio.pnl || data.pnl || 0,
            pnl_pct: data.pnl_percent || 0,
            positions: data.portfolio.positions || {}
          });
        }
        
        if (!data.is_running) {
          setWsConnected(false);
        }
      } catch (err) {
        console.error('Status check failed:', err);
      }
    };

    checkStatus();
    const interval = setInterval(checkStatus, 3000);
    return () => clearInterval(interval);
  }, [API_URL]);

  const startSession = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/api/v1/paper-trading/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ duration: 8, capital: 10000 }),
      });
      const data = await res.json();
      if (data.status === 'started') {
        setIsRunning(true);
        setTrades([]);
      } else {
        setError(data.detail || 'Failed to start');
      }
    } catch {
      setError('Failed to connect to server');
    } finally {
      setLoading(false);
    }
  };

  const stopSession = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/v1/paper-trading/stop`, {
        method: 'POST',
      });
      const data = await res.json();
      if (data.status === 'stopped') {
        setIsRunning(false);
        setWsConnected(false);
        if (wsRef.current) {
          wsRef.current.close();
        }
      }
    } catch {
      setError('Failed to stop session');
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (seconds: number) => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    return `${hrs}h ${mins}m`;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-2xl">Live Paper Trading</CardTitle>
              <CardDescription>
                €10,000 budget • 8 hours • 400+ assets • 5 agents
              </CardDescription>
            </div>
            <div className="flex items-center gap-4">
              {isRunning && (
                <Badge variant={wsConnected ? 'default' : 'secondary'} className="gap-1">
                  {wsConnected ? <Wifi className="h-3 w-3" /> : <WifiOff className="h-3 w-3" />}
                  {wsConnected ? 'Live' : 'Connecting...'}
                </Badge>
              )}
              <Button
                variant={isRunning ? 'destructive' : 'default'}
                onClick={isRunning ? stopSession : startSession}
                disabled={loading}
                className="gap-2"
              >
                {loading ? (
                  <Skeleton className="h-4 w-4" />
                ) : isRunning ? (
                  <Square className="h-4 w-4" />
                ) : (
                  <Play className="h-4 w-4" />
                )}
                {isRunning ? 'Stop' : 'Start'}
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {error && (
            <Alert variant="destructive" className="mb-4">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Stats Row */}
          {isRunning && stats && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
              <Card>
                <CardHeader className="p-4">
                  <CardDescription>Total Trades</CardDescription>
                  <CardTitle className="text-2xl">{stats.total_trades}</CardTitle>
                </CardHeader>
              </Card>
              <Card>
                <CardHeader className="p-4">
                  <CardDescription>Buy/Sell</CardDescription>
                  <CardTitle className="text-2xl">
                    <span className="text-green-500">{stats.buy_trades}</span>
                    <span className="mx-1">/</span>
                    <span className="text-red-500">{stats.sell_trades}</span>
                  </CardTitle>
                </CardHeader>
              </Card>
              <Card>
                <CardHeader className="p-4">
                  <CardDescription>Avg Trade</CardDescription>
                  <CardTitle className="text-2xl">€{stats.avg_trade_value?.toFixed(0) || 0}</CardTitle>
                </CardHeader>
              </Card>
              <Card>
                <CardHeader className="p-4">
                  <CardDescription>Uptime</CardDescription>
                  <CardTitle className="text-2xl">{formatTime(stats.uptime_seconds || 0)}</CardTitle>
                </CardHeader>
              </Card>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Portfolio Overview */}
      {isRunning && portfolio && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Wallet className="h-5 w-5" />
              Portfolio
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              <div>
                <p className="text-sm text-muted-foreground">Cash</p>
                <p className="text-2xl font-bold">€{portfolio.cash?.toFixed(2) || '0.00'}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Total Value</p>
                <p className="text-2xl font-bold">€{portfolio.total_value?.toFixed(2) || '0.00'}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">P&L</p>
                <p className={`text-2xl font-bold ${(portfolio.pnl || 0) >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                  {(portfolio.pnl || 0) >= 0 ? '+' : ''}€{portfolio.pnl?.toFixed(2) || '0.00'}
                  <span className="text-sm ml-1">
                    ({(portfolio.pnl_pct || 0) >= 0 ? '+' : ''}{portfolio.pnl_pct?.toFixed(2) || '0.00'}%)
                  </span>
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Positions</p>
                <p className="text-2xl font-bold">{Object.keys(portfolio.positions || {}).length} assets</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Vedic Context Panel - Always visible when running */}
      {isRunning && (
        <VedicContextPanel wsUrl={getWsUrl()} isRunning={isRunning} />
      )}

      {/* Tabs */}
      <Tabs defaultValue="trades" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="trades" className="gap-2">
            <Activity className="h-4 w-4" />
            Live Trades
          </TabsTrigger>
          <TabsTrigger value="decisions" className="gap-2">
            <Brain className="h-4 w-4" />
            Agent Decisions
          </TabsTrigger>
          <TabsTrigger value="triad" className="gap-2">
            <Network className="h-4 w-4" />
            Federated Triad
          </TabsTrigger>
        </TabsList>

        {/* Live Trades Tab */}
        <TabsContent value="trades">
          <Card>
            <CardHeader>
              <CardTitle>Recent Trades</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Time</TableHead>
                      <TableHead>Symbol</TableHead>
                      <TableHead>Side</TableHead>
                      <TableHead className="text-right">Qty</TableHead>
                      <TableHead className="text-right">Price</TableHead>
                      <TableHead className="text-right">Value</TableHead>
                      <TableHead>Agent</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {trades.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                          {isRunning ? 'Waiting for trades...' : 'Start trading to see live trades'}
                        </TableCell>
                      </TableRow>
                    ) : (
                      trades.map((trade, idx) => (
                        <TableRow key={idx}>
                          <TableCell className="text-xs">
                            {trade.timestamp ? new Date(trade.timestamp).toLocaleTimeString() : '--:--:--'}
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline">{trade.symbol || 'N/A'}</Badge>
                          </TableCell>
                          <TableCell>
                            <Badge 
                              variant={trade.side === 'buy' ? 'default' : 'destructive'}
                              className="gap-1"
                            >
                              {trade.side === 'buy' ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                              {(trade.side || 'unknown').toUpperCase()}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-right">{trade.qty?.toFixed(6) || '0.000000'}</TableCell>
                          <TableCell className="text-right">€{trade.price?.toFixed(2) || '0.00'}</TableCell>
                          <TableCell className="text-right">€{trade.value?.toFixed(2) || '0.00'}</TableCell>
                          <TableCell>
                            <Badge variant="secondary">{trade.agent || 'Unknown'}</Badge>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Agent Decisions Tab */}
        <TabsContent value="decisions">
          {isRunning && <AgentDecisions wsUrl={getWsUrl()} />}
        </TabsContent>

        {/* Federated Triad Tab */}
        <TabsContent value="triad">
          {isRunning && <FederatedTriad wsUrl={getWsUrl()} />}
        </TabsContent>
      </Tabs>
    </div>
  );
}
