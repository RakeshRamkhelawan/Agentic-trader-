'use client';

import React from 'react';
import { motion } from 'framer-motion';

export interface GunaVector {
    sattva: number;
    rajas: number;
    tamas: number;
}

interface GunaDistributionProps {
    guna: GunaVector;
    consciousness_level?: string;
    balance_score?: number;
}

export const GunaDistribution: React.FC<GunaDistributionProps> = ({ 
    guna, 
    consciousness_level,
    balance_score 
}) => {
    if (!guna) return null;

    const total = guna.sattva + guna.rajas + guna.tamas;
    const sattvaPct = (guna.sattva / total) * 100;
    const rajasPct = (guna.rajas / total) * 100;
    const tamasPct = (guna.tamas / total) * 100;

    const getDominantGuna = () => {
        if (guna.sattva >= guna.rajas && guna.sattva >= guna.tamas) return 'sattva';
        if (guna.rajas >= guna.tamas) return 'rajas';
        return 'tamas';
    };

    const dominant = getDominantGuna();

    const getConsciousnessColor = (level?: string) => {
        switch (level?.toLowerCase()) {
            case 'pure awareness': return 'text-emerald-400';
            case 'discriminative intelligence': return 'text-blue-400';
            case 'active manifestation': return 'text-yellow-400';
            case 'material density': return 'text-red-400';
            default: return 'text-white';
        }
    };

    return (
        <div className="w-full bg-card border border-border rounded-xl p-6 backdrop-blur-md">
            <div className="flex justify-between items-start mb-6">
                <div>
                    <h3 className="text-lg font-bold text-white flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-gradient-to-r from-emerald-500 via-yellow-500 to-red-500 animate-pulse"></span>
                        Guna Distribution
                    </h3>
                    {consciousness_level && (
                        <p className="text-sm mt-1">
                            Consciousness: <span className={`font-medium ${getConsciousnessColor(consciousness_level)}`}>
                                {consciousness_level}
                            </span>
                        </p>
                    )}
                </div>
                {balance_score !== undefined && (
                    <div className="text-right">
                        <div className="text-2xl font-bold font-mono text-white">
                            {(balance_score * 100).toFixed(1)}%
                        </div>
                        <div className="text-xs text-muted-foreground">Balance Score</div>
                    </div>
                )}
            </div>

            {/* Donut Chart */}
            <div className="flex items-center justify-center mb-6">
                <div className="relative w-40 h-40">
                    <svg viewBox="0 0 100 100" className="w-full h-full transform -rotate-90">
                        {/* Background circle */}
                        <circle
                            cx="50"
                            cy="50"
                            r="40"
                            fill="none"
                            stroke="rgba(255,255,255,0.1)"
                            strokeWidth="20"
                        />
                        
                        {/* Sattva (Emerald) */}
                        <motion.circle
                            cx="50"
                            cy="50"
                            r="40"
                            fill="none"
                            stroke="#10B981"
                            strokeWidth="20"
                            strokeDasharray={`${sattvaPct * 2.51} 251`}
                            initial={{ strokeDasharray: '0 251' }}
                            animate={{ strokeDasharray: `${sattvaPct * 2.51} 251` }}
                            transition={{ duration: 0.8, ease: 'easeOut' }}
                        />
                        
                        {/* Rajas (Yellow/Orange) */}
                        <motion.circle
                            cx="50"
                            cy="50"
                            r="40"
                            fill="none"
                            stroke="#F59E0B"
                            strokeWidth="20"
                            strokeDasharray={`${rajasPct * 2.51} 251`}
                            strokeDashoffset={-sattvaPct * 2.51}
                            initial={{ strokeDasharray: '0 251' }}
                            animate={{ strokeDasharray: `${rajasPct * 2.51} 251` }}
                            transition={{ duration: 0.8, ease: 'easeOut', delay: 0.1 }}
                        />
                        
                        {/* Tamas (Red) */}
                        <motion.circle
                            cx="50"
                            cy="50"
                            r="40"
                            fill="none"
                            stroke="#EF4444"
                            strokeWidth="20"
                            strokeDasharray={`${tamasPct * 2.51} 251`}
                            strokeDashoffset={-(sattvaPct + rajasPct) * 2.51}
                            initial={{ strokeDasharray: '0 251' }}
                            animate={{ strokeDasharray: `${tamasPct * 2.51} 251` }}
                            transition={{ duration: 0.8, ease: 'easeOut', delay: 0.2 }}
                        />
                    </svg>
                    
                    {/* Center text */}
                    <div className="absolute inset-0 flex flex-col items-center justify-center">
                        <span className="text-xs text-muted-foreground uppercase tracking-wider">Dominant</span>
                        <span className={`text-lg font-bold capitalize ${
                            dominant === 'sattva' ? 'text-emerald-400' :
                            dominant === 'rajas' ? 'text-yellow-400' : 'text-red-400'
                        }`}>
                            {dominant}
                        </span>
                    </div>
                </div>
            </div>

            {/* Legend */}
            <div className="space-y-3">
                <div className="flex items-center justify-between p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                    <div className="flex items-center gap-3">
                        <div className="w-4 h-4 rounded-full bg-emerald-500" />
                        <div>
                            <div className="text-sm font-medium text-white">Sattva</div>
                            <div className="text-xs text-muted-foreground">Harmony, Wisdom, Clarity</div>
                        </div>
                    </div>
                    <div className="text-right">
                        <div className="text-lg font-bold font-mono text-emerald-400">{sattvaPct.toFixed(1)}%</div>
                    </div>
                </div>

                <div className="flex items-center justify-between p-3 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
                    <div className="flex items-center gap-3">
                        <div className="w-4 h-4 rounded-full bg-yellow-500" />
                        <div>
                            <div className="text-sm font-medium text-white">Rajas</div>
                            <div className="text-xs text-muted-foreground">Activity, Passion, Movement</div>
                        </div>
                    </div>
                    <div className="text-right">
                        <div className="text-lg font-bold font-mono text-yellow-400">{rajasPct.toFixed(1)}%</div>
                    </div>
                </div>

                <div className="flex items-center justify-between p-3 rounded-lg bg-red-500/10 border border-red-500/20">
                    <div className="flex items-center gap-3">
                        <div className="w-4 h-4 rounded-full bg-red-500" />
                        <div>
                            <div className="text-sm font-medium text-white">Tamas</div>
                            <div className="text-xs text-muted-foreground">Inertia, Darkness, Resistance</div>
                        </div>
                    </div>
                    <div className="text-right">
                        <div className="text-lg font-bold font-mono text-red-400">{tamasPct.toFixed(1)}%</div>
                    </div>
                </div>
            </div>

            {/* Trading Gate Status */}
            <div className="mt-4 pt-4 border-t border-white/10">
                <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Trading Gate Status</span>
                    <span className={`text-sm font-medium ${
                        tamasPct > 60 ? 'text-red-400' : 'text-emerald-400'
                    }`}>
                        {tamasPct > 60 ? 'BLOCKED (High Tamas)' : 'OPEN'}
                    </span>
                </div>
                {tamasPct > 60 && (
                    <p className="text-xs text-red-400/80 mt-2">
                        ⚠️ High Tamas detected. Trading is restricted to prevent unfavorable outcomes.
                    </p>
                )}
            </div>
        </div>
    );
};
