#!/usr/bin/env bash
# High-level health. BerryCore fields stay unknown until that phase.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
source "${ROOT}/scripts/q10-common.sh"
q10_load_local_env

detect_out="$("${ROOT}/scripts/q10-detect.sh" || true)"
echo "${detect_out}"
echo
echo "Q10 HEALTH"
echo "USB             $(echo "${detect_out}" | awk '/PHONE_USB_PRESENT/{print $2}')"
echo "Network         $(echo "${detect_out}" | awk '/PING_OK/{print $2}')"
echo "QConn           $(echo "${detect_out}" | awk '/QCONN_4455/{print $2}')"
echo "Deploy tool     $(echo "${detect_out}" | awk '/DEPLOY_AVAILABLE/{print $2}')"
echo "SSH port        $(echo "${detect_out}" | awk '/SSH_AVAILABLE/{print $2}')"

KEY="${Q10_SSH_KEY:-${HOME}/.ssh/q10-usb}"
DEVICE_IP="$(echo "${detect_out}" | awk '/DEVICE_IP/{print $2}')"
if [[ "${DEVICE_IP}" != "none" && -f "${KEY}" ]]; then
  if out="$("${ROOT}/scripts/q10-shell.sh" 'uname -a' 2>/dev/null)"; then
    echo "SSH             OK"
    echo "uname           ${out}"
  else
    echo "SSH             FAIL (connect session missing?)"
  fi
else
  echo "SSH             not configured"
fi

echo "BerryCore       not installed this phase"
echo "Term49          not installed this phase"
