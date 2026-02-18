'use client';

import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertOctagon, X } from 'lucide-react';
import { RahuKala } from '@/lib/stores/navagrahaStore';

interface RahuKalaGateProps {
    rahuKala: RahuKala;
}

export const RahuKalaGate: React.FC<RahuKalaGateProps> = ({ rahuKala }) => {
    const [isVisible, setIsVisible] = useState(false);

    useEffect(() => {
        if (rahuKala?.is_active) {
            setIsVisible(true);
        } else {
            setIsVisible(false);
        }
    }, [rahuKala?.is_active]);

    return (
        <AnimatePresence>
            {isVisible && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4"
                >
                    <motion.div
                        initial={{ scale: 0.9, y: 20 }}
                        animate={{ scale: 1, y: 0 }}
                        exit={{ scale: 0.9, y: 20 }}
                        className="bg-card border-2 border-destructive/50 text-card-foreground p-8 rounded-2xl max-w-md w-full shadow-2xl relative overflow-hidden"
                    >
                        {/* Background Glow */}
                        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-destructive to-transparent opacity-50" />
                        <div className="absolute -top-20 -left-20 w-40 h-40 bg-destructive/10 rounded-full blur-3xl" />

                        <div className="flex flex-col items-center text-center relative z-10">
                            <div className="w-16 h-16 rounded-full bg-destructive/10 flex items-center justify-center mb-6 animate-pulse-slow">
                                <AlertOctagon className="w-8 h-8 text-destructive" />
                            </div>

                            <h2 className="text-2xl font-bold mb-2">Trading Blocked</h2>
                            <p className="text-destructive font-medium mb-6 uppercase tracking-widest text-sm">Rahu Kala Active</p>

                            <div className="bg-white/5 rounded-lg p-6 w-full mb-6 border border-white/5">
                                <p className="text-muted-foreground text-sm mb-2">Trading resumes in</p>
                                <div className="text-4xl font-mono font-bold text-white mb-2">
                                    00:{rahuKala.remaining_minutes}:00
                                </div>
                                <div className="text-xs text-muted-foreground flex justify-between px-4 mt-4 pt-4 border-t border-white/5">
                                    <span>Start: {new Date(rahuKala.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                                    <span>End: {new Date(rahuKala.end_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                                </div>
                            </div>

                            <p className="text-xs text-muted-foreground max-w-xs">
                                The inauspicious Rahu Kala period aligns with Vedic timing principles to prevent unfavorable trade outcomes.
                            </p>

                            <button
                                onClick={() => setIsVisible(false)}
                                className="absolute top-0 right-0 p-2 text-muted-foreground hover:text-white"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>
                    </motion.div>
                </motion.div>
            )}
        </AnimatePresence>
    );
};
