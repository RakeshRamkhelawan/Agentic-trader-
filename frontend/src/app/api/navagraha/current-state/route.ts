import { NextResponse } from 'next/server';

export async function GET() {
    try {
        const response = await fetch('http://localhost:8000/api/v1/navagraha/current-state', {
            cache: 'no-store'
        });

        if (!response.ok) {
            throw new Error(`Backend responded with ${response.status}`);
        }

        const backendData = await response.json();

        // Transform Backend Data to Frontend Format
        const planetsList = Object.values(backendData.planets).map((p: any) => ({
            name: p.name,
            longitude: p.longitude,
            latitude: p.latitude,
            speed: p.speed,
            is_retrograde: p.is_retrograde,
            zodiac_sign: p.zodiac_sign,
            house: Math.floor(p.longitude / 30) + 1 // Simple house calculation approximation
        }));

        const data = {
            planets: planetsList,
            guna_ratios: backendData.guna_distribution,
            rahu_kala: {
                is_active: backendData.rahu_kala_active,
                // Fallback for missing backend fields
                start_time: new Date().toISOString(),
                end_time: new Date().toISOString(),
                remaining_minutes: 0
            },
            current_dasha: {
                planet: backendData.current_dasha || "Unknown",
                sub_period: "Unknown",
                remaining_days: 0,
                end_date: new Date().toISOString()
            },
            calculated_at: backendData.calculated_at
        };

        return NextResponse.json(data);
    } catch (error) {
        console.error("Error fetching Navagraha state:", error);
        // Fallback or Error Response
        return NextResponse.json(
            { error: "Failed to fetch real Navagraha state", details: String(error) },
            { status: 500 }
        );
    }
}
