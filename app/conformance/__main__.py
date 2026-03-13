import argparse
import sys
import asyncio
from typing import Optional

from app.conformance.runner import ConformanceRunner
from app.conformance.reporter import ConformanceReporter

async def main():
    parser = argparse.ArgumentParser(description="MT5 Bridge Conformance CLI")
    parser.add_argument("--base-url", required=True, help="Base URL of the MT5 bridge API")
    parser.add_argument("--api-key", required=True, help="API key for authentication")
    parser.add_argument("--include-write-tests", action="store_true", help="Include write tests (order send and cancel)")
    parser.add_argument("--output-json", help="Path to save the JSON report")
    parser.add_argument("--output-md", help="Path to save the Markdown report")

    args = parser.parse_args()

    runner = ConformanceRunner(
        base_url=args.base_url,
        api_key=args.api_key,
        include_write_tests=args.include_write_tests
    )

    try:
        report = await runner.run()
    except Exception as e:
        print(f"Error running conformance suite: {e}", file=sys.stderr)
        sys.exit(1)

    reporter = ConformanceReporter(report)
    
    if args.output_json:
        reporter.write_json(args.output_json)
    else:
        # If no json output path provided, dump to stdout
        print(reporter.to_json())

    if args.output_md:
        reporter.write_markdown(args.output_md)

if __name__ == "__main__":
    asyncio.run(main())
