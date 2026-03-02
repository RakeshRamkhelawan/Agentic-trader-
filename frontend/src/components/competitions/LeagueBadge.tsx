import React from 'react';
import { Star, Trophy, Crown, Diamond } from 'lucide-react';

interface LeagueBadgeProps {
  tier: 'bronze' | 'silver' | 'gold' | 'diamond';
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  points?: number;
}

const tierConfig = {
  bronze: {
    icon: Star,
    label: 'Bronze',
    color: 'text-amber-600',
    bgColor: 'bg-amber-600',
    borderColor: 'border-amber-600',
    gradient: 'from-amber-700 to-amber-500',
    minPoints: 0,
    maxPoints: 1000,
  },
  silver: {
    icon: Trophy,
    label: 'Silver',
    color: 'text-slate-400',
    bgColor: 'bg-slate-400',
    borderColor: 'border-slate-400',
    gradient: 'from-slate-500 to-slate-300',
    minPoints: 1000,
    maxPoints: 10000,
  },
  gold: {
    icon: Crown,
    label: 'Gold',
    color: 'text-yellow-500',
    bgColor: 'bg-yellow-500',
    borderColor: 'border-yellow-500',
    gradient: 'from-yellow-600 to-yellow-400',
    minPoints: 10000,
    maxPoints: 50000,
  },
  diamond: {
    icon: Diamond,
    label: 'Diamond',
    color: 'text-cyan-400',
    bgColor: 'bg-cyan-400',
    borderColor: 'border-cyan-400',
    gradient: 'from-cyan-600 to-cyan-300',
    minPoints: 50000,
    maxPoints: Infinity,
  },
};

const sizeConfig = {
  sm: {
    container: 'w-8 h-8',
    icon: 'w-4 h-4',
    text: 'text-xs',
    padding: 'p-1',
  },
  md: {
    container: 'w-12 h-12',
    icon: 'w-6 h-6',
    text: 'text-sm',
    padding: 'p-2',
  },
  lg: {
    container: 'w-20 h-20',
    icon: 'w-10 h-10',
    text: 'text-lg',
    padding: 'p-3',
  },
};

export const LeagueBadge: React.FC<LeagueBadgeProps> = ({
  tier,
  size = 'md',
  showLabel = true,
  points,
}) => {
  const config = tierConfig[tier];
  const sizeClasses = sizeConfig[size];
  const Icon = config.icon;

  const progressToNext = points
    ? Math.min(
        100,
        ((points - config.minPoints) / (config.maxPoints - config.minPoints)) * 100
      )
    : 0;

  return (
    <div className="flex flex-col items-center gap-2">
      {/* Badge */}
      <div
        className={`
          relative ${sizeClasses.container} rounded-full 
          bg-gradient-to-br ${config.gradient}
          flex items-center justify-center
          shadow-lg
          ${tier === 'diamond' ? 'animate-pulse' : ''}
        `}
      >
        {/* Glow effect for diamond */}
        {tier === 'diamond' && (
          <div className="absolute inset-0 rounded-full bg-cyan-400/30 blur-md" />
        )}
        
        {/* Icon */}
        <Icon className={`${sizeClasses.icon} text-white relative z-10`} />
        
        {/* Shine effect */}
        <div className="absolute inset-0 rounded-full bg-gradient-to-tr from-white/20 to-transparent" />
      </div>

      {/* Label */}
      {showLabel && (
        <div className="text-center">
          <p className={`font-bold ${config.color} ${sizeClasses.text}`}>
            {config.label}
          </p>
          {points !== undefined && (
            <p className="text-xs text-slate-500">
              {points.toLocaleString()} pts
            </p>
          )}
        </div>
      )}

      {/* Progress to next tier */}
      {points !== undefined && tier !== 'diamond' && (
        <div className="w-full max-w-[120px]">
          <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
            <div
              className={`h-full ${config.bgColor} transition-all`}
              style={{ width: `${progressToNext}%` }}
            />
          </div>
          <p className="text-[10px] text-slate-500 text-center mt-1">
            {Math.round(progressToNext)}% to next tier
          </p>
        </div>
      )}
    </div>
  );
};

export const LeagueBadgeInline: React.FC<{
  tier: 'bronze' | 'silver' | 'gold' | 'diamond';
}> = ({ tier }) => {
  const config = tierConfig[tier];
  const Icon = config.icon;

  return (
    <span
      className={`
        inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full
        text-xs font-medium bg-slate-800 ${config.color}
        border border-slate-700
      `}
    >
      <Icon className="w-3 h-3" />
      {config.label}
    </span>
  );
};

export default LeagueBadge;
