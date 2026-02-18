import { useState } from 'react';
import { TrendingUp, PieChart as PieChartIcon, DollarSign, Download } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAppStore } from '@/store/appStore';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

// Simple pie chart component
function AllocationPieChart({ data }: { data: { label: string; value: number; color: string }[] }) {
  const total = data.reduce((acc, item) => acc + item.value, 0);
  let currentAngle = 0;

  return (
    <svg viewBox="0 0 100 100" className="w-48 h-48">
      {data.map((item, index) => {
        const angle = (item.value / total) * 360;
        const startAngle = currentAngle;
        const endAngle = currentAngle + angle;
        currentAngle += angle;

        const startRad = (startAngle * Math.PI) / 180;
        const endRad = (endAngle * Math.PI) / 180;

        const x1 = 50 + 40 * Math.cos(startRad);
        const y1 = 50 + 40 * Math.sin(startRad);
        const x2 = 50 + 40 * Math.cos(endRad);
        const y2 = 50 + 40 * Math.sin(endRad);

        const largeArc = angle > 180 ? 1 : 0;

        return (
          <path
            key={index}
            d={`M 50 50 L ${x1} ${y1} A 40 40 0 ${largeArc} 1 ${x2} ${y2} Z`}
            fill={item.color}
            stroke="#111111"
            strokeWidth="2"
            className="hover:opacity-80 transition-opacity cursor-pointer"
          />
        );
      })}
      <circle cx="50" cy="50" r="25" fill="#111111" />
    </svg>
  );
}

export function Portfolio() {
  const { holdings, portfolioValue, portfolioPnl, portfolioPnlPercent } = useAppStore();
  const [timeRange, setTimeRange] = useState('1W');

  const timeRanges = ['1D', '1W', '1M', '3M', '1Y', 'ALL'];

  const allocationData = holdings.map((h, i) => ({
    label: h.symbol,
    value: h.value,
    color: ['#0075EB', '#00C087', '#8B5CF6', '#FF9500', '#FF4976'][i % 5],
  }));

  const stats = [
    { label: 'Total Value', value: `$${portfolioValue.toLocaleString('en-US', { minimumFractionDigits: 2 })}`, change: `+${portfolioPnlPercent.toFixed(2)}%`, positive: true },
    { label: 'Total P&L', value: `$${portfolioPnl.toLocaleString('en-US', { minimumFractionDigits: 2 })}`, change: '+$3,847.18', positive: true },
    { label: 'Day P&L', value: '+$456.78', change: '+1.23%', positive: true },
    { label: 'Best Performer', value: 'SOL/USD', change: '+19.28%', positive: true },
  ];

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white">Portfolio</h2>
          <p className="text-muted-foreground mt-1">Track your investments and performance</p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" className="border-[#262626] bg-transparent text-white hover:bg-[#1A1A1A]">
            <Download className="w-4 h-4 mr-2" />
            Export CSV
          </Button>
          <Button className="bg-trade-blue hover:bg-trade-blue/90 text-white">
            <DollarSign className="w-4 h-4 mr-2" />
            Deposit
          </Button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {stats.map((stat, index) => (
          <Card 
            key={stat.label}
            className="bg-[#111111] border-[#262626] animate-fade-in opacity-0"
            style={{ animationDelay: `${index * 50}ms`, animationFillMode: 'forwards' }}
          >
            <CardContent className="pt-6">
              <p className="text-sm text-muted-foreground">{stat.label}</p>
              <p className={cn('text-xl font-bold font-mono mt-1', stat.positive ? 'text-white' : 'text-trade-red')}>
                {stat.value}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Allocation Chart */}
        <Card className="bg-[#111111] border-[#262626] lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-lg font-semibold text-white flex items-center gap-2">
              <PieChartIcon className="w-5 h-5 text-trade-purple" />
              Asset Allocation
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col items-center">
              <AllocationPieChart data={allocationData} />
              <div className="w-full mt-6 space-y-2">
                {allocationData.map((item) => (
                  <div key={item.label} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div 
                        className="w-3 h-3 rounded-full" 
                        style={{ backgroundColor: item.color }}
                      />
                      <span className="text-sm text-white">{item.label}</span>
                    </div>
                    <span className="text-sm text-muted-foreground font-mono">
                      {((item.value / portfolioValue) * 100).toFixed(1)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Holdings Table */}
        <Card className="bg-[#111111] border-[#262626] lg:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-lg font-semibold text-white">Your Holdings</CardTitle>
            <div className="flex items-center gap-2">
              {timeRanges.map((range) => (
                <button
                  key={range}
                  onClick={() => setTimeRange(range)}
                  className={cn(
                    'px-3 py-1 text-xs font-medium rounded-lg transition-colors',
                    timeRange === range
                      ? 'bg-[#1A1A1A] text-white'
                      : 'text-muted-foreground hover:text-white'
                  )}
                >
                  {range}
                </button>
              ))}
            </div>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-[#262626]">
                    <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">Asset</th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">Amount</th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">Avg Price</th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">Current</th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">Value</th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">P&L</th>
                  </tr>
                </thead>
                <tbody>
                  {holdings.map((holding, index) => {
                    const isPositive = holding.pnl >= 0;
                    return (
                      <tr
                        key={holding.symbol}
                        className="border-b border-[#1A1A1A] hover:bg-[#1A1A1A] transition-colors animate-fade-in opacity-0"
                        style={{ animationDelay: `${200 + index * 50}ms`, animationFillMode: 'forwards' }}
                      >
                        <td className="py-4 px-4">
                          <div>
                            <p className="font-medium text-white">{holding.symbol}</p>
                            <p className="text-sm text-muted-foreground">{holding.name}</p>
                          </div>
                        </td>
                        <td className="py-4 px-4 text-right">
                          <span className="font-mono text-white">{holding.amount}</span>
                        </td>
                        <td className="py-4 px-4 text-right">
                          <span className="font-mono text-muted-foreground">
                            ${holding.avgPrice.toLocaleString()}
                          </span>
                        </td>
                        <td className="py-4 px-4 text-right">
                          <span className="font-mono text-white">
                            ${holding.currentPrice.toLocaleString()}
                          </span>
                        </td>
                        <td className="py-4 px-4 text-right">
                          <span className="font-mono text-white">
                            ${holding.value.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                          </span>
                        </td>
                        <td className="py-4 px-4 text-right">
                          <div className={cn(
                            'inline-flex flex-col items-end',
                            isPositive ? 'text-trade-green' : 'text-trade-red'
                          )}>
                            <span className="font-mono font-medium">
                              {isPositive ? '+' : ''}${holding.pnl.toFixed(2)}
                            </span>
                            <span className="text-xs">
                              {isPositive ? '+' : ''}{holding.pnlPercent.toFixed(2)}%
                            </span>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Performance Chart Placeholder */}
      <Card className="bg-[#111111] border-[#262626]">
        <CardHeader>
          <CardTitle className="text-lg font-semibold text-white">Performance History</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center bg-[#0A0A0A] rounded-xl">
            <div className="text-center text-muted-foreground">
              <TrendingUp className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p>Performance chart coming soon</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
