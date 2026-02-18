import { useQuery } from "@tanstack/react-query";
import { getCandles, type Candle } from "@/lib/api/trading-api";

export function useCandles(symbol: string) {
    return useQuery({
        queryKey: ["candles", symbol],
        queryFn: () => getCandles(symbol),
        refetchInterval: 60000, // Refresh every 1m
        retry: false,
    });
}
