import { useState, useEffect } from 'react';
import { Search, TrendingUp, TrendingDown, Star, ArrowUpDown, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAppStore } from '@/store/appStore';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

const categories = ['All', 'Crypto', 'Stocks', 'Forex', 'Commodities'];

export function Markets() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [sortBy, setSortBy] = useState<'price' | 'change' | 'volume'>('volume');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const { assets, isLoadingAssets, fetchAssets, setSelectedSymbol } = useAppStore();

  useEffect(() => {
    fetchAssets();
  }, [fetchAssets]);

  const filteredAssets = assets
    .filter((asset) => {
      const matchesSearch =
        asset.symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
        asset.name.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesCategory =
        selectedCategory === 'All' ||
        (selectedCategory === 'Crypto' && asset.symbol.includes('/')) ||
        (selectedCategory === 'Stocks' && !asset.symbol.includes('/'));
      return matchesSearch && matchesCategory;
    })
    .sort((a, b) => {
      const multiplier = sortOrder === 'asc' ? 1 : -1;
      if (sortBy === 'price') return (a.price - b.price) * multiplier;
      if (sortBy === 'change') return (a.change24h - b.change24h) * multiplier;
      return (a.volume24h - b.volume24h) * multiplier;
    });

  const toggleSort = (field: 'price' | 'change' | 'volume') => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('desc');
    }
  };

  return (
    <div className='p-6 space-y-6'>
      <div className='flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4'>
        <div>
          <h2 className='text-2xl font-bold text-white'>Markets</h2>
          <p className='text-muted-foreground mt-1'>Explore and trade across global markets</p>
        </div>
        <div className='flex items-center gap-3'>
          <Button variant='outline' className='border-[#262626] bg-transparent text-white hover:bg-[#1A1A1A]'>
            <Star className='w-4 h-4 mr-2' />
            Watchlist
          </Button>
          <Button className='bg-trade-blue hover:bg-trade-blue/90 text-white'>
            <TrendingUp className='w-4 h-4 mr-2' />
            Trade
          </Button>
        </div>
      </div>

      <div className='flex flex-col sm:flex-row gap-4'>
        <div className='relative flex-1'>
          <Search className='absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground' />
          <Input
            placeholder='Search assets...'
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className='pl-10 bg-[#111111] border-[#262626] text-white'
          />
        </div>
        <div className='flex items-center gap-2 overflow-x-auto pb-2 sm:pb-0'>
          {categories.map((category) => (
            <button
              key={category}
              onClick={() => setSelectedCategory(category)}
              className={cn(
                'px-4 py-2 text-sm font-medium rounded-lg whitespace-nowrap transition-colors',
                selectedCategory === category
                  ? 'bg-[#1A1A1A] text-white'
                  : 'text-muted-foreground hover:text-white hover:bg-[#111111]'
              )}
            >
              {category}
            </button>
          ))}
        </div>
      </div>

      <Card className='bg-[#111111] border-[#262626] overflow-hidden'>
        <CardContent className='p-0'>
          {isLoadingAssets ? (
            <div className='flex items-center justify-center py-20'>
              <Loader2 className='w-8 h-8 text-trade-blue animate-spin' />
            </div>
          ) : filteredAssets.length === 0 ? (
            <div className='flex items-center justify-center py-20 text-muted-foreground'>
              <div className='text-center'>
                <TrendingUp className='w-12 h-12 mx-auto mb-3 opacity-30' />
                <p>{searchQuery ? 'No assets match your search' : 'No market data available'}</p>
              </div>
            </div>
          ) : (
            <div className='overflow-x-auto'>
              <table className='w-full'>
                <thead>
                  <tr className='border-b border-[#262626]'>
                    <th className='text-left py-4 px-6 text-sm font-medium text-muted-foreground'>Asset</th>
                    <th
                      className='text-right py-4 px-6 text-sm font-medium text-muted-foreground cursor-pointer hover:text-white'
                      onClick={() => toggleSort('price')}
                    >
                      <div className='flex items-center justify-end gap-1'>
                        Price <ArrowUpDown className='w-3 h-3' />
                      </div>
                    </th>
                    <th
                      className='text-right py-4 px-6 text-sm font-medium text-muted-foreground cursor-pointer hover:text-white'
                      onClick={() => toggleSort('change')}
                    >
                      <div className='flex items-center justify-end gap-1'>
                        24h Change <ArrowUpDown className='w-3 h-3' />
                      </div>
                    </th>
                    <th
                      className='text-right py-4 px-6 text-sm font-medium text-muted-foreground cursor-pointer hover:text-white'
                      onClick={() => toggleSort('volume')}
                    >
                      <div className='flex items-center justify-end gap-1'>
                        24h Volume <ArrowUpDown className='w-3 h-3' />
                      </div>
                    </th>
                    <th className='text-right py-4 px-6 text-sm font-medium text-muted-foreground'>Market Cap</th>
                    <th className='text-center py-4 px-6 text-sm font-medium text-muted-foreground'>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredAssets.map((asset, index) => {
                    const isPositive = asset.change24h >= 0;
                    return (
                      <tr
                        key={asset.symbol}
                        className={cn(
                          'border-b border-[#1A1A1A] hover:bg-[#1A1A1A] transition-colors cursor-pointer',
                          'animate-fade-in opacity-0'
                        )}
                        style={{ animationDelay: `${index * 50}ms`, animationFillMode: 'forwards' }}
                        onClick={() => setSelectedSymbol(asset.symbol)}
                      >
                        <td className='py-4 px-6'>
                          <div className='flex items-center gap-3'>
                            <div className='w-10 h-10 rounded-xl bg-[#1A1A1A] flex items-center justify-center'>
                              <span className='text-lg font-bold text-white'>{asset.symbol.charAt(0)}</span>
                            </div>
                            <div>
                              <p className='font-medium text-white'>{asset.symbol}</p>
                              <p className='text-sm text-muted-foreground'>{asset.name}</p>
                            </div>
                          </div>
                        </td>
                        <td className='py-4 px-6 text-right'>
                          <span className='font-mono text-white'>
                            {`$${asset.price.toLocaleString('en-US', { minimumFractionDigits: 2 })}`}
                          </span>
                        </td>
                        <td className='py-4 px-6 text-right'>
                          <div
                            className={cn(
                              'inline-flex items-center gap-1 px-2 py-1 rounded-full text-sm font-medium',
                              isPositive ? 'bg-trade-green/10 text-trade-green' : 'bg-trade-red/10 text-trade-red'
                            )}
                          >
                            {isPositive ? <TrendingUp className='w-3 h-3' /> : <TrendingDown className='w-3 h-3' />}
                            {isPositive ? '+' : ''}{asset.change24h.toFixed(2)}%
                          </div>
                        </td>
                        <td className='py-4 px-6 text-right'>
                          <span className='font-mono text-muted-foreground'>
                            {asset.volume24h >= 1e9
                              ? `$${(asset.volume24h / 1e9).toFixed(2)}B`
                              : asset.volume24h >= 1e6
                                ? `$${(asset.volume24h / 1e6).toFixed(2)}M`
                                : `$${asset.volume24h.toLocaleString()}`}
                          </span>
                        </td>
                        <td className='py-4 px-6 text-right'>
                          <span className='font-mono text-muted-foreground'>
                            {asset.marketCap
                              ? asset.marketCap >= 1e12
                                ? `$${(asset.marketCap / 1e12).toFixed(2)}T`
                                : asset.marketCap >= 1e9
                                  ? `$${(asset.marketCap / 1e9).toFixed(2)}B`
                                  : `$${asset.marketCap.toLocaleString()}`
                              : '—'}
                          </span>
                        </td>
                        <td className='py-4 px-6 text-center'>
                          <Button
                            size='sm'
                            variant='outline'
                            className='border-[#262626] bg-transparent text-white hover:bg-[#1A1A1A]'
                            onClick={(e) => { e.stopPropagation(); setSelectedSymbol(asset.symbol); }}
                          >
                            Trade
                          </Button>
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
