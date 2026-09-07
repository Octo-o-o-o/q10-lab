#!/usr/bin/env bash
# 推送并/或运行 Q10 键盘监视器。
#   ./scripts/q10-monitor.sh            # 推送 + 设备 --once --all
#   ./scripts/q10-monitor.sh --local    # Mac 预览 127.0.0.1:8787
#   ./scripts/q10-monitor.sh --push     # 只拷文件
#   ./scripts/q10-monitor.sh --demo     # 设备上显式演示数据
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
FONT="${ROOT}/ai-terminal/q10-term49-font.sh"
WRAP="${ROOT}/ai-terminal/q10mon"
REMOTE_DIR="/accounts/1000/shared/misc"
REMOTE_PY="${REMOTE_DIR}/q10-monitor.py"
REMOTE_DEMO="${REMOTE_DIR}/q10-monitor-demo.json"
REMOTE_WRAP="${REMOTE_DIR}/q10mon"
REMOTE_AUTO="${REMOTE_DIR}/q10-autostart.sh"
REMOTE_FONT="${REMOTE_DIR}/q10-term49-font.sh"

if [[ "${MODE}" == "local" ]]; then
  if [[ "${DEMO}" == "1" ]]; then
    exec python3 "${SRC}" --once --all --lang zh --demo "${EXTRA[@]}"
  fi
  HUB="$(q10_resolve_hub_url || true)"
  if [[ -z "${HUB}" ]]; then
    echo "Hub 未响应 $(q10_hub_ports_csv)。不要在本仓库另起 Hub。"
    exit 1
  fi
  exec python3 "${SRC}" --once --all --lang zh --url "${HUB}" "${EXTRA[@]}"
fi

if [[ "${DO_PUSH}" == "1" ]]; then
  KEY="${Q10_SSH_KEY:-${HOME}/.ssh/q10-usb}"
  DEVICE_IP="$(q10_device_ip || true)"
  if [[ -z "${DEVICE_IP}" || ! -f "${KEY}" ]]; then
    echo "需要 USB 在线，并且有 ${KEY}。"
    exit 1
  fi
  q10_ssh_opts
  ssh "${SSH_OPTS[@]}" "devuser@${DEVICE_IP}" \
    "cat > '${REMOTE_PY}' && chmod 755 '${REMOTE_PY}'" < "${SRC}"
  ssh "${SSH_OPTS[@]}" "devuser@${DEVICE_IP}" \
    "cat > '${REMOTE_DEMO}' && chmod 644 '${REMOTE_DEMO}'" < "${DEMO_JSON}"
  ssh "${SSH_OPTS[@]}" "devuser@${DEVICE_IP}" \
    "cat > '${REMOTE_AUTO}' && chmod 755 '${REMOTE_AUTO}'" < "${AUTO}"
  ssh "${SSH_OPTS[@]}" "devuser@${DEVICE_IP}" \
    "cat > '${REMOTE_FONT}' && chmod 755 '${REMOTE_FONT}'" < "${FONT}"
  ssh "${SSH_OPTS[@]}" "devuser@${DEVICE_IP}" \
    "cat > '${REMOTE_WRAP}' && chmod 755 '${REMOTE_WRAP}'" < "${WRAP}"
  ssh "${SSH_OPTS[@]}" "devuser@${DEVICE_IP}" \
    "if [ -f /accounts/1000/shared/misc/q10-mailbox.token ]; then chmod 640 /accounts/1000/shared/misc/q10-mailbox.token; fi"
  PORTS_CSV="$(q10_hub_ports_csv)"
  LIVE_HUB="$(q10_resolve_hub_url || true)"
  LIVE_PORT="8787"
  if [[ "${LIVE_HUB}" == http://* ]]; then
    LIVE_PORT="$(python3 -c 'import sys
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse
p = urlparse(sys.argv[1])
print(p.port or 8787)' "${LIVE_HUB}")"
  fi
  ssh "${SSH_OPTS[@]}" "devuser@${DEVICE_IP}" \
    "Q10_SYNC_PORTS='${PORTS_CSV}' Q10_SYNC_PORT='${LIVE_PORT}' python3.2 -" <<'PY'
import os, re
ports = os.environ.get("Q10_SYNC_PORTS", "8787,8790").strip()
pref = os.environ.get("Q10_SYNC_PORT", "8787").strip() or "8787"
path = "/accounts/1000/shared/misc/q10-mailbox.env"
try:
    text = open(path, "r").read()
except Exception:
    text = ""
lines = [ln for ln in text.splitlines() if not ln.startswith("Q10_HUB_PORTS=")]
out = []
for ln in lines:
    if ln.startswith("Q10_LAN_HUB_URL="):
        ln = re.sub(r":\d+", ":" + pref, ln, count=1)
    out.append(ln)
out.append("Q10_HUB_PORTS=" + ports)
open(path, "w").write("\n".join(out) + "\n")
print("HUB_PORTS", ports)
print("LAN_PORT", pref)
print("LAN_HAS_8790", any(":8790" in ln and ln.startswith("Q10_LAN_HUB_URL=") for ln in out))
PY
  MONO="${ROOT}/local-config/q10-cjk-mono.ttf"
  if [[ ! -f "${MONO}" ]]; then
    python3 -m pip install --target /tmp/q10-fonttools fonttools -q
    SRC_HEI="/tmp/q10-fonts/mhei.ttf"
    mkdir -p /tmp/q10-fonts
    if [[ ! -f "${SRC_HEI}" ]]; then
      ssh "${SSH_OPTS[@]}" "devuser@${DEVICE_IP}" \
        "cat /usr/fonts/font_repository/monotype/MHeiM.GB18030_200910.ttf" > "${SRC_HEI}"
    fi
    python3 "${ROOT}/scripts/q10-build-cjk-mono.py" "${SRC_HEI}" "${MONO}"
  fi
  if [[ -f "${MONO}" ]]; then
    ssh "${SSH_OPTS[@]}" "devuser@${DEVICE_IP}" \
      "cat > /accounts/1000/shared/misc/q10-cjk-mono.ttf && chmod 644 /accounts/1000/shared/misc/q10-cjk-mono.ttf" < "${MONO}"
  fi
  echo "已推送 ${REMOTE_PY} ${REMOTE_FONT} ${REMOTE_AUTO}"
fi

if [[ "${DO_RUN}" == "1" ]]; then
  ARGS=(--once --all --lang zh)
  if [[ "${DEMO}" == "1" ]]; then
    ARGS=(--once --all --lang zh --demo)
  fi
  "${ROOT}/scripts/q10-shell.sh" \
    "export LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8 PYTHONIOENCODING=utf-8; /usr/bin/python3.2 '${REMOTE_PY}' ${ARGS[*]}"
fi
