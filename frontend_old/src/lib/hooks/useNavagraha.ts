import { useQuery } from '@tanstack/react-query';
import { NavagrahaState } from '../stores/navagrahaStore';

async function fetchNavagrahaState(): Promise<NavagrahaState> {
    const res = await fetch('/api/navagraha/current-state');
    if (!res.ok) {
        throw new Error('Failed to fetch navagraha state');
    }
    return res.json();
}

export function useNavagrahaState() {
    return useQuery({
        queryKey: ['navagraha', 'current-state'],
        queryFn: fetchNavagrahaState,
        refetchInterval: 60000, // Refetch every minute as backup to websocket
        staleTime: 30000,
    });
}
