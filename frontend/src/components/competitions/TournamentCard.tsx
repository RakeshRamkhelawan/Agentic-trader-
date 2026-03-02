import React, { useState } from 'react';
import { Calendar, Users, Trophy, Clock, ChevronRight } from 'lucide-react';

interface Tournament {
  id: string;
  name: string;
  description: string;
  type: string;
  participants: number;
  max_participants: number;
  ends_at: string;
  time_remaining: string;
  entry_fee?: number;
  prize_pool?: number;
}

interface TournamentCardProps {
  tournament: Tournament;
  onEnter?: (tournamentId: string) => void;
  isEntered?: boolean;
}

export const TournamentCard: React.FC<TournamentCardProps> = ({
  tournament,
  onEnter,
  isEntered = false,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const participationPercent = Math.round(
    (tournament.participants / tournament.max_participants) * 100
  );

  const getStatusColor = () => {
    if (participationPercent >= 90) return 'text-red-400';
    if (participationPercent >= 70) return 'text-yellow-400';
    return 'text-green-400';
  };

  return (
    <div className="bg-slate-900 rounded-lg overflow-hidden border border-slate-800 hover:border-slate-700 transition-colors">
      {/* Header */}
      <div className="p-5">
        <div className="flex items-start justify-between mb-3">
          <div>
            <h3 className="text-lg font-bold text-white">{tournament.name}</h3>
            <p className="text-slate-400 text-sm mt-1">{tournament.description}</p>
          </div>
          <span className="px-3 py-1 rounded-full text-xs font-medium bg-indigo-600/20 text-indigo-400">
            {tournament.type}
          </span>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-3 gap-4 mt-4">
          <div className="flex items-center gap-2">
            <Users className="w-4 h-4 text-slate-500" />
            <div>
              <p className={`text-sm font-medium ${getStatusColor()}`}>
                {tournament.participants}/{tournament.max_participants}
              </p>
              <p className="text-xs text-slate-500">Participants</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-slate-500" />
            <div>
              <p className="text-sm font-medium text-white">
                {tournament.time_remaining.split('.')[0]}
              </p>
              <p className="text-xs text-slate-500">Remaining</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Trophy className="w-4 h-4 text-slate-500" />
            <div>
              <p className="text-sm font-medium text-yellow-500">
                {tournament.prize_pool?.toLocaleString() || '1,000'} pts
              </p>
              <p className="text-xs text-slate-500">Prize Pool</p>
            </div>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mt-4">
          <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all ${
                participationPercent >= 90
                  ? 'bg-red-500'
                  : participationPercent >= 70
                  ? 'bg-yellow-500'
                  : 'bg-green-500'
              }`}
              style={{ width: `${participationPercent}%` }}
            />
          </div>
          <p className="text-xs text-slate-500 mt-1">
            {participationPercent}% filled
            {participationPercent >= 90 && ' - Almost full!'}
          </p>
        </div>
      </div>

      {/* Footer */}
      <div className="px-5 py-3 bg-slate-800/50 border-t border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-4 text-sm text-slate-400">
          <div className="flex items-center gap-1">
            <Calendar className="w-4 h-4" />
            <span>Ends {new Date(tournament.ends_at).toLocaleDateString()}</span>
          </div>
          {tournament.entry_fee ? (
            <span className="text-amber-400">Entry: {tournament.entry_fee} pts</span>
          ) : (
            <span className="text-green-400">Free Entry</span>
          )}
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-2 text-slate-400 hover:text-white transition-colors"
          >
            <ChevronRight
              className={`w-5 h-5 transition-transform ${
                isExpanded ? 'rotate-90' : ''
              }`}
            />
          </button>
          {onEnter && !isEntered && (
            <button
              onClick={() => onEnter(tournament.id)}
              disabled={participationPercent >= 100}
              className={`px-4 py-2 rounded-lg font-medium text-sm transition-colors ${
                participationPercent >= 100
                  ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
                  : 'bg-indigo-600 hover:bg-indigo-500 text-white'
              }`}
            >
              {participationPercent >= 100 ? 'Full' : 'Enter'}
            </button>
          )}
          {isEntered && (
            <span className="px-4 py-2 rounded-lg font-medium text-sm bg-green-600/20 text-green-400">
              Entered
            </span>
          )}
        </div>
      </div>

      {/* Expanded Details */}
      {isExpanded && (
        <div className="px-5 py-4 bg-slate-800/30 border-t border-slate-800">
          <h4 className="text-sm font-medium text-white mb-3">Prize Distribution</h4>
          <div className="grid grid-cols-5 gap-2">
            {[
              { pos: 1, prize: '1,000 pts', badge: 'Gold Trophy' },
              { pos: 2, prize: '500 pts', badge: 'Silver Trophy' },
              { pos: 3, prize: '250 pts', badge: 'Bronze Trophy' },
              { pos: 4, prize: '100 pts', badge: '' },
              { pos: 5, prize: '100 pts', badge: '' },
            ].map((prize) => (
              <div
                key={prize.pos}
                className="text-center p-3 bg-slate-800 rounded-lg"
              >
                <p className="text-lg font-bold text-white">#{prize.pos}</p>
                <p className="text-sm text-yellow-500">{prize.prize}</p>
                {prize.badge && (
                  <p className="text-xs text-slate-500 mt-1">{prize.badge}</p>
                )}
              </div>
            ))}
          </div>
          <p className="text-xs text-slate-500 mt-3">
            Positions 6-10 receive 50 points each. Starting balance: 10,000 EUR (paper).
          </p>
        </div>
      )}
    </div>
  );
};

export default TournamentCard;
