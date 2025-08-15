import { useState, useEffect, useMemo } from 'react';
import { useRouter } from 'next/router';
import { motion } from 'framer-motion';
import { 
  ArrowLeft, 
  Play, 
  Square,
  ExternalLink,
  TrendingUp, 
  Clock, 
  DollarSign,
  Activity,
  Settings,
  Target,
  Zap,
  BarChart3
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';
import { formatCurrency, formatPercentage, getStatusColor, getChainColor, getStrategy, startStrategy, stopStrategy, subscribeToMetricsUpdates } from '../../lib/utils';

const COLORS = ['#10B981', '#EF4444', '#F59E0B', '#3B82F6', '#8B5CF6'];

export default function StrategyDetail() {
  const router = useRouter();
  const { id } = router.query;
  const [strategy, setStrategy] = useState(null);
  const [loading, setLoading] = useState(true);
  const [profitHistory, setProfitHistory] = useState([]);
  const [tradeHistory, setTradeHistory] = useState([]);

  useEffect(() => {
    if (id) {
      const strategyData = getStrategy(id);
      if (strategyData) {
        setStrategy(strategyData);
        generateHistoryData(strategyData);
      }
      setLoading(false);

      const unsubscribe = subscribeToMetricsUpdates(() => {
        const updatedStrategy = getStrategy(id);
        if (updatedStrategy) {
          setStrategy(updatedStrategy);
          generateHistoryData(updatedStrategy);
        }
      });

      return unsubscribe;
    }
  }, [id]);

  const generateHistoryData = (strategyData) => {
    const hours = 24;
    const profitData = [];
    const tradeData = [];
    
    for (let i = 0; i < hours; i++) {
      const hour = new Date();
      hour.setHours(hour.getHours() - (hours - i));
      
      const progress = strategyData.total_profit > 0 ? (i / hours) : 0;
      const hourlyProfit = strategyData.total_profit * progress * (0.8 + Math.random() * 0.4);
      
      profitData.push({
        time: hour.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
        profit: hourlyProfit,
        trades: Math.floor(strategyData.total_trades * progress / 4)
      });

      if (i % 4 === 0) {
        const successful = Math.floor(strategyData.total_trades * (strategyData.success_rate / 100) / 6);
        const failed = Math.floor(strategyData.total_trades / 6) - successful;
        
        tradeData.push({
          period: `${String(i).padStart(2, '0')}:00`,
          successful: successful + Math.floor(Math.random() * 3),
          failed: failed + Math.floor(Math.random() * 2)
        });
      }
    }
    
    setProfitHistory(profitData);
    setTradeHistory(tradeData);
  };

  const handleRunStrategy = () => {
    startStrategy(id);
  };

  const handleStopStrategy = () => {
    stopStrategy(id);
  };

  const pieData = useMemo(() => {
    if (!strategy || strategy.total_trades === 0) {
      return [{ name: 'No Trades Yet', value: 1, color: '#6B7280' }];
    }
    
    const successful = Math.floor(strategy.total_trades * (strategy.success_rate / 100));
    const failed = strategy.total_trades - successful;
    
    return [
      { name: 'Successful Trades', value: successful, color: '#10B981' },
      { name: 'Failed Trades', value: failed, color: '#EF4444' }
    ];
  }, [strategy]);

  const performanceMetrics = useMemo(() => {
    if (!strategy) return [];
    
    const profitPerTrade = strategy.total_trades > 0 ? strategy.total_profit / strategy.total_trades : 0;
    const efficiency = strategy.total_trades > 0 ? (strategy.success_rate * profitPerTrade) / 10 : 0;
    
    return [
      { name: 'Avg Profit', value: profitPerTrade, color: '#10B981' },
      { name: 'Success Rate', value: strategy.success_rate, color: '#3B82F6' },
      { name: 'Trade Volume', value: strategy.total_trades, color: '#F59E0B' },
      { name: 'ROI Score', value: Math.min(100, efficiency), color: '#8B5CF6' }
    ];
  }, [strategy]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-xl text-gray-600 dark:text-gray-400">Loading Strategy Details...</p>
        </div>
      </div>
    );
  }

  if (!strategy) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">Strategy Not Found</h2>
          <button
            onClick={() => router.push('/strategies')}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Back to Strategies
          </button>
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
          <div className="flex items-center space-x-4 mb-6">
            <button
              onClick={() => router.push('/strategies')}
              className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
            >
              <ArrowLeft className="w-6 h-6" />
            </button>
            <div className="flex-1">
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                {strategy.name}
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mt-1">
                {strategy.description}
              </p>
            </div>
            <div className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(strategy.status)}`}>
              {strategy.status}
            </div>
          </div>

          {/* Chains and Actions */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600 dark:text-gray-400">Supported Chains:</span>
              <div className="flex space-x-2">
                {strategy.chains?.map((chain) => (
                  <span
                    key={chain}
                    className={`px-3 py-1 rounded-full text-sm font-medium ${getChainColor(chain)}`}
                  >
                    {chain}
                  </span>
                ))}
              </div>
            </div>
            
            <div className="flex items-center space-x-3">
              {strategy.status !== 'running' ? (
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={handleRunStrategy}
                  className="flex items-center space-x-2 px-6 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition-colors"
                >
                  <Play className="w-4 h-4" />
                  <span>Run Strategy</span>
                </motion.button>
              ) : (
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={handleStopStrategy}
                  className="flex items-center space-x-2 px-6 py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors"
                >
                  <Square className="w-4 h-4" />
                  <span>Stop</span>
                </motion.button>
              )}
              
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => window.open(strategy.spreadsheet, '_blank')}
                className="flex items-center space-x-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
              >
                <ExternalLink className="w-4 h-4" />
                <span>View Live Data</span>
              </motion.button>
            </div>
          </div>
        </motion.div>

        {/* Metrics Cards */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8"
        >
          <div className="bg-white dark:bg-dark-800 rounded-xl shadow-lg border border-gray-200 dark:border-dark-700 p-6">
            <div className="flex items-center space-x-3 mb-4">
              <div className="p-2 bg-blue-100 dark:bg-blue-900/20 rounded-lg">
                <Activity className="w-5 h-5 text-blue-600 dark:text-blue-400" />
              </div>
              <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Trades</h3>
            </div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {strategy.total_trades}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              {strategy.status === 'running' ? 'Live updating' : 'Last session'}
            </p>
          </div>

          <div className="bg-white dark:bg-dark-800 rounded-xl shadow-lg border border-gray-200 dark:border-dark-700 p-6">
            <div className="flex items-center space-x-3 mb-4">
              <div className="p-2 bg-green-100 dark:bg-green-900/20 rounded-lg">
                <DollarSign className="w-5 h-5 text-green-600 dark:text-green-400" />
              </div>
              <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Profit</h3>
            </div>
            <p className="text-2xl font-bold text-green-600 dark:text-green-400">
              {formatCurrency(strategy.total_profit)}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Avg: {formatCurrency(strategy.total_trades > 0 ? strategy.total_profit / strategy.total_trades : 0)}/trade
            </p>
          </div>

          <div className="bg-white dark:bg-dark-800 rounded-xl shadow-lg border border-gray-200 dark:border-dark-700 p-6">
            <div className="flex items-center space-x-3 mb-4">
              <div className="p-2 bg-purple-100 dark:bg-purple-900/20 rounded-lg">
                <Target className="w-5 h-5 text-purple-600 dark:text-purple-400" />
              </div>
              <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">Success Rate</h3>
            </div>
            <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">
              {strategy.success_rate.toFixed(1)}%
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              {Math.floor(strategy.total_trades * (strategy.success_rate / 100))} successful
            </p>
          </div>

          <div className="bg-white dark:bg-dark-800 rounded-xl shadow-lg border border-gray-200 dark:border-dark-700 p-6">
            <div className="flex items-center space-x-3 mb-4">
              <div className="p-2 bg-orange-100 dark:bg-orange-900/20 rounded-lg">
                <Zap className="w-5 h-5 text-orange-600 dark:text-orange-400" />
              </div>
              <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">Status</h3>
            </div>
            <p className="text-2xl font-bold text-orange-600 dark:text-orange-400">
              {strategy.status === 'running' ? 'ACTIVE' : 'IDLE'}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              {strategy.status === 'running' ? 'Generating profits' : 'Ready to start'}
            </p>
          </div>
        </motion.div>

        {/* Charts Row 1 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Profit Chart */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-white dark:bg-dark-800 rounded-xl shadow-lg border border-gray-200 dark:border-dark-700 p-6"
          >
            <div className="flex items-center space-x-3 mb-4">
              <TrendingUp className="w-5 h-5 text-green-600 dark:text-green-400" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Profit Over Time (24h)
              </h3>
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={profitHistory}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="time" stroke="#6B7280" fontSize={12} />
                <YAxis stroke="#6B7280" fontSize={12} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1F2937', 
                    border: 'none', 
                    borderRadius: '8px',
                    color: '#F9FAFB'
                  }} 
                  formatter={(value) => [formatCurrency(value), 'Profit']}
                />
                <Line 
                  type="monotone" 
                  dataKey="profit" 
                  stroke="#10B981" 
                  strokeWidth={3}
                  dot={{ fill: '#10B981', strokeWidth: 2, r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </motion.div>

          {/* Trade Success Pie Chart */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-white dark:bg-dark-800 rounded-xl shadow-lg border border-gray-200 dark:border-dark-700 p-6"
          >
            <div className="flex items-center space-x-3 mb-4">
              <BarChart3 className="w-5 h-5 text-blue-600 dark:text-blue-400" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Trade Success Distribution
              </h3>
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={120}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1F2937', 
                    border: 'none', 
                    borderRadius: '8px',
                    color: '#F9FAFB'
                  }} 
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="flex justify-center space-x-6 mt-4">
              {pieData.map((entry, index) => (
                <div key={index} className="flex items-center space-x-2">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: entry.color }}></div>
                  <span className="text-sm text-gray-600 dark:text-gray-400">{entry.name}: {entry.value}</span>
                </div>
              ))}
            </div>
          </motion.div>
        </div>

        {/* Charts Row 2 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Trades Bar Chart */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4 }}
            className="bg-white dark:bg-dark-800 rounded-xl shadow-lg border border-gray-200 dark:border-dark-700 p-6"
          >
            <div className="flex items-center space-x-3 mb-4">
              <Activity className="w-5 h-5 text-purple-600 dark:text-purple-400" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Trade Activity (4h intervals)
              </h3>
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={tradeHistory}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="period" stroke="#6B7280" fontSize={12} />
                <YAxis stroke="#6B7280" fontSize={12} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1F2937', 
                    border: 'none', 
                    borderRadius: '8px',
                    color: '#F9FAFB'
                  }} 
                />
                <Bar dataKey="successful" fill="#10B981" radius={[4, 4, 0, 0]} />
                <Bar dataKey="failed" fill="#EF4444" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
            <div className="flex justify-center space-x-6 mt-4">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 rounded-full bg-green-500"></div>
                <span className="text-sm text-gray-600 dark:text-gray-400">Successful</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 rounded-full bg-red-500"></div>
                <span className="text-sm text-gray-600 dark:text-gray-400">Failed</span>
              </div>
            </div>
          </motion.div>

          {/* Performance Metrics */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.5 }}
            className="bg-white dark:bg-dark-800 rounded-xl shadow-lg border border-gray-200 dark:border-dark-700 p-6"
          >
            <div className="flex items-center space-x-3 mb-4">
              <Target className="w-5 h-5 text-orange-600 dark:text-orange-400" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Performance Metrics
              </h3>
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={performanceMetrics} layout="vertical" margin={{ left: 20, right: 20, top: 20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis type="number" stroke="#6B7280" fontSize={12} domain={[0, 'dataMax + 10']} />
                <YAxis dataKey="name" type="category" stroke="#6B7280" fontSize={12} width={100} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1F2937', 
                    border: 'none', 
                    borderRadius: '8px',
                    color: '#F9FAFB'
                  }} 
                  formatter={(value, name) => [
                    name === 'Avg Profit' ? formatCurrency(value) : 
                    name === 'Success Rate' ? `${value.toFixed(1)}%` : 
                    name === 'ROI Score' ? `${value.toFixed(1)}%` :
                    value.toFixed(0), 
                    name
                  ]}
                />
                <Bar 
                  dataKey="value" 
                  radius={[0, 4, 4, 0]}
                >
                  {performanceMetrics.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </motion.div>
        </div>

        {/* Strategy Configuration */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="bg-white dark:bg-dark-800 rounded-xl shadow-lg border border-gray-200 dark:border-dark-700 p-6"
        >
          <div className="flex items-center space-x-3 mb-6">
            <Settings className="w-6 h-6 text-gray-600 dark:text-gray-400" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Strategy Configuration & Details
            </h3>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div className="bg-gray-50 dark:bg-dark-700 rounded-lg p-4">
              <label className="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
                Strategy Type
              </label>
              <p className="text-gray-900 dark:text-white font-medium">
                {strategy.type.replace('_', ' ').toUpperCase()}
              </p>
            </div>
            
            <div className="bg-gray-50 dark:bg-dark-700 rounded-lg p-4">
              <label className="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
                Total Trades
              </label>
              <p className="text-gray-900 dark:text-white font-medium">
                {strategy.total_trades}
              </p>
            </div>
            
            <div className="bg-gray-50 dark:bg-dark-700 rounded-lg p-4">
              <label className="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
                Success Rate
              </label>
              <p className="text-gray-900 dark:text-white font-medium">
                {formatPercentage(strategy.success_rate / 100)}
              </p>
            </div>
            
            <div className="bg-gray-50 dark:bg-dark-700 rounded-lg p-4">
              <label className="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
                Total Profit
              </label>
              <p className="text-green-600 dark:text-green-400 font-medium">
                {formatCurrency(strategy.total_profit)}
              </p>
            </div>
            
            <div className="bg-gray-50 dark:bg-dark-700 rounded-lg p-4">
              <label className="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
                Profit per Trade
              </label>
              <p className="text-blue-600 dark:text-blue-400 font-medium">
                {formatCurrency(strategy.total_trades > 0 ? strategy.total_profit / strategy.total_trades : 0)}
              </p>
            </div>
            
            <div className="bg-gray-50 dark:bg-dark-700 rounded-lg p-4">
              <label className="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
                Current Status
              </label>
              <p className={`font-medium ${strategy.status === 'running' ? 'text-green-600 dark:text-green-400' : 'text-gray-600 dark:text-gray-400'}`}>
                {strategy.status === 'running' ? 'RUNNING' : 'IDLE'}
              </p>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}