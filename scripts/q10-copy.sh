#!/usr/bin/env bash
# Usage:
#   ./scripts/q10-copy.sh put local remote
#   ./scripts/q10-copy.sh get remote local
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
source "${ROOT}/scripts/q10-common.sh"
q10_load_local_env

KEY="${Q10_SSH_KEY:-${HOME}/.ssh/q10-usb}"
DEVICE_IP="$(q10_device_ip || true)"
mode="${1:-}"
src="${2:-}"
dst="${3:-}"
if [[ -z "${mode}" || -z "${src}" || -z "${dst}" ]]; then
  echo "Usage: $0 put <local> <remote>"
  echo "       $0 get <remote> <local>"
  exit 1
fi
if [[ -z "${DEVICE_IP}" || ! -f "${KEY}" ]]; then
  echo "Need DEVICE_IP and ${KEY}. Run detect + connect first."
  exit 1
fi

q10_ssh_opts
case "${mode}" in
  put) exec scp "${SSH_OPTS[@]}" "${src}" "devuser@${DEVICE_IP}:${dst}" ;;
  get) exec scp "${SSH_OPTS[@]}" "devuser@${DEVICE_IP}:${src}" "${dst}" ;;
  *) echo "mode must be put or get"; exit 1 ;;
esac
