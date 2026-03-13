from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class ConformanceResult(BaseModel):
    category: str
    name: str
    status: str
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

class ConformanceReport(BaseModel):
    broker_name: str
    server: str
    terminal_build: str
    python_runtime: str
    compatibility_profile: str
    results: List[ConformanceResult]
    recommendation: str
