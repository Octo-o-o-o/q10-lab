# AI Terminal 选型（已定第一版）

第一版是 **Term49 / SSH 上的键盘监视器**，不是 Cascades BAR，也不是 Berry Browser。

| 路线 | 决定 | 原因 |
|---|---|---|
| Term49 + `python3.2` TUI | **采用** | 已装、键盘可用、能 GET 8790 |
| USB SSH `./scripts/q10-monitor.sh` | **采用** | 与 Term49 同一份脚本，Mac 可取证 |
| 自签 Cascades 监视器 BAR | 不做 | 无 debug token；生产签名一套未建 |
| Berry Browser Chromium BAR | **禁止** | 作者写明要 root |
| 设备侧 ChatGPT / bcllm | **禁止** | Q10 是 Interface；未授权下模型 |
| 本机 PTT / 语音 | 未对应 | 须先用 BB10 实机 API 验证，不能假设能 hook |

产品约束未改：数据源是 Mac `aindle.snapshot.v2`；BB10 浏览器 TLS 不当运输层。
