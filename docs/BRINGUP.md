# Bring-up log

## 2026-09-07 Phase 0 + Phase 1

Host 是 **Mac**。未改手机系统、未刷机、未 wipe、未装 Term49 / BerryCore、未 commit。

### Q10 USB BRING-UP COMPLETE

| 项 | 值 |
|---|---|
| Device | BlackBerry Q10 / SQN100-3 / PIN `0x2ae7d0bd` / `BLACKBERRY-D0BD` |
| OS | BB10 **10.3.3.3216**（`BB10_3_3` / build 911537）。口述 10.3.3.2137 作废 |
| QNX | `QNX BLACKBERRY-D0BD 8.0.0 2018/02/21-10:54:19EST MSM8960_V3.2.1.1_N_R085_Rev:16 armle` |
| USB IP（Dev Mode 开） | 设备 **`169.254.0.1`**，Mac `169.254.0.2`（`en13` / `ncm0`） |
| deploy | `listDeviceInfo` + `listInstalledApps` 成功。`dev_mode_enabled true` |
| connect | `Successfully connected`；进程须保持。22 仅此时开 |
| SSH | `devuser` + `~/.ssh/q10-usb`。必须 `-F /dev/null` 并强制 `diffie-hellman-group14-sha1` + `aes128-ctr` + `ssh-rsa` |
| Baseline | `/` 13G 用 3.6G；用户 `devuser` 家目录 `/accounts/devuser`；Wi-Fi `bcm0` 在同一 LAN。无 Term49 |
| Next | Term49 / BerryCore / 独立 sshd / AI Terminal。**等用户点头再做** |

### 已完成

- 独立仓库，与 ESP32 圆屏分离。见 `SHARED_FOUNDATION.md`。
- USB：RIM `0x0FCA:0x8017`。Mac 原生 `Hardware Port: BlackBerry`。
- USB 地址会变：未开 Dev Mode 见过 `169.254.57.113`、`169.254.134.221`；开了是 `169.254.0.1`。
- Momentics 2.1.2 CLI 已抽出。Java 17 + TLSv1 override。
- 公钥必须剥注释，否则 `Invalid contents after ssh key`。
- 现代 OpenSSH 10.3 若走 `ecdh-sha2-nistp256` + GCM，QNX OpenSSH 6.2 会在 `KEX_ECDH_REPLY` 直接关连接。
- 只加了 `Host q10-usb`。可靠入口是 `./scripts/q10-shell.sh`（macOS `crypto.conf` 会盖掉 Host 的 KEX）。
- BerryCore latest **v0.90.1**、Term49 **0.4.1.7** 只核过版本，**未下载安装**。

### 2026-09-07 18:39 用户自行恢复系统后重对应

用户恢复后重开 Developer Mode，密码仍走 `local-config/device.env`。本机未 wipe。

| 项 | 恢复后实测 |
|---|---|
| USB | 仍是 `en13`，设备 **`169.254.0.1`**，Mac `169.254.0.2` |
| 身份 | 仍是 Q10 SQN100-3 / PIN `0x2ae7d0bd` / `BLACKBERRY-D0BD` / OS **10.3.3.3216** |
| deploy | `listDeviceInfo` / `listInstalledApps` 成功（约 251 行，仍无 Term49） |
| connect | `Successfully connected`，pid 仍须保持 |
| SSH host key | **已换**。旧 `SHA256:HntCldUR…`，新 `SHA256:NpSPYrZN…`。只改了本仓库 `local-config/known_hosts` |
| `uname` | 仍是 `QNX … 8.0.0 2018/02/21-10:54:19EST MSM8960_V3.2.1.1_N_R085_Rev:16 armle` |
| 磁盘 | `/` 13G 用 **2.9G**（恢复前约 3.6G） |

注意：恢复后无密码的 `listDeviceInfo` 会被算一次认证失败（当时 1/5）。`q10-detect.sh` 已改为没有密码就不探，避免锁设备。

### Phase 1 关闭（用户判定完成）

- Security Wipe 口令已是 `blackberry`（不再要 BBID Verify）。
- 已卸 LinkedIn / Twitter / Facebook / Evernote / Amazon Shop / Amazon Appstore。
- YouTube 无独立应用，系统 Hub 连接器未动。
- Golden baseline：`docs/GOLDEN_BASELINE.md` + tag `q10-clean-baseline`。
- 下一阶段：先 Term49，再评估 BerryCore。不改圆屏仓库。

### 2026-09-07 Term49（Phase 2 第一步）

- 已下并校验 `downloads/Term49.bar`（不进 Git）。
- `blackberry-deploy -installApp` → `result::success`，版本 1.0.0.1。
- `listInstalledApps` 有 `com.example.Term49…`。
- `-launchApp` 回报 `Info: done`。请在手机主屏确认图标和终端能开。
- SSH 可见 `/accounts/1000/appdata/com.example.Term49…`。`/apps` 对 `devuser` 无权限。
- BerryCore **仍未装**。

### 2026-09-07 Term49 本机验收 + 8790 对应

用户确认：Term49 能打字；左上角元模式绿 M；`k/j/h/l` 方向；`c` 再 `c` = Ctrl-C。

Mac 侧对应：

- `isAppRunning` = true
- Q10 `python3.2` GET `http://169.254.0.2:8790/snapshot.json` → `aindle.snapshot.v2`，hub `mini`，hosts=1 / runs=3 / subs=11
- 脚本：`./scripts/q10-snapshot.sh`

### 2026-09-07 BerryCore v0.90.1（userland）

用户要求不在 Term49 里手敲。用 USB SSH `devuser` 跑 `install.sh -y`，写到 `shared/misc`（HOME 是 `devuser`，对 SSH 有用）。

- `INSTALL_EXIT=0`，约 98 包。日志 `logs/q10-berrycore-install.log`
- `qpkg` / `curl 8.12.1` / `git` / `vim` 在 PATH
- BerryCore `curl` 再拉 `http://169.254.0.2:8790/snapshot.json` → `aindle.snapshot.v2`
- `/` 约 3.8G / 30%。未 root、未装 Browser BAR、未开 `sshd-on`、未下本机模型
- `gcc.zip` 只有 134 字节，解压失败
- Term49：`. /accounts/1000/shared/misc/use-berrycore.sh`

详见 `BERRYCORE.md`。

### 2026-09-07 键盘 AI Monitor

与圆屏同一份 `aindle.snapshot.v2`。设备 `python3.2` TUI，不改圆屏仓库。

- 脚本：`ai-terminal/q10_monitor.py`，入口 `./scripts/q10-monitor.sh`
- Mac unittest 13 项通过（限额已用%、spend 不混、error 不是 0%、等你须 direct+needs_input）
- 真机 `--once --all`：hub `Mac mini`，新鲜，主机 mbp ok，ASK 0，Gemini 不可用（不是 0%），DeepSeek 在余额栏
- Term49：`/accounts/1000/shared/misc/q10mon`
- 未做：PTT、Berry Browser、独立 sshd、设备侧对话

详见 `ai-terminal/README.md`、`AI_TERMINAL_OPTIONS.md`、`LAUNCH.md`。

### 2026-09-07 一键启动审查

- Q10 **没有** KEYone 那种侧键。主屏字母快捷键是官方能力。
- 出厂 `1`/`W` = 语音信箱。空键用 **`Z` → App Launch → Term49**。
- SSH 不能写 Term49 `$HOME`。自动进监视器要在 Term49 里跑一次 `q10-autostart.sh`。
- Mac：`./scripts/q10-launch.sh` 可 `-launchApp` Term49。
