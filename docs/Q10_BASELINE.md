# Q10 Hardware / OS Baseline

采集时间：2026-09-07（Asia/Shanghai）。来源：macOS USB + `blackberry-deploy` + SSH `uname` / `df` / `mount` / `ifconfig`。

敏感项：IMEI、密码、账号、token **不写本文件**。USB 序列号不是 IMEI。

## 设备身份（deploy 已读回）

| 项 | 值 | 证据 |
|---|---|---|
| 产品 | BlackBerry Q10 | USB Product Name；`modelfullname::BlackBerry Q10` |
| 型号 | SQN100-3 | `modelnumber::SQN100-3`（与用户一致） |
| OS / scm | **10.3.3.3216** | `scmbundle*`。用户口述 10.3.3.2137 **已被设备否定** |
| 分支 | `BB10_3_3` | `Build Branch` |
| build_id | 911537 | deploy |
| 硬件族 | Bold / `hardwareid::0x8600270a` | deploy |
| PIN / 主机名 | `0x2ae7d0bd` / `BLACKBERRY-D0BD` | deploy；mDNS 后四位一致 |
| 量产机 | `production_device true` | deploy |
| 屏幕 | 720×720，330 dpi，2.2″ | deploy |
| Debug token | 未装 | `no debug token found` |
| Developer Mode | 打开后 `dev_mode_enabled true`，约 10 天过期 | 开之前工具原话：`Device is not in the Development Mode` |
| 成色 | 收藏级完整套装 | 用户。因此禁止破坏性操作 |

## USB（本机实测）

| 项 | 值 |
|---|---|
| Vendor | Research In Motion, Ltd. (`idVendor` 4042 = `0x0FCA`) |
| Product | BlackBerry (`idProduct` 32791 = `0x8017`) |
| USB 速度 | High Speed 480 Mbit/s（`USBSpeed=3`） |
| 设备类 | 239/2/1（Misc + IAD，典型 CDC/NCM） |
| USB 序列号 | `90E880F3647BC5A9B83B56584225C6263CBC0254` |
| 供电分配 | 500 mA |
| 插在 | 扩展坞 USB2 Hub 后面（locationID 18096128） |

## USB 网络（开 Developer Mode 前后不同）

| 阶段 | Host | 设备 | ping |
|---|---|---|---|
| 未开 Dev Mode | `en13` `169.254.57.114/30` | **`169.254.57.113`**（`blackberry-d0bd.local`） | `.113` 通，`.1` 丢包 |
| 已开 Dev Mode | Host `169.254.0.2` | **`169.254.0.1`**（屏幕上也是这个） | `.1` 通，`.113` 丢包 |
| 2026-09-07 14:18 复查 | 无 BlackBerry 网卡 | 无 | 当时线不在 |
| 2026-09-07 14:22 再插 | `en13` `169.254.134.222/30` | **`169.254.134.221`**（MAC 仍 `96:eb:cd:56:aa:5f`） | `.1` / `.113` 丢包。Dev Mode 已关 |

| 项 | 值 |
|---|---|
| macOS Hardware Port | `BlackBerry`（无需 Link） |
| 设备 MAC（ARP，未开 Dev Mode） | `96:eb:cd:56:aa:5f` |
| TLS 证书 CN | `PlayBook: 94:eb:cd:56:aa:5f`（自签名，2011–2051） |

每次插拔以 `./scripts/q10-detect.sh` 为准。脚本从 BlackBerry 网卡的 /30 推对端，再试 `.1` / `.113`。

## 端口

| 端口 | 状态 | 含义 |
|---|---|---|
| 80, 443, 8443 | 开 | 设备 web / `appInstaller.cgi`；HTTPS = **TLSv1 + 自签名** |
| 139, 445 | 开 | SMB：`media`, `removable_SDCARD` |
| 4455 | 开 | QConn。TCP 能连，无文本 banner |
| 22 | 仅在 `blackberry-connect` 存活时开 | 关 connect 即关 |

## 已装应用（deploy，约 242 行）

- 有 Amazon Android runtime / Appstore、Adobe Reader、`sys.android`、`sys.retaildemo` / `retaildemoshim`
- **无 Term49**、无独立 sshd 应用
- 完整原文在本机 `logs/q10-apps.raw`（gitignore）

## SSH（已通）

- 远程 banner：`SSH-2.0-OpenSSH_6.2 QNX_Secure_Shell-20130711`
- 用户 `devuser`，家目录 `/accounts/devuser`，shell `/bin/sh`。PATH 里没有 `id`
- 专用 RSA-4096：`~/.ssh/q10-usb`，fingerprint `SHA256:qdXD6Rim/Viwq6b0dEv5Idpw5ZSwwrj+/qus4tAnKqE`
- 带注释的 `.pub` 会被设备拒：`Invalid contents after ssh key`
- `blackberry-connect` 必须保持；独立 session 拉起，避免 Cursor 杀进程组
- 失败模式：OpenSSH 10.3 选 `ecdh-sha2-nistp256` + `aes128-gcm@openssh.com` → 对端在 `SSH2_MSG_KEX_ECDH_REPLY` 关连接
- 成功参数：`-F /dev/null` + `KexAlgorithms=diffie-hellman-group14-sha1` + `Ciphers=aes128-ctr` + `HostKeyAlgorithms=ssh-rsa` + `RequiredRSASize=1024`
- `uname -a`：`QNX BLACKBERRY-D0BD 8.0.0 2018/02/21-10:54:19EST MSM8960_V3.2.1.1_N_R085_Rev:16 armle`
- 2026-09-07 用户恢复系统后 host key 换成 `SHA256:NpSPYrZNVNBQrnVFmd/CUgJeJP/tRQsQc5y0uyAzjfc`（只记在 gitignore 的 `local-config/known_hosts`）

## 存储 / 网络（SSH 读回）

| 项 | 值 |
|---|---|
| `/` | `/dev/emmc/user0` qnx6，13G；恢复后用 **2.9G**（23%），恢复前约 3.6G |
| 可移动卡 | `/accounts/1000/removable/sdcard` fat32，7.7G，用 1.5G |
| USB NCM | `ncm0` `169.254.0.1/30`，MAC `96:eb:cd:56:aa:5f` |
| Wi-Fi | `bcm0` 在 Host 同一 LAN（地址不写进脚本） |
| radio / NVRAM 分区 | 只读枚举到了。**未改** |

## 本机 Host

- Darwin 27.0.0 arm64，Rosetta 可用
- `blackberry-deploy` 1.5.0 / `blackberry-connect` 1.2.0：已从已校验 Momentics 2.1.2 DMG 抽出，包装在 `tools/bb10/bin/`
- Java：OpenJDK 17.0.19（Homebrew），需 TLSv1 override
- HTTP 代理存在：访问设备必须 `NO_PROXY=*`
- SSH alias：只加了 `Host q10-usb`（`~/.ssh/config.d/q10-usb` + 顶行 `Include`），未改其他 Host

本文件是 Phase 1 硬件/OS 快照。之后装上的 Term49 / BerryCore / 键盘监视器记在 `BRINGUP.md`，不回改上表。
