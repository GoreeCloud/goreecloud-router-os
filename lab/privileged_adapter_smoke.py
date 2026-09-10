from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from prototype.routeros_m0.compiler import compile_plan
from prototype.routeros_m0.linux_adapter import LinuxNamespaceExecutionAdapter


class SmokeError(RuntimeError):
    pass


def _run(command: list[str], *, check: bool = True, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=check,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )


def _host_default_route() -> str:
    return _run(["ip", "route", "show", "default"], capture=True).stdout.strip()


def _namespace_exists(name: str) -> bool:
    result = _run(["ip", "netns", "list"], capture=True)
    return name in {line.split()[0] for line in result.stdout.splitlines() if line.strip()}


def _cleanup(namespace: str) -> None:
    _run(["ip", "netns", "del", namespace], check=False, capture=True)


def _require_tools() -> None:
    missing = [tool for tool in ("ip", "sysctl") if shutil.which(tool) is None]
    if missing:
        raise SmokeError(f"missing required tools: {', '.join(missing)}")


def _reference_plan() -> dict[str, Any]:
    config = json.loads((ROOT / "config/examples/reference-build-0.1.json").read_text(encoding="utf-8"))
    return compile_plan(config)


def supported_adapter_subset(plan: Mapping[str, Any]) -> dict[str, Any]:
    """Extract only operations intentionally accepted by the current adapter tranche."""
    operations = plan.get("operations")
    if not isinstance(operations, list):
        raise SmokeError("reference plan operations are unavailable")
    selected = [
        operation
        for operation in operations
        if isinstance(operation, Mapping)
        and (
            (operation.get("kind") == "interface.configure" and operation.get("role") == "lan")
            or operation.get("kind") == "sysctl.intent"
        )
    ]
    if len(selected) != 2:
        raise SmokeError("expected exactly the static LAN and IPv4-forwarding operations")
    return {
        "plan_version": plan.get("plan_version"),
        "revision": plan.get("revision"),
        "operations": selected,
    }


def run_smoke() -> None:
    _require_tools()
    if os.geteuid() != 0:
        raise SmokeError("privileged adapter smoke test must run as root")

    namespace = f"gcr-a-{os.getpid()}"
    full_plan = _reference_plan()
    subset = supported_adapter_subset(full_plan)
    lan_operation = next(
        operation
        for operation in subset["operations"]
        if operation.get("kind") == "interface.configure"
    )
    interface = lan_operation["name"]
    expected_address = lan_operation["address"]

    before_default = _host_default_route()
    failure: Exception | None = None
    static_lan_ok = False
    forwarding_ok = False
    executed = 0

    _cleanup(namespace)
    try:
        _run(["ip", "netns", "add", namespace])
        _run(["ip", "-n", namespace, "link", "add", interface, "type", "dummy"])

        adapter = LinuxNamespaceExecutionAdapter(namespace, [interface])
        result = adapter.execute(subset)
        executed = result.commands_executed

        address_state = _run(
            ["ip", "-n", namespace, "-4", "-o", "addr", "show", "dev", interface],
            capture=True,
        ).stdout
        static_lan_ok = expected_address in address_state

        link_state = _run(
            ["ip", "-n", namespace, "-o", "link", "show", "dev", interface],
            capture=True,
        ).stdout
        static_lan_ok = static_lan_ok and "UP" in link_state

        forwarding_value = _run(
            ["ip", "netns", "exec", namespace, "sysctl", "-n", "net.ipv4.ip_forward"],
            capture=True,
        ).stdout.strip()
        forwarding_ok = forwarding_value == "1"
    except Exception as exc:
        failure = exc
    finally:
        _cleanup(namespace)

    after_default = _host_default_route()
    unchanged = before_default == after_default
    removed = not _namespace_exists(namespace)

    if not unchanged:
        raise SmokeError("host default route changed during privileged adapter smoke test") from failure
    if not removed:
        raise SmokeError("adapter smoke namespace remained after teardown") from failure
    if failure is not None:
        raise SmokeError("privileged adapter smoke test failed after safe teardown") from failure
    if executed != 3:
        raise SmokeError(f"expected three executed adapter commands, got {executed}")
    if not static_lan_ok:
        raise SmokeError("static LAN address/link state was not observed")
    if not forwarding_ok:
        raise SmokeError("router namespace IPv4 forwarding was not observed")

    print(
        "privileged adapter smoke passed: "
        "static_lan=True "
        "ipv4_forwarding=True "
        "host_default_route_unchanged=True "
        "namespace_removed=True"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Development-only privileged Linux adapter smoke test")
    parser.add_argument("--run", action="store_true", help="execute the isolated adapter smoke test")
    args = parser.parse_args()
    if not args.run:
        parser.error("select --run")
    run_smoke()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
