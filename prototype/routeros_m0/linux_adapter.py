from __future__ import annotations

from dataclasses import dataclass
from ipaddress import ip_interface
import os
import re
import shutil
import subprocess
from typing import Any, Callable, Mapping, Sequence

from .nftables_backend import FILTER_TABLE, NAT_TABLE, NftablesBackendError, compile_firewall_intent


class AdapterError(RuntimeError):
    """Base error for the Development-only privileged Linux adapter."""


class TargetValidationError(AdapterError):
    """Raised when an execution target cannot be proven to be an approved lab target."""


class UnsupportedOperation(AdapterError):
    """Raised when a plan contains an operation without an accepted backend."""


@dataclass(frozen=True)
class RenderedCommand:
    kind: str
    argv: tuple[str, ...]
    stdin: str | None = None
    check: bool = True


@dataclass(frozen=True)
class AdapterPlan:
    namespace: str
    revision: str
    commands: tuple[RenderedCommand, ...]
    required_interfaces: tuple[str, ...]


@dataclass(frozen=True)
class ExecutionResult:
    namespace: str
    revision: str
    commands_executed: int


Runner = Callable[..., subprocess.CompletedProcess[str]]
_NAMESPACE_RE = re.compile(r"^gcr-a-[0-9]+$")
_INTERFACE_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
_REVISION_RE = re.compile(r"^[0-9a-f]{64}$")


def _validate_namespace(value: str) -> str:
    if not isinstance(value, str) or not _NAMESPACE_RE.fullmatch(value):
        raise TargetValidationError("execution namespace must use the generated gcr-a-<digits> form")
    if len(value.encode("utf-8")) > 48:
        raise TargetValidationError("execution namespace name is too long")
    return value


def _validate_interface_name(value: str) -> str:
    if not isinstance(value, str) or not value or not _INTERFACE_RE.fullmatch(value):
        raise TargetValidationError("interface name contains unsupported characters")
    if len(value.encode("utf-8")) > 15:
        raise TargetValidationError("interface name exceeds the Linux interface-name limit")
    return value


def _normalize_ipv4_interface(value: str) -> str:
    if not isinstance(value, str):
        raise UnsupportedOperation("static interface address must be a string")
    try:
        parsed = ip_interface(value)
    except ValueError as exc:
        raise UnsupportedOperation("static interface address is invalid") from exc
    if parsed.version != 4:
        raise UnsupportedOperation("the current adapter accepts IPv4 static addresses only")
    return str(parsed)


class LinuxNamespaceExecutionAdapter:
    """Execute a deliberately bounded set of Router OS operations in one lab namespace.

    This Development adapter is not a host-network executor. It accepts only dedicated
    ``gcr-a-<digits>`` namespaces and an explicit interface allowlist. Complete plan
    preflight happens before target probes or mutation so an unsupported operation
    fails closed. Commands are always structured argv; shell execution is never used.
    """

    def __init__(
        self,
        namespace: str,
        allowed_interfaces: Sequence[str],
        *,
        runner: Runner | None = None,
    ) -> None:
        self.namespace = _validate_namespace(namespace)
        checked = tuple(_validate_interface_name(item) for item in allowed_interfaces)
        if not checked:
            raise TargetValidationError("at least one allowed interface is required")
        if len(set(checked)) != len(checked):
            raise TargetValidationError("allowed interface names must be unique")
        self.allowed_interfaces = frozenset(checked)
        self._runner = runner or subprocess.run

    def preflight(self, plan: Mapping[str, Any]) -> AdapterPlan:
        """Validate the entire abstract plan and render supported operations only."""
        if not isinstance(plan, Mapping):
            raise AdapterError("execution plan must be a mapping")
        if plan.get("plan_version") != "0.1":
            raise UnsupportedOperation("unsupported execution plan version")

        revision = plan.get("revision")
        if not isinstance(revision, str) or not _REVISION_RE.fullmatch(revision):
            raise AdapterError("execution plan requires an exact lowercase SHA-256 revision")

        operations = plan.get("operations")
        if not isinstance(operations, list):
            raise AdapterError("execution plan operations must be a list")

        rendered: list[RenderedCommand] = []
        required_interfaces: list[str] = []
        for operation in operations:
            if not isinstance(operation, Mapping):
                raise AdapterError("each execution plan operation must be a mapping")
            kind = operation.get("kind")
            if kind == "interface.configure":
                commands, interface = self._render_interface(operation)
                rendered.extend(commands)
                required_interfaces.append(interface)
            elif kind == "sysctl.intent":
                rendered.append(self._render_sysctl(operation))
            elif kind == "firewall.intent":
                commands, interfaces = self._render_firewall(operation)
                rendered.extend(commands)
                required_interfaces.extend(interfaces)
            else:
                raise UnsupportedOperation(f"no accepted privileged backend for operation kind: {kind!r}")

        return AdapterPlan(
            namespace=self.namespace,
            revision=revision,
            commands=tuple(rendered),
            required_interfaces=tuple(dict.fromkeys(required_interfaces)),
        )

    def _render_interface(
        self,
        operation: Mapping[str, Any],
    ) -> tuple[tuple[RenderedCommand, ...], str]:
        role = operation.get("role")
        mode = operation.get("mode")
        if role != "lan" or mode != "static":
            raise UnsupportedOperation("the current adapter supports only static LAN interface configuration")

        name = _validate_interface_name(operation.get("name"))
        if name not in self.allowed_interfaces:
            raise TargetValidationError("interface is outside the adapter allowlist")
        address = _normalize_ipv4_interface(operation.get("address"))

        return (
            (
                RenderedCommand(
                    kind="interface.address.replace",
                    argv=("ip", "-n", self.namespace, "addr", "replace", address, "dev", name),
                ),
                RenderedCommand(
                    kind="interface.link.up",
                    argv=("ip", "-n", self.namespace, "link", "set", "dev", name, "up"),
                ),
            ),
            name,
        )

    def _render_sysctl(self, operation: Mapping[str, Any]) -> RenderedCommand:
        if operation.get("setting") != "net.ipv4.ip_forward":
            raise UnsupportedOperation("the current adapter supports only net.ipv4.ip_forward")
        value = operation.get("value")
        if type(value) is not int or value not in (0, 1):
            raise UnsupportedOperation("net.ipv4.ip_forward must be the integer 0 or 1")
        return RenderedCommand(
            kind="sysctl.ipv4_forward",
            argv=(
                "ip",
                "netns",
                "exec",
                self.namespace,
                "sysctl",
                "-q",
                "-w",
                f"net.ipv4.ip_forward={value}",
            ),
        )

    def _render_firewall(
        self,
        operation: Mapping[str, Any],
    ) -> tuple[tuple[RenderedCommand, ...], tuple[str, str]]:
        try:
            ruleset = compile_firewall_intent(operation)
        except NftablesBackendError as exc:
            raise UnsupportedOperation(str(exc)) from exc

        for interface in (ruleset.lan_interface, ruleset.wan_interface):
            if interface not in self.allowed_interfaces:
                raise TargetValidationError("firewall interface is outside the adapter allowlist")

        nft_base = ("ip", "netns", "exec", self.namespace, "nft")
        return (
            (
                RenderedCommand(
                    kind="nftables.stage.filter_table",
                    argv=nft_base + ("add", "table", "inet", FILTER_TABLE),
                    check=False,
                ),
                RenderedCommand(
                    kind="nftables.stage.nat_table",
                    argv=nft_base + ("add", "table", "ip", NAT_TABLE),
                    check=False,
                ),
                RenderedCommand(
                    kind="nftables.check",
                    argv=nft_base + ("--check", "-f", "-"),
                    stdin=ruleset.script,
                ),
                RenderedCommand(
                    kind="nftables.apply",
                    argv=nft_base + ("-f", "-"),
                    stdin=ruleset.script,
                ),
            ),
            (ruleset.lan_interface, ruleset.wan_interface),
        )

    def execute(self, plan: Mapping[str, Any]) -> ExecutionResult:
        """Execute a completely preflighted plan inside the approved namespace."""
        prepared = self.preflight(plan)

        if os.geteuid() != 0:
            raise TargetValidationError("privileged adapter execution requires root")

        ip_path = shutil.which("ip")
        sysctl_path = shutil.which("sysctl")
        needs_nft = any("nft" in command.argv for command in prepared.commands)
        nft_path = shutil.which("nft") if needs_nft else None
        if not ip_path or not sysctl_path or (needs_nft and not nft_path):
            raise TargetValidationError("required Linux networking tools are unavailable")

        self._verify_namespace(ip_path)
        for interface in prepared.required_interfaces:
            self._verify_interface(ip_path, interface)

        for command in prepared.commands:
            argv = self._materialize(
                command.argv,
                ip_path=ip_path,
                sysctl_path=sysctl_path,
                nft_path=nft_path,
            )
            self._run(argv, check=command.check, input_text=command.stdin)

        return ExecutionResult(
            namespace=prepared.namespace,
            revision=prepared.revision,
            commands_executed=len(prepared.commands),
        )

    def _verify_namespace(self, ip_path: str) -> None:
        result = self._run((ip_path, "netns", "list"), capture=True)
        names = {line.split()[0] for line in result.stdout.splitlines() if line.strip()}
        if self.namespace not in names:
            raise TargetValidationError("approved execution namespace does not exist")

    def _verify_interface(self, ip_path: str, interface: str) -> None:
        result = self._run(
            (ip_path, "-n", self.namespace, "link", "show", "dev", interface),
            check=False,
            capture=True,
        )
        if result.returncode != 0:
            raise TargetValidationError("required allowlisted interface does not exist in the namespace")

    @staticmethod
    def _materialize(
        argv: Sequence[str],
        *,
        ip_path: str,
        sysctl_path: str,
        nft_path: str | None = None,
    ) -> tuple[str, ...]:
        materialized = list(argv)
        if not materialized or materialized[0] != "ip":
            raise AdapterError("rendered command must use the ip entrypoint")
        materialized[0] = ip_path
        if len(materialized) >= 5 and materialized[1:3] == ["netns", "exec"]:
            backend = materialized[4]
            if backend == "sysctl":
                materialized[4] = sysctl_path
            elif backend == "nft":
                if not nft_path:
                    raise AdapterError("nftables backend path is unavailable")
                materialized[4] = nft_path
            else:
                raise AdapterError("namespace execution may invoke only approved backends")
        return tuple(materialized)

    def _run(
        self,
        argv: Sequence[str],
        *,
        check: bool = True,
        capture: bool = False,
        input_text: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        kwargs: dict[str, Any] = {
            "check": check,
            "text": True,
            "stdout": subprocess.PIPE if capture else subprocess.DEVNULL,
            "stderr": subprocess.PIPE,
        }
        if input_text is not None:
            kwargs["input"] = input_text
        return self._runner(list(argv), **kwargs)
