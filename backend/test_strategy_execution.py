#!/usr/bin/env python3

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.strategy_service import StrategyService

async def test_strategy_execution():
    """Test strategy execution functionality"""
    
    print("Testing Strategy Execution...")
    
    strategy_service = StrategyService()
    
    # Test getting all strategies
    print("\n1. Getting all strategies:")
    strategies = strategy_service.get_all_strategies()
    for strategy in strategies:
        print(f"   - {strategy.name} (ID: {strategy.id}) - Trades: {strategy.total_trades}")
    
    if not strategies:
        print("   No strategies found!")
        return
    
    # Test running a strategy
    test_strategy = strategies[0]  # Use first strategy
    print(f"\n2. Running strategy: {test_strategy.name}")
    
    result = await strategy_service.run_strategy(
        strategy_id=test_strategy.id,
        duration_minutes=5,
        trade_amount=1000.0,
        paper_trading=True
    )
    
    print(f"   Status: {result.status}")
    print(f"   Message: {result.message}")
    print(f"   Trades Executed: {result.trades_executed}")
    print(f"   Profit Generated: ${result.profit_generated:.2f}")
    print(f"   Execution Time: {result.execution_time:.2f}s")
    
    # Test getting updated metrics
    print(f"\n3. Getting updated metrics for {test_strategy.name}:")
    metrics = strategy_service.get_strategy_metrics(test_strategy.id)
    print(f"   Trades Today: {metrics.trades_today}")
    print(f"   Profit Today: ${metrics.profit_today:.2f}")
    print(f"   Avg Profit per Trade: ${metrics.avg_profit_per_trade:.2f}")
    print(f"   Gas Cost Total: ${metrics.gas_cost_total:.2f}")

if __name__ == "__main__":
    asyncio.run(test_strategy_execution())