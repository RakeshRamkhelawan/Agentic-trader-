import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Sparkles, Command } from 'lucide-react';
import { useAppStore } from '@/store/appStore';
import { chatApi } from '@/lib/api';
import { cn } from '@/lib/utils';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';

interface Message {
  id: string;
  type: 'user' | 'ai' | 'system';
  content: string;
  timestamp: Date;
  actions?: { label: string; action: string }[];
}

const initialMessages: Message[] = [
  {
    id: '1',
    type: 'system',
    content: 'Welcome to Agentic Trader Terminal. How can I help you today?',
    timestamp: new Date(),
  },
  {
    id: '2',
    type: 'ai',
    content: 'I can help you with:\n• Market analysis and insights\n• Portfolio recommendations\n• Trade execution\n• Risk assessment\n• Technical analysis',
    timestamp: new Date(),
    actions: [
      { label: 'Analyze BTC', action: 'analyze BTC' },
      { label: 'Portfolio Review', action: 'review portfolio' },
      { label: 'Market Overview', action: 'market overview' },
    ],
  },
];

const quickCommands = [
  { label: 'Buy BTC', icon: 'B', color: 'bg-trade-green' },
  { label: 'Sell ETH', icon: 'S', color: 'bg-trade-red' },
  { label: 'Portfolio', icon: 'P', color: 'bg-trade-blue' },
  { label: 'Markets', icon: 'M', color: 'bg-trade-purple' },
];

export function Terminal() {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  useAppStore(); // keep store subscribed for sidebar stats

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isTyping) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    const currentInput = input;
    setInput('');
    setIsTyping(true);

    try {
      const historyForApi = [...messages, userMessage]
        .slice(-12)
        .filter((m) => m.type !== 'system')
        .map((m) => ({ type: m.type as 'user' | 'ai', content: m.content }));

      const responseText = await chatApi.sendMessage(currentInput, historyForApi);

      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          type: 'ai',
          content: responseText,
          timestamp: new Date(),
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          type: 'system',
          content: 'Unable to reach the AI assistant. Please try again.',
          timestamp: new Date(),
        },
      ]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="h-[calc(100vh-64px)] flex flex-col p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <Command className="w-6 h-6 text-trade-blue" />
            AI Trading Terminal
          </h2>
          <p className="text-muted-foreground mt-1">Chat with your AI trading assistant</p>
        </div>
        <Badge 
          variant="outline" 
          className="bg-trade-purple/10 text-trade-purple border-trade-purple/20"
        >
          <Sparkles className="w-3 h-3 mr-1" />
          GPT-4 Powered
        </Badge>
      </div>

      {/* Chat Container */}
      <Card className="flex-1 bg-[#111111] border-[#262626] overflow-hidden flex flex-col">
        <CardContent className="flex-1 flex flex-col p-0">
          {/* Messages */}
          <ScrollArea className="flex-1 p-4" ref={scrollRef}>
            <div className="space-y-4">
              {messages.map((message, index) => (
                <div
                  key={message.id}
                  className={cn(
                    'flex gap-3 animate-fade-in opacity-0',
                    message.type === 'user' && 'flex-row-reverse'
                  )}
                  style={{ animationDelay: `${index * 50}ms`, animationFillMode: 'forwards' }}
                >
                  {/* Avatar */}
                  <div 
                    className={cn(
                      'w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0',
                      message.type === 'user' && 'bg-trade-blue',
                      message.type === 'ai' && 'bg-gradient-to-br from-trade-purple to-trade-blue',
                      message.type === 'system' && 'bg-[#1A1A1A]'
                    )}
                  >
                    {message.type === 'user' && <User className="w-4 h-4 text-white" />}
                    {message.type === 'ai' && <Bot className="w-4 h-4 text-white" />}
                    {message.type === 'system' && <Command className="w-4 h-4 text-muted-foreground" />}
                  </div>

                  {/* Content */}
                  <div className={cn(
                    'max-w-[80%]',
                    message.type === 'user' && 'text-right'
                  )}>
                    <div 
                      className={cn(
                        'inline-block px-4 py-2 rounded-2xl text-left',
                        message.type === 'user' && 'bg-trade-blue text-white',
                        message.type === 'ai' && 'bg-[#1A1A1A] text-white',
                        message.type === 'system' && 'bg-[#0A0A0A] text-muted-foreground border border-[#262626]'
                      )}
                    >
                      <p className="whitespace-pre-line">{message.content}</p>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </p>

                    {/* Action Buttons */}
                    {message.actions && (
                      <div className="flex flex-wrap gap-2 mt-2">
                        {message.actions.map((action) => (
                          <button
                            key={action.label}
                            onClick={() => setInput(action.action)}
                            className="px-3 py-1.5 text-sm bg-[#0A0A0A] text-trade-blue border border-trade-blue/30 rounded-lg hover:bg-trade-blue/10 transition-colors"
                          >
                            {action.label}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {/* Typing Indicator */}
              {isTyping && (
                <div className="flex gap-3">
                  <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-trade-purple to-trade-blue flex items-center justify-center">
                    <Bot className="w-4 h-4 text-white" />
                  </div>
                  <div className="bg-[#1A1A1A] px-4 py-3 rounded-2xl">
                    <div className="flex gap-1">
                      <span className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <span className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <span className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                  </div>
                </div>
              )}
            </div>
          </ScrollArea>

          {/* Quick Commands */}
          <div className="px-4 py-2 border-t border-[#262626]">
            <div className="flex gap-2 overflow-x-auto pb-2">
              {quickCommands.map((cmd) => (
                <button
                  key={cmd.label}
                  onClick={() => setInput(cmd.label)}
                  className="flex items-center gap-2 px-3 py-1.5 bg-[#0A0A0A] rounded-lg hover:bg-[#1A1A1A] transition-colors whitespace-nowrap"
                >
                  <span className={cn('w-5 h-5 rounded text-xs font-bold flex items-center justify-center text-white', cmd.color)}>
                    {cmd.icon}
                  </span>
                  <span className="text-sm text-muted-foreground">{cmd.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Input */}
          <div className="p-4 border-t border-[#262626]">
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Type a command or ask a question..."
                  className="pr-12 bg-[#0A0A0A] border-[#262626] text-white placeholder:text-muted-foreground focus:border-trade-blue"
                />
                <div className="absolute right-3 top-1/2 -translate-y-1/2">
                  <span className="text-xs text-muted-foreground">⌘K</span>
                </div>
              </div>
              <Button
                onClick={handleSend}
                disabled={!input.trim() || isTyping}
                className="bg-trade-blue hover:bg-trade-blue/90 text-white px-4"
              >
                <Send className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
