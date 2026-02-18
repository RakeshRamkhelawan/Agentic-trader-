'use client';

import React from 'react';
import { motion } from 'framer-motion';

export interface TattvaLayer {
    layer_number: number;
    name: string;
    coherence: number;
    active: boolean;
}

export interface TattvaState {
    layers: TattvaLayer[];
    overall_coherence: number;
    kanchuka_gate_open: boolean;
    current_traversal: string;
}

interface TattvaMonitorProps {
    state: TattvaState;
}

const TATTVA_GROUPS = [
    { name: 'Shuddha (1-5)', start: 1, end: 5, color: '#FFD700' },
    { name: 'Kanchuka (6-12)', start: 6, end: 12, color: '#FF6B35' },
    { name: 'Interface (13-15)', start: 13, end: 15, color: '#4ECDC4' },
    { name: 'Senses (16-25)', start: 16, end: 25, color: '#95E1D3' },
    { name: 'Actions (26-31)', start: 26, end: 31, color: '#F38181' },
    { name: 'Physical (32-36)', start: 32, end: 36, color: '#AA96DA' },
];

export const TattvaMonitor: React.FC<TattvaMonitorProps> = ({ state }) => {
    if (!state) return null;

    const getCoherenceColor = (coherence: number) => {
        if (coherence >= 0.8) return 'bg-emerald-500';
        if (coherence >= 0.6) return 'bg-yellow-500';
        if (coherence >= 0.4) return 'bg-orange-500';
        return 'bg-red-500';
    };

    const getGroupCoherence = (start: number, end: number) => {
        const groupLayers = state.layers.filter(l => l.layer_number >= start && l.layer_number <= end);
        if (groupLayers.length === 0) return 1.0;
        return groupLayers.reduce((sum, l) => sum + l.coherence, 0) / groupLayers.length;
    };

    return (
        <div className="w-full bg-card border border-border rounded-xl p-6 backdrop-blur-md">
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h3 className="text-lg font-bold text-white flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-purple-500 animate-pulse"></span>
                        36-Tattva Consciousness
                    </h3>
                    <p className="text-sm text-muted-foreground mt-1">
                        Traversal: <span className="font-mono text-purple-400">{state.current_traversal}</span>
                    </p>
                </div>
                <div className="flex items-center gap-3">
                    <div className={`px-3 py-1 rounded-full text-xs font-medium ${
                        state.kanchuka_gate_open 
                            ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' 
                            : 'bg-red-500/20 text-red-400 border border-red-500/30'
                    }`}>
                        {state.kanchuka_gate_open ? 'Kanchuka Gate OPEN' : 'Kanchuka Gate BLOCKED'}
                    </div>
                    <div className="text-right">
                        <div className="text-2xl font-bold font-mono text-white">
                            {(state.overall_coherence * 100).toFixed(1)}%
                        </div>
                        <div className="text-xs text-muted-foreground">Coherence</div>
                    </div>
                </div>
            </div>

            {/* Group Overview */}
            <div className="grid grid-cols-3 md:grid-cols-6 gap-2 mb-6">
                {TATTVA_GROUPS.map((group) => {
                    const coherence = getGroupCoherence(group.start, group.end);
                    return (
                        <motion.div
                            key={group.name}
                            className="p-3 rounded-lg bg-white/5 border border-white/10"
                            whileHover={{ scale: 1.02 }}
                        >
                            <div className="text-xs text-muted-foreground mb-1">{group.name}</div>
                            <div className="flex items-center gap-2">
                                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: group.color }} />
                                <span className="text-sm font-mono font-bold text-white">
                                    {(coherence * 100).toFixed(0)}%
                                </span>
                            </div>
                            <div className="w-full h-1 bg-white/10 rounded-full mt-2 overflow-hidden">
                                <motion.div
                                    className="h-full rounded-full"
                                    style={{ backgroundColor: group.color }}
                                    initial={{ width: 0 }}
                                    animate={{ width: `${coherence * 100}%` }}
                                    transition={{ duration: 0.5 }}
                                />
                            </div>
                        </motion.div>
                    );
                })}
            </div>

            {/* Individual Layers Grid */}
            <div className="grid grid-cols-6 md:grid-cols-12 gap-1">
                {state.layers.map((layer, index) => (
                    <motion.div
                        key={layer.layer_number}
                        className={`aspect-square rounded-md flex items-center justify-center text-xs font-mono cursor-pointer transition-all ${
                            layer.active 
                                ? `${getCoherenceColor(layer.coherence)} text-white font-bold` 
                                : 'bg-white/5 text-muted-foreground'
                        }`}
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: index * 0.01 }}
                        title={`Layer ${layer.layer_number}: ${layer.name} (${(layer.coherence * 100).toFixed(0)}%)`}
                    >
                        {layer.layer_number}
                    </motion.div>
                ))}
            </div>

            {/* Legend */}
            <div className="flex items-center justify-between mt-4 pt-4 border-t border-white/10">
                <div className="flex items-center gap-4 text-xs text-muted-foreground">
                    <div className="flex items-center gap-1">
                        <div className="w-2 h-2 rounded-full bg-emerald-500" />
                        <span>High (80%+)</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <div className="w-2 h-2 rounded-full bg-yellow-500" />
                        <span>Medium (60-80%)</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <div className="w-2 h-2 rounded-full bg-orange-500" />
                        <span>Low (40-60%)</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <div className="w-2 h-2 rounded-full bg-red-500" />
                        <span>Critical (&lt;40%)</span>
                    </div>
                </div>
                <div className="text-xs text-muted-foreground">
                    Layers 6-12 (Kanchuka) act as risk gates
                </div>
            </div>
        </div>
    );
};
