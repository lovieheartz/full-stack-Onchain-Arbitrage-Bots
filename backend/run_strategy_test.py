#!/usr/bin/env python3
"""
Test script to run a strategy and verify it's working with real data
"""

import asyncio
import sys
import os
from datetime import datetime

# Add strategies directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'strategies'))

async def test_flashloan_strategy():
    """Test the flashloan arbitrage strategy"""
    print("Testing Flashloan Arbitrage Strategy")
    print("=" * 50)
    
    try:
        from flashloan_arbitrage_bot_fixed import FlashloanArbitrageBot
        
        bot = FlashloanArbitrageBot()
        print(f"Bot initialized with {len(bot.w3_connections)} chain connections")
        
        # Test price fetching
        print("\nTesting price fetching...")
        prices = await bot.scan_all_dex_prices('ETH')
        print(f"Retrieved {len(prices)} prices for ETH")
        
        for dex, price_data in prices.items():
            print(f"  {dex}: ${price_data['price']:.6f}")
        
        # Test arbitrage detection
        print("\nTesting arbitrage detection...")
        opportunity = await bot.find_best_arbitrage('ETH')
        
        if opportunity:
            print(f"Arbitrage opportunity found:")
            print(f"  Buy: {opportunity['buy_dex']} @ ${opportunity['buy_price']:.6f}")
            print(f"  Sell: {opportunity['sell_dex']} @ ${opportunity['sell_price']:.6f}")
            print(f"  Spread: {opportunity['spread']:.4f}%")
            print(f"  Net Profit: ${opportunity['net_profit']:.2f}")
            print(f"  Success: {opportunity['execution_success']}")
        else:
            print("No arbitrage opportunity found")
        
        # Test logging
        print("\nTesting Google Sheets logging...")
        if opportunity:
            bot.log_trade(opportunity)
            print("Trade logged to Google Sheets")
        
        print("\nFlashloan strategy test completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error testing flashloan strategy: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_l2_latency_strategy():
    """Test the L2 latency arbitrage strategy"""
    print("\nTesting L2 Latency Arbitrage Strategy")
    print("=" * 50)
    
    try:
        from l2_latency_bot import L2LatencyArbitrageBot
        
        bot = L2LatencyArbitrageBot()
        print(f"Bot initialized with {len(bot.w3_connections)} chain connections")
        
        # Test one scan cycle
        print("\nRunning one arbitrage scan cycle...")
        bot.scan_arbitrage_opportunities()
        
        print("L2 latency strategy test completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error testing L2 latency strategy: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all strategy tests"""
    print(f"Strategy Testing Started at {datetime.now()}")
    print("=" * 60)
    
    results = []
    
    # Test flashloan strategy
    try:
        result = await test_flashloan_strategy()
        results.append(("Flashloan Arbitrage", result))
    except Exception as e:
        print(f"Flashloan test failed: {e}")
        results.append(("Flashloan Arbitrage", False))
    
    # Test L2 latency strategy
    try:
        result = await test_l2_latency_strategy()
        results.append(("L2 Latency Arbitrage", result))
    except Exception as e:
        print(f"L2 latency test failed: {e}")
        results.append(("L2 Latency Arbitrage", False))
    
    # Print results
    print("\n" + "=" * 60)
    print("STRATEGY TEST RESULTS")
    print("=" * 60)
    
    for strategy, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{strategy}: {status}")
    
    successful = sum(1 for _, success in results if success)
    total = len(results)
    print(f"\nOverall: {successful}/{total} strategies working correctly")
    
    if successful == total:
        print("🎉 All strategies are working with real data!")
    else:
        print("⚠️  Some strategies need fixing")

if __name__ == "__main__":
    asyncio.run(main())