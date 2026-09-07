#!/usr/bin/env bash
# Bring Term49 to the foreground on the phone. Does not type into it.
#   ./scripts/q10-launch.sh
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
source "${ROOT}/scripts/q10-common.sh"
q10_load_local_env

TERM49_FULL="${Q10_TERM49_FULLNAME:-com.example.Term49.gYABgFEqMSpja5S6kL.DWpWmq50}"
HUB="$(q10_ensure_hub || true)"
HUB="${HUB:-${Q10_MONITOR_URL:-http://169.254.0.2:8787/snapshot.json}}"

if ! BB_BIN="$(q10_find_bb_tools)" || [[ ! -x "${BB_BIN}/blackberry-deploy" ]]; then
  echo "没有 blackberry-deploy。"
  exit 2
fi
DEVICE_IP="$(q10_device_ip || true)"
if [[ -z "${DEVICE_IP}" ]]; then
  echo "找不到 DEVICE_IP。请插上 Q10 并跑 ./scripts/q10-detect.sh"
  exit 1
fi
q10_prompt_password || exit 1

hub_code="$(curl --noproxy '*' -sS -m 3 -o /dev/null -w '%{http_code}' "${HUB}" || echo 000)"
echo "HUB ${HUB}  http=${hub_code}"
if [[ "${hub_code}" != "200" ]]; then
  echo "警告：USB/本机摸不到 Hub（$(q10_hub_ports_csv)）。Term49 能打开，但监视器会先探测再标离线。"
fi

set +e
out="$("${BB_BIN}/blackberry-deploy" -launchApp -device "${DEVICE_IP}" \
  -password "${Q10_DEVICE_PASSWORD}" -package-fullname "${TERM49_FULL}" 2>&1)"
rc=$?
set -e
if [[ -n "${Q10_DEVICE_PASSWORD}" ]]; then
  out="${out//${Q10_DEVICE_PASSWORD}/***}"
fi
printf '%s\n' "${out}"
echo "LAUNCH_EXIT=${rc}"
exit "${rc}"
