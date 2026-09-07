# 与 ESP32 圆屏项目能否共用底座

结论先说：**产品目标可以共用，设备底座不能共用。**  
圆屏仓库：`/Users/wangyixiao/WorkSpace/esp32/waveshare-ESP32-S3-Touch-AMOLED-1.75C`。本仓库不改那边的固件或 USB bridge。

## 圆屏现在是什么

现行链路（`experiments/octoooo-mini/mini`）：

```
Aindle registry
        │  collector.mjs
        ▼
  127.0.0.1:8790  GET /snapshot.json   schema aindle.snapshot.v2
        │
        ├─ USB Serial/JTAG ──► ESP32 LVGL（表盘 + 限额/任务/待处理 + BOOT PTT）
        └─ VoiceService / broker（STT + Agent 在 Mac）
```

设备侧是自定义 USB 帧，不是 ADB，也不是 BB10 QConn。

## Q10 要成为什么

同一类产品角色：**Interface，不是 Intelligence。**

| 面 | 圆屏 | Q10（第二阶段起） |
|---|---|---|
| 数据 | 读 8790 快照 | **同一份** `aindle.snapshot.v2` |
| 呈现 | 466 圆屏，左右滑三页 | 720×720 + 物理键盘信息终端 |
| 交互 | 触摸 + BOOT PTT | 键盘；PTT 以后用实机 API 验证 |
| 智能 | 不在板上跑 LLM | 不在 QNX 上跑 Whisper / LLM |

可视化字段对齐圆屏：Agent / Task / Run / Usage / Machine / Approval / Event。  
新鲜度语义对齐：`seenAt` / `status` / `staleHosts` / `confidence`；生成时间 ≠ 采集时间。

## 可以共用

1. Host 事件模型与 8790 快照。
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

Q10 要读 8790，Mac 必须把 hub **绑到 Q10 能路由到的地址**（USB `169.254.0.2` 或双方都在的 Wi-Fi LAN）。只听 `127.0.0.1` 时手机摸不到。BB10 浏览器 TLS 很老，第一版优先 Term49 里 `curl` HTTP，不要假设能开现代 HTTPS。

## 阶段

1. Phase 1（本 tag）：USB / deploy / connect / SSH。已完成。
2. 先 Term49，本机终端，不依赖 USB 也能探 QNX。
3. 再评估 BerryCore，确认它动哪些系统组件后再装。
4. 然后 Q10 client 读同一 8790 快照。不做小 ChatGPT。
