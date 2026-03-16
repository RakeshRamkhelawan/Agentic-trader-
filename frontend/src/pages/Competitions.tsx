import { useState, useEffect } from 'react';
import { Trophy, Target, Share2, TrendingUp, Calendar, Users, Award, Zap, Loader2 } from 'lucide-react';
import Leaderboard from '../components/competitions/Leaderboard';
import TournamentCard from '../components/competitions/TournamentCard';
import StrategyShare from '../components/competitions/StrategyShare';
import LeagueBadge from '../components/competitions/LeagueBadge';
import { competitionsApi } from '@/lib/api';
import { toast } from 'sonner';

interface Tournament {
  id: string;
  name: string;
  description: string;
  type: string;
  participants: number;
  max_participants: number;
  ends_at: string;
  time_remaining: string;
  entry_fee: number;
  prize_pool: number;
}

interface LeagueInfo {
  tier: string;
  name: string;
  min_points: number;
  max_points: number;
  current_members: number;
  max_members: number;
}

const Competitions = () => {
  const [activeTab, setActiveTab] = useState<'overview' | 'tournaments' | 'leaderboard' | 'strategies'>('overview');
  const [tournaments, setTournaments] = useState<Tournament[]>([]);
  const [leagueInfo, setLeagueInfo] = useState<Record<string, LeagueInfo>>({});
  const [userStats, setUserStats] = useState({
    tier: 'silver' as const,
    points: 4850,
    rank: 42,
    tournamentsEntered: 5,
    tournamentsWon: 1,
    strategiesShared: 3,
    totalPnl: 12580.50,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      // Fetch tournaments
      const tourneyData = await competitionsApi.getTournaments('active');
      setTournaments(tourneyData.tournaments || []);

      // Fetch league info
      const leagueData = await competitionsApi.getLeagueInfo();
      setLeagueInfo(leagueData);
    } catch (error) {
      console.error('Failed to fetch competition data:', error);
      toast.error('Failed to load competition data');
    } finally {
      setLoading(false);
    }
  };

  const handleEnterTournament = async (tournamentId: string) => {
    try {
      const data = await competitionsApi.enterTournament('current-user-id', tournamentId);
      if (data.success) {
        toast.success('Successfully entered tournament!');
        fetchData();
      } else {
        toast.error(data.error || 'Failed to enter tournament');
      }
    } catch (error) {
      console.error('Failed to enter tournament:', error);
      toast.error('Failed to enter tournament');
    }
  };

  const tabs = [
    { id: 'overview', label: 'Overview', icon: Trophy },
    { id: 'tournaments', label: 'Tournaments', icon: Target },
    { id: 'leaderboard', label: 'Leaderboard', icon: TrendingUp },
    { id: 'strategies', label: 'Strategies', icon: Share2 },
  ];

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 p-6">
        <div className="max-w-7xl mx-auto flex items-center justify-center min-h-[400px]">
          <div className="flex items-center gap-2 text-slate-400">
            <Loader2 className="w-5 h-5 animate-spin" />
            <span>Loading competitions...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Header */}
      <div className="bg-slate-900 border-b border-slate-800">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white">Trading Competitions</h1>
              <p className="text-slate-400 mt-1">
                Compete, learn, and climb the ranks from Bronze to Diamond
              </p>
            </div>
            <div className="flex items-center gap-4">
              <LeagueBadge tier={userStats.tier} size="lg" points={userStats.points} />
            </div>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="bg-slate-900/50 border-b border-slate-800">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex gap-1">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === tab.id
                      ? 'border-indigo-500 text-indigo-400'
                      : 'border-transparent text-slate-400 hover:text-white'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {tab.label}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-6 py-6">
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Stats Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-slate-900 rounded-lg p-4 border border-slate-800">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-indigo-600/20 rounded-lg">
                    <Trophy className="w-5 h-5 text-indigo-400" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-white">{userStats.rank}</p>
                    <p className="text-xs text-slate-500">Global Rank</p>
                  </div>
                </div>
              </div>
              <div className="bg-slate-900 rounded-lg p-4 border border-slate-800">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-green-600/20 rounded-lg">
                    <Target className="w-5 h-5 text-green-400" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-white">{userStats.tournamentsEntered}</p>
                    <p className="text-xs text-slate-500">Tournaments</p>
                  </div>
                </div>
              </div>
              <div className="bg-slate-900 rounded-lg p-4 border border-slate-800">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-yellow-600/20 rounded-lg">
                    <Award className="w-5 h-5 text-yellow-400" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-white">{userStats.tournamentsWon}</p>
                    <p className="text-xs text-slate-500">Victories</p>
                  </div>
                </div>
              </div>
              <div className="bg-slate-900 rounded-lg p-4 border border-slate-800">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-cyan-600/20 rounded-lg">
                    <Zap className="w-5 h-5 text-cyan-400" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-white">
                      +{userStats.totalPnl.toLocaleString()} EUR
                    </p>
                    <p className="text-xs text-slate-500">Total P&L</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Two Column Layout */}
            <div className="grid lg:grid-cols-2 gap-6">
              {/* Active Tournaments */}
              <div className="bg-slate-900 rounded-lg p-6 border border-slate-800">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-bold text-white flex items-center gap-2">
                    <Calendar className="w-5 h-5 text-indigo-400" />
                    Active Tournaments
                  </h2>
                  <button
                    onClick={() => setActiveTab('tournaments')}
                    className="text-sm text-indigo-400 hover:text-indigo-300"
                  >
                    View All
                  </button>
                </div>
                <div className="space-y-4">
                  {tournaments.slice(0, 3).map((tournament) => (
                    <TournamentCard
                      key={tournament.id}
                      tournament={tournament}
                      onEnter={handleEnterTournament}
                    />
                  ))}
                  {tournaments.length === 0 && (
                    <p className="text-slate-500 text-center py-8">
                      No active tournaments. Check back soon!
                    </p>
                  )}
                </div>
              </div>

              {/* League Progress */}
              <div className="bg-slate-900 rounded-lg p-6 border border-slate-800">
                <h2 className="text-lg font-bold text-white flex items-center gap-2 mb-4">
                  <Users className="w-5 h-5 text-indigo-400" />
                  League Progress
                </h2>
                <div className="space-y-4">
                  {Object.entries(leagueInfo).map(([tier, info]) => {
                    const isCurrentTier = tier === userStats.tier;
                    const progress = Math.min(
                      100,
                      ((userStats.points - info.min_points) /
                        (info.max_points - info.min_points)) *
                        100
                    );

                    return (
                      <div
                        key={tier}
                        className={`p-4 rounded-lg border ${
                          isCurrentTier
                            ? 'bg-indigo-600/10 border-indigo-500/50'
                            : 'bg-slate-800/50 border-slate-700'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <LeagueBadge tier={tier as any} size="sm" showLabel={false} />
                            <span
                              className={`font-medium capitalize ${
                                isCurrentTier ? 'text-white' : 'text-slate-400'
                              }`}
                            >
                              {tier} League
                            </span>
                          </div>
                          <span className="text-sm text-slate-500">
                            {info.current_members} traders
                          </span>
                        </div>
                        {isCurrentTier && (
                          <div>
                            <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                              <div
                                className="h-full bg-indigo-500 transition-all"
                                style={{ width: `${progress}%` }}
                              />
                            </div>
                            <p className="text-xs text-slate-500 mt-1">
                              {userStats.points.toLocaleString()} /{' '}
                              {info.max_points.toLocaleString()} points (
                              {Math.round(progress)}%)
                            </p>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'tournaments' && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-bold text-white">Active Tournaments</h2>
              <button
                onClick={fetchData}
                className="px-4 py-2 bg-slate-800 text-white rounded-lg hover:bg-slate-700 transition-colors"
              >
                Refresh
              </button>
            </div>
            <div className="grid gap-4">
              {tournaments.map((tournament) => (
                <TournamentCard
                  key={tournament.id}
                  tournament={tournament}
                  onEnter={handleEnterTournament}
                />
              ))}
              {tournaments.length === 0 && (
                <div className="text-center py-12 bg-slate-900 rounded-lg border border-slate-800">
                  <Calendar className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                  <p className="text-slate-400">No active tournaments at the moment.</p>
                  <p className="text-slate-500 text-sm mt-2">
                    Weekly tournaments start every Monday!
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'leaderboard' && <Leaderboard />}

        {activeTab === 'strategies' && <StrategyShare />}
      </div>
    </div>
  );
};

export default Competitions;
