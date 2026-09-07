#!/usr/bin/env bash
# List installed apps via blackberry-deploy. Password is never printed.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
source "${ROOT}/scripts/q10-common.sh"
q10_load_local_env

if ! BB_BIN="$(q10_find_bb_tools)" || [[ ! -x "${BB_BIN}/blackberry-deploy" ]]; then
  echo "blackberry-deploy not available yet. Finish host-tool extract first."
  exit 2
fi

DEVICE_IP="$(q10_device_ip || true)"
if [[ -z "${DEVICE_IP}" ]]; then
  echo "DEVICE_IP not found. Plug the Q10 in and run ./scripts/q10-detect.sh"
  exit 1
fi

q10_prompt_password || exit 1

mkdir -p "${ROOT}/logs"
LOG="${ROOT}/logs/q10-apps-$(date '+%Y%m%d-%H%M%S').log"
echo "Using blackberry-deploy at ${BB_BIN} against ${DEVICE_IP}"
# Confirm real flags from the tool on this machine.
"${BB_BIN}/blackberry-deploy" -help 2>&1 | tee "${LOG}.help" >/dev/null || true

set +e
"${BB_BIN}/blackberry-deploy" -listInstalledApps -device "${DEVICE_IP}" -password "${Q10_DEVICE_PASSWORD}" \
  >"${LOG}" 2>"${LOG}.err"
rc=$?
set -e

# Strip any accidental password echo (tool should not print it).
if [[ -n "${Q10_DEVICE_PASSWORD}" ]]; then
  python3 - "${LOG}" "${LOG}.err" "${Q10_DEVICE_PASSWORD}" <<'PY'
import pathlib, sys
secret = sys.argv[3]
for p in sys.argv[1:3]:
    path = pathlib.Path(p)
    if path.exists():
        text = path.read_text(errors="replace").replace(secret, "***")
        path.write_text(text)
PY
fi

echo "exit=${rc}"
echo "log=${LOG}"
if [[ -s "${LOG}" ]]; then
  cat "${LOG}"
fi
if [[ -s "${LOG}.err" ]]; then
  echo "--- stderr ---"
  cat "${LOG}.err"
fi
exit "${rc}"
