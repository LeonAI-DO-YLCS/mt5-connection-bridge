import httpx
from typing import List, Optional
from app.models.conformance import ConformanceResult, ConformanceReport
from app.conformance.probes import get_all_probes

class ConformanceRunner:
    def __init__(self, base_url: str, api_key: str, include_write_tests: bool = False):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.include_write_tests = include_write_tests
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"X-API-Key": self.api_key},
            timeout=10.0
        )

    async def run(self) -> ConformanceReport:
        results: List[ConformanceResult] = []
        probes = get_all_probes(include_write_tests=self.include_write_tests)

        broker_name = "unknown"
        server = "unknown"
        terminal_build = "unknown"
        python_runtime = "unknown"
        compatibility_profile = "unknown"

        try:
            diag_resp = await self.client.get("/diagnostics/runtime")
            if diag_resp.status_code == 200:
                diag_data = diag_resp.json()
                terminal = diag_data.get("terminal", {})
                runtime = diag_data.get("runtime", {})
                
                broker_name = terminal.get("company", "unknown")
                server = terminal.get("server", "unknown")
                terminal_build = str(terminal.get("build", "unknown"))
                python_runtime = runtime.get("python_version", "unknown")
                
                comp_profile = diag_data.get("compatibility_profile", {})
                if isinstance(comp_profile, dict):
                    compatibility_profile = comp_profile.get("name", "strict_safe")
                else:
                    compatibility_profile = str(comp_profile)
        except Exception:
            pass

        for probe in probes:
            probe_results = await probe(self.client)
            results.extend(probe_results)

        recommendation = self._generate_recommendation(results)

        # compute summary stats is implicitly done inside Reporter for markdown,
        # but recommendation is based on pass/warn/fail ratios here
        return ConformanceReport(
            broker_name=broker_name,
            server=server,
            terminal_build=terminal_build,
            python_runtime=python_runtime,
            compatibility_profile=compatibility_profile,
            results=results,
            recommendation=recommendation
        )

    def _generate_recommendation(self, results: List[ConformanceResult]) -> str:
        if not results:
            return "strict_safe"
            
        passes = sum(1 for r in results if r.status == "pass")
        warns = sum(1 for r in results if r.status == "warn")
        fails = sum(1 for r in results if r.status == "fail")
        
        # recommendation based on pass/warn/fail ratios
        if fails > 0:
            return "strict_safe"
        elif warns > 0:
            return "balanced"
        elif passes == len(results):
            return "max_compat"
        else:
            return "strict_safe"

