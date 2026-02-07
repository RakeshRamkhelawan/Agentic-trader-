"use client"

import { ProtectedRoute } from "@/components/auth/protected-route"
import { TradingView } from "@/components/dashboard/TradingView"
import { TradingConsole } from "@/components/dashboard/TradingConsole"
import { OrderManager } from "@/components/dashboard/OrderManager"
import { CoherenceAura } from "@/components/dashboard/CoherenceAura"

export default function DashboardPage() {
  return (
    <ProtectedRoute>
      <div className="space-y-6">
        <h1 className="text-3xl font-bold tracking-tight">Dashboard Web Trader</h1>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {/* Main Trading Area - Takes up 3 columns */}
          <div className="md:col-span-3 rounded-lg border bg-card text-card-foreground shadow-sm p-6">
            <TradingView />
            <div className="mt-6 space-y-6">
              {/* Active Orders & Emergency Controls */}
              <TradingConsole />
              {/* Detailed Order Management */}
              <OrderManager />
            </div>
          </div>

          {/* Side Panel - Takes up 1 column */}
          <div className="md:col-span-1 space-y-6">
            {/* Mahabhutas Coherence Visualization */}
            <CoherenceAura />

            {/* Placeholder for future widgets like Market Sentiment or Alerts */}
            <div className="rounded-lg border bg-card text-card-foreground shadow-sm p-6 h-[200px] flex items-center justify-center text-muted-foreground">
              Market Sentiment (Coming Soon)
            </div>
          </div>
        </div>
      </div>
    </ProtectedRoute>
  )
}
