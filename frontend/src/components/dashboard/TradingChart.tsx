import { useState, useEffect, useRef, useCallback } from 'react';
import { Maximize2, Minimize2, Settings, Download, Loader2, ChevronDown } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAppStore } from '@/store/appStore';
import { marketsApi, wsClient } from '@/lib/api';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

const timeframes = ['1m', '5m', '15m', '1h', '4h', '1d', '1w'];

interface Candle {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
}

function drawChart(canvas: HTMLCanvasElement, candleData: Candle[]) {
  const ctx = canvas.getContext('2d');
  if (!ctx || candleData.length === 0) return;

  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();

  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  ctx.scale(dpr, dpr);

  const width = rect.width;
  const height = rect.height;
  const padding = { top: 20, right: 80, bottom: 40, left: 20 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  ctx.clearRect(0, 0, width, height);

  const prices = candleData.flatMap((d) => [d.high, d.low]);
  const minPrice = Math.min(...prices);
  const maxPrice = Math.max(...prices);
  const priceRange = maxPrice - minPrice || 1;

  ctx.strokeStyle = '#1A1A1A';
  ctx.lineWidth = 1;
  for (let i = 0; i <= 5; i++) {
    const y = padding.top + (chartHeight / 5) * i;
    ctx.beginPath();
    ctx.moveTo(padding.left, y);
    ctx.lineTo(width - padding.right, y);
    ctx.stroke();

    const price = maxPrice - (priceRange / 5) * i;
    ctx.fillStyle = '#666666';
    ctx.font = '11px JetBrains Mono, monospace';
    ctx.textAlign = 'left';
    ctx.fillText(price.toFixed(2), width - padding.right + 8, y + 4);
  }

  const candleWidth = (chartWidth / candleData.length) * 0.7;
  const candleSpacing = chartWidth / candleData.length;

  candleData.forEach((candle, i) => {
    const x = padding.left + i * candleSpacing + candleSpacing / 2;
    const openY = padding.top + ((maxPrice - candle.open) / priceRange) * chartHeight;
    const closeY = padding.top + ((maxPrice - candle.close) / priceRange) * chartHeight;
    const highY = padding.top + ((maxPrice - candle.high) / priceRange) * chartHeight;
    const lowY = padding.top + ((maxPrice - candle.low) / priceRange) * chartHeight;

    const isGreen = candle.close >= candle.open;
    ctx.fillStyle = isGreen ? '#00C087' : '#FF4976';
    ctx.strokeStyle = isGreen ? '#00C087' : '#FF4976';

    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(x, highY);
    ctx.lineTo(x, lowY);
    ctx.stroke();

    const bodyHeight = Math.max(Math.abs(closeY - openY), 1);
    const bodyY = Math.min(openY, closeY);
    ctx.fillRect(x - candleWidth / 2, bodyY, candleWidth, bodyHeight);
  });

  const lastPrice = candleData[candleData.length - 1].close;
  const lastY = padding.top + ((maxPrice - lastPrice) / priceRange) * chartHeight;
  ctx.strokeStyle = '#0075EB';
  ctx.lineWidth = 1;
  ctx.setLineDash([5, 5]);
  ctx.beginPath();
  ctx.moveTo(padding.left, lastY);
  ctx.lineTo(width - padding.right, lastY);
  ctx.stroke();
  ctx.setLineDash([]);

  ctx.fillStyle = '#0075EB';
  ctx.fillRect(width - padding.right, lastY - 10, 70, 20);
  ctx.fillStyle = '#FFFFFF';
  ctx.textAlign = 'center';
  ctx.fillText(lastPrice.toFixed(2), width - padding.right + 35, lastY + 4);
}

export function TradingChart() {
  const { chartSymbol, setChartSymbol, timeframe, setTimeframe, assets } = useAppStore();
  const selectedSymbol = chartSymbol;
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [candleData, setCandleData] = useState<Candle[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  
  // Group assets by provider
  const assetsByProvider = assets.reduce((acc, asset) => {
    const provider = (asset as any).exchange || 'Unknown';
    if (!acc[provider]) acc[provider] = [];
    acc[provider].push(asset);
    return acc;
  }, {} as Record<string, typeof assets>);
  
  const providers = Object.keys(assetsByProvider).sort();

  const loadCandles = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await marketsApi.getOHLCV(selectedSymbol, timeframe, 100);
      if (data.length > 0) {
        setCandleData(data);
      }
    } catch (error) {
      console.error('Failed to load candles:', error);
    } finally {
      setIsLoading(false);
    }
  }, [selectedSymbol, timeframe]);

  // Load candles when symbol or timeframe changes
  useEffect(() => {
    loadCandles();
  }, [loadCandles]);

  // Subscribe to WebSocket for real-time price updates
  useEffect(() => {
    const channel = `ticker.${selectedSymbol.replace('/', '-')}`;

    const handleMessage = (msg: any) => {
      if (msg.channel === channel && msg.data) {
        const price = Number(msg.data.price ?? 0);
        if (price <= 0) return;

        setCandleData((prev) => {
          if (prev.length === 0) return prev;
          const last = prev[prev.length - 1];
          const updated: Candle = {
            ...last,
            high: Math.max(last.high, price),
            low: Math.min(last.low, price),
            close: price,
          };
          return [...prev.slice(0, -1), updated];
        });
      }
    };

    // connect() is idempotent — only opens a socket if not already open
    wsClient.connect();
    const removeListener = wsClient.addListener(handleMessage);
    wsClient.subscribe(channel);
    return () => {
      removeListener();
      wsClient.unsubscribe(channel);
    };
  }, [selectedSymbol]);

  // Redraw chart whenever candle data changes
  useEffect(() => {
    if (canvasRef.current && candleData.length > 0) {
      drawChart(canvasRef.current, candleData);
    }
  }, [candleData]);

  const currentPrice = candleData.length > 0 ? candleData[candleData.length - 1].close : 0;
  
  // Get selected asset for consistent 24h change data
  const selectedAsset = assets.find(a => a.symbol === selectedSymbol);
  const priceChange = selectedAsset?.change24hValue ?? 0;
  const priceChangePercent = selectedAsset?.change24h ?? 0;

  return (
    <Card
      className={cn(
        'bg-[#111111] border-[#262626] overflow-hidden',
        isFullscreen && 'fixed inset-4 z-50'
      )}
    >
      <CardHeader className='pb-0'>
        <div className='flex items-center justify-between'>
          <div className='flex items-center gap-4'>
            <div>
              <div className='flex items-center gap-2'>
                {/* Symbol Selector Dropdown */}
                <Select value={selectedSymbol} onValueChange={setChartSymbol}>
                  <SelectTrigger className="w-[180px] bg-[#0A0A0A] border-[#262626] text-white hover:bg-[#1A1A1A] focus:ring-0 focus:ring-offset-0">
                    <SelectValue placeholder="Select symbol" />
                  </SelectTrigger>
                  <SelectContent className="bg-[#111111] border-[#262626] max-h-[400px]">
                    {providers.map((provider) => (
                      <SelectGroup key={provider}>
                        <SelectLabel className="text-muted-foreground text-xs uppercase tracking-wider px-2 py-1">
                          {provider}
                        </SelectLabel>
                        {assetsByProvider[provider]
                          .sort((a, b) => a.symbol.localeCompare(b.symbol))
                          .map((asset) => (
                            <SelectItem
                              key={asset.symbol}
                              value={asset.symbol}
                              className="text-white hover:bg-[#1A1A1A] focus:bg-[#1A1A1A] focus:text-white cursor-pointer"
                            >
                              <div className="flex items-center justify-between w-full gap-4">
                                <span>{asset.symbol}</span>
                                <span
                                  className={cn(
                                    'text-xs',
                                    asset.change24h >= 0 ? 'text-trade-green' : 'text-trade-red'
                                  )}
                                >
                                  {asset.change24h >= 0 ? '+' : ''}
                                  {asset.change24h.toFixed(2)}%
                                </span>
                              </div>
                            </SelectItem>
                          ))}
                      </SelectGroup>
                    ))}
                  </SelectContent>
                </Select>
                
                <span
                  className={cn(
                    'text-xs px-2 py-0.5 rounded-full border',
                    priceChange >= 0
                      ? 'bg-trade-green/10 text-trade-green border-trade-green/20'
                      : 'bg-trade-red/10 text-trade-red border-trade-red/20'
                  )}
                >
                  {priceChange >= 0 ? '+' : ''}{priceChangePercent.toFixed(2)}%
                </span>
              </div>
              <div className='flex items-center gap-2 mt-1'>
                {currentPrice > 0 ? (
                  <>
                    <span className='text-2xl font-bold text-white font-mono'>
                      {selectedSymbol.includes('EUR') 
                        ? `€${currentPrice.toLocaleString('de-DE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
                        : `$${currentPrice.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
                      }
                    </span>
                    <span className={cn('text-sm font-medium', priceChange >= 0 ? 'text-trade-green' : 'text-trade-red')}>
                      {priceChange >= 0 ? '+' : ''}
                      {selectedSymbol.includes('EUR') ? '€' : '$'}
                      {priceChange.toFixed(2)}
                    </span>
                  </>
                ) : (
                  <span className='text-2xl font-bold text-muted-foreground font-mono'>—</span>
                )}
              </div>
            </div>
          </div>

          <div className='flex items-center gap-2'>
            <div className='flex items-center gap-1 bg-[#0A0A0A] rounded-lg p-1'>
              {timeframes.map((tf) => (
                <button
                  key={tf}
                  onClick={() => setTimeframe(tf)}
                  className={cn(
                    'px-3 py-1 text-xs font-medium rounded-md transition-all duration-200',
                    timeframe === tf ? 'bg-[#1A1A1A] text-white' : 'text-muted-foreground hover:text-white'
                  )}
                >
                  {tf}
                </button>
              ))}
            </div>
            <Button
              variant='ghost'
              size='icon'
              className='h-8 w-8 text-muted-foreground hover:text-white hover:bg-[#1A1A1A]'
            >
              <Settings className='w-4 h-4' />
            </Button>
            <Button
              variant='ghost'
              size='icon'
              className='h-8 w-8 text-muted-foreground hover:text-white hover:bg-[#1A1A1A]'
            >
              <Download className='w-4 h-4' />
            </Button>
            <Button
              variant='ghost'
              size='icon'
              className='h-8 w-8 text-muted-foreground hover:text-white hover:bg-[#1A1A1A]'
              onClick={() => setIsFullscreen(!isFullscreen)}
            >
              {isFullscreen ? <Minimize2 className='w-4 h-4' /> : <Maximize2 className='w-4 h-4' />}
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className='pt-4'>
        <div className='relative h-[400px]'>
          {isLoading ? (
            <div className='absolute inset-0 flex items-center justify-center'>
              <Loader2 className='w-8 h-8 text-trade-blue animate-spin' />
            </div>
          ) : candleData.length === 0 ? (
            <div className='absolute inset-0 flex items-center justify-center text-muted-foreground'>
              <p className='text-sm'>No chart data available for {selectedSymbol}</p>
            </div>
          ) : null}
          <canvas
            ref={canvasRef}
            className='w-full h-full'
            style={{ width: '100%', height: '400px', display: candleData.length > 0 ? 'block' : 'none' }}
          />
        </div>
      </CardContent>
    </Card>
  );
}
