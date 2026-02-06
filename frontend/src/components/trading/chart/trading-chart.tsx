"use client";

import { useEffect, useRef, useState } from "react";
import { createChart, ColorType, IChartApi, ISeriesApi, UTCTimestamp } from "lightweight-charts";
import { cn } from "@/lib/utils";

interface TradingChartProps {
    symbol: string;
    className?: string;
}

// Mock candlestick data
const generateMockData = () => {
    const data = [];
    let time = Math.floor(new Date("2024-01-01").getTime() / 1000);
    let open = 45000;

    for (let i = 0; i < 500; i++) {
        const change = (Math.random() - 0.48) * 500;
        const high = open + Math.random() * 300;
        const low = open - Math.random() * 300;
        const close = open + change;

        data.push({
            time: time as UTCTimestamp,
            open,
            high: Math.max(open, close, high),
            low: Math.min(open, close, low),
            close,
        });

        open = close;
        time += 3600; // 1 hour candles
    }

    return data;
};

export function TradingChart({ symbol, className }: TradingChartProps) {
    const chartContainerRef = useRef<HTMLDivElement>(null);
    const chartRef = useRef<IChartApi | null>(null);
    const seriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
    const [isLoading, setIsLoading] = useState(true);

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
                mode: 0,
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
                secondsVisible: false,
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

        // Set data
        const data = generateMockData();
        seriesRef.current.setData(data);
        chartRef.current.timeScale().fitContent();

        setIsLoading(false);

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
        handleResize();

        return () => {
            window.removeEventListener("resize", handleResize);
            chartRef.current?.remove();
        };
    }, [symbol]);

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
