#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from prototype.routeros_m0.hardware_discovery import (  # noqa: E402
    DiscoveryReportError,
    extract_gl_mt5000_observations,
    parse_discovery_report,
    report_has_hardware_identity,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a privacy-minimized GL-MT5000 hardware discovery report "
            "and emit a safe direct-observation summary."
        )
    )
    parser.add_argument("report", type=Path)
    args = parser.parse_args()

    try:
        text = args.report.read_text(encoding="utf-8")
        report = parse_discovery_report(text)
        observations = extract_gl_mt5000_observations(report)
    except (OSError, DiscoveryReportError) as exc:
        print(f"validation failed: {exc}", file=sys.stderr)
        return 2

    payload = {
        "evidence_version": "0.1",
        "profile_id": report.profile_id,
        "classification": "direct-observation",
        "hardware_identity_present": report_has_hardware_identity(report),
        "observations": asdict(observations),
        "status": {
            "installable": False,
            "supported": False,
            "note": (
                "Validated discovery evidence only. This summary does not "
                "establish bootability, recovery acceptance, installation "
                "eligibility, or Supported hardware status."
            ),
        },
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
