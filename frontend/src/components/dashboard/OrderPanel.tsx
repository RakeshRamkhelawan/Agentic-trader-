import axios from 'axios';
import { useState } from 'react';
import { ArrowUpRight, ArrowDownRight, Wallet, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAppStore } from '@/store/appStore';
import { ordersApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { toast } from 'sonner';

const orderTypes = ['Market', 'Limit', 'Stop'];

export function OrderPanel() {
  const { selectedSymbol, assets, availableBalance, addOrder, fetchPortfolio, fetchOrders } = useAppStore();
  const [side, setSide] = useState<'buy' | 'sell'>('buy');
  const [orderType, setOrderType] = useState('Market');
  const [price, setPrice] = useState('');
  const [amount, setAmount] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const currentAsset = assets.find((a) => a.symbol === selectedSymbol);
  const currentPrice = currentAsset?.price || 0;

  const total =
    price && amount
      ? parseFloat(price) * parseFloat(amount)
      : orderType === 'Market' && amount
        ? currentPrice * parseFloat(amount)
        : 0;

  const handleSubmit = async () => {
    const parsedAmount = parseFloat(amount);
    if (!parsedAmount || parsedAmount <= 0) return;

    setIsSubmitting(true);
    try {
      const orderReq = {
        symbol: selectedSymbol,
        side,
        type: orderType.toLowerCase() as 'market' | 'limit',
        amount: parsedAmount,
        price: orderType !== 'Market' && price ? parseFloat(price) : undefined,
      };

      const newOrder = await ordersApi.createOrder(orderReq);
      addOrder(newOrder);
      toast.success(`${side === 'buy' ? 'Buy' : 'Sell'} order placed`, {
        description: `${parsedAmount} ${selectedSymbol.split('/')[0]} @ ${orderType === 'Market' ? 'market price' : `$${price}`}`,
      });
      setAmount('');
      setPrice('');

      // Refresh portfolio balance after order
      await Promise.allSettled([fetchPortfolio(), fetchOrders()]);
    } catch (error: unknown) {
      const msg = axios.isAxiosError(error) 
        ? error.response?.data?.detail ?? error.message 
        : error instanceof Error ? error.message : 'Order failed. Please try again.';
      toast.error('Order failed', { description: msg });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Quick amount helper: set percentage of available balance
  const handleQuickAmount = (pct: number) => {
    if (!currentPrice) return;
    const budget = availableBalance * pct;
    const qty = budget / currentPrice;
    setAmount(qty.toFixed(6));
    if (orderType !== 'Market') setPrice(currentPrice.toFixed(2));
  };

  return (
    <Card
      className='bg-[#111111] border-[#262626] animate-fade-in opacity-0'
      style={{ animationFillMode: 'forwards', animationDelay: '200ms' }}
    >
      <CardHeader className='pb-3'>
        <CardTitle className='text-lg font-semibold text-white'>Place Order</CardTitle>
      </CardHeader>
      <CardContent className='space-y-4'>
        {/* Buy/Sell Toggle */}
        <div className='grid grid-cols-2 gap-2'>
          <button
            onClick={() => setSide('buy')}
            className={cn(
              'flex items-center justify-center gap-2 py-3 rounded-xl font-semibold transition-all duration-200',
              side === 'buy'
                ? 'bg-trade-green text-white shadow-glow-green'
                : 'bg-[#0A0A0A] text-muted-foreground hover:text-white'
            )}
          >
            <ArrowUpRight className='w-4 h-4' />
            Buy
          </button>
          <button
            onClick={() => setSide('sell')}
            className={cn(
              'flex items-center justify-center gap-2 py-3 rounded-xl font-semibold transition-all duration-200',
              side === 'sell'
                ? 'bg-trade-red text-white shadow-glow-red'
                : 'bg-[#0A0A0A] text-muted-foreground hover:text-white'
            )}
          >
            <ArrowDownRight className='w-4 h-4' />
            Sell
          </button>
        </div>

        {/* Order Type */}
        <div className='flex items-center gap-2'>
          {orderTypes.map((type) => (
            <button
              key={type}
              onClick={() => setOrderType(type)}
              className={cn(
                'flex-1 py-2 text-sm font-medium rounded-lg transition-all duration-200',
                orderType === type ? 'bg-[#1A1A1A] text-white' : 'text-muted-foreground hover:text-white'
              )}
            >
              {type}
            </button>
          ))}
        </div>

        {/* Price Input (limit/stop) */}
        {orderType !== 'Market' && (
          <div className='space-y-2'>
            <Label className='text-sm text-muted-foreground'>Price (USD)</Label>
            <div className='relative'>
              <span className='absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground'>$</span>
              <Input
                type='number'
                placeholder='0.00'
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                className='pl-8 bg-[#0A0A0A] border-[#262626] text-white placeholder:text-muted-foreground focus:border-trade-blue'
              />
            </div>
          </div>
        )}

        {/* Amount Input */}
        <div className='space-y-2'>
          <Label className='text-sm text-muted-foreground'>Amount</Label>
          <div className='relative'>
            <Input
              type='number'
              placeholder='0.00'
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              className='bg-[#0A0A0A] border-[#262626] text-white placeholder:text-muted-foreground focus:border-trade-blue'
            />
            <span className='absolute right-3 top-1/2 -translate-y-1/2 text-xs text-muted-foreground'>
              {selectedSymbol.split('/')[0]}
            </span>
          </div>
        </div>

        {/* Quick Amount Buttons */}
        <div className='flex items-center gap-2'>
          {[0.25, 0.5, 0.75, 1].map((pct) => (
            <button
              key={pct}
              onClick={() => handleQuickAmount(pct)}
              className='flex-1 py-1.5 text-xs font-medium text-muted-foreground bg-[#0A0A0A] rounded-lg hover:bg-[#1A1A1A] hover:text-white transition-colors'
            >
              {(pct * 100).toFixed(0)}%
            </button>
          ))}
        </div>

        {/* Total */}
        <div className='pt-2 border-t border-[#262626]'>
          <div className='flex items-center justify-between'>
            <span className='text-sm text-muted-foreground'>Total</span>
            <span className='text-lg font-bold text-white font-mono'>
              {`$${total.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
            </span>
          </div>
        </div>

        {/* Submit Button */}
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                onClick={handleSubmit}
                disabled={!amount || parseFloat(amount) <= 0 || isSubmitting}
                className={cn(
                  'w-full py-6 font-semibold transition-all duration-200',
                  side === 'buy'
                    ? 'bg-trade-green hover:bg-trade-green/90 text-white shadow-glow-green disabled:opacity-50'
                    : 'bg-trade-red hover:bg-trade-red/90 text-white shadow-glow-red disabled:opacity-50'
                )}
              >
                {isSubmitting ? (
                  <span className='flex items-center gap-2'>
                    <Loader2 className='w-4 h-4 animate-spin' />
                    Processing...
                  </span>
                ) : (
                  <>
                    {side === 'buy' ? 'Buy' : 'Sell'} {selectedSymbol.split('/')[0]}
                  </>
                )}
              </Button>
            </TooltipTrigger>
            {(!amount || parseFloat(amount) <= 0) && (
              <TooltipContent side="bottom" className="bg-[#1A1A1A] border-[#333333] text-white">
                <p>Enter an amount to place an order</p>
              </TooltipContent>
            )}
          </Tooltip>
        </TooltipProvider>

        {/* Available Balance */}
        <div className='flex items-center justify-center gap-2 text-sm text-muted-foreground'>
          <Wallet className='w-4 h-4' />
          <span>
            Available:{' '}
            <span className='text-white font-mono'>
              {`$${availableBalance.toLocaleString('en-US', { minimumFractionDigits: 2 })}`}
            </span>
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
