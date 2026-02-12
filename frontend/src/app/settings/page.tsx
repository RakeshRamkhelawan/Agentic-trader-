"use client";

import { useState, useEffect, useCallback } from "react";
import { TopBar } from "@/components/layout/top-bar";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { User, Bell, Shield, Palette, Globe, Key, Loader2, Check, X, Trash2, Plus } from "lucide-react";
import * as settingsApi from "@/lib/api/settings-api";
import type {
    UserProfile,
    NotificationSettings,
    SecuritySettings,
    AppearanceSettings,
    UserPreferences,
    BrokerAPIKey,
    ThemeType,
    CurrencyType,
    ExchangeType,
} from "@/lib/api/settings-api";

type TabId = "profile" | "notifications" | "security" | "appearance" | "api" | "preferences";

export default function SettingsPage() {
    const [activeTab, setActiveTab] = useState<TabId>("profile");
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);

    // State for each section
    const [profile, setProfile] = useState<UserProfile>({ first_name: "", last_name: "", email: null });
    const [notifications, setNotifications] = useState<NotificationSettings>({
        order_executions: true,
        price_alerts: true,
        ai_signals: true,
        security_alerts: true,
    });
    const [security, setSecurity] = useState<SecuritySettings>({
        two_factor_enabled: false,
        last_password_change: null,
    });
    const [appearance, setAppearance] = useState<AppearanceSettings>({ theme: "dark" });
    const [preferences, setPreferences] = useState<UserPreferences>({
        default_currency: "EUR",
        default_exchange: "binance",
    });
    const [apiKeys, setApiKeys] = useState<BrokerAPIKey[]>([]);

    // Form state for adding API key
    const [newApiKey, setNewApiKey] = useState({
        exchange: "binance" as ExchangeType,
        api_key: "",
        api_secret: "",
        passphrase: "",
    });
    const [showAddKeyForm, setShowAddKeyForm] = useState(false);

    // Password change state
    const [passwordForm, setPasswordForm] = useState({
        current: "",
        new: "",
        confirm: "",
    });

    const tabs = [
        { id: "profile" as const, label: "Profile", icon: User },
        { id: "notifications" as const, label: "Notifications", icon: Bell },
        { id: "security" as const, label: "Security", icon: Shield },
        { id: "appearance" as const, label: "Appearance", icon: Palette },
        { id: "api" as const, label: "API Keys", icon: Key },
        { id: "preferences" as const, label: "Preferences", icon: Globe },
    ];

    // Load data for current tab
    const loadTabData = useCallback(async (tab: TabId) => {
        setLoading(true);
        setError(null);
        try {
            switch (tab) {
                case "profile":
                    setProfile(await settingsApi.getProfile());
                    break;
                case "notifications":
                    setNotifications(await settingsApi.getNotifications());
                    break;
                case "security":
                    setSecurity(await settingsApi.getSecurity());
                    break;
                case "appearance":
                    setAppearance(await settingsApi.getAppearance());
                    break;
                case "api":
                    const keysData = await settingsApi.getAPIKeys();
                    setApiKeys(keysData.keys);
                    break;
                case "preferences":
                    setPreferences(await settingsApi.getPreferences());
                    break;
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to load data");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        loadTabData(activeTab);
    }, [activeTab, loadTabData]);

    const showSuccess = (msg: string) => {
        setSuccess(msg);
        setTimeout(() => setSuccess(null), 3000);
    };

    // Save handlers
    const saveProfile = async () => {
        setSaving(true);
        setError(null);
        try {
            const updated = await settingsApi.updateProfile(profile);
            setProfile(updated);
            showSuccess("Profile saved!");
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to save");
        } finally {
            setSaving(false);
        }
    };

    const saveNotifications = async () => {
        setSaving(true);
        setError(null);
        try {
            const updated = await settingsApi.updateNotifications(notifications);
            setNotifications(updated);
            showSuccess("Notifications saved!");
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to save");
        } finally {
            setSaving(false);
        }
    };

    const toggleNotification = async (key: keyof NotificationSettings) => {
        const newValue = !notifications[key];
        setNotifications((prev) => ({ ...prev, [key]: newValue }));
        try {
            await settingsApi.updateNotifications({ [key]: newValue });
        } catch (err) {
            // Revert on error
            setNotifications((prev) => ({ ...prev, [key]: !newValue }));
            setError("Failed to update");
        }
    };

    const toggle2FA = async () => {
        setSaving(true);
        setError(null);
        try {
            if (security.two_factor_enabled) {
                const updated = await settingsApi.disable2FA();
                setSecurity(updated);
                showSuccess("2FA disabled");
            } else {
                const response = await settingsApi.enable2FA();
                setSecurity((prev) => ({ ...prev, two_factor_enabled: true }));
                // In production, show QR code and backup codes
                showSuccess("2FA enabled! Secret: " + response.secret.slice(0, 8) + "...");
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to toggle 2FA");
        } finally {
            setSaving(false);
        }
    };

    const handleChangePassword = async () => {
        if (passwordForm.new !== passwordForm.confirm) {
            setError("Passwords do not match");
            return;
        }
        if (passwordForm.new.length < 8) {
            setError("Password must be at least 8 characters");
            return;
        }
        setSaving(true);
        setError(null);
        try {
            await settingsApi.changePassword(passwordForm.current, passwordForm.new);
            setPasswordForm({ current: "", new: "", confirm: "" });
            showSuccess("Password changed!");
            setSecurity((prev) => ({ ...prev, last_password_change: new Date().toISOString() }));
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to change password");
        } finally {
            setSaving(false);
        }
    };

    const saveAppearance = async (theme: ThemeType) => {
        setAppearance({ theme });
        try {
            await settingsApi.updateAppearance({ theme });
            showSuccess("Theme updated!");
        } catch (err) {
            setError("Failed to update theme");
        }
    };

    const addApiKey = async () => {
        if (!newApiKey.api_key || !newApiKey.api_secret) {
            setError("API key and secret are required");
            return;
        }
        setSaving(true);
        setError(null);
        try {
            const created = await settingsApi.addAPIKey(newApiKey);
            setApiKeys((prev) => [...prev, created]);
            setNewApiKey({ exchange: "binance", api_key: "", api_secret: "", passphrase: "" });
            setShowAddKeyForm(false);
            showSuccess("API key added!");
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to add API key");
        } finally {
            setSaving(false);
        }
    };

    const deleteApiKey = async (keyId: string) => {
        if (!confirm("Are you sure you want to delete this API key?")) return;
        try {
            await settingsApi.deleteAPIKey(keyId);
            setApiKeys((prev) => prev.filter((k) => k.id !== keyId));
            showSuccess("API key deleted");
        } catch (err) {
            setError("Failed to delete API key");
        }
    };

    const savePreferences = async () => {
        setSaving(true);
        setError(null);
        try {
            const updated = await settingsApi.updatePreferences(preferences);
            setPreferences(updated);
            showSuccess("Preferences saved!");
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to save");
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="flex min-h-screen flex-col bg-background">
            <TopBar balance={10000} currency="EUR" />

            <div className="flex-1 p-6">
                <div className="mx-auto max-w-4xl">
                    {/* Header */}
                    <div className="mb-8">
                        <h1 className="text-3xl font-bold">Settings</h1>
                        <p className="mt-2 text-muted-foreground">
                            Manage your account and preferences
                        </p>
                    </div>

                    {/* Status Messages */}
                    {error && (
                        <div className="mb-4 flex items-center gap-2 rounded-lg bg-red-500/10 p-3 text-red-500">
                            <X className="h-4 w-4" />
                            {error}
                        </div>
                    )}
                    {success && (
                        <div className="mb-4 flex items-center gap-2 rounded-lg bg-green-500/10 p-3 text-green-500">
                            <Check className="h-4 w-4" />
                            {success}
                        </div>
                    )}

                    <div className="grid gap-6 lg:grid-cols-[200px_1fr]">
                        {/* Sidebar */}
                        <nav className="space-y-1">
                            {tabs.map((tab) => {
                                const Icon = tab.icon;
                                return (
                                    <button
                                        key={tab.id}
                                        onClick={() => setActiveTab(tab.id)}
                                        className={`flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${activeTab === tab.id
                                                ? "bg-primary text-primary-foreground"
                                                : "text-muted-foreground hover:bg-muted hover:text-foreground"
                                            }`}
                                    >
                                        <Icon className="h-4 w-4" />
                                        {tab.label}
                                    </button>
                                );
                            })}
                        </nav>

                        {/* Content */}
                        <div className="space-y-6">
                            {loading ? (
                                <div className="flex items-center justify-center py-12">
                                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                                </div>
                            ) : (
                                <>
                                    {activeTab === "profile" && (
                                        <Card>
                                            <CardHeader>
                                                <CardTitle>Profile</CardTitle>
                                                <CardDescription>
                                                    Update your personal information
                                                </CardDescription>
                                            </CardHeader>
                                            <CardContent className="space-y-4">
                                                <div className="grid gap-4 sm:grid-cols-2">
                                                    <div>
                                                        <label className="text-sm font-medium">
                                                            First Name
                                                        </label>
                                                        <input
                                                            type="text"
                                                            value={profile.first_name}
                                                            onChange={(e) =>
                                                                setProfile((p) => ({
                                                                    ...p,
                                                                    first_name: e.target.value,
                                                                }))
                                                            }
                                                            className="mt-1 w-full rounded-lg border border-border bg-card px-3 py-2 text-sm"
                                                        />
                                                    </div>
                                                    <div>
                                                        <label className="text-sm font-medium">
                                                            Last Name
                                                        </label>
                                                        <input
                                                            type="text"
                                                            value={profile.last_name}
                                                            onChange={(e) =>
                                                                setProfile((p) => ({
                                                                    ...p,
                                                                    last_name: e.target.value,
                                                                }))
                                                            }
                                                            className="mt-1 w-full rounded-lg border border-border bg-card px-3 py-2 text-sm"
                                                        />
                                                    </div>
                                                </div>
                                                <div>
                                                    <label className="text-sm font-medium">Email</label>
                                                    <input
                                                        type="email"
                                                        value={profile.email || ""}
                                                        onChange={(e) =>
                                                            setProfile((p) => ({
                                                                ...p,
                                                                email: e.target.value || null,
                                                            }))
                                                        }
                                                        className="mt-1 w-full rounded-lg border border-border bg-card px-3 py-2 text-sm"
                                                    />
                                                </div>
                                                <Button onClick={saveProfile} disabled={saving}>
                                                    {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                                                    Save Changes
                                                </Button>
                                            </CardContent>
                                        </Card>
                                    )}

                                    {activeTab === "notifications" && (
                                        <Card>
                                            <CardHeader>
                                                <CardTitle>Notifications</CardTitle>
                                                <CardDescription>
                                                    Configure how you receive notifications
                                                </CardDescription>
                                            </CardHeader>
                                            <CardContent className="space-y-4">
                                                {([
                                                    { key: "order_executions" as const, label: "Order Executions", desc: "Get notified when your orders are filled" },
                                                    { key: "price_alerts" as const, label: "Price Alerts", desc: "Receive alerts when prices hit your targets" },
                                                    { key: "ai_signals" as const, label: "AI Signals", desc: "Get notified about new trading signals" },
                                                    { key: "security_alerts" as const, label: "Security Alerts", desc: "Important security notifications" },
                                                ]).map((item) => (
                                                    <div
                                                        key={item.key}
                                                        className="flex items-center justify-between rounded-lg border border-border p-4"
                                                    >
                                                        <div>
                                                            <p className="font-medium">{item.label}</p>
                                                            <p className="text-sm text-muted-foreground">
                                                                {item.desc}
                                                            </p>
                                                        </div>
                                                        <button
                                                            onClick={() => toggleNotification(item.key)}
                                                            className={`relative h-6 w-11 rounded-full transition-colors ${notifications[item.key]
                                                                    ? "bg-primary"
                                                                    : "bg-muted"
                                                                }`}
                                                        >
                                                            <span
                                                                className={`absolute left-0.5 top-0.5 h-5 w-5 rounded-full bg-white transition-transform ${notifications[item.key]
                                                                        ? "translate-x-5"
                                                                        : "translate-x-0"
                                                                    }`}
                                                            />
                                                        </button>
                                                    </div>
                                                ))}
                                            </CardContent>
                                        </Card>
                                    )}

                                    {activeTab === "security" && (
                                        <div className="space-y-6">
                                            <Card>
                                                <CardHeader>
                                                    <CardTitle>Two-Factor Authentication</CardTitle>
                                                    <CardDescription>
                                                        Add an extra layer of security to your account
                                                    </CardDescription>
                                                </CardHeader>
                                                <CardContent>
                                                    <div className="flex items-center justify-between">
                                                        <div>
                                                            <p className="font-medium">
                                                                {security.two_factor_enabled
                                                                    ? "2FA is enabled"
                                                                    : "2FA is disabled"}
                                                            </p>
                                                            <p className="text-sm text-muted-foreground">
                                                                {security.two_factor_enabled
                                                                    ? "Your account is protected with 2FA"
                                                                    : "Enable 2FA for better security"}
                                                            </p>
                                                        </div>
                                                        <Button
                                                            variant={security.two_factor_enabled ? "destructive" : "default"}
                                                            onClick={toggle2FA}
                                                            disabled={saving}
                                                        >
                                                            {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                                                            {security.two_factor_enabled ? "Disable" : "Enable"}
                                                        </Button>
                                                    </div>
                                                </CardContent>
                                            </Card>

                                            <Card>
                                                <CardHeader>
                                                    <CardTitle>Change Password</CardTitle>
                                                    <CardDescription>
                                                        Update your password regularly for security
                                                    </CardDescription>
                                                </CardHeader>
                                                <CardContent className="space-y-4">
                                                    <div>
                                                        <label className="text-sm font-medium">
                                                            Current Password
                                                        </label>
                                                        <input
                                                            type="password"
                                                            value={passwordForm.current}
                                                            onChange={(e) =>
                                                                setPasswordForm((p) => ({
                                                                    ...p,
                                                                    current: e.target.value,
                                                                }))
                                                            }
                                                            className="mt-1 w-full rounded-lg border border-border bg-card px-3 py-2 text-sm"
                                                        />
                                                    </div>
                                                    <div>
                                                        <label className="text-sm font-medium">
                                                            New Password
                                                        </label>
                                                        <input
                                                            type="password"
                                                            value={passwordForm.new}
                                                            onChange={(e) =>
                                                                setPasswordForm((p) => ({
                                                                    ...p,
                                                                    new: e.target.value,
                                                                }))
                                                            }
                                                            className="mt-1 w-full rounded-lg border border-border bg-card px-3 py-2 text-sm"
                                                        />
                                                    </div>
                                                    <div>
                                                        <label className="text-sm font-medium">
                                                            Confirm New Password
                                                        </label>
                                                        <input
                                                            type="password"
                                                            value={passwordForm.confirm}
                                                            onChange={(e) =>
                                                                setPasswordForm((p) => ({
                                                                    ...p,
                                                                    confirm: e.target.value,
                                                                }))
                                                            }
                                                            className="mt-1 w-full rounded-lg border border-border bg-card px-3 py-2 text-sm"
                                                        />
                                                    </div>
                                                    <Button onClick={handleChangePassword} disabled={saving}>
                                                        {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                                                        Change Password
                                                    </Button>
                                                </CardContent>
                                            </Card>
                                        </div>
                                    )}

                                    {activeTab === "appearance" && (
                                        <Card>
                                            <CardHeader>
                                                <CardTitle>Appearance</CardTitle>
                                                <CardDescription>
                                                    Customize the look and feel
                                                </CardDescription>
                                            </CardHeader>
                                            <CardContent className="space-y-4">
                                                <div>
                                                    <label className="text-sm font-medium">Theme</label>
                                                    <div className="mt-2 flex gap-2">
                                                        {(["dark", "light", "system"] as ThemeType[]).map(
                                                            (theme) => (
                                                                <Button
                                                                    key={theme}
                                                                    variant={
                                                                        appearance.theme === theme
                                                                            ? "default"
                                                                            : "outline"
                                                                    }
                                                                    className="flex-1 capitalize"
                                                                    onClick={() => saveAppearance(theme)}
                                                                >
                                                                    {theme}
                                                                </Button>
                                                            )
                                                        )}
                                                    </div>
                                                </div>
                                            </CardContent>
                                        </Card>
                                    )}

                                    {activeTab === "api" && (
                                        <Card>
                                            <CardHeader>
                                                <div className="flex items-center justify-between">
                                                    <div>
                                                        <CardTitle>API Keys</CardTitle>
                                                        <CardDescription>
                                                            Manage your exchange API connections
                                                        </CardDescription>
                                                    </div>
                                                    <Button
                                                        size="sm"
                                                        onClick={() => setShowAddKeyForm(!showAddKeyForm)}
                                                    >
                                                        <Plus className="mr-2 h-4 w-4" />
                                                        Add Key
                                                    </Button>
                                                </div>
                                            </CardHeader>
                                            <CardContent className="space-y-4">
                                                {showAddKeyForm && (
                                                    <div className="rounded-lg border border-primary/50 bg-primary/5 p-4 space-y-4">
                                                        <div>
                                                            <label className="text-sm font-medium">Exchange</label>
                                                            <select
                                                                value={newApiKey.exchange}
                                                                onChange={(e) =>
                                                                    setNewApiKey((k) => ({
                                                                        ...k,
                                                                        exchange: e.target.value as ExchangeType,
                                                                    }))
                                                                }
                                                                className="mt-1 w-full rounded-lg border border-border bg-card px-3 py-2 text-sm"
                                                            >
                                                                <option value="binance">Binance</option>
                                                                <option value="kraken">Kraken</option>
                                                                <option value="coinbase">Coinbase</option>
                                                                <option value="bitvavo">Bitvavo</option>
                                                            </select>
                                                        </div>
                                                        <div>
                                                            <label className="text-sm font-medium">API Key</label>
                                                            <input
                                                                type="text"
                                                                value={newApiKey.api_key}
                                                                onChange={(e) =>
                                                                    setNewApiKey((k) => ({
                                                                        ...k,
                                                                        api_key: e.target.value,
                                                                    }))
                                                                }
                                                                placeholder="Enter your API key"
                                                                className="mt-1 w-full rounded-lg border border-border bg-card px-3 py-2 text-sm"
                                                            />
                                                        </div>
                                                        <div>
                                                            <label className="text-sm font-medium">API Secret</label>
                                                            <input
                                                                type="password"
                                                                value={newApiKey.api_secret}
                                                                onChange={(e) =>
                                                                    setNewApiKey((k) => ({
                                                                        ...k,
                                                                        api_secret: e.target.value,
                                                                    }))
                                                                }
                                                                placeholder="Enter your API secret"
                                                                className="mt-1 w-full rounded-lg border border-border bg-card px-3 py-2 text-sm"
                                                            />
                                                        </div>
                                                        {newApiKey.exchange === "coinbase" && (
                                                            <div>
                                                                <label className="text-sm font-medium">
                                                                    Passphrase (Coinbase only)
                                                                </label>
                                                                <input
                                                                    type="password"
                                                                    value={newApiKey.passphrase}
                                                                    onChange={(e) =>
                                                                        setNewApiKey((k) => ({
                                                                            ...k,
                                                                            passphrase: e.target.value,
                                                                        }))
                                                                    }
                                                                    className="mt-1 w-full rounded-lg border border-border bg-card px-3 py-2 text-sm"
                                                                />
                                                            </div>
                                                        )}
                                                        <div className="flex gap-2">
                                                            <Button onClick={addApiKey} disabled={saving}>
                                                                {saving && (
                                                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                                                )}
                                                                Save Key
                                                            </Button>
                                                            <Button
                                                                variant="outline"
                                                                onClick={() => setShowAddKeyForm(false)}
                                                            >
                                                                Cancel
                                                            </Button>
                                                        </div>
                                                    </div>
                                                )}

                                                {apiKeys.length === 0 && !showAddKeyForm ? (
                                                    <p className="py-8 text-center text-muted-foreground">
                                                        No API keys configured. Add one to start trading.
                                                    </p>
                                                ) : (
                                                    apiKeys.map((key) => (
                                                        <div
                                                            key={key.id}
                                                            className="flex items-center justify-between rounded-lg border border-border p-4"
                                                        >
                                                            <div>
                                                                <p className="font-medium capitalize">
                                                                    {key.exchange}
                                                                </p>
                                                                <p className="font-mono text-sm text-muted-foreground">
                                                                    {key.api_key_masked}
                                                                </p>
                                                                <p className="text-xs text-muted-foreground">
                                                                    Added{" "}
                                                                    {new Date(key.created_at).toLocaleDateString()}
                                                                </p>
                                                            </div>
                                                            <Button
                                                                variant="ghost"
                                                                size="sm"
                                                                className="text-red-500 hover:bg-red-500/10 hover:text-red-500"
                                                                onClick={() => deleteApiKey(key.id)}
                                                            >
                                                                <Trash2 className="h-4 w-4" />
                                                            </Button>
                                                        </div>
                                                    ))
                                                )}
                                            </CardContent>
                                        </Card>
                                    )}

                                    {activeTab === "preferences" && (
                                        <Card>
                                            <CardHeader>
                                                <CardTitle>Preferences</CardTitle>
                                                <CardDescription>
                                                    Set your trading preferences
                                                </CardDescription>
                                            </CardHeader>
                                            <CardContent className="space-y-4">
                                                <div>
                                                    <label className="text-sm font-medium">
                                                        Default Currency
                                                    </label>
                                                    <select
                                                        value={preferences.default_currency}
                                                        onChange={(e) =>
                                                            setPreferences((p) => ({
                                                                ...p,
                                                                default_currency: e.target.value as CurrencyType,
                                                            }))
                                                        }
                                                        className="mt-1 w-full rounded-lg border border-border bg-card px-3 py-2 text-sm"
                                                    >
                                                        <option value="EUR">EUR</option>
                                                        <option value="USD">USD</option>
                                                        <option value="GBP">GBP</option>
                                                    </select>
                                                </div>
                                                <div>
                                                    <label className="text-sm font-medium">
                                                        Default Exchange
                                                    </label>
                                                    <select
                                                        value={preferences.default_exchange}
                                                        onChange={(e) =>
                                                            setPreferences((p) => ({
                                                                ...p,
                                                                default_exchange: e.target.value as ExchangeType,
                                                            }))
                                                        }
                                                        className="mt-1 w-full rounded-lg border border-border bg-card px-3 py-2 text-sm"
                                                    >
                                                        <option value="binance">Binance</option>
                                                        <option value="kraken">Kraken</option>
                                                        <option value="coinbase">Coinbase</option>
                                                        <option value="bitvavo">Bitvavo</option>
                                                    </select>
                                                </div>
                                                <Button onClick={savePreferences} disabled={saving}>
                                                    {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                                                    Save Preferences
                                                </Button>
                                            </CardContent>
                                        </Card>
                                    )}
                                </>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
