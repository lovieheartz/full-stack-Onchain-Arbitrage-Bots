#!/usr/bin/env python3
"""
Multi-Chain Paper Trading Bot - SIMULATION WITH LIVE PRICES
Polygon ($40), Arbitrum ($40), Base ($20) - Total $100 Virtual
"""

import os
import time
import logging
from datetime import datetime
from web3 import Web3
from eth_account import Account
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)

# PAPER TRADING CONFIG - CONTINUOUS SIMULATION
TRADING_CONFIG = {
    'POLYGON_TRADE_USD': 200,   # $200 trades
    'ARBITRUM_TRADE_USD': 200,  # $200 trades
    'BASE_TRADE_USD': 100,      # $100 trades
    'MIN_PROFIT_USD': 0.10,     # $0.10 minimum
    'MAX_GAS_USD': 0.10,        # Max $0.10 gas per trade
    'SLIPPAGE_TOLERANCE': 0.01, # 1% slippage
    'MIN_SPREAD_BPS': 25,       # 25 bps minimum
    'MAX_TRADES_PER_HOUR': 20,  # No hourly limit for paper trading
    'ENABLE_REAL_EXECUTION': False,  # PAPER TRADING ONLY
    'CONTINUOUS_MODE': True,    # Run until manually stopped
}

# VERIFIED STABLECOINS - UPDATED ADDRESSES
TOKENS = {
    'polygon': {
        'USDC': '0x3c499c542cef5e3811e1192ce70d8cc03d5c3359',  # USDC on Polygon - VERIFIED
        'USDT': '0xc2132D05D31c914a87C6611C10748AEb04B58e8F',  # USDT on Polygon - VERIFIED
    },
    'arbitrum': {
        'USDC': '0xaf88d065e77c8cC2239327C5EDb3A432268e5831',  # USDC Arbitrum - VERIFIED
        'USDT': '0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9',  # USDT Arbitrum - VERIFIED
    },
    'base': {
        'USDC': '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913',  # USDC Base - VERIFIED
    }
}

# EXPANDED DEX CONFIGURATIONS FOR MORE OPPORTUNITIES
DEXS = {
    # POLYGON DEXs (Ultra low gas ~$0.005)
    'QuickSwap': {'router': '0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff', 'chain': 'polygon', 'fee': 0.003},
    'SushiSwap_Polygon': {'router': '0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506', 'chain': 'polygon', 'fee': 0.003},
    'Uniswap_Polygon': {'router': '0xE592427A0AEce92De3Edee1F18E0157C05861564', 'chain': 'polygon', 'fee': 0.003},
    'DODO_Polygon': {'router': '0xa222e6a71D1A1Dd5F279805fbe38d5329C1d0e70', 'chain': 'polygon', 'fee': 0.002},
    
    # ARBITRUM DEXs (Low gas ~$0.03)
    'Camelot': {'router': '0xc873fEcbd354f5A56E00E710B90EF4201db2448d', 'chain': 'arbitrum', 'fee': 0.0025},
    'SushiSwap_Arbitrum': {'router': '0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506', 'chain': 'arbitrum', 'fee': 0.003},
    'Uniswap_Arbitrum': {'router': '0xE592427A0AEce92De3Edee1F18E0157C05861564', 'chain': 'arbitrum', 'fee': 0.003},
    'TraderJoe_Arbitrum': {'router': '0xb4315e873dBcf96Ffd0acd8EA43f689D8c20fB30', 'chain': 'arbitrum', 'fee': 0.0025},
    
    # BASE DEXs (Low gas ~$0.02)
    'Uniswap_Base': {'router': '0x2626664c2603336E57B271c5C0b26F421741e481', 'chain': 'base', 'fee': 0.003},
    'PancakeSwap_Base': {'router': '0x8cFe327CEc66d1C090Dd72bd0FF11d690C33a2Eb', 'chain': 'base', 'fee': 0.0025},
    'BaseSwap': {'router': '0x327Df1E6de05895d2ab08513aaDD9313Fe505d86', 'chain': 'base', 'fee': 0.002}
}

WETH = {
    'polygon': '0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270',
    'arbitrum': '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1',
    'base': '0x4200000000000000000000000000000000000006'
}

# Native ETH address for gas calculations
ETH_ADDRESS = '0x0000000000000000000000000000000000000000'

ROUTER_ABI = [
    {"inputs": [{"type": "uint256", "name": "amountIn"}, {"type": "address[]", "name": "path"}],
     "name": "getAmountsOut", "outputs": [{"type": "uint256[]", "name": "amounts"}],
     "stateMutability": "view", "type": "function"},
    {"inputs": [{"type": "uint256", "name": "amountOutMin"}, {"type": "address[]", "name": "path"}, 
      {"type": "address", "name": "to"}, {"type": "uint256", "name": "deadline"}],
     "name": "swapExactETHForTokens", "outputs": [{"type": "uint256[]", "name": "amounts"}],
     "stateMutability": "payable", "type": "function"},
    {"inputs": [{"type": "uint256", "name": "amountIn"}, {"type": "uint256", "name": "amountOutMin"}, 
      {"type": "address[]", "name": "path"}, {"type": "address", "name": "to"}, {"type": "uint256", "name": "deadline"}],
     "name": "swapExactTokensForETH", "outputs": [{"type": "uint256[]", "name": "amounts"}],
     "stateMutability": "nonpayable", "type": "function"}
]

ERC20_ABI = [
    {"inputs": [{"name": "account", "type": "address"}], "name": "balanceOf", 
     "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}], 
     "name": "approve", "outputs": [{"name": "", "type": "bool"}], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], 
     "stateMutability": "view", "type": "function"}
]

class MultiChainLiveBot:
    def __init__(self):
        self.setup_connections()
        self.setup_wallet()
        self.setup_sheets()
        self.trades_this_hour = 0
        self.last_hour = datetime.now().hour
        self.total_trades = 0
        self.total_pnl = 0.0
        self.daily_pnl = 0.0
        self.consecutive_losses = 0
        self.start_time = datetime.now()
        self.last_profit_check = datetime.now().date()
        
    def setup_connections(self):
        """Setup multi-chain connections"""
        self.w3_connections = {}
        
        rpcs = {
            'polygon': os.getenv('POLYGON_RPC'),
            'arbitrum': os.getenv('ARBITRUM_RPC'),
            'base': os.getenv('BASE_RPC')
        }
        
        for chain, rpc in rpcs.items():
            if rpc:
                try:
                    w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={'timeout': 30}))
                    if chain == 'polygon':
                        from web3.middleware import geth_poa_middleware
                        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
                    
                    if w3.is_connected():
                        self.w3_connections[chain] = w3
                        print(f"SUCCESS: {chain.title()} connected")
                except Exception as e:
                    print(f"ERROR: {chain.title()}: {e}")
        
        if not self.w3_connections:
            raise Exception("No chain connections")
            
    def setup_wallet(self):
        """Setup wallet and check balances"""
        private_key = os.getenv('PRIVATE_KEY')
        if not private_key:
            raise Exception("PRIVATE_KEY not found")
            
        self.account = Account.from_key(private_key)
        self.wallet_address = self.account.address
        
        print(f"Wallet: {self.wallet_address}")
        
        # Check balances on each chain
        self.balances = {}
        for chain, w3 in self.w3_connections.items():
            try:
                # Native balance
                native_balance = w3.eth.get_balance(self.wallet_address)
                native_eth = w3.from_wei(native_balance, 'ether')
                
                # Token balances
                tokens = {}
                for token_symbol, token_address in TOKENS[chain].items():
                    try:
                        contract = w3.eth.contract(address=w3.to_checksum_address(token_address), abi=ERC20_ABI)
                        balance = contract.functions.balanceOf(self.wallet_address).call()
                        decimals = contract.functions.decimals().call()
                        token_balance = balance / (10 ** decimals)
                        tokens[token_symbol] = token_balance
                    except:
                        tokens[token_symbol] = 0
                
                self.balances[chain] = {
                    'native': float(native_eth),
                    'tokens': tokens
                }
                
                total_tokens = tokens.get('USDC', 0) + tokens.get('USDT', 0)
                trading_status = "Token Trading Ready" if total_tokens > 5 else "Low Balance"
                print(f"{chain.title()}: {native_eth:.4f} native, USDC: {tokens.get('USDC', 0):.2f}, USDT: {tokens.get('USDT', 0):.2f} | {trading_status}")
                
            except Exception as e:
                print(f"Balance check failed for {chain}: {e}")
                
        # Check if we have any tokens to trade with real money
        total_token_balance = 0
        for chain_balances in self.balances.values():
            for token_balance in chain_balances.get('tokens', {}).values():
                total_token_balance += token_balance
        
        print(f"\nPAPER TRADING: Simulating with virtual $100 balance")
        
        # Virtual balances for paper trading - INCREASED
        self.virtual_balances = {
            'polygon': {'USDC': 500.0, 'USDT': 0.0},
            'arbitrum': {'USDC': 500.0, 'USDT': 0.0}, 
            'base': {'USDC': 300.0}
        }
        total_funded_usd = 1300
        print(f"\n💰 VIRTUAL FUNDING STATUS:")
        print(f"Total virtual capital: $1,300")
        print(f"Polygon: $500 | Arbitrum: $500 | Base: $300")
        print(f"\n📊 PAPER TRADING MODE ACTIVE")
        print(f"✅ Using live prices for realistic simulation")
        print(f"🌉 Cross-chain arbitrage enabled")
        TRADING_CONFIG['ENABLE_REAL_EXECUTION'] = False
        
        # Show initial market scan
        self.show_market_overview()
                
    def setup_sheets(self):
        """Setup Google Sheets"""
        try:
            scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
            creds = Credentials.from_service_account_file('credentials.json', scopes=scope)
            gc = gspread.authorize(creds)
            sheet = gc.open_by_key('1R7Qa7nLPykDKhEQQF0cypHIp2K90ZtO4CnkijxHBL3s')
            
            try:
                self.ws = sheet.worksheet('Multi_Chain_Paper_Trades')
            except:
                self.ws = sheet.add_worksheet('Multi_Chain_Paper_Trades', 1000, 15)
                headers = ['Timestamp', 'Chain', 'Token', 'Buy_DEX', 'Sell_DEX', 'Buy_Price', 
                          'Sell_Price', 'Spread_BPS', 'Trade_Amount', 'Profit_USD', 'Gas_Cost', 
                          'Status', 'TX_Hash', 'Balance_After', 'Notes']
                self.ws.append_row(headers)
                
            print("Google Sheets connected")
        except Exception as e:
            print(f"Sheets failed: {e}")
            self.ws = None
    
    def get_token_price(self, token, dex, chain):
        """Get token price from DEX"""
        try:
            if chain not in self.w3_connections or token not in TOKENS[chain]:
                return None
                
            w3 = self.w3_connections[chain]
            router_address = DEXS[dex]['router']
            router = w3.eth.contract(address=w3.to_checksum_address(router_address), abi=ROUTER_ABI)
            
            token_address = TOKENS[chain][token]
            weth_address = WETH[chain]
            decimals = 6 if token in ['USDC', 'USDT'] else 18
            
            # Token -> WETH -> USDC for price
            if token != 'USDC' and 'USDC' in TOKENS[chain]:
                try:
                    amounts = router.functions.getAmountsOut(
                        10**decimals,
                        [w3.to_checksum_address(token_address), w3.to_checksum_address(TOKENS[chain]['USDC'])]
                    ).call()
                    
                    if len(amounts) >= 2 and amounts[1] > 0:
                        price = amounts[1] / 10**6
                        if 0.9 <= price <= 1.1:  # Reasonable stablecoin range
                            return price
                except:
                    pass
            
            # Fallback: Token -> WETH -> USDC
            try:
                eth_amounts = router.functions.getAmountsOut(
                    10**decimals,
                    [w3.to_checksum_address(token_address), w3.to_checksum_address(weth_address)]
                ).call()
                
                if len(eth_amounts) >= 2 and eth_amounts[1] > 0 and 'USDC' in TOKENS[chain]:
                    usdc_amounts = router.functions.getAmountsOut(
                        eth_amounts[1],
                        [w3.to_checksum_address(weth_address), w3.to_checksum_address(TOKENS[chain]['USDC'])]
                    ).call()
                    
                    if len(usdc_amounts) >= 2 and usdc_amounts[1] > 0:
                        price = usdc_amounts[1] / 10**6
                        if 0.9 <= price <= 1.1:
                            return price
            except:
                pass
                
            return None
            
        except Exception as e:
            logger.error(f"Price fetch error {chain} {dex} {token}: {e}")
            return None
    
    def find_arbitrage(self):
        """Find profitable cross-chain and intra-chain arbitrage opportunities"""
        print("\nScanning for arbitrage across all chains...")
        
        best_opportunity = None
        best_profit = 0
        
        # Get all available chains
        available_chains = [chain for chain in ['polygon', 'arbitrum', 'base'] if chain in self.w3_connections]
        
        # Collect all prices from all DEXs across all chains
        all_prices = {}
        
        for chain in available_chains:
            virtual_tokens = self.virtual_balances.get(chain, {})
            total_virtual_usd = sum(virtual_tokens.values())
            print(f"   {chain}: ${total_virtual_usd:.0f} virtual balance")
            
            chain_dexs = [dex for dex, config in DEXS.items() if config['chain'] == chain]
            
            for token in TOKENS[chain].keys():
                if token not in all_prices:
                    all_prices[token] = {}
                
                # Get prices from all DEXs on this chain
                for dex in chain_dexs:
                    price = self.get_token_price(token, dex, chain)
                    if price:
                        all_prices[token][f"{dex}_{chain}"] = {
                            'price': price,
                            'dex': dex,
                            'chain': chain
                        }
                        print(f"   {chain} {dex} {token}: ${price:.6f}")
        
        # Find best arbitrage opportunities across ALL chains and DEXs
        for token in all_prices.keys():
            if len(all_prices[token]) < 2:
                continue
                
            # Find min and max prices across ALL chains
            prices_list = [(key, data) for key, data in all_prices[token].items()]
            prices_only = [data['price'] for data in all_prices[token].values()]
            
            if len(prices_only) < 2:
                continue
                
            min_price = min(prices_only)
            max_price = max(prices_only)
            spread = max_price - min_price
            spread_bps = (spread / min_price) * 10000
            
            # Find which DEX/chain has min and max prices
            buy_info = None
            sell_info = None
            
            for key, data in all_prices[token].items():
                if data['price'] == min_price and not buy_info:
                    buy_info = data
                if data['price'] == max_price and not sell_info:
                    sell_info = data
            
            if not buy_info or not sell_info:
                # Skip if missing price data
                continue
                
            # Allow both cross-chain and intra-chain, but prioritize cross-chain
            is_cross_chain = buy_info['chain'] != sell_info['chain']
                
            trade_type_label = "CROSS-CHAIN" if is_cross_chain else "INTRA-CHAIN"
            print(f"   {trade_type_label} {token}: {buy_info['chain']} -> {sell_info['chain']} | Spread {spread_bps:.1f} bps")
            
            # Log live prices to sheet
            self.log_live_prices(token, buy_info, sell_info, spread_bps, is_cross_chain)
            
            if spread_bps >= TRADING_CONFIG['MIN_SPREAD_BPS']:
                # Determine trade amount based on buy chain
                buy_chain = buy_info['chain']
                if buy_chain == 'polygon':
                    trade_amount = TRADING_CONFIG['POLYGON_TRADE_USD']
                elif buy_chain == 'arbitrum':
                    trade_amount = TRADING_CONFIG['ARBITRUM_TRADE_USD']
                else:  # base
                    trade_amount = TRADING_CONFIG['BASE_TRADE_USD']
                
                quantity = trade_amount / min_price
                gross_profit = quantity * spread
                
                # Cross-chain costs (higher than intra-chain)
                buy_gas = self.estimate_gas_cost(buy_chain)
                sell_gas = self.estimate_gas_cost(sell_info['chain'])
                bridge_fee = self.estimate_bridge_cost(buy_chain, sell_info['chain'], trade_amount)
                total_gas = buy_gas + sell_gas
                
                # DEX fees and slippage
                dex_fee = trade_amount * 0.006  # 0.6% total (both sides)
                slippage_cost = trade_amount * 0.015  # 1.5% cross-chain slippage
                
                total_costs = total_gas + bridge_fee + dex_fee + slippage_cost
                net_profit = gross_profit - total_costs
                
                print(f"   {token}: Buy {buy_info['chain']} ${min_price:.6f} -> Sell {sell_info['chain']} ${max_price:.6f}")
                print(f"   Costs: Gas ${total_gas:.3f} + Bridge ${bridge_fee:.3f} + Fees ${dex_fee:.3f} = ${total_costs:.3f}")
                print(f"   Profit: Gross ${gross_profit:.4f} - Costs ${total_costs:.3f} = Net ${net_profit:.4f}")
                
                if net_profit >= TRADING_CONFIG['MIN_PROFIT_USD'] and net_profit > best_profit:
                    opportunity_type = 'cross_chain' if is_cross_chain else 'intra_chain'
                    
                    if is_cross_chain:
                        best_opportunity = {
                            'type': opportunity_type,
                            'token': token,
                            'buy_chain': buy_info['chain'],
                            'sell_chain': sell_info['chain'],
                            'buy_dex': buy_info['dex'],
                            'sell_dex': sell_info['dex'],
                            'buy_price': min_price,
                            'sell_price': max_price,
                            'spread_bps': spread_bps,
                            'trade_amount': trade_amount,
                            'quantity': quantity,
                            'gross_profit': gross_profit,
                            'gas_cost': total_gas,
                            'bridge_fee': bridge_fee,
                            'dex_fee': dex_fee,
                            'total_costs': total_costs,
                            'net_profit': net_profit
                        }
                    else:
                        best_opportunity = {
                            'type': opportunity_type,
                            'chain': buy_info['chain'],
                            'token': token,
                            'buy_dex': buy_info['dex'],
                            'sell_dex': sell_info['dex'],
                            'buy_price': min_price,
                            'sell_price': max_price,
                            'spread_bps': spread_bps,
                            'trade_amount': trade_amount,
                            'quantity': quantity,
                            'gross_profit': gross_profit,
                            'gas_cost': total_gas,
                            'dex_fee': dex_fee,
                            'total_costs': total_costs,
                            'net_profit': net_profit
                        }
                    best_profit = net_profit
        
        # Also check intra-chain opportunities as fallback
        if not best_opportunity:
            print("   No cross-chain opportunities, checking intra-chain...")
            
            for chain in available_chains:
                chain_dexs = [dex for dex, config in DEXS.items() if config['chain'] == chain]
                
                if len(chain_dexs) < 2:
                    continue
                    
                for token in TOKENS[chain].keys():
                    prices = {}
                    
                    # Get prices from all DEXs on this chain
                    for dex in chain_dexs:
                        price = self.get_token_price(token, dex, chain)
                        if price:
                            prices[dex] = price
                    
                    # Find arbitrage opportunity
                    if len(prices) >= 2:
                        max_price = max(prices.values())
                        min_price = min(prices.values())
                        spread = max_price - min_price
                        spread_bps = (spread / min_price) * 10000
                        
                        if spread_bps >= TRADING_CONFIG['MIN_SPREAD_BPS']:
                            buy_dex = [k for k, v in prices.items() if v == min_price][0]
                            sell_dex = [k for k, v in prices.items() if v == max_price][0]
                            
                            if chain == 'polygon':
                                trade_amount = TRADING_CONFIG['POLYGON_TRADE_USD']
                            elif chain == 'arbitrum':
                                trade_amount = TRADING_CONFIG['ARBITRUM_TRADE_USD']
                            else:
                                trade_amount = TRADING_CONFIG['BASE_TRADE_USD']
                            
                            quantity = trade_amount / min_price
                            gross_profit = quantity * spread
                            
                            gas_cost = {'polygon': 0.01, 'arbitrum': 0.05, 'base': 0.03}.get(chain, 0.05)
                            dex_fee = trade_amount * 0.003
                            slippage_cost = trade_amount * 0.01
                            total_costs = gas_cost + dex_fee + slippage_cost
                            net_profit = gross_profit - total_costs
                            
                            if net_profit >= TRADING_CONFIG['MIN_PROFIT_USD'] and net_profit > best_profit:
                                best_opportunity = {
                                    'type': 'intra_chain',
                                    'chain': chain,
                                    'token': token,
                                    'buy_dex': buy_dex,
                                    'sell_dex': sell_dex,
                                    'buy_price': min_price,
                                    'sell_price': max_price,
                                    'spread_bps': spread_bps,
                                    'trade_amount': trade_amount,
                                    'quantity': quantity,
                                    'gross_profit': gross_profit,
                                    'gas_cost': gas_cost,
                                    'dex_fee': dex_fee,
                                    'total_costs': total_costs,
                                    'net_profit': net_profit
                                }
                                best_profit = net_profit
        
        return best_opportunity
    
    def estimate_gas_cost(self, chain):
        """Estimate gas cost for chain"""
        try:
            if chain not in self.w3_connections:
                return 2.0
                
            w3 = self.w3_connections[chain]
            gas_price = w3.eth.gas_price
            gas_limit = 400000  # Conservative for buy + approve + sell
            gas_cost_wei = gas_price * gas_limit
            gas_cost_native = w3.from_wei(gas_cost_wei, 'ether')
            
            # Updated native token prices in USD
            native_prices = {'polygon': 0.85, 'arbitrum': 3800, 'base': 3800}
            native_price = native_prices.get(chain, 1)
            
            gas_cost_usd = float(gas_cost_native) * native_price
            return min(gas_cost_usd, TRADING_CONFIG['MAX_GAS_USD'])  # Cap gas cost
            
        except:
            # Ultra low fallback gas estimates
            return {'polygon': 0.005, 'arbitrum': 0.03, 'base': 0.02}.get(chain, 0.02)
    
    def estimate_bridge_cost(self, from_chain, to_chain, amount_usd):
        """Estimate cross-chain bridge costs"""
        # Bridge fee matrix (percentage of trade amount)
        bridge_fees = {
            ('polygon', 'arbitrum'): 0.003,  # 0.3% via Polygon Bridge
            ('arbitrum', 'polygon'): 0.003,  # 0.3% via Arbitrum Bridge
            ('polygon', 'base'): 0.005,      # 0.5% via LayerZero/Stargate
            ('base', 'polygon'): 0.005,      # 0.5% via LayerZero/Stargate
            ('arbitrum', 'base'): 0.004,     # 0.4% via LayerZero/Stargate
            ('base', 'arbitrum'): 0.004,     # 0.4% via LayerZero/Stargate
        }
        
        fee_rate = bridge_fees.get((from_chain, to_chain), 0.005)  # Default 0.5%
        bridge_fee = amount_usd * fee_rate
        
        # Add fixed gas costs for bridge transactions
        bridge_gas = {
            'polygon': 0.02,   # MATIC for bridge tx
            'arbitrum': 0.08,  # ETH for bridge tx
            'base': 0.06       # ETH for bridge tx
        }
        
        total_bridge_cost = bridge_fee + bridge_gas.get(from_chain, 0.05) + bridge_gas.get(to_chain, 0.05)
        return total_bridge_cost
    
    def safety_checks(self, opportunity):
        """Basic safety checks for paper trading"""
        trade_type = opportunity.get('type', 'intra_chain')
        
        if trade_type == 'cross_chain':
            buy_chain = opportunity['buy_chain']
            sell_chain = opportunity['sell_chain']
        else:
            chain = opportunity['chain']
        
        # Reset daily PnL tracking
        current_date = datetime.now().date()
        if current_date != self.last_profit_check:
            self.daily_pnl = 0.0
            self.last_profit_check = current_date
        
        # Check connections
        if trade_type == 'cross_chain':
            if buy_chain not in self.w3_connections:
                print(f"ERROR: No connection to buy chain {buy_chain}")
                return False
            if sell_chain not in self.w3_connections:
                print(f"ERROR: No connection to sell chain {sell_chain}")
                return False
        else:
            if chain not in self.w3_connections:
                print(f"ERROR: No connection to {chain}")
                return False
        
        # For paper trading, check virtual balances instead of real balances
        if trade_type == 'cross_chain':
            # Check virtual balances for cross-chain trades
            buy_virtual = self.virtual_balances.get(buy_chain, {}).get(opportunity['token'], 0)
            sell_virtual = self.virtual_balances.get(sell_chain, {}).get(opportunity['token'], 0)
            
            # Allow trade if we have virtual funds OR if it's profitable (paper trading)
            if buy_virtual < opportunity['trade_amount'] and opportunity['net_profit'] <= 0:
                print(f"SKIP: Insufficient virtual {buy_chain} {opportunity['token']} balance")
                return False
        else:
            # Check virtual balance for intra-chain trades
            virtual_balance = self.virtual_balances.get(chain, {}).get(opportunity['token'], 0)
            
            if virtual_balance < opportunity['trade_amount'] and opportunity['net_profit'] <= 0:
                print(f"SKIP: Insufficient virtual {chain} {opportunity['token']} balance")
                return False
        
        # Will buy tokens with ETH - skip token balance check
        
        # Check gas cost
        if opportunity['gas_cost'] > TRADING_CONFIG['MAX_GAS_USD']:
            print(f"ERROR: Gas too expensive: ${opportunity['gas_cost']:.2f}")
            return False
        
        # Accept profitable trades
        if opportunity['net_profit'] < 0.05:  # Lower threshold for testing
            print(f"SKIP: Insufficient profit: ${opportunity['net_profit']:.4f} < $0.05")
            return False
        
        # Check spread is large enough
        if opportunity['spread_bps'] < 50:
            print(f"SKIP: Spread too small: {opportunity['spread_bps']:.1f} bps < 50")
            return False
        
        # For paper trading, only check profitability
        if opportunity['net_profit'] < TRADING_CONFIG['MIN_PROFIT_USD']:
            print(f"SKIP: Profit ${opportunity['net_profit']:.4f} below minimum ${TRADING_CONFIG['MIN_PROFIT_USD']}")
            return False
        
        print(f"✅ PAPER TRADE APPROVED: ${opportunity['net_profit']:.4f} profit")
        return True
    
    def execute_trade(self, opportunity):
        """Execute paper arbitrage trade (cross-chain or intra-chain)"""
        trade_type = opportunity.get('type', 'intra_chain')
        
        if trade_type == 'cross_chain':
            print(f"🌉 CROSS-CHAIN PAPER TRADE: {opportunity['buy_chain']} -> {opportunity['sell_chain']}")
            print(f"   {opportunity['token']}: Buy ${opportunity['buy_price']:.6f} -> Sell ${opportunity['sell_price']:.6f}")
            print(f"   Expected profit: ${opportunity['net_profit']:.3f}")
            
            # Simulate cross-chain execution with longer delays
            print(f"   Step 1: Buy {opportunity['token']} on {opportunity['buy_dex']} ({opportunity['buy_chain']})")
            time.sleep(1)
            print(f"   Step 2: Bridge {opportunity['token']} to {opportunity['sell_chain']} (5-10 min)")
            time.sleep(2)  # Simulate bridge time
            print(f"   Step 3: Sell {opportunity['token']} on {opportunity['sell_dex']} ({opportunity['sell_chain']})")
            time.sleep(1)
            
            # Update virtual balances on both chains
            buy_chain = opportunity['buy_chain']
            sell_chain = opportunity['sell_chain']
            token = opportunity['token']
            
        else:
            print(f"⚡ INTRA-CHAIN PAPER TRADE: {opportunity['chain']} {opportunity['token']}")
            print(f"   Buy ${opportunity['buy_price']:.6f} -> Sell ${opportunity['sell_price']:.6f}")
            print(f"   Expected profit: ${opportunity['net_profit']:.3f}")
            
            # Simulate intra-chain execution
            time.sleep(1)
            
            chain = opportunity['chain']
            token = opportunity['token']
        
        # Simulate profit/loss with realistic variance
        import random
        
        # Cross-chain trades have lower success rate due to complexity
        success_rate = 0.75 if trade_type == 'cross_chain' else 0.85
        
        if random.random() < success_rate:
            # Successful trade with variance
            variance = random.uniform(0.8, 1.2)  # ±20% variance
            actual_profit = opportunity['net_profit'] * variance
            
            # Update virtual balances
            if trade_type == 'cross_chain':
                # Deduct from buy chain, add to sell chain
                if token in self.virtual_balances.get(buy_chain, {}):
                    self.virtual_balances[buy_chain][token] -= opportunity['trade_amount']
                if token in self.virtual_balances.get(sell_chain, {}):
                    self.virtual_balances[sell_chain][token] += opportunity['trade_amount'] + actual_profit
            else:
                # Intra-chain: just add profit
                if token in self.virtual_balances.get(chain, {}):
                    self.virtual_balances[chain][token] += actual_profit
        else:
            # Failed trade - lose gas and fees
            gas_cost = opportunity.get('gas_cost', 0.05)
            bridge_fee = opportunity.get('bridge_fee', 0)
            actual_profit = -(gas_cost + bridge_fee)
            
            print(f"   ❌ Trade failed - lost ${abs(actual_profit):.3f} in fees")
        
        # Update tracking
        self.total_trades += 1
        self.total_pnl += actual_profit
        self.daily_pnl += actual_profit
        
        if actual_profit > 0:
            self.consecutive_losses = 0
            trade_emoji = "🌉" if trade_type == 'cross_chain' else "⚡"
            print(f"💰 {trade_emoji} PROFIT: ${actual_profit:.3f} | Daily: ${self.daily_pnl:.2f} | Total: ${self.total_pnl:.2f}")
        else:
            self.consecutive_losses += 1
            print(f"📉 LOSS: ${actual_profit:.3f} | Daily: ${self.daily_pnl:.2f} | Total: ${self.total_pnl:.2f}")
        
        # Calculate total virtual balance
        total_virtual = sum(sum(tokens.values()) for tokens in self.virtual_balances.values())
        
        result = {
            'success': actual_profit > 0,
            'simulated': True,
            'trade_type': trade_type,
            'profit': actual_profit,
            'total_pnl': self.total_pnl,
            'trade_number': self.total_trades,
            'virtual_balance': total_virtual
        }
        
        self.log_trade(opportunity, result)
        return result
        
        # Skip complex safety checks for paper trading
        chain = opportunity['chain']
        print(f"SIMULATING TRADE: {chain} {opportunity['token']} ${opportunity['net_profit']:.3f} profit")
        
        # Paper trading simulation - no actual blockchain interaction needed
            
        # All validation passed in paper trading
            
        # Simulate gas costs for paper trading
        gas_cost_usd = opportunity['gas_cost']
            
        # Paper trading - simulate token acquisition
        virtual_balance = self.virtual_balances[chain].get(opportunity['token'], 0)
        if virtual_balance >= opportunity['trade_amount']:
            print(f"Using virtual {opportunity['token']} balance: ${virtual_balance:.2f}")
        else:
            print(f"Simulating token purchase with virtual funds")
            
        # Paper trading - simulate buy transaction
        print(f"Simulating buy on {opportunity['buy_dex']} at ${opportunity['buy_price']:.6f}")
            
        # Simulate buy execution
        print(f"Buy transaction simulated successfully")
        buy_hash = f"0x{''.join([f'{i:02x}' for i in range(32)])}"
        time.sleep(1)  # Simulate confirmation time
            
        # Simulate approval
        print(f"Token approval simulated")
        time.sleep(0.5)
            
        # Simulate sell transaction
        print(f"Simulating sell on {opportunity['sell_dex']} at ${opportunity['sell_price']:.6f}")
        sell_hash = f"0x{''.join([f'{i+32:02x}' for i in range(32)])}"
        time.sleep(1)  # Simulate confirmation time
        print(f"Sell transaction simulated: {sell_hash}")
            
        # Calculate simulated profit
        import random
        # Add some randomness to make simulation realistic
        variance = random.uniform(0.85, 1.15)  # ±15% variance
        actual_profit = opportunity['net_profit'] * variance
        
        # Update tracking
        self.total_trades += 1
        self.total_pnl += actual_profit
        self.daily_pnl += actual_profit
        
        if actual_profit > 0:
            self.consecutive_losses = 0
            print(f"💰 SIMULATED PROFIT: ${actual_profit:.3f} | Daily: ${self.daily_pnl:.2f} | Total: ${self.total_pnl:.2f}")
        else:
            self.consecutive_losses += 1
            print(f"📉 SIMULATED LOSS: ${actual_profit:.3f} | Daily: ${self.daily_pnl:.2f} | Total: ${self.total_pnl:.2f}")
            
        result = {
            'success': True,
            'simulated': True,
            'buy_hash': buy_hash,
            'sell_hash': sell_hash,
            'gas_cost': gas_cost_usd,
            'profit': actual_profit,
            'total_pnl': self.total_pnl,
            'trade_number': self.total_trades,
            'virtual_balance': sum(sum(tokens.values()) for tokens in self.virtual_balances.values())
        }
        
        self.log_trade(opportunity, result)
        return result
    
    def convert_eth_to_usdc(self, chain):
        """Convert ETH back to USDC for continuous trading"""
        try:
            if chain not in self.w3_connections:
                return
                
            w3 = self.w3_connections[chain]
            current_balance = w3.eth.get_balance(self.wallet_address)
            
            # Keep some ETH for gas, convert rest to USDC
            gas_reserve = {'polygon': w3.to_wei(0.1, 'ether'), 'arbitrum': w3.to_wei(0.001, 'ether'), 'base': w3.to_wei(0.001, 'ether')}
            reserve = gas_reserve.get(chain, w3.to_wei(0.001, 'ether'))
            
            if current_balance > reserve * 2:  # Only convert if we have excess ETH
                eth_to_convert = current_balance - reserve
                
                # Get router and addresses
                router_address = DEXS['QuickSwap']['router'] if chain == 'polygon' else DEXS['Uniswap_' + chain.title()]['router']
                router = w3.eth.contract(address=w3.to_checksum_address(router_address), abi=ROUTER_ABI)
                
                weth_address = WETH[chain]
                usdc_address = TOKENS[chain]['USDC']
                
                # Convert ETH to USDC
                gas_price = w3.eth.gas_price
                
                txn = router.functions.swapExactETHForTokens(
                    1,  # Accept any amount of USDC
                    [w3.to_checksum_address(weth_address), w3.to_checksum_address(usdc_address)],
                    self.wallet_address,
                    int(time.time()) + 600
                ).build_transaction({
                    'from': self.wallet_address,
                    'value': eth_to_convert,
                    'gas': 300000,
                    'gasPrice': gas_price,
                    'nonce': w3.eth.get_transaction_count(self.wallet_address)
                })
                
                signed_txn = w3.eth.account.sign_transaction(txn, self.account.key)
                tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
                w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
                
                print(f"✅ Converted ETH back to USDC on {chain}")
                
        except Exception as e:
            print(f"⚠️  ETH to USDC conversion failed on {chain}: {e}")
    
    def refresh_balances(self):
        """Refresh wallet balances after trades"""
        print("\n🔄 Refreshing wallet balances...")
        
        for chain, w3 in self.w3_connections.items():
            try:
                # Native balance
                native_balance = w3.eth.get_balance(self.wallet_address)
                native_eth = w3.from_wei(native_balance, 'ether')
                
                # Token balances
                tokens = {}
                for token_symbol, token_address in TOKENS[chain].items():
                    try:
                        contract = w3.eth.contract(address=w3.to_checksum_address(token_address), abi=ERC20_ABI)
                        balance = contract.functions.balanceOf(self.wallet_address).call()
                        decimals = contract.functions.decimals().call()
                        token_balance = balance / (10 ** decimals)
                        tokens[token_symbol] = token_balance
                    except:
                        tokens[token_symbol] = 0
                
                self.balances[chain] = {
                    'native': float(native_eth),
                    'tokens': tokens
                }
                
                total_tokens = sum(tokens.values())
                print(f"   {chain.title()}: {native_eth:.4f} native, ${total_tokens:.2f} tokens")
                
            except Exception as e:
                print(f"   {chain.title()}: Balance refresh failed - {e}")
    
    def log_trade(self, opportunity, result):
        """Log trade to Google Sheets"""
        if not self.ws:
            return
            
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            trade_type = opportunity.get('type', 'intra_chain')
            
            if result.get('success'):
                status = f"PAPER_{trade_type.upper()}"
                tx_hash = 'SIMULATED'
                profit = f"${result.get('profit', 0):.3f}"
            else:
                status = "FAILED"
                tx_hash = 'FAILED'
                profit = f"${result.get('profit', 0):.3f}"
            
            # Handle different trade types
            if trade_type == 'cross_chain':
                chain_info = f"{opportunity['buy_chain']} -> {opportunity['sell_chain']}"
                buy_dex = f"{opportunity['buy_dex']} ({opportunity['buy_chain']})"
                sell_dex = f"{opportunity['sell_dex']} ({opportunity['sell_chain']})"
                gas_cost = f"${opportunity.get('gas_cost', 0) + opportunity.get('bridge_fee', 0):.3f}"
                notes = f"Cross-chain arbitrage with bridge fee"
            else:
                chain_info = opportunity['chain'].title()
                buy_dex = opportunity['buy_dex']
                sell_dex = opportunity['sell_dex']
                gas_cost = f"${opportunity.get('gas_cost', 0):.3f}"
                notes = f"Intra-chain arbitrage"
            
            row = [
                timestamp,
                chain_info,
                opportunity['token'],
                buy_dex,
                sell_dex,
                f"{opportunity['buy_price']:.6f}",
                f"{opportunity['sell_price']:.6f}",
                f"{opportunity['spread_bps']:.1f}",
                f"${opportunity['trade_amount']:.0f}",
                profit,
                gas_cost,
                status,
                tx_hash,
                f"Virtual: ${result.get('virtual_balance', 1300):.0f}",
                notes
            ]
            
            self.ws.append_row(row)
            print(f"Trade logged: {status}")
            
        except Exception as e:
            logger.error(f"Logging failed: {e}")
    
    def show_market_overview(self):
        """Display current market conditions across all chains"""
        print(f"\n📊 MARKET OVERVIEW - {datetime.now().strftime('%H:%M:%S')}")
        print("-" * 50)
        
        # Collect prices from all chains
        market_data = {}
        
        for chain in ['polygon', 'arbitrum', 'base']:
            if chain not in self.w3_connections:
                continue
                
            chain_dexs = [dex for dex, config in DEXS.items() if config['chain'] == chain]
            
            for token in TOKENS[chain].keys():
                if token not in market_data:
                    market_data[token] = {}
                
                prices = []
                for dex in chain_dexs:
                    price = self.get_token_price(token, dex, chain)
                    if price:
                        market_data[token][f"{dex}_{chain}"] = price
                        prices.append(price)
                
                if prices:
                    min_price = min(prices)
                    max_price = max(prices)
                    spread_bps = ((max_price - min_price) / min_price) * 10000 if min_price > 0 else 0
                    print(f"{chain.title()} {token}: ${min_price:.6f} - ${max_price:.6f} (spread: {spread_bps:.1f} bps)")
        
        # Show best cross-chain opportunities
        print("\n🌉 CROSS-CHAIN SPREADS:")
        for token in market_data.keys():
            if len(market_data[token]) >= 2:
                all_prices = list(market_data[token].values())
                min_price = min(all_prices)
                max_price = max(all_prices)
                spread_bps = ((max_price - min_price) / min_price) * 10000 if min_price > 0 else 0
                
                # Find which chains have min/max
                min_chain = None
                max_chain = None
                for key, price in market_data[token].items():
                    if price == min_price and not min_chain:
                        min_chain = key.split('_')[-1]
                    if price == max_price and not max_chain:
                        max_chain = key.split('_')[-1]
                
                if min_chain != max_chain and spread_bps >= 25:
                    print(f"{token}: {min_chain} ${min_price:.6f} -> {max_chain} ${max_price:.6f} ({spread_bps:.1f} bps)")
        
        print("-" * 50)
    
    def log_live_prices(self, token, buy_info, sell_info, spread_bps, is_cross_chain):
        """Log live prices to Google Sheets"""
        if not hasattr(self, 'prices_ws') or not self.prices_ws:
            return
            
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Calculate potential profit
            trade_amount = 200 if buy_info['chain'] in ['polygon', 'arbitrum'] else 100
            quantity = trade_amount / buy_info['price']
            gross_profit = quantity * (sell_info['price'] - buy_info['price'])
            
            if is_cross_chain:
                gas_cost = 0.08
                bridge_fee = trade_amount * 0.005
                total_costs = gas_cost + bridge_fee + (trade_amount * 0.006)
            else:
                total_costs = 0.05 + (trade_amount * 0.003)
            
            net_profit = gross_profit - total_costs
            
            row = [
                timestamp,
                f"{buy_info['chain']} -> {sell_info['chain']}",
                f"{buy_info['dex']} -> {sell_info['dex']}",
                token,
                f"${buy_info['price']:.6f} -> ${sell_info['price']:.6f}",
                f"{spread_bps:.1f}",
                buy_info['chain'],
                sell_info['chain'],
                f"${net_profit:.4f}",
                "CROSS-CHAIN" if is_cross_chain else "INTRA-CHAIN"
            ]
            
            self.prices_ws.append_row(row)
            
        except Exception as e:
            logger.error(f"Live price logging failed: {e}")
    
    def run_continuous(self):
        """Run continuous multi-chain arbitrage paper trading"""
        print("🌉 MULTI-CHAIN ARBITRAGE PAPER TRADING")
        print("=" * 60)
        print(f"💰 VIRTUAL ALLOCATION: Polygon $500 | Arbitrum $500 | Base $300 = $1,300 Total")
        print(f"📊 CONTINUOUS PAPER TRADING | Min profit: ${TRADING_CONFIG['MIN_PROFIT_USD']}")
        print(f"⚡ CROSS-CHAIN ARBITRAGE: All chains connected")
        print(f"🌉 Bridge support: Polygon <-> Arbitrum <-> Base")
        print("📊 LIVE PRICE SIMULATION - Press Ctrl+C to stop")
        print("=" * 60)
        
        # Track trade statistics by type
        trade_stats = {
            'cross_chain': {'count': 0, 'profit': 0.0},
            'intra_chain': {'count': 0, 'profit': 0.0}
        }
        
        scan_count = 0
        
        while True:
            try:
                scan_count += 1
                print(f"\\nScan #{scan_count} - {datetime.now().strftime('%H:%M:%S')}")
                
                opportunity = self.find_arbitrage()
                
                if opportunity:
                    trade_type = opportunity.get('type', 'intra_chain')
                    if trade_type == 'cross_chain':
                        print(f"🌉 CROSS-CHAIN OPPORTUNITY: {opportunity['buy_chain']} -> {opportunity['sell_chain']} {opportunity['token']} - ${opportunity['net_profit']:.4f} profit")
                    else:
                        print(f"⚡ INTRA-CHAIN OPPORTUNITY: {opportunity['chain']} {opportunity['token']} - ${opportunity['net_profit']:.4f} profit")
                    
                    if self.safety_checks(opportunity):
                        result = self.execute_trade(opportunity)
                    else:
                        print("Trade skipped due to safety checks")
                        continue
                    
                        self.trades_this_hour += 1
                        
                        # Update trade statistics
                        trade_type = result.get('trade_type', 'intra_chain')
                        trade_stats[trade_type]['count'] += 1
                        trade_stats[trade_type]['profit'] += result.get('profit', 0)
                        
                        # Show progress with chain distribution
                        cross_trades = trade_stats['cross_chain']['count']
                        intra_trades = trade_stats['intra_chain']['count']
                        
                        print(f"Trade #{self.total_trades} | Cross-chain: {cross_trades} | Intra-chain: {intra_trades}")
                        print(f"PnL: ${self.total_pnl:.2f} | Cross: ${trade_stats['cross_chain']['profit']:.2f} | Intra: ${trade_stats['intra_chain']['profit']:.2f}")
                        
                        # Show virtual balance distribution
                        for chain, balances in self.virtual_balances.items():
                            total_chain = sum(balances.values())
                            print(f"   {chain.title()}: ${total_chain:.0f} virtual balance")
                    
                    # Update trade frequency tracking
                    current_hour = datetime.now().hour
                    if current_hour != self.last_hour:
                        self.trades_this_hour = 0
                        self.last_hour = current_hour
                else:
                    print("No profitable opportunities found across all chains")
                    # Show current price spreads for debugging
                    print("Current spreads:")
                    for chain in ['polygon', 'arbitrum', 'base']:
                        if chain in self.w3_connections:
                            print(f"   {chain}: Scanning DEXs...")
                
                # Show market overview every 10 scans
                if scan_count % 10 == 0:
                    self.show_market_overview()
                
                time.sleep(15)  # 15 second intervals for faster opportunity detection
                
            except KeyboardInterrupt:
                print(f"\n🛑 PAPER TRADING STOPPED")
                print(f"\n📊 FINAL RESULTS:")
                print(f"Total scans: {scan_count}")
                print(f"Cross-chain trades: {trade_stats['cross_chain']['count']} (${trade_stats['cross_chain']['profit']:.2f})")
                print(f"Intra-chain trades: {trade_stats['intra_chain']['count']} (${trade_stats['intra_chain']['profit']:.2f})")
                print(f"Total trades: {self.total_trades}")
                print(f"Total PnL: ${self.total_pnl:.2f}")
                print(f"Daily PnL: ${self.daily_pnl:.2f}")
                
                # Show final virtual balances
                print(f"\n💰 FINAL VIRTUAL BALANCES:")
                total_balance = 0
                for chain, balances in self.virtual_balances.items():
                    chain_total = sum(balances.values())
                    total_balance += chain_total
                    print(f"   {chain.title()}: ${chain_total:.2f}")
                print(f"   Total: ${total_balance:.2f} (Started: $1,300)")
                print(f"   Net change: ${total_balance - 1300:.2f}")
                break
            except Exception as e:
                logger.error(f"Bot error: {e}")
                time.sleep(60)

if __name__ == "__main__":
    print("🌉 MULTI-CHAIN ARBITRAGE PAPER TRADING")
    print(f"💰 VIRTUAL ALLOCATION: $1,300 across 3 chains")
    print("⚡ CONTINUOUS SIMULATION WITH LIVE PRICES")
    print("📊 Press Ctrl+C to stop and view final results")
    print("-" * 60)
    
    try:
        bot = MultiChainLiveBot()
        bot.run_continuous()
    except Exception as e:
        print(f"Bot startup failed: {e}")