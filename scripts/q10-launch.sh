#!/usr/bin/env bash
# Bring Term49 to the foreground on the phone. Does not type into it.
#   ./scripts/q10-launch.sh
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
source "${ROOT}/scripts/q10-common.sh"
q10_load_local_env

TERM49_FULL="${Q10_TERM49_FULLNAME:-com.example.Term49.gYABgFEqMSpja5S6kL.DWpWmq50}"
HUB="${Q10_MONITOR_URL:-http://169.254.0.2:8790/snapshot.json}"

if ! BB_BIN="$(q10_find_bb_tools)" || [[ ! -x "${BB_BIN}/blackberry-deploy" ]]; then
  echo "blackberry-deploy not available."
  exit 2
fi
DEVICE_IP="$(q10_device_ip || true)"
if [[ -z "${DEVICE_IP}" ]]; then
  echo "DEVICE_IP not found. Plug the Q10 in and run ./scripts/q10-detect.sh"
  exit 1
fi
q10_prompt_password || exit 1

hub_code="$(curl --noproxy '*' -sS -m 3 -o /dev/null -w '%{http_code}' "${HUB}" || echo 000)"
echo "HUB ${HUB}  http=${hub_code}"
if [[ "${hub_code}" != "200" ]]; then
  echo "WARN: 8790 not reachable on USB. Term49 can open, but the monitor will show 不可用/离线."
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
