#!/usr/bin/env bash
# High-level health for the current lab phase.
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
  remote="$("${ROOT}/scripts/q10-shell.sh" 'echo BC=$(test -d /accounts/1000/shared/misc/berrycore && echo yes || echo no); echo MON=$(test -f /accounts/1000/shared/misc/q10-monitor.py && echo yes || echo no); echo T49=$(ls -d /accounts/1000/appdata/com.example.Term49.* 2>/dev/null | wc -l)' 2>/dev/null || true)"
  echo "BerryCore       $(printf '%s\n' "${remote}" | awk -F= '/^BC=/{print $2; exit}')"
  echo "Term49          $(printf '%s\n' "${remote}" | awk -F= '/^T49=/{print ($2+0>0)?"yes":"no"; exit}')"
  echo "Monitor         $(printf '%s\n' "${remote}" | awk -F= '/^MON=/{print $2; exit}')"
else
  echo "SSH             not configured"
  echo "BerryCore       unknown"
  echo "Term49          unknown"
  echo "Monitor         unknown"
fi

HUB="${Q10_MONITOR_URL:-http://169.254.0.2:8790/snapshot.json}"
if curl --noproxy '*' -sS -m 3 -o /dev/null -w '' "${HUB}"; then
  echo "Hub 8790        OK  ${HUB}"
else
  echo "Hub 8790        FAIL  ${HUB}"
fi
