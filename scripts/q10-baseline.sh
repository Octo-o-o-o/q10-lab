#!/usr/bin/env bash
# Collect a redacted SSH baseline. Requires a live blackberry-connect.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
source "${ROOT}/scripts/q10-common.sh"
q10_load_local_env

OUT="${ROOT}/logs/q10-ssh-baseline.txt"
: > "${OUT}"

run() {
  local title="$1"
  shift
  {
    echo "===== ${title} ====="
    "${ROOT}/scripts/q10-shell.sh" "$@" || true
    echo
  } >> "${OUT}"
}

run UNAME uname -a
run ID id
run QNX uname -npsr
run DF df -h
run MOUNT mount
run IFCONFIG ifconfig
run ENV 'env | sed -E "/PASSWORD|TOKEN|SECRET|IMEI|PIN/d"'
run PWD pwd

python3 - "${OUT}" <<'PY'
import pathlib, re, sys
p = pathlib.Path(sys.argv[1])
text = p.read_text(errors="replace")
text = re.sub(r'(?i)(imei|imsi|meid)[=:].*', r'\1=***', text)
p.write_text(text)
print(p.read_text())
PY
