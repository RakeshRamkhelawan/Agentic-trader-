import { useState } from 'react';
import { Send, Sparkles, TrendingUp, TrendingDown } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAppStore } from '@/store/appStore';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { agentsApi } from '@/lib/api';

interface Advice {
  id: string;
  timestamp: Date;
  question: string;
  response: string;
  type: 'market' | 'portfolio' | 'risk' | 'general';
}

export function AIAdvisor() {
  const [question, setQuestion] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [advice, setAdvice] = useState<Advice | null>(null);
  const { assets, topGainer, topLoser } = useAppStore();
  
  // Extra safety: only show topGainer if it's actually positive
  // This handles stale data in the store
  const validTopGainer = topGainer && topGainer.change24h > 0 ? topGainer : null;
  const validTopLoser = topLoser && topLoser.change24h < 0 ? topLoser : null;
  
  // Calculate best/worst performers for display when no valid gainers/losers
  const sortedAssets = [...assets].sort((a, b) => b.change24h - a.change24h);
  const bestPerformer = sortedAssets.length > 0 ? sortedAssets[0] : null;
  const worstPerformer = sortedAssets.length > 0 ? sortedAssets[sortedAssets.length - 1] : null;

  const askAdvisor = async (customQuestion?: string) => {
    const q = customQuestion || question;
    if (!q.trim()) return;

    setIsLoading(true);
    try {
      // Get advice from AI
      const response = await agentsApi.chat(q);
      
      setAdvice({
        id: Math.random().toString(36).substring(7),
        timestamp: new Date(),
        question: q,
        response: response.response,
        type: detectType(q),
      });
      
      if (!customQuestion) {
        setQuestion('');
      }
    } catch (error) {
      console.error('Failed to get advice:', error);
      setAdvice({
        id: Math.random().toString(36).substring(7),
        timestamp: new Date(),
        question: q,
        response: 'I apologize, but I am unable to provide advice at this moment. Please try again later.',
        type: 'general',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const detectType = (q: string): Advice['type'] => {
    const lower = q.toLowerCase();
    if (lower.includes('market') || lower.includes('price') || lower.includes('trend')) return 'market';
    if (lower.includes('portfolio') || lower.includes('hold') || lower.includes('position')) return 'portfolio';
    if (lower.includes('risk') || lower.includes('safe') || lower.includes('danger')) return 'risk';
    return 'general';
  };

  const quickQuestions = [
    { icon: TrendingUp, label: 'Top Picks', question: 'What are the top 3 assets to watch today based on market momentum?' },
    { icon: TrendingDown, label: 'Risk Alert', question: 'Which assets show the highest risk right now?' },
    { icon: Sparkles, label: 'Market Outlook', question: 'What is the general market sentiment for today?' },
  ];

  const typeColors: Record<Advice['type'], string> = {
    market: 'text-trade-blue bg-trade-blue/10 border-trade-blue/20',
    portfolio: 'text-trade-green bg-trade-green/10 border-trade-green/20',
    risk: 'text-trade-orange bg-trade-orange/10 border-trade-orange/20',
    general: 'text-trade-purple bg-trade-purple/10 border-trade-purple/20',
  };

  return (
    <Card className="bg-[#111111] border-[#262626] animate-fade-in opacity-0" style={{ animationFillMode: 'forwards', animationDelay: '400ms' }}>
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-trade-purple to-trade-blue flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <CardTitle className="text-lg font-semibold text-white">AI Advisor</CardTitle>
            <p className="text-xs text-muted-foreground">Ask for trading insights & advice</p>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Quick Questions */}
        <div className="grid grid-cols-3 gap-2">
          {quickQuestions.map((q) => (
            <button
              key={q.label}
              onClick={() => askAdvisor(q.question)}
              disabled={isLoading}
              className="flex flex-col items-center gap-1 p-2 rounded-lg bg-[#0A0A0A] hover:bg-[#1A1A1A] transition-colors disabled:opacity-50"
            >
              <q.icon className="w-4 h-4 text-trade-blue" />
              <span className="text-[10px] text-muted-foreground">{q.label}</span>
            </button>
          ))}
        </div>

        {/* Input */}
        <div className="flex gap-2">
          <Input
            placeholder="Ask about markets, assets, or strategy..."
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && askAdvisor()}
            className="bg-[#0A0A0A] border-[#262626] text-white text-sm placeholder:text-muted-foreground"
            disabled={isLoading}
          />
          <Button
            onClick={() => askAdvisor()}
            disabled={isLoading || !question.trim()}
            className="bg-trade-blue hover:bg-trade-blue/90 px-3"
          >
            {isLoading ? (
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </Button>
        </div>

        {/* Latest Advice */}
        {advice && (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className={cn('text-[10px] px-2 py-0.5 rounded border', typeColors[advice.type])}>
                {advice.type.charAt(0).toUpperCase() + advice.type.slice(1)}
              </span>
              <span className="text-[10px] text-muted-foreground">
                {advice.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>
            <div className="bg-[#0A0A0A] rounded-lg p-3 text-sm">
              <p className="text-muted-foreground mb-2">Q: {advice.question}</p>
              <p className="text-white whitespace-pre-line">{advice.response}</p>
            </div>
          </div>
        )}

        {/* Market Context */}
        {assets.length > 0 && (
          <div className="pt-2 border-t border-[#262626]">
            <p className="text-xs text-muted-foreground mb-2">Current Market Context</p>
            <div className="flex gap-2">
              {validTopGainer ? (
                <div className="flex-1 bg-trade-green/5 border border-trade-green/10 rounded-lg p-2">
                  <p className="text-[10px] text-trade-green">Top Gainer</p>
                  <p className="text-sm font-mono text-white">{validTopGainer.symbol}</p>
                  <p className="text-xs text-trade-green">+{validTopGainer.change24h.toFixed(2)}%</p>
                </div>
              ) : bestPerformer ? (
                <div className="flex-1 bg-trade-orange/5 border border-trade-orange/10 rounded-lg p-2">
                  <p className="text-[10px] text-trade-orange">Best Performer</p>
                  <p className="text-sm font-mono text-white">{bestPerformer.symbol}</p>
                  <p className="text-xs text-trade-orange">{bestPerformer.change24h.toFixed(2)}%</p>
                </div>
              ) : null}
              {validTopLoser ? (
                <div className="flex-1 bg-trade-red/5 border border-trade-red/10 rounded-lg p-2">
                  <p className="text-[10px] text-trade-red">Top Loser</p>
                  <p className="text-sm font-mono text-white">{validTopLoser.symbol}</p>
                  <p className="text-xs text-trade-red">{validTopLoser.change24h.toFixed(2)}%</p>
                </div>
              ) : worstPerformer ? (
                <div className="flex-1 bg-trade-red/5 border border-trade-red/10 rounded-lg p-2">
                  <p className="text-[10px] text-trade-red">Worst Performer</p>
                  <p className="text-sm font-mono text-white">{worstPerformer.symbol}</p>
                  <p className="text-xs text-trade-red">{worstPerformer.change24h.toFixed(2)}%</p>
                </div>
              ) : null}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
