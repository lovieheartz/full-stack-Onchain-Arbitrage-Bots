// Simple global state management
let globalState = {
  runningStrategies: new Map(),
  listeners: []
};

export const setStrategyRunning = (strategyName, isRunning, startTime = null) => {
  if (isRunning) {
    globalState.runningStrategies.set(strategyName, {
      isRunning: true,
      startTime: startTime || new Date(),
      runningProfit: 0,
      runningTrades: 0,
      runningSuccessRate: 0.85
    });
  } else {
    globalState.runningStrategies.delete(strategyName);
  }
  
  // Notify listeners
  globalState.listeners.forEach(listener => listener());
};

export const getStrategyRunningState = (strategyName) => {
  return globalState.runningStrategies.get(strategyName) || null;
};

export const getAllRunningStrategies = () => {
  return Array.from(globalState.runningStrategies.values());
};

export const subscribeToStateChanges = (callback) => {
  globalState.listeners.push(callback);
  
  return () => {
    const index = globalState.listeners.indexOf(callback);
    if (index > -1) {
      globalState.listeners.splice(index, 1);
    }
  };
};

export const updateRunningMetrics = (strategyName, profit, trades, successRate) => {
  const state = globalState.runningStrategies.get(strategyName);
  if (state) {
    state.runningProfit = profit;
    state.runningTrades = trades;
    state.runningSuccessRate = successRate;
    
    // Notify listeners
    globalState.listeners.forEach(listener => listener());
  }
};