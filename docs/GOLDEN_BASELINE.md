# Golden Baseline `q10-clean-baseline`

冻结时间：2026-09-07（Asia/Shanghai）。用户已判定 **Phase 1 完成**。  
本机密码只在 `local-config/device.env`（gitignore）。**不要 commit 密码、IMEI、token。**

## 验收：BBID / Protect 已清

用户在真机上确认：

| 项 | 恢复前 | 现在 |
|---|---|---|
| Protect UI | Off | Off |
| Security Wipe 口令 | 要 BlackBerry ID Password / Verify | 输入 **`blackberry`** 即可 |

官方 Q10 说明：普通 Security Wipe 输入 `blackberry`；开了 Protect / Anti-Theft 才会要 BBID。  
来源：<https://blackberry-q10.berrydoc.net/en/security-and-backup/wiping-your-device-to-delete-your-device-data/>

本实验室 **不执行** wipe。这条只记录用户已完成的验收。

## 设备

| 项 | 值 |
|---|---|
| 型号 | BlackBerry Q10 / SQN100-3 |
| PIN / 主机名 | `0x2ae7d0bd` / `BLACKBERRY-D0BD` |
| OS | 10.3.3.3216 / `BB10_3_3` / build 911537 |
| QNX | `8.0.0 2018/02/21-10:54:19EST MSM8960_V3.2.1.1_N_R085_Rev:16 armle` |
| Dev Mode | 开，约 10 天 |
| Debug token | 未装 |
| USB（Dev Mode） | 设备 `169.254.0.1`，Mac `169.254.0.2`，`en13` / `ncm0` |
| SSH host key | `SHA256:NpSPYrZNVNBQrnVFmd/CUgJeJP/tRQsQc5y0uyAzjfc`（`baselines/q10-usb.known_hosts`） |
| `/` | 13G，卸载三方后约 **2.8G / 22%** |
| Term49 / BerryCore | **未装**（本 tag 刻意保持官方固件干净面） |

## 已卸三方（deploy `-uninstallApp`，result::success）

- LinkedIn `com.linkedin…`
- Twitter `com.twitter…`
- Facebook `com.rim.bb.app.facebook…`
- Evernote `com.evernote…`
- Amazon Shop / Appstore（Android runtime 里的两个 BAR）

没有独立 YouTube 应用。Hub 里的 `sys.socialconnect.youtube` / `sys.uri.youtube` 是系统连接器，**未卸**。  
未动 `sys.*`、Adobe Reader、Maps、Wallet、Retail Demo shim、BBVE。

## 工具链（本仓库）

```sh
./scripts/q10-detect.sh      # 无密码不探认证端点（避免吃 1/5）
./scripts/q10-connect.sh     # 独立 session，公钥须剥注释
./scripts/q10-shell.sh       # -F /dev/null + DH-group14 + AES-CTR + ssh-rsa
./scripts/q10-apps.sh
./scripts/q10-uninstall.sh <package-fullname>
./scripts/q10-health.sh
```

SSH 不能让 OpenSSH 10.3 走 `ecdh-sha2-nistp256` + GCM。macOS `/etc/ssh/crypto.conf` 会盖掉 `Host` KEX，所以脚本用 `-F /dev/null`。

## 下一阶段

本 tag 冻结的是干净官方面。之后 Term49 / BerryCore / 键盘监视器见 `BRINGUP.md`，不回写本 tag。
