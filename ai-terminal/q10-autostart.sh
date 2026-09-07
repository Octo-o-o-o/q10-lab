#!/bin/sh
# Run ONCE inside Term49 (personal user). SSH devuser cannot write Term49 $HOME.
#   . /accounts/1000/shared/misc/q10-autostart.sh
MARKER="# Q10 lab: start keyboard monitor"
PROFILE="${HOME}/.profile"
MON="/accounts/1000/shared/misc/q10mon"

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
# Set Q10_NOMON=1 to get a plain shell.
if [ -z "$Q10_NOMON" ] && [ -t 0 ] && [ -x /accounts/1000/shared/misc/q10mon ]; then
  /accounts/1000/shared/misc/q10mon
fi
EOF
  echo "INSTALLED $PROFILE"
else
  echo "ALREADY $PROFILE"
fi

echo "HOME=$HOME"
echo "After this, opening Term49 starts the monitor. x leaves you in a shell."
if [ -x "$MON" ] && [ -z "$Q10_NOMON" ]; then
  exec "$MON"
fi
