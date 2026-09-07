# Q10 Lab

2026 年在这台收藏级 **BlackBerry Q10（SQN100-3）** 上建立可重复、尽量 CLI-first 的 BB10 / QNX 设备实验室，最终让 Codex 能通过 USB SSH 当 remote target 用。这是单机实验室笔记，不是通用刷机包。密码、IMEI、token 不进仓库。

它**不是** ESP32 圆屏项目的分支。圆屏继续走 LVGL / USB CDC-ACM。Q10 走 BB10 USB Networking + QConn。两边只在 **host 侧的 Agent 事件模型**上共用底座，见 [SHARED_FOUNDATION.md](docs/SHARED_FOUNDATION.md)。

## 当前 Host

- 实测平台：macOS（Apple Silicon + Rosetta 已在）
- ChatGPT 原稿优先 Windows。这台 Mac **已经原生识别** `Hardware Port: BlackBerry`，第一阶段不需要开 Windows、不需要 BlackBerry Link。
- USB-facing 命令用本机 `zsh` / `python3` / 官方 host tools。不要把 USB 放进 WSL。

## 安全红线

未获当面批准，禁止：Security Wipe、Factory Reset、Autoloader、OS 升降级、root、改 NVRAM / radio / bootloader、wipe filesystem、删除系统应用。研究恢复路线 ≠ 执行。见 [RECOVERY.md](docs/RECOVERY.md)。

## 第一阶段命令

```sh
./scripts/q10-detect.sh
# 用户打开 Developer Mode 并设好设备密码之后：
./scripts/q10-apps.sh
./scripts/q10-connect.sh
./scripts/q10-health.sh
./scripts/q10-shell.sh            # USB SSH
./scripts/q10-send.sh             # 把脚本推到 /var/tmp，可选 --run
./scripts/q10-monitor.sh          # 键盘 AI Monitor（真机 --once）
./scripts/q10-monitor.sh --local  # Mac 预览同一份 8790
./scripts/q10-launch.sh           # 把 Term49 拉到前台
```

手机一键：主屏快捷键请用 **`Z`**（`1` 出厂是语音信箱）。详见 [LAUNCH.md](docs/LAUNCH.md)。

密码只通过 prompt 或 `local-config/device.env`（已 gitignore）。不要把它贴进聊天。

## 目录

| 路径 | 用途 |
|---|---|
| `docs/` | 来源、基线、USB 链、恢复、与圆屏的共用底座 |
| `scripts/` | 检测 / 连接 / 部署 / 健康检查 |
| `downloads/` | 已校验的安装包与 BAR，不提交 |
| `checksums/` | 期望哈希 |
| `logs/` | 探测与安装日志，不提交 |
| `tools/bb10/` | 解压后的 host tools，不提交 |
| `ai-terminal/` | 键盘 AI Monitor（python3.2 TUI，读 8790） |

## 状态

**Phase 1 完成**（tag `q10-clean-baseline`）。Term49、BerryCore v0.90.1、键盘监视器已装（无 root）。密码不进 Git。
