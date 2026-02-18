import { NextResponse } from 'next/server';

export async function GET() {
    try {
        const response = await fetch('http://localhost:8000/api/v1/ooda/current-cycle', {
            cache: 'no-store'
        });

        if (!response.ok) {
            throw new Error(`Backend responded with ${response.status}`);
        }

        const backendData = await response.json();
        const currentPhase = backendData.phase || "observe";

        // Helper to determine phase status
        const getStatus = (phaseName: string, activePhase: string) => {
            const phases = ["observe", "orient", "decide", "act"];
            const activeIndex = phases.indexOf(activePhase.toLowerCase());
            const targetIndex = phases.indexOf(phaseName.toLowerCase());

            if (activeIndex > targetIndex) return "completed";
            if (activeIndex === targetIndex) return "in_progress";
            return "pending";
        };

        const data = {
            cycle_id: backendData.cycle_id,
            current_phase: currentPhase.charAt(0).toUpperCase() + currentPhase.slice(1).toLowerCase(),
            phases: {
                Observe: {
                    status: getStatus("observe", currentPhase),
                    duration_ms: 234, // Mock
                    data_collected: {
                        market_data: true,
                        sentiment: true,
                        navagraha_state: true
                    }
                },
                Orient: {
                    status: getStatus("orient", currentPhase),
                    strategy_candidates: ["TrendFollowing", "Breakout"], // Mock
                    selected_strategy: "TrendFollowing", // Mock
                    reason: `Coherence: ${(backendData.coherence * 100).toFixed(1)}%`
                },
                Decide: {
                    status: getStatus("decide", currentPhase),
                    confidence: backendData.confidence
                },
                Act: {
                    status: getStatus("act", currentPhase)
                }
            },
            navagraha_influence: {
                dasha_selected_strategy: true, // Mock
                guna_modulated_risk: "active",
                rahu_kala_blocked: false // Mock
            }
        };

        return NextResponse.json(data);
    } catch (error) {
        console.error("Error fetching OODA cycle:", error);
        // Fallback or Error Response
        return NextResponse.json(
            { error: "Failed to fetch real OODA cycle", details: String(error) },
            { status: 500 }
        );
    }
}
