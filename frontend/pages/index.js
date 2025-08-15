import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import dynamic from 'next/dynamic';
import { 
  TrendingUp, 
  Activity, 
  DollarSign, 
  Zap,
  ArrowUpRight,
  ArrowDownRight
} from 'lucide-react';
import { strategyAPI, healthAPI } from '../lib/api';
import { formatCurrency, formatPercentage, getAllStrategies, getTotalProfit, getAverageSuccessRate, subscribeToMetricsUpdates } from '../lib/utils';

// Dynamically import ThreeScene to avoid SSR issues
const ThreeScene = dynamic(() => import('../components/ThreeScene'), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-blue-50 to-purple-50 dark:from-dark-800 dark:to-dark-900">
      <div className="text-center">
        <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
        <p className="text-gray-600 dark:text-gray-400">Loading 3D Visualization...</p>
      </div>
    </div>
  )
});

export default function Home() {
  const [strategies, setStrategies] = useState([]);
  const [stats, setStats] = useState({
    totalStrategies: 0,
    activeStrategies: 0,
    totalProfit: 0,
    successRate: 0
  });
  const [loading, setLoading] = useState(true);
  const [activeStrategy, setActiveStrategy] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);
  
  useEffect(() => {
    // Subscribe to real-time metrics updates
    const updateStats = () => {
      const strategies = getAllStrategies();
      const activeStrategies = strategies.filter(s => s.status === 'running').length;
      
      setStats(prev => ({
        ...prev,
        totalProfit: getTotalProfit(),
        successRate: getAverageSuccessRate(),
        activeStrategies
      }));
    };
    
    const unsubscribe = subscribeToMetricsUpdates(updateStats);
    return unsubscribe;
  }, []);

  const fetchData = async () => {
    try {
      const strategiesData = getAllStrategies();
      setStrategies(strategiesData);

      setStats({
        totalStrategies: strategiesData.length,
        activeStrategies: strategiesData.filter(s => s.status === 'running').length,
        totalProfit: getTotalProfit(),
        successRate: getAverageSuccessRate()
      });

      // Set a random active strategy for 3D visualization
      if (strategiesData.length > 0) {
        setActiveStrategy(strategiesData[Math.floor(Math.random() * strategiesData.length)]);
      }
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  const statCards = [
    {
      title: 'Total Strategies',
      value: stats.totalStrategies,
      icon: Activity,
      color: 'text-blue-600 dark:text-blue-400',
      bgColor: 'bg-blue-100 dark:bg-blue-900/20',
      change: '+2',
      changeType: 'positive'
    },
    {
      title: 'Active Strategies',
      value: stats.activeStrategies,
      icon: Zap,
      color: 'text-green-600 dark:text-green-400',
      bgColor: 'bg-green-100 dark:bg-green-900/20',
      change: `${stats.activeStrategies}`,
      changeType: 'neutral'
    },
    {
      title: 'Total Profit',
      value: formatCurrency(stats.totalProfit),
      icon: DollarSign,
      color: 'text-purple-600 dark:text-purple-400',
      bgColor: 'bg-purple-100 dark:bg-purple-900/20',
      change: '+12.5%',
      changeType: 'positive'
    },
    {
      title: 'Success Rate',
      value: formatPercentage(stats.successRate / 100),
      icon: TrendingUp,
      color: 'text-orange-600 dark:text-orange-400',
      bgColor: 'bg-orange-100 dark:bg-orange-900/20',
      change: '+2.1%',
      changeType: 'positive'
    }
  ];

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-xl text-gray-600 dark:text-gray-400">Loading Dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* 3D Background */}
      <div className="absolute inset-0 z-0">
        <ThreeScene activeStrategy={activeStrategy} />
      </div>
      
      {/* Content Overlay */}
      <div className="relative z-10 min-h-screen">
      {/* Hero Section */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-blue-600/5 to-purple-600/5"></div>
        
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="flex flex-col items-center text-center">
            {/* Left Content */}
            <motion.div
              initial={{ opacity: 0, x: -50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8 }}
            >
              <h1 className="text-4xl lg:text-6xl font-bold text-white dark:text-white mb-6 drop-shadow-2xl">
                On-Chain
                <span className="bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">
                  {' '}Arbitrage
                </span>
                <br />
                Dashboard
              </h1>
              <p className="text-xl text-gray-200 dark:text-gray-200 mb-6 drop-shadow-lg max-w-4xl">
                Advanced algorithmic trading platform leveraging blockchain arbitrage opportunities across 
                multiple networks. Our sophisticated bots execute high-frequency trades, exploiting price 
                differentials between decentralized exchanges to generate consistent profits.
              </p>
              {/* Feature bullets */}
              <div className="max-w-4xl mx-auto mb-8">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-lg text-gray-300">
                  <div className="flex items-center justify-center gap-4 p-4 rounded-xl bg-gradient-to-r from-blue-500/10 to-blue-600/10 border border-blue-500/20 backdrop-blur-sm hover:from-blue-500/20 hover:to-blue-600/20 transition-all duration-300">
                    <div className="relative">
                      <div className="w-3 h-3 bg-blue-400 rounded-full animate-pulse"></div>
                      <div className="absolute inset-0 w-3 h-3 bg-blue-400 rounded-full animate-ping opacity-30"></div>
                    </div>
                    <span className="font-medium drop-shadow-lg">Real-time monitoring</span>
                  </div>
                  <div className="flex items-center justify-center gap-4 p-4 rounded-xl bg-gradient-to-r from-green-500/10 to-green-600/10 border border-green-500/20 backdrop-blur-sm hover:from-green-500/20 hover:to-green-600/20 transition-all duration-300">
                    <div className="relative">
                      <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
                      <div className="absolute inset-0 w-3 h-3 bg-green-400 rounded-full animate-ping opacity-30"></div>
                    </div>
                    <span className="font-medium drop-shadow-lg">Cross-chain execution</span>
                  </div>
                  <div className="flex items-center justify-center gap-4 p-4 rounded-xl bg-gradient-to-r from-purple-500/10 to-purple-600/10 border border-purple-500/20 backdrop-blur-sm hover:from-purple-500/20 hover:to-purple-600/20 transition-all duration-300">
                    <div className="relative">
                      <div className="w-3 h-3 bg-purple-400 rounded-full animate-pulse"></div>
                      <div className="absolute inset-0 w-3 h-3 bg-purple-400 rounded-full animate-ping opacity-30"></div>
                    </div>
                    <span className="font-medium drop-shadow-lg">Automated profit optimization</span>
                  </div>
                  <div className="flex items-center justify-center gap-4 p-4 rounded-xl bg-gradient-to-r from-yellow-500/10 to-yellow-600/10 border border-yellow-500/20 backdrop-blur-sm hover:from-yellow-500/20 hover:to-yellow-600/20 transition-all duration-300">
                    <div className="relative">
                      <div className="w-3 h-3 bg-yellow-400 rounded-full animate-pulse"></div>
                      <div className="absolute inset-0 w-3 h-3 bg-yellow-400 rounded-full animate-ping opacity-30"></div>
                    </div>
                    <span className="font-medium drop-shadow-lg">Risk management</span>
                  </div>
                </div>
              </div>

            </motion.div>


          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4 }}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
          >
            {statCards.map((stat, index) => {
              const Icon = stat.icon;
              return (
                <motion.div
                  key={stat.title}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: 0.1 * index }}
                  whileHover={{ y: -8, scale: 1.03, boxShadow: "0 0 40px rgba(6, 182, 212, 0.3)" }}
                  className="bg-slate-900/60 backdrop-blur-xl rounded-2xl shadow-2xl border border-cyan-500/20 p-8 hover:bg-slate-900/80 hover:border-cyan-400/40 transition-all"
                >
                  <div className="flex items-center justify-between mb-4">
                    <div className={`p-3 rounded-lg ${stat.bgColor}`}>
                      <Icon className={`w-6 h-6 ${stat.color}`} />
                    </div>
                    <div className={`flex items-center space-x-1 text-sm ${
                      stat.changeType === 'positive' ? 'text-green-600 dark:text-green-400' : 
                      stat.changeType === 'negative' ? 'text-red-600 dark:text-red-400' : 
                      'text-gray-600 dark:text-gray-400'
                    }`}>
                      {stat.changeType === 'positive' && <ArrowUpRight className="w-4 h-4" />}
                      {stat.changeType === 'negative' && <ArrowDownRight className="w-4 h-4" />}
                      <span>{stat.change}</span>
                    </div>
                  </div>
                  <h3 className="text-2xl font-bold text-white mb-1 drop-shadow-lg">
                    {stat.value}
                  </h3>
                  <p className="text-gray-300">
                    {stat.title}
                  </p>
                </motion.div>
              );
            })}
          </motion.div>
        </div>
      </section>

      {/* Recent Activity */}
      <section className="py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.6 }}
          >
            <h2 className="text-3xl font-bold text-white mb-8 drop-shadow-2xl">
              Strategy Overview
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {strategies.map((strategy, index) => (
                <motion.div
                  key={strategy.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: 0.1 * index }}
                  whileHover={{ y: -5 }}
                  className="bg-white/10 dark:bg-black/40 backdrop-blur-md rounded-xl shadow-2xl border border-white/30 dark:border-white/20 p-6 hover:bg-white/20 dark:hover:bg-black/50 transition-all"
                >
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-white dark:text-white drop-shadow-lg">
                      {strategy.name}
                    </h3>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      strategy.status === 'running' ? 'text-green-600 bg-green-100 dark:bg-green-900/20' :
                      'text-gray-600 bg-gray-100 dark:bg-gray-800'
                    }`}>
                      {strategy.status}
                    </span>
                  </div>
                  <p className="text-gray-200 dark:text-gray-300 text-sm mb-4">
                    {strategy.description}
                  </p>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-200 dark:text-gray-300">Profit:</span>
                    <span className="text-green-400 dark:text-green-400 font-medium drop-shadow-lg">
                      {formatCurrency(strategy.total_profit || 0)}
                    </span>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </div>
      </section>
      </div>
    </div>
  );
}