import { useEffect, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import useWebSocket, { ReadyState } from 'react-use-websocket';
import { throttle } from 'lodash';

export function useRealtimeNavagraha(
    onUpdate?: (data: any) => void,
    throttleDelay: number = 1000
) {
    const queryClient = useQueryClient();
    const socketUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws';

    // Throttle updates to prevent UI jank on high-frequency data
    const throttledUpdate = useRef(
        throttle((data: any) => {
            if (onUpdate) onUpdate(data);
        }, throttleDelay)
    ).current;

    const { lastJsonMessage, readyState, sendJsonMessage } = useWebSocket(socketUrl, {
        shouldReconnect: () => true,
        reconnectAttempts: 10,
        reconnectInterval: 3000,
        onOpen: () => {
            console.log('WebSocket connected');
            // Subscribe to relevant channels
            sendJsonMessage({
                "type": "subscribe",
                "channel": "navagraha.updates"
            });
            sendJsonMessage({
                "type": "subscribe",
                "channel": "ooda.updates"
            });
            sendJsonMessage({
                "type": "subscribe",
                "channel": "agents.updates" // Future proofing
            });
        },
    });

    useEffect(() => {
        if (lastJsonMessage) {
            const message = lastJsonMessage as any;

            // Backend format: { channel: "...", type: "update", data: ... }
            if (message.type === 'update') {
                if (message.channel === 'navagraha.updates') {
                    // Update React Query cache
                    queryClient.setQueryData(['navagraha', 'current-state'], (old: any) => {
                        // Merge or replace depending on data structure
                        // Backend sends full state, so replace
                        return message.data;
                    });
                    throttledUpdate(message.data);
                } else if (message.channel === 'ooda.updates') {
                    queryClient.setQueryData(['ooda', 'current-cycle'], (old: any) => {
                        // Backend sends simplified OODA update, match generic route structure or merge
                        // The route returns a specific structure, backend update might be partial
                        // For now, let's assume we replace the core stats
                        if (!old) return message.data;
                        return { ...old, ...message.data };
                    });
                }
            }
        }
    }, [lastJsonMessage, queryClient, throttledUpdate]);

    return {
        ready: readyState === ReadyState.OPEN,
        send: sendJsonMessage,
    };
}
