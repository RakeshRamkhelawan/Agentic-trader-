import React from 'react';
import { render, screen } from '@testing-library/react';
import { GunaDistribution, GunaVector } from '../GunaDistribution';

describe('GunaDistribution', () => {
    const mockGuna: GunaVector = {
        sattva: 0.5,
        rajas: 0.3,
        tamas: 0.2,
    };

    it('renders without crashing', () => {
        render(<GunaDistribution guna={mockGuna} />);
        expect(screen.getByText('Guna Distribution')).toBeInTheDocument();
    });

    it('displays correct percentages', () => {
        render(<GunaDistribution guna={mockGuna} />);
        expect(screen.getByText('50.0%')).toBeInTheDocument(); // Sattva
        expect(screen.getByText('30.0%')).toBeInTheDocument(); // Rajas
        expect(screen.getByText('20.0%')).toBeInTheDocument(); // Tamas
    });

    it('shows dominant guna', () => {
        render(<GunaDistribution guna={mockGuna} />);
        expect(screen.getByText('sattva')).toBeInTheDocument();
    });

    it('shows consciousness level when provided', () => {
        render(
            <GunaDistribution 
                guna={mockGuna} 
                consciousness_level="Pure Awareness"
            />
        );
        expect(screen.getByText('Pure Awareness')).toBeInTheDocument();
    });

    it('shows balance score when provided', () => {
        render(
            <GunaDistribution 
                guna={mockGuna} 
                balance_score={0.85}
            />
        );
        expect(screen.getByText('85.0%')).toBeInTheDocument();
    });

    it('shows trading gate open when tamas is low', () => {
        render(<GunaDistribution guna={mockGuna} />);
        expect(screen.getByText('OPEN')).toBeInTheDocument();
    });

    it('shows trading gate blocked when tamas is high', () => {
        const highTamasGuna: GunaVector = {
            sattva: 0.2,
            rajas: 0.1,
            tamas: 0.7,
        };
        render(<GunaDistribution guna={highTamasGuna} />);
        expect(screen.getByText('BLOCKED (High Tamas)')).toBeInTheDocument();
    });

    it('displays warning for high tamas', () => {
        const highTamasGuna: GunaVector = {
            sattva: 0.2,
            rajas: 0.1,
            tamas: 0.7,
        };
        render(<GunaDistribution guna={highTamasGuna} />);
        expect(screen.getByText(/High Tamas detected/)).toBeInTheDocument();
    });

    it('shows all three guna descriptions', () => {
        render(<GunaDistribution guna={mockGuna} />);
        expect(screen.getByText('Harmony, Wisdom, Clarity')).toBeInTheDocument();
        expect(screen.getByText('Activity, Passion, Movement')).toBeInTheDocument();
        expect(screen.getByText('Inertia, Darkness, Resistance')).toBeInTheDocument();
    });

    it('handles null guna gracefully', () => {
        const { container } = render(<GunaDistribution guna={null as any} />);
        expect(container.firstChild).toBeNull();
    });

    it('identifies rajas as dominant when highest', () => {
        const rajasDominant: GunaVector = {
            sattva: 0.2,
            rajas: 0.6,
            tamas: 0.2,
        };
        render(<GunaDistribution guna={rajasDominant} />);
        expect(screen.getByText('rajas')).toBeInTheDocument();
    });

    it('identifies tamas as dominant when highest', () => {
        const tamasDominant: GunaVector = {
            sattva: 0.1,
            rajas: 0.2,
            tamas: 0.7,
        };
        render(<GunaDistribution guna={tamasDominant} />);
        expect(screen.getByText('tamas')).toBeInTheDocument();
    });
});
