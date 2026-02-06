import Link from "next/link";
import { ArrowRight, TrendingUp, Shield, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col">
      {/* Hero Section */}
      <section className="flex flex-1 flex-col items-center justify-center px-6 py-20">
        <div className="max-w-3xl text-center">
          <h1 className="bg-gradient-to-r from-white to-gray-400 bg-clip-text text-5xl font-bold tracking-tight text-transparent sm:text-6xl">
            Trade Smarter with AI
          </h1>
          <p className="mt-6 text-lg text-muted-foreground">
            AgenticTrader combines advanced AI agents with real-time market data
            to help you make better trading decisions. Backtest strategies,
            simulate trades, and execute with confidence.
          </p>
          <div className="mt-10 flex items-center justify-center gap-4">
            <Link href="/terminal">
              <Button size="lg" className="gap-2">
                Open Terminal
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <Link href="/markets">
              <Button variant="outline" size="lg">
                View Markets
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="border-t border-border bg-card/50 px-6 py-20">
        <div className="mx-auto max-w-5xl">
          <h2 className="mb-12 text-center text-3xl font-bold">
            Built for Professional Trading
          </h2>
          <div className="grid gap-6 md:grid-cols-3">
            <Card className="border-border/50 bg-card">
              <CardContent className="flex flex-col items-center p-6 text-center">
                <div className="mb-4 rounded-full bg-brand-blue/10 p-3">
                  <TrendingUp className="h-6 w-6 text-brand-blue" />
                </div>
                <h3 className="mb-2 font-semibold">Real-Time Charts</h3>
                <p className="text-sm text-muted-foreground">
                  Professional TradingView charts with 100+ indicators and
                  drawing tools.
                </p>
              </CardContent>
            </Card>

            <Card className="border-border/50 bg-card">
              <CardContent className="flex flex-col items-center p-6 text-center">
                <div className="mb-4 rounded-full bg-brand-green/10 p-3">
                  <Shield className="h-6 w-6 text-brand-green" />
                </div>
                <h3 className="mb-2 font-semibold">Smart Order Routing</h3>
                <p className="text-sm text-muted-foreground">
                  VWAP-optimized execution across 100+ exchanges for best
                  prices.
                </p>
              </CardContent>
            </Card>

            <Card className="border-border/50 bg-card">
              <CardContent className="flex flex-col items-center p-6 text-center">
                <div className="mb-4 rounded-full bg-brand-purple/10 p-3">
                  <Zap className="h-6 w-6 text-brand-purple" />
                </div>
                <h3 className="mb-2 font-semibold">AI-Powered Analysis</h3>
                <p className="text-sm text-muted-foreground">
                  Get intelligent insights and automated trading signals from
                  our AI agents.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>
    </div>
  );
}
