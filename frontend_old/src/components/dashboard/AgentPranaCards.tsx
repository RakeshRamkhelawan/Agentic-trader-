'use client';

import React from 'react';
import { motion } from 'framer-motion';

export interface Agent {
    element: string;
    name: string;
    prana_level: number;
    active: boolean;
    last_signal: string;
    recent_contributions: number;
}

interface AgentPranaCardsProps {
    agents: Agent[];
}

const elementIcons: { [key: string]: string } = {
    ether: '🌌',
    air: '💨',
    fire: '🔥',
    water: '💧',
    earth: '🌍'
};

const getPranaColor = (level: number): string => {
    if (level > 70) return '#00C087'; // Green
    if (level > 40) return '#FF9500'; // Orange
    if (level > 20) return '#FF4976'; // Pink/Redish
    return '#DC3545'; // Red
};

export const AgentPranaCards: React.FC<AgentPranaCardsProps> = ({ agents }) => {
    if (!agents) return null;

    return (
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            {agents.map((agent, index) => (
                <motion.div
                    key={agent.element}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className={`p-4 rounded-xl border border-white/5 bg-white/5 backdrop-blur-sm hover:bg-white/10 transition-colors element-${agent.element}`}
                >
                    <div className="flex items-center justify-between mb-3">
                        <span className="text-2xl">{elementIcons[agent.element]}</span>
                        <div className={`w-2 h-2 rounded-full ${agent.active ? 'bg-positive animate-pulse' : 'bg-muted'}`} />
                    </div>

                    <h3 className="text-sm font-medium text-muted-foreground mb-1 uppercase tracking-wide">{agent.name}</h3>

                    <div className="relative h-2 bg-white/10 rounded-full overflow-hidden mb-2">
                        <motion.div
                            className="absolute top-0 left-0 h-full rounded-full"
                            style={{ backgroundColor: getPranaColor(agent.prana_level) }}
                            initial={{ width: 0 }}
                            animate={{ width: `${agent.prana_level}%` }}
                            transition={{ duration: 1, ease: "easeOut" }}
                        />
                    </div>

                    <div className="flex justify-between items-end">
                        <span className="text-2xl font-bold font-mono">{agent.prana_level.toFixed(1)}%</span>
                        <span className="text-xs text-muted-foreground">Prana</span>
                    </div>

                    <div className="mt-3 pt-3 border-t border-white/5 flex justify-between text-xs text-muted-foreground">
                        <span>Contribs: {agent.recent_contributions}</span>
                    </div>
                </motion.div>
            ))}
        </div>
    );
};
