from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.querying.service_bot_v3 import QueryService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Resolve a stock query and optionally run analysis.")
    parser.add_argument("--query", required=True, help="Stock code or stock name.")
    parser.add_argument("--as-of", dest="as_of", default=date.today().isoformat())
    parser.add_argument("--demo", action="store_true", help="Use deterministic demo providers.")
    parser.add_argument("--confirm", action="store_true", help="Execute analysis after resolution.")
    parser.add_argument("--force-refresh", action="store_true", help="Ignore cached daily result and rerun analysis.")
    return parser.parse_args()


def main(query: str, as_of: str, use_demo_data: bool = False, confirm: bool = False, force_refresh: bool = False) -> dict:
    service = QueryService(PROJECT_ROOT)
    if confirm:
        return service.execute_query(query, as_of=as_of, use_demo_data=use_demo_data, force_refresh=force_refresh)
    return service.prepare_query(query, as_of=as_of, use_demo_data=use_demo_data)


if __name__ == "__main__":
    args = parse_args()
    result = main(
        query=args.query,
        as_of=args.as_of,
        use_demo_data=args.demo,
        confirm=args.confirm,
        force_refresh=args.force_refresh,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
