import React from 'react';
import { render, screen } from '@testing-library/react';
import { TattvaMonitor, TattvaState } from '../TattvaMonitor';

describe('TattvaMonitor', () => {
    const mockTattvaState: TattvaState = {
        layers: Array.from({ length: 36 }, (_, i) => ({
            layer_number: i + 1,
            name: `Layer ${i + 1}`,
            coherence: 0.5 + Math.random() * 0.5,
            active: true,
        })),
        overall_coherence: 0.75,
        kanchuka_gate_open: true,
        current_traversal: 'Ascend',
    };

    it('renders without crashing', () => {
        render(<TattvaMonitor state={mockTattvaState} />);
        expect(screen.getByText('36-Tattva Consciousness')).toBeInTheDocument();
    });

    it('displays overall coherence percentage', () => {
        render(<TattvaMonitor state={mockTattvaState} />);
        expect(screen.getByText('75.0%')).toBeInTheDocument();
    });

    it('shows Kanchuka gate status when open', () => {
        render(<TattvaMonitor state={mockTattvaState} />);
        expect(screen.getByText('Kanchuka Gate OPEN')).toBeInTheDocument();
    });

    it('shows Kanchuka gate status when blocked', () => {
        const blockedState = { ...mockTattvaState, kanchuka_gate_open: false };
        render(<TattvaMonitor state={blockedState} />);
        expect(screen.getByText('Kanchuka Gate BLOCKED')).toBeInTheDocument();
    });

    it('renders all 36 tattva layers', () => {
        render(<TattvaMonitor state={mockTattvaState} />);
        const layers = screen.getAllByTitle(/Layer \d+/);
        expect(layers).toHaveLength(36);
    });

    it('displays group coherence for all 6 groups', () => {
        render(<TattvaMonitor state={mockTattvaState} />);
        expect(screen.getByText('Shuddha (1-5)')).toBeInTheDocument();
        expect(screen.getByText('Kanchuka (6-12)')).toBeInTheDocument();
        expect(screen.getByText('Interface (13-15)')).toBeInTheDocument();
        expect(screen.getByText('Senses (16-25)')).toBeInTheDocument();
        expect(screen.getByText('Actions (26-31)')).toBeInTheDocument();
        expect(screen.getByText('Physical (32-36)')).toBeInTheDocument();
    });

    it('shows current traversal', () => {
        render(<TattvaMonitor state={mockTattvaState} />);
        expect(screen.getByText(/Ascend/)).toBeInTheDocument();
    });

    it('handles null state gracefully', () => {
        const { container } = render(<TattvaMonitor state={null as any} />);
        expect(container.firstChild).toBeNull();
    });
});
