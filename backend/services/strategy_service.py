import os
import asyncio
import subprocess
import sys
import threading
import time
import random
from typing import List, Dict, Any
from datetime import datetime
from models.strategy import StrategyInfo, StrategyMetrics, StrategyExecution

class StrategyService:
    def __init__(self):
        self.strategies_dir = os.path.join(os.path.dirname(__file__), "..", "strategies")
        self.running_strategies = {}
        self.strategy_data = {}  # Store strategy metrics locally
        
    def get_all_strategies(self) -> List[StrategyInfo]:
        """Get information about all available strategies"""
        strategies = []
        
        strategy_configs = {
            "cross-chain-arbitrage": {
                "file": "cross_exchange_bot.py",
                "name": "Cross-Chain Arbitrage",
                "description": "Arbitrage between different DEXs across multiple chains",
                "type": "cross_chain",
                "chains": ["ethereum", "arbitrum", "polygon"]
            },
            "flashloan-arbitrage": {
                "file": "flashloan_arbitrage_bot_fixed.py",
                "name": "Flashloan Arbitrage",
                "description": "Capital-efficient arbitrage using flashloans",
                "type": "flashloan",
                "chains": ["ethereum", "arbitrum", "polygon", "base"]
            },
            "latency-arbitrage": {
                "file": "l2_latency_bot.py",
                "name": "Latency Arbitrage",
                "description": "Exploit latency differences between L2 networks",
                "type": "latency",
                "chains": ["arbitrum", "polygon", "optimism"]
            },
            "dex-to-dex-arbitrage": {
                "file": "multi_pair_arbitrage_bot.py",
                "name": "DEX-to-DEX Arbitrage",
                "description": "Arbitrage across multiple trading pairs simultaneously",
                "type": "multi_pair",
                "chains": ["ethereum", "arbitrum", "polygon", "solana"]
            },
            "sandwich-arbitrage": {
                "file": "Sandwich_Arbitrage.py",
                "name": "Sandwich Arbitrage",
                "description": "MEV sandwich attacks on large transactions",
                "type": "mev",
                "chains": ["ethereum"]
            },
            "stablecoin-arbitrage": {
                "file": "StableCoin_Live_BOT.py",
                "name": "StableCoin Arbitrage",
                "description": "Low-risk arbitrage between stablecoins",
                "type": "stablecoin",
                "chains": ["polygon", "arbitrum", "base"]
            },
            "triangular-arbitrage": {
                "file": "triangular_arbitrage_bot.py",
                "name": "Triangular Arbitrage",
                "description": "Three-token cycle arbitrage opportunities",
                "type": "triangular",
                "chains": ["ethereum", "solana"]
            }
        }
        
        for strategy_id, config in strategy_configs.items():
            file_path = os.path.join(self.strategies_dir, config["file"])
            
            # Get stored metrics
            metrics = self.strategy_data.get(strategy_id, {
                'total_trades': random.randint(15, 45),
                'total_profit': round(random.uniform(50, 200), 2),
                'success_rate': round(random.uniform(75, 95), 1)
            })
            
            current_status = "running" if strategy_id in self.running_strategies else "idle"
            
            strategies.append(StrategyInfo(
                id=strategy_id,
                name=config["name"],
                description=config["description"],
                type=config["type"],
                chains=config["chains"],
                status=current_status,
                file_path=file_path,
                total_trades=metrics['total_trades'],
                total_profit=metrics['total_profit'],
                success_rate=metrics['success_rate']
            ))
        
        return strategies
    
    def get_strategy_by_id(self, strategy_id: str) -> StrategyInfo:
        """Get specific strategy information"""
        strategies = self.get_all_strategies()
        for strategy in strategies:
            if strategy.id == strategy_id:
                return strategy
        return None
    
    def get_strategy_metrics(self, strategy_id: str) -> StrategyMetrics:
        """Get performance metrics for a strategy"""
        metrics = self.strategy_data.get(strategy_id, {
            'total_trades': random.randint(15, 45),
            'total_profit': round(random.uniform(50, 200), 2)
        })
        
        return StrategyMetrics(
            trades_today=metrics['total_trades'],
            profit_today=metrics['total_profit'],
            avg_profit_per_trade=round(metrics['total_profit'] / max(metrics['total_trades'], 1), 2),
            execution_time_avg=2.3,
            gas_cost_total=metrics['total_trades'] * 3.5
        )
    
    async def run_strategy(self, strategy_id: str, duration_minutes: int = 5, 
                          trade_amount: float = 1000.0, paper_trading: bool = True) -> StrategyExecution:
        """Execute a strategy"""
        strategy = self.get_strategy_by_id(strategy_id)
        if not strategy:
            return StrategyExecution(
                strategy_id=strategy_id,
                status="error",
                message="Strategy not found",
                execution_time=0.0,
                trades_executed=0,
                profit_generated=0.0
            )
        
        if strategy_id in self.running_strategies:
            return StrategyExecution(
                strategy_id=strategy_id,
                status="error",
                message="Strategy is already running",
                execution_time=0.0,
                trades_executed=0,
                profit_generated=0.0
            )
        
        try:
            # Mark strategy as running
            self.running_strategies[strategy_id] = {
                'status': 'running',
                'start_time': datetime.now(),
                'duration_minutes': duration_minutes,
                'trade_amount': trade_amount,
                'paper_trading': paper_trading
            }
            
            # Simulate strategy execution
            await self._simulate_strategy_execution(strategy_id, duration_minutes, trade_amount)
            
            return StrategyExecution(
                strategy_id=strategy_id,
                status="started",
                message=f"Strategy started successfully. Running for {duration_minutes} minutes.",
                execution_time=0.0,
                trades_executed=0,
                profit_generated=0.0
            )
            
        except Exception as e:
            if strategy_id in self.running_strategies:
                del self.running_strategies[strategy_id]
            return StrategyExecution(
                strategy_id=strategy_id,
                status="error",
                message=f"Failed to start strategy: {str(e)}",
                execution_time=0.0,
                trades_executed=0,
                profit_generated=0.0
            )
    
    async def stop_strategy(self, strategy_id: str) -> Dict[str, Any]:
        """Stop a running strategy"""
        if strategy_id not in self.running_strategies:
            return {
                'status': 'error',
                'message': 'Strategy is not running'
            }
        
        try:
            del self.running_strategies[strategy_id]
            
            return {
                'status': 'stopped',
                'message': 'Strategy stopped successfully'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Failed to stop strategy: {str(e)}'
            }
    
    def get_strategy_status(self, strategy_id: str) -> Dict[str, Any]:
        """Get current status of a strategy"""
        if strategy_id in self.running_strategies:
            strategy_info = self.running_strategies[strategy_id]
            runtime = (datetime.now() - strategy_info['start_time']).total_seconds()
            return {
                'strategy_id': strategy_id,
                'status': 'running',
                'is_running': True,
                'runtime_seconds': runtime,
                'duration_minutes': strategy_info['duration_minutes'],
                'remaining_seconds': max(0, strategy_info['duration_minutes'] * 60 - runtime)
            }
        else:
            return {
                'strategy_id': strategy_id,
                'status': 'idle',
                'is_running': False,
                'runtime_seconds': 0,
                'duration_minutes': 0,
                'remaining_seconds': 0
            }
    
    async def _simulate_strategy_execution(self, strategy_id: str, duration_minutes: int, trade_amount: float):
        """Simulate strategy execution and update local data"""
        def run_simulation():
            time.sleep(duration_minutes * 60)  # Run for specified duration
            
            # Generate new trades and profit
            new_trades = random.randint(1, max(1, duration_minutes // 2))
            new_profit = round(random.uniform(5, 25) * new_trades, 2)
            
            # Update strategy data
            if strategy_id not in self.strategy_data:
                self.strategy_data[strategy_id] = {
                    'total_trades': 0,
                    'total_profit': 0.0,
                    'success_rate': 85.0
                }
            
            self.strategy_data[strategy_id]['total_trades'] += new_trades
            self.strategy_data[strategy_id]['total_profit'] += new_profit
            
            # Remove from running strategies
            if strategy_id in self.running_strategies:
                del self.running_strategies[strategy_id]
        
        # Run simulation in background thread
        thread = threading.Thread(target=run_simulation, daemon=True)
        thread.start()
    def execute_python_file(self, python_file: str):
        """Execute a Python strategy file"""
        try:
            file_path = os.path.join(self.strategies_dir, python_file)
            if os.path.exists(file_path):
                print(f"🐍 Executing Python file: {python_file}")
                print(f"📁 Full path: {file_path}")
                process = subprocess.Popen(
                    [sys.executable, python_file], 
                    cwd=self.strategies_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                print(f"✅ Process started with PID: {process.pid}")
            else:
                print(f"❌ Python file not found: {file_path}")
        except Exception as e:
            print(f"❌ Error executing Python file {python_file}: {str(e)}")
    
    def get_spreadsheet_link(self, strategy_id: str) -> str:
        """Get Google Sheets link for a strategy"""
        links = {
            "cross-chain-arbitrage": "https://docs.google.com/spreadsheets/d/1TcW2S9jnoIRSxyb-vZYJyqP2xVG-wHZhQkQWmVkxcuw/edit?gid=392614953#gid=392614953",
            "flashloan-arbitrage": "https://docs.google.com/spreadsheets/d/1qInbTXpO8kfxhJ0k6mc_rmf6-qN7mUGABM6r436212g/edit?gid=1210480912#gid=1210480912",
            "latency-arbitrage": "https://docs.google.com/spreadsheets/d/1fZ_aMLvZI7HFfM-7k1xscxl64NImlnwNDJQvhgLmY_8/edit?gid=1618823639#gid=1618823639",
            "dex-to-dex-arbitrage": "https://docs.google.com/spreadsheets/d/1MLkSz43NI7R_-GYkhDvx7fg07cS6A_jF2KJutWs5sV4/edit?gid=584715960#gid=584715960",
            "sandwich-arbitrage": "https://docs.google.com/spreadsheets/d/1dXN3bGNrWHldLGrxuwr5vUS68-jqG2JHauP1kHOxFE0/edit?gid=1328963250#gid=1328963250",
            "stablecoin-arbitrage": "https://docs.google.com/spreadsheets/d/1R7Qa7nLPykDKhEQQF0cypHIp2K90ZtO4CnkijxHBL3s/edit?gid=1334922412#gid=1334922412",
            "triangular-arbitrage": "https://docs.google.com/spreadsheets/d/1KLWtnqwM4AKPyOuEDuQoOZ1rZJGfQZAt4MF-JdgaPiM/edit?gid=954866961#gid=954866961"
        }
        return links.get(strategy_id, "https://docs.google.com/spreadsheets")