/**
 * PaperOrderPanel Component
 * 
 * Manual order placement interface for paper trading.
 * Allows users to place buy/sell orders manually.
 */

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  Loader2,
  AlertCircle,
} from 'lucide-react';
import { ordersApi } from '@/lib/api';
import usePaperTradingStore from '@/store/paper-trading';
import { toast } from 'sonner';

export function PaperOrderPanel() {
  const { isRunning, portfolio } = usePaperTradingStore();
  
  const [symbol, setSymbol] = useState('BTC/EUR');
  const [side, setSide] = useState<'buy' | 'sell'>('buy');
  const [type, setType] = useState<'market' | 'limit'>('market');
  const [amount, setAmount] = useState('');
  const [price, setPrice] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!isRunning) {
      toast.error('Start a paper trading session first');
      return;
    }

    setError(null);
    setIsSubmitting(true);

    try {
      const orderData = {
        symbol: symbol.toUpperCase(),
        side,
        type,
        amount: parseFloat(amount),
        ...(type === 'limit' && { price: parseFloat(price) }),
      };

      await ordersApi.createOrder(orderData);
      
      toast.success(`${side.toUpperCase()} order placed for ${symbol}`);
      
      // Reset form
      setAmount('');
      setPrice('');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to place order';
      setError(message);
      toast.error(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const buyingPower = portfolio?.buying_power || 0;
  const estimatedValue = side === 'buy' 
    ? parseFloat(amount || '0') * parseFloat(price || '50000')
    : parseFloat(amount || '0') * parseFloat(price || '50000');

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <DollarSign className="h-5 w-5" />
          Place Order
          {!isRunning && (
            <Badge variant="secondary" className="ml-auto">Session Required</Badge>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Symbol */}
          <div className="space-y-2">
            <Label htmlFor="symbol">Symbol</Label>
            <Input
              id="symbol"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value)}
              placeholder="BTC/EUR"
              disabled={!isRunning || isSubmitting}
            />
          </div>

          {/* Side Selection */}
          <div className="grid grid-cols-2 gap-2">
            <Button
              type="button"
              variant={side === 'buy' ? 'default' : 'outline'}
              onClick={() => setSide('buy')}
              disabled={!isRunning || isSubmitting}
              className="gap-2"
            >
              <TrendingUp className="h-4 w-4" />
              Buy
            </Button>
            <Button
              type="button"
              variant={side === 'sell' ? 'destructive' : 'outline'}
              onClick={() => setSide('sell')}
              disabled={!isRunning || isSubmitting}
              className="gap-2"
            >
              <TrendingDown className="h-4 w-4" />
              Sell
            </Button>
          </div>

          {/* Order Type */}
          <div className="space-y-2">
            <Label>Order Type</Label>
            <div className="flex gap-2">
              <Button
                type="button"
                variant={type === 'market' ? 'default' : 'outline'}
                onClick={() => setType('market')}
                disabled={!isRunning || isSubmitting}
                size="sm"
              >
                Market
              </Button>
              <Button
                type="button"
                variant={type === 'limit' ? 'default' : 'outline'}
                onClick={() => setType('limit')}
                disabled={!isRunning || isSubmitting}
                size="sm"
              >
                Limit
              </Button>
            </div>
          </div>

          {/* Amount */}
          <div className="space-y-2">
            <Label htmlFor="amount">Amount</Label>
            <Input
              id="amount"
              type="number"
              step="0.000001"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="0.1"
              disabled={!isRunning || isSubmitting}
            />
          </div>

          {/* Limit Price (only for limit orders) */}
          {type === 'limit' && (
            <div className="space-y-2">
              <Label htmlFor="price">Limit Price (€)</Label>
              <Input
                id="price"
                type="number"
                step="0.01"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                placeholder="50000"
                disabled={!isRunning || isSubmitting}
              />
            </div>
          )}

          {/* Summary */}
          {amount && (
            <div className="p-3 bg-muted rounded-md text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Estimated Value:</span>
                <span>€{estimatedValue.toLocaleString('en-US', { minimumFractionDigits: 2 })}</span>
              </div>
              <div className="flex justify-between mt-1">
                <span className="text-muted-foreground">Buying Power:</span>
                <span>€{buyingPower.toLocaleString('en-US', { minimumFractionDigits: 2 })}</span>
              </div>
            </div>
          )}

          {/* Submit */}
          <Button
            type="submit"
            disabled={!isRunning || isSubmitting || !amount}
            className="w-full gap-2"
          >
            {isSubmitting ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : side === 'buy' ? (
              <TrendingUp className="h-4 w-4" />
            ) : (
              <TrendingDown className="h-4 w-4" />
            )}
            {isSubmitting ? 'Placing Order...' : `${side.toUpperCase()} ${symbol}`}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

export default PaperOrderPanel;
