/**
 * CognitiveInsightsPanel - AI Decision Transparency Component
 *
 * Premium glassmorphism panel that visualizes the V18 Engine's
 * cognitive decision-making process: RAG evidence, VedAstro signals,
 * regime detection, and historical match quality.
 *
 * Data sources:
 * - REST: GET /trading/paper-trading/cognitive-insights (initial load)
 * - WebSocket: { type: 'cognitive_insight' } (real-time push)
 */

import { useEffect, useState, useCallback } from 'react';
import {
  Brain,
  ChevronDown,
  ChevronRight,
  Sparkles,
  Activity,
  Target,
  TrendingUp,
  TrendingDown,
  Zap,
  Globe,
  Clock,
  RefreshCw,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Button } from '@/components/ui/button';
import {
  paperTradingApi,
  type CognitiveInsight,
  type RagEvidence,
} from '@/lib/api/paper-trading';

// ============================================================================
// REGIME BADGE CONFIG
// ============================================================================

const REGIME_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  expansion: { label: 'Expansion', color: 'text-green-400', bg: 'bg-green-500/20 border-green-500/30' },
  contraction: { label: 'Contractie', color: 'text-red-400', bg: 'bg-red-500/20 border-red-500/30' },
  recovery: { label: 'Herstel', color: 'text-blue-400', bg: 'bg-blue-500/20 border-blue-500/30' },
  neutral: { label: 'Neutraal', color: 'text-gray-400', bg: 'bg-gray-500/20 border-gray-500/30' },
  unknown: { label: 'Onbekend', color: 'text-gray-500', bg: 'bg-gray-500/10 border-gray-500/20' },
};

// ============================================================================
// MATCH QUALITY HELPER
// ============================================================================

function getMatchQuality(distance: number): { pct: number; label: string; color: string } {
  // ChromaDB distance: 0 = perfect, ~2.0 = no match
  const pct = Math.max(0, Math.round((1 - distance / 2) * 100));
  if (pct >= 70) return { pct, label: 'Sterk', color: 'text-green-400' };
  if (pct >= 45) return { pct, label: 'Matig', color: 'text-yellow-400' };
  return { pct, label: 'Zwak', color: 'text-red-400' };
}

// ============================================================================
// RAG EVIDENCE CARD
// ============================================================================

function RagEvidenceCard({ evidence, index }: { evidence: RagEvidence; index: number }) {
  const match = getMatchQuality(evidence.distance);
  const isPositive = evidence.return_pct > 0;

  return (
    <div
      className={cn(
        'p-3 rounded-lg bg-[#0A0A0A] border border-[#1A1A1A]',
        'hover:border-[#333333] transition-all duration-200',
        'animate-fade-in',
      )}
      style={{ animationDelay: `${index * 80}ms` }}
    >
      <div className='flex items-center justify-between mb-2'>
        <div className='flex items-center gap-2'>
          <span className='text-xs text-[#555555] font-mono'>#{index + 1}</span>
          {evidence.period !== 'unknown' && (
            <Badge variant='outline' className='text-[10px] border-[#333333] text-[#888888]'>
              {evidence.period}
            </Badge>
          )}
          {evidence.symbol !== 'unknown' && (
            <span className='text-[10px] text-[#666666]'>{evidence.symbol}</span>
          )}
        </div>
        <span className={cn('text-xs font-mono font-bold', match.color)}>
          {match.pct}% match
        </span>
      </div>

      {/* Match Quality Bar */}
      <div className='mb-2'>
        <Progress
          value={match.pct}
          className='h-1.5 bg-[#1A1A1A]'
        />
      </div>

      <div className='flex items-center justify-between'>
        <div className='flex items-center gap-2'>
          {evidence.outcome !== 'unknown' && (
            <Badge
              className={cn(
                'text-[10px]',
                evidence.outcome === 'success'
                  ? 'bg-green-500/20 text-green-400 border-green-500/30'
                  : evidence.outcome === 'failure'
                    ? 'bg-red-500/20 text-red-400 border-red-500/30'
                    : 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30'
              )}
              variant='outline'
            >
              {evidence.outcome === 'success' ? 'Succes' : evidence.outcome === 'failure' ? 'Verlies' : 'Deels'}
            </Badge>
          )}
          {evidence.mahadasha !== 'Unknown' && (
            <span className='text-[10px] text-[#555555]'>
              {evidence.mahadasha}-{evidence.antardasha}
            </span>
          )}
        </div>
        <span
          className={cn(
            'text-sm font-mono font-bold',
            isPositive ? 'text-green-400' : 'text-red-400'
          )}
        >
          {isPositive ? '+' : ''}{evidence.return_pct.toFixed(1)}%
        </span>
      </div>
    </div>
  );
}

// ============================================================================
// SINGLE DECISION ITEM (COLLAPSIBLE)
// ============================================================================

function DecisionItem({ insight }: { insight: CognitiveInsight }) {
  const [isOpen, setIsOpen] = useState(false);
  const regime = REGIME_CONFIG[insight.regime] || REGIME_CONFIG.unknown;
  const isBuy = insight.final_decision === 'BUY';
  const time = new Date(insight.timestamp).toLocaleTimeString('nl-NL', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });

  return (
    <div
      className={cn(
        'rounded-xl border transition-all duration-300',
        'bg-[#111111] hover:bg-[#141414]',
        isBuy
          ? 'border-green-500/30 hover:border-green-500/50'
          : 'border-[#1A1A1A] hover:border-[#333333]',
        isBuy && 'glow-green',
      )}
    >
      {/* Header - always visible */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className='w-full flex items-center justify-between p-3 text-left'
        id={`cognitive-decision-${insight.symbol}-${insight.timestamp}`}
      >
        <div className='flex items-center gap-3'>
          {/* Decision Icon */}
          <div
            className={cn(
              'w-9 h-9 rounded-lg flex items-center justify-center',
              isBuy ? 'bg-green-500/20' : 'bg-[#1A1A1A]'
            )}
          >
            {isBuy ? (
              <TrendingUp className='w-4 h-4 text-green-400' />
            ) : (
              <Target className='w-4 h-4 text-[#666666]' />
            )}
          </div>

          {/* Symbol + Time */}
          <div>
            <div className='flex items-center gap-2'>
              <span className='font-semibold text-white text-sm'>
                {insight.symbol.replace('/EUR', '')}
              </span>
              <Badge
                className={cn('text-[10px] border', regime.bg, regime.color)}
                variant='outline'
              >
                {regime.label}
              </Badge>
            </div>
            <div className='flex items-center gap-2 mt-0.5'>
              <Clock className='w-3 h-3 text-[#555555]' />
              <span className='text-[11px] text-[#555555]'>{time}</span>
              {insight.rag_evidence.length > 0 && (
                <span className='text-[10px] text-[#444444]'>
                  {insight.rag_evidence.length} matches
                </span>
              )}
            </div>
          </div>
        </div>

        <div className='flex items-center gap-2'>
          {/* Decision Badge */}
          <Badge
            className={cn(
              'font-mono text-xs',
              isBuy
                ? 'bg-green-500 text-black'
                : 'bg-[#1A1A1A] text-[#888888] border-[#333333]'
            )}
          >
            {insight.final_decision}
          </Badge>
          {isOpen ? (
            <ChevronDown className='w-4 h-4 text-[#555555]' />
          ) : (
            <ChevronRight className='w-4 h-4 text-[#555555]' />
          )}
        </div>
      </button>

      {/* Expanded Content */}
      {isOpen && (
        <div className='px-3 pb-3 space-y-3 animate-fade-in'>
          <Separator className='bg-[#1A1A1A]' />

          {/* Scores Grid */}
          <div className='grid grid-cols-3 gap-2'>
            <div className='p-2 rounded-lg bg-[#0A0A0A] text-center'>
              <p className='text-[10px] text-[#555555] uppercase tracking-wider'>VedAstro</p>
              <p className={cn('text-sm font-mono font-bold',
                insight.vedastro_vote > 0 ? 'text-green-400' :
                insight.vedastro_vote < 0 ? 'text-red-400' : 'text-[#666666]'
              )}>
                {insight.vedastro_vote > 0 ? '+' : ''}{insight.vedastro_vote.toFixed(2)}
              </p>
            </div>
            <div className='p-2 rounded-lg bg-[#0A0A0A] text-center'>
              <p className='text-[10px] text-[#555555] uppercase tracking-wider'>RAG Adj.</p>
              <p className={cn('text-sm font-mono font-bold',
                insight.rag_adjustment > 0 ? 'text-blue-400' :
                insight.rag_adjustment < 0 ? 'text-red-400' : 'text-[#666666]'
              )}>
                {insight.rag_adjustment > 0 ? '+' : ''}{insight.rag_adjustment.toFixed(3)}
              </p>
            </div>
            <div className='p-2 rounded-lg bg-[#0A0A0A] text-center'>
              <p className='text-[10px] text-[#555555] uppercase tracking-wider'>Signaal</p>
              <p className='text-sm font-mono font-bold text-[#888888] uppercase'>
                {insight.engine_signal}
              </p>
            </div>
          </div>

          {/* RAG Evidence */}
          {insight.rag_evidence.length > 0 && (
            <div>
              <div className='flex items-center gap-2 mb-2'>
                <Sparkles className='w-3 h-3 text-purple-400' />
                <p className='text-[11px] font-medium text-purple-400 uppercase tracking-wider'>
                  Historische Matches
                </p>
              </div>
              <div className='space-y-2'>
                {insight.rag_evidence.map((evidence, i) => (
                  <RagEvidenceCard key={i} evidence={evidence} index={i} />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ============================================================================
// MAIN PANEL COMPONENT
// ============================================================================

export function CognitiveInsightsPanel() {
  const [insights, setInsights] = useState<CognitiveInsight[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<string | null>(null);

  const fetchInsights = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await paperTradingApi.getCognitiveInsights(20);
      if (response.insights && response.insights.length > 0) {
        setInsights(response.insights);
        setLastUpdate(new Date().toLocaleTimeString('nl-NL'));
      }
    } catch {
      // Silent fail - engine might not be running
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Initial load
  useEffect(() => {
    fetchInsights();
  }, [fetchInsights]);

  // Auto-refresh every 30s as fallback (WebSocket is primary)
  useEffect(() => {
    const id = setInterval(fetchInsights, 30000);
    return () => clearInterval(id);
  }, [fetchInsights]);

  const buyCount = insights.filter((i) => i.final_decision === 'BUY').length;
  const skipCount = insights.filter((i) => i.final_decision === 'SKIP').length;

  return (
    <Card className='bg-[#111111] border-[#262626] overflow-hidden'>
      {/* Gradient top accent */}
      <div className='h-[2px] bg-gradient-to-r from-purple-500 via-blue-500 to-cyan-500' />

      <CardHeader className='pb-2'>
        <div className='flex items-center justify-between'>
          <CardTitle className='flex items-center gap-2 text-white text-sm'>
            <Brain className='h-4 w-4 text-purple-400' />
            AI Drijfveren
            {insights.length > 0 && (
              <Badge variant='secondary' className='text-[10px] bg-[#1A1A1A] text-[#888888]'>
                {insights.length}
              </Badge>
            )}
          </CardTitle>
          <Button
            variant='ghost'
            size='sm'
            onClick={fetchInsights}
            disabled={isLoading}
            className='h-7 w-7 p-0 text-[#666666] hover:text-white'
          >
            <RefreshCw className={cn('h-3 w-3', isLoading && 'animate-spin')} />
          </Button>
        </div>

        {/* Stats bar */}
        {insights.length > 0 && (
          <div className='flex items-center gap-3 mt-1'>
            <div className='flex items-center gap-1'>
              <Zap className='w-3 h-3 text-green-500' />
              <span className='text-[10px] text-green-400 font-mono'>{buyCount} BUY</span>
            </div>
            <div className='flex items-center gap-1'>
              <Activity className='w-3 h-3 text-[#666666]' />
              <span className='text-[10px] text-[#666666] font-mono'>{skipCount} SKIP</span>
            </div>
            {lastUpdate && (
              <span className='text-[10px] text-[#444444] ml-auto'>
                {lastUpdate}
              </span>
            )}
          </div>
        )}
      </CardHeader>

      <CardContent className='pt-0'>
        <ScrollArea className='h-[400px] pr-2'>
          {insights.length > 0 ? (
            <div className='space-y-2'>
              {insights.map((insight, idx) => (
                <DecisionItem key={`${insight.symbol}-${insight.timestamp}-${idx}`} insight={insight} />
              ))}
            </div>
          ) : (
            <div className='flex flex-col items-center justify-center py-12 text-center'>
              <div className='w-12 h-12 rounded-full bg-[#1A1A1A] flex items-center justify-center mb-3'>
                <Brain className='w-6 h-6 text-[#333333]' />
              </div>
              <p className='text-sm text-[#555555] font-medium'>Wacht op AI beslissingen...</p>
              <p className='text-[11px] text-[#444444] mt-1'>
                Start een paper trading sessie om inzichten te ontvangen
              </p>
            </div>
          )}
        </ScrollArea>
      </CardContent>
    </Card>
  );
}

export default CognitiveInsightsPanel;
