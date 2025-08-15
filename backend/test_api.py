#!/usr/bin/env python3

import sys
import os
sys.path.append('.')

# Test the API endpoint directly
async def test_endpoint():
    try:
        print("Testing spreadsheet API endpoint...")
        
        # Import the route function
        from routes.spreadsheet import get_strategy_data
        
        # Test the function directly
        result = await get_strategy_data("DEX_to_DEX_Arbitrage")
        
        print("✓ API call successful")
        print("Result keys:", list(result.keys()))
        print("Status:", result.get('status'))
        print("Worksheets:", result.get('worksheets', []))
        print("Data keys:", list(result.get('data', {}).keys()))
        
        return result
        
    except Exception as e:
        print("✗ API Error:", str(e))
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_endpoint())