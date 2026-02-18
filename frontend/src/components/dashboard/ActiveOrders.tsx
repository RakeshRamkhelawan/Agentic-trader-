import React from 'react';
import { X, Clock, CheckCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAppStore } from '@/store/appStore';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';

const statusColors: Record<string, string> = {
  open: 'bg-trade-blue/10 text-trade-blue border-trade-blue/20',
  filled: 'bg-trade-green/10 text-trade-green border-trade-green/20',
  cancelled: 'bg-muted/10 text-muted-foreground border-muted/20',
  partial: 'bg-trade-orange/10 text-trade-orange border-trade-orange/20',
};

const statusIcons: Record<string, React.ElementType> = {
  open: Clock,
  filled: CheckCircle,
  cancelled: X,
  partial: Clock,
};

export function ActiveOrders() {
  const { orders, cancelOrder } = useAppStore();

  const activeOrders = orders.filter(o => o.status === 'open' || o.status === 'partial');
  const recentOrders = orders.filter(o => o.status !== 'open' && o.status !== 'partial').slice(0, 5);

  return (
    <Card 
      className="bg-[#111111] border-[#262626] animate-fade-in opacity-0"
      style={{ animationFillMode: 'forwards', animationDelay: '300ms' }}
    >
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <div className="flex items-center gap-2">
          <CardTitle className="text-lg font-semibold text-white">Active Orders</CardTitle>
          <Badge 
            variant="outline" 
            className="bg-[#1A1A1A] text-muted-foreground border-[#262626]"
          >
            {activeOrders.length}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        {activeOrders.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <Clock className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p>No active orders</p>
            <p className="text-sm mt-1">Your open orders will appear here</p>
          </div>
        ) : (
          <ScrollArea className="h-[250px]">
            <div className="space-y-2">
              {activeOrders.map((order) => {
                const StatusIcon = statusIcons[order.status];
                return (
                  <div
                    key={order.id}
                    className={cn(
                      'flex items-center justify-between p-3 rounded-xl',
                      'bg-[#0A0A0A] border border-[#1A1A1A]',
                      'hover:border-[#333333] transition-all duration-200',
                      'group animate-fade-in'
                    )}
                  >
                    <div className="flex items-center gap-3">
                      <div 
                        className={cn(
                          'w-8 h-8 rounded-lg flex items-center justify-center',
                          order.side === 'buy' ? 'bg-trade-green/10' : 'bg-trade-red/10'
                        )}
                      >
                        <span 
                          className={cn(
                            'text-xs font-bold',
                            order.side === 'buy' ? 'text-trade-green' : 'text-trade-red'
                          )}
                        >
                          {order.side === 'buy' ? 'B' : 'S'}
                        </span>
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-white">{order.symbol}</span>
                          <Badge 
                            variant="outline" 
                            className={cn('text-xs', statusColors[order.status])}
                          >
                            <StatusIcon className="w-3 h-3 mr-1" />
                            {order.status}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                          <span>{order.type}</span>
                          <span>•</span>
                          <span className="font-mono">${order.price.toLocaleString()}</span>
                          <span>•</span>
                          <span className="font-mono">{order.amount}</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      <div className="text-right">
                        <p className="font-mono text-white">
                          ${(order.price * order.amount).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          Filled: {((order.filled / order.amount) * 100).toFixed(0)}%
                        </p>
                      </div>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => cancelOrder(order.id)}
                        className="h-8 w-8 text-muted-foreground hover:text-trade-red hover:bg-trade-red/10 opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        <X className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          </ScrollArea>
        )}

        {/* Recent Orders */}
        {recentOrders.length > 0 && (
          <div className="mt-4 pt-4 border-t border-[#262626]">
            <p className="text-sm text-muted-foreground mb-2">Recent</p>
            <div className="space-y-2">
              {recentOrders.map((order) => (
                <div
                  key={order.id}
                  className="flex items-center justify-between p-2 rounded-lg bg-[#0A0A0A]/50 text-sm"
                >
                  <div className="flex items-center gap-2">
                    <span 
                      className={cn(
                        'text-xs font-bold',
                        order.side === 'buy' ? 'text-trade-green' : 'text-trade-red'
                      )}
                    >
                      {order.side === 'buy' ? 'Bought' : 'Sold'}
                    </span>
                    <span className="text-muted-foreground">{order.symbol}</span>
                  </div>
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <span className="font-mono">{order.amount}</span>
                    <span>@</span>
                    <span className="font-mono">${order.price.toLocaleString()}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
