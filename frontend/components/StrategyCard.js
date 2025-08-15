import { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  Play, 
  Square,
  ExternalLink,
  TrendingUp, 
  Clock, 
  DollarSign,
  Activity,
  Zap
} from 'lucide-react';

export default function StrategyCard({ strategy, onRun, onStop, onViewDetails }) {
  const [isLoading, setIsLoading] = useState(false);
  const isRunning = strategy.status === 'running';

  const handleRun = async () => {
    setIsLoading(true);
    try {
      await onRun(strategy.id);
    } catch (error) {
      console.error('Failed to run strategy:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStop = () => {
    onStop(strategy.id);
  };

  const getTypeIcon = (type) => {
    const icons = {
      cross_chain: Activity,
      flashloan: Zap,
      latency: Clock,
      multi_pair: TrendingUp,
      mev: Activity,
      stablecoin: DollarSign,
      triangular: Activity,
    };
    return icons[type] || Activity;
  };

  const getStatusColor = (status) => {
    return status === 'running' 
      ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400'
      : 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400';
  };

  const getChainColor = (chain) => {
    const colors = {
      ethereum: 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400',
      arbitrum: 'bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-400',
      polygon: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/20 dark:text-indigo-400',
      solana: 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400',
      base: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400',
      optimism: 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400',
    };
    return colors[chain] || 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400';
  };

  const TypeIcon = getTypeIcon(strategy.type);
  const currentStatus = strategy.status;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -5, scale: 1.02 }}
      transition={{ duration: 0.3 }}
      className="bg-white dark:bg-dark-800 rounded-xl shadow-lg border border-gray-200 dark:border-dark-700 overflow-hidden h-[380px] flex flex-col"
    >
      {/* Header */}
      <div className="p-4 flex-shrink-0">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center space-x-2">
            <div className="p-1.5 bg-blue-100 dark:bg-blue-900/20 rounded-lg">
              <TypeIcon className="w-4 h-4 text-blue-600 dark:text-blue-400" />
            </div>
            <h3 className="text-base font-semibold text-gray-900 dark:text-white truncate">
              {strategy.name}
            </h3>
          </div>
          <div className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(currentStatus)}`}>
            {currentStatus}
          </div>
        </div>
        <p className="text-xs text-gray-600 dark:text-gray-400 line-clamp-1">
          {strategy.description}
        </p>
      </div>

      {/* Chains */}
      <div className="px-4 py-2 bg-gray-50 dark:bg-dark-700/50 flex-shrink-0">
        <div className="flex flex-wrap gap-1">
          {strategy.chains?.map((chain) => (
            <span
              key={chain}
              className={`px-1.5 py-0.5 rounded text-xs font-medium ${getChainColor(chain)}`}
            >
              {chain}
            </span>
          ))}
        </div>
      </div>

      {/* Metrics */}
      <div className="p-4 flex-1 flex flex-col">
        <div className="grid grid-cols-2 gap-4 mb-4 flex-1">
          <div className="bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-700 rounded-lg p-3 text-center border border-gray-200 dark:border-gray-600">
            <p className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Total Trades</p>
            <p className="text-xl font-bold text-gray-900 dark:text-white">
              {strategy.total_trades || 0}
            </p>
          </div>
          <div className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 rounded-lg p-3 text-center border border-green-200 dark:border-green-700">
            <p className="text-xs font-medium text-green-700 dark:text-green-400 mb-1">Total Profit</p>
            <p className="text-xl font-bold text-green-600 dark:text-green-400">
              ${(strategy.total_profit || 0).toFixed(2)}
            </p>
          </div>
          <div className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 rounded-lg p-3 text-center border border-blue-200 dark:border-blue-700">
            <p className="text-xs font-medium text-blue-700 dark:text-blue-400 mb-1">Success Rate</p>
            <p className="text-xl font-bold text-blue-600 dark:text-blue-400">
              {(strategy.success_rate || 0).toFixed(1)}%
            </p>
          </div>
          <div className="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 rounded-lg p-3 text-center border border-purple-200 dark:border-purple-700">
            <p className="text-xs font-medium text-purple-700 dark:text-purple-400 mb-1">Status</p>
            <p className="text-sm font-bold text-purple-600 dark:text-purple-400">
              {isRunning ? 'Active' : 'Ready'}
            </p>
          </div>
        </div>

        {/* Actions */}
        <div className="flex space-x-2 mt-auto">
          {isRunning ? (
            <>
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={handleStop}
                className="flex-1 flex items-center justify-center space-x-1 px-3 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-medium transition-colors"
              >
                <Square className="w-3 h-3" />
                <span>Stop</span>
              </motion.button>
              
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => window.open(strategy.spreadsheet, '_blank')}
                className="px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                title="View Live Sheet"
              >
                <ExternalLink className="w-3 h-3" />
              </motion.button>
            </>
          ) : (
            <>
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={handleRun}
                disabled={isLoading}
                className="flex-1 flex items-center justify-center space-x-1 px-3 py-2 bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white rounded-lg text-sm font-medium transition-colors"
              >
                {isLoading ? (
                  <>
                    <div className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    <span>Starting...</span>
                  </>
                ) : (
                  <>
                    <Play className="w-3 h-3" />
                    <span>Run</span>
                  </>
                )}
              </motion.button>
              
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => onViewDetails(strategy.id)}
                className="px-3 py-2 border border-gray-300 dark:border-dark-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-dark-700 rounded-lg text-sm font-medium transition-colors"
              >
                Details
              </motion.button>
            </>
          )}
        </div>
      </div>
    </motion.div>
  );
}