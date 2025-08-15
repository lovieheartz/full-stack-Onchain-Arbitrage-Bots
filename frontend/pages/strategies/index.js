import { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useRouter } from 'next/router';
import { Search, Filter } from 'lucide-react';
import StrategyCard from '../../components/StrategyCard';
import { getAllStrategies, getTotalProfit, getAverageSuccessRate, subscribeToMetricsUpdates, startStrategy, stopStrategy } from '../../lib/utils';

export default function Strategies() {
  const [strategies, setStrategies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const router = useRouter();

  // Initialize strategies and set up real-time updates
  useEffect(() => {
    const initialStrategies = getAllStrategies();
    setStrategies(initialStrategies);
    setLoading(false);
    
    // Subscribe to real-time updates
    const unsubscribe = subscribeToMetricsUpdates(() => {
      setStrategies(getAllStrategies());
    });
    
    return unsubscribe;
  }, []);

  // Filtered strategies
  const filteredStrategies = useMemo(() => {
    let filtered = strategies;

    if (searchTerm) {
      filtered = filtered.filter(strategy =>
        strategy.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        strategy.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
        strategy.type.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (filterType !== 'all') {
      filtered = filtered.filter(strategy => strategy.type === filterType);
    }

    if (filterStatus !== 'all') {
      filtered = filtered.filter(strategy => strategy.status === filterStatus);
    }

    return filtered;
  }, [strategies, searchTerm, filterType, filterStatus]);

  const handleRunStrategy = async (strategyId) => {
    startStrategy(strategyId);
    return { status: 'started' };
  };
  
  const handleStopStrategy = (strategyId) => {
    stopStrategy(strategyId);
  };

  const handleViewDetails = (strategyId) => {
    router.push(`/strategies/${strategyId}`);
  };

  // Calculate totals
  const totalStrategies = strategies.length;
  const runningStrategies = strategies.filter(s => s.status === 'running').length;
  const idleStrategies = totalStrategies - runningStrategies;
  const totalProfit = getTotalProfit();
  const avgSuccessRate = getAverageSuccessRate();

  const uniqueTypes = [...new Set(strategies.map(s => s.type))];

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-xl text-gray-600 dark:text-gray-400">Loading Strategies...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-dark-900 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                Arbitrage Strategies
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mt-2">
                Manage and monitor your on-chain arbitrage strategies
              </p>
            </div>
            <div className="flex items-center space-x-2 px-4 py-2 bg-green-100 dark:bg-green-900/20 text-green-700 dark:text-green-400 rounded-lg">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              <span className="text-sm font-medium">Live Updates</span>
            </div>
          </div>

          {/* Filters */}
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Search strategies..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-dark-600 rounded-lg bg-white dark:bg-dark-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="px-4 py-2 border border-gray-300 dark:border-dark-600 rounded-lg bg-white dark:bg-dark-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">All Types</option>
              {uniqueTypes.map(type => (
                <option key={type} value={type}>
                  {type.replace('_', ' ').toUpperCase()}
                </option>
              ))}
            </select>

            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-4 py-2 border border-gray-300 dark:border-dark-600 rounded-lg bg-white dark:bg-dark-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">All Status</option>
              <option value="running">RUNNING</option>
              <option value="idle">IDLE</option>
            </select>
          </div>
        </motion.div>

        {/* Stats */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-6 mb-8"
        >
          <div className="bg-white dark:bg-dark-800 rounded-lg shadow p-6 border border-gray-200 dark:border-dark-700">
            <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Strategies</h3>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">{totalStrategies}</p>
          </div>
          
          <div className="bg-white dark:bg-dark-800 rounded-lg shadow p-6 border border-gray-200 dark:border-dark-700">
            <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">Running</h3>
            <p className="text-2xl font-bold text-green-600 dark:text-green-400">{runningStrategies}</p>
          </div>
          
          <div className="bg-white dark:bg-dark-800 rounded-lg shadow p-6 border border-gray-200 dark:border-dark-700">
            <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">Idle</h3>
            <p className="text-2xl font-bold text-gray-600 dark:text-gray-400">{idleStrategies}</p>
          </div>
          
          <div className="bg-white dark:bg-dark-800 rounded-lg shadow p-6 border border-gray-200 dark:border-dark-700">
            <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Profit</h3>
            <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">${totalProfit.toFixed(2)}</p>
          </div>
          
          <div className="bg-white dark:bg-dark-800 rounded-lg shadow p-6 border border-gray-200 dark:border-dark-700">
            <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">Avg Success Rate</h3>
            <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">{avgSuccessRate.toFixed(1)}%</p>
          </div>
        </motion.div>

        {/* Strategy Grid */}
        {filteredStrategies.length === 0 ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-12"
          >
            <Filter className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
              No strategies found
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Try adjusting your search or filter criteria
            </p>
          </motion.div>
        ) : (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6"
          >
            {filteredStrategies.map((strategy, index) => (
              <motion.div
                key={strategy.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.05 * index }}
                className="w-full"
              >
                <StrategyCard
                  strategy={strategy}
                  onRun={handleRunStrategy}
                  onStop={handleStopStrategy}
                  onViewDetails={handleViewDetails}
                />
              </motion.div>
            ))}
          </motion.div>
        )}
      </div>
    </div>
  );
}