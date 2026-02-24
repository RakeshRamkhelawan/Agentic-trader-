import { useState, useEffect, useCallback } from 'react';
import { 
  Brain, 
  Sparkles, Info, Layers, Eye, 
  Scale, CircleDot, GitMerge, History, CheckCircle2, 
  AlertTriangle, Flame, 
  Target, Shield, Zap, 
  Users, Workflow, GitBranch, Microscope, 
  Radio, Sparkle, Telescope, Cpu, Gauge, Crown,
  Triangle, Hexagon, Pentagon,
  TrendingUp, Network,
  Loader2
} from 'lucide-react';

import { cn } from '@/lib/utils';
import { useAppStore } from '@/store/appStore';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Badge } from '@/components/ui/badge';

import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { agentsApi, federatedApi, type CouncilView as ApiCouncilView } from '@/lib/api';
import { isDemoMode } from '@/lib/config';

// Federated Triad Types
interface CouncilView {
  name: string;
  type: 'guna' | 'elemental' | 'graha' | 'mind' | 'body';
  perspective: string;
  confidence: number;
  insights: string[];
  contradictions?: string[];
  icon: React.ReactNode;
  color: string;
  bgColor?: string;
  borderColor?: string;
  symbol?: string;
}

interface ChittaNode {
  id: string;
  content: string;
  source: string;
  timestamp: string;
  council: string;
  verified: boolean;
}

interface DeliberationStep {
  iteration: number;
  council: string;
  perspective: string;
  confidence: number;
  reaction_to?: string;
}

interface BuddhiDecision {
  action: 'buy' | 'sell' | 'hold';
  confidence: number;
  rationale: string;
  supporting: string[];
  opposing: string[];
  contradictions: number;
  timestamp: string;
}

interface CoherenceMetrics {
  total: number;
  harmony: number;
  performance: number;
  chitta_health: number;
  deliberation_quality: number;
  buddhi_clarity: number;
}

// Helper functions for council icons and colors
const getCouncilIcon = (type: string) => {
  switch (type) {
    case 'guna': return <Scale className="w-5 h-5" />;
    case 'elemental': return <Flame className="w-5 h-5" />;
    case 'graha': return <Telescope className="w-5 h-5" />;
    case 'mind': return <Crown className="w-5 h-5" />;
    case 'body': return <Cpu className="w-5 h-5" />;
    default: return <CircleDot className="w-5 h-5" />;
  }
};

const getCouncilColor = (type: string) => {
  switch (type) {
    case 'guna': return 'text-trade-blue';
    case 'elemental': return 'text-trade-orange';
    case 'graha': return 'text-trade-purple';
    case 'mind': return 'text-trade-green';
    case 'body': return 'text-trade-red';
    default: return 'text-white';
  }
};

// Default data generators
const getDefaultCouncilViews = (): CouncilView[] => [
  {
    name: 'Guna Council',
    type: 'guna',
    perspective: 'sattva_dominant',
    confidence: 0.72,
    insights: ['Market shows calmness (Sattva)', 'Clear trend direction'],
    icon: <Triangle className="w-5 h-5" />,
    color: 'text-blue-400',
    bgColor: 'bg-blue-400/10',
    borderColor: 'border-blue-400/30',
    symbol: '☸️'
  },
  {
    name: 'Elemental Council',
    type: 'elemental',
    perspective: 'fire_rising',
    confidence: 0.68,
    insights: ['Fire: High volatility', 'Air: Momentum increasing'],
    contradictions: ['tamas_dominant'],
    icon: <Pentagon className="w-5 h-5" />,
    color: 'text-orange-400',
    bgColor: 'bg-orange-400/10',
    borderColor: 'border-orange-400/30',
    symbol: '🔥'
  },
  {
    name: 'Graha Council',
    type: 'graha',
    perspective: 'jupiter_blessing',
    confidence: 0.65,
    insights: ['Jupiter: Favorable conditions', 'Cosmic alignment positive'],
    icon: <Hexagon className="w-5 h-5" />,
    color: 'text-purple-400',
    bgColor: 'bg-purple-400/10',
    borderColor: 'border-purple-400/30',
    symbol: '🪐'
  },
  {
    name: 'Mind (Buddhi)',
    type: 'mind',
    perspective: 'synthesized',
    confidence: 0.70,
    insights: ['Cross-verified all signals', 'Contradictions resolved'],
    icon: <Crown className="w-5 h-5" />,
    color: 'text-emerald-400',
    bgColor: 'bg-emerald-400/10',
    borderColor: 'border-emerald-400/30',
    symbol: '👑'
  },
  {
    name: 'Body (Execution)',
    type: 'body',
    perspective: 'executing',
    confidence: 0.95,
    insights: ['Order routing active', 'Position management'],
    icon: <Cpu className="w-5 h-5" />,
    color: 'text-red-400',
    bgColor: 'bg-red-400/10',
    borderColor: 'border-red-400/30',
    symbol: '⚡'
  }
];

const getDefaultChittaNodes = (): ChittaNode[] => [
  { id: '1', content: 'BTC price: $93,141.94', source: 'market_feed', timestamp: '2m ago', council: 'Body', verified: true },
  { id: '2', content: 'Sattva dominant: market shows calmness', source: 'guna_council', timestamp: '1m ago', council: 'Guna', verified: true },
  { id: '3', content: 'Fire rising: volatility increasing', source: 'elemental_council', timestamp: '1m ago', council: 'Elemental', verified: true },
  { id: '4', content: 'Jupiter blessing: favorable conditions', source: 'graha_council', timestamp: '45s ago', council: 'Graha', verified: false },
];

const getDefaultDeliberation = (): DeliberationStep[] => [
  { iteration: 1, council: 'Guna', perspective: 'sattva_dominant', confidence: 0.72 },
  { iteration: 1, council: 'Elemental', perspective: 'fire_rising', confidence: 0.68 },
  { iteration: 1, council: 'Graha', perspective: 'jupiter_blessing', confidence: 0.65 },
  { iteration: 2, council: 'Guna', perspective: 'refined_sattva', confidence: 0.75, reaction_to: 'elemental_fire' },
  { iteration: 2, council: 'Elemental', perspective: 'confirmed_fire', confidence: 0.70, reaction_to: 'guna_sattva' },
];

const getDefaultDecision = (): BuddhiDecision => ({
  action: 'buy',
  confidence: 0.70,
  rationale: 'Sattva (calmness) + Fire (momentum) = bullish. Graha confirms favorable conditions.',
  supporting: ['Guna', 'Elemental', 'Graha'],
  opposing: [],
  contradictions: 0,
  timestamp: new Date().toISOString()
});

export function AIAgentStatus() {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [_expanded, _setExpanded] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [lastAnalysis, setLastAnalysis] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [councilViews, setCouncilViews] = useState<CouncilView[]>([]);
  const [chittaNodes, setChittaNodes] = useState<ChittaNode[]>([]);
  const [deliberationSteps, setDeliberationSteps] = useState<DeliberationStep[]>([]);
  const [latestDecision, setLatestDecision] = useState<BuddhiDecision | null>(null);
  const [coherence, setCoherence] = useState<CoherenceMetrics>({
    total: 0, harmony: 0, performance: 0, chitta_health: 0, deliberation_quality: 0, buddhi_clarity: 0
  });
  
  const { agentsStatus, agentsCoherence, isLoadingAgents, fetchAgentsStatus, agentTrades, fetchAgentTrades } = useAppStore();

  // Fetch data on mount and periodically
  useEffect(() => {
    fetchAgentsStatus();
    fetchAgentTrades();
    fetchFederatedData();
    
    const interval = setInterval(() => {
      fetchAgentsStatus();
      fetchAgentTrades();
      fetchFederatedData();
    }, 30000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fetchAgentsStatus, fetchAgentTrades]);

  // Fetch Federated Triad specific data
  const fetchFederatedData = useCallback(async () => {
    try {
      const state = await federatedApi.getState();
      
      // Map API data to component format (defensive: handle undefined councils)
      const mappedCouncils: CouncilView[] = (state.councils || []).map((c: ApiCouncilView) => ({
        ...c,
        icon: getCouncilIcon(c.type),
        color: getCouncilColor(c.type)
      }));
      
      // Only use demo data in Demo Mode
      setCouncilViews(mappedCouncils.length > 0 ? mappedCouncils : (isDemoMode ? getDefaultCouncilViews() : []));
      setChittaNodes(state.chitta?.nodes || (isDemoMode ? getDefaultChittaNodes() : []));
      setDeliberationSteps(state.deliberation_steps || (isDemoMode ? getDefaultDeliberation() : []));
      setLatestDecision(state.latest_decision || (isDemoMode ? getDefaultDecision() : null));
      
      // Use API coherence or calculate from agents
      setCoherence({
        total: state.coherence?.total || Math.round(agentsCoherence?.total_coherence || 75),
        harmony: state.coherence?.harmony || Math.round(agentsCoherence?.harmony || 80),
        performance: state.coherence?.performance || Math.round(agentsCoherence?.performance || 100),
        chitta_health: state.coherence?.chitta_health || 85,
        deliberation_quality: state.coherence?.deliberation_quality || 70,
        buddhi_clarity: state.coherence?.buddhi_clarity || 75
      });

    } catch (error) {
      console.error('Failed to fetch federated data:', error);
      // Only use demo data in Demo Mode, otherwise show empty states
      if (isDemoMode) {
        setCouncilViews(getDefaultCouncilViews());
        setChittaNodes(getDefaultChittaNodes());
        setDeliberationSteps(getDefaultDeliberation());
        setLatestDecision(getDefaultDecision());
      }
    }
  }, [agentsCoherence]);

  const runAnalysis = async () => {
    setIsAnalyzing(true);
    try {
      // Try Federated Triad API first, fallback to agents API
      const result = await federatedApi.runCycle();
      setLastAnalysis(result.insights);
      setLatestDecision(result.decision);
      setCoherence(prev => ({
        ...prev,
        total: result.coherence.total,
        harmony: result.coherence.harmony,
        performance: result.coherence.performance
      }));
      await fetchAgentTrades();
      await fetchFederatedData();
    } catch (error) {
      console.error('Failed to run analysis:', error);
      // Fallback to legacy API
      try {
        const legacyResult = await agentsApi.runCycle();
        setLastAnalysis(legacyResult.insights);
        await fetchAgentTrades();
      } catch (legacyError) {
        console.error('Legacy API also failed:', legacyError);
      }
    } finally {
      setIsAnalyzing(false);
    }
  };

  const activeCount = agentsStatus.filter((s) => s.status === 'running').length;

  // Recent logs from agent trades
  const recentLogs = agentTrades.slice(0, 5).map((t) => ({
    id: t.id,
    timestamp: new Date(t.timestamp),
    type: t.side === 'buy' ? 'success' : 'info',
    message: `${t.side === 'buy' ? 'Buy' : 'Sell'} order: ${t.amount} ${t.symbol} @ €${t.price.toLocaleString()}`,
  }));

  const logColors: Record<string, string> = {
    info: 'text-trade-blue',
    success: 'text-trade-green',
    warning: 'text-trade-orange',
    error: 'text-trade-red',
  };

  // Get Guna distribution from agent status
  const orchestrator = agentsStatus.find(a => a.id === 'orchestrator_v1');
  const gunaBalance = (orchestrator as unknown as Record<string, unknown>)?.guna_balance as Record<string, number> | undefined;
  const gunaDistribution = gunaBalance || {
    sattva: 0.5, rajas: 0.3, tamas: 0.2
  };

  if (isLoadingAgents && agentsStatus.length === 0) {
    return (
      <Card className='bg-[#111111] border-[#262626] animate-fade-in opacity-0' style={{ animationFillMode: 'forwards', animationDelay: '350ms' }}>
        <CardContent className='flex items-center justify-center py-10'>
          <Loader2 className='w-6 h-6 text-trade-blue animate-spin' />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card
      className={cn('bg-[#111111] border-[#262626] overflow-hidden', 'animate-fade-in opacity-0')}
      style={{ animationFillMode: 'forwards', animationDelay: '350ms' }}
    >
      <CardHeader className='pb-3'>
        <div className='flex items-center justify-between'>
          <div className='flex items-center gap-2'>
            <div className='relative'>
              <div className='w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center shadow-lg shadow-purple-500/20'>
                <Workflow className='w-6 h-6 text-white' />
              </div>
              {activeCount > 0 && (
                <span className='absolute -top-1 -right-1 w-3 h-3 bg-emerald-400 rounded-full animate-pulse shadow-lg shadow-emerald-400/50' />
              )}
              {/* Orbiting dots effect */}
              <div className="absolute inset-0 animate-spin-slow">
                <div className="absolute -top-1 left-1/2 w-1.5 h-1.5 bg-blue-400 rounded-full shadow-lg shadow-blue-400/50" />
                <div className="absolute top-1/2 -right-1 w-1.5 h-1.5 bg-orange-400 rounded-full shadow-lg shadow-orange-400/50" />
                <div className="absolute -bottom-1 left-1/2 w-1.5 h-1.5 bg-purple-400 rounded-full shadow-lg shadow-purple-400/50" />
              </div>
            </div>
            <div>
              <CardTitle className='text-lg font-semibold text-white'>Federated Triad</CardTitle>
              <div className='flex items-center gap-2'>
                <span
                  className={cn(
                    'text-xs px-2 py-0.5 rounded-full border',
                    activeCount > 0
                      ? 'bg-trade-green/10 text-trade-green border-trade-green/20'
                      : 'bg-muted/10 text-muted-foreground border-muted/20'
                  )}
                >
                  {activeCount > 0 ? 'Coherent' : 'Idle'}
                </span>
                {isDemoMode && (
                  <span className='text-xs px-2 py-0.5 rounded-full border bg-amber-500/10 text-amber-400 border-amber-500/20'>
                    DEMO
                  </span>
                )}
                <span className='text-xs text-muted-foreground'>5 Councils Active</span>
              </div>
            </div>
          </div>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger>
                <Info className='w-4 h-4 text-muted-foreground opacity-50 hover:opacity-100' />
              </TooltipTrigger>
              <TooltipContent side="left" className="max-w-[320px] bg-[#1A1A1A] border-[#333333] p-4">
                <p className="text-sm font-medium text-white mb-3 flex items-center gap-2">
                  <Workflow className='w-4 h-4 text-purple-400' />
                  Federated Triad Architecture
                </p>
                <div className="space-y-2 text-xs">
                  <div className='flex items-center gap-2 p-2 rounded-lg bg-blue-500/10 border border-blue-500/20'>
                    <Layers className='w-4 h-4 text-blue-400' />
                    <span className="text-gray-300"><span className="text-blue-400 font-medium">Chitta</span>: Shared knowledge graph</span>
                  </div>
                  <div className='flex items-center gap-2 p-2 rounded-lg bg-purple-500/10 border border-purple-500/20'>
                    <Users className='w-4 h-4 text-purple-400' />
                    <span className="text-gray-300"><span className="text-purple-400 font-medium">5 Councils</span>: Guna, Elemental, Graha</span>
                  </div>
                  <div className='flex items-center gap-2 p-2 rounded-lg bg-orange-500/10 border border-orange-500/20'>
                    <GitMerge className='w-4 h-4 text-orange-400' />
                    <span className="text-gray-300"><span className="text-orange-400 font-medium">Cooperative</span>: Iterative deliberation</span>
                  </div>
                  <div className='flex items-center gap-2 p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20'>
                    <Crown className='w-4 h-4 text-emerald-400' />
                    <span className="text-gray-300"><span className="text-emerald-400 font-medium">Buddhi</span>: Cross-verification</span>
                  </div>
                </div>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      </CardHeader>

      <CardContent className='space-y-4'>
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid grid-cols-4 bg-[#0A0A0A] h-9 p-1">
            <TabsTrigger value="overview" className="text-xs flex items-center gap-1 data-[state=active]:bg-[#1A1A1A] data-[state=active]:text-white">
              <Target className='w-3 h-3' />
              <span className='hidden sm:inline'>Overview</span>
            </TabsTrigger>
            <TabsTrigger value="councils" className="text-xs flex items-center gap-1 data-[state=active]:bg-[#1A1A1A] data-[state=active]:text-white">
              <Users className='w-3 h-3' />
              <span className='hidden sm:inline'>Councils</span>
            </TabsTrigger>
            <TabsTrigger value="chitta" className="text-xs flex items-center gap-1 data-[state=active]:bg-[#1A1A1A] data-[state=active]:text-white">
              <Layers className='w-3 h-3' />
              <span className='hidden sm:inline'>Chitta</span>
            </TabsTrigger>
            <TabsTrigger value="decision" className="text-xs flex items-center gap-1 data-[state=active]:bg-[#1A1A1A] data-[state=active]:text-white">
              <Crown className='w-3 h-3' />
              <span className='hidden sm:inline'>Buddhi</span>
            </TabsTrigger>
          </TabsList>

          {/* OVERVIEW TAB */}
          <TabsContent value="overview" className="space-y-4 mt-4">
            {/* Total Coherence with Icons */}
            <div className='bg-gradient-to-br from-[#0A0A0A] to-[#111111] rounded-xl p-4 border border-[#262626] relative overflow-hidden'>
              {/* Background glow effect */}
              <div className={cn(
                'absolute top-0 right-0 w-32 h-32 rounded-full blur-3xl opacity-20',
                coherence.total >= 80 ? 'bg-emerald-500' : 
                coherence.total >= 60 ? 'bg-blue-500' : 
                coherence.total >= 40 ? 'bg-orange-500' : 'bg-red-500'
              )} />
              
              <div className='flex items-center justify-between mb-3 relative'>
                <div className='flex items-center gap-2'>
                  <div className='p-1.5 rounded-lg bg-gradient-to-br from-indigo-500/20 to-purple-500/20'>
                    <Target className='w-4 h-4 text-indigo-400' />
                  </div>
                  <span className='text-sm font-medium text-white'>System Coherence</span>
                </div>
                <Badge className={cn(
                  'border-0 text-xs',
                  coherence.total >= 80 ? 'bg-emerald-500/20 text-emerald-400' :
                  coherence.total >= 50 ? 'bg-orange-500/20 text-orange-400' :
                  'bg-red-500/20 text-red-400'
                )}>
                  {coherence.total >= 80 ? 'High' : coherence.total >= 50 ? 'Medium' : 'Low'}
                </Badge>
              </div>
              
              <div className='flex items-baseline gap-2 mb-4 relative'>
                <span className={cn(
                  'text-5xl font-bold font-mono tracking-tight',
                  coherence.total >= 80 ? 'text-emerald-400' : 
                  coherence.total >= 60 ? 'text-blue-400' : 
                  coherence.total >= 40 ? 'text-orange-400' : 'text-red-400'
                )}>
                  {coherence.total}
                  <span className='text-2xl'>%</span>
                </span>
              </div>

              {/* Sub-metrics Grid with Icons */}
              <div className='grid grid-cols-2 gap-3 relative'>
                <div className='space-y-1.5'>
                  <div className='flex justify-between text-xs items-center'>
                    <div className='flex items-center gap-1'>
                      <Users className='w-3 h-3 text-blue-400' />
                      <span className='text-muted-foreground'>Harmony</span>
                    </div>
                    <span className='text-white font-mono'>{coherence.harmony}%</span>
                  </div>
                  <div className='h-1.5 bg-[#1A1A1A] rounded-full overflow-hidden'>
                    <div 
                      className='h-full bg-gradient-to-r from-blue-500 to-blue-400 rounded-full transition-all duration-500'
                      style={{ width: `${coherence.harmony}%` }}
                    />
                  </div>
                </div>
                <div className='space-y-1.5'>
                  <div className='flex justify-between text-xs items-center'>
                    <div className='flex items-center gap-1'>
                      <TrendingUp className='w-3 h-3 text-emerald-400' />
                      <span className='text-muted-foreground'>Performance</span>
                    </div>
                    <span className={cn('font-mono', coherence.performance >= 100 ? 'text-emerald-400' : 'text-white')}>
                      {coherence.performance >= 100 ? '+' : ''}{coherence.performance - 100}%
                    </span>
                  </div>
                  <div className='h-1.5 bg-[#1A1A1A] rounded-full overflow-hidden'>
                    <div 
                      className='h-full bg-gradient-to-r from-emerald-500 to-emerald-400 rounded-full transition-all duration-500'
                      style={{ width: `${Math.min(coherence.performance, 150)}%` }}
                    />
                  </div>
                </div>
                <div className='space-y-1.5'>
                  <div className='flex justify-between text-xs items-center'>
                    <div className='flex items-center gap-1'>
                      <Layers className='w-3 h-3 text-purple-400' />
                      <span className='text-muted-foreground'>Chitta Health</span>
                    </div>
                    <span className='text-white font-mono'>{coherence.chitta_health}%</span>
                  </div>
                  <div className='h-1.5 bg-[#1A1A1A] rounded-full overflow-hidden'>
                    <div 
                      className='h-full bg-gradient-to-r from-purple-500 to-purple-400 rounded-full transition-all duration-500'
                      style={{ width: `${coherence.chitta_health}%` }}
                    />
                  </div>
                </div>
                <div className='space-y-1.5'>
                  <div className='flex justify-between text-xs items-center'>
                    <div className='flex items-center gap-1'>
                      <Brain className='w-3 h-3 text-pink-400' />
                      <span className='text-muted-foreground'>Buddhi Clarity</span>
                    </div>
                    <span className='text-white font-mono'>{coherence.buddhi_clarity}%</span>
                  </div>
                  <div className='h-1.5 bg-[#1A1A1A] rounded-full overflow-hidden'>
                    <div 
                      className='h-full bg-gradient-to-r from-pink-500 to-pink-400 rounded-full transition-all duration-500'
                      style={{ width: `${coherence.buddhi_clarity}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Guna Balance with Icons */}
            <div className='bg-[#0A0A0A] rounded-xl p-3 border border-[#262626]'>
              <div className='flex items-center gap-2 mb-3'>
                <div className='p-1 rounded bg-blue-500/20'>
                  <Scale className='w-4 h-4 text-blue-400' />
                </div>
                <span className='text-xs text-muted-foreground'>3 Guna Balance</span>
              </div>
              <div className='flex h-3 rounded-full overflow-hidden shadow-inner'>
                <div 
                  className='bg-gradient-to-r from-blue-500 to-blue-400 h-full transition-all duration-500' 
                  style={{ width: `${(gunaDistribution?.sattva || 0.5) * 100}%` }}
                  title={`Sattva (Harmony): ${((gunaDistribution?.sattva || 0.5) * 100).toFixed(0)}%`}
                />
                <div 
                  className='bg-gradient-to-r from-orange-500 to-orange-400 h-full transition-all duration-500' 
                  style={{ width: `${(gunaDistribution?.rajas || 0.3) * 100}%` }}
                  title={`Rajas (Activity): ${((gunaDistribution?.rajas || 0.3) * 100).toFixed(0)}%`}
                />
                <div 
                  className='bg-gradient-to-r from-red-500 to-red-400 h-full transition-all duration-500' 
                  style={{ width: `${(gunaDistribution?.tamas || 0.2) * 100}%` }}
                  title={`Tamas (Inertia): ${((gunaDistribution?.tamas || 0.2) * 100).toFixed(0)}%`}
                />
              </div>
              <div className='flex justify-between mt-3 text-[10px]'>
                <div className='flex items-center gap-1'>
                  <div className='w-2 h-2 rounded-full bg-blue-400' />
                  <span className='text-blue-400 font-medium'>Sattva {(gunaDistribution?.sattva || 0.5) * 100}%</span>
                </div>
                <div className='flex items-center gap-1'>
                  <div className='w-2 h-2 rounded-full bg-orange-400' />
                  <span className='text-orange-400 font-medium'>Rajas {(gunaDistribution?.rajas || 0.3) * 100}%</span>
                </div>
                <div className='flex items-center gap-1'>
                  <div className='w-2 h-2 rounded-full bg-red-400' />
                  <span className='text-red-400 font-medium'>Tamas {(gunaDistribution?.tamas || 0.2) * 100}%</span>
                </div>
              </div>
            </div>

            {/* Latest Decision Preview */}
            {latestDecision && (
              <div className={cn(
                'rounded-xl p-4 border relative overflow-hidden',
                latestDecision.action === 'buy' ? 'bg-emerald-500/5 border-emerald-500/30' :
                latestDecision.action === 'sell' ? 'bg-red-500/5 border-red-500/30' :
                'bg-orange-500/5 border-orange-500/30'
              )}>
                {/* Glow effect */}
                <div className={cn(
                  'absolute -top-10 -right-10 w-20 h-20 rounded-full blur-2xl opacity-30',
                  latestDecision.action === 'buy' ? 'bg-emerald-500' :
                  latestDecision.action === 'sell' ? 'bg-red-500' :
                  'bg-orange-500'
                )} />
                
                <div className='flex items-center justify-between mb-2 relative'>
                  <span className='text-xs text-muted-foreground flex items-center gap-1'>
                    <Shield className='w-3 h-3' />
                    Buddhi Decision
                  </span>
                  <Badge className={cn(
                    'text-xs capitalize border-0 shadow-lg',
                    latestDecision.action === 'buy' ? 'bg-emerald-500 text-white shadow-emerald-500/25' :
                    latestDecision.action === 'sell' ? 'bg-red-500 text-white shadow-red-500/25' :
                    'bg-orange-500 text-white shadow-orange-500/25'
                  )}>
                    {latestDecision.action === 'buy' && <TrendingUp className='w-3 h-3 mr-1' />}
                    {latestDecision.action === 'sell' && <TrendingUp className='w-3 h-3 mr-1 rotate-180' />}
                    {latestDecision.action === 'hold' && <CircleDot className='w-3 h-3 mr-1' />}
                    {latestDecision.action}
                  </Badge>
                </div>
                <p className='text-sm text-white relative'>{latestDecision.rationale}</p>
                <div className='flex items-center gap-4 mt-3 text-xs relative'>
                  <div className='flex items-center gap-1'>
                    <Gauge className='w-3 h-3 text-muted-foreground' />
                    <span className='text-muted-foreground'>{Math.round(latestDecision.confidence * 100)}% conf</span>
                  </div>
                  <div className='flex items-center gap-1'>
                    <CheckCircle2 className='w-3 h-3 text-emerald-400' />
                    <span className='text-emerald-400'>{latestDecision.supporting.length} supporting</span>
                  </div>
                  {latestDecision.contradictions > 0 && (
                    <div className='flex items-center gap-1'>
                      <AlertTriangle className='w-3 h-3 text-orange-400' />
                      <span className='text-orange-400'>{latestDecision.contradictions} resolved</span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </TabsContent>

          {/* COUNCILS TAB */}
          <TabsContent value="councils" className="space-y-3 mt-4">
            <div className='text-xs text-muted-foreground mb-2 flex items-center gap-1'>
              <Network className='w-3 h-3' />
              <span>5 Council Views (Iterative Deliberation)</span>
            </div>
            
            {councilViews.map((council, idx) => (
              <div key={council.name} className={cn(
                'rounded-xl p-4 border transition-all duration-300 hover:scale-[1.02]',
                council.bgColor || 'bg-[#0A0A0A]',
                council.borderColor || 'border-[#262626]'
              )}>
                <div className='flex items-center justify-between mb-3'>
                  <div className='flex items-center gap-3'>
                    <div className={cn(
                      'w-10 h-10 rounded-xl flex items-center justify-center shadow-lg',
                      council.bgColor || 'bg-[#1A1A1A]'
                    )}>
                      <span className={cn('text-lg', council.color)}>
                        {council.symbol}
                      </span>
                    </div>
                    <div>
                      <span className='text-sm font-medium text-white block'>{council.name}</span>
                      <span className='text-[10px] text-muted-foreground uppercase tracking-wider'>
                        {council.type} council
                      </span>
                    </div>
                  </div>
                  <div className='flex items-center gap-2'>
                    <div className='flex items-center gap-1 px-2 py-1 rounded-lg bg-black/30'>
                      <Gauge className='w-3 h-3 text-muted-foreground' />
                      <span className='text-xs font-mono text-white'>
                        {Math.round(council.confidence * 100)}%
                      </span>
                    </div>
                    {council.type === 'mind' && (
                      <Badge className='text-[10px] bg-emerald-500 text-white border-0'>
                        <Crown className='w-3 h-3 mr-1' />
                        BUDDHI
                      </Badge>
                    )}
                  </div>
                </div>
                
                <div className='flex items-center gap-2 mb-2'>
                  <span className='text-xs text-muted-foreground'>Perspective:</span>
                  <span className='text-xs text-white font-mono'>{council.perspective}</span>
                </div>

                <div className='space-y-2'>
                  {council.insights.map((insight, i) => (
                    <div key={i} className='flex items-center gap-2 text-xs'>
                      <div className={cn(
                        'w-5 h-5 rounded flex items-center justify-center',
                        council.bgColor || 'bg-[#1A1A1A]'
                      )}>
                        <Sparkle className={cn('w-3 h-3', council.color)} />
                      </div>
                      <span className='text-gray-300'>{insight}</span>
                    </div>
                  ))}
                </div>

                {council.contradictions && council.contradictions.length > 0 && (
                  <div className='mt-2 flex items-center gap-2 text-xs text-trade-orange'>
                    <AlertTriangle className='w-3 h-3' />
                    <span>Contradicts: {council.contradictions.join(', ')}</span>
                  </div>
                )}

                {/* Show deliberation arrows between councils */}
                {idx < councilViews.length - 1 && (
                  <div className='flex justify-center my-2'>
                    <div className='flex flex-col items-center text-[#333333]'>
                      <GitMerge className='w-4 h-4 rotate-90' />
                      <span className='text-[10px]'>iterates</span>
                    </div>
                  </div>
                )}
              </div>
            ))}

            {/* Deliberation Summary */}
            <div className='bg-[#0A0A0A] rounded-xl p-4 border border-[#262626]'>
              <div className='flex items-center gap-2 mb-3'>
                <div className='p-1 rounded bg-orange-500/20'>
                  <GitMerge className='w-4 h-4 text-orange-400' />
                </div>
                <span className='text-xs font-medium text-white'>Cooperative Deliberation</span>
                <Badge className='text-[10px] bg-orange-500/20 text-orange-400 border-0'>
                  {deliberationSteps.length} steps
                </Badge>
              </div>
              <div className='space-y-2'>
                {deliberationSteps.map((step, idx) => (
                  <div key={idx} className='flex items-center gap-2 text-xs p-2 rounded-lg bg-[#111111] border border-[#222222]'>
                    <div className='w-5 h-5 rounded-full bg-[#1A1A1A] flex items-center justify-center text-[10px] text-muted-foreground'>
                      {step.iteration}
                    </div>
                    <span className={cn(
                      'px-1.5 py-0.5 rounded text-[10px]',
                      step.council === 'Guna' && 'bg-blue-500/20 text-blue-400',
                      step.council === 'Elemental' && 'bg-orange-500/20 text-orange-400',
                      step.council === 'Graha' && 'bg-purple-500/20 text-purple-400',
                    )}>
                      {step.council}
                    </span>
                    <span className='text-[#666666]'>→</span>
                    <span className='text-white'>{step.perspective}</span>
                    {step.reaction_to && (
                      <Badge variant="outline" className='text-[10px] h-4 border-[#333333] text-[#888888]'>
                        reacts to {step.reaction_to}
                      </Badge>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </TabsContent>

          {/* CHITTA TAB */}
          <TabsContent value="chitta" className="space-y-3 mt-4">
            <div className='text-xs text-muted-foreground mb-2 flex items-center gap-1'>
              <Layers className='w-3 h-3' />
              <span>Chitta Mahasagar (Shared Knowledge Graph)</span>
            </div>

            {/* Chitta Stats with Icons */}
            <div className='grid grid-cols-3 gap-2'>
              <div className='bg-[#0A0A0A] rounded-lg p-3 border border-[#262626] text-center'>
                <div className='flex justify-center mb-1'>
                  <Layers className='w-5 h-5 text-blue-400' />
                </div>
                <div className='text-xl font-bold text-white font-mono'>{chittaNodes.length}</div>
                <div className='text-[10px] text-muted-foreground'>Total Nodes</div>
              </div>
              <div className='bg-[#0A0A0A] rounded-lg p-3 border border-[#262626] text-center'>
                <div className='flex justify-center mb-1'>
                  <CheckCircle2 className='w-5 h-5 text-emerald-400' />
                </div>
                <div className='text-xl font-bold text-emerald-400 font-mono'>
                  {chittaNodes.filter(n => n.verified).length}
                </div>
                <div className='text-[10px] text-muted-foreground'>Verified</div>
              </div>
              <div className='bg-[#0A0A0A] rounded-lg p-3 border border-[#262626] text-center'>
                <div className='flex justify-center mb-1'>
                  <Users className='w-5 h-5 text-purple-400' />
                </div>
                <div className='text-xl font-bold text-purple-400 font-mono'>
                  {new Set(chittaNodes.map(n => n.council)).size}
                </div>
                <div className='text-[10px] text-muted-foreground'>Sources</div>
              </div>
            </div>

            {/* Knowledge Nodes with Council Icons */}
            <ScrollArea className='h-[280px]'>
              <div className='space-y-2'>
                {chittaNodes.map((node) => {
                  const councilIcons: Record<string, React.ReactNode> = {
                    'Body': <Cpu className='w-3 h-3 text-red-400' />,
                    'Guna': <Scale className='w-3 h-3 text-blue-400' />,
                    'Elemental': <Flame className='w-3 h-3 text-orange-400' />,
                    'Graha': <Telescope className='w-3 h-3 text-purple-400' />,
                    'Mind': <Crown className='w-3 h-3 text-emerald-400' />,
                  };
                  return (
                    <div 
                      key={node.id} 
                      className={cn(
                        'p-3 rounded-xl border transition-all duration-300',
                        node.verified 
                          ? 'bg-[#0A0A0A] border-[#262626] hover:border-[#333333]' 
                          : 'bg-[#0A0A0A]/50 border-[#262626]/50'
                      )}
                    >
                      <div className='flex items-start justify-between gap-2'>
                        <div className='flex-1 min-w-0'>
                          <p className={cn(
                            'text-sm truncate',
                            node.verified ? 'text-white' : 'text-gray-500'
                          )}>
                            {node.content}
                          </p>
                          <div className='flex items-center gap-2 mt-2'>
                            <Badge 
                              variant="outline" 
                              className={cn(
                                'text-[10px] h-5 flex items-center gap-1 border-0',
                                node.council === 'Body' && 'bg-red-500/10 text-red-400',
                                node.council === 'Guna' && 'bg-blue-500/10 text-blue-400',
                                node.council === 'Elemental' && 'bg-orange-500/10 text-orange-400',
                                node.council === 'Graha' && 'bg-purple-500/10 text-purple-400',
                                node.council === 'Mind' && 'bg-emerald-500/10 text-emerald-400',
                              )}
                            >
                              {councilIcons[node.council] || <CircleDot className='w-3 h-3' />}
                              {node.council}
                            </Badge>
                            <span className='text-[10px] text-muted-foreground'>{node.timestamp}</span>
                          </div>
                        </div>
                        <div className={cn(
                          'w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0',
                          node.verified ? 'bg-emerald-500/20' : 'bg-gray-500/10'
                        )}>
                          {node.verified ? (
                            <CheckCircle2 className='w-4 h-4 text-emerald-400' />
                          ) : (
                            <CircleDot className='w-4 h-4 text-gray-500' />
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </ScrollArea>

            {/* Chitta Info */}
            <div className='bg-[#0A0A0A] rounded-xl p-3 border border-[#262626]'>
              <div className='flex items-center gap-2 mb-3'>
                <div className='p-1 rounded bg-blue-500/20'>
                  <Eye className='w-4 h-4 text-blue-400' />
                </div>
                <span className='text-xs font-medium text-white'>Cross-Council Visibility</span>
              </div>
              <div className='space-y-2 text-xs'>
                <div className='flex items-center gap-2 p-2 rounded-lg bg-[#111111] border border-[#222222]'>
                  <div className='w-6 h-6 rounded flex items-center justify-center bg-purple-500/20'>
                    <Microscope className='w-3 h-3 text-purple-400' />
                  </div>
                  <span className="text-gray-400"><span className='text-purple-400 font-medium'>Guna/Elemental/Graha</span>: Own nodes + market</span>
                </div>
                <div className='flex items-center gap-2 p-2 rounded-lg bg-[#111111] border border-[#222222]'>
                  <div className='w-6 h-6 rounded flex items-center justify-center bg-emerald-500/20'>
                    <Crown className='w-3 h-3 text-emerald-400' />
                  </div>
                  <span className="text-gray-400"><span className='text-emerald-400 font-medium'>Mind (Buddhi)</span>: Sees ALL nodes</span>
                </div>
                <div className='flex items-center gap-2 p-2 rounded-lg bg-[#111111] border border-[#222222]'>
                  <div className='w-6 h-6 rounded flex items-center justify-center bg-red-500/20'>
                    <Radio className='w-3 h-3 text-red-400' />
                  </div>
                  <span className="text-gray-400"><span className='text-red-400 font-medium'>Body</span>: Ingests raw data</span>
                </div>
              </div>
            </div>
          </TabsContent>

          {/* BUDDHI TAB */}
          <TabsContent value="decision" className="space-y-3 mt-4">
            {latestDecision ? (
              <>
                {/* Main Decision */}
                <div className={cn(
                  'rounded-xl p-4 border',
                  latestDecision.action === 'buy' ? 'bg-trade-green/10 border-trade-green/30' :
                  latestDecision.action === 'sell' ? 'bg-trade-red/10 border-trade-red/30' :
                  'bg-trade-orange/10 border-trade-orange/30'
                )}>
                  <div className='flex items-center justify-between mb-3'>
                    <div className='flex items-center gap-2'>
                      <Brain className={cn(
                        'w-5 h-5',
                        latestDecision.action === 'buy' ? 'text-trade-green' :
                        latestDecision.action === 'sell' ? 'text-trade-red' :
                        'text-trade-orange'
                      )} />
                      <span className='font-medium text-white'>Buddhi Synthesis</span>
                    </div>
                    <Badge className={cn(
                      'text-sm capitalize px-3 py-1',
                      latestDecision.action === 'buy' ? 'bg-trade-green text-white' :
                      latestDecision.action === 'sell' ? 'bg-trade-red text-white' :
                      'bg-trade-orange text-white'
                    )}>
                      {latestDecision.action}
                    </Badge>
                  </div>

                  <div className='flex items-baseline gap-2 mb-3'>
                    <span className='text-3xl font-bold font-mono text-white'>
                      {latestDecision.confidence * 100}%
                    </span>
                    <span className='text-sm text-muted-foreground'>confidence</span>
                  </div>

                  <p className='text-sm text-white mb-4'>{latestDecision.rationale}</p>

                  {/* Supporting vs Opposing */}
                  <div className='grid grid-cols-2 gap-3'>
                    <div className='bg-[#0A0A0A] rounded-lg p-3'>
                      <div className='flex items-center gap-2 mb-2'>
                        <CheckCircle2 className='w-4 h-4 text-trade-green' />
                        <span className='text-xs text-muted-foreground'>Supporting</span>
                      </div>
                      <div className='flex flex-wrap gap-1'>
                        {latestDecision.supporting.map((s) => (
                          <Badge key={s} variant="outline" className='text-[10px] border-trade-green/30 text-trade-green'>
                            {s}
                          </Badge>
                        ))}
                      </div>
                    </div>
                    <div className='bg-[#0A0A0A] rounded-lg p-3'>
                      <div className='flex items-center gap-2 mb-2'>
                        <AlertTriangle className='w-4 h-4 text-trade-red' />
                        <span className='text-xs text-muted-foreground'>Opposing</span>
                      </div>
                      <div className='flex flex-wrap gap-1'>
                        {latestDecision.opposing.length > 0 ? (
                          latestDecision.opposing.map((s) => (
                            <Badge key={s} variant="outline" className='text-[10px] border-trade-red/30 text-trade-red'>
                              {s}
                            </Badge>
                          ))
                        ) : (
                          <span className='text-xs text-[#666666]'>None</span>
                        )}
                      </div>
                    </div>
                  </div>

                  {latestDecision.contradictions > 0 && (
                    <div className='mt-3 flex items-center gap-2 text-xs text-trade-orange bg-trade-orange/10 rounded-lg p-2'>
                      <AlertTriangle className='w-4 h-4' />
                      <span>{latestDecision.contradictions} contradiction(s) detected and resolved</span>
                    </div>
                  )}
                </div>

                {/* Decision Process with Visual Flow */}
                <div className='bg-[#0A0A0A] rounded-xl p-4 border border-[#262626]'>
                  <div className='flex items-center gap-2 mb-4'>
                    <GitBranch className='w-4 h-4 text-blue-400' />
                    <span className='text-xs font-medium text-white'>5-Stage Decision Flow</span>
                  </div>
                  <div className='space-y-3'>
                    <div className='flex items-center gap-3 group'>
                      <div className='w-8 h-8 rounded-lg bg-red-500/20 flex items-center justify-center group-hover:scale-110 transition-transform'>
                        <Radio className='w-4 h-4 text-red-400' />
                      </div>
                      <div className='flex-1'>
                        <span className='text-xs text-white font-medium'>1. Body Ingestion</span>
                        <p className='text-[10px] text-muted-foreground'>Raw market data → Chitta</p>
                      </div>
                    </div>
                    <div className='flex items-center gap-3 group'>
                      <div className='w-8 h-8 rounded-lg bg-purple-500/20 flex items-center justify-center group-hover:scale-110 transition-transform'>
                        <Microscope className='w-4 h-4 text-purple-400' />
                      </div>
                      <div className='flex-1'>
                        <span className='text-xs text-white font-medium'>2. Council Analysis</span>
                        <p className='text-[10px] text-muted-foreground'>Guna/Elemental/Graha perspectives</p>
                      </div>
                    </div>
                    <div className='flex items-center gap-3 group'>
                      <div className='w-8 h-8 rounded-lg bg-orange-500/20 flex items-center justify-center group-hover:scale-110 transition-transform'>
                        <GitMerge className='w-4 h-4 text-orange-400' />
                      </div>
                      <div className='flex-1'>
                        <span className='text-xs text-white font-medium'>3. Deliberation</span>
                        <p className='text-[10px] text-muted-foreground'>Iterative council cooperation (3 cycles)</p>
                      </div>
                    </div>
                    <div className='flex items-center gap-3 group'>
                      <div className='w-8 h-8 rounded-lg bg-emerald-500/20 flex items-center justify-center group-hover:scale-110 transition-transform'>
                        <Shield className='w-4 h-4 text-emerald-400' />
                      </div>
                      <div className='flex-1'>
                        <span className='text-xs text-white font-medium'>4. Buddhi Synthesis</span>
                        <p className='text-[10px] text-muted-foreground'>Cross-verification & contradiction resolution</p>
                      </div>
                    </div>
                    <div className='flex items-center gap-3 group'>
                      <div className='w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center group-hover:scale-110 transition-transform'>
                        <Zap className='w-4 h-4 text-blue-400' />
                      </div>
                      <div className='flex-1'>
                        <span className='text-xs text-white font-medium'>5. Execution</span>
                        <p className='text-[10px] text-muted-foreground'>Body executes final decision</p>
                      </div>
                    </div>
                  </div>
                </div>
              </>
            ) : (
              <div className='flex flex-col items-center justify-center py-10 text-muted-foreground'>
                <Brain className='w-12 h-12 mb-3 opacity-20' />
                <p className='text-sm'>No decision yet</p>
                <p className='text-xs'>Run analysis to generate a decision</p>
              </div>
            )}
          </TabsContent>
        </Tabs>

        {/* Run Analysis Button */}
        <Button
          onClick={runAnalysis}
          disabled={isAnalyzing}
          className='w-full bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 hover:opacity-90 text-white shadow-lg shadow-purple-500/25 border-0 h-11'
        >
          {isAnalyzing ? (
            <>
              <Loader2 className='w-5 h-5 mr-2 animate-spin' />
              <span className='font-medium'>Running Federated Cycle...</span>
            </>
          ) : (
            <>
              <Workflow className='w-5 h-5 mr-2' />
              <span className='font-medium'>Run Triad Analysis</span>
            </>
          )}
        </Button>

        {/* Last Analysis Result */}
        {lastAnalysis && (
          <div className='bg-[#0A0A0A] rounded-lg p-3 border border-trade-purple/20'>
            <p className='text-xs text-trade-purple mb-1 flex items-center gap-1'>
              <Sparkles className='w-3 h-3' />
              Latest Analysis
            </p>
            <p className='text-sm text-white whitespace-pre-line'>{lastAnalysis}</p>
          </div>
        )}

        {/* Recent Activity */}
        {recentLogs.length > 0 && (
          <div className='pt-3 border-t border-[#262626]'>
            <div className='flex items-center gap-2 mb-3'>
              <History className='w-4 h-4 text-muted-foreground' />
              <span className='text-sm text-muted-foreground'>Recent Activity</span>
            </div>
            <ScrollArea className='h-[100px]'>
              <div className='space-y-2'>
                {recentLogs.map((log) => (
                  <div key={log.id} className='flex items-center gap-3 text-sm p-2 rounded-lg bg-[#0A0A0A] hover:bg-[#1A1A1A] transition-colors'>
                    <div className={cn(
                      'w-2 h-2 rounded-full',
                      log.type === 'success' ? 'bg-emerald-400 shadow-lg shadow-emerald-400/50' :
                      log.type === 'error' ? 'bg-red-400' :
                      'bg-blue-400'
                    )} />
                    <span className='text-xs text-muted-foreground whitespace-nowrap font-mono'>
                      {log.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                    <span className={cn('text-xs', logColors[log.type])}>{log.message}</span>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
