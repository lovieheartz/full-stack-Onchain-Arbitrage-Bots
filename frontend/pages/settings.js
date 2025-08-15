import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Save, 
  Key, 
  Database, 
  Globe, 
  Shield,
  Eye,
  EyeOff,
  CheckCircle,
  AlertCircle
} from 'lucide-react';

export default function Settings() {
  const [settings, setSettings] = useState({
    googleSheetsId: '',
    ethereumRpc: '',
    arbitrumRpc: '',
    polygonRpc: '',
    baseRpc: '',
    solanaRpc: '',
    etherscanApiKey: '',
    polygonscanApiKey: '',
    arbiscanApiKey: '',
    paperTradingMode: true,
    defaultTradeAmount: 1000,
    minProfitThreshold: 0.01,
    maxGasPrice: 100,
  });

  const [showKeys, setShowKeys] = useState({});
  const [saved, setSaved] = useState(false);
  const [errors, setErrors] = useState({});

  useEffect(() => {
    // Load settings from localStorage
    const savedSettings = localStorage.getItem('arbitrageSettings');
    if (savedSettings) {
      setSettings({ ...settings, ...JSON.parse(savedSettings) });
    }
  }, []);

  const handleInputChange = (key, value) => {
    setSettings(prev => ({ ...prev, [key]: value }));
    // Clear error when user starts typing
    if (errors[key]) {
      setErrors(prev => ({ ...prev, [key]: null }));
    }
  };

  const toggleShowKey = (key) => {
    setShowKeys(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const validateSettings = () => {
    const newErrors = {};

    // Validate Google Sheets ID
    if (settings.googleSheetsId && !settings.googleSheetsId.match(/^[a-zA-Z0-9-_]{44}$/)) {
      newErrors.googleSheetsId = 'Invalid Google Sheets ID format';
    }

    // Validate RPC URLs
    const rpcFields = ['ethereumRpc', 'arbitrumRpc', 'polygonRpc', 'baseRpc', 'solanaRpc'];
    rpcFields.forEach(field => {
      if (settings[field] && !settings[field].startsWith('http')) {
        newErrors[field] = 'RPC URL must start with http:// or https://';
      }
    });

    // Validate numeric fields
    if (settings.defaultTradeAmount <= 0) {
      newErrors.defaultTradeAmount = 'Trade amount must be greater than 0';
    }

    if (settings.minProfitThreshold < 0) {
      newErrors.minProfitThreshold = 'Profit threshold cannot be negative';
    }

    if (settings.maxGasPrice <= 0) {
      newErrors.maxGasPrice = 'Max gas price must be greater than 0';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSave = () => {
    if (validateSettings()) {
      localStorage.setItem('arbitrageSettings', JSON.stringify(settings));
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    }
  };

  const handleReset = () => {
    const defaultSettings = {
      googleSheetsId: '',
      ethereumRpc: '',
      arbitrumRpc: '',
      polygonRpc: '',
      baseRpc: '',
      solanaRpc: '',
      etherscanApiKey: '',
      polygonscanApiKey: '',
      arbiscanApiKey: '',
      paperTradingMode: true,
      defaultTradeAmount: 1000,
      minProfitThreshold: 0.01,
      maxGasPrice: 100,
    };
    setSettings(defaultSettings);
    localStorage.removeItem('arbitrageSettings');
    setErrors({});
  };

  const renderInput = (key, label, type = 'text', placeholder = '', isSecret = false) => {
    const showPassword = showKeys[key];
    const inputType = isSecret ? (showPassword ? 'text' : 'password') : type;

    return (
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          {label}
        </label>
        <div className="relative">
          <input
            type={inputType}
            value={settings[key]}
            onChange={(e) => handleInputChange(key, e.target.value)}
            placeholder={placeholder}
            className={`w-full px-4 py-2 border rounded-lg bg-white dark:bg-dark-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
              errors[key] ? 'border-red-500' : 'border-gray-300 dark:border-dark-600'
            }`}
          />
          {isSecret && (
            <button
              type="button"
              onClick={() => toggleShowKey(key)}
              className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
            </button>
          )}
        </div>
        {errors[key] && (
          <p className="mt-1 text-sm text-red-600 dark:text-red-400 flex items-center">
            <AlertCircle className="w-4 h-4 mr-1" />
            {errors[key]}
          </p>
        )}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-dark-900 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Settings</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Configure your API keys, RPC endpoints, and trading parameters
          </p>
        </motion.div>

        {/* Success Message */}
        {saved && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg flex items-center"
          >
            <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400 mr-2" />
            <span className="text-green-800 dark:text-green-200">Settings saved successfully!</span>
          </motion.div>
        )}

        <div className="space-y-8">
          {/* Google Sheets Configuration */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-white dark:bg-dark-800 rounded-xl shadow-lg border border-gray-200 dark:border-dark-700 p-6"
          >
            <div className="flex items-center space-x-3 mb-6">
              <Database className="w-6 h-6 text-blue-600 dark:text-blue-400" />
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                Google Sheets Integration
              </h2>
            </div>
            
            <div className="space-y-4">
              {renderInput(
                'googleSheetsId',
                'Google Sheets ID',
                'text',
                'Enter your Google Sheets ID (44 characters)'
              )}
              <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                <p className="text-blue-800 dark:text-blue-200 text-sm">
                  <strong>How to find your Google Sheets ID:</strong><br />
                  1. Open your Google Sheet<br />
                  2. Copy the ID from the URL: https://docs.google.com/spreadsheets/d/<strong>[SHEET_ID]</strong>/edit<br />
                  3. Make sure the sheet is shared with your service account email
                </p>
              </div>
            </div>
          </motion.div>

          {/* RPC Endpoints */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-white dark:bg-dark-800 rounded-xl shadow-lg border border-gray-200 dark:border-dark-700 p-6"
          >
            <div className="flex items-center space-x-3 mb-6">
              <Globe className="w-6 h-6 text-green-600 dark:text-green-400" />
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                RPC Endpoints
              </h2>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {renderInput(
                'ethereumRpc',
                'Ethereum RPC',
                'url',
                'https://eth-mainnet.g.alchemy.com/v2/YOUR_API_KEY'
              )}
              {renderInput(
                'arbitrumRpc',
                'Arbitrum RPC',
                'url',
                'https://arb-mainnet.g.alchemy.com/v2/YOUR_API_KEY'
              )}
              {renderInput(
                'polygonRpc',
                'Polygon RPC',
                'url',
                'https://polygon-mainnet.g.alchemy.com/v2/YOUR_API_KEY'
              )}
              {renderInput(
                'baseRpc',
                'Base RPC',
                'url',
                'https://base-mainnet.g.alchemy.com/v2/YOUR_API_KEY'
              )}
              {renderInput(
                'solanaRpc',
                'Solana RPC',
                'url',
                'https://api.mainnet-beta.solana.com'
              )}
            </div>
          </motion.div>

          {/* API Keys */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-white dark:bg-dark-800 rounded-xl shadow-lg border border-gray-200 dark:border-dark-700 p-6"
          >
            <div className="flex items-center space-x-3 mb-6">
              <Key className="w-6 h-6 text-purple-600 dark:text-purple-400" />
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                API Keys
              </h2>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {renderInput(
                'etherscanApiKey',
                'Etherscan API Key',
                'text',
                'Enter your Etherscan API key',
                true
              )}
              {renderInput(
                'polygonscanApiKey',
                'Polygonscan API Key',
                'text',
                'Enter your Polygonscan API key',
                true
              )}
              {renderInput(
                'arbiscanApiKey',
                'Arbiscan API Key',
                'text',
                'Enter your Arbiscan API key',
                true
              )}
            </div>
          </motion.div>

          {/* Trading Configuration */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="bg-white dark:bg-dark-800 rounded-xl shadow-lg border border-gray-200 dark:border-dark-700 p-6"
          >
            <div className="flex items-center space-x-3 mb-6">
              <Shield className="w-6 h-6 text-orange-600 dark:text-orange-400" />
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                Trading Configuration
              </h2>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    checked={settings.paperTradingMode}
                    onChange={(e) => handleInputChange('paperTradingMode', e.target.checked)}
                    className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
                  />
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Paper Trading Mode
                  </span>
                </label>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Enable to simulate trades without real money
                </p>
              </div>
              
              {renderInput(
                'defaultTradeAmount',
                'Default Trade Amount ($)',
                'number',
                '1000'
              )}
              
              {renderInput(
                'minProfitThreshold',
                'Min Profit Threshold ($)',
                'number',
                '0.01'
              )}
              
              {renderInput(
                'maxGasPrice',
                'Max Gas Price (Gwei)',
                'number',
                '100'
              )}
            </div>
          </motion.div>

          {/* Action Buttons */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="flex justify-between"
          >
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleReset}
              className="px-6 py-3 border border-gray-300 dark:border-dark-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-dark-700 rounded-lg font-medium transition-colors"
            >
              Reset to Defaults
            </motion.button>
            
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleSave}
              className="flex items-center space-x-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
            >
              <Save className="w-5 h-5" />
              <span>Save Settings</span>
            </motion.button>
          </motion.div>
        </div>
      </div>
    </div>
  );
}