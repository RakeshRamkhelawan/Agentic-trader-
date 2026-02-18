import { create } from 'zustand';

// Define the shape of the Navagraha state
export interface Planet {
    name: string;
    longitude: number;
    latitude: number;
    speed: number;
    is_retrograde: boolean;
    zodiac_sign: string;
    house: number;
}

export interface GunaRatios {
    sattva: number;
    rajas: number;
    tamas: number;
}

export interface RahuKala {
    is_active: boolean;
    start_time: string;
    end_time: string;
    remaining_minutes: number;
}

export interface Dasha {
    planet: string;
    sub_period: string;
    remaining_days: number;
    end_date: string;
}

export interface NavagrahaState {
    planets: Planet[];
    guna_ratios: GunaRatios;
    rahu_kala: RahuKala;
    current_dasha: Dasha;
    calculated_at: string;
}

interface NavagrahaStore {
    currentState: NavagrahaState | null;
    setCurrentState: (state: NavagrahaState) => void;
}

export const useNavagrahaStore = create<NavagrahaStore>((set) => ({
    currentState: null,
    setCurrentState: (state) => set({ currentState: state }),
}));
