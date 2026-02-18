import { useState } from 'react';
import { 
  User, 
  Bell, 
  Shield, 
  Wallet, 
  Globe, 
  Key,
  Smartphone,
  Mail
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';

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
