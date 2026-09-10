#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from prototype.routeros_m0 import ConfigRevision, compile_plan, validate_config  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a GoreeCloud Router OS Milestone 0 prototype configuration.")
    parser.add_argument("config", type=Path)
    parser.add_argument("--check-only", action="store_true", help="Validate without printing the plan")
    args = parser.parse_args()

    try:
        config = json.loads(args.config.read_text(encoding="utf-8"))
        validate_config(config)
        revision = ConfigRevision.from_config(config)
        print(f"valid revision: {revision.digest}")
        if not args.check_only:
            print(json.dumps(compile_plan(config), indent=2, sort_keys=True))
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"validation failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
