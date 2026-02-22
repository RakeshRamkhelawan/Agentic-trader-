import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Bell, Moon, Sun, User, LogOut } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAppStore } from '@/store/appStore';
import { useAuth } from '@/context';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Badge } from '@/components/ui/badge';

interface HeaderProps {
  className?: string;
}

const pageTitles: Record<string, string> = {
  '/dashboard': 'Dashboard',
  '/markets': 'Markets',
  '/portfolio': 'Portfolio',
  '/terminal': 'Trading Terminal',
  '/history': 'Trade History',
  '/settings': 'Settings',
};

export function Header({ className }: HeaderProps) {
  const navigate = useNavigate();
  const { sidebarExpanded } = useAppStore();
  const { user, logout } = useAuth();
  const [isDark, setIsDark] = useState(true);
  const [searchFocused, setSearchFocused] = useState(false);

  const location = window.location.pathname;
  const pageTitle = pageTitles[location] || 'Dashboard';

  const toggleTheme = () => {
    setIsDark(!isDark);
    document.documentElement.classList.toggle('dark');
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header
      className={cn(
        'fixed top-0 right-0 h-16 z-40',
        'bg-background/80 backdrop-blur-xl border-b border-border',
        'flex items-center justify-between px-6',
        'transition-all duration-300',
        sidebarExpanded ? 'left-60' : 'left-[72px]',
        className
      )}
    >
      {/* Page Title */}
      <div className="flex items-center gap-4">
        <h1 className="text-xl font-semibold text-white tracking-tight">
          {pageTitle}
        </h1>
        {location === '/dashboard' && (
          <Badge 
            variant="outline" 
            className="bg-trade-green/10 text-trade-green border-trade-green/20 text-xs"
          >
            Live
          </Badge>
        )}
      </div>

      {/* Right Section */}
      <div className="flex items-center gap-4">
        {/* Search */}
        <div 
          className={cn(
            'relative transition-all duration-300',
            searchFocused ? 'w-80' : 'w-64'
          )}
        >
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search assets, markets..."
            className={cn(
              'pl-10 bg-[#111111] border-[#262626] text-white placeholder:text-muted-foreground',
              'focus:border-trade-blue focus:ring-1 focus:ring-trade-blue/30',
              'transition-all duration-300'
            )}
            onFocus={() => setSearchFocused(true)}
            onBlur={() => setSearchFocused(false)}
          />
        </div>

        {/* Theme Toggle */}
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleTheme}
          className="relative hover:bg-[#1A1A1A]"
        >
          {isDark ? (
            <Moon className="w-5 h-5 text-muted-foreground" />
          ) : (
            <Sun className="w-5 h-5 text-muted-foreground" />
          )}
        </Button>

        {/* Notifications */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="relative hover:bg-[#1A1A1A]"
            >
              <Bell className="w-5 h-5 text-muted-foreground" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-trade-red rounded-full animate-pulse" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-80 bg-[#111111] border-[#262626]">
            <DropdownMenuLabel className="text-white">Notifications</DropdownMenuLabel>
            <DropdownMenuSeparator className="bg-[#262626]" />
            <div className="max-h-64 overflow-y-auto">
              <DropdownMenuItem className="flex flex-col items-start gap-1 py-3 cursor-pointer hover:bg-[#1A1A1A]">
                <span className="text-sm text-white">Order Filled</span>
                <span className="text-xs text-muted-foreground">Your buy order for 0.1 BTC was filled at $67,234</span>
                <span className="text-xs text-trade-blue">2 minutes ago</span>
              </DropdownMenuItem>
              <DropdownMenuItem className="flex flex-col items-start gap-1 py-3 cursor-pointer hover:bg-[#1A1A1A]">
                <span className="text-sm text-white">Price Alert</span>
                <span className="text-xs text-muted-foreground">ETH reached your target price of $3,500</span>
                <span className="text-xs text-trade-blue">15 minutes ago</span>
              </DropdownMenuItem>
              <DropdownMenuItem className="flex flex-col items-start gap-1 py-3 cursor-pointer hover:bg-[#1A1A1A]">
                <span className="text-sm text-white">AI Agent Update</span>
                <span className="text-xs text-muted-foreground">Market analysis completed - Bullish sentiment detected</span>
                <span className="text-xs text-trade-blue">1 hour ago</span>
              </DropdownMenuItem>
            </div>
          </DropdownMenuContent>
        </DropdownMenu>

        {/* User Menu */}
        {user ? (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                className="flex items-center gap-2 hover:bg-[#1A1A1A]"
              >
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-trade-purple to-trade-blue flex items-center justify-center">
                  <span className="text-sm font-semibold text-white">
                    {user.firstName?.charAt(0).toUpperCase() || user.displayName?.charAt(0).toUpperCase()}
                  </span>
                </div>
                <span className="text-sm text-white hidden sm:inline">{user.displayName}</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56 bg-[#111111] border-[#262626]">
              <DropdownMenuLabel className="text-white">My Account</DropdownMenuLabel>
              <DropdownMenuSeparator className="bg-[#262626]" />
              <DropdownMenuItem 
                className="text-white hover:bg-[#1A1A1A] cursor-pointer"
                onClick={() => navigate('/settings')}
              >
                <User className="w-4 h-4 mr-2" />
                Profile
              </DropdownMenuItem>
              <DropdownMenuItem 
                className="text-destructive hover:bg-[#1A1A1A] cursor-pointer"
                onClick={handleLogout}
              >
                <LogOut className="w-4 h-4 mr-2" />
                Logout
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        ) : null}
      </div>
    </header>
  );
}
