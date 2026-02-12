import { useQuery } from "@tanstack/react-query";
import { getMarkets, type Market } from "@/lib/api/trading-api";

export function useMarkets() {
    return useQuery({
        queryKey: ["markets"],
        queryFn: getMarkets,
        refetchInterval: 10000, // Refresh every 10s
        retry: false,
    });
}
