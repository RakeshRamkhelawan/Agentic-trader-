import { useState, useEffect } from 'react';
import { 
  User, 
  Bell, 
  Shield, 
  Wallet, 
  Globe, 
  Key,
  Smartphone,
  Mail,
  Loader2
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import { settingsApi, type UserProfile, type NotificationSettings, type SecuritySettings, type UserPreferences } from '@/lib/api';

export function Settings() {
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  // Profile state
  const [profile, setProfile] = useState<UserProfile>({
    first_name: '',
    last_name: '',
    email: null,
  });

  // Notifications state
  const [notifications, setNotifications] = useState<NotificationSettings>({
    order_executions: true,
    price_alerts: true,
    ai_signals: true,
    security_alerts: true,
  });

  // Security state
  const [security, setSecurity] = useState<SecuritySettings>({
    two_factor_enabled: false,
    last_password_change: null,
  });

  // Password change state
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  // Trading preferences state
  const [preferences, setPreferences] = useState<UserPreferences>({
    default_currency: 'EUR',
    default_exchange: 'bitvavo',
  });

  // Load settings on mount
  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setIsLoading(true);
      const allSettings = await settingsApi.getAll();
      
      setProfile(allSettings.profile);
      setNotifications(allSettings.notifications);
      setSecurity(allSettings.security);
      setPreferences(allSettings.preferences);
    } catch (error) {
      console.error('Failed to load settings:', error);
      toast.error('Failed to load settings');
    } finally {
      setIsLoading(false);
    }
  };

  // Profile handlers
  const handleSaveProfile = async () => {
    try {
      setIsSaving(true);
      await settingsApi.updateProfile(profile);
      toast.success('Profile saved successfully');
    } catch (error) {
      console.error('Failed to save profile:', error);
      toast.error('Failed to save profile');
    } finally {
      setIsSaving(false);
    }
  };

  // Notification handlers
  const handleSaveNotifications = async () => {
    try {
      setIsSaving(true);
      await settingsApi.updateNotifications(notifications);
      toast.success('Notification preferences saved');
    } catch (error) {
      console.error('Failed to save notifications:', error);
      toast.error('Failed to save notification preferences');
    } finally {
      setIsSaving(false);
    }
  };

  // Security handlers
  const handleToggle2FA = async (enabled: boolean) => {
    try {
      setIsSaving(true);
      await settingsApi.toggle2FA(enabled);
      setSecurity({ ...security, two_factor_enabled: enabled });
      toast.success(`Two-factor authentication ${enabled ? 'enabled' : 'disabled'}`);
    } catch (error) {
      console.error('Failed to toggle 2FA:', error);
      toast.error('Failed to update 2FA settings');
    } finally {
      setIsSaving(false);
    }
  };

  const handleChangePassword = async () => {
    if (newPassword !== confirmPassword) {
      toast.error('New passwords do not match');
      return;
    }
    if (newPassword.length < 8) {
      toast.error('Password must be at least 8 characters');
      return;
    }

    try {
      setIsSaving(true);
      await settingsApi.changePassword(currentPassword, newPassword);
      toast.success('Password changed successfully');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (error) {
      console.error('Failed to change password:', error);
      toast.error('Failed to change password');
    } finally {
      setIsSaving(false);
    }
  };

  // Trading preferences handlers
  const handleSavePreferences = async () => {
    try {
      setIsSaving(true);
      await settingsApi.updatePreferences(preferences);
      toast.success('Trading preferences saved');
    } catch (error) {
      console.error('Failed to save preferences:', error);
      toast.error('Failed to save trading preferences');
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-[400px]">
        <div className="flex items-center gap-2 text-muted-foreground">
          <Loader2 className="w-5 h-5 animate-spin" />
          <span>Loading settings...</span>
        </div>
      </div>
    );
  }

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
                  <span className="text-2xl font-bold text-white">
                    {profile.first_name?.charAt(0) || profile.email?.charAt(0) || 'T'}
                  </span>
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
                  <Label className="text-white">First Name</Label>
                  <Input 
                    value={profile.first_name}
                    onChange={(e) => setProfile({ ...profile, first_name: e.target.value })}
                    placeholder="Enter your first name"
                    className="bg-[#0A0A0A] border-[#262626] text-white"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-white">Last Name</Label>
                  <Input 
                    value={profile.last_name}
                    onChange={(e) => setProfile({ ...profile, last_name: e.target.value })}
                    placeholder="Enter your last name"
                    className="bg-[#0A0A0A] border-[#262626] text-white"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-white">Email</Label>
                  <Input 
                    value={profile.email || ''}
                    onChange={(e) => setProfile({ ...profile, email: e.target.value || null })}
                    placeholder="Enter your email"
                    className="bg-[#0A0A0A] border-[#262626] text-white"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-white">Display Name</Label>
                  <Input 
                    value={`${profile.first_name} ${profile.last_name}`.trim() || 'Trader'}
                    disabled
                    className="bg-[#0A0A0A] border-[#262626] text-white opacity-50"
                  />
                </div>
              </div>

              <Button 
                onClick={handleSaveProfile}
                disabled={isSaving}
                className="bg-trade-blue hover:bg-trade-blue/90 text-white"
              >
                {isSaving && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                Save Changes
              </Button>
            </CardContent>
          </Card>
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
                    checked={notifications.order_executions}
                    onCheckedChange={(v) => setNotifications({...notifications, order_executions: v})}
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
                    checked={notifications.ai_signals}
                    onCheckedChange={(v) => setNotifications({...notifications, ai_signals: v})}
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
                    checked={notifications.order_executions}
                    onCheckedChange={(v) => setNotifications({...notifications, order_executions: v})}
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
                    checked={notifications.price_alerts}
                    onCheckedChange={(v) => setNotifications({...notifications, price_alerts: v})}
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
                    checked={notifications.ai_signals}
                    onCheckedChange={(v) => setNotifications({...notifications, ai_signals: v})}
                  />
                </div>

                <div className="flex items-center justify-between py-3 border-b border-[#262626]">
                  <div className="flex items-center gap-3">
                    <Shield className="w-5 h-5 text-muted-foreground" />
                    <div>
                      <p className="text-white font-medium">Security Alerts</p>
                      <p className="text-sm text-muted-foreground">Important security notifications</p>
                    </div>
                  </div>
                  <Switch 
                    checked={notifications.security_alerts}
                    onCheckedChange={(v) => setNotifications({...notifications, security_alerts: v})}
                  />
                </div>
              </div>

              <Button 
                onClick={handleSaveNotifications}
                disabled={isSaving}
                className="bg-trade-blue hover:bg-trade-blue/90 text-white"
              >
                {isSaving && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                Save Preferences
              </Button>
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
                    <Badge className={security.two_factor_enabled 
                      ? "bg-trade-green/10 text-trade-green border-trade-green/20" 
                      : "bg-yellow-500/10 text-yellow-500 border-yellow-500/20"}>
                      {security.two_factor_enabled ? 'Enabled' : 'Disabled'}
                    </Badge>
                    <Switch 
                      checked={security.two_factor_enabled}
                      onCheckedChange={handleToggle2FA}
                    />
                  </div>
                </div>
              </div>

              <Separator className="bg-[#262626]" />

              <div className="space-y-4">
                <h4 className="text-white font-medium">Change Password</h4>
                <div className="space-y-3">
                  <div className="space-y-2">
                    <Label className="text-white">Current Password</Label>
                    <Input 
                      type="password"
                      value={currentPassword}
                      onChange={(e) => setCurrentPassword(e.target.value)}
                      placeholder="Enter current password"
                      className="bg-[#0A0A0A] border-[#262626] text-white"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-white">New Password</Label>
                    <Input 
                      type="password"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      placeholder="Enter new password (min 8 characters)"
                      className="bg-[#0A0A0A] border-[#262626] text-white"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-white">Confirm New Password</Label>
                    <Input 
                      type="password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="Confirm new password"
                      className="bg-[#0A0A0A] border-[#262626] text-white"
                    />
                  </div>
                </div>
                <Button 
                  variant="outline" 
                  onClick={handleChangePassword}
                  disabled={isSaving || !currentPassword || !newPassword || !confirmPassword}
                  className="border-[#262626] bg-transparent text-white hover:bg-[#1A1A1A]"
                >
                  {isSaving && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
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
                  <Label className="text-white">Default Currency</Label>
                  <select
                    value={preferences.default_currency}
                    onChange={(e) => setPreferences({ ...preferences, default_currency: e.target.value as 'EUR' | 'USD' | 'GBP' })}
                    className="w-full h-10 px-3 rounded-md bg-[#0A0A0A] border border-[#262626] text-white focus:outline-none focus:ring-2 focus:ring-trade-blue"
                  >
                    <option value="EUR">EUR (€)</option>
                    <option value="USD">USD ($)</option>
                    <option value="GBP">GBP (£)</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <Label className="text-white">Default Exchange</Label>
                  <select
                    value={preferences.default_exchange}
                    onChange={(e) => setPreferences({ ...preferences, default_exchange: e.target.value as 'binance' | 'kraken' | 'coinbase' | 'bitvavo' })}
                    className="w-full h-10 px-3 rounded-md bg-[#0A0A0A] border border-[#262626] text-white focus:outline-none focus:ring-2 focus:ring-trade-blue"
                  >
                    <option value="bitvavo">Bitvavo</option>
                    <option value="binance">Binance</option>
                    <option value="kraken">Kraken</option>
                    <option value="coinbase">Coinbase</option>
                  </select>
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

              <Button 
                onClick={handleSavePreferences}
                disabled={isSaving}
                className="bg-trade-blue hover:bg-trade-blue/90 text-white"
              >
                {isSaving && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                Save Preferences
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
