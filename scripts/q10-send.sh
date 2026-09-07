#!/usr/bin/env bash
# Push a command script onto the Q10. Paste on the Mac; do not type on the phone.
#
#   ./scripts/q10-send.sh                  # stdin → /var/tmp/q10-last.sh
#   ./scripts/q10-send.sh --clipboard      # Mac 剪贴板
#   ./scripts/q10-send.sh --run            # 写完后用 USB SSH（devuser）执行
#   pbpaste | ./scripts/q10-send.sh --name install-berrycore
#
# Term49 与 SSH 不是同一个用户。要在 Term49 里跑，写完后在手机上只打：
#   sh /var/tmp/q10-last.sh
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
source "${ROOT}/scripts/q10-common.sh"
q10_load_local_env

REMOTE_NAME="q10-last.sh"
DO_RUN=0
USE_CLIP=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --clipboard|-c) USE_CLIP=1; shift ;;
    --run|-r) DO_RUN=1; shift ;;
    --name|-n) REMOTE_NAME="$2"; shift 2 ;;
    --) shift; break ;;
    -*) echo "Unknown flag $1"; exit 1 ;;
    *) break ;;
  esac
done

KEY="${Q10_SSH_KEY:-${HOME}/.ssh/q10-usb}"
DEVICE_IP="$(q10_device_ip || true)"
if [[ -z "${DEVICE_IP}" || ! -f "${KEY}" ]]; then
  echo "Need live USB IP and ${KEY}. Run detect + connect first."
  exit 1
fi

TMP="$(mktemp)"
cleanup() { rm -f "${TMP}"; }
trap cleanup EXIT

if [[ "${USE_CLIP}" == "1" ]]; then
  pbpaste > "${TMP}"
elif [[ $# -gt 0 ]]; then
  printf '%s\n' "$*" > "${TMP}"
else
  cat > "${TMP}"
fi

if [[ ! -s "${TMP}" ]]; then
  echo "Nothing to send (empty stdin/clipboard)."
  exit 1
fi

# Remote path is world-readable so Term49 (user 1000) can sh it.
REMOTE="/var/tmp/${REMOTE_NAME}"
q10_ssh_opts
ssh "${SSH_OPTS[@]}" "devuser@${DEVICE_IP}" \
  "cat > '${REMOTE}' && chmod 755 '${REMOTE}' && wc -c '${REMOTE}'" < "${TMP}"

echo "WROTE ${REMOTE}  ($(wc -c < "${TMP}" | tr -d ' ') bytes)"
echo "Term49:  sh ${REMOTE}"
echo "SSH:     ./scripts/q10-shell.sh 'sh ${REMOTE}'"

if [[ "${DO_RUN}" == "1" ]]; then
  echo "----- run as devuser -----"
  ssh "${SSH_OPTS[@]}" "devuser@${DEVICE_IP}" "sh '${REMOTE}'"
fi
