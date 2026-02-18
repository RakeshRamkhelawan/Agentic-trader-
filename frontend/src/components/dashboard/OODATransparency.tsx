'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { ArrowRight, CheckCircle2, CircleDashed, AlertCircle } from 'lucide-react';

export interface OODAPhase {
    status: 'pending' | 'in_progress' | 'completed' | 'failed';
    duration_ms?: number;
    data_collected?: any;
    selected_strategy?: string;
    reason?: string;
}

export interface OODACycle {
    cycle_id: string;
    current_phase: string;
    phases: {
        Observe: OODAPhase;
        Orient: OODAPhase;
        Decide: OODAPhase;
        Act: OODAPhase;
    };
    navagraha_influence: {
        dasha_selected_strategy: boolean;
        guna_modulated_risk: string;
        rahu_kala_blocked: boolean;
    };
}

interface OODATransparencyProps {
    cycle: OODACycle;
}

const PhaseCard: React.FC<{ name: string; phase: OODAPhase; isActive: boolean }> = ({ name, phase, isActive }) => {
    const getStatusColor = (status: string) => {
        switch (status) {
            case 'completed': return 'text-positive border-positive/30 bg-positive/10';
            case 'in_progress': return 'text-brand-blue border-brand-blue/30 bg-brand-blue/10 animate-pulse-slow';
            case 'failed': return 'text-destructive border-destructive/30 bg-destructive/10';
            default: return 'text-muted-foreground border-white/5 bg-white/5 opacity-50';
        }
    };

    const getIcon = (status: string) => {
        switch (status) {
            case 'completed': return <CheckCircle2 className="w-5 h-5" />;
            case 'in_progress': return <CircleDashed className="w-5 h-5 animate-spin-slow" />;
            case 'failed': return <AlertCircle className="w-5 h-5" />;
            default: return <CircleDashed className="w-5 h-5" />;
        }
    };

    return (
        <div className={`flex flex-col p-4 rounded-lg border ${getStatusColor(phase.status)} transition-all duration-300 min-w-[140px]`}>
            <div className="flex items-center justify-between mb-2">
                <span className="font-bold tracking-wide">{name}</span>
                {getIcon(phase.status)}
            </div>

            {phase.duration_ms && (
                <span className="text-xs opacity-70 mb-1">{phase.duration_ms}ms</span>
            )}

            {name === 'Orient' && phase.selected_strategy && (
                <div className="mt-2 text-xs bg-black/20 p-2 rounded">
                    Strategy: <span className="font-mono text-brand-blue">{phase.selected_strategy}</span>
                </div>
            )}
        </div>
    );
};

export const OODATransparency: React.FC<OODATransparencyProps> = ({ cycle }) => {
    if (!cycle) return null;

    return (
        <div className="w-full bg-white/5 border border-white/10 rounded-xl p-6 backdrop-blur-md">
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h3 className="text-lg font-bold text-white flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-brand-blue animate-pulse"></span>
                        OODA Loop Transparency
                    </h3>
                    <p className="text-sm text-muted-foreground font-mono mt-1">ID: {cycle.cycle_id}</p>
                </div>
                <div className="flex gap-4 text-xs">
                    <div className="flex items-center gap-1.5">
                        <div className={`w-2 h-2 rounded-full ${cycle.navagraha_influence.dasha_selected_strategy ? 'bg-brand-purple' : 'bg-muted'}`} />
                        <span className="text-muted-foreground">Dasha Strategy</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                        <div className={`w-2 h-2 rounded-full ${!cycle.navagraha_influence.rahu_kala_blocked ? 'bg-positive' : 'bg-destructive'}`} />
                        <span className="text-muted-foreground">Rahu Gate</span>
                    </div>
                </div>
            </div>

            <div className="flex flex-col md:flex-row gap-4 items-stretch relative">
                {/* Connecting Line (Desktop) */}
                <div className="hidden md:block absolute top-1/2 left-0 w-full h-0.5 bg-white/5 -z-10 transform -translate-y-1/2" />

                <PhaseCard name="Observe" phase={cycle.phases.Observe} isActive={cycle.current_phase === 'Observe'} />
                <div className="hidden md:flex items-center text-muted-foreground"><ArrowRight className="w-4 h-4" /></div>

                <PhaseCard name="Orient" phase={cycle.phases.Orient} isActive={cycle.current_phase === 'Orient'} />
                <div className="hidden md:flex items-center text-muted-foreground"><ArrowRight className="w-4 h-4" /></div>

                <PhaseCard name="Decide" phase={cycle.phases.Decide} isActive={cycle.current_phase === 'Decide'} />
                <div className="hidden md:flex items-center text-muted-foreground"><ArrowRight className="w-4 h-4" /></div>

                <PhaseCard name="Act" phase={cycle.phases.Act} isActive={cycle.current_phase === 'Act'} />
            </div>
        </div>
    );
};
