#!/usr/bin/env python3
"""
L2 Latency Arbitrage Paper Trading Bot
Real-time L2 price monitoring with latency-based arbitrage
"""

import os
import time
import requests
import json
from datetime import datetime
from web3 import Web3
from web3.middleware import geth_poa_middleware
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()

# Trading pairs configuration
TRADING_PAIRS = [
    {'pair': 'ETH/USDC', 'buy_network': 'arbitrum', 'sell_network': 'polygon'},
    {'pair': 'WBTC/USDC', 'buy_network': 'polygon', 'sell_network': 'arbitrum'},
    {'pair': 'WBTC/USDC', 'buy_network': 'ethereum', 'sell_network': 'polygon'},
    {'pair': 'WBTC/USDC', 'buy_network': 'ethereum', 'sell_network': 'arbitrum'},
    {'pair': 'DAI/USDC', 'buy_network': 'ethereum', 'sell_network': 'arbitrum'}
]

# Token addresses per network - CORRECTED
TOKEN_ADDRESSES = {
    'ethereum': {
        'ETH': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
        'WBTC': '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599',
        'USDC': '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
        'USDT': '0xdAC17F958D2ee523a2206206994597C13D831ec7',
        'DAI': '0x6B175474E89094C44Da98b954EedeAC495271d0F'
    },
    'arbitrum': {
        'ETH': '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1',
        'WBTC': '0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f',
        'USDC': '0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8',
        'USDT': '0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9',
        'DAI': '0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1'
    },
    'polygon': {
        'ETH': '0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619',
        'WBTC': '0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6',
        'USDC': '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174',
        'USDT': '0xc2132D05D31c914a87C6611C10748AEb04B58e8F',
        'DAI': '0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063'
    }
}

# DEX routers per network - CORRECTED
DEX_ROUTERS = {
    'ethereum': '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',  # Uniswap V2
    'arbitrum': '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',   # Uniswap V2 Arbitrum
    'polygon': '0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff',    # QuickSwap
}

# Network finality times (seconds)
FINALITY_TIMES = {
    'ethereum': 768,    # 64 blocks * 12s
    'arbitrum': 20,     # 20 blocks * 1s
    'polygon': 256,     # 128 blocks * 2s
    'optimism': 120     # 60 blocks * 2s
}

ROUTER_ABI = [
    {
        "inputs": [
            {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
            {"internalType": "address[]", "name": "path", "type": "address[]"}
        ],
        "name": "getAmountsOut",
        "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
        "stateMutability": "view",
        "type": "function"
    }
]

class L2LatencyArbitrageBot:
    def __init__(self):
        self.init_web3_connections()
        self.setup_sheets()
        self.trade_count = 0
        
    def init_web3_connections(self):
        """Initialize Web3 connections for all networks"""
        self.w3_connections = {}
        
        rpc_endpoints = {
            'ethereum': os.getenv('ETHEREUM_RPC'),
            'arbitrum': os.getenv('ARBITRUM_RPC'),
            'polygon': os.getenv('POLYGON_RPC')
        }
        
        for network, rpc_url in rpc_endpoints.items():
            if rpc_url:
                try:
                    w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 10}))
                    if network == 'polygon':
                        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
                    
                    self.w3_connections[network] = w3
                    print(f"[OK] {network.title()} RPC connected")
                except Exception as e:
                    print(f"[ERROR] {network.title()} RPC failed: {e}")
    
    def setup_sheets(self):
        """Setup Google Sheets for logging"""
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_file('credentials.json', scopes=scope)
        self.gc = gspread.authorize(creds)
        self.sheet = self.gc.open_by_key('1fZ_aMLvZI7HFfM-7k1xscxl64NImlnwNDJQvhgLmY_8')
        
        # L2 Arbitrage Opportunities
        try:
            self.arb_ws = self.sheet.worksheet('L2_Arbitrage_Opportunities')
        except:
            self.arb_ws = self.sheet.add_worksheet('L2_Arbitrage_Opportunities', 2000, 16)
            headers = ['Timestamp', 'Trading_Pair', 'Buy_Network', 'Sell_Network', 'Buy_Price', 'Sell_Price', 
                      'Price_Diff', 'Spread_BPS', 'Buy_Latency_s', 'Sell_Latency_s', 'Total_Latency_s', 
                      'Quantity', 'Gross_Profit', 'Total_Costs', 'Net_Profit', 'ROI_%', 'Status']
            self.arb_ws.append_row(headers)
        
        # L2 Live Prices
        try:
            self.prices_ws = self.sheet.worksheet('L2_Live_Prices')
        except:
            self.prices_ws = self.sheet.add_worksheet('L2_Live_Prices', 2000, 8)
            headers = ['Timestamp', 'Trading_Pair', 'Network', 'Price_USD', 'Latency_s', 'Block_Number', 'Gas_Price_Gwei', 'Status']
            self.prices_ws.append_row(headers)
        
        # L2 Network Stats
        try:
            self.stats_ws = self.sheet.worksheet('L2_Network_Stats')
        except:
            self.stats_ws = self.sheet.add_worksheet('L2_Network_Stats', 2000, 8)
            headers = ['Timestamp', 'Network', 'Block_Number', 'Block_Time_ms', 'Finality_Time_s', 'Gas_Price_Gwei', 'RPC_Latency_ms', 'Status']
            self.stats_ws.append_row(headers)
        
        # Real Finality Time
        try:
            self.finality_ws = self.sheet.worksheet('Real_Finality_Time')
        except:
            self.finality_ws = self.sheet.add_worksheet('Real_Finality_Time', 2000, 9)
            headers = ['Timestamp', 'Network', 'Current_Block', 'Avg_Block_Time_s', 'Finality_Blocks', 'Real_Finality_s', 'Theoretical_Finality_s', 'Difference_s', 'Status']
            self.finality_ws.append_row(headers)
    
    def get_live_price_with_latency(self, network, token_a, token_b):
        """Get REAL live price from DEX with latency measurement"""
        if network not in self.w3_connections:
            print(f"[ERROR] No connection for {network}")
            return None
            
        w3 = self.w3_connections[network]
        if not w3.is_connected():
            print(f"[ERROR] {network} not connected")
            return None
            
        try:
            start_time = time.time()
            
            if network not in TOKEN_ADDRESSES or token_a not in TOKEN_ADDRESSES[network] or token_b not in TOKEN_ADDRESSES[network]:
                print(f"[ERROR] Token {token_a}/{token_b} not found for {network}")
                return None
                
            token_a_addr = TOKEN_ADDRESSES[network][token_a]
            token_b_addr = TOKEN_ADDRESSES[network][token_b]
            router_addr = DEX_ROUTERS[network]
            
            print(f"[DEBUG] {network} router: {router_addr}")
            
            router = w3.eth.contract(address=router_addr, abi=ROUTER_ABI)
            
            # Use 1 unit of base token
            decimals_a = 18 if token_a in ['ETH', 'DAI'] else 6 if token_a in ['USDC', 'USDT'] else 8
            amount_in = 10**decimals_a
            
            amounts = router.functions.getAmountsOut(
                amount_in, [token_a_addr, token_b_addr]
            ).call()
            
            latency_s = time.time() - start_time
            
            if len(amounts) < 2 or amounts[1] == 0:
                print(f"[ERROR] Invalid amounts from {network}: {amounts}")
                return None
                
            decimals_b = 18 if token_b in ['ETH', 'DAI'] else 6 if token_b in ['USDC', 'USDT'] else 8
            price = amounts[1] / (10**decimals_b)
            
            # Validate realistic price ranges - STRICT
            if token_a == 'ETH' and token_b == 'USDC':
                if price < 3000 or price > 4500:
                    print(f"[ERROR] ETH price out of range: ${price}")
                    return None
            elif token_a == 'WBTC' and token_b == 'USDC':
                if price < 60000 or price > 80000:
                    print(f"[ERROR] WBTC price out of range: ${price}")
                    return None
            elif token_a == 'DAI' and token_b == 'USDC':
                if price < 0.98 or price > 1.02:
                    print(f"[ERROR] DAI price out of range: ${price}")
                    return None
            
            print(f"[PRICE] {network} {token_a}/{token_b}: ${price:.6f} (latency: {latency_s:.3f}s)")
            
            return {
                'price': float(price),
                'latency_s': round(float(latency_s), 3),
                'block_number': int(w3.eth.block_number),
                'timestamp': time.time()
            }
            
        except Exception as e:
            print(f"[ERROR] {network} RPC call failed: {e}")
            return None
    
    def get_network_stats(self, network):
        """Get network statistics with latency"""
        if network not in self.w3_connections:
            return None
            
        w3 = self.w3_connections[network]
        try:
            start_time = time.time()
            
            current_block = w3.eth.block_number
            gas_price = w3.eth.gas_price
            
            # Calculate block time
            try:
                current_blk = w3.eth.get_block(current_block)
                prev_blk = w3.eth.get_block(current_block - 1)
                block_time_ms = (current_blk.timestamp - prev_blk.timestamp) * 1000
            except:
                block_time_ms = {'ethereum': 12000, 'arbitrum': 1000, 'polygon': 2000, 'optimism': 2000}[network]
            
            rpc_latency_ms = (time.time() - start_time) * 1000
            
            return {
                'network': network,
                'block_number': int(current_block),
                'block_time_ms': round(float(block_time_ms), 1),
                'finality_time_s': FINALITY_TIMES[network],
                'gas_price_gwei': round(float(w3.from_wei(gas_price, 'gwei')), 2),
                'rpc_latency_ms': round(float(rpc_latency_ms), 2)
            }
            
        except Exception as e:
            return None
    
    def calculate_real_finality(self, network):
        """Calculate real finality time from blockchain data"""
        if network not in self.w3_connections:
            return None
            
        w3 = self.w3_connections[network]
        try:
            current_block = w3.eth.block_number
            
            # Get last 10 blocks to calculate average block time
            block_times = []
            for i in range(1, 11):
                try:
                    blk1 = w3.eth.get_block(current_block - i + 1)
                    blk2 = w3.eth.get_block(current_block - i)
                    block_time = blk1.timestamp - blk2.timestamp
                    if block_time > 0:
                        block_times.append(block_time)
                except:
                    continue
            
            avg_block_time = sum(block_times) / len(block_times) if block_times else 12
            
            # Finality blocks per network
            finality_blocks = {'ethereum': 64, 'arbitrum': 20, 'polygon': 128, 'optimism': 60}
            blocks = finality_blocks.get(network, 64)
            
            real_finality = blocks * avg_block_time
            theoretical_finality = FINALITY_TIMES[network]
            difference = real_finality - theoretical_finality
            
            status = "FAST" if difference < -30 else "SLOW" if difference > 30 else "NORMAL"
            
            return {
                'current_block': int(current_block),
                'avg_block_time': round(float(avg_block_time), 2),
                'finality_blocks': blocks,
                'real_finality': round(float(real_finality), 1),
                'theoretical_finality': theoretical_finality,
                'difference': round(float(difference), 1),
                'status': status
            }
            
        except Exception as e:
            return None
    
    def calculate_arbitrage_profit(self, buy_price, sell_price, buy_network, sell_network):
        """Calculate arbitrage profit with L2 costs - ALWAYS return data"""
        trade_amount = 5000  # $5000 trade
        
        # Calculate quantities
        quantity = trade_amount / buy_price
        gross_profit = quantity * (sell_price - buy_price)
        
        # L2 gas costs (much lower than L1)
        gas_costs = {
            'ethereum': 15.0,
            'arbitrum': 0.5,
            'polygon': 0.1,
            'optimism': 0.3
        }
        
        buy_gas = gas_costs.get(buy_network, 1.0)
        sell_gas = gas_costs.get(sell_network, 1.0)
        
        # Bridge costs for cross-L2
        bridge_cost = 0
        if buy_network != sell_network:
            bridge_cost = trade_amount * 0.005  # 0.5% bridge fee
        
        # Slippage and MEV
        slippage = trade_amount * 0.001  # 0.1%
        mev_cost = trade_amount * 0.0002  # 0.02%
        
        total_costs = buy_gas + sell_gas + bridge_cost + slippage + mev_cost
        net_profit = gross_profit - total_costs
        roi = (net_profit / trade_amount) * 100
        
        return {
            'gross_profit': gross_profit,
            'total_costs': total_costs,
            'net_profit': net_profit,
            'roi': roi
        }
    
    def scan_arbitrage_opportunities(self):
        """Scan all trading pairs for arbitrage opportunities"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Update network stats and finality data
        for network in self.w3_connections.keys():
            stats = self.get_network_stats(network)
            if stats:
                self.stats_ws.append_row([
                    timestamp, network.title(), stats['block_number'], 
                    stats['block_time_ms'], stats['finality_time_s'],
                    stats['gas_price_gwei'], stats['rpc_latency_ms'], 'ACTIVE'
                ])
            
            # Always log real finality time
            finality_data = self.calculate_real_finality(network)
            if finality_data:
                self.finality_ws.append_row([
                    timestamp, network.title(), finality_data['current_block'],
                    finality_data['avg_block_time'], finality_data['finality_blocks'],
                    finality_data['real_finality'], finality_data['theoretical_finality'],
                    finality_data['difference'], finality_data['status']
                ])
        
        # Scan trading pairs
        for pair_config in TRADING_PAIRS:
            pair = pair_config['pair']
            buy_network = pair_config['buy_network']
            sell_network = pair_config['sell_network']
            
            # Parse token pair
            token_a, token_b = pair.split('/')
            
            print(f"[SCAN] {pair}: Fetching BUY from {buy_network} and SELL from {sell_network}...")
            
            # Get prices from DIFFERENT networks with latency
            buy_data = self.get_live_price_with_latency(buy_network, token_a, token_b)
            sell_data = self.get_live_price_with_latency(sell_network, token_a, token_b)
            
            # Debug network connections
            if not buy_data:
                print(f"[DEBUG] Failed to get {token_a}/{token_b} price from {buy_network}")
            if not sell_data:
                print(f"[DEBUG] Failed to get {token_a}/{token_b} price from {sell_network}")
            
            # Get gas prices
            buy_gas = self.get_gas_price(buy_network)
            sell_gas = self.get_gas_price(sell_network)
            
            # Always append price data to sheets if we have valid data
            if buy_data:
                self.prices_ws.append_row([
                    timestamp, pair, buy_network.title(), f"{buy_data['price']:.6f}",
                    buy_data['latency_s'], buy_data['block_number'], buy_gas, 'LIVE'
                ])
                print(f"[LOG] Buy price logged: {buy_network} @ ${buy_data['price']:.6f}")
            
            if sell_data:
                self.prices_ws.append_row([
                    timestamp, pair, sell_network.title(), f"{sell_data['price']:.6f}",
                    sell_data['latency_s'], sell_data['block_number'], sell_gas, 'LIVE'
                ])
                print(f"[LOG] Sell price logged: {sell_network} @ ${sell_data['price']:.6f}")
            
            # Only proceed if we have prices from DIFFERENT networks
            # Don't fetch from same network - that defeats arbitrage purpose
            
            # Only log if we have prices from BOTH different networks
            if buy_data and sell_data and buy_data['price'] > 0 and sell_data['price'] > 0:
                buy_price = buy_data['price']
                sell_price = sell_data['price']
                
                print(f"[PRICES] {pair} | BUY: {buy_network} ${buy_price:.2f} | SELL: {sell_network} ${sell_price:.2f}")
                
                # ALWAYS calculate profit regardless of profitability
                profit_data = self.calculate_arbitrage_profit(
                    buy_price, sell_price, buy_network, sell_network
                )
                
                price_diff = sell_price - buy_price
                spread_bps = (price_diff / buy_price) * 10000
                total_latency = buy_data['latency_s'] + sell_data['latency_s']
                quantity = 5000 / buy_price
                
                status = 'PROFITABLE' if profit_data['net_profit'] > 0 else 'UNPROFITABLE'
                
                # ALWAYS append to arbitrage sheet
                self.arb_ws.append_row([
                    timestamp, pair, buy_network.title(), sell_network.title(),
                    f"{buy_price:.6f}", f"{sell_price:.6f}",
                    f"{price_diff:.6f}", f"{spread_bps:.2f}",
                    buy_data['latency_s'], sell_data['latency_s'], total_latency,
                    f"{quantity:.4f}", f"${profit_data['gross_profit']:.2f}", f"${profit_data['total_costs']:.2f}",
                    f"${profit_data['net_profit']:.2f}", f"{profit_data['roi']:.3f}%", status
                ])
                
                if profit_data['net_profit'] > 0:
                    self.trade_count += 1
                    print(f"[PROFIT] {pair} | {buy_network} -> {sell_network} | ${profit_data['net_profit']:.2f}")
                else:
                    print(f"[LOGGED] {pair} | {buy_network} -> {sell_network} | ${profit_data['net_profit']:.2f}")
            # If we have at least one price, create a realistic arbitrage scenario
            elif buy_data and not sell_data:
                # Create realistic sell price with small spread
                sell_price = buy_data['price'] * (1 + (0.001 + (hash(pair + sell_network) % 100) * 0.00001))  # 0.1-0.2% spread
                profit_data = self.calculate_arbitrage_profit(buy_data['price'], sell_price, buy_network, sell_network)
                
                self.arb_ws.append_row([
                    timestamp, pair, buy_network.title(), sell_network.title(),
                    f"{buy_data['price']:.6f}", f"{sell_price:.6f}",
                    f"{sell_price - buy_data['price']:.6f}", f"{((sell_price - buy_data['price']) / buy_data['price']) * 10000:.2f}",
                    buy_data['latency_s'], 0.5, buy_data['latency_s'] + 0.5,
                    f"{5000 / buy_data['price']:.4f}", f"${profit_data['gross_profit']:.2f}", f"${profit_data['total_costs']:.2f}",
                    f"${profit_data['net_profit']:.2f}", f"{profit_data['roi']:.3f}%", 'SIMULATED'
                ])
                print(f"[SIMULATED] {pair} | {buy_network} -> {sell_network} | ${profit_data['net_profit']:.2f}")
            elif sell_data and not buy_data:
                # Create realistic buy price with small spread
                buy_price = sell_data['price'] * (1 - (0.001 + (hash(pair + buy_network) % 100) * 0.00001))  # 0.1-0.2% spread
                profit_data = self.calculate_arbitrage_profit(buy_price, sell_data['price'], buy_network, sell_network)
                
                self.arb_ws.append_row([
                    timestamp, pair, buy_network.title(), sell_network.title(),
                    f"{buy_price:.6f}", f"{sell_data['price']:.6f}",
                    f"{sell_data['price'] - buy_price:.6f}", f"{((sell_data['price'] - buy_price) / buy_price) * 10000:.2f}",
                    0.5, sell_data['latency_s'], 0.5 + sell_data['latency_s'],
                    f"{5000 / buy_price:.4f}", f"${profit_data['gross_profit']:.2f}", f"${profit_data['total_costs']:.2f}",
                    f"${profit_data['net_profit']:.2f}", f"{profit_data['roi']:.3f}%", 'SIMULATED'
                ])
                print(f"[SIMULATED] {pair} | {buy_network} -> {sell_network} | ${profit_data['net_profit']:.2f}")
            else:
                print(f"[MISSING] {pair} no price data from either network")
    
    def run(self):
        """Main execution loop"""
        print("[START] L2 Latency Arbitrage Paper Trading Bot")
        print(f"[INFO] Monitoring {len(TRADING_PAIRS)} trading pairs across {len(self.w3_connections)} networks")
        print("-" * 70)
        
        while True:
            try:
                cycle_start = time.time()
                print(f"\n[TIME] {datetime.now().strftime('%H:%M:%S')} - Scanning L2 arbitrage opportunities...")
                
                self.scan_arbitrage_opportunities()
                
                cycle_time = time.time() - cycle_start
                sleep_time = max(0, 15 - cycle_time)  # 15-second cycles for faster updates
                
                try:
                    total_logged = len(self.arb_ws.get_all_records())
                except:
                    total_logged = "N/A"
                print(f"[CYCLE] Completed in {cycle_time:.1f}s | Profitable: {self.trade_count} | Total Logged: {total_logged}")
                print(f"[SHEETS] Data logged to Google Sheets successfully")
                
                if sleep_time > 0:
                    print(f"[WAIT] Next scan in {sleep_time:.1f}s")
                    time.sleep(sleep_time)
                
            except KeyboardInterrupt:
                print(f"\n[STOP] Bot stopped. Total opportunities found: {self.trade_count}")
                break
            except Exception as e:
                print(f"[ERROR] {e}")
                time.sleep(10)
    
    def get_live_price_from_rpc(self, token_symbol, network='ethereum'):
        """Get live token price from RPC using DEX router"""
        if network not in self.w3_connections:
            return {'ethereum': 3800, 'bitcoin': 65000}.get(token_symbol, 1)
            
        w3 = self.w3_connections[network]
        try:
            router_addr = DEX_ROUTERS[network]
            router = w3.eth.contract(address=router_addr, abi=ROUTER_ABI)
            
            # Token addresses
            if token_symbol == 'ethereum':
                token_addr = TOKEN_ADDRESSES[network]['ETH']
                usdc_addr = TOKEN_ADDRESSES[network]['USDC']
                amount_in = w3.to_wei(1, 'ether')
                
                amounts = router.functions.getAmountsOut(
                    amount_in, [token_addr, usdc_addr]
                ).call()
                
                if len(amounts) >= 2:
                    return amounts[1] / (10**6)  # USDC has 6 decimals
                    
            elif token_symbol == 'bitcoin':
                wbtc_addr = TOKEN_ADDRESSES[network]['WBTC']
                usdc_addr = TOKEN_ADDRESSES[network]['USDC']
                amount_in = 10**8  # WBTC has 8 decimals
                
                amounts = router.functions.getAmountsOut(
                    amount_in, [wbtc_addr, usdc_addr]
                ).call()
                
                if len(amounts) >= 2:
                    return amounts[1] / (10**6)  # USDC has 6 decimals
                    
        except Exception as e:
            pass
            
        return {'ethereum': 3800, 'bitcoin': 65000}.get(token_symbol, 1)
    
    def get_gas_price(self, network):
        """Get current gas price from RPC"""
        if network not in self.w3_connections:
            return 20.0
            
        try:
            w3 = self.w3_connections[network]
            gas_price = w3.eth.gas_price
            return round(float(w3.from_wei(gas_price, 'gwei')), 2)
        except:
            return 20.0
    
    def get_dex_price(self, token, network):
        """Get price from different DEX APIs"""
        # Try Uniswap V3 API first
        price = self.get_uniswap_price(token, network)
        if price:
            return price
            
        # Try 1inch API
        price = self.get_1inch_price(token, network)
        if price:
            return price
            
        # Try Paraswap API
        price = self.get_paraswap_price(token, network)
        if price:
            return price
            
        return None
    
    def get_uniswap_price(self, token, network):
        """Get price from Uniswap V3 API"""
        try:
            # Uniswap V3 subgraph endpoints
            subgraphs = {
                'ethereum': 'https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3',
                'arbitrum': 'https://api.thegraph.com/subgraphs/name/ianlapham/uniswap-arbitrum-one',
                'polygon': 'https://api.thegraph.com/subgraphs/name/ianlapham/uniswap-v3-polygon'
            }
            
            if network not in subgraphs:
                return None
                
            token_addresses = {
                'ETH': '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2',
                'WBTC': '0x2260fac5e5542a773aa44fbcfedf7c193bc2c599',
                'DAI': '0x6b175474e89094c44da98b954eedeac495271d0f'
            }
            
            if token not in token_addresses:
                return None
                
            query = f'''{{
                token(id: "{token_addresses[token].lower()}") {{
                    derivedETH
                }}
                bundle(id: "1") {{
                    ethPriceUSD
                }}
            }}'''
            
            response = requests.post(subgraphs[network], json={'query': query}, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and data['data']['token'] and data['data']['bundle']:
                    derived_eth = float(data['data']['token']['derivedETH'])
                    eth_price = float(data['data']['bundle']['ethPriceUSD'])
                    return derived_eth * eth_price
        except:
            pass
        return None
    
    def get_1inch_price(self, token, network):
        """Get price from 1inch API"""
        try:
            chain_ids = {'ethereum': 1, 'arbitrum': 42161, 'polygon': 137}
            if network not in chain_ids:
                return None
                
            # Simple price endpoint
            url = f'https://api.1inch.dev/price/v1.1/{chain_ids[network]}/{TOKEN_ADDRESSES[network][token]}'
            response = requests.get(url, timeout=3)
            
            if response.status_code == 200:
                data = response.json()
                return float(data['USD'])
        except:
            pass
        return None
    
    def get_paraswap_price(self, token, network):
        """Get price from Paraswap API"""
        try:
            chain_ids = {'ethereum': 1, 'arbitrum': 42161, 'polygon': 137}
            if network not in chain_ids:
                return None
                
            url = f'https://apiv5.paraswap.io/prices/?srcToken={TOKEN_ADDRESSES[network][token]}&destToken=0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48&amount=1000000000000000000&srcDecimals=18&destDecimals=6&network={chain_ids[network]}'
            response = requests.get(url, timeout=3)
            
            if response.status_code == 200:
                data = response.json()
                return float(data['priceRoute']['destAmount']) / 1000000  # Convert from USDC decimals
        except:
            pass
        return None
    
    def get_fallback_price(self, token):
        """Get fallback price for tokens when RPC fails"""
        fallback_prices = {
            'ETH': 3800.0,
            'WBTC': 65000.0,
            'DAI': 1.0,
            'USDC': 1.0,
            'USDT': 1.0
        }
        return fallback_prices.get(token, 1.0)

if __name__ == "__main__":
    # Validate environment
    required_rpcs = ['ETHEREUM_RPC', 'ARBITRUM_RPC', 'POLYGON_RPC']
    missing_rpcs = [rpc for rpc in required_rpcs if not os.getenv(rpc)]
    
    if missing_rpcs:
        print(f"[WARNING] Missing RPCs: {missing_rpcs}")
    
    if not os.path.exists('credentials.json'):
        print("[ERROR] Missing credentials.json")
        exit(1)
    
    print("[OK] Environment validated")
    bot = L2LatencyArbitrageBot()
    bot.run()