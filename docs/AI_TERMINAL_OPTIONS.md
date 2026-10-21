# AI Terminal 选型

## 第一版（已落地）

**Term49 / SSH 上的键盘监视器**。保留为降级和对照，不卸。

| 路线 | 决定 | 原因 |
|---|---|---|
| Term49 + `python3.2` TUI | **采用（降级）** | 已装、键盘可用、能 GET 8787 |
| USB SSH `./scripts/q10-monitor.sh` | **采用** | 与 Term49 同一份脚本，Mac 可取证 |
| Berry Browser Chromium BAR | **禁止** | 作者写明要 root；Q10 上键盘/字号/稳定性有现场缺陷 |
| 设备侧 ChatGPT / bcllm | **禁止** | Q10 是 Interface |
| Cordova / WebWorks 主界面 | **不采用** | 能做壳，手感、录音、通知都不如 Cascades |

产品约束：手机不跑模型。BB10 浏览器 TLS 不当运输层。

## 第二版（2026-09-15 采纳）

**Cascades 原生 App「Q10 Console」** 接本机 Octoooo。手感、`AudioRecorder`、Hub 通知走官方 API。

正本：[plan/2026-09-15-cascades-octoooo-surface-plan.md](plan/2026-09-15-cascades-octoooo-surface-plan.md)。工程契约：`cascades/`。

这改写 Octoooo r6「不新建 BB10 工程」；该实验室仍以 Term49 为兼容回归，本仓库以 Console 为主界面。

| 路线 | 决定 | 缺口 |
|---|---|---|
| Cascades 监视器 + 录音 + 通知 | **采用** | 编译改 Windows win32 NDK；无 debug token；未批准 C7 则装不进未签名 BAR |
| 本机 PTT | **走 Console** | C6 真机 `AudioRecorder` 尚未验 |
| 本仓 720 预览 | **C1 验收面** | `cascades/preview/`，夹具或 Aindle；Octoooo 后接 |
| 出厂浏览器 720 页 | **C1 真机旁路** | `--lan` 后出厂 `B` 打开；不替代主屏图标 |

未另批之前：不 wipe / Autoloader / root。
