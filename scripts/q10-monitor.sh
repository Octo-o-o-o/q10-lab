#!/usr/bin/env bash
# Push and/or run the Q10 keyboard AI Monitor.
#   ./scripts/q10-monitor.sh            # push + device --once --all
#   ./scripts/q10-monitor.sh --local    # Mac preview of 127.0.0.1:8790
#   ./scripts/q10-monitor.sh --push     # copy files only
#   ./scripts/q10-monitor.sh --demo     # explicit DEMO on the device
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
source "${ROOT}/scripts/q10-common.sh"
q10_load_local_env

MODE="device"
DO_PUSH=1
DO_RUN=1
DEMO=0
EXTRA=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --local) MODE="local"; DO_PUSH=0; shift ;;
    --push) DO_RUN=0; shift ;;
    --demo) DEMO=1; shift ;;
    --watch) EXTRA+=(--watch); shift ;;
    --once) EXTRA+=(--once); shift ;;
    --page) EXTRA+=(--page "$2"); shift 2 ;;
    *) EXTRA+=("$1"); shift ;;
  esac
done

SRC="${ROOT}/ai-terminal/q10_monitor.py"
DEMO_JSON="${ROOT}/ai-terminal/fixtures/snapshot_demo.json"
AUTO="${ROOT}/ai-terminal/q10-autostart.sh"
REMOTE_DIR="/accounts/1000/shared/misc"
REMOTE_PY="${REMOTE_DIR}/q10-monitor.py"
REMOTE_DEMO="${REMOTE_DIR}/q10-monitor-demo.json"
REMOTE_WRAP="${REMOTE_DIR}/q10mon"
REMOTE_AUTO="${REMOTE_DIR}/q10-autostart.sh"

if [[ "${MODE}" == "local" ]]; then
  ARGS=(--once --all --url "${Q10_MONITOR_URL:-http://127.0.0.1:8790/snapshot.json}")
  if [[ "${DEMO}" == "1" ]]; then
    ARGS=(--once --all --demo)
  fi
  exec python3 "${SRC}" "${ARGS[@]}" "${EXTRA[@]}"
fi

if [[ "${DO_PUSH}" == "1" ]]; then
  KEY="${Q10_SSH_KEY:-${HOME}/.ssh/q10-usb}"
  DEVICE_IP="$(q10_device_ip || true)"
  if [[ -z "${DEVICE_IP}" || ! -f "${KEY}" ]]; then
    echo "Need live USB IP and ${KEY}."
    exit 1
  fi
  q10_ssh_opts
  WRAP=$'#!/bin/sh\nexport LANG="${LANG:-en_US.UTF-8}"\nexport LC_ALL="${LC_ALL:-en_US.UTF-8}"\nexport PYTHONIOENCODING=utf-8\nexec /usr/bin/python3.2 /accounts/1000/shared/misc/q10-monitor.py "$@"\n'
  ssh "${SSH_OPTS[@]}" "devuser@${DEVICE_IP}" \
    "cat > '${REMOTE_PY}' && chmod 755 '${REMOTE_PY}'" < "${SRC}"
  ssh "${SSH_OPTS[@]}" "devuser@${DEVICE_IP}" \
    "cat > '${REMOTE_DEMO}' && chmod 644 '${REMOTE_DEMO}'" < "${DEMO_JSON}"
  ssh "${SSH_OPTS[@]}" "devuser@${DEVICE_IP}" \
    "cat > '${REMOTE_AUTO}' && chmod 755 '${REMOTE_AUTO}'" < "${AUTO}"
  printf '%s' "${WRAP}" | ssh "${SSH_OPTS[@]}" "devuser@${DEVICE_IP}" \
    "cat > '${REMOTE_WRAP}' && chmod 755 '${REMOTE_WRAP}'"
  echo "PUSHED ${REMOTE_PY} ${REMOTE_AUTO}"
fi

if [[ "${DO_RUN}" == "1" ]]; then
  ARGS=(--once --all)
  if [[ "${DEMO}" == "1" ]]; then
    ARGS=(--once --all --demo)
  fi
  "${ROOT}/scripts/q10-shell.sh" \
    "export LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8 PYTHONIOENCODING=utf-8; /usr/bin/python3.2 '${REMOTE_PY}' ${ARGS[*]}"
fi
