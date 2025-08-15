from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class StrategyInfo(BaseModel):
    id: str
    name: str
    description: str
    type: str
    chains: List[str]
    status: str
    last_run: Optional[datetime] = None
    total_trades: int = 0
    total_profit: float = 0.0
    success_rate: float = 0.0
    file_path: str

class StrategyMetrics(BaseModel):
    trades_today: int
    profit_today: float
    avg_profit_per_trade: float
    execution_time_avg: float
    gas_cost_total: float

class StrategyExecution(BaseModel):
    strategy_id: str
    status: str
    message: str
    execution_time: float
    trades_executed: int
    profit_generated: float

class StrategyRunRequest(BaseModel):
    duration_minutes: Optional[int] = 5
    trade_amount: Optional[float] = 1000.0
    paper_trading: Optional[bool] = True