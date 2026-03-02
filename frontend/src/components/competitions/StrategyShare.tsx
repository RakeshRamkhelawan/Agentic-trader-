import React, { useState } from 'react';
import { Code, Share2, Eye, Heart, Download, GitBranch, Search, Filter } from 'lucide-react';

interface Strategy {
  id: string;
  name: string;
  description: string;
  author_name: string;
  language: string;
  tags: string[];
  metrics: {
    total_return: number;
    sharpe_ratio: number;
    max_drawdown: number;
    win_rate: number;
    total_trades: number;
  };
  engagement: {
    likes: number;
    views: number;
    downloads: number;
    forks: number;
  };
  score: number;
  created_at: string;
}

interface StrategyShareProps {
  strategies?: Strategy[];
}

export const StrategyShare: React.FC<StrategyShareProps> = ({ strategies = [] }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [sortBy, setSortBy] = useState('score');
  const [showShareModal, setShowShareModal] = useState(false);

  // Mock data if no strategies provided
  const mockStrategies: Strategy[] = [
    {
      id: '1',
      name: 'Vedic Moon Breakout',
      description: 'Entry on nakshatra transitions with volume confirmation',
      author_name: 'TraderPro',
      language: 'python',
      tags: ['vedic', 'breakout', 'momentum'],
      metrics: {
        total_return: 45.2,
        sharpe_ratio: 1.8,
        max_drawdown: -12.5,
        win_rate: 68.5,
        total_trades: 127,
      },
      engagement: {
        likes: 42,
        views: 523,
        downloads: 89,
        forks: 12,
      },
      score: 87.3,
      created_at: '2026-02-20T10:00:00Z',
    },
    {
      id: '2',
      name: 'Elemental Consensus',
      description: 'Multi-element confirmation system for high-probability trades',
      author_name: 'AlgoMaster',
      language: 'python',
      tags: ['elemental', 'consensus', 'swing'],
      metrics: {
        total_return: 38.7,
        sharpe_ratio: 2.1,
        max_drawdown: -8.3,
        win_rate: 72.1,
        total_trades: 89,
      },
      engagement: {
        likes: 38,
        views: 412,
        downloads: 67,
        forks: 8,
      },
      score: 91.5,
      created_at: '2026-02-18T14:30:00Z',
    },
  ];

  const displayStrategies = strategies.length > 0 ? strategies : mockStrategies;

  const allTags = Array.from(
    new Set(displayStrategies.flatMap((s) => s.tags))
  ).sort();

  const toggleTag = (tag: string) => {
    setSelectedTags((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]
    );
  };

  const filteredStrategies = displayStrategies.filter((strategy) => {
    const matchesSearch =
      !searchQuery ||
      strategy.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      strategy.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesTags =
      selectedTags.length === 0 ||
      selectedTags.some((tag) => strategy.tags.includes(tag));
    return matchesSearch && matchesTags;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Share2 className="w-6 h-6 text-indigo-400" />
          <h2 className="text-xl font-bold text-white">Strategy Library</h2>
        </div>
        <button
          onClick={() => setShowShareModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg font-medium transition-colors"
        >
          <Code className="w-4 h-4" />
          Share Strategy
        </button>
      </div>

      {/* Search and Filter */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
          <input
            type="text"
            placeholder="Search strategies..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter className="w-5 h-5 text-slate-500" />
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-indigo-500"
          >
            <option value="score">Highest Score</option>
            <option value="likes">Most Liked</option>
            <option value="newest">Newest</option>
            <option value="downloads">Most Downloaded</option>
          </select>
        </div>
      </div>

      {/* Tags */}
      <div className="flex flex-wrap gap-2">
        {allTags.map((tag) => (
          <button
            key={tag}
            onClick={() => toggleTag(tag)}
            className={`px-3 py-1 rounded-full text-sm transition-colors ${
              selectedTags.includes(tag)
                ? 'bg-indigo-600 text-white'
                : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
            }`}
          >
            {tag}
          </button>
        ))}
      </div>

      {/* Strategy Grid */}
      <div className="grid gap-4">
        {filteredStrategies.map((strategy) => (
          <div
            key={strategy.id}
            className="bg-slate-900 rounded-lg p-5 border border-slate-800 hover:border-slate-700 transition-colors"
          >
            <div className="flex items-start justify-between mb-3">
              <div>
                <h3 className="text-lg font-bold text-white">{strategy.name}</h3>
                <p className="text-slate-400 text-sm mt-1">{strategy.description}</p>
              </div>
              <div className="flex items-center gap-2">
                <span className="px-3 py-1 rounded-full text-xs font-medium bg-slate-800 text-slate-400">
                  {strategy.language}
                </span>
                <span className="px-3 py-1 rounded-full text-xs font-medium bg-indigo-600/20 text-indigo-400">
                  Score: {strategy.score.toFixed(1)}
                </span>
              </div>
            </div>

            {/* Author */}
            <div className="flex items-center gap-2 mb-4">
              <div className="w-6 h-6 rounded-full bg-slate-700 flex items-center justify-center">
                <span className="text-xs text-white font-medium">
                  {strategy.author_name.charAt(0)}
                </span>
              </div>
              <span className="text-sm text-slate-400">{strategy.author_name}</span>
              <span className="text-slate-600">|</span>
              <span className="text-sm text-slate-500">
                {new Date(strategy.created_at).toLocaleDateString()}
              </span>
            </div>

            {/* Metrics */}
            <div className="grid grid-cols-5 gap-4 mb-4 p-3 bg-slate-800/50 rounded-lg">
              <div>
                <p className="text-xs text-slate-500">Return</p>
                <p
                  className={`text-sm font-mono font-medium ${
                    strategy.metrics.total_return >= 0
                      ? 'text-green-400'
                      : 'text-red-400'
                  }`}
                >
                  {strategy.metrics.total_return >= 0 ? '+' : ''}
                  {strategy.metrics.total_return.toFixed(1)}%
                </p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Sharpe</p>
                <p className="text-sm font-mono font-medium text-white">
                  {strategy.metrics.sharpe_ratio.toFixed(2)}
                </p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Drawdown</p>
                <p className="text-sm font-mono font-medium text-red-400">
                  {strategy.metrics.max_drawdown.toFixed(1)}%
                </p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Win Rate</p>
                <p className="text-sm font-mono font-medium text-white">
                  {strategy.metrics.win_rate.toFixed(1)}%
                </p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Trades</p>
                <p className="text-sm font-mono font-medium text-white">
                  {strategy.metrics.total_trades}
                </p>
              </div>
            </div>

            {/* Tags and Engagement */}
            <div className="flex items-center justify-between">
              <div className="flex gap-2">
                {strategy.tags.map((tag) => (
                  <span
                    key={tag}
                    className="px-2 py-1 bg-slate-800 text-slate-400 text-xs rounded"
                  >
                    {tag}
                  </span>
                ))}
              </div>
              <div className="flex items-center gap-4 text-sm text-slate-400">
                <span className="flex items-center gap-1">
                  <Eye className="w-4 h-4" />
                  {strategy.engagement.views}
                </span>
                <span className="flex items-center gap-1">
                  <Heart className="w-4 h-4" />
                  {strategy.engagement.likes}
                </span>
                <span className="flex items-center gap-1">
                  <Download className="w-4 h-4" />
                  {strategy.engagement.downloads}
                </span>
                <span className="flex items-center gap-1">
                  <GitBranch className="w-4 h-4" />
                  {strategy.engagement.forks}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {filteredStrategies.length === 0 && (
        <div className="text-center py-12">
          <Code className="w-12 h-12 text-slate-600 mx-auto mb-4" />
          <p className="text-slate-400">No strategies found matching your criteria.</p>
        </div>
      )}
    </div>
  );
};

export default StrategyShare;
