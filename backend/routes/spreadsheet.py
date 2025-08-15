from fastapi import APIRouter, HTTPException, Response
from services.spreadsheet_service import spreadsheet_service
from typing import Optional, Dict, Any
from datetime import datetime

router = APIRouter()

@router.get("/test")
async def test_endpoint() -> Dict[str, Any]:
    """Test endpoint to verify API is working"""
    return {
        "status": "success",
        "message": "Spreadsheet API is working",
        "timestamp": datetime.now().isoformat(),
        "available_strategies": list(spreadsheet_service.strategy_sheets.keys())
    }

@router.get("/strategies")
async def get_available_strategies() -> Dict[str, Any]:
    """Get list of available strategies"""
    try:
        strategies = spreadsheet_service.get_available_strategies()
        print(f"Available strategies: {strategies}")  # Debug log
        return {
            "status": "success",
            "strategies": strategies,
            "total": len(strategies)
        }
    except Exception as e:
        print(f"Error getting strategies: {e}")
        return {
            "status": "error",
            "strategies": [],
            "total": 0,
            "error": str(e)
        }

@router.get("/overview")
async def get_strategies_overview() -> Dict[str, Any]:
    """Get overview of all strategies with their worksheets"""
    return spreadsheet_service.get_spreadsheet_data()

@router.get("/data/{strategy_name}")
async def get_strategy_data(
    strategy_name: str,
    worksheet_name: Optional[str] = None
) -> Dict[str, Any]:
    """Get data from a specific strategy spreadsheet"""
    print(f"API: Raw strategy_name received: '{strategy_name}'")
    
    # Clean strategy name - remove any trailing numbers or colons
    clean_strategy_name = strategy_name.split(':')[0].strip()
    print(f"API: Cleaned strategy name: '{clean_strategy_name}'")
    
    # Validate strategy name
    if not clean_strategy_name or clean_strategy_name.strip() == "":
        print("Empty strategy name after cleaning")
        return {
            "status": "success",
            "strategy": "unknown",
            "data": {"Main": [{"Message": "Invalid strategy name", "Timestamp": datetime.now().isoformat()}]},
            "worksheets": ["Main"],
            "last_updated": datetime.now().isoformat()
        }
    
    try:
        result = spreadsheet_service.get_spreadsheet_data(clean_strategy_name, worksheet_name)
        print(f"API: Result status: {result.get('status', 'unknown')}")
        
        # Always ensure we return a valid response structure
        if not result or not isinstance(result, dict):
            print(f"Invalid result, returning mock data for {clean_strategy_name}")
            result = spreadsheet_service._get_mock_data(clean_strategy_name, worksheet_name)
        
        # Ensure required fields exist
        if 'status' not in result:
            result['status'] = 'success'
        if 'data' not in result:
            result['data'] = {}
        if 'worksheets' not in result:
            result['worksheets'] = list(result.get('data', {}).keys())
        
        return result
        
    except Exception as e:
        print(f"API Error in get_strategy_data: {e}")
        import traceback
        traceback.print_exc()
        
        # Always return valid mock data structure - never raise exception
        return {
            "status": "success",
            "strategy": clean_strategy_name,
            "data": {"Main": [{"Message": f"Error loading data: {str(e)}", "Timestamp": datetime.now().isoformat()}]},
            "worksheets": ["Main"],
            "last_updated": datetime.now().isoformat(),
            "data_source": "error_fallback",
            "error": str(e)
        }

@router.get("/export/{strategy_name}")
async def export_strategy_data(
    strategy_name: str,
    worksheet_name: Optional[str] = None,
    format: str = "csv"
):
    """Export strategy data as CSV or JSON"""
    try:
        data = spreadsheet_service.export_data(format, strategy_name, worksheet_name)
        
        filename = f"{strategy_name}"
        if worksheet_name:
            filename += f"_{worksheet_name}"
        
        if format.lower() == "csv":
            return Response(
                content=data,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={filename}.csv"}
            )
        else:
            return Response(
                content=data,
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename={filename}.json"}
            )
    except Exception as e:
        print(f"Export error: {e}")
        return Response(
            content=f"Error exporting data: {str(e)}",
            status_code=500,
            media_type="text/plain"
        )

# Legacy endpoints for backward compatibility
@router.get("/view")
async def view_spreadsheet_data(strategy_name: Optional[str] = None):
    """View spreadsheet data for a strategy or all strategies"""
    try:
        return spreadsheet_service.get_spreadsheet_data(strategy_name)
    except Exception as e:
        print(f"View error: {e}")
        return {
            "status": "error",
            "data": {},
            "error": str(e)
        }

@router.get("/download/{type}")
async def download_spreadsheet_data(
    type: str,
    strategy_name: Optional[str] = None,
    worksheet_name: Optional[str] = None
):
    """Download spreadsheet data"""
    try:
        data = spreadsheet_service.export_data(type, strategy_name, worksheet_name)
        
        filename = "arbitrage_data"
        if strategy_name:
            filename = strategy_name
        if worksheet_name:
            filename += f"_{worksheet_name}"
        
        if type.lower() == "csv":
            return Response(
                content=data,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={filename}.csv"}
            )
        else:
            return Response(
                content=data,
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename={filename}.json"}
            )
    except Exception as e:
        print(f"Download error: {e}")
        return Response(
            content=f"Error downloading data: {str(e)}",
            status_code=500,
            media_type="text/plain"
        )