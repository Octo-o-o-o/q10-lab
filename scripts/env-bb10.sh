#!/usr/bin/env bash
# Usage: source ./scripts/env-bb10.sh
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck disable=SC1091
source "${ROOT}/scripts/q10-common.sh"
if bin="$(q10_find_bb_tools)"; then
  export BB10_HOST_BIN="${bin}"
  export PATH="${BB10_HOST_BIN}:${PATH}"
  echo "BB10_HOST_BIN=${BB10_HOST_BIN}"
else
  echo "BB10 host tools not found. Extract blackberry-deploy / blackberry-connect into tools/bb10/ first." >&2
fi
export Q10_LAB_ROOT
export NO_PROXY='*'
export no_proxy='*'
