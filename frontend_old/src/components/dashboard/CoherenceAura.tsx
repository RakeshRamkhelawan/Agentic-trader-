"use client"

import * as d3 from 'd3';
import { useEffect, useRef } from 'react';
import { useMetrics } from '@/hooks/useMetrics';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export const CoherenceAura = () => {
    const svgRef = useRef<SVGSVGElement>(null);
    const { data: metrics } = useMetrics();

    useEffect(() => {
        if (!metrics?.mahabhutas_coherence || !svgRef.current) return;

        const svg = d3.select(svgRef.current);
        const width = 400;
        const height = 400;
        const centerX = width / 2;
        const centerY = height / 2;

        // Clear previous render
        svg.selectAll('*').remove();

        const coherenceData = metrics.mahabhutas_coherence as any; // Type assertion until full regen propagate

        // Draw concentric circles for each layer
        const layers = ['L32', 'L33', 'L34', 'L35', 'L36'];

        layers.forEach((layer, i) => {
            const coherence = coherenceData[layer] || 0;
            const radius = 50 + (i * 35);

            // Color logic: Green > 0.8, Yellow > 0.6, Red < 0.6
            const color = coherence > 0.8 ? '#10b981' : coherence > 0.6 ? '#fbbf24' : '#ef4444';

            // Ring
            svg.append('circle')
                .attr('cx', centerX)
                .attr('cy', centerY)
                .attr('r', radius)
                .attr('fill', 'none')
                .attr('stroke', color)
                .attr('stroke-width', 8)
                .attr('opacity', 0.6)
                .transition()
                .duration(1000)
                .attr('opacity', coherence); // Opacity reflects strength

            // Label
            svg.append('text')
                .attr('x', centerX)
                .attr('y', centerY - radius - 8)
                .attr('text-anchor', 'middle')
                .attr('fill', 'currentColor')
                .attr('class', 'text-xs font-mono fill-foreground')
                .text(`${layer}: ${(coherence * 100).toFixed(0)}%`);
        });

        // Center Text
        svg.append('text')
            .attr('x', centerX)
            .attr('y', centerY)
            .attr('dy', '0.3em')
            .attr('text-anchor', 'middle')
            .attr('class', 'text-sm font-bold fill-foreground')
            .text('COHERENCE');

    }, [metrics]);

    return (
        <Card className="w-full max-w-md mx-auto">
            <CardHeader>
                <CardTitle>Mahabhutas Coherence</CardTitle>
            </CardHeader>
            <CardContent className="flex justify-center p-6">
                <svg ref={svgRef} width={400} height={400} viewBox="0 0 400 400" className="w-full h-auto max-w-[400px]" />
            </CardContent>
        </Card>
    );
};
