#!/usr/bin/env bash
# 用 blackberry-deploy 改 Term49 沙箱里的 .term49rc（SSH 写不进去）。
#   ./scripts/q10-term49-cjk.sh          # 只写字体
#   ./scripts/q10-term49-cjk.sh --restart  # 写完后结束并重开 Term49
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
source "${ROOT}/scripts/q10-common.sh"
q10_load_local_env

RESTART=0
if [[ "${1:-}" == "--restart" ]]; then
  RESTART=1
fi

FONT_SRC="/usr/fonts/font_repository/monotype/MHeiM.GB18030_200910.ttf"
TERM49_FULL="${Q10_TERM49_FULLNAME:-com.example.Term49.gYABgFEqMSpja5S6kL.DWpWmq50}"

if ! BB_BIN="$(q10_find_bb_tools)" || [[ ! -x "${BB_BIN}/blackberry-deploy" ]]; then
  echo "没有 blackberry-deploy。"
  exit 2
fi
DEVICE_IP="$(q10_device_ip || true)"
if [[ -z "${DEVICE_IP}" ]]; then
  echo "找不到 DEVICE_IP。请插上 Q10。"
  exit 1
fi
q10_prompt_password || exit 1

scrub() {
  local text="$1"
  if [[ -n "${Q10_DEVICE_PASSWORD}" ]]; then
    text="${text//${Q10_DEVICE_PASSWORD}/***}"
  fi
  printf '%s\n' "${text}"
}

deploy() {
  local out rc
  set +e
  out="$("${BB_BIN}/blackberry-deploy" "$@" -device "${DEVICE_IP}" \
    -password "${Q10_DEVICE_PASSWORD}" -package-fullname "${TERM49_FULL}" 2>&1)"
  rc=$?
  set -e
  scrub "${out}"
  return "${rc}"
}

TMPDIR_RC="$(mktemp -d)"
RC_LOCAL="${TMPDIR_RC}/term49rc"
cleanup() { rm -rf "${TMPDIR_RC}"; }
trap cleanup EXIT

echo "GET .term49rc"
if ! deploy -getFile .term49rc "${RC_LOCAL}"; then
  echo "GET data/.term49rc"
  if ! deploy -getFile data/.term49rc "${RC_LOCAL}"; then
    echo "沙箱里还没有 .term49rc，将新建一份只含 font_path。"
    printf 'font_path = "%s";\n' "${FONT_SRC}" > "${RC_LOCAL}"
  fi
fi

python3 - "${RC_LOCAL}" "${FONT_SRC}" <<'PY'
import re, sys
path, want = sys.argv[1], sys.argv[2]
line = 'font_path = "%s";\n' % want
try:
    text = open(path, "r", encoding="utf-8", errors="replace").read()
except OSError:
    text = ""
if want in text:
    print("FONT_ALREADY")
    raise SystemExit(0)
new, n = re.subn(
    r'font_path\s*=\s*(?:"[^"]*"|[^;\n]+)\s*;',
    'font_path = "%s";' % want,
    text,
    count=1,
)
if n == 0:
    new = (text.rstrip("\n") + "\n" if text.strip() else "") + line
open(path, "w", encoding="utf-8").write(new)
print("FONT_PATCHED")
PY

echo "PUT .term49rc"
set +e
put_out="$(deploy -putFile "${RC_LOCAL}" .term49rc)"
put_rc=$?
set -e
printf '%s\n' "${put_out}"
if [[ "${put_rc}" -ne 0 ]]; then
  echo "生产签名的 Term49 不允许 Mac 改沙箱文件。字体只能在 Term49 里由 q10mon 写。"
  if [[ "${RESTART}" == "1" ]]; then
    echo "结束并重开 Term49，让 q10mon 自己写 .term49rc。"
    deploy -terminateApp || true
    sleep 1
    deploy -launchApp || true
  fi
  exit 0
fi

if [[ "${RESTART}" == "1" ]]; then
  echo "结束 Term49 并重新打开，让新字体生效。"
  deploy -terminateApp || true
  sleep 1
  deploy -launchApp
fi
