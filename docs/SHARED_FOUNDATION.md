# 与 ESP32 圆屏项目能否共用底座

结论先说：**产品目标可以共用，设备底座不能共用。**  
圆屏仓库：`/Users/wangyixiao/WorkSpace/esp32/waveshare-ESP32-S3-Touch-AMOLED-1.75C`。本仓库不改那边的固件或 USB bridge。

## 圆屏现在是什么

现行链路（`experiments/octoooo-mini/mini`）：

```
Aindle registry
        │  collector.mjs
        ▼
  127.0.0.1:8787  GET /snapshot.json   schema aindle.snapshot.v2
  （圆屏 collector 仍写死 8790；Q10 读 8787，不要再起抢端口的 8790 Hub）
        │
        ├─ USB Serial/JTAG ──► ESP32 LVGL（表盘 + 限额/任务/待处理 + BOOT PTT）
        └─ VoiceService / broker（STT + Agent 在 Mac）
```

设备侧是自定义 USB 帧，不是 ADB，也不是 BB10 QConn。

## Q10 要成为什么

同一类产品角色：**Interface，不是 Intelligence。**

| 面 | 圆屏 | Q10（第二阶段起） |
|---|---|---|
| 数据 | 读 Hub 快照（圆屏 collector 仍指向 8790） | **同一份** `aindle.snapshot.v2`（Q10 读 8787） |
| 呈现 | 466 圆屏，左右滑三页 | 720×720 + 物理键盘信息终端 |
| 交互 | 触摸 + BOOT PTT | 键盘；PTT 以后用实机 API 验证 |
| 智能 | 不在板上跑 LLM | 不在 QNX 上跑 Whisper / LLM |

可视化字段对齐圆屏：Agent / Task / Run / Usage / Machine / Approval / Event。  
新鲜度语义对齐：`seenAt` / `status` / `staleHosts` / `confidence`；生成时间 ≠ 采集时间。

## 可以共用

1. Host 事件模型与 Hub 快照。
2. 采集失败标 error/unknown，不写假的 0%。
3. 语音：设备只出 PTT/PCM；STT/Agent 在电脑上。
4. 「电脑在线才完整」的 tethered lab 假设。

这些以后抽 `ai-gateway`。不是把圆屏固件拷进 Q10。

## 不能共用

| 层 | 圆屏 | Q10 |
|---|---|---|
| SoC / OS | ESP32-S3 / FreeRTOS | MSM8960 / BB10 / QNX |
| USB | Espressif CDC-ACM 串口 | RIM `0x0fca:0x8017` USB 网卡 |
| 地址 | `/dev/cu.usbmodem*` | `169.254.0.1` + QConn `:4455` + SSH |
| 部署 | `idf.py flash` | `blackberry-deploy` + 已签名 BAR |
| 日常控制 | 串口 ACK | `./scripts/q10-shell.sh` |

Q10 要读 Aindle Hub，Mac 必须把 hub **绑到 Q10 能路由到的地址**（USB `169.254.0.2` 或双方都在的 Wi-Fi LAN）。只听 `127.0.0.1` 时手机摸不到。默认端口 `AINDLE_PORT=8787`；客户端探测 last-good 与 `Q10_HUB_PORTS`（8787、回退 8790），不要在本仓库另起 Hub。BB10 浏览器 TLS 很老；USB/LAN 用库存 `python3.2` 拉 HTTP。异地走 BerryCore `curl` + [MAILBOX.md](MAILBOX.md)，不要假设库存 HTTPS 能用。

## 已实测（2026-09-07）

Q10 USB SSH 用 `python3.2` 拉 Hub 快照成功（当时端口 8790；现默认 8787）：

- schema `aindle.snapshot.v2`
- hub `mini` / Mac mini
- `staleHosts` 空
- hosts / runs / subscriptions 都有真实条目

本机 Hub 当时同时听在 `127.0.0.1`、`169.254.0.2`、LAN（端口当时 8790，现 8787）。圆屏仍走串口；Q10 走 USB 网卡。同一份 JSON。

复查：`./scripts/q10-snapshot.sh`

## 阶段

1. Phase 1：USB / deploy / connect / SSH。已完成（`q10-clean-baseline`）。
2. Term49：已装，用户确认本机键盘 + 元模式可用。
3. BerryCore userland **已装**到 `shared/misc/berrycore`。不 root、未装 Browser BAR。
4. Q10 键盘监视器 **已落地**（Term49 / SSH TUI，`./scripts/q10-monitor.sh`）。主屏一键用 **`Z` → Term49**，见 `LAUNCH.md`。不做小 ChatGPT。
5. **主界面改 Cascades「Q10 Console」**（2026-09-15）：录音/通知走官方 API。Term49 留下降级。C1 先走本仓 `cascades/preview/`（Aindle / 夹具）。Octoooo 合同后接。Berry Browser、独立 sshd、设备侧 LLM 仍不做。PTT 以 Console `AudioRecorder` 为准，尚未真机验收。正本 `docs/plan/2026-09-15-cascades-octoooo-surface-plan.md`，闸门 `docs/plan/2026-09-15-cascades-gates.md`。

设备侧读 Hub `8787`，**不读** Mac `/tmp/octoooo-mini-*/source-times.json`。没有 sidecar 时，缓存限额的年龄写「时间未知」，不用 Hub `generatedAt` 冒充采集时间。
