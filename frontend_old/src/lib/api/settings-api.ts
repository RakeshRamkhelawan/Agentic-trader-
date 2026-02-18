/**
 * Settings API Client - TypeScript client for user settings endpoints.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

// ============================================================================
// Types
// ============================================================================

export type ThemeType = "dark" | "light" | "system";
export type CurrencyType = "EUR" | "USD" | "GBP";
export type ExchangeType = "binance" | "kraken" | "coinbase" | "bitvavo";

export interface UserProfile {
    first_name: string;
    last_name: string;
    email: string | null;
}

export interface NotificationSettings {
    order_executions: boolean;
    price_alerts: boolean;
    ai_signals: boolean;
    security_alerts: boolean;
}

export interface SecuritySettings {
    two_factor_enabled: boolean;
    last_password_change: string | null;
}

export interface Enable2FAResponse {
    secret: string;
    qr_code_url: string;
    backup_codes: string[];
}

export interface AppearanceSettings {
    theme: ThemeType;
}

export interface BrokerAPIKey {
    id: string;
    exchange: ExchangeType;
    api_key_masked: string;
    created_at: string;
    last_used: string | null;
    is_valid: boolean;
}

export interface BrokerAPIKeyList {
    keys: BrokerAPIKey[];
    total: number;
}

export interface BrokerAPIKeyCreate {
    exchange: ExchangeType;
    api_key: string;
    api_secret: string;
    passphrase?: string;
}

export interface UserPreferences {
    default_currency: CurrencyType;
    default_exchange: ExchangeType;
}

export interface AllUserSettings {
    profile: UserProfile;
    notifications: NotificationSettings;
    security: SecuritySettings;
    appearance: AppearanceSettings;
    preferences: UserPreferences;
    api_keys_count: number;
}

// ============================================================================
// API Functions
// ============================================================================

async function apiRequest<T>(
    endpoint: string,
    options: RequestInit = {}
): Promise<T> {
    const url = `${API_BASE}${endpoint}`;

    const response = await fetch(url, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...options.headers,
        },
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: "Request failed" }));
        throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
}

// Profile
export async function getProfile(): Promise<UserProfile> {
    return apiRequest<UserProfile>("/api/v1/settings/profile");
}

export async function updateProfile(data: Partial<UserProfile>): Promise<UserProfile> {
    return apiRequest<UserProfile>("/api/v1/settings/profile", {
        method: "PUT",
        body: JSON.stringify(data),
    });
}

// Notifications
export async function getNotifications(): Promise<NotificationSettings> {
    return apiRequest<NotificationSettings>("/api/v1/settings/notifications");
}

export async function updateNotifications(
    data: Partial<NotificationSettings>
): Promise<NotificationSettings> {
    return apiRequest<NotificationSettings>("/api/v1/settings/notifications", {
        method: "PUT",
        body: JSON.stringify(data),
    });
}

// Security
export async function getSecurity(): Promise<SecuritySettings> {
    return apiRequest<SecuritySettings>("/api/v1/settings/security");
}

export async function enable2FA(): Promise<Enable2FAResponse> {
    return apiRequest<Enable2FAResponse>("/api/v1/settings/security/2fa", {
        method: "POST",
        body: JSON.stringify({}),
    });
}

export async function disable2FA(): Promise<SecuritySettings> {
    return apiRequest<SecuritySettings>("/api/v1/settings/security/2fa", {
        method: "DELETE",
    });
}

export async function changePassword(
    currentPassword: string,
    newPassword: string
): Promise<{ message: string }> {
    return apiRequest<{ message: string }>("/api/v1/settings/security/password", {
        method: "POST",
        body: JSON.stringify({
            current_password: currentPassword,
            new_password: newPassword,
        }),
    });
}

// Appearance
export async function getAppearance(): Promise<AppearanceSettings> {
    return apiRequest<AppearanceSettings>("/api/v1/settings/appearance");
}

export async function updateAppearance(
    data: Partial<AppearanceSettings>
): Promise<AppearanceSettings> {
    return apiRequest<AppearanceSettings>("/api/v1/settings/appearance", {
        method: "PUT",
        body: JSON.stringify(data),
    });
}

// API Keys
export async function getAPIKeys(): Promise<BrokerAPIKeyList> {
    return apiRequest<BrokerAPIKeyList>("/api/v1/settings/api-keys");
}

export async function addAPIKey(data: BrokerAPIKeyCreate): Promise<BrokerAPIKey> {
    return apiRequest<BrokerAPIKey>("/api/v1/settings/api-keys", {
        method: "POST",
        body: JSON.stringify(data),
    });
}

export async function deleteAPIKey(keyId: string): Promise<{ message: string }> {
    return apiRequest<{ message: string }>(`/api/v1/settings/api-keys/${keyId}`, {
        method: "DELETE",
    });
}

// Preferences
export async function getPreferences(): Promise<UserPreferences> {
    return apiRequest<UserPreferences>("/api/v1/settings/preferences");
}

export async function updatePreferences(
    data: Partial<UserPreferences>
): Promise<UserPreferences> {
    return apiRequest<UserPreferences>("/api/v1/settings/preferences", {
        method: "PUT",
        body: JSON.stringify(data),
    });
}

// All Settings
export async function getAllSettings(): Promise<AllUserSettings> {
    return apiRequest<AllUserSettings>("/api/v1/settings/all");
}
