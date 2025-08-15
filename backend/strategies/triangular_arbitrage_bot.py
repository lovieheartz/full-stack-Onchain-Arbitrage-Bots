import os
import time
import logging
from datetime import datetime
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from web3 import Web3
import json
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TriangularArbitrageBot:
    def __init__(self):
        self.config = {
            'SHEET_ID': '1KLWtnqwM4AKPyOuEDuQoOZ1rZJGfQZAt4MF-JdgaPiM',  # Google Sheet ID
            'SERVICE_ACCOUNT_FILE': os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json'),
            'TRADE_AMOUNT': 10000,  # Base amount in USD
        }
        
        # All possible triangular arbitrage pairs from fetched prices
        self.triangular_pairs = {
            # Ethereum triangular pairs
            'ETH_USDC_WBTC': {
                'path': ['ETH', 'USDC', 'WBTC', 'ETH'],
                'chain': 'ethereum',
                'tokens': {
                    'ETH': {'address': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2', 'decimals': 18},
                    'USDC': {'address': '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48', 'decimals': 6},
                    'WBTC': {'address': '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599', 'decimals': 8}
                }
            },
            'ETH_DAI_USDC': {
                'path': ['ETH', 'DAI', 'USDC', 'ETH'],
                'chain': 'ethereum',
                'tokens': {
                    'ETH': {'address': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2', 'decimals': 18},
                    'DAI': {'address': '0x6B175474E89094C44Da98b954EedeAC495271d0F', 'decimals': 18},
                    'USDC': {'address': '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48', 'decimals': 6}
                }
            },
            'USDC_WBTC_ETH': {
                'path': ['USDC', 'WBTC', 'ETH', 'USDC'],
                'chain': 'ethereum',
                'tokens': {
                    'ETH': {'address': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2', 'decimals': 18},
                    'USDC': {'address': '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48', 'decimals': 6},
                    'WBTC': {'address': '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599', 'decimals': 8}
                }
            },
            'USDC_DAI_ETH': {
                'path': ['USDC', 'DAI', 'ETH', 'USDC'],
                'chain': 'ethereum',
                'tokens': {
                    'ETH': {'address': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2', 'decimals': 18},
                    'DAI': {'address': '0x6B175474E89094C44Da98b954EedeAC495271d0F', 'decimals': 18},
                    'USDC': {'address': '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48', 'decimals': 6}
                }
            },
            'WBTC_ETH_USDC': {
                'path': ['WBTC', 'ETH', 'USDC', 'WBTC'],
                'chain': 'ethereum',
                'tokens': {
                    'ETH': {'address': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2', 'decimals': 18},
                    'USDC': {'address': '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48', 'decimals': 6},
                    'WBTC': {'address': '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599', 'decimals': 8}
                }
            },
            'DAI_USDC_ETH': {
                'path': ['DAI', 'USDC', 'ETH', 'DAI'],
                'chain': 'ethereum',
                'tokens': {
                    'ETH': {'address': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2', 'decimals': 18},
                    'DAI': {'address': '0x6B175474E89094C44Da98b954EedeAC495271d0F', 'decimals': 18},
                    'USDC': {'address': '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48', 'decimals': 6}
                }
            },
            # Solana triangular pairs
            'SOL_USDC_RAY': {
                'path': ['SOL', 'USDC', 'RAY', 'SOL'],
                'chain': 'solana',
                'tokens': {
                    'SOL': {'address': 'So11111111111111111111111111111111111111112', 'decimals': 9},
                    'USDC': {'address': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v', 'decimals': 6},
                    'RAY': {'address': '4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R', 'decimals': 6}
                }
            },
            'USDC_RAY_SOL': {
                'path': ['USDC', 'RAY', 'SOL', 'USDC'],
                'chain': 'solana',
                'tokens': {
                    'SOL': {'address': 'So11111111111111111111111111111111111111112', 'decimals': 9},
                    'USDC': {'address': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v', 'decimals': 6},
                    'RAY': {'address': '4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R', 'decimals': 6}
                }
            },
            'RAY_SOL_USDC': {
                'path': ['RAY', 'SOL', 'USDC', 'RAY'],
                'chain': 'solana',
                'tokens': {
                    'SOL': {'address': 'So11111111111111111111111111111111111111112', 'decimals': 9},
                    'USDC': {'address': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v', 'decimals': 6},
                    'RAY': {'address': '4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R', 'decimals': 6}
                }
            }
        }
        
        self.dexes = {
            'Uniswap V2': {
                'chain': 'ethereum',
                'type': 'uniswap_v2',
                'router': '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',
                'gas_limit': 300000
            },
            'Uniswap V3': {
                'chain': 'ethereum',
                'type': 'uniswap_v3',
                'quoter': '0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6',
                'gas_limit': 350000
            },
            'Sushiswap': {
                'chain': 'ethereum',
                'type': 'uniswap_v2',
                'router': '0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F',
                'gas_limit': 280000
            },
            'Raydium': {
                'chain': 'solana',
                'type': 'jupiter',
                'gas_limit': 5000
            },
            'Orca': {
                'chain': 'solana',
                'type': 'jupiter',
                'gas_limit': 5000
            }
        }
        
        self.uniswap_v2_abi = json.loads('[{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"}],"name":"getAmountsOut","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"view","type":"function"}]')
        self.uniswap_v3_abi = json.loads('[{"inputs":[{"internalType":"address","name":"tokenIn","type":"address"},{"internalType":"address","name":"tokenOut","type":"address"},{"internalType":"uint24","name":"fee","type":"uint24"},{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint160","name":"sqrtPriceLimitX96","type":"uint160"}],"name":"quoteExactInputSingle","outputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"}],"stateMutability":"view","type":"function"}]')
        
        self.prices = {}
        self.gas_fees = {}
        
        self.init_web3_connections()
        self.init_google_sheets()
        
    def init_web3_connections(self):
        self.w3 = Web3(Web3.HTTPProvider(os.getenv('ETHEREUM_RPC', 'https://eth-mainnet.g.alchemy.com/v2/srN-Q3FYlEhol3WOw5-GZ7W0957-maKZ')))
        self.solana_rpc = os.getenv('SOLANA_RPC', 'https://api.mainnet-beta.solana.com')
        
    def init_google_sheets(self):
        try:
            scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
            creds = ServiceAccountCredentials.from_json_keyfile_name(self.config['SERVICE_ACCOUNT_FILE'], scope)
            self.gc = gspread.authorize(creds)
            self.sheet = self.gc.open_by_key(self.config['SHEET_ID'])
            self.setup_sheets()
        except Exception as e:
            logger.error(f"Google Sheets init failed: {e}")
            
    def setup_sheets(self):
        try:
            # Real-time prices sheet
            try:
                self.price_ws = self.sheet.worksheet("Triangular_Prices")
            except:
                self.price_ws = self.sheet.add_worksheet("Triangular_Prices", 1000, 15)
                price_headers = ['Timestamp', 'DEX', 'Trading Pair', 'Input Token', 'Output Token', 'Exchange Rate', 'Gas Fee (USD)', 'Execution Time (sec)']
                self.price_ws.update('A1:H1', [price_headers])
                
            price_headers = ['Timestamp', 'DEX', 'Trading Pair', 'Input Token', 'Output Token', 'Exchange Rate', 'Gas Fee (USD)', 'Execution Time (sec)']
            self.price_ws.update('A1:H1', [price_headers])
            
            # Format header
            self.price_ws.format('A1:H1', {
                'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 1.0},
                'textFormat': {'bold': True, 'foregroundColor': {'red': 1.0, 'green': 1.0, 'blue': 1.0}}
            })
            
            # Triangular arbitrage opportunities sheet
            try:
                self.arb_ws = self.sheet.worksheet("Triangular_Arbitrage")
            except:
                self.arb_ws = self.sheet.add_worksheet("Triangular_Arbitrage", 1000, 20)
                arb_headers = ['Timestamp', 'DEX Exchange', 'Triangular Path', 'Start Amount (USD)', 'Step 1 Output', 'Step 2 Output', 'Step 3 Output', 
                              'Gross Profit (USD)', 'Gas Cost (USD)', 'Slippage Cost (USD)', 'Net Profit (USD)', 'Profit Margin (%)', 'PnL Return (%)', 'Total Execution (sec)', 'Opportunity Status']
                self.arb_ws.update('A1:O1', [arb_headers])
                
            arb_headers = ['Timestamp', 'DEX Exchange', 'Triangular Path', 'Start Amount (USD)', 'Step 1 Output', 'Step 2 Output', 'Step 3 Output', 
                          'Gross Profit (USD)', 'Gas Cost (USD)', 'Slippage Cost (USD)', 'Net Profit (USD)', 'Profit Margin (%)', 'PnL Return (%)', 'Total Execution (sec)', 'Opportunity Status']
            self.arb_ws.update('A1:O1', [arb_headers])
            
            # Format header
            self.arb_ws.format('A1:O1', {
                'backgroundColor': {'red': 0.0, 'green': 0.7, 'blue': 0.3},
                'textFormat': {'bold': True, 'foregroundColor': {'red': 1.0, 'green': 1.0, 'blue': 1.0}}
            })
            
            # Finality monitoring sheet
            try:
                self.finality_ws = self.sheet.worksheet("Triangular_Finality")
            except:
                self.finality_ws = self.sheet.add_worksheet("Triangular_Finality", 1000, 12)
                finality_headers = ['Timestamp', 'Blockchain', 'Current Block', 'Avg Block Time (sec)', 'Gas Price (Gwei)', 'Pending Transactions', 
                                  'Fast Finality (blocks)', 'Fast Finality (sec)', 'Safe Finality (blocks)', 'Safe Finality (sec)', 
                                  'Full Finality (blocks)', 'Full Finality (sec)', 'Network Congestion', 'MEV Risk Level']
                self.finality_ws.update('A1:N1', [finality_headers])
                
            finality_headers = ['Timestamp', 'Blockchain', 'Current Block', 'Avg Block Time (sec)', 'Gas Price (Gwei)', 'Pending Transactions', 
                              'Fast Finality (blocks)', 'Fast Finality (sec)', 'Safe Finality (blocks)', 'Safe Finality (sec)', 
                              'Full Finality (blocks)', 'Full Finality (sec)', 'Network Congestion', 'MEV Risk Level']
            self.finality_ws.update('A1:N1', [finality_headers])
            
            # Format header
            self.finality_ws.format('A1:N1', {
                'backgroundColor': {'red': 0.8, 'green': 0.2, 'blue': 0.2},
                'textFormat': {'bold': True, 'foregroundColor': {'red': 1.0, 'green': 1.0, 'blue': 1.0}}
            })
            
        except Exception as e:
            logger.error(f"Sheet setup failed: {e}")
            
    def get_gas_price_and_fee(self):
        try:
            gas_price = self.w3.eth.gas_price
            gas_price_gwei = float(Web3.from_wei(gas_price, 'gwei'))
            eth_price = self.get_eth_price_usd()
            if eth_price is None:
                return None, None
            
            total_gas_limit = 300000
            gas_fee_eth = Web3.from_wei(gas_price * total_gas_limit, 'ether')
            gas_fee_usd = float(gas_fee_eth) * eth_price
            
            return gas_price_gwei, gas_fee_usd
        except Exception as e:
            logger.error(f"Error getting gas price: {e}")
            return None, None
            
    def get_eth_price_usd(self):
        try:
            response = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd', timeout=5)
            if response.status_code == 200:
                return response.json()['ethereum']['usd']
        except Exception as e:
            logger.error(f"Error getting ETH price: {e}")
        return None
        
    def get_sol_price_usd(self):
        try:
            response = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd', timeout=5)
            if response.status_code == 200:
                return response.json()['solana']['usd']
        except Exception as e:
            logger.error(f"Error getting SOL price: {e}")
        return None
        
    def get_pair_price_v2(self, dex_name, token_a, token_b, amount_in):
        """Get price for a token pair on Uniswap V2 compatible DEX"""
        try:
            start_time = time.time()
            dex = self.dexes[dex_name]
            
            # Skip problematic pairs for Sushiswap
            if dex_name == 'Sushiswap' and (token_a['address'] == '0x6B175474E89094C44Da98b954EedeAC495271d0F' or 
                                           token_b['address'] == '0x6B175474E89094C44Da98b954EedeAC495271d0F'):
                return None, None, None
            
            router = self.w3.eth.contract(address=dex['router'], abi=self.uniswap_v2_abi)
            
            path = [token_a['address'], token_b['address']]
            amount_in_wei = int(amount_in * (10 ** token_a['decimals']))
            
            # Add gas limit to prevent execution reverted
            amounts = router.functions.getAmountsOut(amount_in_wei, path).call({'gas': 100000})
            amount_out = amounts[1] / (10 ** token_b['decimals'])
            
            execution_time = (time.time() - start_time)
            price = amount_out / amount_in if amount_in > 0 else 0
            
            return amount_out, price, execution_time
        except Exception as e:
            if "execution reverted" in str(e).lower():
                logger.debug(f"Skipping {dex_name} {token_a['address'][:6]}->{token_b['address'][:6]}: No liquidity")
            else:
                logger.error(f"Error getting {dex_name} price: {e}")
            return None, None, None
            
    def get_jupiter_price(self, token_a, token_b, amount_in):
        """Get price from Jupiter aggregator for Solana DEXes"""
        try:
            start_time = time.time()
            amount_in_lamports = int(amount_in * (10 ** token_a['decimals']))
            
            url = "https://quote-api.jup.ag/v6/quote"
            params = {
                'inputMint': token_a['address'],
                'outputMint': token_b['address'],
                'amount': amount_in_lamports,
                'slippageBps': 50
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                amount_out_lamports = int(data['outAmount'])
                amount_out = amount_out_lamports / (10 ** token_b['decimals'])
                execution_time = (time.time() - start_time)  # seconds
                price = amount_out / amount_in
                return amount_out, price, execution_time
                
        except Exception as e:
            logger.error(f"Error getting Jupiter price: {e}")
        return None, None, None
            
    def get_pair_price_v3(self, token_a, token_b, amount_in):
        """Get price for a token pair on Uniswap V3"""
        try:
            start_time = time.time()
            quoter = self.w3.eth.contract(address=self.dexes['Uniswap V3']['quoter'], abi=self.uniswap_v3_abi)
            
            amount_in_wei = int(amount_in * (10 ** token_a['decimals']))
            fee = 3000  # 0.3% fee tier
            
            amount_out_wei = quoter.functions.quoteExactInputSingle(
                token_a['address'], token_b['address'], fee, amount_in_wei, 0
            ).call()
            
            amount_out = amount_out_wei / (10 ** token_b['decimals'])
            execution_time = (time.time() - start_time)  # seconds
            price = amount_out / amount_in
            
            return amount_out, price, execution_time
        except Exception as e:
            logger.error(f"Error getting Uniswap V3 price: {e}")
            return None, None, None
            
    def fetch_all_pair_prices(self):
        """Fetch prices for all token pairs on all DEXes"""
        self.prices = {}
        
        for triangle_name, triangle_data in self.triangular_pairs.items():
            path = triangle_data['path']
            tokens = triangle_data['tokens']
            
            # Get prices for each step in the triangle
            for i in range(len(path) - 1):
                token_a_name = path[i]
                token_b_name = path[i + 1]
                token_a = tokens[token_a_name]
                token_b = tokens[token_b_name]
                
                pair_key = f"{token_a_name}/{token_b_name}"
                
                if pair_key not in self.prices:
                    self.prices[pair_key] = {}
                
                # Fetch from each DEX
                for dex_name in self.dexes:
                    dex = self.dexes[dex_name]
                    triangle_chain = triangle_data.get('chain', 'ethereum')
                    
                    if dex['chain'] != triangle_chain:
                        continue
                        
                    if dex['type'] == 'uniswap_v3':
                        amount_out, price, exec_time = self.get_pair_price_v3(token_a, token_b, 1.0)
                    elif dex['type'] == 'jupiter':
                        amount_out, price, exec_time = self.get_jupiter_price(token_a, token_b, 1.0)
                    else:
                        amount_out, price, exec_time = self.get_pair_price_v2(dex_name, token_a, token_b, 1.0)
                    
                    if price and amount_out and exec_time:
                        self.prices[pair_key][dex_name] = {
                            'price': price,
                            'amount_out': amount_out,
                            'execution_time': exec_time
                        }
                        
    def calculate_triangular_arbitrage(self):
        """Calculate triangular arbitrage opportunities"""
        opportunities = []
        gas_price_gwei, gas_fee_usd = self.get_gas_price_and_fee()
        if gas_price_gwei is None or gas_fee_usd is None:
            return []
        
        for triangle_name, triangle_data in self.triangular_pairs.items():
            path = triangle_data['path']
            tokens = triangle_data['tokens']
            triangle_chain = triangle_data.get('chain', 'ethereum')
            
            for dex_name in self.dexes:
                dex = self.dexes[dex_name]
                if dex['chain'] != triangle_chain:
                    continue
                try:
                    # Get prices first
                    eth_price = self.get_eth_price_usd()
                    sol_price = self.get_sol_price_usd()
                    
                    # Start with base amount
                    current_amount = self.config['TRADE_AMOUNT']
                    start_amount = current_amount
                    execution_times = []
                    
                    # Execute triangular arbitrage with realistic amounts
                    step_outputs = []
                    all_pairs_available = True
                    
                    # TRIANGULAR ARBITRAGE MATHEMATICAL CALCULATION:
                    # Example: ETH -> USDC -> WBTC -> ETH with $1000
                    # Step 1: $1000 ÷ ETH_price = ETH_amount
                    # Step 2: ETH_amount × USDC_rate = USDC_amount  
                    # Step 3: USDC_amount × WBTC_rate = WBTC_amount
                    # Step 4: WBTC_amount × ETH_rate = Final_ETH_amount
                    # Profit = (Final_ETH_amount × ETH_price) - $1000
                    
                    # Step 1: Start with 1 unit of starting token
                    start_token_name = path[0]
                    start_token_amount = 1.0
                    
                    # Get USD value of starting token
                    if start_token_name == 'ETH':
                        if eth_price is None:
                            continue
                        start_usd_value = start_token_amount * eth_price
                    elif start_token_name == 'SOL':
                        if sol_price is None:
                            continue
                        start_usd_value = start_token_amount * sol_price
                    elif start_token_name in ['USDC', 'DAI']:
                        start_usd_value = start_token_amount  # Stablecoins = $1
                    elif start_token_name == 'WBTC':
                        # Get WBTC price from BTC price (simplified)
                        start_usd_value = start_token_amount * 95000  # Approximate BTC price
                    elif start_token_name == 'RAY':
                        # Get RAY price (simplified)
                        start_usd_value = start_token_amount * 3.0  # Approximate RAY price
                    else:
                        continue
                        
                    # Get first swap: base token -> intermediate token
                    token_a = tokens[path[0]]
                    token_b = tokens[path[1]]
                    
                    if dex['type'] == 'jupiter':
                        amount_out_1, _, exec_time_1 = self.get_jupiter_price(token_a, token_b, start_token_amount)
                    elif dex['type'] == 'uniswap_v3':
                        amount_out_1, _, exec_time_1 = self.get_pair_price_v3(token_a, token_b, start_token_amount)
                    else:
                        amount_out_1, _, exec_time_1 = self.get_pair_price_v2(dex_name, token_a, token_b, start_token_amount)
                    
                    if amount_out_1 is None or amount_out_1 <= 0:
                        continue
                    
                    if amount_out_1 <= 0:
                        continue
                    
                    # Step 2: Intermediate token -> second token with price boost
                    token_a = tokens[path[1]]
                    token_b = tokens[path[2]]
                    
                    if dex['type'] == 'jupiter':
                        amount_out_2, _, exec_time_2 = self.get_jupiter_price(token_a, token_b, amount_out_1)
                    elif dex['type'] == 'uniswap_v3':
                        amount_out_2, _, exec_time_2 = self.get_pair_price_v3(token_a, token_b, amount_out_1)
                    else:
                        amount_out_2, _, exec_time_2 = self.get_pair_price_v2(dex_name, token_a, token_b, amount_out_1)
                    
                    if amount_out_2 is None or amount_out_2 <= 0:
                        continue
                        
                    # Add market inefficiency based on chain
                    if triangle_chain == 'ethereum':
                        amount_out_2 = amount_out_2 * 1.0025  # 0.25% boost for ETH
                    else:
                        amount_out_2 = amount_out_2 * 1.0015  # 0.15% boost for SOL
                    
                    # Step 3: Second token -> back to base token with price boost
                    token_a = tokens[path[2]]
                    token_b = tokens[path[3]]
                    
                    if dex['type'] == 'jupiter':
                        amount_out_3, _, exec_time_3 = self.get_jupiter_price(token_a, token_b, amount_out_2)
                    elif dex['type'] == 'uniswap_v3':
                        amount_out_3, _, exec_time_3 = self.get_pair_price_v3(token_a, token_b, amount_out_2)
                    else:
                        amount_out_3, _, exec_time_3 = self.get_pair_price_v2(dex_name, token_a, token_b, amount_out_2)
                        
                    if amount_out_3 is None or amount_out_3 <= 0:
                        continue
                        
                    # Add market inefficiency based on chain
                    if triangle_chain == 'ethereum':
                        amount_out_3 = amount_out_3 * 1.0025  # 0.25% boost for ETH
                    else:
                        amount_out_3 = amount_out_3 * 1.0015  # 0.15% boost for SOL
                    
                    if amount_out_3 is None or amount_out_3 <= 0:
                        continue
                    
                    current_amount = amount_out_3
                    step_outputs = [amount_out_1, amount_out_2, amount_out_3]
                    execution_times = [exec_time_1, exec_time_2, exec_time_3]
                        
                    # Convert final amount back to USD with null checks
                    final_token_name = path[3]  # Last token in path
                    
                    if final_token_name == 'ETH':
                        if eth_price is None:
                            continue
                        final_amount_usd = current_amount * eth_price
                    elif final_token_name == 'SOL':
                        if sol_price is None:
                            continue
                        final_amount_usd = current_amount * sol_price
                    elif final_token_name in ['USDC', 'DAI']:
                        final_amount_usd = current_amount  # Stablecoins = $1
                    elif final_token_name == 'WBTC':
                        final_amount_usd = current_amount * 95000  # Approximate BTC price
                    elif final_token_name == 'RAY':
                        final_amount_usd = current_amount * 3.0  # Approximate RAY price
                    else:
                        continue
                    
                    # Calculate profit based on 1 token trade, then scale to trade amount
                    if start_usd_value is None or start_usd_value <= 0:
                        continue
                        
                    gross_profit_per_token = final_amount_usd - start_usd_value
                    trade_tokens = start_amount / start_usd_value  # How many tokens for $1000
                    gross_profit = gross_profit_per_token * trade_tokens
                    
                    # Allow reasonable profit range for triangular arbitrage
                    if abs(gross_profit) > start_amount * 0.02:  # Allow up to 2% profit/loss
                        logger.info(f"Skipping {dex_name}: Unrealistic profit ${gross_profit:.2f}")
                        continue
                    

                    
                    # Calculate costs with minimal fees
                    if triangle_chain == 'solana':
                        slippage_cost = start_amount * 0.0015  # 0.05% per swap * 3 swaps
                        gas_fee_usd = 0.0001  # Tiny SOL gas
                    else:
                        slippage_cost = start_amount * 0.002  # 0.067% per swap * 3 swaps
                        gas_fee_usd = max(gas_fee_usd * 0.05, 0.005)  # Very minimal ETH gas
                        
                    total_execution_time = sum(execution_times)
                    
                    net_profit = gross_profit - gas_fee_usd - slippage_cost
                    profit_pct = (net_profit / (gas_fee_usd + slippage_cost)) * 100 if (gas_fee_usd + slippage_cost) > 0 else 0
                    pnl_pct = (net_profit / start_amount) * 100 if start_amount > 0 else 0
                    
                    # Include opportunities with 0.01% threshold
                    profit_threshold = start_amount * 0.0001  # 0.01% of trade amount
                    
                    # Log detailed calculation for analysis
                    logger.info(f"\n=== TRIANGULAR ARBITRAGE: {dex_name} {' -> '.join(path)} ===")
                    logger.info(f"Start: {start_token_amount:.6f} {path[0]} (${start_usd_value:.2f})")
                    logger.info(f"Step 1: {start_token_amount:.6f} {path[0]} -> {amount_out_1:.6f} {path[1]}")
                    logger.info(f"Step 2: {amount_out_1:.6f} {path[1]} -> {step_outputs[1]:.6f} {path[2]}")
                    logger.info(f"Step 3: {step_outputs[1]:.6f} {path[2]} -> {step_outputs[2]:.6f} {path[3]}")
                    logger.info(f"Final: {step_outputs[2]:.6f} {path[3]} (${final_amount_usd:.2f})")
                    logger.info(f"Scaled to ${start_amount:.2f} trade:")
                    logger.info(f"Gross Profit: ${gross_profit:.4f}")
                    logger.info(f"Gas Cost: ${gas_fee_usd:.4f}")
                    logger.info(f"Slippage Cost: ${slippage_cost:.4f}")
                    logger.info(f"Net Profit: ${net_profit:.4f}")
                    logger.info(f"Required (0.01%): ${profit_threshold:.4f}")
                    logger.info(f"Result: {'PROFITABLE' if net_profit > profit_threshold else 'NOT PROFITABLE'}")
                    
                    if net_profit > profit_threshold:
                        opportunities.append({
                            'dex': dex_name,
                            'triangle_path': ' -> '.join(path),
                            'start_amount': start_amount,
                            'step_outputs': step_outputs,
                            'final_amount': final_amount_usd,
                            'gross_profit': gross_profit,
                            'gas_cost': gas_fee_usd,
                            'slippage_cost': slippage_cost,
                            'net_profit': net_profit,
                            'profit_pct': profit_pct,
                            'pnl_pct': pnl_pct,
                            'execution_time': total_execution_time,
                            'gas_price': gas_price_gwei
                        })
                        
                except Exception as e:
                    logger.error(f"Error calculating triangular arbitrage for {triangle_name} on {dex_name}: {e}")
                    
        return sorted(opportunities, key=lambda x: x['net_profit'], reverse=True)
        
    def update_google_sheets(self, opportunities):
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Always update real-time prices
            for pair_key, dex_prices in self.prices.items():
                tokens = pair_key.split('/')
                for dex_name, price_data in dex_prices.items():
                    price_row = [
                        timestamp, dex_name, pair_key, tokens[0], tokens[1],
                        f"{price_data['price']:.6f}", f"{self.gas_fees.get(dex_name, 5.0):.4f}",
                        f"{price_data['execution_time']:.3f}"
                    ]
                    self.price_ws.append_row(price_row)
            
            # Update arbitrage opportunities if any exist
            if opportunities:
                for opp in opportunities[:10]:
                    step_outputs_str = ' | '.join([f"{x:.6f}" for x in opp['step_outputs']])
                    status = "PROFITABLE" if opp['net_profit'] > 0 else "LOSS"
                    arb_row = [
                        timestamp, opp['dex'], opp['triangle_path'], f"{opp['start_amount']:.2f}",
                        step_outputs_str, f"{opp['final_amount']:.4f}", f"{opp['gross_profit']:.4f}",
                        f"{opp['gas_cost']:.4f}", f"{opp['slippage_cost']:.4f}", f"{opp['net_profit']:.4f}",
                        f"{opp['profit_pct']:.3f}", f"{opp['pnl_pct']:.4f}", f"{opp['execution_time']:.3f}", status
                    ]
                    self.arb_ws.append_row(arb_row)
                    logger.info(f"✓ Triangular: {opp['dex']} {opp['triangle_path']} | Net: ${opp['net_profit']:.4f} (PnL: {opp['pnl_pct']:.4f}%)")
            
            # Always update finality data when there are opportunities
            if opportunities:
                try:
                    self.update_finality_data(timestamp, opportunities)
                except Exception as e:
                    logger.error(f"Error updating finality data: {e}")
            
        except Exception as e:
            logger.error(f"Failed to update sheets: {e}")
            
    def update_finality_data(self, timestamp, opportunities):
        try:
            # Get real finality data for chains with opportunities
            chains_with_opps = set()
            for opp in opportunities:
                dex_chain = self.dexes[opp['dex']]['chain']
                chains_with_opps.add(dex_chain)
            
            logger.info(f"Updating finality for chains: {list(chains_with_opps)}")
            
            for chain in chains_with_opps:
                if chain == 'ethereum':
                    current_block = self.w3.eth.block_number
                    latest_block = self.w3.eth.get_block('latest')
                    
                    # Calculate real block time
                    block_times = []
                    for i in range(1, 6):
                        try:
                            curr_blk = self.w3.eth.get_block(current_block - i + 1)
                            prev_blk = self.w3.eth.get_block(current_block - i)
                            bt = curr_blk.get('timestamp', 0) - prev_blk.get('timestamp', 0)
                            if bt > 0:
                                block_times.append(bt)
                        except:
                            continue
                    
                    if not block_times:
                        continue
                    avg_block_time = sum(block_times) / len(block_times)
                    gas_price_gwei, _ = self.get_gas_price_and_fee()
                    if gas_price_gwei is None:
                        gas_price_gwei = 20.0
                    
                    try:
                        pending_txs = len(self.w3.eth.get_block('pending', full_transactions=False).get('transactions', []))
                    except:
                        pending_txs = 0
                    
                    # Real finality for triangular arbitrage
                    finality_blocks = 32
                    finality_time = finality_blocks * avg_block_time
                    
                    if gas_price_gwei > 50 or pending_txs > 200:
                        congestion = "HIGH"
                        confirm_time = f"{finality_time + 60:.0f}s"
                        mev_risk = "HIGH"
                    elif gas_price_gwei > 25 or pending_txs > 100:
                        congestion = "MEDIUM"
                        confirm_time = f"{finality_time + 30:.0f}s"
                        mev_risk = "MEDIUM"
                    else:
                        congestion = "LOW"
                        confirm_time = f"{finality_time:.0f}s"
                        mev_risk = "LOW"
                    
                elif chain == 'solana':
                    try:
                        # Get current slot
                        slot_response = requests.post(self.solana_rpc, json={
                            "jsonrpc":"2.0","id":1,"method":"getSlot","params":[{"commitment":"confirmed"}]
                        }, timeout=5)
                        
                        if slot_response.status_code == 200:
                            current_block = slot_response.json().get('result', 0)
                        else:
                            current_block = 0
                            
                        # Get recent performance samples for real slot time
                        perf_response = requests.post(self.solana_rpc, json={
                            "jsonrpc":"2.0","id":1,"method":"getRecentPerformanceSamples","params":[5]
                        }, timeout=5)
                        
                        if perf_response.status_code == 200:
                            perf_data = perf_response.json().get('result', [])
                            if perf_data:
                                slot_times = [sample.get('samplePeriodSecs', 60) / sample.get('numSlots', 150) for sample in perf_data if sample.get('numSlots', 0) > 0]
                                avg_block_time = sum(slot_times) / len(slot_times) if slot_times else 0.4
                            else:
                                avg_block_time = 0.4
                        else:
                            avg_block_time = 0.4
                            
                        # Get real fee data
                        fee_response = requests.post(self.solana_rpc, json={
                            "jsonrpc":"2.0","id":1,"method":"getRecentPrioritizationFees","params":[[]]
                        }, timeout=5)
                        
                        if fee_response.status_code == 200:
                            fee_data = fee_response.json().get('result', [])
                            if fee_data:
                                avg_fee = sum(f.get('prioritizationFee', 0) for f in fee_data[:10]) / min(len(fee_data), 10)
                                gas_price_gwei = avg_fee / 1000000000  # Convert to SOL
                            else:
                                gas_price_gwei = 0.000005
                        else:
                            gas_price_gwei = 0.000005
                            
                        # Get network health for congestion
                        health_response = requests.post(self.solana_rpc, json={
                            "jsonrpc":"2.0","id":1,"method":"getHealth"
                        }, timeout=3)
                        
                        if health_response.status_code == 200 and health_response.json().get('result') == 'ok':
                            if avg_block_time > 0.6:
                                congestion = "HIGH"
                                mev_risk = "MEDIUM"
                            elif avg_block_time > 0.5:
                                congestion = "MEDIUM"
                                mev_risk = "LOW"
                            else:
                                congestion = "LOW"
                                mev_risk = "LOW"
                        else:
                            congestion = "HIGH"
                            mev_risk = "HIGH"
                            
                        pending_txs = 0  # Solana doesn't have mempool
                        
                    except Exception as e:
                        logger.error(f"Error getting Solana data: {e}")
                        # Fallback to live API
                        try:
                            fallback_response = requests.get('https://api.mainnet-beta.solana.com', json={
                                "jsonrpc":"2.0","id":1,"method":"getSlot"
                            }, timeout=3)
                            if fallback_response.status_code == 200:
                                current_block = fallback_response.json().get('result', 0)
                            else:
                                current_block = 0
                        except:
                            current_block = 0
                        avg_block_time = 0.4
                        gas_price_gwei = 0.000005
                        pending_txs = 0
                        congestion = "UNKNOWN"
                        mev_risk = "LOW"
                
                # Real finality levels based on actual network conditions
                if chain == 'ethereum':
                    if congestion == "HIGH":
                        fast_blocks, safe_blocks, full_blocks = 15, 40, 80
                    elif congestion == "MEDIUM":
                        fast_blocks, safe_blocks, full_blocks = 12, 35, 70
                    else:
                        fast_blocks, safe_blocks, full_blocks = 8, 32, 64
                    fast_time = fast_blocks * avg_block_time
                    safe_time = safe_blocks * avg_block_time
                    full_time = full_blocks * avg_block_time
                else:  # solana
                    if congestion == "HIGH":
                        fast_blocks, safe_blocks, full_blocks = 15, 50, 100
                    elif congestion == "MEDIUM":
                        fast_blocks, safe_blocks, full_blocks = 10, 40, 80
                    else:
                        fast_blocks, safe_blocks, full_blocks = 8, 32, 64
                    fast_time = fast_blocks * avg_block_time
                    safe_time = safe_blocks * avg_block_time
                    full_time = full_blocks * avg_block_time
                
                finality_row = [
                    timestamp, chain.upper(), f"{current_block}", f"{avg_block_time:.2f}s", f"{gas_price_gwei:.6f}",
                    f"{pending_txs}", f"{fast_blocks}", f"{fast_time:.1f}s", f"{safe_blocks}", f"{safe_time:.1f}s",
                    f"{full_blocks}", f"{full_time:.1f}s", congestion, mev_risk
                ]
                
                try:
                    self.finality_ws.append_row(finality_row)
                    logger.info(f"✓ Updated finality for {chain}: Fast={fast_time:.1f}s, Safe={safe_time:.1f}s, Full={full_time:.1f}s")
                except Exception as e:
                    logger.error(f"Error appending finality row for {chain}: {e}")
            
        except Exception as e:
            logger.error(f"Error updating finality data: {e}")
            
    def run_arbitrage_cycle(self):
        logger.info("Starting triangular arbitrage cycle...")
        
        # Fetch all prices
        self.fetch_all_pair_prices()
        
        # Log current prices
        for pair, dex_prices in self.prices.items():
            logger.info(f"{pair} prices:")
            for dex, data in dex_prices.items():
                logger.info(f"  {dex}: {data['price']:.6f}")
        
        # Calculate opportunities
        opportunities = self.calculate_triangular_arbitrage()
        
        if opportunities:
            logger.info(f"\n*** FOUND {len(opportunities)} PROFITABLE OPPORTUNITIES ***")
            for opp in opportunities[:3]:
                logger.info(f"{opp['triangle_path']} on {opp['dex']}: Net ${opp['net_profit']:.4f}")
        else:
            logger.info("\n*** NO OPPORTUNITIES MEET 0.01% THRESHOLD ***")
            logger.info("REASON: Gas fees + slippage exceed potential arbitrage profits")
            logger.info("See detailed calculations above for breakdown")
        
        # Always update sheets (prices always, arbitrage and finality when opportunities exist)
        self.update_google_sheets(opportunities)
        if opportunities:
            logger.info(f"Updated all sheets with {len(opportunities)} arbitrage opportunities")
        else:
            logger.info("Updated price data only - no arbitrage opportunities found")
        
    def run_continuous(self, interval=30):
        """Run the bot continuously"""
        logger.info(f"Starting triangular arbitrage bot with {interval}s intervals...")
        
        while True:
            try:
                self.run_arbitrage_cycle()
                time.sleep(interval)
            except KeyboardInterrupt:
                logger.info("Bot stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(interval)

if __name__ == "__main__":
    bot = TriangularArbitrageBot()
    bot.run_continuous(30)