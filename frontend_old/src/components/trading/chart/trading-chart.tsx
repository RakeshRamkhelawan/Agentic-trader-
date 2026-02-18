"use client";

import { useEffect, useRef, useState } from "react";
import { createChart, ColorType, IChartApi, ISeriesApi, UTCTimestamp } from "lightweight-charts";
import { cn } from "@/lib/utils";
import { useTicker } from "@/lib/hooks/use-ticker";
import { useCandles } from "@/lib/hooks/use-candles";

interface TradingChartProps {
    symbol: string;
    className?: string;
}

// Mock data generation removed for GTM production implementation

export function TradingChart({ symbol, className }: TradingChartProps) {
    const chartContainerRef = useRef<HTMLDivElement>(null);
    const chartRef = useRef<IChartApi | null>(null);
    const seriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    // Subscribe to live ticker updates
    const { ticker } = useTicker(symbol);
    const { data: candles, isLoading: isCandlesLoading } = useCandles(symbol);

    // Initial data load
    useEffect(() => {
        if (seriesRef.current && candles && candles.length > 0) {
            // Transform if needed, but API returns compatible format?
            // API: { time, open, high, low, close, value }
            // Lightweight: { time, open, high, low, close }
            // We need to ensure 'time' is UTCTimestamp (seconds).
            // Our API returns seconds (TradingService confirmed).

            const formattedData = candles.map(c => ({
                ...c,
                time: c.time as UTCTimestamp
            }));

            seriesRef.current.setData(formattedData);
            setIsLoading(false);
        }
    }, [candles]);

    useEffect(() => {
        if (!chartContainerRef.current) return;

        // Create chart
        chartRef.current = createChart(chartContainerRef.current, {
            layout: {
                background: { type: ColorType.Solid, color: "transparent" },
                textColor: "#9CA3AF",
            },
            grid: {
                vertLines: { color: "rgba(255, 255, 255, 0.05)" },
                horzLines: { color: "rgba(255, 255, 255, 0.05)" },
            },
            crosshair: {
                mode: 1, // CrosshairMode.Normal - explicit value to avoid import
                vertLine: {
                    color: "rgba(255, 255, 255, 0.2)",
                    labelBackgroundColor: "#1F1F1F",
                },
                horzLine: {
                    color: "rgba(255, 255, 255, 0.2)",
                    labelBackgroundColor: "#1F1F1F",
                },
            },
            rightPriceScale: {
                borderColor: "rgba(255, 255, 255, 0.1)",
            },
            timeScale: {
                borderColor: "rgba(255, 255, 255, 0.1)",
                timeVisible: true,
                secondsVisible: true,
            },
        });

        // Add candlestick series
        seriesRef.current = chartRef.current.addCandlestickSeries({
            upColor: "#00C087",
            downColor: "#FF4976",
            borderUpColor: "#00C087",
            borderDownColor: "#FF4976",
            wickUpColor: "#00C087",
            wickDownColor: "#FF4976",
        });

        // Initialize with empty data
        seriesRef.current.setData([]);

        if (!isCandlesLoading && !candles) {
            setIsLoading(false);
        }

        // Handle resize
        const handleResize = () => {
            if (chartRef.current && chartContainerRef.current) {
                chartRef.current.applyOptions({
                    width: chartContainerRef.current.clientWidth,
                    height: chartContainerRef.current.clientHeight,
                });
            }
        };

        window.addEventListener("resize", handleResize);

        return () => {
            window.removeEventListener("resize", handleResize);
            chartRef.current?.remove();
        };
    }, [symbol]);

    // Update chart with real-time data
    useEffect(() => {
        if (ticker && seriesRef.current) {
            // In a real app, we'd aggregate ticks. 
            // Here we simply update the current candle logic or just push a new point 
            // dependent on timeframe. For simplicity in this demo, we assume 1-minute updates
            // or just update the "current" candle.

            // Note: lightweight-charts wants UTCTimestamp. 
            // We use the ticker timestamp.
            const time = Math.floor(new Date(ticker.timestamp).getTime() / 1000) as UTCTimestamp;

            seriesRef.current.update({
                time: time,
                open: ticker.last, // Simplification: open = current for single tick updates if no aggregation
                high: ticker.last,
                low: ticker.last,
                close: ticker.last,
            });
        }
    }, [ticker]);

    return (
        <div className={cn("relative h-full w-full", className)}>
            {isLoading && (
                <div className="absolute inset-0 flex items-center justify-center bg-card">
                    <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
                </div>
            )}
            <div ref={chartContainerRef} className="h-full w-full" />
        </div>
    );
}
