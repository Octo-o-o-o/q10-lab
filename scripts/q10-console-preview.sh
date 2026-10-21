#!/usr/bin/env bash
# 本仓 Cascades 720 预览。不另起 Hub，不占用 8787/8790。
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
source "${ROOT}/scripts/q10-common.sh"
q10_load_local_env
exec python3 "${ROOT}/cascades/preview/serve.py" "$@"
