#!/usr/bin/env bash
# Detect the real Q10 over USB on macOS. Does not change the phone.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
source "${ROOT}/scripts/q10-common.sh"
q10_load_local_env

PHONE_USB_PRESENT=no
USB_NETWORK_PRESENT=no
DEVICE_IP=""
HOST_IFACE=""
HOST_IP=""
PING_OK=no
QCONN_OK=no
HTTP_OK=no
DEPLOY_AVAILABLE=no
CONNECT_AVAILABLE=no
SSH_AVAILABLE=no
DEV_MODE=unknown

if [[ "$(q10_usb_present)" == "yes" ]]; then
  PHONE_USB_PRESENT=yes
fi

HOST_IFACE="$(q10_net_iface || true)"
if [[ -n "${HOST_IFACE}" ]]; then
  USB_NETWORK_PRESENT=yes
  HOST_IP="$(q10_host_ip "${HOST_IFACE}" || true)"
fi

DEVICE_IP="$(q10_device_ip || true)"
if [[ -n "${DEVICE_IP}" ]] && q10_ping_ok "${DEVICE_IP}"; then
  PING_OK=yes
fi
if [[ -n "${DEVICE_IP}" ]] && q10_port_open "${DEVICE_IP}" 4455; then
  QCONN_OK=yes
fi
if [[ -n "${DEVICE_IP}" ]] && q10_port_open "${DEVICE_IP}" 443; then
  HTTP_OK=yes
fi

BB_BIN=""
if BB_BIN="$(q10_find_bb_tools)"; then
  [[ -x "${BB_BIN}/blackberry-deploy" ]] && DEPLOY_AVAILABLE=yes
  [[ -x "${BB_BIN}/blackberry-connect" ]] && CONNECT_AVAILABLE=yes
fi

if [[ "${DEPLOY_AVAILABLE}" == "yes" && -n "${DEVICE_IP}" ]]; then
  # Never probe listDeviceInfo without a password: after restore the phone
  # counts those as failed auth (5 and you wait).
  if [[ -z "${Q10_DEVICE_PASSWORD:-}" ]]; then
    DEV_MODE=skipped_no_password
  else
  _dm_out="$(python3 - "${BB_BIN}/blackberry-deploy" "${DEVICE_IP}" <<'PY'
import os, subprocess, sys
cmd = [sys.argv[1], "-listDeviceInfo", "-device", sys.argv[2], "-password", os.environ.get("Q10_DEVICE_PASSWORD", "")]
try:
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=12)
    sys.stdout.write(r.stdout)
    sys.stderr.write(r.stderr)
except subprocess.TimeoutExpired:
    print("Error: listDeviceInfo timed out")
PY
)"
  if echo "${_dm_out}" | grep -q 'Development Mode'; then
    DEV_MODE=no
  elif echo "${_dm_out}" | grep -qi 'password'; then
    DEV_MODE=yes_needs_password
  elif echo "${_dm_out}" | grep -qi 'timed out'; then
    DEV_MODE=timeout
  elif echo "${_dm_out}" | grep -qi 'Error:'; then
    DEV_MODE=error
  else
    DEV_MODE=yes
  fi
  fi
fi

if [[ -n "${DEVICE_IP}" ]] && q10_port_open "${DEVICE_IP}" 22; then
  SSH_AVAILABLE=yes
fi

cat <<EOF
Q10 DETECT  $(q10_timestamp)
PHONE_USB_PRESENT     ${PHONE_USB_PRESENT}
USB_NETWORK_PRESENT   ${USB_NETWORK_PRESENT}
HOST_IFACE            ${HOST_IFACE:-none}
HOST_IP               ${HOST_IP:-none}
DEVICE_IP             ${DEVICE_IP:-none}
PING_OK               ${PING_OK}
QCONN_4455            ${QCONN_OK}
HTTP_443              ${HTTP_OK}
DEV_MODE              ${DEV_MODE}
DEPLOY_AVAILABLE      ${DEPLOY_AVAILABLE}
CONNECT_AVAILABLE     ${CONNECT_AVAILABLE}
SSH_AVAILABLE         ${SSH_AVAILABLE}
BB10_HOST_BIN         ${BB_BIN:-none}
EOF

mkdir -p "${ROOT}/logs"
{
  echo "----- $(q10_timestamp) -----"
  echo "PHONE_USB_PRESENT=${PHONE_USB_PRESENT}"
  echo "USB_NETWORK_PRESENT=${USB_NETWORK_PRESENT}"
  echo "HOST_IFACE=${HOST_IFACE}"
  echo "HOST_IP=${HOST_IP}"
  echo "DEVICE_IP=${DEVICE_IP}"
  echo "PING_OK=${PING_OK}"
  echo "QCONN_4455=${QCONN_OK}"
  echo "DEPLOY_AVAILABLE=${DEPLOY_AVAILABLE}"
  echo "SSH_AVAILABLE=${SSH_AVAILABLE}"
} >> "${ROOT}/logs/q10-detect.log"

if [[ "${PHONE_USB_PRESENT}" == "yes" && "${PING_OK}" == "yes" ]]; then
  exit 0
fi
exit 1
