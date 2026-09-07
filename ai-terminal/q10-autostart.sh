#!/bin/sh
# 必须在 Term49 里跑一次。SSH devuser 写不进 Term49 的 $HOME。
MARKER="# Q10 lab: start keyboard monitor"
PROFILE="${HOME}/.profile"
MON="/accounts/1000/shared/misc/q10mon"
FONT="/accounts/1000/shared/misc/q10-term49-font.sh"

case "$HOME" in
  *Term49*)
    ;;
  *)
    echo "请在 Term49 里运行本脚本，不要从 SSH 跑。"
    echo "当前 HOME=$HOME"
    exit 1
    ;;
esac

if [ -x "$FONT" ]; then
  font_msg="$($FONT 2>&1)" || true
  case "$font_msg" in
    *FONT_UPDATED*|*FONT_CREATED*)
      echo "已写入中文字体。请完全划掉 Term49，再打开一次。"
      echo "CJK font saved. Fully quit Term49 and open again."
      ;;
  esac
fi

already=0
if [ -f "$PROFILE" ]; then
  if /usr/bin/grep -q "$MARKER" "$PROFILE" 2>/dev/null; then
    already=1
  fi
fi

if [ "$already" -eq 0 ]; then
  if [ -f "$PROFILE" ]; then
    cp "$PROFILE" "$PROFILE.bak.q10" 2>/dev/null || true
  fi
  cat >> "$PROFILE" <<'EOF'

# Q10 lab: start keyboard monitor
# 设 Q10_NOMON=1 可只要普通 shell。
if [ -z "$Q10_NOMON" ] && [ -t 0 ] && [ -x /accounts/1000/shared/misc/q10mon ]; then
  /accounts/1000/shared/misc/q10mon
fi
EOF
  echo "已写入 $PROFILE"
else
  echo "已经装过：$PROFILE"
fi

echo "HOME=$HOME"
echo "之后打开 Term49 会进监视器。按 x 退回 shell。"
if [ -x "$MON" ] && [ -z "$Q10_NOMON" ]; then
  exec "$MON"
fi
