"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useTradingStore } from "@/lib/stores/trading-store";

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
    currentPrice?: number;
    className?: string;
}

export function OrderTicket({
    symbol,
    currentPrice = 45230.5,
    className,
}: OrderTicketProps) {
    const { orderSide, orderType, setOrderSide, setOrderType } = useTradingStore();
    const [isSubmitting, setIsSubmitting] = useState(false);

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
            limitPrice: currentPrice.toString(),
        },
    });

    const quantity = watch("quantity");
    const estimatedTotal = Number(quantity || 0) * currentPrice;

    const onSubmit = async (data: OrderFormData) => {
        setIsSubmitting(true);
        try {
            // TODO: Submit order to backend
            console.log("Submit order:", { ...data, side: orderSide, type: orderType });
            await new Promise((r) => setTimeout(r, 1000));
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className={cn("flex flex-col gap-4 p-4", className)}>
            {/* Buy/Sell Toggle */}
            <div className="grid grid-cols-2 gap-1 rounded-lg bg-secondary p-1">
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
                    <label className="text-sm font-medium text-muted-foreground">
                        Amount (BTC)
                    </label>
                    <Input
                        {...register("quantity")}
                        type="number"
                        step="0.0001"
                        placeholder="0.00"
                        className="font-mono"
                    />
                    {errors.quantity && (
                        <p className="text-xs text-brand-red">{errors.quantity.message}</p>
                    )}
                </div>

                {/* Limit Price (for limit orders) */}
                {orderType !== "market" && (
                    <div className="space-y-2">
                        <label className="text-sm font-medium text-muted-foreground">
                            {orderType === "stop" ? "Stop Price" : "Limit Price"} (EUR)
                        </label>
                        <Input
                            {...register("limitPrice")}
                            type="number"
                            step="0.01"
                            placeholder={currentPrice.toString()}
                            className="font-mono"
                        />
                    </div>
                )}

                {/* Quick Amount Buttons */}
                <div className="grid grid-cols-4 gap-2">
                    {[25, 50, 75, 100].map((pct) => (
                        <button
                            key={pct}
                            type="button"
                            onClick={() => setValue("quantity", ((10000 * pct) / 100 / currentPrice).toFixed(4))}
                            className="rounded-md bg-secondary py-1.5 text-xs font-medium hover:bg-accent"
                        >
                            {pct}%
                        </button>
                    ))}
                </div>

                {/* Total Estimate */}
                <div className="flex items-center justify-between rounded-md bg-secondary px-3 py-2">
                    <span className="text-sm text-muted-foreground">Total</span>
                    <span className="font-mono font-medium">
                        EUR {estimatedTotal.toLocaleString("nl-NL", { minimumFractionDigits: 2 })}
                    </span>
                </div>

                {/* Submit Button */}
                <Button
                    type="submit"
                    variant={orderSide === "buy" ? "buy" : "sell"}
                    className="w-full py-3 text-base font-semibold"
                    disabled={isSubmitting}
                >
                    {isSubmitting ? (
                        "Processing..."
                    ) : (
                        <>
                            {orderSide === "buy" ? "Buy" : "Sell"} BTC
                        </>
                    )}
                </Button>
            </form>
        </div>
    );
}
