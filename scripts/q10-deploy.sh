#!/usr/bin/env bash
# Usage: ./scripts/q10-deploy.sh ./downloads/Term49.bar
# Installs a locally present, already-signed BAR. Does not resign.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
source "${ROOT}/scripts/q10-common.sh"
q10_load_local_env

BAR="${1:-}"
if [[ -z "${BAR}" || ! -f "${BAR}" ]]; then
  echo "Usage: $0 /path/to/app.bar"
  exit 1
fi

if ! BB_BIN="$(q10_find_bb_tools)" || [[ ! -x "${BB_BIN}/blackberry-deploy" ]]; then
  echo "blackberry-deploy not available yet."
  exit 2
fi

DEVICE_IP="$(q10_device_ip || true)"
if [[ -z "${DEVICE_IP}" ]]; then
  echo "DEVICE_IP not found. Run ./scripts/q10-detect.sh"
  exit 1
fi

q10_prompt_password || exit 1

mkdir -p "${ROOT}/logs"
LOG="${ROOT}/logs/q10-deploy-$(date '+%Y%m%d-%H%M%S').log"
echo "Deploying ${BAR} to ${DEVICE_IP}"
echo "BAR sha256: $(shasum -a 256 "${BAR}" | awk '{print $1}')"

set +e
"${BB_BIN}/blackberry-deploy" -installApp -device "${DEVICE_IP}" -password "${Q10_DEVICE_PASSWORD}" -package "${BAR}" \
  >"${LOG}" 2>"${LOG}.err"
rc=$?
set -e

if [[ -n "${Q10_DEVICE_PASSWORD}" ]]; then
  python3 - "${LOG}" "${LOG}.err" "${Q10_DEVICE_PASSWORD}" <<'PY'
import pathlib, sys
secret = sys.argv[3]
for p in sys.argv[1:3]:
    path = pathlib.Path(p)
    if path.exists():
        path.write_text(path.read_text(errors="replace").replace(secret, "***"))
PY
fi

echo "exit=${rc} log=${LOG}"
cat "${LOG}" 2>/dev/null || true
if [[ -s "${LOG}.err" ]]; then
  echo "--- stderr ---"
  cat "${LOG}.err"
fi
exit "${rc}"
