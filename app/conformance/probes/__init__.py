from typing import List, Callable, Awaitable
import httpx
from app.models.conformance import ConformanceResult

from .connection import run_connection_probe
from .symbols import run_symbols_probe
from .pricing import run_pricing_probe
from .calculations import run_calculations_probe
from .market_book import run_market_book_probe
from .write_tests import run_write_tests_probe

ProbeFunction = Callable[[httpx.AsyncClient], Awaitable[List[ConformanceResult]]]

def get_all_probes(include_write_tests: bool = False) -> List[ProbeFunction]:
    probes = [
        run_connection_probe,
        run_symbols_probe,
        run_pricing_probe,
        run_calculations_probe,
        run_market_book_probe
    ]
    
    if include_write_tests:
        probes.append(run_write_tests_probe)
        
    return probes
