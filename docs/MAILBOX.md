# 异地信箱（Q10 不在 USB / 同一局域网）

手机走流量、Mac 在家宽时，两边都在 NAT 后面，直连 `169.254` 或局域网 8787 都不通。Q10 仍只做 Interface：GET 同一份 `aindle.snapshot.v2`。

```
Mac 8787  --PUT-->  Cloudflare Worker /snapshot.json  --GET-->  Q10 (BerryCore curl)
```

监视器**每次刷新**重选源（约 10 秒，离线时约 4 秒），不用重启 Term49：last-good → 强制 `Q10_MONITOR_URL` → 当前还在的 USB `169.254` → 本机网卡与 `Q10_LAN_HUB_URL` 同一 /24 才试局域网 → 信箱 `Q10_MAILBOX_URL`。每个 HTTP 源会先试写在 URL 里的端口，再试 `Q10_HUB_PORTS`（默认 8787、回退 8790）。前一个失败自动试下一个。出门后家里局域网不在同一网段，会跳过，不会死等。头上一行会标 `USB` / `局域网` / `信箱`。

Hub 进程只由 Aindle 管（`AINDLE_PORT` + 可选 `com.aindle.hub` launchd）。本仓库不另起 Hub、不抢 8790。`./scripts/q10-health.sh` 在 8787/8790 都摸不到且 launchd 已装时，才 kickstart 一次。

同屋只是没插线：Q10 连家里 Wi-Fi，用 `Q10_LAN_HUB_URL=http://<Mac局域网IP>:8787/snapshot.json`，不必走 Cloudflare。

真异地才用信箱。Q10 的 HTTPS 走 BerryCore `curl`。`*.workers.dev` 在部分网络（含国内家宽/蜂窝）可能被拦；Mac 能推、手机超时，先当可达性问题，不是 token 错。换自定义域名或手机能打开的 HTTPS 再改 `Q10_MAILBOX_URL`。

## 本机

Token 和 URL 只在 `local-config/`（gitignore），不进 Git。

```sh
# 一次推送
./scripts/q10-mailbox-push.sh

# 离开家之前拉起循环（独立进程，pid 在 local-config）
./scripts/q10-mailbox-push.sh --loop
```

Worker 源码在 `mailbox/`。改完后：`cd mailbox && wrangler deploy`。`MAILBOX_TOKEN` 用 `wrangler secret put`，不要写进 `wrangler.jsonc`。

## 设备

`/accounts/1000/shared/misc/q10-mailbox.env` 只放 URL：

```sh
Q10_LAN_HUB_URL=http://192.168.1.10:8787/snapshot.json
Q10_MAILBOX_URL=https://q10-lab-mailbox.example.workers.dev/snapshot.json
```

Token 单独放 `/accounts/1000/shared/misc/q10-mailbox.token`，权限须是 **640**（group `1000_shared` 可读）。`600` 时 Term49 会 `Permission denied`，整页失败。`q10mon` 会 source 这个 env；HTTPS 走 BerryCore `curl`，不用库存 python3.2 的 TLS。USB / 局域网 HTTP 不带 token。

不要把 8787 或本机 22 映射到公网。不要在 Q10 上 `settings sshd-on`。
