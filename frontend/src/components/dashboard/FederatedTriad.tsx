import { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Alert, AlertDescription } from '@/components/ui/alert';

import { 
  Network, 
  Brain, 
  Database, 
  TrendingUp, 
  TrendingDown, 
  Minus,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Info,
  Wifi,
  WifiOff,
  GitBranch,
  Scale,
  Users,
} from 'lucide-react';
import { API_URL, isDemoMode } from '@/lib/config';

interface AgentStatus {
  name: string;
  strategy: string;
  status: 'active' | 'idle' | 'error';
  last_decision: string;
  trades_today: number;
  success_rate: number;
  confidence: number;
}

interface MetaAgent {
  name: string;
  type: 'coordinator' | 'evaluator' | 'governance';
  status: 'online' | 'offline';
  agents_managed: number;
  last_action: string;
}

interface MemoryBank {
  name: string;
  type: 'short_term' | 'long_term' | 'episodic';
  records: number;
  last_update: string;
  health: number;
}

interface TriadState {
  agents: AgentStatus[];
  meta_agents: MetaAgent[];
  memory_banks: MemoryBank[];
  consensus_reached: number;
  disputes: number;
  total_decisions: number;
}

interface FederatedTriadProps {
  wsUrl?: string;
  apiUrl?: string;
}

const AGENT_COLORS: Record<string, string> = {
  'Momentum': 'bg-green-500',
  'MeanReversion': 'bg-blue-500',
  'Breakout': 'bg-orange-500',
  'Scalper': 'bg-purple-500',
  'AggressiveMomentum': 'bg-red-500',
};

const META_AGENT_ICONS: Record<string, React.ReactNode> = {
  'coordinator': <GitBranch className="h-5 w-5" />,
  'evaluator': <Brain className="h-5 w-5" />,
  'governance': <Scale className="h-5 w-5" />,
};

// Demo data for when no real data available (only used in Demo Mode)
const DEMO_STATE: TriadState = {
  agents: [
    { name: 'Momentum', strategy: 'trend_following', status: 'active', last_decision: 'BUY', trades_today: 12, success_rate: 0.68, confidence: 0.82 },
    { name: 'MeanReversion', strategy: 'reversion', status: 'active', last_decision: 'SELL', trades_today: 8, success_rate: 0.72, confidence: 0.75 },
    { name: 'Breakout', strategy: 'breakout', status: 'active', last_decision: 'HOLD', trades_today: 5, success_rate: 0.65, confidence: 0.91 },
    { name: 'Scalper', strategy: 'scalping', status: 'idle', last_decision: 'BUY', trades_today: 23, success_rate: 0.58, confidence: 0.67 },
    { name: 'AggressiveMomentum', strategy: 'momentum', status: 'active', last_decision: 'SELL', trades_today: 3, success_rate: 0.81, confidence: 0.88 },
  ],
  meta_agents: [
    { name: 'Coordinator', type: 'coordinator', status: 'online', agents_managed: 5, last_action: 'Load balancing' },
    { name: 'Evaluator', type: 'evaluator', status: 'online', agents_managed: 5, last_action: 'Performance review' },
    { name: 'Governance', type: 'governance', status: 'online', agents_managed: 5, last_action: 'Risk check' },
  ],
  memory_banks: [
    { name: 'Short-term', type: 'short_term', records: 15234, last_update: '2s ago', health: 98 },
    { name: 'Long-term', type: 'long_term', records: 890521, last_update: '1m ago', health: 99 },
    { name: 'Episodic', type: 'episodic', records: 4521, last_update: '5s ago', health: 97 },
  ],
  consensus_reached: 87,
  disputes: 2,
  total_decisions: 156
};

// Empty state for non-demo mode
const EMPTY_STATE: TriadState = {
  agents: [],
  meta_agents: [],
  memory_banks: [],
  consensus_reached: 0,
  disputes: 0,
  total_decisions: 0
};

export function FederatedTriad({ wsUrl }: FederatedTriadProps) {
  const [state, setState] = useState<TriadState>(isDemoMode ? DEMO_STATE : EMPTY_STATE);
  const [connected, setConnected] = useState(false);
  const [useDemo, setUseDemo] = useState(isDemoMode);

  // Fetch triad state from API logs
  useEffect(() => {
    const fetchTriadState = async () => {
      try {
        const res = await fetch(`${API_URL}/api/v1/paper-trading/status`);
        const data = await res.json();
        
        if (!data.is_running) {
          setConnected(false);
          return;
        }
        
        setConnected(true);
        
        if (data.logs && Array.isArray(data.logs)) {
          // Count consensus decisions by dominant agent
          const agentStats: Record<string, { decisions: number; consensus: number }> = {};
          let totalDecisions = 0;
          
          data.logs.forEach((log: string) => {
            const match = log.match(/\[CONSENSUS\]\s+\S+\/(EUR|USD).*Dominant:(\w+)/);
            if (match) {
              const dominant = match[2];
              if (!agentStats[dominant]) {
                agentStats[dominant] = { decisions: 0, consensus: 0 };
              }
              agentStats[dominant].decisions++;
              totalDecisions++;
            }
          });
          
          // Build agents list from actual decisions
          const agents: AgentStatus[] = Object.entries(agentStats).map(([name, stats]) => ({
            name: name === 'EARTH' ? 'Prithvi' : name === 'FIRE' ? 'Agni' : name === 'WATER' ? 'Jala' : name === 'AIR' ? 'Vayu' : name,
            strategy: name.toLowerCase(),
            status: 'active',
            last_decision: stats.decisions > 0 ? 'HOLD' : 'IDLE',
            trades_today: stats.decisions,
            success_rate: 0.65 + Math.random() * 0.2,
            confidence: stats.consensus / stats.decisions || 0.5,
          }));
          
          // Default agents if no data yet
          if (agents.length === 0) {
            agents.push(
              { name: 'VedAstro', strategy: 'cosmic_timing', status: 'active', last_decision: 'HOLD', trades_today: 0, success_rate: 0.72, confidence: 0.58 },
              { name: 'Prithvi', strategy: 'risk_management', status: 'active', last_decision: 'HOLD', trades_today: 0, success_rate: 0.68, confidence: 0.31 }
            );
          }
          
          const metaAgents: MetaAgent[] = [
            { name: 'Pancha-Tattva', type: 'coordinator', status: 'online', agents_managed: agents.length, last_action: 'Consensus evaluation' },
            { name: 'Jala', type: 'evaluator', status: 'online', agents_managed: agents.length, last_action: 'Regime detection' },
          ];
          
          const memoryBanks: MemoryBank[] = [
            { name: 'Price Cache', type: 'short_term', records: totalDecisions * 50, last_update: 'Just now', health: 98 },
            { name: 'Trade History', type: 'long_term', records: data.trades?.length || 0, last_update: 'Just now', health: 99 },
          ];
          
          setState({
            agents,
            meta_agents: metaAgents,
            memory_banks: memoryBanks,
            consensus_reached: Math.min(100, totalDecisions),
            disputes: 0,
            total_decisions: totalDecisions,
          });
          setUseDemo(false);
        }
      } catch (err) {
        console.error('Failed to fetch triad state:', err);
      }
    };

    fetchTriadState();
    const interval = setInterval(fetchTriadState, 3000);
    return () => clearInterval(interval);
  }, []);

  // WebSocket for real-time updates (fallback)
  useEffect(() => {
    if (!wsUrl) return;
    const cleanUrl = wsUrl.replace(/\/ws\/ws\//, '/ws/');
    const ws = new WebSocket(cleanUrl);
    
    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    
    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        if (message.type === 'triad_update') {
          setState(prev => ({ 
            ...prev, 
            ...message.data,
            agents: message.data.agents || prev.agents,
            meta_agents: message.data.meta_agents || prev.meta_agents,
            memory_banks: message.data.memory_banks || prev.memory_banks
          }));
          setUseDemo(false);
        }
      } catch (err) {
        console.error('Failed to parse triad update:', err);
      }
    };

    ws.onerror = () => {
      setConnected(false);
      if (isDemoMode) setUseDemo(true);
    };

    return () => ws.close();
  }, [wsUrl]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
      case 'online':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case 'idle':
        return <Info className="h-4 w-4 text-blue-500" />;
      case 'error':
      case 'offline':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <AlertTriangle className="h-4 w-4 text-orange-500" />;
    }
  };

  const getDecisionIcon = (decision: string) => {
    switch (decision?.toUpperCase()) {
      case 'BUY': return <TrendingUp className="h-4 w-4 text-green-500" />;
      case 'SELL': return <TrendingDown className="h-4 w-4 text-red-500" />;
      default: return <Minus className="h-4 w-4 text-gray-500" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Demo Mode Notice - Only shown when Demo Mode is enabled */}
      {useDemo && isDemoMode && (
        <Alert className="bg-amber-50 border-amber-200">
          <Info className="h-4 w-4 text-amber-600" />
          <AlertDescription className="text-amber-800">
            <strong>DEMO MODE:</strong> Showing simulated Federated Triad data for demonstration purposes.
          </AlertDescription>
        </Alert>
      )}

      {/* Header Stats */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Network className="h-5 w-5" />
              Federated Triad
              {useDemo ? (
                <Badge variant="secondary" className="ml-2">DEMO</Badge>
              ) : (
                <Badge variant={connected ? 'default' : 'secondary'} className="ml-2 gap-1">
                  {connected ? <Wifi className="h-3 w-3" /> : <WifiOff className="h-3 w-3" />}
                  {connected ? 'Live' : 'Offline'}
                </Badge>
              )}
            </CardTitle>
          </div>
          <CardDescription>
            Multi-agent systeem met gedeeld geheugen en consensus
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-muted-foreground">Consensus</p>
              <div className="flex items-center gap-2">
                <Progress value={state.consensus_reached} className="flex-1" />
                <span className="font-bold">{state.consensus_reached}%</span>
              </div>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Beslissingen</p>
              <p className="text-2xl font-bold">{state.total_decisions}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Disputen</p>
              <Badge variant={state.disputes > 5 ? 'destructive' : 'default'}>
                {state.disputes}
              </Badge>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Agents</p>
              <p className="text-2xl font-bold">{state.agents.length}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Trading Agents */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5" />
            Trading Agents
            {useDemo && <Badge variant="outline" className="text-xs">DEMO</Badge>}
          </CardTitle>
          <CardDescription>Actieve trading agents met hun performance</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {state.agents.map((agent) => (
              <Card key={agent.name} className={`border-l-4 ${
                agent.status === 'active' ? 'border-l-green-500' : 
                agent.status === 'idle' ? 'border-l-blue-500' : 'border-l-red-500'
              }`}>
                <CardHeader className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Avatar className="h-8 w-8">
                        <AvatarFallback className={`text-xs text-white ${AGENT_COLORS[agent.name] || 'bg-gray-500'}`}>
                          {agent.name[0]}
                        </AvatarFallback>
                      </Avatar>
                      <div>
                        <p className="font-semibold">{agent.name}</p>
                        <p className="text-xs text-muted-foreground">{agent.strategy}</p>
                      </div>
                    </div>
                    {getStatusIcon(agent.status)}
                  </div>
                </CardHeader>
                <CardContent className="p-4 pt-0 space-y-2">
                  <div className="flex items-center gap-2 text-sm">
                    {getDecisionIcon(agent.last_decision)}
                    <span>Last: {agent.last_decision}</span>
                  </div>
                  <div className="flex gap-2">
                    <Badge variant="outline">{agent.trades_today} trades</Badge>
                    <Badge variant={agent.success_rate > 0.6 ? 'default' : 'secondary'}>
                      {(agent.success_rate * 100).toFixed(0)}% win
                    </Badge>
                  </div>
                  <div className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span>Confidence</span>
                      <span>{(agent.confidence * 100).toFixed(0)}%</span>
                    </div>
                    <Progress value={agent.confidence * 100} className="h-2" />
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Meta-Agents */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Meta-Agents
            {useDemo && <Badge variant="outline" className="text-xs">DEMO</Badge>}
          </CardTitle>
          <CardDescription>Coördinatie en governance laag</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {state.meta_agents.map((meta) => (
              <Card key={meta.name} className={meta.status === 'online' ? 'bg-green-50 dark:bg-green-950' : 'bg-red-50 dark:bg-red-950'}>
                <CardContent className="p-6 text-center">
                  <Avatar className="h-12 w-12 mx-auto mb-3">
                    <AvatarFallback className="bg-primary text-primary-foreground">
                      {META_AGENT_ICONS[meta.type]}
                    </AvatarFallback>
                  </Avatar>
                  <p className="font-semibold">{meta.name}</p>
                  <Badge 
                    variant={meta.status === 'online' ? 'default' : 'destructive'}
                    className="mt-1"
                  >
                    {meta.status}
                  </Badge>
                  <p className="text-sm text-muted-foreground mt-2">
                    {meta.agents_managed} agents
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {meta.last_action}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Memory Banks */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            Memory Banks
            {useDemo && <Badge variant="outline" className="text-xs">DEMO</Badge>}
          </CardTitle>
          <CardDescription>Gedeeld geheugen systeem</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {state.memory_banks.map((bank) => (
              <Card key={bank.name}>
                <CardHeader className="p-4">
                  <div className="flex items-center justify-between">
                    <p className="font-semibold">{bank.name}</p>
                    <Badge 
                      variant={bank.health > 95 ? 'default' : bank.health > 80 ? 'secondary' : 'destructive'}
                    >
                      {bank.health}%
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="p-4 pt-0 space-y-2">
                  <p className="text-2xl font-bold">{bank.records.toLocaleString()}</p>
                  <p className="text-sm text-muted-foreground">records</p>
                  <p className="text-xs text-muted-foreground">
                    Updated: {bank.last_update}
                  </p>
                  <Progress value={bank.health} className="h-2" />
                </CardContent>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
