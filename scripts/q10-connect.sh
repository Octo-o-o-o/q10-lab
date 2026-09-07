#!/usr/bin/env bash
# Start blackberry-connect and keep it running. Password never logged.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
source "${ROOT}/scripts/q10-common.sh"
q10_load_local_env

KEY="${Q10_SSH_KEY:-${HOME}/.ssh/q10-usb}"
if [[ ! -f "${KEY}" ]]; then
  echo "Generating RSA-4096 key at ${KEY} (no passphrase, local-only)"
  mkdir -p "$(dirname "${KEY}")"
  ssh-keygen -t rsa -b 4096 -f "${KEY}" -N "" -C "q10-usb"
fi
if [[ ! -f "${KEY}.pub" ]]; then
  echo "Missing ${KEY}.pub"
  exit 1
fi

if ! BB_BIN="$(q10_find_bb_tools)" || [[ ! -x "${BB_BIN}/blackberry-connect" ]]; then
  echo "blackberry-connect not available yet. Extract host tools first."
  exit 2
fi

DEVICE_IP="$(q10_device_ip || true)"
if [[ -z "${DEVICE_IP}" ]]; then
  echo "DEVICE_IP not found. Run ./scripts/q10-detect.sh"
  exit 1
fi

q10_prompt_password || exit 1

mkdir -p "${ROOT}/logs" "${ROOT}/local-config"
LOG="${ROOT}/logs/q10-connect.log"
PIDFILE="${ROOT}/local-config/q10-connect.pid"

if [[ -f "${PIDFILE}" ]]; then
  old="$(cat "${PIDFILE}")"
  if kill -0 "${old}" 2>/dev/null; then
    echo "blackberry-connect already running pid=${old}"
    echo "DEVICE_IP=${DEVICE_IP}"
    exit 0
  fi
fi

PUB="$(q10_plain_pubkey "${KEY}.pub")"
echo "Connecting ${DEVICE_IP}:4455 with comment-stripped ${PUB}"
echo "This process must stay running for temporary SSH (new session, not Cursor process group)."

# Detach from this shell's process group. Cursor otherwise kills connect when the command ends.
set +e
python3 - "${BB_BIN}/blackberry-connect" "${DEVICE_IP}" "${PUB}" "${LOG}" "${PIDFILE}" <<'PY'
import os, pathlib, subprocess, sys, time

connect, ip, pub, log, pidfile = sys.argv[1:6]
pw = os.environ.get("Q10_DEVICE_PASSWORD", "")
pathlib.Path(log).write_text("")
old = pathlib.Path(pidfile)
if old.exists():
    try:
        os.kill(int(old.read_text().strip()), 15)
        time.sleep(0.5)
    except Exception:
        pass
env = os.environ.copy()
env["NO_PROXY"] = "*"
env["no_proxy"] = "*"
with open(log, "w") as out:
    proc = subprocess.Popen(
        [connect, ip, "-password", pw, "-sshPublicKey", pub],
        stdout=out,
        stderr=subprocess.STDOUT,
        start_new_session=True,
        env=env,
    )
pathlib.Path(pidfile).write_text(str(proc.pid) + "\n")
ok = False
for _ in range(20):
    text = pathlib.Path(log).read_text(errors="replace")
    if "Successfully connected" in text:
        ok = True
        break
    if "Error:" in text and proc.poll() is not None:
        break
    time.sleep(1)
sys.exit(0 if ok else 1)
PY
rc=$?
set -e
pid="$(cat "${PIDFILE}" 2>/dev/null || echo none)"

python3 - "${LOG}" "${Q10_DEVICE_PASSWORD}" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1])
if p.exists():
    p.write_text(p.read_text(errors="replace").replace(sys.argv[2], "***"))
PY

if [[ "${rc}" != "0" ]]; then
  echo "blackberry-connect failed. See ${LOG}"
  tail -n 40 "${LOG}"
  exit 1
fi

echo "blackberry-connect pid=${pid} log=${LOG}"
echo "DEVICE_IP=${DEVICE_IP}"
echo "Next: ./scripts/q10-shell.sh 'uname -a'"
