import React, { useState, useEffect } from 'react';
import { Trophy, Medal, Star, TrendingUp, Users } from 'lucide-react';

interface Competitor {
  rank: number;
  competitor_id: string;
  name: string;
  tier: string;
  points: number;
  total_pnl: number;
  win_rate: number;
  reputation: number;
}

interface LeaderboardProps {
  tier?: string;
  limit?: number;
}

const tierColors: Record<string, string> = {
  bronze: 'text-amber-600',
  silver: 'text-slate-400',
  gold: 'text-yellow-500',
  diamond: 'text-cyan-400',
};

const tierBgColors: Record<string, string> = {
  bronze: 'bg-amber-600',
  silver: 'bg-slate-400',
  gold: 'bg-yellow-500',
  diamond: 'bg-cyan-400',
};

export const Leaderboard: React.FC<LeaderboardProps> = ({ tier, limit = 20 }) => {
  const [leaderboard, setLeaderboard] = useState<Competitor[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTier, setSelectedTier] = useState<string>(tier || 'all');

  useEffect(() => {
    fetchLeaderboard();
  }, [selectedTier, limit]);

  const fetchLeaderboard = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (selectedTier !== 'all') params.append('tier', selectedTier);
      params.append('limit', limit.toString());

      const response = await fetch(`/api/competitions/leaderboard?${params}`);
      const data = await response.json();
      setLeaderboard(data.leaderboard || []);
    } catch (error) {
      console.error('Failed to fetch leaderboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const getRankIcon = (rank: number) => {
    if (rank === 1) return <Trophy className="w-6 h-6 text-yellow-500" />;
    if (rank === 2) return <Medal className="w-6 h-6 text-slate-400" />;
    if (rank === 3) return <Medal className="w-6 h-6 text-amber-600" />;
    return <span className="text-slate-500 font-mono w-6 text-center">{rank}</span>;
  };

  if (loading) {
    return (
      <div className="bg-slate-900 rounded-lg p-6">
        <div className="animate-pulse space-y-4">
          {[...Array(10)].map((_, i) => (
            <div key={i} className="h-16 bg-slate-800 rounded" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-slate-900 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="p-6 border-b border-slate-800">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <Trophy className="w-6 h-6 text-yellow-500" />
            <h2 className="text-xl font-bold text-white">Leaderboard</h2>
          </div>
          <div className="flex items-center gap-2 text-slate-400 text-sm">
            <Users className="w-4 h-4" />
            <span>{leaderboard.length} traders</span>
          </div>
        </div>

        {/* Tier Filter */}
        <div className="flex gap-2">
          {['all', 'bronze', 'silver', 'gold', 'diamond'].map((t) => (
            <button
              key={t}
              onClick={() => setSelectedTier(t)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                selectedTier === t
                  ? 'bg-indigo-600 text-white'
                  : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
              }`}
            >
              {t.charAt(0).toUpperCase() + t.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Leaderboard Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-slate-800 text-slate-400 text-sm">
            <tr>
              <th className="px-4 py-3 text-left">Rank</th>
              <th className="px-4 py-3 text-left">Trader</th>
              <th className="px-4 py-3 text-left">Tier</th>
              <th className="px-4 py-3 text-right">Points</th>
              <th className="px-4 py-3 text-right">P&L</th>
              <th className="px-4 py-3 text-right">Win Rate</th>
              <th className="px-4 py-3 text-right">Reputation</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {leaderboard.map((competitor) => (
              <tr
                key={competitor.competitor_id}
                className="hover:bg-slate-800/50 transition-colors"
              >
                <td className="px-4 py-4">
                  <div className="flex items-center justify-center">
                    {getRankIcon(competitor.rank)}
                  </div>
                </td>
                <td className="px-4 py-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-slate-700 flex items-center justify-center">
                      <span className="text-white font-bold">
                        {competitor.name.charAt(0).toUpperCase()}
                      </span>
                    </div>
                    <span className="text-white font-medium">{competitor.name}</span>
                  </div>
                </td>
                <td className="px-4 py-4">
                  <span
                    className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-slate-800 ${tierColors[competitor.tier]}`}
                  >
                    <Star className="w-3 h-3" />
                    {competitor.tier.charAt(0).toUpperCase() + competitor.tier.slice(1)}
                  </span>
                </td>
                <td className="px-4 py-4 text-right">
                  <span className="text-white font-mono">
                    {competitor.points.toLocaleString()}
                  </span>
                </td>
                <td className="px-4 py-4 text-right">
                  <span
                    className={`font-mono ${
                      competitor.total_pnl >= 0 ? 'text-green-400' : 'text-red-400'
                    }`}
                  >
                    {competitor.total_pnl >= 0 ? '+' : ''}
                    {competitor.total_pnl.toFixed(2)} EUR
                  </span>
                </td>
                <td className="px-4 py-4 text-right">
                  <span className="text-slate-300 font-mono">
                    {competitor.win_rate.toFixed(1)}%
                  </span>
                </td>
                <td className="px-4 py-4 text-right">
                  <div className="flex items-center justify-end gap-1 text-indigo-400">
                    <TrendingUp className="w-4 h-4" />
                    <span className="font-mono">{competitor.reputation.toFixed(0)}</span>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {leaderboard.length === 0 && (
        <div className="p-12 text-center">
          <Trophy className="w-12 h-12 text-slate-600 mx-auto mb-4" />
          <p className="text-slate-400">No competitors found in this tier yet.</p>
          <p className="text-slate-500 text-sm mt-2">Be the first to join!</p>
        </div>
      )}
    </div>
  );
};

export default Leaderboard;
