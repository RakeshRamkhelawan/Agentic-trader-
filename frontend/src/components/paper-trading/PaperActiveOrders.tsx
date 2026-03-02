/**
 * PaperActiveOrders Component
 * 
 * Displays active (open/pending) orders for paper trading.
 */

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { XCircle, Clock, AlertCircle } from 'lucide-react';
import { ordersApi, type Order } from '@/lib/api';
import usePaperTradingStore from '@/store/paper-trading';
import { toast } from 'sonner';

export function PaperActiveOrders() {
  const { isRunning } = usePaperTradingStore();
  const [orders, setOrders] = useState<Order[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [cancellingId, setCancellingId] = useState<string | null>(null);

  const fetchOrders = async () => {
    if (!isRunning) {
      setOrders([]);
      return;
    }

    setIsLoading(true);
    try {
      const activeOrders = await ordersApi.getOrders();
      setOrders(activeOrders.filter(o => o.status === 'open' || o.status === 'partial'));
    } catch (err) {
      console.error('Failed to fetch orders:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancel = async (orderId: string) => {
    setCancellingId(orderId);
    try {
      await ordersApi.cancelOrder(orderId);
      toast.success('Order cancelled');
      await fetchOrders();
    } catch (err) {
      toast.error('Failed to cancel order');
    } finally {
      setCancellingId(null);
    }
  };

  useEffect(() => {
    fetchOrders();
    const interval = setInterval(fetchOrders, 5000);
    return () => clearInterval(interval);
  }, [isRunning]);

  if (isLoading && orders.length === 0) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-32" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-48 w-full" />
        </CardContent>
      </Card>
    );
  }

  if (!isRunning) {
    return (
      <Card className="border-dashed">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Active Orders
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col items-center justify-center py-8">
          <AlertCircle className="h-12 w-12 text-muted-foreground mb-4" />
          <p className="text-lg font-medium">No Active Session</p>
          <p className="text-sm text-muted-foreground">
            Start a paper trading session to see active orders
          </p>
        </CardContent>
      </Card>
    );
  }

  if (orders.length === 0) {
    return (
      <Card className="border-dashed">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Active Orders
            <Badge variant="secondary" className="ml-2">0</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col items-center justify-center py-8">
          <p className="text-lg font-medium">No Active Orders</p>
          <p className="text-sm text-muted-foreground">
            All orders have been filled or cancelled
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Clock className="h-5 w-5" />
          Active Orders
          <Badge variant="secondary" className="ml-2">{orders.length}</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Symbol</TableHead>
                <TableHead>Side</TableHead>
                <TableHead>Type</TableHead>
                <TableHead className="text-right">Amount</TableHead>
                <TableHead className="text-right">Price</TableHead>
                <TableHead className="text-right">Filled</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {orders.map((order) => (
                <TableRow key={order.id}>
                  <TableCell>
                    <Badge variant="outline">{order.symbol}</Badge>
                  </TableCell>
                  <TableCell>
                    <Badge 
                      variant={order.side === 'buy' ? 'default' : 'destructive'}
                      className={order.side === 'buy' ? 'bg-green-500' : ''}
                    >
                      {order.side.toUpperCase()}
                    </Badge>
                  </TableCell>
                  <TableCell className="capitalize">{order.type}</TableCell>
                  <TableCell className="text-right">
                    {order.amount.toFixed(6)}
                  </TableCell>
                  <TableCell className="text-right">
                    €{order.price.toLocaleString('en-US', { 
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2,
                    })}
                  </TableCell>
                  <TableCell className="text-right">
                    {((order.filled / order.amount) * 100).toFixed(0)}%
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleCancel(order.id)}
                      disabled={cancellingId === order.id}
                    >
                      {cancellingId === order.id ? (
                        <span className="text-xs">...</span>
                      ) : (
                        <XCircle className="h-4 w-4" />
                      )}
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}

export default PaperActiveOrders;
