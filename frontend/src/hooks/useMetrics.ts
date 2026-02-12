import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';

export const useMetrics = () => {
    return useQuery({
        queryKey: ['metrics'],
        queryFn: async () => {
            // Correct auto-generated method name
            const response = await apiClient.analytics.getDashboardMetricsApiV1AnalyticsMetricsGet();
            return response;
        },
        refetchInterval: 2000, // Poll every 2 seconds
    });
};
