#!/usr/bin/env bash
# Usage: ./scripts/q10-shell.sh [remote command...]
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
source "${ROOT}/scripts/q10-common.sh"
q10_load_local_env

KEY="${Q10_SSH_KEY:-${HOME}/.ssh/q10-usb}"
DEVICE_IP="$(q10_device_ip || true)"
if [[ -z "${DEVICE_IP}" ]]; then
  echo "DEVICE_IP not found"
  exit 1
fi
if [[ ! -f "${KEY}" ]]; then
  echo "Missing ${KEY}. Run ./scripts/q10-connect.sh first."
  exit 1
fi

q10_ssh_opts
if [[ "${Q10_SSH_VERBOSE:-}" == "1" ]]; then
  SSH_OPTS=(-vvv "${SSH_OPTS[@]}")
fi
if [[ $# -eq 0 ]]; then
  exec ssh "${SSH_OPTS[@]}" "devuser@${DEVICE_IP}"
fi
exec ssh "${SSH_OPTS[@]}" "devuser@${DEVICE_IP}" "$@"
