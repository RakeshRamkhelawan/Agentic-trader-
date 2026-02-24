import { useState, useEffect, useCallback } from 'react';
import {
  User,
  Bell,
  Shield,
  Wallet,
  Globe,
  Key,
  Smartphone,
  Mail,
  Link2,
  CheckCircle2,
  XCircle,
  Loader2,
  ExternalLink,
  Trash2,
  Plus,
  Eye,
  EyeOff,
  RefreshCw,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import { providersApi, type SupportedExchange, type ConnectedProvider } from '@/lib/api';

// ─── Exchange connect form state ───────────────────────────────────────────────
interface ConnectFormState {
  apiKey: string;
  apiSecret: string;
  passphrase: string;
  showSecret: boolean;
  isLoading: boolean;
  error: string | null;
}

const defaultFormState = (): ConnectFormState => ({
  apiKey: '',
  apiSecret: '',
  passphrase: '',
  showSecret: false,
  isLoading: false,
  error: null,
});

// ─── Exchange icons / colours ──────────────────────────────────────────────────
const EXCHANGE_COLORS: Record<string, string> = {
  revolut:  'from-[#191C82] to-[#5C5FCC]',
  bitvavo:  'from-[#1A4ECC] to-[#3B7AEF]',
  kraken:   'from-[#5741D9] to-[#7B5CF6]',
  binance:  'from-[#B8831A] to-[#F3BA2F]',
  coinbase: 'from-[#0052FF] to-[#3B82F6]',
  bybit:    'from-[#CC2B2B] to-[#EF4444]',
};

const EXCHANGE_INITIALS: Record<string, string> = {
  revolut:  'RX',
  bitvavo:  'BV',
  kraken:   'KR',
  binance:  'BNB',
  coinbase: 'CB',
  bybit:    'BB',
};

// ─── Single exchange card ──────────────────────────────────────────────────────
function ExchangeCard({
  exchangeId,
  info,
  connected,
  onConnect,
  onDisconnect,
}: {
  exchangeId: string;
  info: SupportedExchange;
  connected: ConnectedProvider | undefined;
  onConnect: (id: string, form: ConnectFormState) => Promise<void>;
  onDisconnect: (id: string) => Promise<void>;
}) {
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<ConnectFormState>(defaultFormState());
  const [disconnecting, setDisconnecting] = useState(false);

  const handleConnect = async () => {
    setForm(f => ({ ...f, isLoading: true, error: null }));
    try {
      await onConnect(exchangeId, form);
      setShowForm(false);
      setForm(defaultFormState());
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Connection failed';
      setForm(f => ({ ...f, error: msg, isLoading: false }));
    }
  };

  const handleDisconnect = async () => {
    setDisconnecting(true);
    try {
      await onDisconnect(exchangeId);
    } finally {
      setDisconnecting(false);
    }
  };

  const gradient = EXCHANGE_COLORS[exchangeId] ?? 'from-[#333] to-[#555]';
  const initials = EXCHANGE_INITIALS[exchangeId] ?? exchangeId.slice(0, 2).toUpperCase();

  return (
    <Card className="bg-[#111111] border-[#262626]">
      <CardContent className="p-5">
        <div className="flex items-center justify-between">
          {/* Left: logo + name */}
          <div className="flex items-center gap-3">
            <div className={`w-11 h-11 rounded-xl bg-gradient-to-br ${gradient} flex items-center justify-center flex-shrink-0`}>
              <span className="text-xs font-bold text-white">{initials}</span>
            </div>
            <div>
              <p className="font-semibold text-white">{info.name}</p>
              <div className="flex items-center gap-2 mt-0.5">
                {connected ? (
                  <>
                    <CheckCircle2 className="w-3 h-3 text-trade-green" />
                    <span className="text-xs text-trade-green">Connected</span>
                    <span className="text-xs text-muted-foreground">· {connected.api_key_masked}</span>
                  </>
                ) : (
                  <>
                    <XCircle className="w-3 h-3 text-muted-foreground" />
                    <span className="text-xs text-muted-foreground">Not connected</span>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Right: actions */}
          <div className="flex items-center gap-2">
            {info.website && (
              <a
                href={info.website}
                target="_blank"
                rel="noopener noreferrer"
                className="p-1.5 rounded text-muted-foreground hover:text-white transition-colors"
                title={`Visit ${info.name}`}
              >
                <ExternalLink className="w-4 h-4" />
              </a>
            )}
            {connected ? (
              <Button
                variant="outline"
                size="sm"
                onClick={handleDisconnect}
                disabled={disconnecting}
                className="border-red-800 text-red-400 hover:bg-red-900/20 hover:text-red-300 bg-transparent"
              >
                {disconnecting ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Trash2 className="w-3.5 h-3.5 mr-1" />
                )}
                Disconnect
              </Button>
            ) : (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowForm(v => !v)}
                className="border-[#333] text-white hover:bg-[#1A1A1A] bg-transparent"
              >
                <Plus className="w-3.5 h-3.5 mr-1" />
                Connect
              </Button>
            )}
          </div>
        </div>

        {/* Connect form */}
        {showForm && !connected && (
          <div className="mt-5 pt-5 border-t border-[#262626] space-y-4">
            <p className="text-sm text-muted-foreground">
              Enter your {info.name} API credentials. You can generate these in your exchange account
              under <strong className="text-white">API Management</strong>.
            </p>

            <div className="space-y-3">
              <div className="space-y-1.5">
                <Label className="text-white text-sm">API Key</Label>
                <Input
                  value={form.apiKey}
                  onChange={e => setForm(f => ({ ...f, apiKey: e.target.value }))}
                  placeholder="Paste your API key here"
                  className="bg-[#0A0A0A] border-[#333] text-white font-mono text-sm"
                />
              </div>

              <div className="space-y-1.5">
                <Label className="text-white text-sm">API Secret</Label>
                <div className="relative">
                  <Input
                    type={form.showSecret ? 'text' : 'password'}
                    value={form.apiSecret}
                    onChange={e => setForm(f => ({ ...f, apiSecret: e.target.value }))}
                    placeholder="Paste your API secret here"
                    className="bg-[#0A0A0A] border-[#333] text-white font-mono text-sm pr-10"
                  />
                  <button
                    type="button"
                    onClick={() => setForm(f => ({ ...f, showSecret: !f.showSecret }))}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-white transition-colors"
                  >
                    {form.showSecret ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* Passphrase only for Coinbase */}
              {exchangeId === 'coinbase' && (
                <div className="space-y-1.5">
                  <Label className="text-white text-sm">Passphrase <span className="text-muted-foreground">(Coinbase only)</span></Label>
                  <Input
                    type="password"
                    value={form.passphrase}
                    onChange={e => setForm(f => ({ ...f, passphrase: e.target.value }))}
                    placeholder="Your API passphrase"
                    className="bg-[#0A0A0A] border-[#333] text-white text-sm"
                  />
                </div>
              )}

              {form.error && (
                <p className="text-sm text-red-400 flex items-center gap-1.5">
                  <XCircle className="w-4 h-4 flex-shrink-0" />
                  {form.error}
                </p>
              )}

              <div className="flex items-center gap-2 pt-1">
                <Button
                  onClick={handleConnect}
                  disabled={form.isLoading || form.apiKey.length < 10 || form.apiSecret.length < 10}
                  className="bg-trade-blue hover:bg-trade-blue/90 text-white"
                  size="sm"
                >
                  {form.isLoading && <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />}
                  {form.isLoading ? 'Connecting…' : 'Save & Connect'}
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => { setShowForm(false); setForm(defaultFormState()); }}
                  className="text-muted-foreground hover:text-white"
                >
                  Cancel
                </Button>
              </div>

              <p className="text-xs text-muted-foreground">
                Your keys are stored encrypted and never leave this platform.
                We recommend using <strong className="text-white">read + trade</strong> permissions only —
                never withdrawal permissions.
              </p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ─── Main Settings page ────────────────────────────────────────────────────────
export function Settings() {
  const [notifications, setNotifications] = useState({
    email: true,
    push: true,
    trades: true,
    priceAlerts: true,
    agentUpdates: false,
    marketing: false,
  });

  const [security, setSecurity] = useState({
    twoFactor: true,
    biometric: false,
    withdrawalConfirm: true,
  });

  // Exchange state
  const [supported, setSupported] = useState<Record<string, SupportedExchange>>({});
  const [connected, setConnected] = useState<ConnectedProvider[]>([]);
  const [loadingExchanges, setLoadingExchanges] = useState(false);

  const loadExchanges = useCallback(async () => {
    setLoadingExchanges(true);
    try {
      const [sup, conn] = await Promise.all([
        providersApi.getSupported(),
        providersApi.getConnected(),
      ]);
      setSupported(sup);
      setConnected(conn);
    } catch (err) {
      console.error('Failed to load exchanges:', err);
    } finally {
      setLoadingExchanges(false);
    }
  }, []);

  const handleConnect = async (exchangeId: string, form: ConnectFormState) => {
    await providersApi.connect(exchangeId, {
      api_key: form.apiKey,
      api_secret: form.apiSecret,
      passphrase: form.passphrase || undefined,
    });
    await loadExchanges();
  };

  const handleDisconnect = async (exchangeId: string) => {
    await providersApi.disconnect(exchangeId);
    await loadExchanges();
  };

  return (
    <div className="p-6 space-y-6 max-w-4xl">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-white">Settings</h2>
        <p className="text-muted-foreground mt-1">Manage your account and preferences</p>
      </div>

      <Tabs defaultValue="profile" className="w-full">
        <TabsList className="bg-[#111111] border border-[#262626] p-1">
          <TabsTrigger value="profile" className="data-[state=active]:bg-[#1A1A1A]">
            <User className="w-4 h-4 mr-2" />
            Profile
          </TabsTrigger>
          <TabsTrigger value="exchanges" className="data-[state=active]:bg-[#1A1A1A]" onClick={loadExchanges}>
            <Link2 className="w-4 h-4 mr-2" />
            Exchanges
          </TabsTrigger>
          <TabsTrigger value="notifications" className="data-[state=active]:bg-[#1A1A1A]">
            <Bell className="w-4 h-4 mr-2" />
            Notifications
          </TabsTrigger>
          <TabsTrigger value="security" className="data-[state=active]:bg-[#1A1A1A]">
            <Shield className="w-4 h-4 mr-2" />
            Security
          </TabsTrigger>
          <TabsTrigger value="trading" className="data-[state=active]:bg-[#1A1A1A]">
            <Wallet className="w-4 h-4 mr-2" />
            Trading
          </TabsTrigger>
        </TabsList>

        {/* Profile Tab */}
        <TabsContent value="profile" className="space-y-4 mt-6">
          <Card className="bg-[#111111] border-[#262626]">
            <CardHeader>
              <CardTitle className="text-lg font-semibold text-white">Profile Information</CardTitle>
              <CardDescription className="text-muted-foreground">
                Update your personal details and public profile
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center gap-4">
                <div className="w-20 h-20 rounded-full bg-gradient-to-br from-trade-purple to-trade-blue flex items-center justify-center">
                  <span className="text-2xl font-bold text-white">T</span>
                </div>
                <div>
                  <Button variant="outline" className="border-[#262626] bg-transparent text-white hover:bg-[#1A1A1A]">
                    Change Avatar
                  </Button>
                  <p className="text-xs text-muted-foreground mt-2">JPG, PNG or GIF. Max 2MB.</p>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="text-white">Display Name</Label>
                  <Input
                    defaultValue="Trader"
                    className="bg-[#0A0A0A] border-[#262626] text-white"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-white">Email</Label>
                  <Input
                    defaultValue="trader@example.com"
                    className="bg-[#0A0A0A] border-[#262626] text-white"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-white">Phone</Label>
                  <Input
                    placeholder="+1 (555) 000-0000"
                    className="bg-[#0A0A0A] border-[#262626] text-white"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-white">Timezone</Label>
                  <Input
                    defaultValue="UTC-5 (Eastern Time)"
                    className="bg-[#0A0A0A] border-[#262626] text-white"
                  />
                </div>
              </div>

              <Button className="bg-trade-blue hover:bg-trade-blue/90 text-white">
                Save Changes
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Exchanges Tab */}
        <TabsContent value="exchanges" className="space-y-4 mt-6">
          {/* Header card */}
          <Card className="bg-[#111111] border-[#262626]">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="text-lg font-semibold text-white">Exchange Connections</CardTitle>
                  <CardDescription className="text-muted-foreground mt-1">
                    Connect your exchange accounts to start trading. Your API keys are encrypted and
                    stored securely — they cannot be used to withdraw funds.
                  </CardDescription>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={loadExchanges}
                  disabled={loadingExchanges}
                  className="text-muted-foreground hover:text-white flex-shrink-0"
                >
                  <RefreshCw className={`w-4 h-4 ${loadingExchanges ? 'animate-spin' : ''}`} />
                </Button>
              </div>

              {/* Summary badges */}
              <div className="flex items-center gap-2 mt-3 flex-wrap">
                <Badge className="bg-trade-green/10 text-trade-green border-trade-green/20">
                  {connected.length} connected
                </Badge>
                <Badge variant="outline" className="border-[#333] text-muted-foreground">
                  {Object.keys(supported).length} supported
                </Badge>
              </div>
            </CardHeader>
          </Card>

          {/* Loading state */}
          {loadingExchanges && Object.keys(supported).length === 0 && (
            <div className="flex items-center justify-center py-12 gap-2 text-muted-foreground">
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Loading exchanges…</span>
            </div>
          )}

          {/* Exchange cards */}
          {Object.keys(supported).length > 0 && (
            <div className="space-y-3">
              {Object.entries(supported).map(([id, info]) => (
                <ExchangeCard
                  key={id}
                  exchangeId={id}
                  info={info}
                  connected={connected.find(c => c.exchange === id)}
                  onConnect={handleConnect}
                  onDisconnect={handleDisconnect}
                />
              ))}
            </div>
          )}

          {/* Empty state if no supported loaded yet (and not loading) */}
          {!loadingExchanges && Object.keys(supported).length === 0 && (
            <Card className="bg-[#111111] border-[#262626]">
              <CardContent className="flex flex-col items-center justify-center py-12 text-center gap-3">
                <Globe className="w-10 h-10 text-muted-foreground" />
                <p className="text-white font-medium">Could not load exchanges</p>
                <p className="text-sm text-muted-foreground">Make sure the API server is running.</p>
                <Button variant="outline" onClick={loadExchanges} className="border-[#333] text-white hover:bg-[#1A1A1A] bg-transparent mt-2">
                  Try again
                </Button>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Notifications Tab */}
        <TabsContent value="notifications" className="space-y-4 mt-6">
          <Card className="bg-[#111111] border-[#262626]">
            <CardHeader>
              <CardTitle className="text-lg font-semibold text-white">Notification Preferences</CardTitle>
              <CardDescription className="text-muted-foreground">
                Choose how you want to be notified
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between py-3 border-b border-[#262626]">
                  <div className="flex items-center gap-3">
                    <Mail className="w-5 h-5 text-muted-foreground" />
                    <div>
                      <p className="text-white font-medium">Email Notifications</p>
                      <p className="text-sm text-muted-foreground">Receive updates via email</p>
                    </div>
                  </div>
                  <Switch
                    checked={notifications.email}
                    onCheckedChange={(v) => setNotifications({...notifications, email: v})}
                  />
                </div>

                <div className="flex items-center justify-between py-3 border-b border-[#262626]">
                  <div className="flex items-center gap-3">
                    <Smartphone className="w-5 h-5 text-muted-foreground" />
                    <div>
                      <p className="text-white font-medium">Push Notifications</p>
                      <p className="text-sm text-muted-foreground">Receive push notifications</p>
                    </div>
                  </div>
                  <Switch
                    checked={notifications.push}
                    onCheckedChange={(v) => setNotifications({...notifications, push: v})}
                  />
                </div>

                <div className="flex items-center justify-between py-3 border-b border-[#262626]">
                  <div className="flex items-center gap-3">
                    <Wallet className="w-5 h-5 text-muted-foreground" />
                    <div>
                      <p className="text-white font-medium">Trade Updates</p>
                      <p className="text-sm text-muted-foreground">Get notified when orders are filled</p>
                    </div>
                  </div>
                  <Switch
                    checked={notifications.trades}
                    onCheckedChange={(v) => setNotifications({...notifications, trades: v})}
                  />
                </div>

                <div className="flex items-center justify-between py-3 border-b border-[#262626]">
                  <div className="flex items-center gap-3">
                    <Bell className="w-5 h-5 text-muted-foreground" />
                    <div>
                      <p className="text-white font-medium">Price Alerts</p>
                      <p className="text-sm text-muted-foreground">Notifications for price targets</p>
                    </div>
                  </div>
                  <Switch
                    checked={notifications.priceAlerts}
                    onCheckedChange={(v) => setNotifications({...notifications, priceAlerts: v})}
                  />
                </div>

                <div className="flex items-center justify-between py-3 border-b border-[#262626]">
                  <div className="flex items-center gap-3">
                    <Globe className="w-5 h-5 text-muted-foreground" />
                    <div>
                      <p className="text-white font-medium">AI Agent Updates</p>
                      <p className="text-sm text-muted-foreground">Get notified about AI actions</p>
                    </div>
                  </div>
                  <Switch
                    checked={notifications.agentUpdates}
                    onCheckedChange={(v) => setNotifications({...notifications, agentUpdates: v})}
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Security Tab */}
        <TabsContent value="security" className="space-y-4 mt-6">
          <Card className="bg-[#111111] border-[#262626]">
            <CardHeader>
              <CardTitle className="text-lg font-semibold text-white">Security Settings</CardTitle>
              <CardDescription className="text-muted-foreground">
                Protect your account with advanced security
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between py-3 border-b border-[#262626]">
                  <div className="flex items-center gap-3">
                    <Key className="w-5 h-5 text-muted-foreground" />
                    <div>
                      <p className="text-white font-medium">Two-Factor Authentication</p>
                      <p className="text-sm text-muted-foreground">Add an extra layer of security</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge className="bg-trade-green/10 text-trade-green border-trade-green/20">
                      Enabled
                    </Badge>
                    <Switch
                      checked={security.twoFactor}
                      onCheckedChange={(v) => setSecurity({...security, twoFactor: v})}
                    />
                  </div>
                </div>

                <div className="flex items-center justify-between py-3 border-b border-[#262626]">
                  <div className="flex items-center gap-3">
                    <Shield className="w-5 h-5 text-muted-foreground" />
                    <div>
                      <p className="text-white font-medium">Biometric Login</p>
                      <p className="text-sm text-muted-foreground">Use fingerprint or face recognition</p>
                    </div>
                  </div>
                  <Switch
                    checked={security.biometric}
                    onCheckedChange={(v) => setSecurity({...security, biometric: v})}
                  />
                </div>

                <div className="flex items-center justify-between py-3 border-b border-[#262626]">
                  <div className="flex items-center gap-3">
                    <Wallet className="w-5 h-5 text-muted-foreground" />
                    <div>
                      <p className="text-white font-medium">Withdrawal Confirmation</p>
                      <p className="text-sm text-muted-foreground">Require email confirmation for withdrawals</p>
                    </div>
                  </div>
                  <Switch
                    checked={security.withdrawalConfirm}
                    onCheckedChange={(v) => setSecurity({...security, withdrawalConfirm: v})}
                  />
                </div>
              </div>

              <div className="pt-4">
                <Button variant="outline" className="border-[#262626] bg-transparent text-white hover:bg-[#1A1A1A]">
                  Change Password
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Trading Tab */}
        <TabsContent value="trading" className="space-y-4 mt-6">
          <Card className="bg-[#111111] border-[#262626]">
            <CardHeader>
              <CardTitle className="text-lg font-semibold text-white">Trading Preferences</CardTitle>
              <CardDescription className="text-muted-foreground">
                Customize your trading experience
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="text-white">Default Order Type</Label>
                  <Input
                    defaultValue="Limit"
                    className="bg-[#0A0A0A] border-[#262626] text-white"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-white">Default Time in Force</Label>
                  <Input
                    defaultValue="GTC (Good Till Canceled)"
                    className="bg-[#0A0A0A] border-[#262626] text-white"
                  />
                </div>
              </div>

              <Separator className="bg-[#262626]" />

              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-white font-medium">Confirm Before Trade</p>
                    <p className="text-sm text-muted-foreground">Show confirmation dialog for each trade</p>
                  </div>
                  <Switch defaultChecked />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-white font-medium">Auto-Cancel Stale Orders</p>
                    <p className="text-sm text-muted-foreground">Cancel unfilled orders after 24 hours</p>
                  </div>
                  <Switch defaultChecked />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-white font-medium">AI Auto-Trading</p>
                    <p className="text-sm text-muted-foreground">Allow AI to execute trades on your behalf</p>
                  </div>
                  <Switch />
                </div>
              </div>

              <Button className="bg-trade-blue hover:bg-trade-blue/90 text-white">
                Save Preferences
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
