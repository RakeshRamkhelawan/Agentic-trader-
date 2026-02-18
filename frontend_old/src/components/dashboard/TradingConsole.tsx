import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '@/components/ui/table';
import { AlertTriangle, ShieldAlert } from 'lucide-react';
import { useOrders } from '@/hooks/useOrders';
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
    AlertDialogTrigger,
} from '@/components/ui/alert-dialog';

export const TradingConsole: React.FC = () => {
    const { activeOrders, isLoading, cancelAll, isCancelling } = useOrders();

    return (
        <Card className="w-full mt-4 border-l-4 border-l-yellow-500">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-xl font-bold flex items-center gap-2">
                    <ShieldAlert className="h-6 w-6 text-yellow-500" />
                    Prop Trading Console
                </CardTitle>

                <AlertDialog>
                    <AlertDialogTrigger asChild>
                        <Button variant="destructive" size="sm" className="bg-red-600 hover:bg-red-700 font-bold animate-pulse">
                            <AlertTriangle className="mr-2 h-4 w-4" />
                            PANIC: CANCEL ALL
                        </Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent>
                        <AlertDialogHeader>
                            <AlertDialogTitle>EMERGENCY PROTOCOL</AlertDialogTitle>
                            <AlertDialogDescription>
                                Are you sure you want to CANCEL ALL ACTIVE ORDERS?
                                <br /><br />
                                This action is irreversible and will stop all pending trades immediately.
                                Existing positions will NOT be closed (Liquidation is manual).
                            </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                            <AlertDialogCancel>Abort</AlertDialogCancel>
                            <AlertDialogAction
                                onClick={() => cancelAll()}
                                className="bg-red-600 hover:bg-red-700"
                            >
                                {isCancelling ? "Processing..." : "CONFIRM CANCEL ALL"}
                            </AlertDialogAction>
                        </AlertDialogFooter>
                    </AlertDialogContent>
                </AlertDialog>
            </CardHeader>
            <CardContent>
                <div className="rounded-md border">
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Order ID</TableHead>
                                <TableHead>Symbol</TableHead>
                                <TableHead>Side</TableHead>
                                <TableHead>Qty</TableHead>
                                <TableHead>Filled</TableHead>
                                <TableHead>Status</TableHead>
                                <TableHead className="text-right">Time</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {isLoading ? (
                                <TableRow>
                                    <TableCell colSpan={7} className="h-24 text-center">Loading Active Orders...</TableCell>
                                </TableRow>
                            ) : activeOrders && activeOrders.length > 0 ? (
                                activeOrders.map((order: any) => (
                                    <TableRow key={order.order_id}>
                                        <TableCell className="font-mono text-xs">{order.order_id.substring(0, 8)}...</TableCell>
                                        <TableCell className="font-bold">{order.symbol}</TableCell>
                                        <TableCell className={order.side === 'buy' ? 'text-green-500' : 'text-red-500'}>
                                            {order.side.toUpperCase()}
                                        </TableCell>
                                        <TableCell>{order.quantity}</TableCell>
                                        <TableCell>{order.filled_qty}</TableCell>
                                        <TableCell>
                                            <span className="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80">
                                                {order.status}
                                            </span>
                                        </TableCell>
                                        <TableCell className="text-right text-xs text-muted-foreground">
                                            {new Date(order.created_at).toLocaleTimeString()}
                                        </TableCell>
                                    </TableRow>
                                ))
                            ) : (
                                <TableRow>
                                    <TableCell colSpan={7} className="h-24 text-center text-muted-foreground">
                                        No Active Orders
                                    </TableCell>
                                </TableRow>
                            )}
                        </TableBody>
                    </Table>
                </div>
            </CardContent>
        </Card>
    );
};
