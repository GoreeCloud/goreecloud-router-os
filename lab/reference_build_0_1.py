from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
import re
import shutil
import subprocess
from typing import Iterable, Sequence

LAB_VERSION = "0.1"
ROUTER_WAN = "198.51.100.1/30"
UPSTREAM = "198.51.100.2/30"
ROUTER_LAN = "192.168.50.1/24"
CLIENT = "192.168.50.2/24"


class LabError(RuntimeError):
    """Raised when the isolated Reference Build 0.1 lab cannot prove its invariants."""


@dataclass(frozen=True)
class LabNames:
    router: str
    upstream: str
    client: str
    wan_router_if: str
    wan_peer_if: str
    lan_router_if: str
    lan_peer_if: str

    @classmethod
    def for_pid(cls, pid: int | None = None) -> "LabNames":
        suffix = str(os.getpid() if pid is None else pid)
        if not re.fullmatch(r"[0-9]+", suffix):
            raise LabError("lab namespace suffix must be numeric")
        tail = suffix[-5:]
        return cls(
            router=f"gcr-r-{suffix}",
            upstream=f"gcr-w-{suffix}",
            client=f"gcr-l-{suffix}",
            wan_router_if=f"grw{tail}",
            wan_peer_if=f"gww{tail}",
            lan_router_if=f"grl{tail}",
            lan_peer_if=f"gll{tail}",
        )


@dataclass(frozen=True)
class LabResult:
    lab_version: str
    routed_ping_passed: bool
    host_default_route_unchanged: bool
    namespaces_removed: bool


def _run(command: Sequence[str], *, check: bool = True, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        check=check,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )


def _host_default_route() -> str:
    result = _run(["ip", "route", "show", "default"], capture=True)
    return result.stdout.strip()


def _namespace_exists(name: str) -> bool:
    result = _run(["ip", "netns", "list"], capture=True)
    names = {line.split()[0] for line in result.stdout.splitlines() if line.strip()}
    return name in names


def _require_tools() -> None:
    missing = [tool for tool in ("ip", "ping", "sysctl") if shutil.which(tool) is None]
    if missing:
        raise LabError(f"missing required lab tools: {', '.join(missing)}")


def planned_operations(names: LabNames) -> tuple[tuple[str, ...], ...]:
    """Return fixed isolated-lab operations for inspection and unit tests.

    No caller-supplied command fragments are accepted. Host route modification is
    intentionally absent; all route changes target named network namespaces.
    """
    return (
        ("ip", "netns", "add", names.router),
        ("ip", "netns", "add", names.upstream),
        ("ip", "netns", "add", names.client),
        ("ip", "link", "add", names.wan_router_if, "type", "veth", "peer", "name", names.wan_peer_if),
        ("ip", "link", "set", names.wan_router_if, "netns", names.router),
        ("ip", "link", "set", names.wan_peer_if, "netns", names.upstream),
        ("ip", "link", "add", names.lan_router_if, "type", "veth", "peer", "name", names.lan_peer_if),
        ("ip", "link", "set", names.lan_router_if, "netns", names.router),
        ("ip", "link", "set", names.lan_peer_if, "netns", names.client),
        ("ip", "-n", names.router, "link", "set", "lo", "up"),
        ("ip", "-n", names.upstream, "link", "set", "lo", "up"),
        ("ip", "-n", names.client, "link", "set", "lo", "up"),
        ("ip", "-n", names.router, "addr", "add", ROUTER_WAN, "dev", names.wan_router_if),
        ("ip", "-n", names.upstream, "addr", "add", UPSTREAM, "dev", names.wan_peer_if),
        ("ip", "-n", names.router, "addr", "add", ROUTER_LAN, "dev", names.lan_router_if),
        ("ip", "-n", names.client, "addr", "add", CLIENT, "dev", names.lan_peer_if),
        ("ip", "-n", names.router, "link", "set", names.wan_router_if, "up"),
        ("ip", "-n", names.upstream, "link", "set", names.wan_peer_if, "up"),
        ("ip", "-n", names.router, "link", "set", names.lan_router_if, "up"),
        ("ip", "-n", names.client, "link", "set", names.lan_peer_if, "up"),
        ("ip", "netns", "exec", names.router, "sysctl", "-q", "-w", "net.ipv4.ip_forward=1"),
        ("ip", "-n", names.upstream, "route", "add", "192.168.50.0/24", "via", "198.51.100.1"),
        ("ip", "-n", names.client, "route", "add", "default", "via", "192.168.50.1"),
    )


def _cleanup(names: LabNames) -> None:
    for name in (names.client, names.upstream, names.router):
        _run(["ip", "netns", "del", name], check=False, capture=True)


def run_lab() -> LabResult:
    """Run an isolated topology smoke test and always tear it down.

    This is a CI/development harness, not a Router OS privileged execution
    adapter. It creates only temporary namespaces/veths and namespace-local
    addresses/routes. The host default route is observed before and after and
    must remain byte-for-byte unchanged.
    """
    _require_tools()
    if os.geteuid() != 0:
        raise LabError("the namespace lab must run as root (use sudo in CI)")

    names = LabNames.for_pid()
    _cleanup(names)
    before_default = _host_default_route()
    ping_ok = False
    failure: Exception | None = None
    try:
        for command in planned_operations(names):
            _run(command)
        _run(["ip", "netns", "exec", names.client, "ping", "-c", "2", "-W", "1", "198.51.100.2"])
        ping_ok = True
    except Exception as exc:
        failure = exc
    finally:
        _cleanup(names)

    after_default = _host_default_route()
    unchanged = before_default == after_default
    removed = not any(_namespace_exists(name) for name in (names.router, names.upstream, names.client))
    if not unchanged:
        raise LabError("host default route changed during isolated lab execution") from failure
    if not removed:
        raise LabError("one or more lab namespaces remained after teardown") from failure
    if failure is not None:
        raise LabError("isolated namespace lab failed after safe teardown") from failure
    if not ping_ok:
        raise LabError("routed namespace connectivity test did not complete")
    return LabResult(
        lab_version=LAB_VERSION,
        routed_ping_passed=True,
        host_default_route_unchanged=True,
        namespaces_removed=True,
    )


def _print_plan(commands: Iterable[Sequence[str]]) -> None:
    for command in commands:
        print(" ".join(command))


def main() -> int:
    parser = argparse.ArgumentParser(description="Reference Build 0.1 isolated virtual-network lab")
    parser.add_argument("--run", action="store_true", help="execute the isolated namespace smoke test")
    parser.add_argument("--plan", action="store_true", help="print the fixed lab operation plan")
    args = parser.parse_args()

    names = LabNames.for_pid()
    if args.plan:
        _print_plan(planned_operations(names))
    if args.run:
        result = run_lab()
        print(
            "lab passed: "
            f"routed_ping={result.routed_ping_passed} "
            f"host_default_route_unchanged={result.host_default_route_unchanged} "
            f"namespaces_removed={result.namespaces_removed}"
        )
    if not args.run and not args.plan:
        parser.error("select --plan or --run")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
