import { create } from 'zustand';
import { 
    UnifiedConsciousnessState, 
    NavagrahaState, 
    Planet, 
    RahuKala,
    TattvaState,
    TattvaLayer,
} from '@/components/dashboard/UnifiedConsciousnessDashboard';
import { OODACycle } from '@/components/dashboard/OODATransparency';
import { GunaVector } from '@/components/dashboard/GunaDistribution';

// Generate mock Tattva layers
const generateTattvaLayers = (): TattvaLayer[] => {
    const layers: TattvaLayer[] = [];
    
    // Layer names based on 36-Tattva system
    const layerNames: Record<number, string> = {
        1: 'Shiva', 2: 'Shakti', 3: 'Sadashiva', 4: 'Isvara', 5: 'Shuddha Vidya',
        6: 'Kala', 7: 'Niyati', 8: 'Raga', 9: 'Vidya', 10: 'Kala', 11: 'Maya',
        12: 'Purusha', 13: 'Prakriti', 14: 'Buddhi', 15: 'Ahamkara',
        16: 'Sound', 17: 'Touch', 18: 'Sight', 19: 'Taste', 20: 'Smell',
        21: 'Ear', 22: 'Skin', 23: 'Eye', 24: 'Tongue', 25: 'Nose',
        26: 'Speech', 27: 'Hand', 28: 'Foot', 29: 'Anus', 30: 'Genital',
        31: 'Mind', 32: 'Ether', 33: 'Air', 34: 'Fire', 35: 'Water', 36: 'Earth'
    };
    
    for (let i = 1; i <= 36; i++) {
        // Random coherence between 0.5 and 1.0
        const coherence = 0.5 + Math.random() * 0.5;
        // Active layers based on coherence
        const active = coherence > 0.7;
        
        layers.push({
            layer_number: i,
            name: layerNames[i] || `Layer ${i}`,
            coherence,
            active,
        });
    }
    
    return layers;
};

// Generate mock planets
const generatePlanets = (): Planet[] => [
    { name: 'Sun', longitude: 45 + Math.random() * 30, is_retrograde: false },
    { name: 'Moon', longitude: 120 + Math.random() * 30, is_retrograde: false },
    { name: 'Mars', longitude: 200 + Math.random() * 30, is_retrograde: Math.random() > 0.5 },
    { name: 'Mercury', longitude: 60 + Math.random() * 30, is_retrograde: Math.random() > 0.7 },
    { name: 'Jupiter', longitude: 280 + Math.random() * 30, is_retrograde: Math.random() > 0.5 },
    { name: 'Venus', longitude: 150 + Math.random() * 30, is_retrograde: Math.random() > 0.7 },
    { name: 'Saturn', longitude: 320 + Math.random() * 30, is_retrograde: Math.random() > 0.5 },
    { name: 'Rahu', longitude: 180, is_retrograde: true },
    { name: 'Ketu', longitude: 0, is_retrograde: true },
];

// Generate mock Rahu Kala
const generateRahuKala = (): RahuKala => {
    const isActive = Math.random() > 0.9; // 10% chance of being active
    const now = new Date();
    
    if (isActive) {
        return {
            is_active: true,
            start_time: new Date(now.getTime() - 30 * 60000).toISOString(),
            end_time: new Date(now.getTime() + 60 * 60000).toISOString(),
            remaining_minutes: 60,
        };
    }
    
    return {
        is_active: false,
        start_time: '',
        end_time: '',
        remaining_minutes: 0,
    };
};

// Generate mock Guna
const generateGuna = (): GunaVector => {
    const sattva = 0.3 + Math.random() * 0.4; // 30-70%
    const rajas = 0.2 + Math.random() * 0.3;  // 20-50%
    const tamas = 1 - sattva - rajas;         // Remainder
    
    return {
        sattva: Math.max(0, sattva),
        rajas: Math.max(0, rajas),
        tamas: Math.max(0, tamas),
    };
};

// Generate consciousness level based on guna
const getConsciousnessLevel = (guna: GunaVector): string => {
    if (guna.sattva >= 0.6) return 'Pure Awareness';
    if (guna.sattva >= 0.4) return 'Discriminative Intelligence';
    if (guna.sattva >= 0.25) return 'Active Manifestation';
    return 'Material Density';
};

// Generate mock OODA cycle
const generateOODACycle = (): OODACycle => {
    const phases = ['Observe', 'Orient', 'Decide', 'Act'] as const;
    const currentPhase = phases[Math.floor(Math.random() * phases.length)];
    
    return {
        cycle_id: `cycle_${Date.now()}`,
        current_phase: currentPhase,
        phases: {
            Observe: {
                status: currentPhase === 'Observe' ? 'in_progress' : 'completed',
                duration_ms: Math.floor(Math.random() * 100),
            },
            Orient: {
                status: currentPhase === 'Orient' ? 'in_progress' : 
                       phases.indexOf(currentPhase) > phases.indexOf('Orient') ? 'completed' : 'pending',
                duration_ms: Math.floor(Math.random() * 200),
                selected_strategy: 'trend_following',
            },
            Decide: {
                status: currentPhase === 'Decide' ? 'in_progress' :
                       phases.indexOf(currentPhase) > phases.indexOf('Decide') ? 'completed' : 'pending',
                duration_ms: Math.floor(Math.random() * 150),
            },
            Act: {
                status: currentPhase === 'Act' ? 'in_progress' :
                       phases.indexOf(currentPhase) > phases.indexOf('Act') ? 'completed' : 'pending',
                duration_ms: Math.floor(Math.random() * 50),
            },
        },
        navagraha_influence: {
            dasha_selected_strategy: true,
            guna_modulated_risk: 'low',
            rahu_kala_blocked: false,
        },
    };
};

// Initial state
const generateInitialState = (): UnifiedConsciousnessState => {
    const guna = generateGuna();
    const tattvaLayers = generateTattvaLayers();
    const kanchukaCoherence = tattvaLayers
        .filter(l => l.layer_number >= 6 && l.layer_number <= 12)
        .reduce((sum, l) => sum + l.coherence, 0) / 7;
    
    return {
        navagraha: {
            planets: generatePlanets(),
            rahu_kala: generateRahuKala(),
            guna,
            consciousness_level: getConsciousnessLevel(guna),
            trading_gate_open: guna.tamas < 0.6,
        },
        tattva: {
            layers: tattvaLayers,
            overall_coherence: tattvaLayers.reduce((sum, l) => sum + l.coherence, 0) / tattvaLayers.length,
            kanchuka_gate_open: kanchukaCoherence > 0.7,
            current_traversal: 'Ascend → Filter → Interface → Sense → Decide → Act → Materialize → Descend',
        },
        ooda_cycle: generateOODACycle(),
        components: {
            cognitive_orchestrator: true,
            risk_orchestrator: true,
            karma_register: true,
            system_identity: true,
        },
    };
};

interface UnifiedConsciousnessStore {
    state: UnifiedConsciousnessState;
    refresh: () => void;
    setComponentStatus: (component: keyof UnifiedConsciousnessState['components'], status: boolean) => void;
}

export const useUnifiedConsciousness = create<UnifiedConsciousnessStore>((set) => ({
    state: generateInitialState(),
    
    refresh: () => {
        set({ state: generateInitialState() });
    },
    
    setComponentStatus: (component, status) => {
        set((store) => ({
            state: {
                ...store.state,
                components: {
                    ...store.state.components,
                    [component]: status,
                },
            },
        }));
    },
}));

export default useUnifiedConsciousness;
