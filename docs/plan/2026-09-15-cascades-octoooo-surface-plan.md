# Q10 Cascades 主界面（接 Octoooo）

日期：2026-09-15  
状态：已采纳方向，未开工刷机 / 未取 NDK / 未装新 BAR  
取代：Octoooo r6「Q10 只保留 Term49、不新建 BB10 工程」；本实验室以 Cascades 为**主界面**。历史 r6 文档不回改，以本文件为准。

## 决定

主屏图标打开 **Q10 Console**（Cascades / C++）。手感、录音、Hub 通知走官方 API。数据只打本机 `~/WorkSpace/Octoooo`，不在手机上跑模型、不直连 OpenAI。

Term49 **0.4.1.7** 监视器留下当降级和对照，不卸。Berry Browser 仍禁止。未另批之前：不 wipe、不 Autoloader、不 root、不改 NVRAM / radio / bootloader。

## 做成什么样

720×720 原生页，键盘第一：

| 键 | 作用 |
|---|---|
| `2` / `E` | 任务 |
| `3` / `R` | 待处理 |
| `W` 在监视器里是限额；Console 用 **`Q` 或空的字母** 回限额，不抢出厂 `1`/`W` 语音信箱 |
| 按住约定键 | 录音；松开上传 Mac |
| `x` | 退出确认（或回封面） |

默认落地限额页。用量阅读时新待处理只加角标 / Hub 通知，不抢页。数字：超限原值、空窗「—」、花费≠限额、过期标旧。截断正文禁用操作，写「请在电脑看」。Active Frame：时钟 + 最高已用% + 待处理数。

语音：设备只出 PCM（16 kHz / mono / s16le，≤15 s）。STT 与意图在 Octoooo / Mac。入口在「有声波 + 转写成功」之前不得显示「开始说话」。改事项要确认，迟到 `audio_id` 丢弃。契约对齐 `Octoooo/docs/contracts/voice-assistant.md`，**第一版用 HTTP 上传**，不把 Tab5 WebSocket 当必经。

## 和 Octoooo 怎么接

弱端只读，身份独立：

- 本地 `Q10_OCTOOOO_BINDING_FILE`（建议 `/accounts/1000/shared/misc/q10-octoooo.binding`，权限 **640**，格式与信箱 token 同纪律：不进 Git）
- 轮询：`GET /v2/usage`、`GET /v2/sync/snapshot`（或一条已投影的 `projection.json`）
- USB / 家宽：**HTTP**。库存 BB10 TLS 不当运输层
- 远途：信箱或以后才开的设备 HTTPS 入口
- 撤销 / 过期：清事项；已到用量可留，须标旧
- 不做已读 / 关闭 / `reply.submit`，直到只读稳了再单开

Aindle `8787` 监视器可暂时并行。Console 的权威源是 Octoooo，不在 QNX 另起 Hub。

## 本机缺口（2026-09-15 核对）

| 项 | 现状 |
|---|---|
| Cascades 编译器 `qcc` / `qmake` / NDK | **没有**。`tools/bb10/` 只有 `blackberry-deploy` / `connect`。Momentics 2.1.2 Mac DMG 是 IDE，不含 `host_10_3_1_12/darwin` |
| 公开 Mac NDK 包 | `docs/SOURCES.md`：IA 列出的是 win32 tools；macosx 官方链今日空 |
| Debug token | 设备 `no debug token found` |
| 生产签名 | 一套未建；官方签名服务 EOL |
| 装未签名 BAR | 库存机拒绝（社区 Chromium 881） |
| 录音硬件 | `/dev/snd` 在；Cascades `AudioRecorder` 未在这台机验过 |
| Term49 录音权 | 已装 0.4.1.7 **无** `record_audio` |

因此：**方向已定，现在还不能出可安装 BAR。** 编译改走 Windows win32 NDK（这台 arm64 Mac 不跑 darwin `qcc`）。安装闸另批。闸门推进正本：`docs/plan/2026-09-15-cascades-gates.md`。Octoooo 仓库另有在途工作，合同对接放到最后。

## 工程落点

仓库内 `cascades/`（包名 `com.q10lab.console`）。清单见该目录 `bar-descriptor.xml`。源码按闸补，不在无 NDK 时假装能编过。

官方 API（有 NDK 头文件后再写实现）：

- 界面：`Page` / `ListView` / `Container`；按键 `shortcuts` + `keyReleased`
- 网络：`QNetworkAccessManager`（先 HTTP）
- 录音：`bb::multimedia::AudioRecorder` → 共享目录 WAV → `POST` 到 Mac
- 通知：`bb::platform::Notification` + `post_notification`
- 封面：`SceneCover` / Active Frame

失败回退（不替代主路径）：出厂浏览器打开本仓 `cascades/preview/`；Term49 `q10mon` 读 Aindle。Octoooo 720 页等对方仓库空闲后再接，只换投影上游。

## 闸门

**C0 合同（本文件 + `cascades/` 契约）** — 本次完成。

**C1 本仓 720 预览** — `cascades/preview/` 出 720×720 限额/事项页 + `q10.console.projection.v1`。数据来自夹具或既有 Aindle 8787。Mac 浏览器先验收；真机可用出厂 `B` 打开 `--lan` 地址。不依赖 Cascades，不改 Octoooo。失败则停，不下 NDK、不刷机。

**C2 工具链** — **书面改用 Windows x64 编 BAR**（WoW64 跑 IA `bbndk.win32.*`）。这台 Mac 只 `blackberry-deploy`。不要把「本机 darwin `qcc -V`」当成功标准。未校验哈希的 NDK 不跑（`SOURCES.md`）。未另说不下载 1.6GB libraries。

**C3 Hello BAR** — 一屏字 + 版本号，能在模拟器或（若已有安装闸）真机打开。无安装闸时只保留未签名制品，不报「已交付真机」。

**C4 三页 + 轮询** — 与 C1 同一份 JSON。和 Term49 监视器对照字段，不对照像素。

**C5 通知** — 新待处理打一条 Hub 通知；点开回 App。库存 Term49 无此权，必须是 Console BAR。

**C6 录音** — `AudioRecorder` 2 秒，共享目录文件 >0 字节。再接 Octoooo 上传与 STT。QSA/`talkbutton` 只作对照，不当产品录音栈。

**C7 安装** — **另需一句明确批准**：debug token **或** root/Autoloader（建议炮灰机，这台 SQN100-3 先保持库存）。未批准前 C3–C6 的真机安装保持未完成。

## 明确不做

- 设备侧 ChatGPT / bcllm / Vosk 当产品识别
- Cordova / WebWorks 作为主界面（可当实验，不替代 Console）
- Berry Browser、未签名 Chromium 当主 UI
- 把 Tab5 LVGL / USB 帧协议套过来
- 改 NVRAM、解锁、降级
- 密钥进 Git

## 验收（真机，分闸）

- C1：本仓预览肉眼三页、未知不是 0%、断网留旧或诚实不可用。不要求 Octoooo 已出页。
- C4：键盘切页，与监视器同一快照条数/状态
- C5：来一条待处理，Hub 有通知，用量页不被抢走
- C6：按住有波形文件；Mac 日志有 `audio_id`；未配 STT 显示未配置
- C7：`listInstalledApps` 有 `com.q10lab.console`，主屏图标能开
