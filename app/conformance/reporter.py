import json
from collections import defaultdict
from app.models.conformance import ConformanceReport

class ConformanceReporter:
    def __init__(self, report: ConformanceReport):
        self.report = report

    def to_json(self) -> str:
        return self.report.model_dump_json(indent=2)

    def write_json(self, path: str) -> None:
        with open(path, "w") as f:
            f.write(self.to_json())

    def write_markdown(self, path: str) -> None:
        md = self._generate_markdown()
        with open(path, "w") as f:
            f.write(md)

    def _generate_markdown(self) -> str:
        lines = []
        lines.append("# Conformance Report")
        lines.append("")
        lines.append("## Environment")
        lines.append(f"- **Broker:** {self.report.broker_name}")
        lines.append(f"- **Server:** {self.report.server}")
        lines.append(f"- **Terminal Build:** {self.report.terminal_build}")
        lines.append(f"- **Python Runtime:** {self.report.python_runtime}")
        lines.append(f"- **Compatibility Profile Used:** {self.report.compatibility_profile}")
        lines.append("")
        
        # Group by category
        categories = defaultdict(list)
        for res in self.report.results:
            categories[res.category].append(res)
            
        lines.append("## Summary by Category")
        lines.append("| Category | Pass | Warn | Fail |")
        lines.append("|---|---|---|---|")
        
        for category, results in categories.items():
            passes = sum(1 for r in results if r.status == "pass")
            warns = sum(1 for r in results if r.status == "warn")
            fails = sum(1 for r in results if r.status == "fail")
            lines.append(f"| {category} | {passes} | {warns} | {fails} |")
            
        lines.append("")
        lines.append("## Details")
        lines.append("| Category | Probe | Status | Message |")
        lines.append("|---|---|---|---|")
        
        for res in self.report.results:
            msg = res.message or ""
            status_indicator = {
                "pass": "✅ Pass",
                "warn": "⚠️ Warn",
                "fail": "❌ Fail"
            }.get(res.status, res.status)
            lines.append(f"| {res.category} | {res.name} | {status_indicator} | {msg} |")
            
        lines.append("")
        lines.append("## Recommendation")
        lines.append(f"Recommended Profile: **{self.report.recommendation}**")
        lines.append("")
        
        return "\n".join(lines)
