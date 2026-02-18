import { useQuery } from "@tanstack/react-query";
import { getPortfolio, type PortfolioStats } from "@/lib/api/trading-api";

export function usePortfolio() {
    return useQuery({
        queryKey: ["portfolio"],
        queryFn: getPortfolio,
        refetchInterval: 5000, // Refresh every 5s
        retry: false,
    });
}
