/**
 * Paper Trading Page - Dashboard Equivalent
 * 
 * A complete rebuild of the paper trading page with:
 * - Real-time data from WebSocket
 * - Portfolio statistics
 * - Trade history
 * - Session controls
 * 
 * NO MOCK DATA - 100% backend integration
 */

import { useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Wifi, WifiOff } from 'lucide-react';
import {
  PaperPortfolioStats,
  PaperTradeHistory,
  PaperSessionControls,
} from '@/components/paper-trading';
import usePaperTradingStore from '@/store/paper-trading';
import { usePaperTradingWebSocket } from '@/hooks/paper-trading/usePaperTradingWebSocket';

export default function PaperTradingPage() {
  const { isRunning, lastUpdated, fetchStatus } = usePaperTradingStore();

  // WebSocket for real-time updates
  const { isConnected } = usePaperTradingWebSocket({
    enabled: isRunning,
  });

  // Fetch status on mount
  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  const isDataFresh = lastUpdated 
    ? new Date().getTime() - new Date(lastUpdated).getTime() < 10000 
    : false;

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Paper Trading</h1>
          <p className="text-muted-foreground mt-1">
            Practice trading with virtual money using real market data
          </p>
        </div>
        {isRunning && (
          <Badge 
            variant={isConnected && isDataFresh ? 'default' : 'secondary'}
            className="gap-1"
          >
            {isConnected && isDataFresh ? (
              <Wifi className="h-3 w-3" />
            ) : (
              <WifiOff className="h-3 w-3" />
            )}
            {isConnected && isDataFresh ? 'Live' : 'Connecting...'}
          </Badge>
        )}
      </div>

      {/* Session Controls */}
      <PaperSessionControls />

      {/* Portfolio Stats - Only show when session is running */}
      {isRunning && (
        <>
          <PaperPortfolioStats />
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <PaperTradeHistory />
            
            {/* Placeholder for future components */}
            <Card className="border-dashed">
              <CardHeader>
                <CardTitle>Coming Soon</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">
                  More features will be added in upcoming updates:
                </p>
                <ul className="list-disc list-inside mt-2 text-sm text-muted-foreground">
                  <li>Trading Chart with real-time prices</li>
                  <li>Manual Order Placement</li>
                  <li>Active Orders Management</li>
                  <li>AI Advisor Integration</li>
                  <li>Agent Status Monitor</li>
                </ul>
              </CardContent>
            </Card>
          </div>
        </>
      )}

      {/* Info Cards - Show when no session running */}
      {!isRunning && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardHeader>
              <CardTitle>What is Paper Trading?</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Paper trading allows you to practice trading with virtual money 
                using real market data. All trades are simulated but prices are 
                real-time from connected exchanges.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Trading Agents</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Our AI agents use different strategies: Momentum following, 
                Mean Reversion, and Breakout detection. Each agent makes 
                independent trading decisions based on market conditions.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Live Data</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                All prices are fetched in real-time from connected exchanges. 
                Trades execute instantly at current market prices with zero 
                slippage simulation.
              </p>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

export { PaperTradingPage };
