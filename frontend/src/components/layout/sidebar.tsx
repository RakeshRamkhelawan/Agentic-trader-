import { useNavigate, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  TrendingUp, 
  Wallet, 
  Terminal, 
  History, 
  Settings, 
  LogOut,
  Zap,
  ChevronRight,
  Bot
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAppStore } from '@/store/appStore';
import { useAuth } from '@/context';
import { Button } from '@/components/ui/button';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

interface NavItem {
  id: string;
  label: string;
  icon: React.ElementType;
  path: string;
}

const navItems: NavItem[] = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, path: '/dashboard' },
  { id: 'markets', label: 'Markets', icon: TrendingUp, path: '/markets' },
  { id: 'portfolio', label: 'Portfolio', icon: Wallet, path: '/portfolio' },
  { id: 'terminal', label: 'Terminal', icon: Terminal, path: '/terminal' },
  { id: 'history', label: 'History', icon: History, path: '/history' },
  { id: 'paper-trading', label: 'Live Paper Trading', icon: Bot, path: '/paper-trading' },
  { id: 'settings', label: 'Settings', icon: Settings, path: '/settings' },
];

export function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();
  const { 
    sidebarExpanded, 
    toggleSidebar, 
    setCurrentPage
  } = useAppStore();
  
  const { logout, user } = useAuth();

  const handleNavClick = (item: NavItem) => {
    setCurrentPage(item.id);
    navigate(item.path);
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <TooltipProvider delayDuration={0}>
      <aside
        className={cn(
          'fixed left-0 top-0 h-screen bg-[#0A0A0A] border-r border-[#1A1A1A] z-50',
          'flex flex-col transition-all duration-300 ease-out',
          sidebarExpanded ? 'w-60' : 'w-[72px]'
        )}
      >
        {/* Logo */}
        <div className="h-16 flex items-center px-4 border-b border-[#1A1A1A]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-trade-blue to-trade-cyan flex items-center justify-center shadow-glow-blue">
              <Zap className="w-5 h-5 text-white" />
            </div>
            {sidebarExpanded && (
              <span className="font-semibold text-white text-lg tracking-tight">
                Agentic
              </span>
            )}
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 py-4 px-3 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;

            return (
              <Tooltip key={item.id}>
                <TooltipTrigger asChild>
                  <button
                    onClick={() => handleNavClick(item)}
                    className={cn(
                      'w-full flex items-center gap-3 px-3 py-3 rounded-xl',
                      'transition-all duration-200 ease-out group',
                      'hover:bg-[#1A1A1A] hover:scale-[1.02]',
                      isActive && 'bg-[#1A1A1A]',
                      isActive && 'relative before:absolute before:left-0 before:top-1/2 before:-translate-y-1/2',
                      isActive && 'before:w-[3px] before:h-6 before:bg-trade-blue before:rounded-r-full'
                    )}
                  >
                    <Icon 
                      className={cn(
                        'w-5 h-5 transition-colors duration-200',
                        isActive ? 'text-trade-blue' : 'text-muted-foreground group-hover:text-white'
                      )} 
                    />
                    {sidebarExpanded && (
                      <span 
                        className={cn(
                          'text-sm font-medium transition-colors duration-200',
                          isActive ? 'text-white' : 'text-muted-foreground group-hover:text-white'
                        )}
                      >
                        {item.label}
                      </span>
                    )}
                    {sidebarExpanded && isActive && (
                      <ChevronRight className="w-4 h-4 text-trade-blue ml-auto" />
                    )}
                  </button>
                </TooltipTrigger>
                {!sidebarExpanded && (
                  <TooltipContent side="right" className="bg-[#1A1A1A] border-[#262626]">
                    <p>{item.label}</p>
                  </TooltipContent>
                )}
              </Tooltip>
            );
          })}
        </nav>

        {/* Expand/Collapse Button */}
        <div className="px-3 py-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={toggleSidebar}
            className="w-full justify-center hover:bg-[#1A1A1A]"
          >
            <ChevronRight 
              className={cn(
                'w-5 h-5 text-muted-foreground transition-transform duration-300',
                sidebarExpanded && 'rotate-180'
              )} 
            />
          </Button>
        </div>

        {/* User Section */}
        {user && (
          <div className="p-3 border-t border-[#1A1A1A]">
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="flex items-center gap-3 px-3 py-2 rounded-xl hover:bg-[#1A1A1A] cursor-pointer group">
                  <div className="w-9 h-9 rounded-full bg-gradient-to-br from-trade-purple to-trade-blue flex items-center justify-center">
                    <span className="text-sm font-semibold text-white">
                      {user.firstName?.charAt(0).toUpperCase() || user.displayName?.charAt(0).toUpperCase()}
                    </span>
                  </div>
                  {sidebarExpanded && (
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-white truncate">{user.displayName}</p>
                      <p className="text-xs text-muted-foreground truncate">{user.email}</p>
                    </div>
                  )}
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={handleLogout}
                    className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    <LogOut className="w-4 h-4 text-muted-foreground hover:text-destructive" />
                  </Button>
                </div>
              </TooltipTrigger>
              {!sidebarExpanded && (
                <TooltipContent side="right" className="bg-[#1A1A1A] border-[#262626]">
                  <p>{user.displayName}</p>
                </TooltipContent>
              )}
            </Tooltip>
          </div>
        )}
      </aside>
    </TooltipProvider>
  );
}
