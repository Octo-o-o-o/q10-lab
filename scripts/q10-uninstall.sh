#!/usr/bin/env bash
# Uninstall one already-installed app by package-fullname (the token before ::
# in -listInstalledApps). Does not touch sys.* unless the caller passes one.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
source "${ROOT}/scripts/q10-common.sh"
q10_load_local_env

FORCE_SYS=0
if [[ "${1:-}" == "--system" ]]; then
  FORCE_SYS=1
  shift
fi
FULL="${1:-}"
if [[ -z "${FULL}" ]]; then
  echo "Usage: $0 [--system] <package-fullname>"
  exit 1
fi
if [[ "${FULL}" == sys.* && "${FORCE_SYS}" != "1" ]]; then
  echo "Refusing to uninstall system package without --system: ${FULL}"
  exit 2
fi
if [[ "${FULL}" == *Term49* ]]; then
  echo "Refusing to uninstall Term49"
  exit 2
fi

if ! BB_BIN="$(q10_find_bb_tools)" || [[ ! -x "${BB_BIN}/blackberry-deploy" ]]; then
  echo "blackberry-deploy not available."
  exit 2
fi

DEVICE_IP="$(q10_device_ip || true)"
if [[ -z "${DEVICE_IP}" ]]; then
  echo "DEVICE_IP not found"
  exit 1
fi
q10_prompt_password || exit 1

mkdir -p "${ROOT}/logs"
LOG="${ROOT}/logs/q10-uninstall-$(date '+%Y%m%d-%H%M%S').log"
echo "Uninstall ${FULL} on ${DEVICE_IP}"

set +e
"${BB_BIN}/blackberry-deploy" -uninstallApp -device "${DEVICE_IP}" \
  -password "${Q10_DEVICE_PASSWORD}" -package-fullname "${FULL}" \
  >"${LOG}" 2>"${LOG}.err"
rc=$?
set -e

python3 - "${LOG}" "${LOG}.err" "${Q10_DEVICE_PASSWORD}" <<'PY'
import pathlib, sys
secret = sys.argv[3]
for p in sys.argv[1:3]:
    path = pathlib.Path(p)
    if path.exists():
        path.write_text(path.read_text(errors="replace").replace(secret, "***"))
PY

echo "exit=${rc} log=${LOG}"
cat "${LOG}" 2>/dev/null || true
if [[ -s "${LOG}.err" ]]; then
  echo "--- stderr ---"
  cat "${LOG}.err"
fi
exit "${rc}"
