#!/usr/bin/env bash
set -u

RULE_SRC="/home/hit/ROS/config/99-hwk-pressure.rules"
RULE_DST="/etc/udev/rules.d/99-hwk-pressure.rules"

EXPECTED_PATHS=(
  "pci-0000:00:14.0-usb-0:2.4.3.2.2:1.0"
  "pci-0000:00:14.0-usb-0:2.4.3.2.4:1.0"
  "pci-0000:00:14.0-usb-0:2.4.1.1:1.0"
  "pci-0000:00:14.0-usb-0:2.4.4.2:1.0"
)

RIGHT_HUB_SYSFS=(
  "3-2.4.1"
  "3-2.4.4"
)

usage() {
  cat <<'EOF'
Usage:
  scripts/hwk_pressure_usb_recover.sh
      Diagnose current HWK pressure USB serial status.

  sudo scripts/hwk_pressure_usb_recover.sh --install-udev
      Install /home/hit/ROS/config/99-hwk-pressure.rules to /etc and reload udev.

  sudo scripts/hwk_pressure_usb_recover.sh --reset-right-hubs
      Reset the two parent USB hubs that previously hosted the right gripper CH340 devices.
      This may briefly disconnect other USB devices on those hub branches.

  sudo scripts/hwk_pressure_usb_recover.sh --install-udev --reset-right-hubs
      Do both privileged recovery actions, then print status again.
EOF
}

section() {
  printf '\n=== %s ===\n' "$1"
}

have() {
  command -v "$1" >/dev/null 2>&1
}

count_ch340() {
  lsusb 2>/dev/null | grep -c '1a86:7523'
}

print_status() {
  section "CH340 devices"
  if have lsusb; then
    lsusb | grep '1a86:7523' || true
    printf 'count=%s expected=4\n' "$(count_ch340)"
  else
    echo "lsusb not found"
  fi

  section "ttyUSB nodes"
  ls -l /dev/ttyUSB* /dev/hwk_pressure_* 2>/dev/null || true

  section "serial by-path links"
  find /dev/serial/by-path -maxdepth 1 -type l -printf '%p -> %l\n' 2>/dev/null | sort || true

  section "expected HWK paths"
  for path in "${EXPECTED_PATHS[@]}"; do
    link="/dev/serial/by-path/${path}-port0"
    if [ -e "$link" ]; then
      printf 'OK   %s -> %s\n' "$link" "$(readlink "$link")"
    else
      printf 'MISS %s\n' "$link"
    fi
  done

  section "installed udev rule"
  if [ -f "$RULE_DST" ]; then
    if cmp -s "$RULE_SRC" "$RULE_DST"; then
      echo "OK   $RULE_DST matches $RULE_SRC"
    else
      echo "WARN $RULE_DST differs from $RULE_SRC"
      echo "     Run: sudo $0 --install-udev"
    fi
  else
    echo "MISS $RULE_DST"
    echo "     Run: sudo $0 --install-udev"
  fi

  section "recent kernel events"
  if have journalctl; then
    journalctl -k --since 'today' --no-pager 2>/dev/null \
      | grep -Ei 'ch341|ttyUSB|1a86|device descriptor|over-current|unable to enumerate|USB disconnect' \
      | tail -n 80 || true
  else
    dmesg --ctime 2>/dev/null \
      | grep -Ei 'ch341|ttyUSB|1a86|device descriptor|over-current|unable to enumerate|USB disconnect' \
      | tail -n 80 || true
  fi
}

install_udev() {
  if [ "$(id -u)" -ne 0 ]; then
    echo "ERROR: --install-udev requires root. Re-run with sudo." >&2
    return 1
  fi
  if [ ! -f "$RULE_SRC" ]; then
    echo "ERROR: missing rule source: $RULE_SRC" >&2
    return 1
  fi
  install -m 0644 "$RULE_SRC" "$RULE_DST"
  udevadm control --reload-rules
  udevadm trigger
  echo "Installed and reloaded: $RULE_DST"
}

reset_right_hubs() {
  if [ "$(id -u)" -ne 0 ]; then
    echo "ERROR: --reset-right-hubs requires root. Re-run with sudo." >&2
    return 1
  fi
  if ! have usbreset; then
    echo "ERROR: usbreset not found" >&2
    return 1
  fi
  for hub in "${RIGHT_HUB_SYSFS[@]}"; do
    sysfs="/sys/bus/usb/devices/$hub"
    if [ ! -e "$sysfs" ]; then
      echo "SKIP missing hub sysfs path: $sysfs"
      continue
    fi
    devname="$(udevadm info --query=property --path="$sysfs" 2>/dev/null | sed -n 's/^DEVNAME=//p')"
    if [ -z "$devname" ]; then
      echo "SKIP cannot resolve DEVNAME for $hub"
      continue
    fi
    echo "Resetting $hub via $devname"
    usbreset "$devname" || true
    sleep 2
  done
  udevadm trigger
}

do_install=0
do_reset=0

for arg in "$@"; do
  case "$arg" in
    --install-udev)
      do_install=1
      ;;
    --reset-right-hubs)
      do_reset=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $arg" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [ "$do_install" -eq 1 ]; then
  install_udev || exit 1
fi

if [ "$do_reset" -eq 1 ]; then
  reset_right_hubs || exit 1
fi

print_status
