import {
  ArrowUpRight,
  Bot,
  Bell,
  Settings,
  Clock,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAppStore } from '@/store/appStore';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';

const typeIcons: Record<string, React.ElementType> = {
  trade: ArrowUpRight,
  agent: Bot,
  alert: Bell,
  system: Settings,
};

const typeColors: Record<string, string> = {
  trade: 'bg-trade-blue/10 text-trade-blue',
  agent: 'bg-trade-purple/10 text-trade-purple',
  alert: 'bg-trade-orange/10 text-trade-orange',
  system: 'bg-muted/10 text-muted-foreground',
};

function formatTimeAgo(date: Date): string {
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000);
  if (seconds < 60) return 'Just now';
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}

export function RecentActivity() {
  const { tradeHistory, orders } = useAppStore();

  // Build activity list from real trade history and recent orders
  const activities = [
    ...tradeHistory.slice(0, 4).map((t) => ({
      id: `trade-${t.id}`,
      type: 'trade',
      title: t.side === 'buy' ? 'Buy Order Filled' : 'Sell Order Filled',
      description: `${t.amount} ${t.symbol} @ $${t.price.toLocaleString()}`,
      timestamp: new Date(t.timestamp),
      value: t.side === 'buy' ? `+$${t.total.toFixed(2)}` : `-$${t.total.toFixed(2)}`,
      valueType: t.side === 'buy' ? 'positive' : 'negative',
    })),
    ...orders.slice(0, 3).map((o) => ({
      id: `order-${o.id}`,
      type: 'trade',
      title: `${o.side === 'buy' ? 'Buy' : 'Sell'} Order ${o.status}`,
      description: `${o.amount} ${o.symbol} @ $${o.price.toLocaleString()}`,
      timestamp: new Date(o.createdAt),
      value: undefined,
      valueType: undefined,
    })),
  ]
    .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
    .slice(0, 8);

  return (
    <Card
      className='bg-[#111111] border-[#262626] animate-fade-in opacity-0'
      style={{ animationFillMode: 'forwards', animationDelay: '400ms' }}
    >
      <CardHeader className='pb-3'>
        <div className='flex items-center justify-between'>
          <CardTitle className='text-lg font-semibold text-white'>Recent Activity</CardTitle>
          <div className='w-8 h-8 rounded-lg bg-[#1A1A1A] flex items-center justify-center'>
            <Clock className='w-4 h-4 text-muted-foreground' />
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {activities.length === 0 ? (
          <div className='flex items-center justify-center py-8 text-muted-foreground'>
            <div className='text-center'>
              <Clock className='w-10 h-10 mx-auto mb-2 opacity-30' />
              <p className='text-sm'>No recent activity</p>
            </div>
          </div>
        ) : (
          <ScrollArea className='h-[300px]'>
            <div className='space-y-3'>
              {activities.map((activity, index) => {
                const Icon = typeIcons[activity.type] ?? ArrowUpRight;
                return (
                  <div
                    key={activity.id}
                    className={cn(
                      'flex items-start gap-3 p-3 rounded-xl',
                      'bg-[#0A0A0A] hover:bg-[#1A1A1A] transition-colors duration-200',
                      'group cursor-pointer',
                      'animate-fade-in opacity-0'
                    )}
                    style={{ animationDelay: `${450 + index * 50}ms`, animationFillMode: 'forwards' }}
                  >
                    <div
                      className={cn(
                        'w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0',
                        typeColors[activity.type] ?? typeColors.system
                      )}
                    >
                      <Icon className='w-4 h-4' />
                    </div>

                    <div className='flex-1 min-w-0'>
                      <div className='flex items-start justify-between gap-2'>
                        <div>
                          <p className='text-sm font-medium text-white'>{activity.title}</p>
                          <p className='text-xs text-muted-foreground mt-0.5 line-clamp-2'>
                            {activity.description}
                          </p>
                        </div>
                        {activity.value && (
                          <span
                            className={cn(
                              'text-sm font-mono font-medium whitespace-nowrap',
                              activity.valueType === 'positive' && 'text-trade-green',
                              activity.valueType === 'negative' && 'text-trade-red',
                              activity.valueType === 'neutral' && 'text-muted-foreground'
                            )}
                          >
                            {activity.value}
                          </span>
                        )}
                      </div>
                      <p className='text-xs text-muted-foreground mt-1'>
                        {formatTimeAgo(activity.timestamp)}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </ScrollArea>
        )}
      </CardContent>
    </Card>
  );
}
