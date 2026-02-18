'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Planet } from '@/lib/stores/navagrahaStore';

interface NavagrahaWheelProps {
    planets: Planet[];
}

const zodiacSigns = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces"
];

const getPlanetColor = (name: string) => {
    switch (name) {
        case 'Sun': return '#FFD700'; // Gold
        case 'Moon': return '#C0C0C0'; // Silver
        case 'Mars': return '#FF4500'; // Red-Orange
        case 'Mercury': return '#32CD32'; // Lime Green
        case 'Jupiter': return '#FFA500'; // Orange
        case 'Venus': return '#FF69B4'; // Hot Pink
        case 'Saturn': return '#4169E1'; // Royal Blue
        case 'Rahu': return '#4B0082'; // Indigo
        case 'Ketu': return '#808080'; // Gray
        default: return '#FFFFFF';
    }
};

export const NavagrahaWheel: React.FC<NavagrahaWheelProps> = ({ planets }) => {
    const radius = 180;
    const center = 200;

    return (
        <div className="relative w-full max-w-[400px] aspect-square mx-auto">
            <svg viewBox="0 0 400 400" className="w-full h-full">
                {/* Zodiac Circle Background */}
                <circle cx={center} cy={center} r={radius} fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth="2" />

                {/* Zodiac Divisions */}
                {[...Array(12)].map((_, i) => {
                    const angle = (i * 30 - 90) * (Math.PI / 180);
                    const x1 = center + (radius - 10) * Math.cos(angle);
                    const y1 = center + (radius - 10) * Math.sin(angle);
                    const x2 = center + radius * Math.cos(angle);
                    const y2 = center + radius * Math.sin(angle);
                    return (
                        <g key={i}>
                            <line x1={x1} y1={y1} x2={x2} y2={y2} stroke="rgba(255,255,255,0.3)" strokeWidth="1" />
                            <text
                                x={center + (radius + 20) * Math.cos(angle + (15 * Math.PI / 180))}
                                y={center + (radius + 20) * Math.sin(angle + (15 * Math.PI / 180))}
                                textAnchor="middle"
                                dominantBaseline="middle"
                                fill="rgba(255,255,255,0.5)"
                                fontSize="10"
                                className="uppercase tracking-wider"
                            >
                                {zodiacSigns[i].substring(0, 3)}
                            </text>
                        </g>
                    )
                })}

                {/* Inner Rings */}
                <circle cx={center} cy={center} r={radius * 0.7} fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="1" />
                <circle cx={center} cy={center} r={radius * 0.4} fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="1" />

                {/* Planets */}
                {planets.map((planet) => {
                    // Adjust longitude to start Aries at 0 degrees at 3 o'clock, 
                    // or standard astrological chart where Aries Ascendant is usually 9 o'clock.
                    // Let's stick to standard polar coordinates: 0 is 3 o'clock.
                    // In charts, usually 0 Aries is 9 o'clock (180 deg) or top (270 deg).
                    // Let's assume 0 Aries is at 9 o'clock (Left) for North Indian or standard circular.
                    // Actually, let's just map 0-360 directly to the circle starting from top (270 deg).
                    // So 0 deg = -90 deg in SVG.

                    const angle = (planet.longitude - 90) * (Math.PI / 180);
                    const planetRadius = radius * 0.85; // Place planets inside the ring
                    const x = center + planetRadius * Math.cos(angle);
                    const y = center + planetRadius * Math.sin(angle);

                    return (
                        <motion.g
                            key={planet.name}
                            initial={{ opacity: 0, scale: 0 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ duration: 0.5, delay: 0.1 }}
                        >
                            {/* Retrograde Halo */}
                            {planet.is_retrograde && (
                                <circle cx={x} cy={y} r="12" fill="none" stroke="rgba(255, 0, 0, 0.5)" strokeWidth="1" strokeDasharray="2 2" />
                            )}

                            {/* Planet Dot */}
                            <circle cx={x} cy={y} r="6" fill={getPlanetColor(planet.name)} className="cursor-pointer hover:filter hover:brightness-125 box-shadow-glow" />

                            {/* Planet Label */}
                            <text x={x} y={y + 16} textAnchor="middle" fill="white" fontSize="10" fontWeight="bold">
                                {planet.name}
                            </text>
                            {planet.is_retrograde && (
                                <text x={x} y={y - 10} textAnchor="middle" fill="#FF4976" fontSize="8">R</text>
                            )}
                        </motion.g>
                    );
                })}

                {/* Center Decoration */}
                <circle cx={center} cy={center} r="5" fill="rgba(255,255,255,0.2)" />
            </svg>

            {/* Legend or center info can go here */}
        </div>
    );
};
