from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class SpreadsheetData(BaseModel):
    sheet_name: str
    headers: List[str]
    rows: List[List[Any]]
    total_rows: int
    last_updated: str

class SpreadsheetSummary(BaseModel):
    total_sheets: int
    sheets: List[str]
    total_records: int
    last_updated: str

class ExportRequest(BaseModel):
    sheet_name: str
    format: str = "csv"
    filters: Optional[Dict[str, Any]] = None