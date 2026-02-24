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
import { API_URL } from '@/lib/config';

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
  isRunning?: boolean;
}

const AGENT_COLORS: Record<string, string> = {
  'Momentum': 'bg-green-500',
  'MeanReversion': 'bg-blue-500',
  'Breakout': 'bg-orange-500',
  'Scalper': 'bg-purple-500',
  'AggressiveMomentum': 'bg-red-500',
  'V18_Elemental': 'bg-indigo-500',
  'V18': 'bg-indigo-500',
};

export function AgentDecisions({ wsUrl, maxItems = 20, isRunning = true }: AgentDecisionsProps) {
  const [decisions, setDecisions] = useState<AgentDecision[]>([]);
  const [connected, setConnected] = useState(false);

  // Fetch decisions from API (parses V18 logs)
  useEffect(() => {
    if (!isRunning) return;
    
    const fetchDecisions = async () => {
      try {
        const res = await fetch(`${API_URL}/api/v1/paper-trading/status`);
        const data = await res.json();
        
        // Extract agent decisions from V18 logs
        if (data.logs && Array.isArray(data.logs)) {
          const parsedDecisions: AgentDecision[] = [];
          const seen = new Set<string>();
          
          // Process logs in reverse (newest first)
          [...data.logs].reverse().forEach((log: string) => {
            // Parse [CONSENSUS] logs - these are the agent decisions
            // Format: [CONSENSUS] SYMBOL/EUR: 0.27 (raw:0.27) | Regime:unknown | Threshold:0.35 | Dominant:EARTH | Vayu:1.0
            const consensusMatch = log.match(/\[CONSENSUS\]\s+(\S+)\/(EUR|USD)\s*:\s*([\d.]+).*Regime:(\w+).*Threshold:([\d.]+).*Dominant:(\w+)/);
            if (consensusMatch) {
              const symbol = consensusMatch[1] + '/' + consensusMatch[2];
              const consensus = parseFloat(consensusMatch[3]);
              const regime = consensusMatch[4];
              const threshold = parseFloat(consensusMatch[5]);
              const dominant = consensusMatch[6];
              
              // Skip duplicates (same symbol in last 10 seconds)
              const key = `${symbol}-${Math.floor(Date.now() / 10000)}`;
              if (seen.has(key)) return;
              seen.add(key);
              
              // Decision based on consensus vs threshold
              let decision: 'buy' | 'sell' | 'hold' = 'hold';
              let executed = false;
              
              if (consensus >= threshold) {
                decision = 'buy';
                executed = true;
              } else if (consensus >= threshold * 0.8) {
                decision = 'hold';  // Close to threshold
              } else {
                decision = 'hold';
              }
              
              parsedDecisions.push({
                timestamp: new Date().toISOString(),
                agent: `V18_${dominant}`,
                strategy: `pancha_tattva_${regime}`,
                symbol: symbol,
                decision: decision,
                confidence: consensus,
                reason: `Consensus ${consensus.toFixed(2)} vs threshold ${threshold.toFixed(2)} | Regime: ${regime} | Dominant: ${dominant}`,
                executed: executed,
              });
            }
            
            // Parse [ENTRY] logs for executed trades
            const entryMatch = log.match(/\[ENTRY\]\s+(\S+)\s+[\d.]+\s+@\s+EUR\s+[\d.]+.*Consensus:\s*([\d.]+)/);
            if (entryMatch && !seen.has(`entry-${entryMatch[1]}`)) {
              seen.add(`entry-${entryMatch[1]}`);
              parsedDecisions.unshift({
                timestamp: new Date().toISOString(),
                agent: 'V18_Elemental',
                strategy: 'vedastro_consensus',
                symbol: entryMatch[1],
                decision: 'buy',
                confidence: parseFloat(entryMatch[2]),
                reason: `Trade executed - Consensus ${entryMatch[2]}`,
                executed: true,
              });
            }
          });
          
          if (parsedDecisions.length > 0) {
            setDecisions(parsedDecisions.slice(0, maxItems));
            setConnected(true);
          }
        }
      } catch (err) {
        console.error('Failed to fetch decisions:', err);
      }
    };

    fetchDecisions();
    const interval = setInterval(fetchDecisions, 3000);  // Check every 3s
    return () => clearInterval(interval);
  }, [isRunning, maxItems]);

  // WebSocket for real-time updates
  useEffect(() => {
    if (!wsUrl || !isRunning) return;

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
          const newDecision: AgentDecision = {
            timestamp: message.data.timestamp || new Date().toISOString(),
            agent: message.data.agent || 'V18_Elemental',
            strategy: message.data.strategy || 'vedastro_consensus',
            symbol: message.data.symbol,
            decision: message.data.decision.toLowerCase(),
            confidence: message.data.confidence || 0.5,
            reason: message.data.reason || 'Consensus based',
            executed: message.data.executed !== false,
          };
          setDecisions(prev => [newDecision, ...prev].slice(0, maxItems));
        }
      } catch (err) {
        console.error('Failed to parse agent decision:', err);
      }
    };

    ws.onerror = () => {
      setConnected(false);
    };

    return () => ws.close();
  }, [wsUrl, maxItems, isRunning]);

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
          <Badge variant={connected ? 'default' : 'secondary'} className="ml-auto gap-1">
            {connected ? <Wifi className="h-3 w-3" /> : <WifiOff className="h-3 w-3" />}
            {connected ? 'Live' : 'Offline'}
          </Badge>
        </CardTitle>
        <CardDescription>
          Laatste beslissingen van de V18 Pancha-Tattva agents
        </CardDescription>
      </CardHeader>
      <CardContent>
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
              {decisions.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                    {isRunning 
                      ? connected 
                        ? 'Waiting for agent decisions... (V18 engine running)' 
                        : 'Connecting to WebSocket...'
                      : 'Start trading session to see agent decisions'}
                  </TableCell>
                </TableRow>
              ) : (
                decisions.map((decision, idx) => (
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
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}
