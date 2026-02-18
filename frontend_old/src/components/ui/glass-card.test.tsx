import { render, screen } from "@testing-library/react";
import { GlassCard } from "./glass-card";
import { describe, it, expect } from "vitest";

describe("GlassCard Component", () => {
    // Happy Path
    it("renders children correctly", () => {
        render(<GlassCard>Test Content</GlassCard>);
        expect(screen.getByText("Test Content")).toBeDefined();
    });

    it("applies glass utility classes by default", () => {
        const { container } = render(<GlassCard>Content</GlassCard>);
        // Look for the 'glass-card' utility class we defined in globals.css
        expect(container.firstChild).toHaveClass("glass-card");
    });

    it("accepts and merges custom className", () => {
        const { container } = render(<GlassCard className="custom-class">Content</GlassCard>);
        expect(container.firstChild).toHaveClass("glass-card");
        expect(container.firstChild).toHaveClass("custom-class");
    });

    // Unhappy Path / Edge Cases
    it("renders with no children gracefully", () => {
        const { container } = render(<GlassCard />);
        expect(container.firstChild).toBeDefined();
        expect(container.firstChild).toHaveClass("glass-card");
    });
});
