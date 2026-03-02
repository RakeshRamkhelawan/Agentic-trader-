/**
 * PaperAIAdvisor Component
 * 
 * AI-powered trading advisor for paper trading.
 * Provides insights and recommendations based on portfolio and market data.
 */

import { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';
import { Brain, Send, User, Bot, TrendingUp, TrendingDown, AlertCircle } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { chatApi, agentsApi } from '@/lib/api';
import usePaperTradingStore from '@/store/paper-trading';
import { cn } from '@/lib/utils';

interface Message {
  id: string;
  type: 'user' | 'ai';
  content: string;
  timestamp: Date;
  metadata?: {
    sentiment?: 'positive' | 'negative' | 'neutral';
    action?: 'buy' | 'sell' | 'hold';
    confidence?: number;
  };
}

export function PaperAIAdvisor() {
  const { isRunning, portfolio, trades } = usePaperTradingStore();
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      type: 'ai',
      content: 'Hello! I\'m your AI trading advisor. Ask me anything about your paper trading portfolio, market conditions, or trading strategies.',
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || !isRunning) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      // Build context from portfolio
      const portfolioContext = portfolio
        ? `Current portfolio: €${portfolio.total_value.toFixed(2)} total value, €${portfolio.cash.toFixed(2)} cash, P&L: €${portfolio.pnl.toFixed(2)} (${portfolio.pnl_percent.toFixed(2)}%). Positions: ${Object.keys(portfolio.positions).join(', ') || 'none'}.`
        : 'No active portfolio.';

      const tradeContext = trades.length > 0
        ? `Recent trades: ${trades.slice(0, 3).map(t => `${t.side.toUpperCase()} ${t.symbol} @ €${t.price}`).join(', ')}.`
        : 'No recent trades.';

      const enhancedMessage = `[Paper Trading Context] ${portfolioContext} ${tradeContext}\n\nUser question: ${userMessage.content}`;

      const response = await chatApi.sendMessage(enhancedMessage, []);

      // Parse sentiment/action from response
      let sentiment: 'positive' | 'negative' | 'neutral' = 'neutral';
      let action: 'buy' | 'sell' | 'hold' | undefined;
      let confidence: number | undefined;

      const lowerResponse = response.toLowerCase();
      if (lowerResponse.includes('buy') || lowerResponse.includes('bullish')) {
        sentiment = 'positive';
        action = 'buy';
      } else if (lowerResponse.includes('sell') || lowerResponse.includes('bearish')) {
        sentiment = 'negative';
        action = 'sell';
      } else if (lowerResponse.includes('hold') || lowerResponse.includes('neutral')) {
        action = 'hold';
      }

      // Extract confidence if mentioned
      const confidenceMatch = response.match(/confidence[:\s]+(\d+)%/i);
      if (confidenceMatch) {
        confidence = parseInt(confidenceMatch[1]) / 100;
      }

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: response,
        timestamp: new Date(),
        metadata: { sentiment, action, confidence },
      };

      setMessages((prev) => [...prev, aiMessage]);
    } catch (err) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleQuickQuestion = (question: string) => {
    setInput(question);
  };

  if (!isRunning) {
    return (
      <Card className="border-dashed">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5" />
            AI Advisor
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col items-center justify-center py-8">
          <AlertCircle className="h-12 w-12 text-muted-foreground mb-4" />
          <p className="text-lg font-medium">AI Advisor Ready</p>
          <p className="text-sm text-muted-foreground text-center">
            Start a paper trading session to chat with the AI advisor
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="flex flex-col h-[500px]">
      <CardHeader className="flex-none">
        <CardTitle className="flex items-center gap-2">
          <Brain className="h-5 w-5" />
          AI Advisor
          <Badge variant="secondary" className="ml-auto">Paper Trading</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col min-h-0">
        {/* Messages */}
        <ScrollArea className="flex-1 pr-4" ref={scrollRef}>
          <div className="space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={cn(
                  'flex gap-3',
                  message.type === 'user' ? 'justify-end' : 'justify-start'
                )}
              >
                {message.type === 'ai' && (
                  <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center flex-shrink-0">
                    <Bot className="h-4 w-4 text-primary-foreground" />
                  </div>
                )}
                <div
                  className={cn(
                    'max-w-[80%] rounded-lg p-3',
                    message.type === 'user'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted'
                  )}
                >
                  <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                  {message.metadata?.action && (
                    <div className="mt-2 flex items-center gap-2">
                      {message.metadata.action === 'buy' && (
                        <Badge variant="default" className="bg-green-500 gap-1">
                          <TrendingUp className="h-3 w-3" />
                          BUY
                        </Badge>
                      )}
                      {message.metadata.action === 'sell' && (
                        <Badge variant="destructive" className="gap-1">
                          <TrendingDown className="h-3 w-3" />
                          SELL
                        </Badge>
                      )}
                      {message.metadata.action === 'hold' && (
                        <Badge variant="secondary">HOLD</Badge>
                      )}
                      {message.metadata.confidence && (
                        <span className="text-xs text-muted-foreground">
                          {(message.metadata.confidence * 100).toFixed(0)}% confidence
                        </span>
                      )}
                    </div>
                  )}
                  <span className="text-xs opacity-50 mt-1 block">
                    {message.timestamp.toLocaleTimeString()}
                  </span>
                </div>
                {message.type === 'user' && (
                  <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center flex-shrink-0">
                    <User className="h-4 w-4" />
                  </div>
                )}
              </div>
            ))}
            {isLoading && (
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center">
                  <Bot className="h-4 w-4 text-primary-foreground" />
                </div>
                <div className="bg-muted rounded-lg p-3">
                  <Skeleton className="h-4 w-32" />
                </div>
              </div>
            )}
          </div>
        </ScrollArea>

        {/* Quick Questions */}
        <div className="flex flex-wrap gap-2 my-3">
          {['Should I buy BTC?', 'Portfolio analysis', 'Market outlook'].map((q) => (
            <Button
              key={q}
              variant="outline"
              size="sm"
              onClick={() => handleQuickQuestion(q)}
              disabled={isLoading}
            >
              {q}
            </Button>
          ))}
        </div>

        {/* Input */}
        <div className="flex gap-2 flex-none">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about your portfolio..."
            disabled={isLoading}
            className="flex-1"
          />
          <Button
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            size="icon"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

export default PaperAIAdvisor;
