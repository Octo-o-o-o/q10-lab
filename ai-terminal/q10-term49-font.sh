#!/bin/sh
# 在 Term49 沙箱里改 $HOME/.term49rc。SSH /accounts/devuser 写不进去。
FONT_SRC="/usr/fonts/font_repository/monotype/MHeiM.GB18030_200910.ttf"
FONT_LINK="/accounts/1000/shared/misc/q10-cjk-mono.ttf"
if [ ! -f "$FONT_LINK" ]; then
  FONT_LINK="/accounts/1000/shared/misc/q10-cjk.ttf"
fi
STATE="/accounts/1000/shared/misc/q10-term49-font.state"

if [ ! -f "$FONT_SRC" ]; then
  echo "没有找到中文字体：$FONT_SRC"
  exit 1
fi
# 优先用 Mac 做好的等宽黑体。没有才退回系统字体拷贝。
if [ ! -f "$FONT_LINK" ] || [ -L "$FONT_LINK" ]; then
  rm -f "$FONT_LINK"
  cp "$FONT_SRC" "$FONT_LINK" 2>/dev/null || ln -sf "$FONT_SRC" "$FONT_LINK"
fi

{
  echo "HOME=$HOME"
  echo "PWD=$PWD"
  echo "USER=${USER:-}"
  ls -la "${HOME}/.term49rc" "${HOME}/.term48rc" 2>&1 || true
  echo "==== rc ===="
  cat "${HOME}/.term49rc" 2>&1 || true
} > "$STATE" 2>&1
cp "${HOME}/.term49rc" /accounts/1000/shared/misc/q10-term49rc.snapshot 2>/dev/null || true

case "$HOME" in
  /accounts/devuser|/accounts/devuser/*)
    echo "跳过写入配置：当前 HOME=$HOME（请在 Term49 里跑）"
    echo "SKIP_DEVUSER" >> "$STATE"
    exit 0
    ;;
esac

RC="${HOME}/.term49rc"
if ! touch "${HOME}/.q10-font-write" 2>/dev/null; then
  echo "HOME 不可写：$HOME"
  echo "HOME_NOT_WRITABLE" >> "$STATE"
  exit 0
fi
rm -f "${HOME}/.q10-font-write"

/usr/bin/python3.2 - "$RC" "$FONT_LINK" "$STATE" <<'PY'
import os, re, sys
rc, want, state = sys.argv[1], sys.argv[2], sys.argv[3]
line = 'font_path = "%s";\n' % want
if os.path.isfile(rc):
    text = open(rc, "rb").read().decode("utf-8", "replace")
    if want in text:
        open(state, "ab").write(("FONT_ALREADY %s\n" % rc).encode("utf-8"))
        print("FONT_ALREADY")
        raise SystemExit(0)
    new, n = re.subn(
        r'font_path\s*=\s*(?:"[^"]*"|[^;\n]+)\s*;',
        'font_path = "%s";' % want,
        text,
        count=1,
    )
    if n == 0:
        new = text.rstrip("\n") + "\n" + line
    open(rc, "wb").write(new.encode("utf-8"))
    open(state, "ab").write(("FONT_UPDATED %s\n" % rc).encode("utf-8"))
    print("FONT_UPDATED")
else:
    open(rc, "wb").write(line.encode("utf-8"))
    open(state, "ab").write(("FONT_CREATED %s\n" % rc).encode("utf-8"))
    print("FONT_CREATED")
PY
