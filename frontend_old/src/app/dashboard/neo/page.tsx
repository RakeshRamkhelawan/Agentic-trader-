'use client';

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { NavagrahaWheel } from '@/components/dashboard/NavagrahaWheel';
import { AgentPranaCards } from '@/components/dashboard/AgentPranaCards';
import { OODATransparency } from '@/components/dashboard/OODATransparency';
import { RahuKalaGate } from '@/components/dashboard/RahuKalaGate';
import { useRealtimeNavagraha } from '@/lib/hooks/useRealtime';
import { Shield, Activity, Zap } from 'lucide-react';

export default function NeoDashboard() {
    // Integrate Real-time Hooks
    const { ready } = useRealtimeNavagraha();

    // Fetch initial dashboard data
    const { data, isLoading, error } = useQuery({
        queryKey: ['dashboard', 'neo'],
        queryFn: async () => {
            const res = await fetch('/api/dashboard/neo');
            if (!res.ok) throw new Error('Failed to fetch dashboard data');
            return res.json();
        },
        refetchInterval: 30000,
    });

    if (isLoading) {
        return (
            <div className="flex h-screen items-center justify-center bg-black text-white">
                <div className="flex flex-col items-center gap-4">
                    <div className="w-12 h-12 border-4 border-brand-blue border-t-transparent rounded-full animate-spin"></div>
                    <p className="animate-pulse">Loading Neuromantic Interface...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex h-screen items-center justify-center bg-black text-destructive">
                Error loading dashboard: {(error as Error).message}
            </div>
        );
    }

    const { navagraha, agents, ooda } = data;

    return (
        <div className="min-h-screen bg-black text-white p-6 md:p-8 font-sans selection:bg-brand-blue/30 selection:text-brand-blue">
            {/* Rahu Kala Overlay */}
            {navagraha?.rahu_kala && <RahuKalaGate rahuKala={navagraha.rahu_kala} />}

            {/* Header */}
            <header className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4 border-b border-white/10 pb-6">
                <div>
                    <h1 className="text-3xl font-bold tracking-tighter bg-gradient-to-r from-white to-white/50 bg-clip-text text-transparent">
                        NEO TRADER
                    </h1>
                    <p className="text-sm text-muted-foreground flex items-center gap-2 mt-1">
                        <span className={`w-2 h-2 rounded-full ${ready ? 'bg-positive' : 'bg-destructive'}`}></span>
                        {ready ? 'Neural Link Active' : 'Connecting to Cortex...'}
                    </p>
                </div>

                <div className="flex gap-6">
                    {/* Guna Ratios Widget */}
                    <div className="flex flex-col gap-1 items-end">
                        <span className="text-xs text-muted-foreground uppercase tracking-wider">Guna Balance</span>
                        <div className="flex h-2 w-32 rounded-full overflow-hidden bg-white/10">
                            <div style={{ width: `${navagraha?.guna_ratios?.sattva * 100}%` }} className="bg-sattva h-full" title="Sattva" />
                            <div style={{ width: `${navagraha?.guna_ratios?.rajas * 100}%` }} className="bg-rajas h-full" title="Rajas" />
                            <div style={{ width: `${navagraha?.guna_ratios?.tamas * 100}%` }} className="bg-tamas h-full" title="Tamas" />
                        </div>
                    </div>

                    {/* Dasha Widget */}
                    <div className="hidden md:flex flex-col gap-1 items-end">
                        <span className="text-xs text-muted-foreground uppercase tracking-wider">Current Dasha</span>
                        <div className="flex items-center gap-2 font-mono text-sm">
                            <span className="text-brand-purple font-bold">{navagraha?.current_dasha?.planet}</span>
                            <span className="text-muted-foreground">/</span>
                            <span className="text-white/70">{navagraha?.current_dasha?.sub_period}</span>
                        </div>
                    </div>
                </div>
            </header>

            {/* Main Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

                {/* Left Column: Navagraha (Zodiac) */}
                <div className="lg:col-span-4 xl:col-span-3">
                    <div className="bg-card border border-white/5 rounded-2xl p-6 h-full flex flex-col items-center justify-center relative overflow-hidden group">
                        <div className="absolute inset-0 bg-gradient-to-b from-brand-blue/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                        <h2 className="text-xl font-semibold mb-6 z-10 flex items-center gap-2">
                            <Activity className="w-5 h-5 text-brand-blue" />
                            Cosmic Alignment
                        </h2>
                        <div className="scale-90 md:scale-100 transition-transform duration-500 hover:scale-105 z-10">
                            {navagraha?.planets && <NavagrahaWheel planets={navagraha.planets} />}
                        </div>
                        <div className="mt-6 text-center z-10">
                            <p className="text-xs text-muted-foreground">
                                Next Transition: <span className="text-white font-mono">2d 14h</span>
                            </p>
                        </div>
                    </div>
                </div>

                {/* Center/Right Column: OODA + Agents */}
                <div className="lg:col-span-8 xl:col-span-9 flex flex-col gap-6">

                    {/* OODA Loop Section */}
                    <div className="relative">
                        <div className="absolute -left-1 top-1/2 w-1 h-12 bg-gradient-to-b from-transparent via-brand-blue to-transparent transform -translate-y-1/2 opacity-50" />
                        {ooda && <OODATransparency cycle={ooda} />}
                    </div>

                    {/* Elemental Agents Section */}
                    <div>
                        <div className="flex items-center justify-between mb-4 px-1">
                            <h2 className="text-lg font-semibold flex items-center gap-2">
                                <Shield className="w-5 h-5 text-brand-green" />
                                Autonomous Agents
                            </h2>
                            <span className="text-xs text-muted-foreground bg-white/5 px-2 py-1 rounded-full border border-white/5">
                                System Health: <span className="text-brand-green">98.4%</span>
                            </span>
                        </div>
                        {agents?.agents && <AgentPranaCards agents={agents.agents} />}
                    </div>

                    {/* Metrics / Strategy (Placeholder for future expansion) */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="bg-white/5 border border-white/5 rounded-xl p-6 hover:bg-white/[0.07] transition-colors cursor-pointer group">
                            <div className="flex justify-between items-start mb-4">
                                <div className="p-2 rounded-lg bg-brand-purple/10 text-brand-purple group-hover:scale-110 transition-transform">
                                    <Zap className="w-6 h-6" />
                                </div>
                                <span className="text-xs font-mono text-muted-foreground">Active Strategy</span>
                            </div>
                            <h3 className="text-2xl font-bold mb-1">Mars Trend Following</h3>
                            <p className="text-sm text-muted-foreground">Aggression: High • Leverage: 3x</p>
                        </div>

                        <div className="bg-white/5 border border-white/5 rounded-xl p-6 hover:bg-white/[0.07] transition-colors cursor-pointer group">
                            <div className="flex justify-between items-start mb-4">
                                <div className="p-2 rounded-lg bg-brand-orange/10 text-brand-orange group-hover:scale-110 transition-transform">
                                    <Activity className="w-6 h-6" />
                                </div>
                                <span className="text-xs font-mono text-muted-foreground">Performance (24h)</span>
                            </div>
                            <h3 className="text-2xl font-bold mb-1 text-positive">+4.2%</h3>
                            <p className="text-sm text-muted-foreground">PnL: $1,240.50 • Win Rate: 68%</p>
                        </div>
                    </div>

                </div>
            </div>
        </div>
    );
}
