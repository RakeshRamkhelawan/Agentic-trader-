"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useTradingStore } from "@/lib/stores/trading-store";
import { submitOrder } from "@/lib/api/trading-api";
import { toast } from "sonner";
import { useTicker } from "@/lib/hooks/use-ticker";
import { usePortfolio } from "@/lib/hooks/use-portfolio";

const orderSchema = z.object({
    quantity: z.string().min(1, "Quantity is required").refine(
        (val) => !isNaN(Number(val)) && Number(val) > 0,
        "Must be a positive number"
    ),
    limitPrice: z.string().optional(),
    stopPrice: z.string().optional(),
});

type OrderFormData = z.infer<typeof orderSchema>;

interface OrderTicketProps {
    symbol: string;
    className?: string;
}

export function OrderTicket({
    symbol,
    className,
}: OrderTicketProps) {
    const { orderSide, orderType, setOrderSide, setOrderType } = useTradingStore();
    const [isSubmitting, setIsSubmitting] = useState(false);

    // Real data hooks
    const { ticker } = useTicker(symbol);
    const { data: portfolio } = usePortfolio();

    // Derived values
    const currentPrice = ticker?.last || 0;
    const baseAsset = symbol.split("-")[0]; // e.g., "BTC"
    const quoteAsset = symbol.split("-")[1] || "EUR"; // e.g., "EUR"

    // Calculate available balance
    const availableBalance = orderSide === "buy"
        ? portfolio?.holdings.find(h => h.symbol === quoteAsset)?.amount || portfolio?.total_value || 0 // Fallback to total_value if plain cash
        : portfolio?.holdings.find(h => h.symbol === baseAsset)?.amount || 0;

    const {
        register,
        handleSubmit,
        formState: { errors },
        watch,
        setValue,
    } = useForm<OrderFormData>({
        resolver: zodResolver(orderSchema),
        defaultValues: {
            quantity: "",
            limitPrice: currentPrice > 0 ? currentPrice.toString() : "",
        },
    });

    const quantity = watch("quantity");
    const estimatedTotal = Number(quantity || 0) * currentPrice;

    const onSubmit = async (data: OrderFormData) => {
        setIsSubmitting(true);
        try {
            await submitOrder({
                symbol,
                side: orderSide,
                type: orderType,
                quantity: Number(data.quantity),
                price: data.limitPrice ? Number(data.limitPrice) : undefined
            });
            toast.success("Order Submitted", {
                description: `${orderSide.toUpperCase()} ${data.quantity} ${baseAsset} @ ${data.limitPrice || "Market"}`,
            });
        } catch (error) {
            console.error("Order failed:", error);
            toast.error("Order Failed", {
                description: error instanceof Error ? error.message : "Please try again",
            });
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className={cn("flex flex-col gap-4 p-4", className)}>
            {/* Buy/Sell Toggle */}
            <div className="grid grid-cols-2 gap-1 rounded-lg bg-white/5 p-1">
                <button
                    onClick={() => setOrderSide("buy")}
                    className={cn(
                        "rounded-md py-2 text-sm font-medium transition-colors",
                        orderSide === "buy"
                            ? "bg-brand-green text-white"
                            : "text-muted-foreground hover:text-foreground"
                    )}
                >
                    Buy
                </button>
                <button
                    onClick={() => setOrderSide("sell")}
                    className={cn(
                        "rounded-md py-2 text-sm font-medium transition-colors",
                        orderSide === "sell"
                            ? "bg-brand-red text-white"
                            : "text-muted-foreground hover:text-foreground"
                    )}
                >
                    Sell
                </button>
            </div>

            {/* Order Type Tabs */}
            <div className="flex gap-2 border-b border-border">
                {(["market", "limit", "stop"] as const).map((type) => (
                    <button
                        key={type}
                        onClick={() => setOrderType(type)}
                        className={cn(
                            "border-b-2 px-3 py-2 text-sm font-medium transition-colors",
                            orderType === type
                                ? "border-primary text-foreground"
                                : "border-transparent text-muted-foreground hover:text-foreground"
                        )}
                    >
                        {type.charAt(0).toUpperCase() + type.slice(1)}
                    </button>
                ))}
            </div>

            {/* Order Form */}
            <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
                {/* Quantity */}
                <div className="space-y-2">
                    <div className="flex justify-between">
                        <label className="text-sm font-medium text-muted-foreground">
                            Amount ({baseAsset})
                        </label>
                        <span className="text-xs text-muted-foreground">
                            Avail: {availableBalance.toFixed(4)} {orderSide === "buy" ? quoteAsset : baseAsset}
                        </span>
                    </div>

                    <Input
                        {...register("quantity")}
                        type="number"
                        step="0.0001"
                        placeholder="0.00"
                        className="font-mono text-lg h-12 bg-white/5 border-white/10"
                    />
                    {errors.quantity && (
                        <p className="text-xs text-brand-red">{errors.quantity.message}</p>
                    )}
                </div>

                {/* Limit Price (for limit orders) */}
                {orderType !== "market" && (
                    <div className="space-y-2">
                        <label className="text-sm font-medium text-muted-foreground">
                            {orderType === "stop" ? "Stop Price" : "Limit Price"} ({quoteAsset})
                        </label>
                        <Input
                            {...register("limitPrice")}
                            type="number"
                            step="0.01"
                            placeholder={currentPrice > 0 ? currentPrice.toString() : "0.00"}
                            className="font-mono text-lg h-12 bg-white/5 border-white/10"
                        />
                    </div>
                )}

                {/* Quick Amount Buttons */}
                <div className="grid grid-cols-4 gap-2">
                    {[25, 50, 75, 100].map((pct) => (
                        <button
                            key={pct}
                            type="button"
                            disabled={currentPrice === 0}
                            onClick={() => {
                                if (orderSide === "buy") {
                                    // Calculate amount based on available quote currency / price
                                    if (currentPrice > 0) {
                                        const amount = (availableBalance * (pct / 100)) / currentPrice;
                                        setValue("quantity", amount.toFixed(4));
                                    }
                                } else {
                                    // Use available base asset directly
                                    const amount = availableBalance * (pct / 100);
                                    setValue("quantity", amount.toFixed(4));
                                }
                            }}
                            className="rounded-md bg-white/5 py-1.5 text-xs font-medium hover:bg-white/10 disabled:opacity-50"
                        >
                            {pct}%
                        </button>
                    ))}
                </div>

                {/* Total Estimate */}
                <div className="flex items-center justify-between rounded-md bg-white/5 px-3 py-3 border border-white/5">
                    <span className="text-sm text-muted-foreground">Total</span>
                    <span className="font-mono font-medium">
                        {quoteAsset} {estimatedTotal.toLocaleString("nl-NL", { minimumFractionDigits: 2 })}
                    </span>
                </div>

                {/* Submit Button */}
                <Button
                    type="submit"
                    variant={orderSide === "buy" ? "buy" : "sell"}
                    className="w-full py-3 text-base font-semibold"
                    disabled={isSubmitting || currentPrice === 0}
                >
                    {isSubmitting ? (
                        "Processing..."
                    ) : (
                        <>
                            {orderSide === "buy" ? "Buy" : "Sell"} {baseAsset}
                        </>
                    )}
                </Button>
            </form >
        </div >
    );
}
