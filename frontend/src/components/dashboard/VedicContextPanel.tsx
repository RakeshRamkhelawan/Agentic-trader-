import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  Moon, 
  Sun, 
  Activity, 
  Flame, 
  Droplets, 
  Mountain, 
  Wind,
  AlertTriangle,
  CheckCircle2,
  BarChart3,
  Sparkles
} from 'lucide-react';

interface VedicState {
  rahu_kala: boolean;
  market_regime: 'expansion' | 'contraction' | 'neutral' | 'recovery';
  harmony_score: number;
  dominant_element: string;
  prana_levels: Record<string, number>;
  vedic_time: string;
  navagraha_dominant: string;
  consciousness_level: number;
  trading_gate_open: boolean;
}

interface VedicContextPanelProps {
  wsUrl: string;
  isRunning: boolean;
}

export function VedicContextPanel({ wsUrl, isRunning }: VedicContextPanelProps) {
  const [vedicState, setVedicState] = useState<VedicState>({
    rahu_kala: false,
    market_regime: 'neutral',
    harmony_score: 0.5,
    dominant_element: 'ether',
    prana_levels: {
      ether: 100,
      air: 100,
      fire: 100,
      water: 100,
      earth: 100,
    },
    vedic_time: 'Brahma Muhurta',
    navagraha_dominant: 'Jupiter',
    consciousness_level: 0.5,
    trading_gate_open: true,
  });

  useEffect(() => {
    if (!isRunning) return;

    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        
        if (message.channel === 'paper_trading.vedic') {
          switch (message.type) {
            case 'soul_update':
              setVedicState(prev => ({
                ...prev,
                rahu_kala: message.data.rahu_kala,
                market_regime: message.data.market_regime,
                vedic_time: message.data.vedic_time,
                navagraha_dominant: message.data.navagraha_dominant,
                consciousness_level: message.data.consciousness_level,
                trading_gate_open: message.data.trading_gate_open,
              }));
              break;
            case 'prana_update':
              setVedicState(prev => ({
                ...prev,
                prana_levels: {
                  ether: message.data.ether ?? prev.prana_levels.ether,
                  air: message.data.air ?? prev.prana_levels.air,
                  fire: message.data.fire ?? prev.prana_levels.fire,
                  water: message.data.water ?? prev.prana_levels.water,
                  earth: message.data.earth ?? prev.prana_levels.earth,
                },
              }));
              break;
            case 'harmony_update':
              setVedicState(prev => ({
                ...prev,
                harmony_score: message.data.harmony_score,
                dominant_element: message.data.dominant_element,
              }));
              break;
            case 'cosmic_block':
              // Cosmic block event - Rahu Kala or other blocking condition
              console.log('Cosmic block:', message.data.reason);
              break;
          }
        }
      } catch (err) {
        console.error('Failed to parse Vedic message:', err);
      }
    };

    return () => {
      ws.close();
    };
  }, [wsUrl, isRunning]);

  const getHarmonyColor = (score: number) => {
    if (score < 0.3) return 'text-red-500';
    if (score < 0.7) return 'text-yellow-500';
    return 'text-green-500';
  };

  const getHarmonyBgColor = (score: number) => {
    if (score < 0.3) return 'bg-red-500';
    if (score < 0.7) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const getRegimeBadge = (regime: string) => {
    switch (regime) {
      case 'expansion':
        return <Badge className="bg-green-500 gap-1"><TrendingUp className="h-3 w-3" /> Expansion</Badge>;
      case 'contraction':
        return <Badge className="bg-red-500 gap-1"><TrendingDown className="h-3 w-3" /> Contraction</Badge>;
      case 'recovery':
        return <Badge className="bg-blue-500 gap-1"><Activity className="h-3 w-3" /> Recovery</Badge>;
      default:
        return <Badge variant="secondary" className="gap-1"><Minus className="h-3 w-3" /> Neutral</Badge>;
    }
  };

  const getElementIcon = (element: string) => {
    switch (element) {
      case 'ether': return <Sparkles className="h-4 w-4" />;
      case 'air': return <Wind className="h-4 w-4" />;
      case 'fire': return <Flame className="h-4 w-4" />;
      case 'water': return <Droplets className="h-4 w-4" />;
      case 'earth': return <Mountain className="h-4 w-4" />;
      default: return <Sparkles className="h-4 w-4" />;
    }
  };

  const getElementColor = (element: string) => {
    switch (element) {
      case 'ether': return 'bg-purple-500';
      case 'air': return 'bg-sky-500';
      case 'fire': return 'bg-orange-500';
      case 'water': return 'bg-blue-500';
      case 'earth': return 'bg-emerald-500';
      default: return 'bg-gray-500';
    }
  };

  return (
    <div className="space-y-4">
      {/* Rahu Kala Warning */}
      {vedicState.rahu_kala && (
        <Card className="border-red-500 bg-red-50 dark:bg-red-950">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <AlertTriangle className="h-8 w-8 text-red-500" />
              <div>
                <h3 className="font-bold text-red-700 dark:text-red-300">Rahu Kala Active</h3>
                <p className="text-sm text-red-600 dark:text-red-400">
                  Trading is blocked. Cosmic gate closed until period ends.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Main Vedic Context Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Harmony Score */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              Harmony Score
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-end gap-2">
              <span className={`text-3xl font-bold ${getHarmonyColor(vedicState.harmony_score)}`}>
                {(vedicState.harmony_score * 100).toFixed(0)}%
              </span>
            </div>
            <div className="mt-2 h-2 w-full rounded-full bg-gray-200 dark:bg-gray-700">
              <div 
                className={`h-full rounded-full transition-all duration-500 ${getHarmonyBgColor(vedicState.harmony_score)}`}
                style={{ width: `${vedicState.harmony_score * 100}%` }}
              />
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {vedicState.harmony_score < 0.3 ? 'Low harmony - trading paused' : 
               vedicState.harmony_score < 0.7 ? 'Moderate harmony' : 'High harmony - optimal trading'}
            </p>
          </CardContent>
        </Card>

        {/* Market Regime */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Activity className="h-4 w-4" />
              Market Regime
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              {getRegimeBadge(vedicState.market_regime)}
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              Current market condition
            </p>
          </CardContent>
        </Card>

        {/* Vedic Time */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Sun className="h-4 w-4" />
              Vedic Time
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-lg font-semibold">{vedicState.vedic_time}</p>
            <p className="text-xs text-muted-foreground mt-1">
              Dominant: {vedicState.navagraha_dominant}
            </p>
          </CardContent>
        </Card>

        {/* Trading Gate */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4" />
              Trading Gate
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Badge 
              variant={vedicState.trading_gate_open ? 'default' : 'destructive'}
              className="gap-1"
            >
              {vedicState.trading_gate_open ? (
                <><CheckCircle2 className="h-3 w-3" /> Open</>
              ) : (
                <><Moon className="h-3 w-3" /> Closed</>
              )}
            </Badge>
            <p className="text-xs text-muted-foreground mt-2">
              {vedicState.trading_gate_open ? 'All systems operational' : 'Cosmic blocking active'}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Prana Levels */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5" />
            Elemental Prana Levels
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            {Object.entries(vedicState.prana_levels).map(([element, prana]) => (
              <div key={element} className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {getElementIcon(element)}
                    <span className="text-sm font-medium capitalize">{element}</span>
                  </div>
                  <span className={`text-sm font-bold ${prana < 20 ? 'text-red-500' : prana < 50 ? 'text-yellow-500' : 'text-green-500'}`}>
                    {prana.toFixed(0)}
                  </span>
                </div>
                <div className="h-2 w-full rounded-full bg-gray-200 dark:bg-gray-700">
                  <div 
                    className={`h-full rounded-full transition-all duration-500 ${getElementColor(element)}`}
                    style={{ width: `${prana}%`, opacity: prana < 20 ? 0.5 : 1 }}
                  />
                </div>
                {prana < 20 && (
                  <p className="text-xs text-red-500">Depleted</p>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// Helper icons
function TrendingUp({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
      <polyline points="17 6 23 6 23 12" />
    </svg>
  );
}

function TrendingDown({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <polyline points="23 18 13.5 8.5 8.5 13.5 1 6" />
      <polyline points="17 18 23 18 23 12" />
    </svg>
  );
}

function Minus({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <line x1="5" y1="12" x2="19" y2="12" />
    </svg>
  );
}
