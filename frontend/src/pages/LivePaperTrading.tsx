import { LivePaperTrading } from '@/components/dashboard/LivePaperTrading';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Play, Square, Info } from 'lucide-react';
import { useState } from 'react';

export default function LivePaperTradingPage() {
  const [isRunning, setIsRunning] = useState(false);

  const startTrading = async () => {
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/v1/paper-trading/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ duration: 8, capital: 10000 })
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log('Trading session:', data);
        setIsRunning(true);
      }
    } catch (error) {
      console.error('Failed to start trading:', error);
      // For demo, still set running to true
      setIsRunning(true);
    }
  };

  const stopTrading = async () => {
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      await fetch(`${apiUrl}/api/v1/paper-trading/stop`, { method: 'POST' });
      setIsRunning(false);
    } catch (error) {
      console.error('Failed to stop trading:', error);
      setIsRunning(false);
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Live Paper Trading</h1>
          <p className="text-muted-foreground mt-1">
            Real-time trading simulation with live market data
          </p>
        </div>
        <div className="flex items-center gap-4">
          <Badge variant="outline" className="text-sm">
            <Info className="h-4 w-4 mr-1" />
            No real money involved
          </Badge>
          {!isRunning ? (
            <Button onClick={startTrading} className="gap-2">
              <Play className="h-4 w-4" />
              Start Session
            </Button>
          ) : (
            <Button onClick={stopTrading} variant="destructive" className="gap-2">
              <Square className="h-4 w-4" />
              Stop Session
            </Button>
          )}
        </div>
      </div>

      {/* Info Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>What is Paper Trading?</CardTitle>
          </CardHeader>
          <CardContent>
            <CardDescription>
              Paper trading allows you to practice trading with virtual money 
              using real market data. All trades are simulated but prices are 
              real-time from Bitvavo and Revolut X.
            </CardDescription>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Trading Agents</CardTitle>
          </CardHeader>
          <CardContent>
            <CardDescription>
              Our AI agents use different strategies: Momentum following, 
              Mean Reversion, and Breakout detection. Each agent makes 
              independent trading decisions based on market conditions.
            </CardDescription>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Live Data</CardTitle>
          </CardHeader>
          <CardContent>
            <CardDescription>
              All prices are fetched in real-time from connected exchanges. 
              Trades execute instantly at current market prices with zero 
              slippage simulation.
            </CardDescription>
          </CardContent>
        </Card>
      </div>

      {/* Live Trading Component */}
      <LivePaperTrading />
    </div>
  );
}
