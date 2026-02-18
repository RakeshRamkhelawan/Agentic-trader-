import { TrendingUp, TrendingDown, ArrowRight } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAppStore } from '@/store/appStore';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

// Mini sparkline component
function Sparkline({ 
  data, 
  isPositive 
}: { 
  data: number[]; 
  isPositive: boolean;
}) {
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  
  const points = data.map((value, i) => {
    const x = (i / (data.length - 1)) * 100;
    const y = 100 - ((value - min) / range) * 100;
    return `${x},${y}`;
  }).join(' ');

  return (
    <svg viewBox="0 0 100 100" className="w-full h-12" preserveAspectRatio="none">
      <polyline
        points={points}
        fill="none"
        stroke={isPositive ? '#00C087' : '#FF4976'}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        className="opacity-60"
      />
      <defs>
        <linearGradient id={`gradient-${isPositive}`} x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor={isPositive ? '#00C087' : '#FF4976'} stopOpacity="0.2" />
          <stop offset="100%" stopColor={isPositive ? '#00C087' : '#FF4976'} stopOpacity="0" />
        </linearGradient>
      </defs>
      <polygon
        points={`0,100 ${points} 100,100`}
        fill={`url(#gradient-${isPositive})`}
      />
    </svg>
  );
}

function MarketCard({ 
  asset, 
  delay 
}: { 
  asset: { 
    symbol: string; 
    name: string; 
    price: number; 
    change24h: number;
    sparkline?: number[];
  }; 
  delay: number;
}) {
  const isPositive = asset.change24h >= 0;
  const { setSelectedSymbol } = useAppStore();

  return (
    <div 
      className={cn(
        'bg-[#0A0A0A] rounded-xl p-4 border border-[#1A1A1A]',
        'hover:border-[#333333] hover:bg-[#111111] transition-all duration-300',
        'cursor-pointer group animate-fade-in opacity-0'
      )}
      style={{ animationDelay: `${delay}ms`, animationFillMode: 'forwards' }}
      onClick={() => setSelectedSymbol(asset.symbol)}
    >
      <div className="flex items-start justify-between mb-2">
        <div>
          <h4 className="font-semibold text-white">{asset.symbol}</h4>
          <p className="text-xs text-muted-foreground">{asset.name}</p>
        </div>
        <div 
          className={cn(
            'flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium',
            isPositive 
              ? 'bg-trade-green/10 text-trade-green' 
              : 'bg-trade-red/10 text-trade-red'
          )}
        >
          {isPositive ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
          {isPositive ? '+' : ''}{asset.change24h.toFixed(2)}%
        </div>
      </div>

      <div className="mb-2">
        <span className="text-xl font-bold text-white font-mono">
          ${asset.price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </span>
      </div>

      {asset.sparkline && (
        <Sparkline data={asset.sparkline} isPositive={isPositive} />
      )}
    </div>
  );
}

export function MarketOverview() {
  const { assets } = useAppStore();

  return (
    <Card className="bg-[#111111] border-[#262626]">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-lg font-semibold text-white">Market Overview</CardTitle>
        <Button 
          variant="ghost" 
          size="sm" 
          className="text-trade-blue hover:text-trade-blue/80 hover:bg-trade-blue/10"
        >
          View All
          <ArrowRight className="w-4 h-4 ml-1" />
        </Button>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {assets.map((asset, index) => (
            <MarketCard 
              key={asset.symbol} 
              asset={asset} 
              delay={300 + index * 50}
            />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
