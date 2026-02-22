import React, { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface VedicState {
  rahu_kala: boolean;
  market_regime: "expansion" | "contraction" | "neutral" | "recovery";
  harmony_score: number;
  dominant_element: "ether" | "fire" | "air" | "water" | "earth";
  prana_levels: Record<string, number>;
  vedic_time: string;
  navagraha_dominant: string;
}

const ELEMENT_COLORS: Record<string, string> = {
  ether: "#9B59B6",
  air: "#3498DB",
  fire: "#E74C3C",
  water: "#1ABC9C",
  earth: "#F39C12",
};

const REGIME_BADGES: Record<string, { color: string; icon: string }> = {
  expansion: { color: "bg-green-500", icon: "🟢" },
  contraction: { color: "bg-red-500", icon: "🔴" },
  neutral: { color: "bg-gray-400", icon: "⚪" },
  recovery: { color: "bg-blue-500", icon: "🔵" },
};

export function VedicContextPanel({ wsUrl }: { wsUrl: string }) {
  const [state, setState] = useState<VedicState>({
    rahu_kala: false,
    market_regime: "neutral",
    harmony_score: 0.5,
    dominant_element: "ether",
    prana_levels: { ether: 100, air: 100, fire: 100, water: 100, earth: 100 },
    vedic_time: "Brahma Muhurta",
    navagraha_dominant: "Jupiter",
  });

  useEffect(() => {
    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.channel === "paper_trading.vedic") {
          if (msg.type === "soul_update") {
            setState((prev) => ({
              ...prev,
              rahu_kala: msg.data.rahu_kala,
              market_regime: msg.data.market_regime,
              vedic_time: msg.data.vedic_time,
              navagraha_dominant: msg.data.navagraha_dominant,
            }));
          } else if (msg.type === "prana_update") {
            setState((prev) => ({
              ...prev,
              prana_levels: {
                ether: msg.data.ether ?? prev.prana_levels.ether,
                air: msg.data.air ?? prev.prana_levels.air,
                fire: msg.data.fire ?? prev.prana_levels.fire,
                water: msg.data.water ?? prev.prana_levels.water,
                earth: msg.data.earth ?? prev.prana_levels.earth,
              },
            }));
          } else if (msg.type === "harmony_update") {
            setState((prev) => ({
              ...prev,
              harmony_score: msg.data.harmony_score,
              dominant_element: msg.data.dominant_element,
            }));
          }
        }
      } catch (err) {
        console.error("WS parse error:", err);
      }
    };

    return () => ws.close();
  }, [wsUrl]);

  const harmonyColor =
    state.harmony_score >= 0.7
      ? "text-green-400"
      : state.harmony_score >= 0.3
      ? "text-yellow-400"
      : "text-red-400";

  return (
    <div className="space-y-4">
      {/* Rahu Kala Alert */}
      {state.rahu_kala && (
        <Card className="border-red-500 bg-red-900/50">
          <CardContent className="pt-6">
            <div className="flex items-center gap-2">
              <span className="text-2xl">🔴</span>
              <div>
                <p className="text-red-300 font-bold">RAHU KALA ACTIEF</p>
                <p className="text-red-400 text-sm">Trading geblokkeerd</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Harmony Score */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Harmony Score</CardTitle>
        </CardHeader>
        <CardContent>
          <div className={`text-3xl font-bold ${harmonyColor}`}>
            {(state.harmony_score * 100).toFixed(0)}%
          </div>
          <div className="w-full bg-gray-700 rounded-full h-2 mt-2">
            <div
              className={`h-2 rounded-full ${
                state.harmony_score >= 0.7
                  ? "bg-green-400"
                  : state.harmony_score >= 0.3
                  ? "bg-yellow-400"
                  : "bg-red-400"
              }`}
              style={{ width: `${state.harmony_score * 100}%` }}
            />
          </div>
        </CardContent>
      </Card>

      {/* Market Regime */}
      <Card>
        <CardContent className="pt-4">
          <div className="flex items-center gap-2">
            <span className="text-gray-400 text-sm">Regime:</span>
            <Badge className={REGIME_BADGES[state.market_regime]?.color}>
              {REGIME_BADGES[state.market_regime]?.icon} {state.market_regime.toUpperCase()}
            </Badge>
          </div>
        </CardContent>
      </Card>

      {/* Prana Bars */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Elementaire Prana</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {Object.entries(state.prana_levels).map(([element, prana]) => (
              <div key={element}>
                <div className="flex justify-between text-xs mb-1">
                  <span style={{ color: ELEMENT_COLORS[element] }}>
                    {element.charAt(0).toUpperCase() + element.slice(1)}
                    {element === state.dominant_element ? " ★" : ""}
                  </span>
                  <span className={prana < 10 ? "text-red-400" : ""}>
                    {prana.toFixed(0)}
                  </span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-1.5">
                  <div
                    className="h-1.5 rounded-full"
                    style={{
                      width: `${prana}%`,
                      backgroundColor: ELEMENT_COLORS[element],
                      opacity: prana < 10 ? 0.4 : 1,
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default VedicContextPanel;
