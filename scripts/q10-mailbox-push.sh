#!/usr/bin/env bash
# Push the local 8787 snapshot to the Q10 mailbox Worker.
#   ./scripts/q10-mailbox-push.sh          # once
#   ./scripts/q10-mailbox-push.sh --loop   # every 10s; pid in local-config
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
source "${ROOT}/scripts/q10-common.sh"
q10_load_local_env

LOOP=0
INTERVAL=10
while [[ $# -gt 0 ]]; do
  case "$1" in
    --loop) LOOP=1; shift ;;
    --interval) INTERVAL="$2"; shift 2 ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done

TOKEN_FILE="${Q10_MAILBOX_TOKEN_FILE:-${ROOT}/local-config/mailbox.token}"
URL="${Q10_MAILBOX_URL:-}"
if [[ -z "${URL}" && -f "${ROOT}/local-config/mailbox.url" ]]; then
  URL="$(tr -d '[:space:]' < "${ROOT}/local-config/mailbox.url")"
fi
if [[ -z "${URL}" ]]; then
  echo "Set Q10_MAILBOX_URL or write local-config/mailbox.url" >&2
  exit 1
fi
if [[ ! -f "${TOKEN_FILE}" ]]; then
  echo "Missing mailbox token file." >&2
  exit 1
fi
TOKEN="$(tr -d '[:space:]' < "${TOKEN_FILE}")"
HUB="$(q10_resolve_hub_url || true)"
HUB="${HUB:-${Q10_HUB_URL:-http://127.0.0.1:8787/snapshot.json}}"
PIDFILE="${ROOT}/local-config/q10-mailbox-push.pid"

push_once() {
  local tmp
  tmp="$(mktemp)"
  if ! curl --noproxy '*' -sS -m 5 -f -o "${tmp}" "${HUB}"; then
    rm -f "${tmp}"
    echo "HUB_FAIL ${HUB}"
    return 1
  fi
  if ! python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); assert d.get("schema")=="aindle.snapshot.v2"' "${tmp}"; then
    rm -f "${tmp}"
    echo "HUB_BAD_SCHEMA"
    return 1
  fi
  local code
  code="$(curl --noproxy '*' -sS -m 20 -o /tmp/q10-mailbox-put.out -w '%{http_code}' \
    -X PUT -H "Authorization: Bearer ${TOKEN}" -H "Content-Type: application/json" \
    --data-binary "@${tmp}" "${URL}")"
  rm -f "${tmp}"
  if [[ "${code}" != "200" ]]; then
    echo "PUT_FAIL http=${code}"
    return 1
  fi
  echo "PUT_OK"
}

if [[ "${LOOP}" != "1" ]]; then
  push_once
  exit $?
fi

if [[ -f "${PIDFILE}" ]]; then
  old="$(cat "${PIDFILE}")"
  if kill -0 "${old}" 2>/dev/null; then
    echo "mailbox-push already running pid=${old}"
    exit 0
  fi
fi

mkdir -p "${ROOT}/local-config" "${ROOT}/logs"
LOG="${ROOT}/logs/q10-mailbox-push.log"
# New session, like q10-connect: Cursor 结束前台命令时不要带走循环。
python3 - "${ROOT}/scripts/q10-mailbox-push.sh" "${INTERVAL}" "${LOG}" "${PIDFILE}" <<'PY'
import os, pathlib, subprocess, sys, time

script, interval, log, pidfile = sys.argv[1:5]
path = pathlib.Path(pidfile)
if path.exists():
    try:
        os.kill(int(path.read_text().strip()), 15)
        time.sleep(0.3)
    except Exception:
        pass
out = open(log, "a")
proc = subprocess.Popen(
    ["bash", "-c", "while true; do \"%s\" || true; sleep %s; done" % (script, interval)],
    stdout=out,
    stderr=subprocess.STDOUT,
    start_new_session=True,
    env=os.environ.copy(),
)
path.write_text(str(proc.pid) + "\n")
out.close()
print("STARTED pid=%s log=%s" % (proc.pid, log))
PY
