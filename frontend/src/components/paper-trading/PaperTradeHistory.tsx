/**
 * PaperTradeHistory Component
 * 
 * Displays a table of recent trades with real-time updates.
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { TrendingUp, TrendingDown, Activity } from 'lucide-react';
import { cn } from '@/lib/utils';
import usePaperTradingStore from '@/store/paper-trading';

export function PaperTradeHistory() {
  const { trades, isLoading } = usePaperTradingStore();

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-32" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-64 w-full" data-testid="skeleton" />
        </CardContent>
      </Card>
    );
  }

  if (trades.length === 0) {
    return (
      <Card className="border-dashed">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Recent Trades
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col items-center justify-center py-8">
          <p className="text-lg font-medium">No trades yet</p>
          <p className="text-sm text-muted-foreground">
            Start trading to see your trade history
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Activity className="h-5 w-5" />
          Recent Trades
          <Badge variant="secondary" className="ml-2">
            {trades.length}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Time</TableHead>
                <TableHead>Symbol</TableHead>
                <TableHead>Side</TableHead>
                <TableHead className="text-right">Qty</TableHead>
                <TableHead className="text-right">Price</TableHead>
                <TableHead className="text-right">Value</TableHead>
                <TableHead>Agent</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {trades.map((trade) => (
                <TableRow key={trade.id}>
                  <TableCell className="text-xs">
                    {new Date(trade.timestamp).toLocaleTimeString()}
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">{trade.symbol}</Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1">
                      {trade.side === 'buy' ? (
                        <TrendingUp className="h-4 w-4 text-green-500" />
                      ) : (
                        <TrendingDown className="h-4 w-4 text-red-500" />
                      )}
                      <Badge
                        variant={trade.side === 'buy' ? 'default' : 'destructive'}
                        className={cn(
                          'text-xs',
                          trade.side === 'buy' ? 'bg-green-500' : ''
                        )}
                      >
                        {trade.side.toUpperCase()}
                      </Badge>
                    </div>
                  </TableCell>
                  <TableCell className="text-right">
                    {trade.qty.toFixed(6)}
                  </TableCell>
                  <TableCell className="text-right">
                    €{trade.price.toLocaleString('en-US', {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2,
                    })}
                  </TableCell>
                  <TableCell className="text-right">
                    €{trade.value.toLocaleString('en-US', {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2,
                    })}
                  </TableCell>
                  <TableCell>
                    <Badge variant="secondary" className="text-xs">
                      {trade.agent}
                    </Badge>
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

export default PaperTradeHistory;
