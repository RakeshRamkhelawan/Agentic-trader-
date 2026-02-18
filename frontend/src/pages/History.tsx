import { useState, useEffect } from 'react';
import { Download, Calendar, ArrowUpRight, ArrowDownRight, Search, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAppStore } from '@/store/appStore';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

export function History() {
  const [searchQuery, setSearchQuery] = useState('');
  const [filter, setFilter] = useState<'all' | 'buy' | 'sell'>('all');
  const { tradeHistory, isLoadingHistory, fetchTradeHistory } = useAppStore();

  useEffect(() => {
    fetchTradeHistory();
  }, [fetchTradeHistory]);

  const filteredTrades = tradeHistory.filter((trade) => {
    const matchesSearch = trade.symbol.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesFilter = filter === 'all' || trade.side === filter;
    return matchesSearch && matchesFilter;
  });

  const totalVolume = filteredTrades.reduce((acc, t) => acc + t.total, 0);
  const totalTrades = filteredTrades.length;
  const buyTrades = filteredTrades.filter((t) => t.side === 'buy').length;
  const sellTrades = filteredTrades.filter((t) => t.side === 'sell').length;

  return (
    <div className='p-6 space-y-6'>
      <div className='flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4'>
        <div>
          <h2 className='text-2xl font-bold text-white'>Trade History</h2>
          <p className='text-muted-foreground mt-1'>View all your past trades and transactions</p>
        </div>
        <Button variant='outline' className='border-[#262626] bg-transparent text-white hover:bg-[#1A1A1A]'>
          <Download className='w-4 h-4 mr-2' />
          Export CSV
        </Button>
      </div>

      <div className='grid grid-cols-2 sm:grid-cols-4 gap-4'>
        {[
          { label: 'Total Trades', value: totalTrades.toString() },
          { label: 'Buy Orders', value: buyTrades.toString(), color: 'text-trade-green' },
          { label: 'Sell Orders', value: sellTrades.toString(), color: 'text-trade-red' },
          { label: 'Total Volume', value: `$${totalVolume.toLocaleString('en-US', { minimumFractionDigits: 2 })}` },
        ].map((stat, index) => (
          <Card
            key={stat.label}
            className='bg-[#111111] border-[#262626] animate-fade-in opacity-0'
            style={{ animationDelay: `${index * 50}ms`, animationFillMode: 'forwards' }}
          >
            <CardContent className='pt-6'>
              <p className='text-sm text-muted-foreground'>{stat.label}</p>
              <p className={cn('text-xl font-bold font-mono mt-1', stat.color || 'text-white')}>
                {stat.value}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className='flex flex-col sm:flex-row gap-4'>
        <div className='relative flex-1'>
          <Search className='absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground' />
          <Input
            placeholder='Search trades...'
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className='pl-10 bg-[#111111] border-[#262626] text-white'
          />
        </div>
        <div className='flex items-center gap-2'>
          {(['all', 'buy', 'sell'] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={cn(
                'px-4 py-2 text-sm font-medium rounded-lg transition-colors capitalize',
                filter === f ? 'bg-[#1A1A1A] text-white' : 'text-muted-foreground hover:text-white hover:bg-[#111111]'
              )}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      <Card className='bg-[#111111] border-[#262626] overflow-hidden'>
        <CardContent className='p-0'>
          {isLoadingHistory ? (
            <div className='flex items-center justify-center py-20'>
              <Loader2 className='w-8 h-8 text-trade-blue animate-spin' />
            </div>
          ) : filteredTrades.length === 0 ? (
            <div className='flex items-center justify-center py-20 text-muted-foreground'>
              <div className='text-center'>
                <Calendar className='w-12 h-12 mx-auto mb-3 opacity-30' />
                <p>{searchQuery ? 'No trades match your search' : 'No trade history available'}</p>
              </div>
            </div>
          ) : (
            <div className='overflow-x-auto'>
              <table className='w-full'>
                <thead>
                  <tr className='border-b border-[#262626]'>
                    <th className='text-left py-4 px-6 text-sm font-medium text-muted-foreground'>Date &amp; Time</th>
                    <th className='text-left py-4 px-6 text-sm font-medium text-muted-foreground'>Asset</th>
                    <th className='text-left py-4 px-6 text-sm font-medium text-muted-foreground'>Type</th>
                    <th className='text-right py-4 px-6 text-sm font-medium text-muted-foreground'>Price</th>
                    <th className='text-right py-4 px-6 text-sm font-medium text-muted-foreground'>Amount</th>
                    <th className='text-right py-4 px-6 text-sm font-medium text-muted-foreground'>Total</th>
                    <th className='text-center py-4 px-6 text-sm font-medium text-muted-foreground'>Side</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredTrades.map((trade, index) => {
                    const ts = new Date(trade.timestamp);
                    return (
                      <tr
                        key={trade.id}
                        className='border-b border-[#1A1A1A] hover:bg-[#1A1A1A] transition-colors animate-fade-in opacity-0'
                        style={{ animationDelay: `${200 + index * 50}ms`, animationFillMode: 'forwards' }}
                      >
                        <td className='py-4 px-6'>
                          <div className='flex items-center gap-2'>
                            <Calendar className='w-4 h-4 text-muted-foreground' />
                            <span className='text-sm text-white'>{ts.toLocaleDateString()}</span>
                            <span className='text-sm text-muted-foreground'>
                              {ts.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </span>
                          </div>
                        </td>
                        <td className='py-4 px-6'>
                          <span className='font-medium text-white'>{trade.symbol}</span>
                        </td>
                        <td className='py-4 px-6'>
                          <span className='text-xs px-2 py-1 rounded-full bg-[#1A1A1A] text-muted-foreground border border-[#262626] capitalize'>
                            {trade.type ?? 'market'}
                          </span>
                        </td>
                        <td className='py-4 px-6 text-right'>
                          <span className='font-mono text-white'>
                            {`$${trade.price.toLocaleString('en-US', { minimumFractionDigits: 2 })}`}
                          </span>
                        </td>
                        <td className='py-4 px-6 text-right'>
                          <span className='font-mono text-white'>{trade.amount}</span>
                        </td>
                        <td className='py-4 px-6 text-right'>
                          <span className='font-mono text-white'>
                            {`$${trade.total.toLocaleString('en-US', { minimumFractionDigits: 2 })}`}
                          </span>
                        </td>
                        <td className='py-4 px-6 text-center'>
                          <div
                            className={cn(
                              'inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium',
                              trade.side === 'buy'
                                ? 'bg-trade-green/10 text-trade-green'
                                : 'bg-trade-red/10 text-trade-red'
                            )}
                          >
                            {trade.side === 'buy' ? (
                              <ArrowUpRight className='w-3 h-3' />
                            ) : (
                              <ArrowDownRight className='w-3 h-3' />
                            )}
                            {trade.side.toUpperCase()}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
