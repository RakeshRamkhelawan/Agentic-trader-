
import { useEffect, useState } from 'react';
import { wsClient, IncomingMessage } from '@/lib/api/websocket-client';

export function useSocket<T>(channel: string) {
    const [data, setData] = useState<T | null>(null);
    const [isConnected, setIsConnected] = useState(wsClient.connected);

    useEffect(() => {
        // Handle connection state
        const handleConnect = () => setIsConnected(true);
        const handleDisconnect = () => setIsConnected(false);

        wsClient.on('connect', handleConnect);
        wsClient.on('disconnect', handleDisconnect);

        // Subscribe to channel
        const sub = wsClient.subscribe(channel, (msg) => {
            // We cast the data to T. 
            // msg is IncomingMessage, msg.data is unknown.
            const payload = msg as IncomingMessage;
            if (payload.data) {
                setData(payload.data as T);
            }
        });

        // Initial connect if needed
        if (!wsClient.connected) {
            wsClient.connect();
        }

        return () => {
            sub.unsubscribe();
            wsClient.off('connect', handleConnect);
            wsClient.off('disconnect', handleDisconnect);
        };
    }, [channel]);

    return { data, isConnected };
}
