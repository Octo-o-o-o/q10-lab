# Shared helpers for Q10 lab scripts. Source only, do not execute.
set -euo pipefail

Q10_LAB_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export NO_PROXY='*'
export no_proxy='*'

Q10_USB_VID="0x0fca"
Q10_USB_VID_DEC=4042
Q10_DEFAULT_PORTS="80 443 4455 8443 22"

q10_timestamp() {
  date '+%Y-%m-%dT%H:%M:%S%z'
}

q10_log() {
  printf '%s\n' "$*"
}

q10_find_bb_tools() {
  local cand
  if [[ -n "${BB10_HOST_BIN:-}" && -x "${BB10_HOST_BIN}/blackberry-deploy" ]]; then
    printf '%s\n' "${BB10_HOST_BIN}"
    return 0
  fi
  for cand in \
    "${Q10_LAB_ROOT}/tools/bb10/bin" \
    "${Q10_LAB_ROOT}/tools/bb10/host/usr/bin" \
    "${Q10_LAB_ROOT}/tools/bb10/host_10_3_1_12/darwin/x86/usr/bin" \
    /Applications/Momentics.app/Contents/MacOS/host_10_3_1_12/darwin/x86/usr/bin \
    /Applications/Momentics.app/host_10_3_1_12/darwin/x86/usr/bin \
    /Applications/bbndk/host_10_3_1_12/darwin/x86/usr/bin
  do
    if [[ -x "${cand}/blackberry-deploy" || -x "${cand}/blackberry-connect" ]]; then
      printf '%s\n' "${cand}"
      return 0
    fi
  done
  if command -v blackberry-deploy >/dev/null 2>&1; then
    dirname "$(command -v blackberry-deploy)"
    return 0
  fi
  return 1
}

q10_load_local_env() {
  local envf="${Q10_LAB_ROOT}/local-config/device.env"
  if [[ -f "${envf}" ]]; then
    # shellcheck disable=SC1090
    set -a
    source "${envf}"
    set +a
  fi
}

q10_usb_present() {
  ioreg -p IOUSB -l -w 0 2>/dev/null | python3 -c '
import sys
t = sys.stdin.read()
print("yes" if ("idVendor\" = 4042" in t and "BlackBerry" in t) else "no")
'
}

q10_net_iface() {
  networksetup -listallhardwareports 2>/dev/null | python3 -c '
import subprocess, sys
text = sys.stdin.read().split("\n\n")
cands = []
for block in text:
    if "Hardware Port: BlackBerry" not in block:
        continue
    for line in block.splitlines():
        if line.startswith("Device:"):
            cands.append(line.split(":",1)[1].strip())
out = subprocess.check_output(["ifconfig"], text=True, errors="replace")
# Prefer the BlackBerry iface that already has IPv4.
for iface in cands:
    chunk = ""
    take = False
    for line in out.splitlines():
        if line and not line[0].isspace():
            take = line.startswith(iface + ":")
        if take:
            chunk += line + "\n"
    if "inet 169.254." in chunk:
        print(iface)
        raise SystemExit
if cands:
    print(cands[0])
'
}

q10_host_ip() {
  local iface="$1"
  ifconfig "${iface}" 2>/dev/null | awk '/inet 169\.254\./ { print $2; exit }'
}

q10_linklocal_peer() {
  local iface="${1:-}"
  python3 - "${iface}" <<'PY'
import ipaddress, subprocess, sys
iface = sys.argv[1]
out = subprocess.check_output(["ifconfig", iface], text=True, errors="replace") if iface else ""
host = mask = None
for line in out.splitlines():
    parts = line.split()
    if len(parts) >= 4 and parts[0] == "inet" and parts[1].startswith("169.254."):
        host, mask = parts[1], parts[3]
        break
if host and mask:
    if mask.startswith("0x"):
        prefix = bin(int(mask, 16)).count("1")
    else:
        prefix = ipaddress.IPv4Network(f"0.0.0.0/{mask}").prefixlen
    net = ipaddress.IPv4Interface(f"{host}/{prefix}").network
    for addr in net.hosts():
        if str(addr) != host:
            print(addr)
            raise SystemExit
PY
}

q10_device_ip() {
  local ip iface peer
  if [[ -n "${Q10_DEVICE_IP:-}" ]] && q10_ping_ok "${Q10_DEVICE_IP}"; then
    printf '%s\n' "${Q10_DEVICE_IP}"
    return 0
  fi
  iface="$(q10_net_iface || true)"
  if [[ -n "${iface}" ]]; then
    peer="$(q10_linklocal_peer "${iface}" || true)"
    if [[ -n "${peer}" ]] && q10_ping_ok "${peer}"; then
      printf '%s\n' "${peer}"
      return 0
    fi
  fi
  for ip in 169.254.0.1 169.254.57.113; do
    if q10_ping_ok "${ip}"; then
      printf '%s\n' "${ip}"
      return 0
    fi
  done
  ip="$(arp -an 2>/dev/null | awk '/96:eb:cd:56:aa:5f/ { gsub(/[()]/,"",$2); print $2; exit }')"
  if [[ -n "${ip}" ]]; then
    printf '%s\n' "${ip}"
    return 0
  fi
  ip="$(arp -a 2>/dev/null | awk '/blackberry/ && /169\.254\./ { gsub(/[()]/,"",$2); print $2; exit }')"
  if [[ -n "${ip}" ]]; then
    printf '%s\n' "${ip}"
    return 0
  fi
  python3 - <<'PY'
import socket
for name in ("blackberry-d0bd.local", "BLACKBERRY-D0BD.local"):
    try:
        print(socket.getaddrinfo(name, None, socket.AF_INET)[0][4][0])
        raise SystemExit
    except Exception:
        pass
PY
}

q10_plain_pubkey() {
  local src="$1"
  local dest="${Q10_LAB_ROOT}/local-config/q10-usb.pub.plain"
  mkdir -p "${Q10_LAB_ROOT}/local-config"
  awk '{print $1" "$2}' "${src}" > "${dest}"
  printf '%s\n' "${dest}"
}

q10_ssh_opts() {
  local key="${Q10_SSH_KEY:-${HOME}/.ssh/q10-usb}"
  # Remote is OpenSSH_6.2 QNX_Secure_Shell-20130711. A "+" list still lets
  # /etc/ssh/crypto.conf pick ecdh-sha2-nistp256 + aes128-gcm, then the
  # phone closes during SSH2_MSG_KEX_ECDH_REPLY. Force a 2013-era subset.
  # -F /dev/null skips user + macOS crypto.conf.
  SSH_OPTS=(
    -F /dev/null
    -i "${key}"
    -o IdentitiesOnly=yes
    -o StrictHostKeyChecking=accept-new
    -o UserKnownHostsFile="${Q10_LAB_ROOT}/local-config/known_hosts"
    -o ProxyCommand=none
    -o UpdateHostKeys=no
    -o HostKeyAlgorithms=ssh-rsa
    -o PubkeyAcceptedAlgorithms=ssh-rsa
    -o CASignatureAlgorithms=ssh-rsa
    -o KexAlgorithms=diffie-hellman-group14-sha1
    -o Ciphers=aes128-ctr,aes192-ctr,aes256-ctr
    -o MACs=hmac-sha1
    -o RequiredRSASize=1024
  )
}

q10_ping_ok() {
  local ip="$1"
  ping -c 1 -W 1000 "${ip}" >/dev/null 2>&1
}

q10_port_open() {
  local ip="$1" port="$2"
  python3 -c '
import socket, sys
s = socket.socket(); s.settimeout(0.4)
try:
    sys.exit(0 if s.connect_ex((sys.argv[1], int(sys.argv[2]))) == 0 else 1)
finally:
    s.close()
' "${ip}" "${port}"
}

q10_prompt_password() {
  if [[ -n "${Q10_DEVICE_PASSWORD:-}" ]]; then
    return 0
  fi
  if [[ ! -t 0 ]]; then
    q10_log "ERROR: device password needed. Set Q10_DEVICE_PASSWORD in the environment or local-config/device.env (gitignored)."
    return 1
  fi
  printf 'Q10 device password (not echoed, not logged): ' >&2
  read -r -s Q10_DEVICE_PASSWORD
  printf '\n' >&2
  export Q10_DEVICE_PASSWORD
}

# Aindle 默认 8787；8790 只作回退。不要在本仓库另起 Hub。
q10_hub_ports() {
  local raw="${Q10_HUB_PORTS:-}"
  if [[ -z "${raw}" && -n "${AINDLE_PORT:-}" ]]; then
    raw="${AINDLE_PORT}"
  fi
  raw="${raw//,/ }"
  local out="" p
  for p in ${raw} 8787 8790; do
    case "${p}" in
      ''|*[!0-9]*) continue ;;
    esac
    case " ${out} " in
      *" ${p} "*) ;;
      *) out="${out} ${p}" ;;
    esac
  done
  # shellcheck disable=SC2086
  printf '%s\n' ${out}
}

q10_hub_ports_csv() {
  q10_hub_ports | paste -sd, -
}

q10_hub_last_file() {
  printf '%s\n' "${Q10_LAB_ROOT}/local-config/q10-hub.last"
}

q10_probe_snapshot() {
  local url="$1"
  local tmp
  tmp="$(mktemp)"
  if ! curl --noproxy '*' -sS -m 2 -f -o "${tmp}" "${url}" >/dev/null 2>&1; then
    rm -f "${tmp}"
    return 1
  fi
  if python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); raise SystemExit(0 if d.get("schema")=="aindle.snapshot.v2" else 1)' "${tmp}"; then
    rm -f "${tmp}"
    return 0
  fi
  rm -f "${tmp}"
  return 1
}

q10_remember_hub_url() {
  local url="$1"
  local dest
  dest="$(q10_hub_last_file)"
  mkdir -p "$(dirname "${dest}")"
  printf '%s\n' "${url}" > "${dest}"
}

q10_hub_candidate_urls() {
  local lastf url host port last=""
  lastf="$(q10_hub_last_file)"
  if [[ -n "${Q10_MONITOR_URL:-}" ]]; then
    printf '%s\n' "${Q10_MONITOR_URL}"
  fi
  if [[ -f "${lastf}" ]]; then
    last="$(tr -d '[:space:]' < "${lastf}")"
    if [[ -n "${last}" ]]; then
      printf '%s\n' "${last}"
    fi
  fi
  if [[ -n "${Q10_HUB_URL:-}" ]]; then
    printf '%s\n' "${Q10_HUB_URL}"
  fi
  if [[ -f "${Q10_LAB_ROOT}/local-config/mailbox.lan" ]]; then
    printf '%s\n' "$(tr -d '[:space:]' < "${Q10_LAB_ROOT}/local-config/mailbox.lan")"
  fi
  while read -r port; do
    for host in 169.254.0.2 127.0.0.1; do
      printf 'http://%s:%s/snapshot.json\n' "${host}" "${port}"
    done
  done <<EOF
$(q10_hub_ports)
EOF
}

q10_resolve_hub_url() {
  local url seen=""
  while read -r url; do
    [[ -z "${url}" ]] && continue
    case " ${seen} " in
      *" ${url} "*) continue ;;
    esac
    seen="${seen} ${url}"
    if q10_probe_snapshot "${url}"; then
      q10_remember_hub_url "${url}"
      printf '%s\n' "${url}"
      return 0
    fi
  done <<EOF
$(q10_hub_candidate_urls)
EOF
  return 1
}

q10_ensure_hub() {
  local url
  if url="$(q10_resolve_hub_url)"; then
    printf '%s\n' "${url}"
    return 0
  fi
  local label="gui/$(id -u)/com.aindle.hub"
  if launchctl print "${label}" >/dev/null 2>&1; then
    echo "Hub 全端口未响应，kickstart ${label}" >&2
    launchctl kickstart -k "${label}" || true
    sleep 2
    if url="$(q10_resolve_hub_url)"; then
      printf '%s\n' "${url}"
      return 0
    fi
  fi
  return 1
}
