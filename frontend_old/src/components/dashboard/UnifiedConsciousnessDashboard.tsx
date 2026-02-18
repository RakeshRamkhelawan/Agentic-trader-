'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Brain, Sparkles, Activity, Shield, TrendingUp } from 'lucide-react';

import { NavagrahaWheel } from './NavagrahaWheel';
import { RahuKalaGate } from './RahuKalaGate';
import { OODATransparency, OODACycle } from './OODATransparency';
import { TattvaMonitor, TattvaState } from './TattvaMonitor';
import { GunaDistribution, GunaVector } from './GunaDistribution';

// Types for the unified state
export interface Planet {
    name: string;
    longitude: number;
    is_retrograde: boolean;
}

export interface RahuKala {
    is_active: boolean;
    start_time: string;
    end_time: string;
    remaining_minutes: number;
}

export interface NavagrahaState {
    planets: Planet[];
    rahu_kala: RahuKala;
    guna: GunaVector;
    consciousness_level: string;
    trading_gate_open: boolean;
}

export interface UnifiedConsciousnessState {
    navagraha: NavagrahaState;
    tattva: TattvaState;
    ooda_cycle: OODACycle;
    components: {
        cognitive_orchestrator: boolean;
        risk_orchestrator: boolean;
        karma_register: boolean;
        system_identity: boolean;
    };
}

interface UnifiedConsciousnessDashboardProps {
    state: UnifiedConsciousnessState;
}

const StatusCard: React.FC<{
    title: string;
    status: boolean;
    icon: React.ReactNode;
    description: string;
}> = ({ title, status, icon, description }) => (
    <motion.div
        className={`p-4 rounded-lg border ${
            status 
                ? 'bg-emerald-500/10 border-emerald-500/30' 
                : 'bg-white/5 border-white/10 opacity-50'
        }`}
        whileHover={{ scale: 1.02 }}
    >
        <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                status ? 'bg-emerald-500/20 text-emerald-400' : 'bg-white/10 text-muted-foreground'
            }`}>
                {icon}
            </div>
            <div>
                <div className="text-sm font-medium text-white">{title}</div>
                <div className="text-xs text-muted-foreground">{description}</div>
            </div>
            <div className={`ml-auto w-2 h-2 rounded-full ${status ? 'bg-emerald-400 animate-pulse' : 'bg-muted'}`} />
        </div>
    </motion.div>
);

export const UnifiedConsciousnessDashboard: React.FC<UnifiedConsciousnessDashboardProps> = ({ state }) => {
    if (!state) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="text-muted-foreground">Loading unified consciousness...</div>
            </div>
        );
    }

    const { navagraha, tattva, ooda_cycle, components } = state;

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div>
                    <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                        <Brain className="w-6 h-6 text-brand-purple" />
                        Unified Consciousness
                    </h2>
                    <p className="text-sm text-muted-foreground mt-1">
                        Integrated OODA + 36-Tattva + Navagraha system
                    </p>
                </div>
                <div className="flex items-center gap-2">
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                        navagraha.trading_gate_open 
                            ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' 
                            : 'bg-red-500/20 text-red-400 border border-red-500/30'
                    }`}>
                        {navagraha.trading_gate_open ? '🟢 Trading Gate Open' : '🔴 Trading Gate Closed'}
                    </span>
                </div>
            </div>

            {/* Component Status Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <StatusCard
                    title="Cognitive Orchestrator"
                    status={components.cognitive_orchestrator}
                    icon={<Sparkles className="w-5 h-5" />}
                    description="Message bus & agent registry"
                />
                <StatusCard
                    title="System Identity"
                    status={components.system_identity}
                    icon={<Brain className="w-5 h-5" />}
                    description="36-Tattva consciousness"
                />
                <StatusCard
                    title="Risk Orchestrator"
                    status={components.risk_orchestrator}
                    icon={<Shield className="w-5 h-5" />}
                    description="Pre-trade validation"
                />
                <StatusCard
                    title="Karma Register"
                    status={components.karma_register}
                    icon={<TrendingUp className="w-5 h-5" />}
                    description="Learning feedback loop"
                />
            </div>

            {/* Main Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Left Column */}
                <div className="space-y-6">
                    {/* OODA Cycle */}
                    <OODATransparency cycle={ooda_cycle} />

                    {/* Tattva Monitor */}
                    <TattvaMonitor state={tattva} />
                </div>

                {/* Right Column */}
                <div className="space-y-6">
                    {/* Guna Distribution */}
                    <GunaDistribution
                        guna={navagraha.guna}
                        consciousness_level={navagraha.consciousness_level}
                    />

                    {/* Navagraha Wheel */}
                    <div className="bg-card border border-border rounded-xl p-6 backdrop-blur-md">
                        <h3 className="text-lg font-bold text-white flex items-center gap-2 mb-4">
                            <Activity className="w-5 h-5 text-brand-purple" />
                            Navagraha Positions
                        </h3>
                        <NavagrahaWheel planets={navagraha.planets} />
                    </div>
                </div>
            </div>

            {/* Rahu Kala Gate Modal */}
            <RahuKalaGate rahuKala={navagraha.rahu_kala} />

            {/* Footer Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-white/10">
                <div className="text-center">
                    <div className="text-2xl font-bold font-mono text-white">OODA</div>
                    <div className="text-xs text-muted-foreground">Primary Orchestrator</div>
                </div>
                <div className="text-center">
                    <div className="text-2xl font-bold font-mono text-white">36</div>
                    <div className="text-xs text-muted-foreground">Tattva Layers</div>
                </div>
                <div className="text-center">
                    <div className="text-2xl font-bold font-mono text-white">9</div>
                    <div className="text-xs text-muted-foreground">Grahas (Planets)</div>
                </div>
                <div className="text-center">
                    <div className="text-2xl font-bold font-mono text-white">1</div>
                    <div className="text-xs text-muted-foreground">Unified Body</div>
                </div>
            </div>
        </div>
    );
};

export default UnifiedConsciousnessDashboard;
