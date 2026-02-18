import { NextResponse } from 'next/server';

export async function GET() {
    try {
        const response = await fetch('http://localhost:8000/api/v1/agents/status', {
            cache: 'no-store'
        });

        if (!response.ok) {
            throw new Error(`Backend responded with ${response.status}`);
        }

        const backendData = await response.json();

        // Element mapping helper
        const getElement = (agentType: string) => {
            if (agentType.includes("Prithvi")) return "earth";
            if (agentType.includes("Jala")) return "water";
            if (agentType.includes("Agni")) return "fire";
            if (agentType.includes("Vayu")) return "air";
            if (agentType.includes("Akasha") || agentType.includes("Orchestrator")) return "ether";
            if (agentType.includes("Research")) return "air"; // Research is Vayu-like
            if (agentType.includes("Risk")) return "earth"; // Risk is Prithvi-like
            if (agentType.includes("Execution")) return "fire"; // Exec is Agni-like
            if (agentType.includes("Strategy")) return "air"; // Strategy is Vayu-like
            if (agentType.includes("Sentiment")) return "water"; // Sentiment is Jala-like
            return "ether";
        };

        const agentsList = Object.values(backendData.agents).map((a: any) => ({
            element: getElement(a.type),
            name: a.id.replace("_v1", "").replace(/_/g, " "), // Humanize ID
            prana_level: (a.prana || 1.0) * 100, // Convert 0-1 to 0-100
            active: a.is_active,
            last_signal: new Date().toISOString(), // Mock for now
            recent_contributions: Math.floor(Math.random() * 10) // Mock for now
        }));

        // Determine dominant guna
        const gunas = backendData.orchestrator_state.guna_balance;
        let dominant = "sattva";
        if (gunas.rajas > gunas.sattva && gunas.rajas > gunas.tamas) dominant = "rajas";
        if (gunas.tamas > gunas.sattva && gunas.tamas > gunas.rajas) dominant = "tamas";

        const data = {
            agents: agentsList,
            guna_influence: {
                dominant_guna: dominant,
                prana_decay_rate: 0.05 // Static for now
            }
        };

        return NextResponse.json(data);
    } catch (error) {
        console.error("Error fetching Agents status:", error);
        // Fallback or Error Response
        return NextResponse.json(
            { error: "Failed to fetch real Agents status", details: String(error) },
            { status: 500 }
        );
    }
}
