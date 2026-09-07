#!/usr/bin/env bash
# Pull aindle.snapshot.v2 from the Mac hub as seen by the Q10 USB NIC.
# Default hub is the Mac USB address the phone already proved can reach.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
source "${ROOT}/scripts/q10-common.sh"
q10_load_local_env

HUB="$(q10_resolve_hub_url || true)"
if [[ -z "${HUB}" ]]; then
  echo "Hub 未响应 $(q10_hub_ports_csv)。不要在本仓库另起 Hub。"
  exit 1
fi
"${ROOT}/scripts/q10-shell.sh" "python3.2 -c '
import json, sys, urllib.request
url = sys.argv[1]
raw = urllib.request.urlopen(url, timeout=8).read()
obj = json.loads(raw.decode(\"utf-8\", \"replace\"))
print(\"BYTES\", len(raw))
print(\"SCHEMA\", obj.get(\"schema\"))
print(\"GENERATED\", obj.get(\"generatedAt\"))
hub = obj.get(\"hub\") or {}
print(\"HUB\", hub.get(\"id\"), hub.get(\"label\"))
fresh = obj.get(\"freshness\") or {}
print(\"STALE\", fresh.get(\"staleHosts\"))
print(\"HOSTS\", len(obj.get(\"hosts\") or []))
print(\"RUNS\", len(obj.get(\"runs\") or []))
print(\"SUBS\", len(obj.get(\"subscriptions\") or []))
for h in (obj.get(\"hosts\") or [])[:12]:
    print(\"HOST\", h.get(\"id\"), h.get(\"status\"))
for r in (obj.get(\"runs\") or [])[:12]:
    title = (r.get(\"title\") or r.get(\"id\") or \"\")
    print(\"RUN\", r.get(\"state\") or r.get(\"status\"), title.encode(\"ascii\", \"replace\").decode(\"ascii\"))
' '${HUB}'"
