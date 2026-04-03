/**
 * Bitvavo Connection Status Component
 *
 * Shows the connection status to Bitvavo API and account balance.
 * Helps users verify their Bitvavo setup before starting live trading.
 */

import { useEffect, useState } from 'react';
import { Zap, AlertCircle, CheckCircle, Wallet, RefreshCw } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { paperTradingApi, type BitvavoStatus } from '@/lib/api/paper-trading';

interface BitvavoConnectionStatusProps {
  className?: string;
}

export function BitvavoConnectionStatus({ className }: BitvavoConnectionStatusProps) {
  const [status, setStatus] = useState<BitvavoStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await paperTradingApi.getBitvavoStatus();
      setStatus(data);
    } catch (err) {
      setError('Failed to fetch Bitvavo status');
      console.error('Error fetching Bitvavo status:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    // Refresh every 30 seconds
    const interval = setInterval(fetchStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading && !status) {
    return (
      <Card className={cn('bg-[#111111] border-[#262626]', className)}>
        <CardContent className='p-6'>
          <div className='flex items-center justify-center'>
            <RefreshCw className='w-5 h-5 animate-spin text-[#666666]' />
            <span className='ml-2 text-[#888888]'>Checking Bitvavo connection...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={cn('bg-[#111111] border-[#262626]', className)}>
        <CardContent className='p-6'>
          <Alert className='bg-red-500/10 border-red-500/30'>
            <AlertDescription className='text-red-400'>{error}</AlertDescription>
          </Alert>
          <Button
            variant='outline'
            onClick={fetchStatus}
            className='mt-4 w-full border-[#333333]'
          >
            <RefreshCw className='w-4 h-4 mr-2' />
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (!status) return null;

  const hasCredentials = status.has_api_key && status.has_api_secret;
  const isConnected = status.connected;
  const canTrade = status.can_trade_live;

  return (
    <Card className={cn('bg-[#111111] border-[#262626]', className)}>
      <CardHeader className='pb-3'>
        <div className='flex items-center justify-between'>
          <CardTitle className='flex items-center gap-2 text-white text-base'>
            <Zap className='h-4 w-4 text-yellow-500' />
            Bitvavo Account
          </CardTitle>
          <Button
            variant='ghost'
            size='sm'
            onClick={fetchStatus}
            disabled={loading}
            className='h-8 w-8 p-0 text-[#666666] hover:text-white'
          >
            <RefreshCw className={cn('h-4 w-4', loading && 'animate-spin')} />
          </Button>
        </div>
      </CardHeader>
      <CardContent className='space-y-4'>
        {/* Connection Status */}
        <div className='flex items-center gap-3'>
          {isConnected ? (
            <>
              <CheckCircle className='h-5 w-5 text-green-500' />
              <div>
                <p className='text-green-400 font-medium'>Connected</p>
                <p className='text-xs text-[#666666]'>{status.message}</p>
              </div>
            </>
          ) : hasCredentials ? (
            <>
              <AlertCircle className='h-5 w-5 text-yellow-500' />
              <div>
                <p className='text-yellow-400 font-medium'>Connection Failed</p>
                <p className='text-xs text-[#666666]'>{status.message}</p>
              </div>
            </>
          ) : (
            <>
              <AlertCircle className='h-5 w-5 text-red-500' />
              <div>
                <p className='text-red-400 font-medium'>Not Configured</p>
                <p className='text-xs text-[#666666]'>API keys missing in .env</p>
              </div>
            </>
          )}
        </div>

        {/* Balance Info */}
        {isConnected && (
          <div className='grid grid-cols-2 gap-3'>
            <div className='bg-[#1A1A1A] rounded-lg p-3'>
              <div className='flex items-center gap-2 text-[#888888] text-xs mb-1'>
                <Wallet className='h-3 w-3' />
                Total Balance
              </div>
              <p className='text-white font-mono font-semibold'>
                €{status.balance_eur.toLocaleString('nl-NL', { minimumFractionDigits: 2 })}
              </p>
            </div>
            <div className='bg-[#1A1A1A] rounded-lg p-3'>
              <div className='flex items-center gap-2 text-[#888888] text-xs mb-1'>
                <Zap className='h-3 w-3' />
                Available
              </div>
              <p className={cn(
                'font-mono font-semibold',
                canTrade ? 'text-green-400' : 'text-yellow-400'
              )}>
                €{status.available_eur.toLocaleString('nl-NL', { minimumFractionDigits: 2 })}
              </p>
            </div>
          </div>
        )}

        {/* Live Trading Status */}
        {isConnected && (
          <div className='flex items-center justify-between pt-2 border-t border-[#262626]'>
            <span className='text-sm text-[#888888]'>Live Trading</span>
            {canTrade ? (
              <Badge className='bg-green-500/20 text-green-400 border-green-500/30'>
                <CheckCircle className='h-3 w-3 mr-1' />
                Ready (€5+ available)
              </Badge>
            ) : (
              <Badge className='bg-yellow-500/20 text-yellow-400 border-yellow-500/30'>
                <AlertCircle className='h-3 w-3 mr-1' />
                Insufficient funds (need €5+)
              </Badge>
            )}
          </div>
        )}

        {/* Setup Instructions */}
        {!hasCredentials && (
          <Alert className='bg-blue-500/10 border-blue-500/30 mt-2'>
            <AlertDescription className='text-blue-400 text-xs'>
              To enable live trading, add your Bitvavo API keys to the .env file:
              <code className='block mt-2 bg-[#0A0A0A] p-2 rounded'>
                BITVAVO_API_KEY=your_key_here<br />
                BITVAVO_API_SECRET=your_secret_here
              </code>
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
}
