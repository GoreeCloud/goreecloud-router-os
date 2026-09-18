#!/bin/sh
set -eu

PROFILE_ID="glinet-gl-mt5000"
ROOT="/"

usage() {
  cat <<'EOF'
Usage: collect_gl_mt5000_hardware.sh [--root PATH]

Collect a privacy-minimized, non-mutating GL-MT5000 hardware report to stdout.
The script reads an allowlisted set of system files and sysfs attributes only.
It does not change networking, UCI configuration, boot state, partitions, MTD,
firewall rules, services, or firmware.

--root PATH  Read from an alternate filesystem root. Intended for tests only.
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --root)
      [ "$#" -ge 2 ] || { echo "missing value for --root" >&2; exit 2; }
      ROOT="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

case "$ROOT" in
  /*) ;;
  *) echo "--root must be an absolute path" >&2; exit 2 ;;
esac

root_path() {
  if [ "$ROOT" = "/" ]; then
    printf '/%s' "$1"
  else
    printf '%s/%s' "${ROOT%/}" "$1"
  fi
}

section() {
  printf '\n[%s]\n' "$1"
}

emit_file() {
  label="$1"
  rel="$2"
  path="$(root_path "$rel")"
  if [ -r "$path" ]; then
    section "$label"
    cat "$path"
    printf '\n'
  fi
}

emit_nul_file() {
  label="$1"
  rel="$2"
  path="$(root_path "$rel")"
  if [ -r "$path" ]; then
    section "$label"
    tr '\000' '\n' < "$path"
    printf '\n'
  fi
}

emit_attr() {
  key="$1"
  path="$2"
  if [ -r "$path" ]; then
    value="$(cat "$path" 2>/dev/null || true)"
    [ -n "$value" ] && printf '%s=%s\n' "$key" "$value"
  fi
}

printf 'goreecloud_router_os_hardware_discovery=0.1\n'
printf 'profile_id=%s\n' "$PROFILE_ID"
printf 'collector_mode=non-mutating\n'
printf 'privacy=device-unique-identifiers-excluded\n'

emit_file "board.model" "tmp/sysinfo/model"
emit_file "board.name" "tmp/sysinfo/board_name"
emit_file "os.openwrt_release" "etc/openwrt_release"
emit_file "os.release" "etc/os-release"

CPUINFO="$(root_path "proc/cpuinfo")"
if [ -r "$CPUINFO" ]; then
  section "cpu.summary"
  awk '
    /^[[:space:]]*processor[[:space:]]*:/ ||
    /^[[:space:]]*model name[[:space:]]*:/ ||
    /^[[:space:]]*BogoMIPS[[:space:]]*:/ ||
    /^[[:space:]]*Features[[:space:]]*:/ ||
    /^[[:space:]]*CPU implementer[[:space:]]*:/ ||
    /^[[:space:]]*CPU architecture[[:space:]]*:/ ||
    /^[[:space:]]*CPU variant[[:space:]]*:/ ||
    /^[[:space:]]*CPU part[[:space:]]*:/ ||
    /^[[:space:]]*CPU revision[[:space:]]*:/ ||
    /^[[:space:]]*Hardware[[:space:]]*:/ { print }
  ' "$CPUINFO"
fi

emit_nul_file "devicetree.model" "sys/firmware/devicetree/base/model"
emit_nul_file "devicetree.compatible" "sys/firmware/devicetree/base/compatible"

DTROOT="$(root_path "sys/firmware/devicetree/base")"
if [ -d "$DTROOT" ]; then
  section "devicetree.node_paths"
  (
    cd "$DTROOT"
    find . -type d -print 2>/dev/null | LC_ALL=C sort
  )
fi

emit_file "storage.mtd" "proc/mtd"
emit_file "storage.partitions" "proc/partitions"

BLOCKROOT="$(root_path "sys/class/block")"
if [ -d "$BLOCKROOT" ]; then
  section "storage.sysfs"
  for dev in "$BLOCKROOT"/*; do
    [ -e "$dev" ] || continue
    name="$(basename "$dev")"
    printf 'device=%s\n' "$name"
    emit_attr "  dev" "$dev/dev"
    emit_attr "  size_sectors" "$dev/size"
    emit_attr "  start_sector" "$dev/start"
    emit_attr "  read_only" "$dev/ro"
    emit_attr "  removable" "$dev/removable"
  done
fi

NETROOT="$(root_path "sys/class/net")"
if [ -d "$NETROOT" ]; then
  section "network.interfaces"
  for netdev in "$NETROOT"/*; do
    [ -e "$netdev" ] || continue
    name="$(basename "$netdev")"
    printf 'interface=%s\n' "$name"
    emit_attr "  ifindex" "$netdev/ifindex"
    emit_attr "  type" "$netdev/type"
    emit_attr "  operstate" "$netdev/operstate"
    emit_attr "  carrier" "$netdev/carrier"
    emit_attr "  speed_mbps" "$netdev/speed"
    emit_attr "  duplex" "$netdev/duplex"
    emit_attr "  phys_port_name" "$netdev/phys_port_name"
    if [ -L "$netdev/device" ]; then
      printf '  device_path=%s\n' "$(readlink "$netdev/device" 2>/dev/null || true)"
    fi
    if [ -L "$netdev/device/driver" ]; then
      printf '  driver_path=%s\n' "$(readlink "$netdev/device/driver" 2>/dev/null || true)"
    fi
  done
fi

BOARD_JSON="$(root_path "etc/board.json")"
if [ "$ROOT" = "/" ] && [ -r "$BOARD_JSON" ] && command -v jsonfilter >/dev/null 2>&1; then
  section "board.network_roles"
  for role in lan wan wan6; do
    value="$(jsonfilter -i "$BOARD_JSON" -e "@.network.$role.device" 2>/dev/null || true)"
    [ -n "$value" ] && printf '%s.device=%s\n' "$role" "$value"
  done
fi

WATCHROOT="$(root_path "sys/class/watchdog")"
if [ -d "$WATCHROOT" ]; then
  section "watchdog"
  for wd in "$WATCHROOT"/*; do
    [ -e "$wd" ] || continue
    printf 'watchdog=%s\n' "$(basename "$wd")"
    emit_attr "  identity" "$wd/identity"
    emit_attr "  state" "$wd/state"
    emit_attr "  status" "$wd/status"
    emit_attr "  nowayout" "$wd/nowayout"
  done
fi

THERMROOT="$(root_path "sys/class/thermal")"
if [ -d "$THERMROOT" ]; then
  section "thermal"
  for zone in "$THERMROOT"/thermal_zone*; do
    [ -e "$zone" ] || continue
    printf 'zone=%s\n' "$(basename "$zone")"
    emit_attr "  type" "$zone/type"
    emit_attr "  temp_millicelsius" "$zone/temp"
  done
fi

GPIOROOT="$(root_path "sys/class/gpio")"
if [ -d "$GPIOROOT" ]; then
  section "gpio.controllers"
  for chip in "$GPIOROOT"/gpiochip*; do
    [ -e "$chip" ] || continue
    printf 'controller=%s\n' "$(basename "$chip")"
    emit_attr "  label" "$chip/label"
    emit_attr "  base" "$chip/base"
    emit_attr "  ngpio" "$chip/ngpio"
  done
fi

emit_file "kernel.modules" "proc/modules"

if [ "$ROOT" = "/" ]; then
  section "tools.available"
  for tool in nft ip bridge ethtool ubus jsonfilter block fw_printenv; do
    if command -v "$tool" >/dev/null 2>&1; then
      printf '%s=present\n' "$tool"
    else
      printf '%s=absent\n' "$tool"
    fi
  done
fi

printf '\n[collector.boundary]\n'
printf 'network_configuration_changed=false\n'
printf 'boot_environment_changed=false\n'
printf 'storage_layout_changed=false\n'
printf 'firmware_changed=false\n'
printf 'device_unique_addresses_collected=false\n'
printf 'credentials_collected=false\n'
