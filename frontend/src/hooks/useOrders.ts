import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { toast } from 'sonner';

export const useOrders = () => {
    const queryClient = useQueryClient();

    const { data: activeOrders, isLoading, error } = useQuery({
        queryKey: ['activeOrders'],
        queryFn: async () => {
            // Needed to cast or ensure type safety if generated client isn't strict yet
            // The generated method should be getActiveOrdersApiV1TradingOrdersActiveGet
            // Check generated service to be sure, but relying on standard naming
            return await apiClient.trading.getActiveOrdersApiV1TradingOrdersActiveGet();
        },
        refetchInterval: 5000, // Poll every 5s
    });

    const cancelAllMutation = useMutation({
        mutationFn: async () => {
            return await apiClient.trading.cancelAllOrdersApiV1TradingOrdersDelete();
        },
        onSuccess: () => {
            toast.success("Emergency: All open orders cancelled");
            queryClient.invalidateQueries({ queryKey: ['activeOrders'] });
            queryClient.invalidateQueries({ queryKey: ['portfolio'] });
        },
        onError: (err: any) => {
            toast.error(`Failed to cancel orders: ${err.message}`);
        }
    });

    return {
        activeOrders,
        isLoading,
        error,
        cancelAll: cancelAllMutation.mutate,
        isCancelling: cancelAllMutation.isPending
    };
};
