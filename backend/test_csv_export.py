#!/usr/bin/env python3
"""
Test CSV export functionality
"""

import os
from services.spreadsheet_service import spreadsheet_service

def test_csv_export():
    """Test CSV export for all strategies"""
    print("Testing CSV Export Functionality")
    print("=" * 50)
    
    strategies = spreadsheet_service.get_available_strategies()
    print(f"Testing {len(strategies)} strategies")
    
    for strategy in strategies:
        print(f"\nTesting CSV export for: {strategy}")
        print("-" * 30)
        
        try:
            # Test CSV export
            csv_data = spreadsheet_service.export_data("csv", strategy)
            
            if csv_data:
                csv_text = csv_data.decode('utf-8')
                lines = csv_text.split('\n')
                
                print(f"✅ CSV export successful")
                print(f"   Size: {len(csv_data)} bytes")
                print(f"   Lines: {len(lines)}")
                print(f"   Header: {lines[0] if lines else 'No header'}")
                
                # Show sample data
                if len(lines) > 1:
                    print(f"   Sample: {lines[1][:100]}{'...' if len(lines[1]) > 100 else ''}")
                
                # Save to file for inspection
                filename = f"export_{strategy}.csv"
                with open(filename, 'wb') as f:
                    f.write(csv_data)
                print(f"   Saved to: {filename}")
                
            else:
                print("❌ CSV export returned empty data")
                
        except Exception as e:
            print(f"❌ CSV export failed: {e}")
    
    # Test JSON export
    print(f"\nTesting JSON export...")
    print("-" * 30)
    
    try:
        json_data = spreadsheet_service.export_data("json", "Cross_Chain_Arbitrage")
        
        if json_data:
            json_text = json_data.decode('utf-8')
            print(f"✅ JSON export successful")
            print(f"   Size: {len(json_data)} bytes")
            print(f"   Preview: {json_text[:200]}...")
            
            # Save to file
            with open("export_sample.json", 'wb') as f:
                f.write(json_data)
            print(f"   Saved to: export_sample.json")
        else:
            print("❌ JSON export returned empty data")
            
    except Exception as e:
        print(f"❌ JSON export failed: {e}")
    
    print(f"\nCSV Export Test Complete!")

if __name__ == "__main__":
    test_csv_export()