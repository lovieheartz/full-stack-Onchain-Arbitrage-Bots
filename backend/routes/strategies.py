from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any
from models.strategy import StrategyInfo, StrategyMetrics, StrategyExecution, StrategyRunRequest
from services.strategy_service import StrategyService

router = APIRouter()
strategy_service = StrategyService()

@router.get("/", response_model=List[StrategyInfo])
async def get_strategies():
    """Get all available strategies"""
    return strategy_service.get_all_strategies()

@router.get("/{strategy_id}", response_model=StrategyInfo)
async def get_strategy(strategy_id: str):
    """Get specific strategy details"""
    strategy = strategy_service.get_strategy_by_id(strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return strategy

@router.get("/{strategy_id}/metrics", response_model=StrategyMetrics)
async def get_strategy_metrics(strategy_id: str):
    """Get strategy performance metrics"""
    strategy = strategy_service.get_strategy_by_id(strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return strategy_service.get_strategy_metrics(strategy_id)

@router.post("/{strategy_id}/run", response_model=StrategyExecution)
async def run_strategy(strategy_id: str, request: StrategyRunRequest, background_tasks: BackgroundTasks):
    """Execute a strategy"""
    print(f"🎯 API ENDPOINT HIT: /strategies/{strategy_id}/run")
    print(f"📋 Request params: duration={request.duration_minutes}, amount={request.trade_amount}")
    
    strategy = strategy_service.get_strategy_by_id(strategy_id)
    if not strategy:
        print(f"❌ Strategy not found: {strategy_id}")
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    print(f"✅ Found strategy: {strategy.name} -> {strategy.file_path}")
    
    result = await strategy_service.run_strategy(
        strategy_id=strategy_id,
        duration_minutes=request.duration_minutes,
        trade_amount=request.trade_amount,
        paper_trading=request.paper_trading
    )
    
    print(f"🏁 Strategy execution result: {result.status}")
    return result

@router.get("/{strategy_id}/status")
async def get_strategy_status(strategy_id: str):
    """Get current running status of a strategy"""
    strategy = strategy_service.get_strategy_by_id(strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    return strategy_service.get_strategy_status(strategy_id)

@router.post("/{strategy_id}/stop")
async def stop_strategy(strategy_id: str):
    """Stop a running strategy"""
    strategy = strategy_service.get_strategy_by_id(strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    result = await strategy_service.stop_strategy(strategy_id)
    if result['status'] == 'error':
        raise HTTPException(status_code=400, detail=result['message'])
    
    return result

@router.get("/{strategy_id}/spreadsheet-link")
async def get_spreadsheet_link(strategy_id: str):
    """Get the Google Sheets link for a strategy"""
    strategy = strategy_service.get_strategy_by_id(strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    link = strategy_service.get_spreadsheet_link(strategy_id)
    return {"spreadsheet_link": link}

@router.post("/run-python")
async def run_python_strategy(request: Dict[str, Any]):
    """Execute Python strategy file"""
    strategy_id = request.get('strategyId')
    python_file = request.get('pythonFile')
    
    print(f"🎯 Received request to run: {python_file} for strategy: {strategy_id}")
    
    if not strategy_id or not python_file:
        raise HTTPException(status_code=400, detail="Missing strategyId or pythonFile")
    
    # Execute Python file immediately
    strategy_service.execute_python_file(python_file)
    
    return {"status": "started", "message": f"Executing {python_file}"}