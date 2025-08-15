#!/usr/bin/env python3
"""
Test script to verify Google Sheets connection and data retrieval
"""

import os
import sys
from services.spreadsheet_service import spreadsheet_service

def test_sheets_connection():
    """Test Google Sheets connection and data retrieval"""
    print("Testing Google Sheets Connection...")
    print("=" * 50)
    
    # Test getting available strategies
    strategies = spreadsheet_service.get_available_strategies()
    print(f"Available strategies: {strategies}")
    
    # Test each strategy
    for strategy in strategies[:3]:  # Test first 3 strategies
        print(f"\nTesting strategy: {strategy}")
        print("-" * 30)
        
        try:
            data = spreadsheet_service.get_spreadsheet_data(strategy)
            print(f"Status: {data.get('status')}")
            print(f"Data source: {data.get('data_source', 'unknown')}")
            print(f"Worksheets: {data.get('worksheets', [])}")
            
            if data.get('data'):
                total_records = sum(len(sheet_data) for sheet_data in data['data'].values() if isinstance(sheet_data, list))
                print(f"Total records: {total_records}")
                
                # Show sample data from first worksheet
                for sheet_name, sheet_data in data['data'].items():
                    if sheet_data and isinstance(sheet_data, list):
                        print(f"Sample from {sheet_name}: {len(sheet_data)} records")
                        if sheet_data:
                            print(f"First record keys: {list(sheet_data[0].keys()) if isinstance(sheet_data[0], dict) else 'Not a dict'}")
                        break
            
        except Exception as e:
            print(f"Error testing {strategy}: {e}")
    
    # Test CSV export
    print(f"\nTesting CSV Export...")
    print("-" * 30)
    
    try:
        csv_data = spreadsheet_service.export_data("csv", "Cross_Chain_Arbitrage")
        print(f"CSV export successful: {len(csv_data)} bytes")
        
        # Show first few lines of CSV
        csv_text = csv_data.decode('utf-8')
        lines = csv_text.split('\n')[:5]
        for i, line in enumerate(lines):
            print(f"Line {i+1}: {line[:100]}{'...' if len(line) > 100 else ''}")
            
    except Exception as e:
        print(f"CSV export error: {e}")

if __name__ == "__main__":
    test_sheets_connection()