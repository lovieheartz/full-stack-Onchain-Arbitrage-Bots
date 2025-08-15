#!/usr/bin/env python3
"""Test all strategy endpoints to ensure they work properly"""

from fastapi.testclient import TestClient
from main import app

def test_all_strategies():
    client = TestClient(app)
    
    strategies = [
        'DEX_to_DEX_Arbitrage',
        'Cross_Chain_Arbitrage', 
        'Triangular_Arbitrage',
        'Flashloan_Arbitrage',
        'Sandwich_Arbitrage',
        'StableCoin_Arbitrage',
        'Latency_Arbitrage'
    ]
    
    print("Testing all strategy endpoints...")
    print("=" * 50)
    
    for strategy in strategies:
        try:
            response = client.get(f'/api/spreadsheet/data/{strategy}')
            result = response.json()
            
            status = "✓" if response.status_code == 200 and result.get('status') == 'success' else "✗"
            worksheets = result.get('worksheets', [])
            data_keys = list(result.get('data', {}).keys())
            
            print(f"{status} {strategy}")
            print(f"  Status Code: {response.status_code}")
            print(f"  API Status: {result.get('status')}")
            print(f"  Worksheets: {len(worksheets)} ({', '.join(worksheets)})")
            print(f"  Data Keys: {', '.join(data_keys)}")
            print()
            
        except Exception as e:
            print(f"✗ {strategy} - ERROR: {e}")
            print()

if __name__ == "__main__":
    test_all_strategies()