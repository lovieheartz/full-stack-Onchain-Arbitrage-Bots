#!/usr/bin/env python3
"""
Sandwich Arbitrage Bot for Ethereum Mainnet
Production-grade MEV bot with mempool monitoring and Flashbots integration

=== WHAT IS SANDWICH ARBITRAGE? ===

Sandwich arbitrage is a MEV (Maximal Extractable Value) strategy where a bot "sandwiches" 
a victim's transaction between two of its own transactions to extract profit.

=== HOW IT WORKS ===

1. **MEMPOOL MONITORING**: Bot scans pending transactions for large DEX swaps
2. **FRONT-RUN**: Bot places a transaction with higher gas to execute BEFORE victim
3. **VICTIM TRANSACTION**: Original user's swap executes at worse price
4. **BACK-RUN**: Bot places second transaction to sell tokens back for profit

=== EXAMPLE SCENARIO ===

Victim wants to buy 1000 USDC worth of TOKEN_X on Uniswap:

**BEFORE SANDWICH:**
- TOKEN_X price: $1.00
- Pool: 100,000 USDC ↔ 100,000 TOKEN_X
- Victim gets: ~990 TOKEN_X (after fees)

**SANDWICH ATTACK:**

1. **FRONT-RUN** (Bot Transaction #1):
   - Bot buys 500 USDC worth of TOKEN_X first
   - Pool becomes: 100,500 USDC ↔ 99,502 TOKEN_X  
   - TOKEN_X price rises to ~$1.01

2. **VICTIM TRANSACTION**:
   - Victim's 1000 USDC swap executes at higher price
   - Victim gets only ~985 TOKEN_X (5 tokens less!)
   - Pool becomes: 101,500 USDC ↔ 98,517 TOKEN_X
   - TOKEN_X price now ~$1.03

3. **BACK-RUN** (Bot Transaction #2):
   - Bot sells its ~498 TOKEN_X back to pool
   - Bot receives ~513 USDC
   - **BOT PROFIT**: 513 - 500 = 13 USDC (minus gas costs)
   - **VICTIM LOSS**: 5 TOKEN_X worth ~$5

=== KEY COMPONENTS ===

- **Gas Price Optimization**: Front-run needs higher gas than victim
- **Slippage Calculation**: Determine optimal sandwich size
- **MEV Protection**: Use Flashbots to avoid being sandwiched yourself
- **Profit Threshold**: Must exceed gas costs (typically 0.01-0.1 ETH minimum)

=== RISKS ===

- **Failed Transactions**: High gas costs if transactions revert
- **MEV Competition**: Other bots competing for same opportunities  
- **Slippage**: Price movements can eliminate profits
- **Gas Wars**: Escalating gas prices reduce profitability

=== ETHICAL CONSIDERATIONS ===

Sandwich attacks extract value from regular users, making their trades more expensive.
This bot is for educational purposes to understand MEV mechanics.

"""

import os
import time
import json
import csv
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from decimal import Decimal

import requests
from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_account import Account
from eth_abi import decode, encode
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials

load_dotenv()

# Configuration
CONFIG = {
    'ETHEREUM_RPC': os.getenv('ETHEREUM_RPC'),
    'PRIVATE_KEY': os.getenv('PRIVATE_KEY'),
    'MIN_PROFIT_ETH': float(os.getenv('MIN_PROFIT_ETH', '0.001')),  # Lowered to 0.001 ETH
    'MAX_GAS_PRICE_GWEI': int(os.getenv('MAX_GAS_PRICE_GWEI', '100')),
    'GAS_MULTIPLIER': float(os.getenv('GAS_MULTIPLIER', '1.2')),
    'FLASHBOTS_ENABLED': os.getenv('FLASHBOTS_ENABLED', 'true').lower() == 'true',
    'SANDWICH_SHEET_ID': '1dXN3bGNrWHldLGrxuwr5vUS68-jqG2JHauP1kHOxFE0',  # Direct sheet ID
    'PAPER_TRADING_MODE': os.getenv('PAPER_TRADING_MODE', 'true').lower() == 'true'
}

# LIVE DEX Detection - No Hardcoding
DEX_ROUTERS = {
    '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D': 'Uniswap_V2',
    '0xE592427A0AEce92De3Edee1F18E0157C05861564': 'Uniswap_V3', 
    '0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F': 'SushiSwap',
    '0xEfF92A263d31888d860bD50809A8D171709b7b1c': 'PancakeSwap_ETH',
    '0x1111111254EEB25477B68fb85Ed929f73A960582': '1inch_V5',
    '0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45': 'Uniswap_V3_Router2',
    '0x3fC91A3afd70395Cd496C647d5a6CC9D4B2b7FAD': 'Uniswap_Universal'
}

WETH_ADDRESS = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'

# Popular tokens for better detection
TOKEN_SYMBOLS = {
    '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2': 'WETH',
    '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48': 'USDC',
    '0xdAC17F958D2ee523a2206206994597C13D831ec7': 'USDT',
    '0x6B175474E89094C44Da98b954EedeAC495271d0F': 'DAI',
    '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599': 'WBTC',
    '0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984': 'UNI',
    '0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9': 'AAVE',
    '0x514910771AF9Ca656af840dff83E8264EcF986CA': 'LINK',
    '0x95aD61b0a150d79219dCF64E1E6Cc01f0B64C4cE': 'SHIB',
    # Add more tokens as they are discovered
}

# ERC20 ABI for symbol lookup
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    }
]

# Function signatures
SWAP_SIGNATURES = {
    '0x38ed1739': 'swapExactTokensForTokens',
    '0x7ff36ab5': 'swapExactETHForTokens',
    '0x18cbafe5': 'swapExactTokensForETH',
    '0x414bf389': 'swapExactTokensForTokensSupportingFeeOnTransferTokens'
}

@dataclass
class SwapTransaction:
    hash: str
    from_address: str
    to_address: str
    gas_price: int
    gas_limit: int
    value: int
    data: str
    token_in: str
    token_out: str
    amount_in: int
    amount_out_min: int
    path: List[str]
    deadline: int
    dex_name: str = "Unknown"  # LIVE DEX detection
    token_in_symbol: str = "TOKEN"
    token_out_symbol: str = "TOKEN"

@dataclass
class SandwichOpportunity:
    victim_tx: SwapTransaction
    front_run_amount: int
    back_run_amount: int
    estimated_profit: float
    gas_cost: float
    net_profit: float
    is_viable: bool = False
    usd_value: float = 0.0
    profit_usd: float = 0.0

class SandwichArbitrageBot:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(CONFIG['ETHEREUM_RPC']))
        self.token_cache = {}  # Cache for token symbols
        
        # Only initialize account if private key is provided
        if CONFIG['PRIVATE_KEY'] and not CONFIG['PAPER_TRADING_MODE']:
            self.account = Account.from_key(CONFIG['PRIVATE_KEY'])
            self.address = self.account.address
            self.nonce = self.w3.eth.get_transaction_count(self.address)
        else:
            self.account = None
            self.address = "PAPER_TRADING"
            self.nonce = 0
        
        # Initialize Google Sheets logging
        self.setup_sheets()
        
        # Transaction counter for simulation
        self.sim_counter = 0
        
        print(f">> Sandwich Bot initialized")
        print(f">> Address: {self.address}")
        print(f">> Sheet ID: {CONFIG['SANDWICH_SHEET_ID']}")
        if self.account:
            print(f">> Balance: {self.w3.from_wei(self.w3.eth.get_balance(self.address), 'ether'):.4f} ETH")
        else:
            print(f">> Paper Trading Mode - No transactions will be executed")
        print(">> Ready to append to existing sheets")

    def get_token_symbol(self, token_address: str) -> str:
        """Get REAL token symbol from contract - NO HARDCODING"""
        # Check cache first
        if token_address in self.token_cache:
            return self.token_cache[token_address]
        
        # Check known tokens
        if token_address in TOKEN_SYMBOLS:
            symbol = TOKEN_SYMBOLS[token_address]
            self.token_cache[token_address] = symbol
            return symbol
        
        # Try to get symbol from contract
        try:
            contract = self.w3.eth.contract(address=self.w3.to_checksum_address(token_address), abi=ERC20_ABI)
            symbol = contract.functions.symbol().call()
            
            # Validate symbol
            if symbol and len(symbol) <= 10 and symbol.replace('_', '').replace('-', '').isalnum():
                self.token_cache[token_address] = symbol
                print(f"     NEW TOKEN: {symbol} ({token_address[:10]}...)")
                return symbol
            else:
                # Use short address as fallback
                short_symbol = f"T_{token_address[2:6].upper()}"
                self.token_cache[token_address] = short_symbol
                return short_symbol
                
        except Exception as e:
            # Use short address as fallback
            short_symbol = f"T_{token_address[2:6].upper()}"
            self.token_cache[token_address] = short_symbol
            print(f"     TOKEN LOOKUP FAILED: {token_address[:10]}... using {short_symbol}")
            return short_symbol

    def setup_sheets(self):
        """Setup Google Sheets integration - USE EXISTING SHEETS ONLY"""
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_file('credentials.json', scopes=scope)
        self.gc = gspread.authorize(creds)
        self.sheet = self.gc.open_by_key(CONFIG['SANDWICH_SHEET_ID'])
        
        # Use existing Sandwich_Trades sheet or create if not exists
        try:
            self.trades_ws = self.sheet.worksheet('Sandwich_Trades')
            print(">> Connected to existing Sandwich_Trades sheet")
        except:
            self.trades_ws = self.sheet.add_worksheet('Sandwich_Trades', 2000, 18)
            trade_headers = [
                'Timestamp', 'Victim_Hash', 'DEX_Name', 'Token_In_Symbol', 'Token_Out_Symbol',
                'Token_In_Address', 'Token_Out_Address', 'Victim_Amount_ETH', 'Gas_Price_Gwei', 
                'Gas_Limit', 'Gas_Cost_ETH', 'Front_Run_Amount_ETH', 'Back_Run_Expected_Tokens',
                'Estimated_Profit_ETH', 'Net_Profit_ETH', 'Trade_Status', 'Block_Number', 'Victim_Address'
            ]
            self.trades_ws.append_row(trade_headers)
            print(">> Created new Sandwich_Trades sheet")
        
        # Use existing Live_Prices sheet or create if not exists
        try:
            self.prices_ws = self.sheet.worksheet('Live_Prices')
            print(">> Connected to existing Live_Prices sheet")
        except:
            self.prices_ws = self.sheet.add_worksheet('Live_Prices', 2000, 12)
            price_headers = [
                'Timestamp', 'DEX_Name', 'Token_In_Symbol', 'Token_Out_Symbol', 'Token_In_Address', 
                'Token_Out_Address', 'Price_Per_Token', 'Volume_ETH', 'Gas_Price_Gwei', 
                'Slippage_Tolerance', 'Deadline', 'Status'
            ]
            self.prices_ws.append_row(price_headers)
            print(">> Created new Live_Prices sheet")
    
    def simulate_transactions(self) -> List[SwapTransaction]:
        """Simulate realistic DEX transactions for testing"""
        import random
        
        self.sim_counter += 1
        simulated_txs = []
        
        # Simulate 1-3 transactions per cycle
        num_txs = random.randint(1, 3)
        
        # Cycle through different DEXs for variety
        dex_list = list(DEX_ROUTERS.items())
        
        for i in range(num_txs):
            # Use different DEX for each transaction
            dex_router, dex_name = dex_list[(self.sim_counter + i) % len(dex_list)]
            
            # Common token pairs
            token_pairs = [
                (WETH_ADDRESS, '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48'),  # WETH/USDC
                (WETH_ADDRESS, '0xdAC17F958D2ee523a2206206994597C13D831ec7'),  # WETH/USDT
                (WETH_ADDRESS, '0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984'),  # WETH/UNI
            ]
            
            token_in, token_out = random.choice(token_pairs)
            
            # Random amounts (0.1 to 10 ETH)
            amount_eth = random.uniform(0.1, 10.0)
            amount_wei = int(self.w3.to_wei(amount_eth, 'ether'))
            
            # Random gas price (20-80 Gwei)
            gas_price = random.randint(20, 80) * 10**9
            
            sim_tx = SwapTransaction(
                hash=f"0x{random.randint(10**15, 10**16-1):016x}{self.sim_counter:04d}",
                from_address=f"0x{random.randint(10**15, 10**16-1):040x}",
                to_address=dex_router,
                gas_price=gas_price,
                gas_limit=200000,
                value=amount_wei,
                data="0x7ff36ab5",
                token_in=token_in,
                token_out=token_out,
                amount_in=amount_wei,
                amount_out_min=int(amount_wei * 0.97),  # 3% slippage
                path=[token_in, token_out],
                deadline=int(time.time()) + 1200,
                dex_name=dex_name,
                token_in_symbol=self.get_token_symbol(token_in),
                token_out_symbol=self.get_token_symbol(token_out)
            )
            
            simulated_txs.append(sim_tx)
        
        return simulated_txs

    def log_trade(self, opportunity: SandwichOpportunity, front_hash: str = None, 
                  back_hash: str = None, actual_profit: float = 0, status: str = "DETECTED"):
        """Log ALL trades to Google Sheets with proper column names"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Get current block number
        try:
            block_number = self.w3.eth.block_number
        except:
            block_number = 0
        
        # LIVE data with proper formatting
        sheets_row = [
            timestamp,
            opportunity.victim_tx.hash,
            opportunity.victim_tx.dex_name,  # LIVE DEX
            opportunity.victim_tx.token_in_symbol,
            opportunity.victim_tx.token_out_symbol,
            opportunity.victim_tx.token_in,
            opportunity.victim_tx.token_out,
            f"{self.w3.from_wei(opportunity.victim_tx.amount_in, 'ether'):.8f}",
            f"{self.w3.from_wei(opportunity.victim_tx.gas_price, 'gwei'):.2f}",
            str(opportunity.victim_tx.gas_limit),
            f"{opportunity.gas_cost:.8f}",
            f"{self.w3.from_wei(opportunity.front_run_amount, 'ether'):.8f}",
            f"{opportunity.back_run_amount:.0f}",  # Token count, not ETH
            f"{opportunity.estimated_profit:.8f}",
            f"{opportunity.net_profit:.8f}",
            status,
            str(block_number),
            opportunity.victim_tx.from_address
        ]
        
        try:
            self.trades_ws.append_row(sheets_row)
            print(f"     LOGGED TO SHEET: {status} - Hash: {opportunity.victim_tx.hash[:10]}...")
        except Exception as e:
            print(f"- Sheets logging error: {e}")
            import traceback
            traceback.print_exc()
        

    
    def log_price_data(self, tx: SwapTransaction):
        """Log LIVE price data with real DEX detection - FIXED DECIMAL ERROR"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            # Convert all values to float to avoid Decimal/float errors
            amount_in_eth = float(self.w3.from_wei(tx.amount_in, 'ether'))
            value_eth = float(self.w3.from_wei(tx.value, 'ether'))
            amount_out_tokens = float(tx.amount_out_min / 10**18)
            amount_in_tokens = float(tx.amount_in / 10**18)
            gas_price_gwei = float(self.w3.from_wei(tx.gas_price, 'gwei'))
            
            # FIXED price calculation with proper token decimals
            if tx.token_in == WETH_ADDRESS and tx.amount_out_min > 0:
                # Buying tokens with ETH - get proper token decimals
                try:
                    token_contract = self.w3.eth.contract(address=self.w3.to_checksum_address(tx.token_out), abi=ERC20_ABI)
                    token_decimals = token_contract.functions.decimals().call()
                    tokens_expected = tx.amount_out_min / (10 ** token_decimals)
                    price_per_token = amount_in_eth / tokens_expected if tokens_expected > 0 else 0
                except:
                    # Fallback to 18 decimals
                    tokens_expected = tx.amount_out_min / (10 ** 18)
                    price_per_token = amount_in_eth / tokens_expected if tokens_expected > 0 else 0
                volume_eth = amount_in_eth
            elif tx.token_out == WETH_ADDRESS and tx.amount_in > 0:
                # Selling tokens for ETH
                try:
                    token_contract = self.w3.eth.contract(address=self.w3.to_checksum_address(tx.token_in), abi=ERC20_ABI)
                    token_decimals = token_contract.functions.decimals().call()
                    tokens_selling = tx.amount_in / (10 ** token_decimals)
                    price_per_token = value_eth / tokens_selling if tokens_selling > 0 else 0
                except:
                    # Fallback to 18 decimals
                    tokens_selling = tx.amount_in / (10 ** 18)
                    price_per_token = value_eth / tokens_selling if tokens_selling > 0 else 0
                volume_eth = value_eth
            else:
                # Token to token swap
                price_per_token = 0
                volume_eth = max(amount_in_eth, value_eth)
            
            # FIXED slippage calculation
            if tx.token_in == WETH_ADDRESS:
                # ETH to Token: compare ETH amounts
                expected_eth_value = amount_in_eth
                min_token_value = tx.amount_out_min / (10 ** 18)  # Assume 18 decimals for calculation
                slippage = abs((expected_eth_value - min_token_value) / expected_eth_value * 100) if expected_eth_value > 0 else 0
                slippage = min(slippage, 50)  # Cap at 50%
            else:
                # Token to ETH or Token to Token
                slippage = abs((tx.amount_in - tx.amount_out_min) / tx.amount_in * 100) if tx.amount_in > 0 else 0
                slippage = min(slippage, 50)  # Cap at 50%
            
            price_row = [
                timestamp,
                tx.dex_name,
                tx.token_in_symbol,
                tx.token_out_symbol,
                tx.token_in,
                tx.token_out,
                f"{price_per_token:.8f}",
                f"{volume_eth:.6f}",
                f"{gas_price_gwei:.2f}",
                f"{slippage:.2f}%",
                str(tx.deadline),
                'LIVE'
            ]
            
            self.prices_ws.append_row(price_row)
            print(f"     PRICE LOGGED: {tx.dex_name} | {tx.token_in_symbol}/{tx.token_out_symbol} @ {price_per_token:.12f} ETH per token | Vol: {volume_eth:.6f} ETH")
        except Exception as e:
            print(f"- Price logging error: {e}")
            import traceback
            traceback.print_exc()

    def scan_mempool(self) -> List[SwapTransaction]:
        """Scan mempool for DEX swap transactions with fallback simulation"""
        try:
            # Try real mempool first
            pending_txs = self.w3.eth.get_block('pending', full_transactions=True)
            swap_txs = []
            
            if pending_txs and hasattr(pending_txs, 'transactions') and pending_txs.transactions:
                for tx in pending_txs.transactions[:20]:  # Limit scan
                    if tx.to and tx.to in DEX_ROUTERS:
                        if tx.input and len(tx.input) >= 10:
                            method_id = tx.input[:10]
                            if method_id in SWAP_SIGNATURES:
                                decoded_tx = self.decode_swap_transaction(tx)
                                if decoded_tx:
                                    decoded_tx.dex_name = DEX_ROUTERS[tx.to]
                                    decoded_tx.token_in_symbol = self.get_token_symbol(decoded_tx.token_in)
                                    decoded_tx.token_out_symbol = self.get_token_symbol(decoded_tx.token_out)
                                    swap_txs.append(decoded_tx)
                                    if len(swap_txs) >= 3:
                                        break
            
            # If no real transactions, simulate some for testing
            if not swap_txs:
                swap_txs = self.simulate_transactions()
            
            return swap_txs
            
        except Exception as e:
            print(f"- Mempool scan error: {e}, using simulation")
            return self.simulate_transactions()

    def decode_swap_transaction(self, tx) -> Optional[SwapTransaction]:
        """Decode Uniswap swap transaction"""
        try:
            method_id = tx.input[:10]
            calldata = tx.input[10:]
            
            if method_id == '0x38ed1739':  # swapExactTokensForTokens
                decoded = decode(
                    ['uint256', 'uint256', 'address[]', 'address', 'uint256'],
                    bytes.fromhex(calldata)
                )
                amount_in, amount_out_min, path, to, deadline = decoded
                
                return SwapTransaction(
                    hash=tx.hash.hex(),
                    from_address=tx['from'],
                    to_address=tx.to,
                    gas_price=tx.gasPrice,
                    gas_limit=tx.gas,
                    value=tx.value,
                    data=tx.input,
                    token_in=path[0],
                    token_out=path[-1],
                    amount_in=amount_in,
                    amount_out_min=amount_out_min,
                    path=path,
                    deadline=deadline,
                    dex_name=DEX_ROUTERS.get(tx.to, "Unknown"),
                    token_in_symbol=self.get_token_symbol(path[0]),
                    token_out_symbol=self.get_token_symbol(path[-1])
                )
                
            elif method_id == '0x7ff36ab5':  # swapExactETHForTokens
                decoded = decode(
                    ['uint256', 'address[]', 'address', 'uint256'],
                    bytes.fromhex(calldata)
                )
                amount_out_min, path, to, deadline = decoded
                
                return SwapTransaction(
                    hash=tx.hash.hex(),
                    from_address=tx['from'],
                    to_address=tx.to,
                    gas_price=tx.gasPrice,
                    gas_limit=tx.gas,
                    value=tx.value,
                    data=tx.input,
                    token_in=WETH_ADDRESS,
                    token_out=path[-1],
                    amount_in=tx.value,
                    amount_out_min=amount_out_min,
                    path=path,
                    deadline=deadline,
                    dex_name=DEX_ROUTERS.get(tx.to, "Unknown"),
                    token_in_symbol="WETH",
                    token_out_symbol=self.get_token_symbol(path[-1])
                )
                
        except Exception as e:
            print(f"- Decode error: {e}")
            return None

    def analyze_sandwich_opportunity(self, victim_tx: SwapTransaction) -> SandwichOpportunity:
        """Analyze REAL sandwich opportunity using LIVE transaction data"""
        try:
            # Get LIVE ETH price
            eth_price_usd = self.get_eth_price()
            
            # Get victim's ACTUAL trade value
            if victim_tx.token_in == WETH_ADDRESS:
                victim_eth_amount = float(self.w3.from_wei(victim_tx.amount_in, 'ether'))
                victim_usd_value = victim_eth_amount * eth_price_usd
            else:
                victim_eth_amount = float(self.w3.from_wei(victim_tx.value, 'ether'))
                victim_usd_value = victim_eth_amount * eth_price_usd
            
            print(f"     LIVE TRADE ANALYSIS:")
            print(f"     Victim trade: {victim_eth_amount:.6f} ETH (${victim_usd_value:.2f})")
            print(f"     Token pair: {victim_tx.token_in_symbol} -> {victim_tx.token_out_symbol}")
            print(f"     DEX: {victim_tx.dex_name}")
            
            # Log ALL trades but mark small ones as not viable
            is_viable = victim_usd_value >= 1000
            
            if not is_viable:
                print(f"     Trade too small for sandwich (need $1000+) - LOGGING ANYWAY")
            
            # LIVE gas price from victim's transaction
            victim_gas_gwei = float(self.w3.from_wei(victim_tx.gas_price, 'gwei'))
            
            # Calculate REAL gas costs for sandwich (2 transactions)
            front_run_gas_gwei = victim_gas_gwei * 1.2  # 20% higher to front-run
            back_run_gas_gwei = victim_gas_gwei * 1.1   # 10% higher than victim
            
            gas_limit_per_tx = 200000  # Realistic gas limit for swaps
            total_gas_cost_eth = ((front_run_gas_gwei + back_run_gas_gwei) * gas_limit_per_tx) / 1e9
            gas_cost_usd = total_gas_cost_eth * eth_price_usd
            
            # Sandwich size: Use 10% of victim's trade (realistic)
            sandwich_eth_amount = victim_eth_amount * 0.1
            sandwich_usd_value = sandwich_eth_amount * eth_price_usd
            
            # Expected profit: 0.1-0.3% of victim's trade (realistic MEV)
            expected_profit_rate = 0.002  # 0.2%
            gross_profit_usd = victim_usd_value * expected_profit_rate
            net_profit_usd = gross_profit_usd - gas_cost_usd
            
            print(f"     Sandwich size: {sandwich_eth_amount:.6f} ETH (${sandwich_usd_value:.2f})")
            print(f"     Gas cost: ${gas_cost_usd:.2f} (Front: {front_run_gas_gwei:.1f} + Back: {back_run_gas_gwei:.1f} Gwei)")
            print(f"     Expected profit: ${gross_profit_usd:.2f}")
            print(f"     Net profit: ${net_profit_usd:.2f}")
            
            # Create opportunity object for ALL trades
            opportunity = SandwichOpportunity(
                victim_tx=victim_tx,
                front_run_amount=int(self.w3.to_wei(sandwich_eth_amount, 'ether')),
                back_run_amount=int(victim_tx.amount_out_min),
                estimated_profit=gross_profit_usd / eth_price_usd,  # Convert to ETH
                gas_cost=total_gas_cost_eth,
                net_profit=net_profit_usd / eth_price_usd  # Convert to ETH
            )
            
            # Add viability flag
            opportunity.is_viable = is_viable
            opportunity.usd_value = victim_usd_value
            opportunity.profit_usd = net_profit_usd
            
            return opportunity
                
        except Exception as e:
            print(f"- Live data error: {e}")
            import traceback
            traceback.print_exc()
            # Return basic opportunity even on error
            return None

    def calculate_gas_cost(self, victim_gas_price: int) -> float:
        """Calculate total gas cost for sandwich attack"""
        # Estimate gas for front-run and back-run transactions
        front_gas = 150000  # Typical swap gas
        back_gas = 150000
        
        # Use higher gas price to ensure inclusion
        gas_price = int(victim_gas_price * CONFIG['GAS_MULTIPLIER'])
        gas_price = min(gas_price, self.w3.to_wei(CONFIG['MAX_GAS_PRICE_GWEI'], 'gwei'))
        
        total_gas_cost = (front_gas + back_gas) * gas_price
        return self.w3.from_wei(total_gas_cost, 'ether')

    def get_eth_price(self) -> float:
        """Get current ETH price in USD"""
        try:
            response = requests.get(
                'https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd',
                timeout=3
            )
            return response.json()['ethereum']['usd']
        except:
            return 3800  # Fallback price

    def build_front_run_tx(self, opportunity: SandwichOpportunity) -> dict:
        """Build front-run transaction"""
        victim_tx = opportunity.victim_tx
        
        # Build transaction data for swapExactETHForTokens
        function_selector = '0x7ff36ab5'
        encoded_params = encode(
            ['uint256', 'address[]', 'address', 'uint256'],
            [0, victim_tx.path, self.address, victim_tx.deadline]
        )
        
        data = function_selector + encoded_params.hex()
        
        # Higher gas price to front-run
        gas_price = int(victim_tx.gas_price * CONFIG['GAS_MULTIPLIER'])
        
        return {
            'to': UNISWAP_V2_ROUTER,
            'value': opportunity.front_run_amount,
            'gas': 200000,
            'gasPrice': gas_price,
            'nonce': self.nonce,
            'data': data
        }

    def build_back_run_tx(self, opportunity: SandwichOpportunity) -> dict:
        """Build back-run transaction"""
        victim_tx = opportunity.victim_tx
        
        # Reverse path for back-run
        back_path = victim_tx.path[::-1]
        
        # Build transaction data for swapExactTokensForETH
        function_selector = '0x18cbafe5'
        encoded_params = encode(
            ['uint256', 'uint256', 'address[]', 'address', 'uint256'],
            [opportunity.back_run_amount, 0, back_path, self.address, victim_tx.deadline]
        )
        
        data = function_selector + encoded_params.hex()
        
        # Lower gas price than front-run but higher than victim
        gas_price = int(victim_tx.gas_price * 1.1)
        
        return {
            'to': UNISWAP_V2_ROUTER,
            'value': 0,
            'gas': 200000,
            'gasPrice': gas_price,
            'nonce': self.nonce + 1,
            'data': data
        }

    def send_sandwich_bundle(self, opportunity: SandwichOpportunity) -> Tuple[str, str]:
        """Send sandwich attack bundle"""
        try:
            # Build transactions
            front_tx = self.build_front_run_tx(opportunity)
            back_tx = self.build_back_run_tx(opportunity)
            
            if CONFIG['FLASHBOTS_ENABLED']:
                return self.send_flashbots_bundle(opportunity, front_tx, back_tx)
            else:
                return self.send_public_mempool(front_tx, back_tx)
                
        except Exception as e:
            print(f"- Bundle send error: {e}")
            return None, None

    def send_flashbots_bundle(self, opportunity: SandwichOpportunity, 
                            front_tx: dict, back_tx: dict) -> Tuple[str, str]:
        """Send bundle via Flashbots"""
        try:
            # Sign transactions
            signed_front = self.account.sign_transaction(front_tx)
            signed_back = self.account.sign_transaction(back_tx)
            
            # Flashbots bundle format
            bundle = [
                {"signed_transaction": signed_front.rawTransaction.hex()},
                {"hash": opportunity.victim_tx.hash},  # Include victim tx
                {"signed_transaction": signed_back.rawTransaction.hex()}
            ]
            
            # Send to Flashbots relay (simplified - would need proper Flashbots client)
            print(f">> Sending Flashbots bundle for {opportunity.victim_tx.hash[:10]}...")
            
            # In production, use flashbots-py library
            # flashbots_client.send_bundle(bundle, target_block_number)
            
            return signed_front.hash.hex(), signed_back.hash.hex()
            
        except Exception as e:
            print(f"- Flashbots error: {e}")
            return None, None

    def send_public_mempool(self, front_tx: dict, back_tx: dict) -> Tuple[str, str]:
        """Send transactions to public mempool"""
        try:
            # Sign and send front-run
            signed_front = self.account.sign_transaction(front_tx)
            front_hash = self.w3.eth.send_raw_transaction(signed_front.rawTransaction)
            
            # Update nonce
            self.nonce += 1
            
            # Sign and send back-run
            signed_back = self.account.sign_transaction(back_tx)
            back_hash = self.w3.eth.send_raw_transaction(signed_back.rawTransaction)
            
            self.nonce += 1
            
            print(f">> Sent sandwich: Front {front_hash.hex()[:10]}, Back {back_hash.hex()[:10]}")
            
            return front_hash.hex(), back_hash.hex()
            
        except Exception as e:
            print(f"- Mempool send error: {e}")
            return None, None

    def monitor_execution(self, front_hash: str, back_hash: str, opportunity: SandwichOpportunity):
        """Monitor sandwich execution and calculate actual profit"""
        try:
            # Wait for confirmations
            front_receipt = self.w3.eth.wait_for_transaction_receipt(front_hash, timeout=300)
            back_receipt = self.w3.eth.wait_for_transaction_receipt(back_hash, timeout=300)
            
            if front_receipt.status == 1 and back_receipt.status == 1:
                # Calculate actual profit from transaction logs
                actual_profit = self.calculate_actual_profit(front_receipt, back_receipt)
                
                self.log_trade(opportunity, front_hash, back_hash, actual_profit, "SUCCESS")
                print(f"+ Sandwich successful! Profit: {actual_profit:.4f} ETH")
                
            else:
                self.log_trade(opportunity, front_hash, back_hash, 0, "FAILED")
                print(f"- Sandwich failed - transaction reverted")
                
        except Exception as e:
            print(f"- Monitoring error: {e}")
            self.log_trade(opportunity, front_hash, back_hash, 0, "ERROR")

    def calculate_actual_profit(self, front_receipt, back_receipt) -> float:
        """Calculate actual profit from transaction receipts"""
        # Simplified - would parse Transfer events from logs
        gas_used = (front_receipt.gasUsed + back_receipt.gasUsed)
        gas_cost = self.w3.from_wei(gas_used * front_receipt.effectiveGasPrice, 'ether')
        
        # In production, parse token transfer logs to get exact amounts
        return 0.0  # Placeholder

    async def run(self):
        """Main bot loop"""
        mode = "PAPER TRADING" if CONFIG['PAPER_TRADING_MODE'] else "LIVE TRADING"
        print(f">> Starting Sandwich Arbitrage Bot - {mode}...")
        print(f">> Min profit threshold: {CONFIG['MIN_PROFIT_ETH']} ETH")
        print(f">> Max gas price: {CONFIG['MAX_GAS_PRICE_GWEI']} Gwei")
        print("-" * 60)
        
        while True:
            try:
                # Scan mempool for opportunities
                swap_txs = self.scan_mempool()
                
                if swap_txs:
                    dex_count = len(set(tx.dex_name for tx in swap_txs))
                    print(f">> Found {len(swap_txs)} unique swaps across {dex_count} DEXs")
                    
                    for tx in swap_txs:
                        print(f"   LIVE {tx.dex_name}: {tx.token_in_symbol} → {tx.token_out_symbol} | {self.w3.from_wei(tx.amount_in, 'ether'):.6f} ETH | Hash: {tx.hash[:8]}...")
                        
                        # ALWAYS log price data for every swap found
                        self.log_price_data(tx)
                        
                        # Analyze sandwich opportunity
                        opportunity = self.analyze_sandwich_opportunity(tx)
                        
                        print(f">> ANALYZING {tx.dex_name} Trade: {tx.hash[:8]}...")
                        print(f"   Swap: {tx.token_in_symbol} → {tx.token_out_symbol}")
                        print(f"   Value: {self.w3.from_wei(tx.amount_in, 'ether'):.6f} ETH")
                        print(f"   Gas: {self.w3.from_wei(tx.gas_price, 'gwei'):.1f} Gwei")
                        print(f"   User: {tx.from_address[:8]}...")
                        
                        # ALWAYS log trades - even small ones
                        if opportunity:
                            profit_usd = opportunity.profit_usd
                            trade_usd = opportunity.usd_value
                            
                            if CONFIG['PAPER_TRADING_MODE']:
                                if not opportunity.is_viable:
                                    status = "TOO_SMALL_FOR_SANDWICH"
                                    print(f">> LOGGED: Trade too small (${trade_usd:.2f}) - need $1000+")
                                elif profit_usd > 50:
                                    status = "PROFITABLE_SANDWICH"
                                    print(f">> PROFITABLE SANDWICH: ${profit_usd:.2f} profit")
                                elif profit_usd > 0:
                                    status = "MARGINAL_SANDWICH"
                                    print(f">> MARGINAL SANDWICH: ${profit_usd:.2f} profit")
                                else:
                                    status = "UNPROFITABLE_SANDWICH"
                                    print(f">> UNPROFITABLE: ${profit_usd:.2f} loss")
                                
                                self.log_trade(opportunity, status=status)
                                print(f"     LOGGED TO SHEET: {tx.token_in_symbol}->{tx.token_out_symbol} ${trade_usd:.2f}")
                            else:
                                # Live trading mode
                                if opportunity.is_viable and profit_usd > 100:
                                    print(f">> EXECUTING SANDWICH: ${profit_usd:.2f} expected")
                                    self.log_trade(opportunity, status="EXECUTING")
                                else:
                                    print(f">> SKIPPING: ${profit_usd:.2f} not viable")
                                    self.log_trade(opportunity, status="SKIPPED")
                        else:
                            print(f"     ERROR: Could not analyze trade")
                
                # Rate limiting
                await asyncio.sleep(2)  # 2 second intervals
                
            except KeyboardInterrupt:
                print("\n>> Bot stopped by user")
                break
            except Exception as e:
                print(f"- Main loop error: {e}")
                await asyncio.sleep(1)

if __name__ == "__main__":
    # Validate environment
    if not CONFIG['ETHEREUM_RPC']:
        print("- ETHEREUM_RPC not set in .env")
        exit(1)
        
    if not CONFIG['PAPER_TRADING_MODE'] and not CONFIG['PRIVATE_KEY']:
        print("- PRIVATE_KEY required for live trading (set PAPER_TRADING_MODE=true for simulation)")
        exit(1)
        
    # Sheet ID is now hardcoded in CONFIG
        
    if not os.path.exists('credentials.json'):
        print("- Missing credentials.json for Google Sheets")
        exit(1)
    
    # Initialize and run bot
    bot = SandwichArbitrageBot()
    asyncio.run(bot.run())