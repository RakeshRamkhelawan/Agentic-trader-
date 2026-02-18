import { NextResponse } from 'next/server';

export async function GET() {
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000/api/v1';

    try {
        const [navagrahaRes, agentsRes, oodaRes] = await Promise.all([
            fetch(`${backendUrl}/navagraha/current-state`, { cache: 'no-store' }),
            fetch(`${backendUrl}/agents/status`, { cache: 'no-store' }),
            fetch(`${backendUrl}/ooda/current-cycle`, { cache: 'no-store' }),
        ]);

        if (!navagrahaRes.ok || !agentsRes.ok || !oodaRes.ok) {
            throw new Error("One or more backend services failed");
        }

        const navagrahaData = await navagrahaRes.json();
        const agentsData = await agentsRes.json();
        const oodaData = await oodaRes.json();

        // Transform Navagraha
        const planetsList = Object.values(navagrahaData.planets).map((p: any) => ({
            name: p.name,
            longitude: p.longitude,
            latitude: p.latitude,
            speed: p.speed,
            is_retrograde: p.is_retrograde,
            zodiac_sign: p.zodiac_sign,
            house: Math.floor(p.longitude / 30) + 1
        }));

        const navagraha = {
            planets: planetsList,
            guna_ratios: navagrahaData.guna_distribution,
            rahu_kala: {
                is_active: navagrahaData.rahu_kala_active,
                start_time: new Date().toISOString(), // Fallback
                end_time: new Date().toISOString(),
                remaining_minutes: 0
            },
            current_dasha: {
                planet: navagrahaData.current_dasha || "Unknown",
                sub_period: "Unknown",
                remaining_days: 0,
                end_date: new Date().toISOString()
            },
            calculated_at: navagrahaData.calculated_at
        };

        // Transform Agents
        const agents = agentsData.agents ? agentsData.agents : []; // Backend returns { agents: [] } or just []? Backend returns dict of agents.
        // Backend `agents_api.py` returns `List[AgentStatus]`.
        // Let's assume it returns list.
        // Wait, `agents_api.py` logic: `return [agent.model_dump(...) for agent in agents]`
        // So it returns a list directly.

        // Transform OODA
        // Backend `ooda_api.py` returns schema `OODACycle`.
        const ooda = {
            current_phase: oodaData.phase,
            phase_status: {
                observe: oodaData.phase === 'OBSERVE' ? 'active' : 'completed',
                orient: oodaData.phase === 'ORIENT' ? 'active' : (oodaData.phase === 'OBSERVE' ? 'pending' : 'completed'),
                decide: oodaData.phase === 'DECIDE' ? 'active' : (['OBSERVE', 'ORIENT'].includes(oodaData.phase) ? 'pending' : 'completed'),
                act: oodaData.phase === 'ACT' ? 'active' : 'pending',
            },
            cycle_id: oodaData.cycle_id,
            navagraha_influence: "Neutral" // Placeholder
        };

        const dashboard = {
            navagraha,
            agents: { agents: agents }, // Frontend expects { agents: [...] } structure in some components? or just [...]?
            // `dashboard/neo/page.tsx` likely passes these to components.
            // `AgentPranaCards` takes `agents` prop.
            // Let's match the structure from `api/agents/status/route.ts` which returns `{ agents: ... }` wrapper?
            // Checking `api/agents/status/route.ts` in step 1242:
            // It mapped backend list to `transformedAgents` and returned `NextResponse.json({ agents: transformedAgents })`.
            // So yes, wrapper needed.
            ooda,
            timestamp: new Date().toISOString(),
        };

        return NextResponse.json(dashboard);
    } catch (error) {
        console.error("Error fetching dashboard data:", error);
        return NextResponse.json({ error: "Failed to fetch dashboard data" }, { status: 500 });
    }
}
