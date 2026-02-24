import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { useAppStore } from '@/store/appStore';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

const TOP_N = 5;

interface MoverRowProps {
  rank: number;
  symbol: string;
  name: string;
  price: number;
  change24h: number;
  onSelect: (symbol: string) => void;
}

function MoverRow({ rank, symbol, name, price, change24h, exchange, onSelect }: MoverRowProps & { exchange?: string }) {
  const isPositive = change24h > 0;
  const isNeutral = change24h === 0;
  const isNegative = change24h < 0;
  
  // Format price with € for EUR pairs
  const priceDisplay = symbol.includes('EUR') 
    ? `€${price.toLocaleString('de-DE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
    : `$${price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  
  return (
    <button
      type="button"
      onClick={() => onSelect(symbol)}
      className={cn(
        'w-full flex items-center justify-between px-3 py-2 rounded-lg',
        'hover:bg-[#1A1A1A] transition-colors text-left'
      )}
    >
      <div className="flex items-center gap-3 min-w-0">
        <span className="text-xs text-muted-foreground w-4 shrink-0">{rank}</span>
        <div className="min-w-0">
          <p className="text-sm font-medium text-white truncate">{symbol}</p>
          <p className="text-xs text-muted-foreground truncate">
            {name}
            {exchange && <span className="ml-1 text-[10px] opacity-60">({exchange})</span>}
          </p>
        </div>
      </div>
      <div className="flex flex-col items-end shrink-0 ml-2">
        <span className="text-sm font-mono text-white">
          {priceDisplay}
        </span>
        <span
          className={cn(
            'text-xs font-medium flex items-center gap-0.5',
            isPositive && 'text-trade-green',
            isNeutral && 'text-muted-foreground',
            isNegative && 'text-trade-red'
          )}
        >
          {isPositive ? (
            <TrendingUp className="w-3 h-3" />
          ) : isNegative ? (
            <TrendingDown className="w-3 h-3" />
          ) : (
            <Minus className="w-3 h-3" />
          )}
          {isPositive ? '+' : ''}
          {change24h.toFixed(2)}%
        </span>
      </div>
    </button>
  );
}

export function TopMovers() {
  const { assets, setSelectedSymbol } = useAppStore();
  const navigate = useNavigate();

  if (assets.length === 0) return null;

  // Sort by change (descending)
  const sorted = [...assets].sort((a, b) => b.change24h - a.change24h);
  
  // Find actual gainers (positive change) and losers (negative change)
  const actualGainers = sorted.filter(a => a.change24h > 0);
  const actualLosers = sorted.filter(a => a.change24h < 0);
  
  // If we have actual gainers, show them. Otherwise show best performers (least negative)
  const gainersToShow = actualGainers.length > 0 
    ? actualGainers.slice(0, TOP_N)
    : sorted.slice(0, TOP_N);
    
  // If we have actual losers, show worst ones. Otherwise show worst from the list
  const losersToShow = actualLosers.length > 0
    ? actualLosers.slice(-TOP_N).reverse()
    : sorted.slice(-TOP_N).reverse();
  
  // Determine titles and colors based on actual market conditions
  const hasGainers = actualGainers.length > 0;
  const hasLosers = actualLosers.length > 0;
  
  // Titles
  const gainersTitle = hasGainers ? 'Top Gainers' : 'Best Performing';
  const losersTitle = hasLosers ? 'Worst Losers' : 'Weakest Assets';
  
  // Icon colors
  const gainersIconColor = hasGainers ? 'text-trade-green' : 'text-trade-orange';
  const losersIconColor = 'text-trade-red'; // Losers are always red
  
  // Card title colors
  const gainersTitleColor = hasGainers ? 'text-white' : 'text-trade-orange';

  const handleSelect = (symbol: string) => {
    setSelectedSymbol(symbol);
    navigate('/dashboard');
  };

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      {/* Gainers / Best Performing */}
      <Card className="bg-[#111111] border-[#262626]">
        <CardHeader className="pb-2">
          <CardTitle className={cn("text-sm font-semibold flex items-center gap-2", gainersTitleColor)}>
            <TrendingUp className={cn('w-4 h-4', gainersIconColor)} />
            {gainersTitle}
            {!hasGainers && <span className="text-[10px] font-normal text-muted-foreground ml-1">(all negative)</span>}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-0.5 px-3 pb-3">
          {gainersToShow.map((asset, i) => (
            <MoverRow
              key={asset.symbol}
              rank={i + 1}
              symbol={asset.symbol}
              name={asset.name}
              price={asset.price}
              change24h={asset.change24h}
              exchange={asset.exchange}
              onSelect={handleSelect}
            />
          ))}
        </CardContent>
      </Card>

      {/* Losers / Weakest */}
      <Card className="bg-[#111111] border-[#262626]">
        <CardHeader className="pb-2">
          <CardTitle className={cn("text-sm font-semibold flex items-center gap-2", hasLosers ? "text-white" : "text-muted-foreground")}>
            <TrendingDown className={cn('w-4 h-4', losersIconColor)} />
            {losersTitle}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-0.5 px-3 pb-3">
          {losersToShow.map((asset, i) => (
            <MoverRow
              key={asset.symbol}
              rank={i + 1}
              symbol={asset.symbol}
              name={asset.name}
              price={asset.price}
              change24h={asset.change24h}
              exchange={asset.exchange}
              onSelect={handleSelect}
            />
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
