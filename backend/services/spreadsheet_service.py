import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from typing import Dict, List, Any, Optional
import os
from datetime import datetime
import re
import time
import random
import threading

class SpreadsheetService:
    def __init__(self):
        self.gc = None
        self.last_request_time = 0
        self.request_lock = threading.Lock()
        self.setup_credentials()
        # Map strategy names to their Google Sheets
        self.strategy_sheets = {
            "DEX_to_DEX_Arbitrage": {
                "url": "https://docs.google.com/spreadsheets/d/1MLkSz43NI7R_-GYkhDvx7fg07cS6A_jF2KJutWs5sV4/edit",
                "sheet_id": "1MLkSz43NI7R_-GYkhDvx7fg07cS6A_jF2KJutWs5sV4"
            },
            "Cross_Chain_Arbitrage": {
                "url": "https://docs.google.com/spreadsheets/d/1TcW2S9jnoIRSxyb-vZYJyqP2xVG-wHZhQkQWmVkxcuw/edit",
                "sheet_id": "1TcW2S9jnoIRSxyb-vZYJyqP2xVG-wHZhQkQWmVkxcuw"
            },
            "Triangular_Arbitrage": {
                "url": "https://docs.google.com/spreadsheets/d/1KLWtnqwM4AKPyOuEDuQoOZ1rZJGfQZAt4MF-JdgaPiM/edit",
                "sheet_id": "1KLWtnqwM4AKPyOuEDuQoOZ1rZJGfQZAt4MF-JdgaPiM"
            },
            "Flashloan_Arbitrage": {
                "url": "https://docs.google.com/spreadsheets/d/1qInbTXpO8kfxhJ0k6mc_rmf6-qN7mUGABM6r436212g/edit",
                "sheet_id": "1qInbTXpO8kfxhJ0k6mc_rmf6-qN7mUGABM6r436212g"
            },
            "Sandwich_Arbitrage": {
                "url": "https://docs.google.com/spreadsheets/d/1dXN3bGNrWHldLGrxuwr5vUS68-jqG2JHauP1kHOxFE0/edit",
                "sheet_id": "1dXN3bGNrWHldLGrxuwr5vUS68-jqG2JHauP1kHOxFE0"
            },
            "StableCoin_Arbitrage": {
                "url": "https://docs.google.com/spreadsheets/d/1R7Qa7nLPykDKhEQQF0cypHIp2K90ZtO4CnkijxHBL3s/edit",
                "sheet_id": "1R7Qa7nLPykDKhEQQF0cypHIp2K90ZtO4CnkijxHBL3s"
            },
            "Latency_Arbitrage": {
                "url": "https://docs.google.com/spreadsheets/d/1fZ_aMLvZI7HFfM-7k1xscxl64NImlnwNDJQvhgLmY_8/edit",
                "sheet_id": "1fZ_aMLvZI7HFfM-7k1xscxl64NImlnwNDJQvhgLmY_8"
            }
        }
    
    def setup_credentials(self):
        """Setup Google Sheets credentials"""
        try:
            # Use service account credentials
            credentials_file = os.getenv('GOOGLE_CREDENTIALS_FILE', 'strategies/credentials.json')
            
            # Check multiple possible locations
            possible_paths = [
                credentials_file,
                'credentials.json',
                'strategies/credentials.json',
                os.path.join(os.path.dirname(__file__), '..', 'strategies', 'credentials.json')
            ]
            
            credentials_found = False
            for path in possible_paths:
                if os.path.exists(path):
                    scope = [
                        'https://spreadsheets.google.com/feeds',
                        'https://www.googleapis.com/auth/drive'
                    ]
                    creds = Credentials.from_service_account_file(path, scopes=scope)
                    self.gc = gspread.authorize(creds)
                    credentials_found = True
                    print(f"[SUCCESS] Google Sheets credentials loaded from: {path}")
                    break
            
            if not credentials_found:
                print("[ERROR] Google Sheets credentials not found - will use mock data")
                self.gc = None
                
        except Exception as e:
            print(f"[ERROR] Failed to setup Google Sheets credentials: {e} - will use mock data")
            self.gc = None
    
    def _rate_limit(self):
        """Rate limit Google Sheets API calls to prevent quota exceeded"""
        with self.request_lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            min_interval = 1.5  # 1.5 seconds between requests (40 requests/minute max)
            
            if time_since_last < min_interval:
                sleep_time = min_interval - time_since_last
                time.sleep(sleep_time)
            
            self.last_request_time = time.time()
    
    def get_available_strategies(self) -> List[str]:
        """Get list of available strategies"""
        return list(self.strategy_sheets.keys())
    
    def get_spreadsheet_data(self, strategy_name: str = None, worksheet_name: str = None) -> Dict[str, Any]:
        """Get data from Google Sheets for specific strategy"""
        print(f"Service: Getting spreadsheet data for strategy: '{strategy_name}', worksheet: '{worksheet_name}'")
        
        try:
            if not strategy_name:
                return self._get_all_strategies_overview()
            
            # Clean strategy name
            clean_strategy_name = strategy_name.strip()
            print(f"Service: Clean strategy name: '{clean_strategy_name}'")
            
            if clean_strategy_name not in self.strategy_sheets:
                print(f"Strategy '{clean_strategy_name}' not found in configured sheets. Available: {list(self.strategy_sheets.keys())}")
                return self._get_mock_data(clean_strategy_name, worksheet_name)
            
            # Try to get real data from Google Sheets
            print(f"Service: Attempting to get real data for {clean_strategy_name}")
            try:
                result = self._get_real_data(clean_strategy_name, worksheet_name)
                print(f"Service: Real data result has {len(result.get('worksheets', []))} worksheets")
                return result
            except Exception as e:
                print(f"Service: Real data failed: {e}, using mock data")
                result = self._get_mock_data(clean_strategy_name, worksheet_name)
                print(f"Service: Mock data result has {len(result.get('worksheets', []))} worksheets")
                return result
            
        except Exception as e:
            print(f"Service: Error in get_spreadsheet_data: {e}")
            import traceback
            traceback.print_exc()
            return self._get_mock_data(strategy_name or "unknown", worksheet_name)
    
    def _get_all_strategies_overview(self) -> Dict[str, Any]:
        """Get overview of all strategies"""
        overview = {}
        for strategy_name in self.strategy_sheets.keys():
            overview[strategy_name] = {
                "worksheets": [],
                "sheet_url": self.strategy_sheets[strategy_name]["url"],
                "status": "available"
            }
        
        return {
            "status": "success",
            "strategies": overview,
            "last_updated": datetime.now().isoformat()
        }
    
    def _get_mock_data(self, strategy_name: str = None, worksheet_name: str = None) -> Dict[str, Any]:
        """Return realistic mock data when Google Sheets is not available"""
        try:
            from datetime import datetime, timedelta
            import random
            
            print(f"Mock: Generating data for strategy: '{strategy_name}', worksheet: '{worksheet_name}'")
            
            # Generate timestamps
            now = datetime.now()
            timestamps = [(now - timedelta(minutes=i*5)).strftime('%Y-%m-%d %H:%M:%S') for i in range(10)]
            
            # Simple mock data generators
            def generate_cross_chain_data():
                return {
                    "Arbitrage_Opportunities": [
                        {
                            "Timestamp": ts,
                            "Pair": "ETH/USDC",
                            "Buy_Chain": "Ethereum",
                            "Sell_Chain": "Arbitrum", 
                            "Net_Profit": round(random.uniform(2.5, 25.8), 2),
                            "Expected_Profit": round(random.uniform(5.0, 30.0), 2),
                            "Status": random.choice(["PROFITABLE", "EXECUTED"])
                        } for ts in timestamps
                    ],
                    "Real_Time_Prices": [
                        {
                            "Timestamp": ts,
                            "Pair": "ETH/USDC",
                            "Chain": "Ethereum",
                            "Price": round(3800 + random.uniform(-30, 30), 2)
                        } for ts in timestamps
                    ]
                }
            
            def generate_dex_data():
                return {
                    "Live_Prices": [
                        {
                            "Timestamp": ts,
                            "Pair": "ETH/USDC",
                            "Chain": "Ethereum",
                            "DEX": "Uniswap",
                            "Price": round(3800 + random.uniform(-50, 50), 2),
                            "Gas_Fee": round(random.uniform(2, 8), 2),
                            "Liquidity": random.randint(1000000, 5000000)
                        } for ts in timestamps
                    ],
                    "Live_Arbitrage": [
                        {
                            "Timestamp": ts,
                            "Pair": "ETH/USDC",
                            "Chain": "Ethereum",
                            "Buy_DEX": "Uniswap",
                            "Sell_DEX": "SushiSwap",
                            "Buy_Price": round(3795 + random.uniform(-5, 5), 2),
                            "Sell_Price": round(3798 + random.uniform(-3, 3), 2),
                            "Spread_Percent": round(random.uniform(0.05, 0.15), 3),
                            "Net_Profit": round(random.uniform(1.2, 18.5), 2),
                            "Expected_Profit": round(random.uniform(2.0, 22.0), 2),
                            "Status": random.choice(["PROFITABLE", "EXECUTED"])
                        } for ts in timestamps
                    ]
                }
            
            # Strategy data mapping
            strategy_data_map = {
                "Cross_Chain_Arbitrage": generate_cross_chain_data(),
                "DEX_to_DEX_Arbitrage": generate_dex_data(),
                "Triangular_Arbitrage": generate_dex_data(),
                "Flashloan_Arbitrage": generate_dex_data(),
                "Sandwich_Arbitrage": generate_dex_data(),
                "StableCoin_Arbitrage": generate_dex_data(),
                "Latency_Arbitrage": generate_cross_chain_data()
            }
            
            if strategy_name:
                clean_name = strategy_name.strip()
                strategy_data = strategy_data_map.get(clean_name, {"Main": [{"Message": f"No data for {clean_name}", "Timestamp": now.isoformat()}]})
                
                print(f"Mock: Generated {len(strategy_data)} worksheets for {clean_name}")
                
                result = {
                    "status": "success",
                    "strategy": clean_name,
                    "data": strategy_data,
                    "worksheets": list(strategy_data.keys()),
                    "sheet_url": self.strategy_sheets.get(clean_name, {}).get("url", ""),
                    "last_updated": now.isoformat(),
                    "data_source": "mock_data"
                }
                
                print(f"Mock: Returning result with worksheets: {result['worksheets']}")
                return result
            
            return {
                "status": "success",
                "strategies": {name: {"worksheets": list(data.keys())} for name, data in strategy_data_map.items()},
                "last_updated": now.isoformat()
            }
            
        except Exception as e:
            print(f"Mock data error: {e}")
            import traceback
            traceback.print_exc()
            
            fallback_name = strategy_name.strip() if strategy_name else "unknown"
            return {
                "status": "success",
                "strategy": fallback_name,
                "data": {"Main": [{"Message": f"Error generating data: {str(e)}", "Timestamp": datetime.now().isoformat()}]},
                "worksheets": ["Main"],
                "last_updated": datetime.now().isoformat(),
                "error": str(e)
            }
    
    def export_data(self, format_type: str = "csv", strategy_name: str = None, worksheet_name: str = None) -> bytes:
        """Export spreadsheet data in specified format"""
        print(f"Exporting {format_type} data for strategy: {strategy_name}, worksheet: {worksheet_name}")
        data = self.get_spreadsheet_data(strategy_name, worksheet_name)
        
        if format_type.lower() == "csv":
            if strategy_name and "data" in data and data["data"]:
                if worksheet_name and worksheet_name in data["data"]:
                    sheet_data = data["data"][worksheet_name]
                    if sheet_data:
                        df = pd.DataFrame(sheet_data)
                        print(f"Exporting {len(sheet_data)} records from {worksheet_name}")
                    else:
                        print(f"No data found in worksheet {worksheet_name}")
                        df = pd.DataFrame([{"message": "No data available", "timestamp": datetime.now().isoformat()}])
                else:
                    # Combine all worksheets for the strategy
                    all_data = []
                    for sheet_name, sheet_data in data["data"].items():
                        if sheet_data:
                            for row in sheet_data:
                                if isinstance(row, dict):
                                    row["worksheet"] = sheet_name
                                    all_data.append(row)
                    
                    if all_data:
                        df = pd.DataFrame(all_data)
                        print(f"Exporting {len(all_data)} total records from all worksheets")
                    else:
                        print("No data found in any worksheet")
                        df = pd.DataFrame([{"message": "No data available", "strategy": strategy_name, "timestamp": datetime.now().isoformat()}])
            else:
                print("No strategy data available")
                df = pd.DataFrame([{"message": "No data available", "timestamp": datetime.now().isoformat()}])
            
            csv_data = df.to_csv(index=False)
            return csv_data.encode('utf-8')
        
        elif format_type.lower() == "json":
            import json
            json_data = json.dumps(data, indent=2, default=str)
            return json_data.encode('utf-8')
        
        else:
            raise ValueError(f"Unsupported format: {format_type}")

    def _get_real_data(self, strategy_name: str, worksheet_name: str = None) -> Dict[str, Any]:
        """Get real data from Google Sheets"""
        if not self.gc:
            raise Exception("Google Sheets client not initialized")
            
        try:
            sheet_info = self.strategy_sheets[strategy_name]
            sheet_id = sheet_info["sheet_id"]
            
            print(f"[INFO] Opening spreadsheet: {sheet_id}")
            
            # Rate limit to prevent quota exceeded
            self._rate_limit()
            
            # Open the spreadsheet
            spreadsheet = self.gc.open_by_key(sheet_id)
            worksheets = spreadsheet.worksheets()
            
            print(f"[INFO] Found {len(worksheets)} worksheets: {[w.title for w in worksheets]}")
            
            data = {}
            worksheet_names = []
            
            for worksheet in worksheets:
                try:
                    print(f"[INFO] Reading worksheet: {worksheet.title}")
                    # Get all values first to check if worksheet has data
                    all_values = worksheet.get_all_values()
                    if len(all_values) > 1:  # Has header + at least one data row
                        records = worksheet.get_all_records()
                        if records:
                            data[worksheet.title] = records
                            worksheet_names.append(worksheet.title)
                            print(f"[SUCCESS] Loaded {len(records)} records from {worksheet.title}")
                        else:
                            print(f"[WARNING] No records found in worksheet {worksheet.title}")
                    else:
                        print(f"[WARNING] Worksheet {worksheet.title} is empty or has no data rows")
                except Exception as e:
                    print(f"[ERROR] Error reading worksheet {worksheet.title}: {e}")
                    # Add empty worksheet to list but not to data
                    worksheet_names.append(worksheet.title)
                    continue
            
            # If no data found, return empty structure
            if not data:
                print(f"[WARNING] No data found in any worksheet for {strategy_name}")
                data = {"Main": [{"Message": "No data available", "Timestamp": datetime.now().isoformat()}]}
                worksheet_names = ["Main"]
            
            # If specific worksheet requested, filter to that worksheet
            if worksheet_name and worksheet_name in data:
                filtered_data = {worksheet_name: data[worksheet_name]}
            else:
                filtered_data = data
            
            print(f"[SUCCESS] Successfully retrieved data for {strategy_name}")
            
            return {
                "status": "success",
                "strategy": strategy_name,
                "data": filtered_data,
                "worksheets": worksheet_names,
                "sheet_url": sheet_info["url"],
                "last_updated": datetime.now().isoformat(),
                "data_source": "google_sheets",
                "total_worksheets": len(worksheets),
                "data_worksheets": len([w for w in worksheet_names if w in data])
            }
            
        except Exception as e:
            print(f"[ERROR] Error fetching real data for {strategy_name}: {e}")
            import traceback
            traceback.print_exc()
            raise e

# Create service instance
spreadsheet_service = SpreadsheetService()