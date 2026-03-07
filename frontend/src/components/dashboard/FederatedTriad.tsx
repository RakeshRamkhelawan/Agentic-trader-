/**
 * Federated Triad Component - REAL DATA ONLY
 * 
 * Displays the Federated Triad system state including:
 * - Council views and their perspectives
 * - Coherence metrics
 * - Chitta knowledge nodes
 * - Buddhi decisions
 * 
 * NO MOCK DATA - All data comes from useFederatedStore
 * which fetches from /api/v1/federated/state
 */

import { useEffect } from 'react';
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
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';

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
  RefreshCw,
} from 'lucide-react';
import { useFederatedStore } from '@/store/federatedStore';

const COUNCIL_COLORS: Record<string, string> = {
  'guna': 'bg-amber-500',
  'elemental': 'bg-emerald-500',
  'graha': 'bg-indigo-500',
  'mind': 'bg-cyan-500',
  'body': 'bg-rose-500',
  'shiva': 'bg-violet-600',
};

const META_AGENT_ICONS: Record<string, React.ReactNode> = {
  'coordinator': <GitBranch className="h-5 w-5" />,
  'evaluator': <Brain className="h-5 w-5" />,
  'governance': <Scale className="h-5 w-5" />,
};

function getStatusIcon(status: string) {
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
}

function getDecisionIcon(decision: string) {
  switch (decision?.toUpperCase()) {
    case 'BUY': return <TrendingUp className="h-4 w-4 text-green-500" />;
    case 'SELL': return <TrendingDown className="h-4 w-4 text-red-500" />;
    default: return <Minus className="h-4 w-4 text-gray-500" />;
  }
}

/**
 * Skeleton loader for loading state
 */
function FederatedTriadSkeleton() {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <Skeleton className="h-8 w-48" />
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <Skeleton key={i} className="h-20" />
            ))}
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-32" />
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <Skeleton key={i} className="h-32" />
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

/**
 * Error state component
 */
function FederatedTriadError({ error, onRetry }: { error: string; onRetry: () => void }) {
  return (
    <Alert className="bg-red-50 border-red-200">
      <AlertTriangle className="h-4 w-4 text-red-600" />
      <AlertDescription className="text-red-800">
        <p className="font-semibold">Failed to load Federated Triad data</p>
        <p className="text-sm">{error}</p>
        <Button 
          variant="outline" 
          size="sm" 
          onClick={onRetry}
          className="mt-2"
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          Retry
        </Button>
      </AlertDescription>
    </Alert>
  );
}

/**
 * Empty state when no data available
 */
function FederatedTriadEmpty() {
  return (
    <Alert className="bg-blue-50 border-blue-200">
      <Info className="h-4 w-4 text-blue-600" />
      <AlertDescription className="text-blue-800">
        <p className="font-semibold">No Federated Triad Data</p>
        <p className="text-sm">The federated triad system is not active or has no data available.</p>
      </AlertDescription>
    </Alert>
  );
}

/**
 * Main Federated Triad Component
 * 
 * Uses real data from useFederatedStore
 * NO MOCK DATA
 */
export function FederatedTriad() {
  const {
    coherence,
    councils,
    chittaNodes,
    latestDecision,
    deliberationSteps,
    isLoading,
    error,
    lastUpdated,
    fetchState,
  } = useFederatedStore();

  // Fetch data on mount and every 5 seconds
  useEffect(() => {
    fetchState();
    const interval = setInterval(fetchState, 5000);
    return () => clearInterval(interval);
  }, [fetchState]);

  // Loading state
  if (isLoading && !coherence) {
    return <FederatedTriadSkeleton />;
  }

  // Error state
  if (error) {
    return <FederatedTriadError error={error} onRetry={fetchState} />;
  }

  // Empty state
  if (!coherence || councils.length === 0) {
    return <FederatedTriadEmpty />;
  }

  const isConnected = !!lastUpdated && (new Date().getTime() - lastUpdated.getTime()) < 10000;

  return (
    <div className="space-y-6">
      {/* Header Stats */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Network className="h-5 w-5" />
              Federated Triad
              <Badge 
                variant={isConnected ? 'default' : 'secondary'} 
                className="ml-2 gap-1"
              >
                {isConnected ? <Wifi className="h-3 w-3" /> : <WifiOff className="h-3 w-3" />}
                {isConnected ? 'Live' : 'Stale'}
              </Badge>
            </CardTitle>
            {lastUpdated && (
              <p className="text-xs text-muted-foreground">
                Last update: {lastUpdated.toLocaleTimeString()}
              </p>
            )}
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
                <Progress value={coherence.total} className="flex-1" />
                <span className="font-bold">{coherence.total}%</span>
              </div>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Harmony</p>
              <div className="flex items-center gap-2">
                <Progress value={coherence.harmony} className="flex-1" />
                <span className="font-bold">{coherence.harmony}%</span>
              </div>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Performance</p>
              <div className="flex items-center gap-2">
                <Progress value={coherence.performance} className="flex-1" />
                <span className="font-bold">{coherence.performance}%</span>
              </div>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Councils</p>
              <p className="text-2xl font-bold">{councils.length}</p>
            </div>
          </div>
          
          {/* Additional coherence metrics */}
          <div className="grid grid-cols-3 gap-4 mt-4 pt-4 border-t">
            <div>
              <p className="text-xs text-muted-foreground">Chitta Health</p>
              <p className="text-lg font-semibold">{coherence.chitta_health}%</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Deliberation Quality</p>
              <p className="text-lg font-semibold">{coherence.deliberation_quality}%</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Buddhi Clarity</p>
              <p className="text-lg font-semibold">{coherence.buddhi_clarity}%</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Councils */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5" />
            Councils
          </CardTitle>
          <CardDescription>
            Active councils with their perspectives and confidence
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {councils.map((council) => (
              <Card 
                key={council.name} 
                className={`border-l-4 ${
                  council.status === 'active' ? 'border-l-green-500' : 
                  council.status === 'idle' ? 'border-l-blue-500' : 
                  council.status === 'error' ? 'border-l-red-500' : 'border-l-gray-500'
                }`}
              >
                <CardHeader className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Avatar className="h-8 w-8">
                        <AvatarFallback className={`text-xs text-white ${COUNCIL_COLORS[council.type] || 'bg-gray-500'}`}>
                          {council.name[0]}
                        </AvatarFallback>
                      </Avatar>
                      <div>
                        <p className="font-semibold text-sm">{council.name}</p>
                        <p className="text-xs text-muted-foreground capitalize">{council.type}</p>
                      </div>
                    </div>
                    {getStatusIcon(council.status || 'idle')}
                  </div>
                </CardHeader>
                <CardContent className="p-4 pt-0 space-y-2">
                  <div className="flex items-center gap-2 text-sm">
                    {getDecisionIcon(council.perspective)}
                    <span className="capitalize">{council.perspective}</span>
                  </div>
                  
                  {/* Insights */}
                  {council.insights.length > 0 && (
                    <div className="space-y-1">
                      {council.insights.slice(0, 2).map((insight, idx) => (
                        <p key={idx} className="text-xs text-muted-foreground">
                          • {insight}
                        </p>
                      ))}
                    </div>
                  )}
                  
                  {/* Confidence */}
                  <div className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span>Confidence</span>
                      <span>{(council.confidence * 100).toFixed(0)}%</span>
                    </div>
                    <Progress value={council.confidence * 100} className="h-2" />
                  </div>
                  
                  {/* Contradictions */}
                  {council.contradictions && council.contradictions.length > 0 && (
                    <Badge variant="destructive" className="text-xs">
                      {council.contradictions.length} contradictions
                    </Badge>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Latest Decision */}
      {latestDecision && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Scale className="h-5 w-5" />
              Latest Buddhi Decision
            </CardTitle>
            <CardDescription>
              Consensus decision from council deliberation
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                {getDecisionIcon(latestDecision.action)}
                <div>
                  <p className="text-2xl font-bold uppercase">{latestDecision.action}</p>
                  <p className="text-sm text-muted-foreground">
                    Confidence: {(latestDecision.confidence * 100).toFixed(0)}%
                  </p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-xs text-muted-foreground">
                  {new Date(latestDecision.timestamp).toLocaleString()}
                </p>
                {latestDecision.contradictions > 0 && (
                  <Badge variant="destructive" className="mt-1">
                    {latestDecision.contradictions} contradictions
                  </Badge>
                )}
              </div>
            </div>
            
            {latestDecision.rationale && (
              <div className="mt-4 p-3 bg-muted rounded-md">
                <p className="text-sm">{latestDecision.rationale}</p>
              </div>
            )}
            
            {/* Supporting/Opposing */}
            <div className="grid grid-cols-2 gap-4 mt-4">
              <div>
                <p className="text-xs text-muted-foreground mb-1">Supporting</p>
                <div className="flex flex-wrap gap-1">
                  {latestDecision.supporting.slice(0, 3).map((name, idx) => (
                    <Badge key={idx} variant="default" className="text-xs">
                      {name}
                    </Badge>
                  ))}
                </div>
              </div>
              <div>
                <p className="text-xs text-muted-foreground mb-1">Opposing</p>
                <div className="flex flex-wrap gap-1">
                  {latestDecision.opposing.slice(0, 3).map((name, idx) => (
                    <Badge key={idx} variant="secondary" className="text-xs">
                      {name}
                    </Badge>
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Chitta Nodes */}
      {chittaNodes.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Database className="h-5 w-5" />
              Chitta Knowledge Nodes
            </CardTitle>
            <CardDescription>
              Shared knowledge from deliberation ({chittaNodes.length} nodes)
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {chittaNodes.slice(0, 10).map((node) => (
                <div 
                  key={node.id} 
                  className="flex items-center justify-between p-2 bg-muted rounded-md"
                >
                  <div className="flex items-center gap-2">
                    {node.verified ? (
                      <CheckCircle2 className="h-4 w-4 text-green-500" />
                    ) : (
                      <AlertTriangle className="h-4 w-4 text-yellow-500" />
                    )}
                    <span className="text-sm">{node.content}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="text-xs">
                      {node.council}
                    </Badge>
                    <span className="text-xs text-muted-foreground">
                      {new Date(node.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                </div>
              ))}
              {chittaNodes.length > 10 && (
                <p className="text-center text-xs text-muted-foreground">
                  +{chittaNodes.length - 10} more nodes
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Deliberation Steps */}
      {deliberationSteps.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              Deliberation Steps
            </CardTitle>
            <CardDescription>
              Council collaboration history
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {deliberationSteps.slice(0, 5).map((step, idx) => (
                <div 
                  key={idx}
                  className="flex items-center justify-between p-2 bg-muted rounded-md"
                >
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono text-muted-foreground">
                      #{step.iteration}
                    </span>
                    <span className="text-sm font-medium">{step.council}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm">{step.perspective}</span>
                    <Badge variant="outline" className="text-xs">
                      {(step.confidence * 100).toFixed(0)}%
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default FederatedTriad;
