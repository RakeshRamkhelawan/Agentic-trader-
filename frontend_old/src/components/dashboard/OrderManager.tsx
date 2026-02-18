import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useOrders } from '@/hooks/useOrders';
import { RefreshCw, History, ShieldAlert } from 'lucide-react';
import { apiClient } from '@/lib/api-client';
import { useQuery } from '@tanstack/react-query';
import { toast } from 'sonner';

export const OrderManager: React.FC = () => {
    const { activeOrders, isLoading: isLoadingActive, cancelAll, isCancelling } = useOrders();
    const [page, setPage] = useState(1);

    // Fetch Order History
    const { data: orderHistory, isLoading: isLoadingHistory, refetch: refetchHistory } = useQuery({
        queryKey: ['orderHistory', page],
        queryFn: async () => {
            return await apiClient.trading.getOrderHistoryApiV1TradingOrdersHistoryGet(50);
        }
    });

    const handleRefreshHistory = () => {
        refetchHistory();
        toast.info("Refreshed order history");
    };

    return (
        <Card className="w-full mt-6">
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <History className="h-5 w-5" />
                    Order Management
                </CardTitle>
                <CardDescription>View and manage your trading orders</CardDescription>
            </CardHeader>
            <CardContent>
                <Tabs defaultValue="active" className="w-full">
                    <TabsList className="grid w-full grid-cols-2 mb-4">
                        <TabsTrigger value="active">Active Orders ({activeOrders?.length || 0})</TabsTrigger>
                        <TabsTrigger value="history">Order History</TabsTrigger>
                    </TabsList>

                    <TabsContent value="active">
                        <div className="rounded-md border">
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>ID</TableHead>
                                        <TableHead>Symbol</TableHead>
                                        <TableHead>Side</TableHead>
                                        <TableHead>Qty</TableHead>
                                        <TableHead>Filled</TableHead>
                                        <TableHead>Status</TableHead>
                                        <TableHead className="text-right">Action</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {isLoadingActive ? (
                                        <TableRow>
                                            <TableCell colSpan={7} className="h-24 text-center">Loading active orders...</TableCell>
                                        </TableRow>
                                    ) : activeOrders && activeOrders.length > 0 ? (
                                        activeOrders.map((order: any) => (
                                            <TableRow key={order.order_id}>
                                                <TableCell className="font-mono text-xs">{order.order_id.substring(0, 8)}</TableCell>
                                                <TableCell className="font-bold">{order.symbol}</TableCell>
                                                <TableCell className={order.side === 'buy' ? 'text-green-500' : 'text-red-500'}>
                                                    {order.side.toUpperCase()}
                                                </TableCell>
                                                <TableCell>{order.quantity}</TableCell>
                                                <TableCell>{order.filled_qty}</TableCell>
                                                <TableCell>
                                                    <Badge variant={order.status === 'SUBMITTED' ? 'secondary' : 'outline'}>
                                                        {order.status}
                                                    </Badge>
                                                </TableCell>
                                                <TableCell className="text-right">
                                                    {/* Individual cancel not yet in hook, but UI ready */}
                                                    <Button variant="ghost" size="sm" disabled>Cancel</Button>
                                                </TableCell>
                                            </TableRow>
                                        ))
                                    ) : (
                                        <TableRow>
                                            <TableCell colSpan={7} className="h-24 text-center text-muted-foreground">
                                                No active orders
                                            </TableCell>
                                        </TableRow>
                                    )}
                                </TableBody>
                            </Table>
                        </div>
                    </TabsContent>

                    <TabsContent value="history">
                        <div className="flex justify-end mb-2">
                            <Button variant="outline" size="sm" onClick={handleRefreshHistory}>
                                <RefreshCw className="h-4 w-4 mr-2" />
                                Refresh
                            </Button>
                        </div>
                        <div className="rounded-md border">
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>ID</TableHead>
                                        <TableHead>Time</TableHead>
                                        <TableHead>Symbol</TableHead>
                                        <TableHead>Side</TableHead>
                                        <TableHead>Price</TableHead>
                                        <TableHead>Filled</TableHead>
                                        <TableHead>Status</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {isLoadingHistory ? (
                                        <TableRow>
                                            <TableCell colSpan={7} className="h-24 text-center">Loading history...</TableCell>
                                        </TableRow>
                                    ) : orderHistory && orderHistory.length > 0 ? (
                                        orderHistory.map((order: any) => (
                                            <TableRow key={order.order_id}>
                                                <TableCell className="font-mono text-xs text-muted-foreground">{order.order_id.substring(0, 8)}</TableCell>
                                                <TableCell className="text-xs">
                                                    {new Date(order.created_at).toLocaleString()}
                                                </TableCell>
                                                <TableCell className="font-bold">{order.symbol}</TableCell>
                                                <TableCell className={order.side === 'buy' ? 'text-green-500' : 'text-red-500'}>
                                                    {order.side.toUpperCase()}
                                                </TableCell>
                                                <TableCell>{order.avg_price || '-'}</TableCell>
                                                <TableCell>{order.filled_qty}/{order.quantity}</TableCell>
                                                <TableCell>
                                                    <Badge variant={
                                                        order.status === 'FILLED' ? 'default' :
                                                            order.status === 'CANCELLED' ? 'destructive' : 'secondary'
                                                    }>
                                                        {order.status}
                                                    </Badge>
                                                </TableCell>
                                            </TableRow>
                                        ))
                                    ) : (
                                        <TableRow>
                                            <TableCell colSpan={7} className="h-24 text-center text-muted-foreground">
                                                No order history found
                                            </TableCell>
                                        </TableRow>
                                    )}
                                </TableBody>
                            </Table>
                        </div>
                    </TabsContent>
                </Tabs>
            </CardContent>
        </Card>
    );
};
