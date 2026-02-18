import { render, screen } from "@testing-library/react";
import { Sidebar } from "./sidebar";
import { describe, it, expect, vi } from "vitest";

// Mock next/navigation
vi.mock("next/navigation", () => ({
    usePathname: () => "/terminal",
}));

// Mock useAuth
vi.mock("@/context/auth-context", () => ({
    useAuth: () => ({
        isAuthenticated: true,
        login: vi.fn(),
        logout: vi.fn(),
        user: { name: "Test User" },
        isLoading: false,
    }),
}));

describe("Sidebar Component", () => {
    it("renders navigation items", () => {
        render(<Sidebar />);
        // Check for some icons or links. Since icons are SVGs, we can look for specific identifying attributes or just the presence of links.
        const links = screen.getAllByRole("link");
        expect(links.length).toBeGreaterThan(0);
    });

    it("has fixed width of w-16 (icons only)", () => {
        const { container } = render(<Sidebar />);
        const sidebar = container.querySelector("aside");
        expect(sidebar).toHaveClass("w-16");
        expect(sidebar).not.toHaveClass("w-56"); // Should not be expanded
    });

    it("renders the Logo as an icon/mark", () => {
        render(<Sidebar />);
        // Check for the logo text which is sr-only
        expect(screen.getByText("AgenticTrader Logo")).toBeInTheDocument();
    });
});
