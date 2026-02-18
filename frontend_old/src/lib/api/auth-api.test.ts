import { describe, it, expect, vi, beforeEach } from "vitest";
import { authApi } from "./auth-api";

// Mock global fetch
global.fetch = vi.fn();

describe("authApi", () => {
    beforeEach(() => {
        vi.resetAllMocks();
    });

    const mockUser = {
        id: "123",
        email: "test@example.com",
        role: "user",
        tenant_id: "tenant-123",
        full_name: "Test User"
    };

    const mockAuthResponse = {
        access_token: "fake-token",
        token_type: "bearer",
        user: mockUser
    };

    it("login calls correct endpoint and returns auth response", async () => {
        // Setup mock response
        (global.fetch as any).mockResolvedValue({
            ok: true,
            json: async () => mockAuthResponse
        });

        const credentials = { email: "test@example.com", password: "password" };
        const result = await authApi.login(credentials);

        // Verify fetch assertions
        expect(global.fetch).toHaveBeenCalledWith(
            expect.stringContaining("/api/v1/auth/login"),
            expect.objectContaining({
                method: "POST",
                body: JSON.stringify(credentials)
            })
        );

        // Verify result
        expect(result).toEqual(mockAuthResponse);
    });

    it("register calls correct endpoint and returns auth response", async () => {
        // Setup mock response
        (global.fetch as any).mockResolvedValue({
            ok: true,
            json: async () => mockAuthResponse
        });

        const data = {
            email: "test@example.com",
            password: "password",
            full_name: "Test User"
        };
        const result = await authApi.register(data);

        // Verify fetch assertions
        expect(global.fetch).toHaveBeenCalledWith(
            expect.stringContaining("/api/v1/auth/register"),
            expect.objectContaining({
                method: "POST",
                body: JSON.stringify(data)
            })
        );

        // Verify result
        expect(result).toEqual(mockAuthResponse);
    });

    it("throws error on failed request", async () => {
        // Setup mock error response
        (global.fetch as any).mockResolvedValue({
            ok: false,
            json: async () => ({ detail: "Invalid credentials" })
        });

        const credentials = { email: "test@example.com", password: "wrong" };

        await expect(authApi.login(credentials)).rejects.toThrow("Invalid credentials");
    });
});
