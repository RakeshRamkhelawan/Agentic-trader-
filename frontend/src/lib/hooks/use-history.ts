import { useQuery } from "@tanstack/react-query";
import { getHistory, type Trade } from "@/lib/api/trading-api";

export function useHistory() {
    return useQuery({
        queryKey: ["history"],
        queryFn: getHistory,
        refetchInterval: 10000,
        retry: false,
    });
}
