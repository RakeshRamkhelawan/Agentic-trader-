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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Brain, TrendingUp, TrendingDown, Minus, CheckCircle2, XCircle, HelpCircle, Wifi, WifiOff, Info } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface AgentDecision {
  timestamp: string;
  agent: string;
  strategy: string;
  symbol: string;
  decision: 'buy' | 'sell' | 'hold' | string;
  confidence: number;
  reason: string;
  executed: boolean;
}

interface AgentDecisionsProps {
  wsUrl?: string;
  maxItems?: number;
}

const AGENT_COLORS: Record<string, string> = {
  'Momentum': 'bg-green-500',
  'MeanReversion': 'bg-blue-500',
  'Breakout': 'bg-orange-500',
  'Scalper': 'bg-purple-500',
  'AggressiveMomentum': 'bg-red-500',
};

// Demo decisions for when no real data
const DEMO_DECISIONS: AgentDecision[] = [
  { timestamp: new Date(Date.now() - 60000).toISOString(), agent: 'Breakout', strategy: 'breakout', symbol: 'BTC/EUR', decision: 'buy', confidence: 0.8, reason: 'breakout_high', executed: true },
  { timestamp: new Date(Date.now() - 120000).toISOString(), agent: 'AggressiveMomentum', strategy: 'momentum', symbol: 'ETH/EUR', decision: 'buy', confidence: 0.75, reason: 'strong_uptrend', executed: true },
  { timestamp: new Date(Date.now() - 180000).toISOString(), agent: 'MeanReversion', strategy: 'mean_reversion', symbol: 'SOL/EUR', decision: 'sell', confidence: 0.65, reason: 'above_avg_2.5%', executed: true },
  { timestamp: new Date(Date.now() - 240000).toISOString(), agent: 'Scalper', strategy: 'scalping', symbol: 'ADA/EUR', decision: 'buy', confidence: 0.6, reason: 'scalp_0.8%', executed: true },
  { timestamp: new Date(Date.now() - 300000).toISOString(), agent: 'Momentum', strategy: 'momentum', symbol: 'DOT/EUR', decision: 'buy', confidence: 0.7, reason: 'uptrend', executed: true },
];

export function AgentDecisions({ wsUrl, maxItems = 20 }: AgentDecisionsProps) {
  const [decisions, setDecisions] = useState<AgentDecision[]>(DEMO_DECISIONS);
  const [connected, setConnected] = useState(false);
  const [useDemo, setUseDemo] = useState(true);

  useEffect(() => {
    if (!wsUrl) return;

    // Fix double /ws/ in URL
    const cleanUrl = wsUrl.replace(/\/ws\/ws\//, '/ws/');
    console.log('AgentDecisions connecting to:', cleanUrl);

    const ws = new WebSocket(cleanUrl);
    
    ws.onopen = () => {
      setConnected(true);
      console.log('AgentDecisions WebSocket connected');
    };
    
    ws.onclose = () => setConnected(false);
    
    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        if (message.type === 'agent_decision') {
          setDecisions(prev => [message.data, ...prev].slice(0, maxItems));
          setUseDemo(false);
        }
      } catch (err) {
        console.error('Failed to parse agent decision:', err);
      }
    };

    ws.onerror = () => {
      setConnected(false);
      // Keep demo mode on error
      setUseDemo(true);
    };

    return () => ws.close();
  }, [wsUrl, maxItems]);

  const getDecisionIcon = (decision: string) => {
    switch (decision) {
      case 'buy': return <TrendingUp className="h-4 w-4 text-green-500" />;
      case 'sell': return <TrendingDown className="h-4 w-4 text-red-500" />;
      case 'hold': return <Minus className="h-4 w-4 text-gray-500" />;
      default: return <HelpCircle className="h-4 w-4 text-gray-500" />;
    }
  };

  const getDecisionVariant = (decision: string): 'default' | 'destructive' | 'secondary' | 'outline' => {
    switch (decision) {
      case 'buy': return 'default';
      case 'sell': return 'destructive';
      case 'hold': return 'secondary';
      default: return 'outline';
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Brain className="h-5 w-5" />
          Agent Decisions
          {useDemo ? (
            <Badge variant="secondary" className="ml-auto">DEMO</Badge>
          ) : (
            <Badge variant={connected ? 'default' : 'secondary'} className="ml-auto gap-1">
              {connected ? <Wifi className="h-3 w-3" /> : <WifiOff className="h-3 w-3" />}
              {connected ? 'Live' : 'Offline'}
            </Badge>
          )}
        </CardTitle>
        <CardDescription>
          {useDemo 
            ? 'Laatste beslissingen van de trading agents (DEMO DATA)' 
            : `Laatste ${decisions.length} beslissingen van de trading agents`}
        </CardDescription>
      </CardHeader>
      <CardContent>
        {useDemo && (
          <Alert className="mb-4 bg-blue-50 border-blue-200">
            <Info className="h-4 w-4 text-blue-600" />
            <AlertDescription className="text-blue-800">
              Showing demo decisions. Real decisions will appear here when WebSocket is connected.
            </AlertDescription>
          </Alert>
        )}
        
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Tijd</TableHead>
                <TableHead>Agent</TableHead>
                <TableHead>Symbool</TableHead>
                <TableHead>Beslissing</TableHead>
                <TableHead>Vertrouwen</TableHead>
                <TableHead>Uitgevoerd</TableHead>
                <TableHead>Reden</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {decisions.map((decision, idx) => (
                <TableRow key={idx}>
                  <TableCell className="text-xs">
                    {new Date(decision.timestamp).toLocaleTimeString()}
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Avatar className="h-6 w-6">
                        <AvatarFallback className={`text-xs text-white ${AGENT_COLORS[decision.agent] || 'bg-gray-500'}`}>
                          {decision.agent[0]}
                        </AvatarFallback>
                      </Avatar>
                      <span className="text-sm">{decision.agent}</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">{decision.symbol}</Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1">
                      {getDecisionIcon(decision.decision)}
                      <Badge variant={getDecisionVariant(decision.decision)}>
                        {decision.decision.toUpperCase()}
                      </Badge>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2 w-32">
                      <Progress 
                        value={decision.confidence * 100}
                        className="flex-1"
                      />
                      <span className="text-xs w-8">{(decision.confidence * 100).toFixed(0)}%</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    {decision.executed ? 
                      <CheckCircle2 className="h-5 w-5 text-green-500" /> : 
                      <XCircle className="h-5 w-5 text-gray-400" />
                    }
                  </TableCell>
                  <TableCell className="text-xs max-w-xs truncate" title={decision.reason}>
                    {decision.reason}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}
