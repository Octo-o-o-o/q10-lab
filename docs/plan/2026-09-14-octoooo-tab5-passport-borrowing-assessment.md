# Octoooo Tab5 / AI Passport 借鉴评估

日期：2026-09-14  
范围：只评 `~/WorkSpace/Octoooo` 的 **Tab5** 与 **AI Passport**。不是 Octoooo 全仓盘点，也不把 r6 手机/手表/Aindle 输出服务算进来。  
本产品语境：Q10 键盘监视器（Term49 / `python3.2`），角色是 Interface，数据源是 Mac `aindle.snapshot.v2`（默认 `8787`）。

## 既有评估

- 本仓库 `docs/` **没有** 对 Octoooo / Tab5 / Passport 的借鉴评估。`docs/SHARED_FOUNDATION.md` 对照的是微雪圆屏，不是这两块屏。
- Octoooo 自己把 Q10 写成受限只读面（`docs/profiles/r6-surfaces.md`：文本三页、offset 分页、未知不归零、过期拒绝、无读态操作）。那是对方看 Q10，不是本仓已落地的适配。当前 `q10-lab` **没有** `Q10_OCTOOOO_BINDING_FILE`、租约或 `/v2/sync/snapshot` 客户端。

## 借鉴目标

要补的是监视器还缺、且不破坏现线的能力：

1. 限额数字诚实：未知不是 0，超限不是 100，过期不是实时。
2. 阅读用量时不被刷新抢走焦点；待处理仍可发现。
3. 以后若做 PTT，设备只出按键/PCM，识别与动作在 Mac；入口在未协商前不得显示「可用」。
4. 不换 Hub、不 root、不新 BAR、不把 Tab5/Passport 固件或 USB/Wi-Fi 协议套到 QNX。

成功标准：裁决能落到 `ai-terminal/q10_monitor.py` 或明确「等产品决定 / 等实机 API」；对方能力有本会话读过的代码或文档行号。

## License

本会话在 Octoooo 仓库根 **未找到** `LICENSE`。`package.json` 为 `"private": true`。  
Tab5 BSP（`firmware/tab5/components/m5stack_tab5/LICENSE`）与 Passport BSP（`firmware/ai-passport/components/bsp/LICENSE`，Copyright 2026 FoloToy）为 **MIT**，只管板级驱动，不管网关与业务 UI。

裁决：只借语义与交互规则，**不复制** Tab5/Passport 的 C/LVGL、不引入 Octoooo runtime、不把私有网关合同当本仓默认运输层。

## 红线（本仓已定，本次不放松）

- 未当面批准：wipe / Autoloader / 升降级 / root / 改 NVRAM / radio / bootloader / 删系统应用。
- 不装 Berry Browser（要 root）。不在 QNX 跑 LLM / Whisper。
- 不另起 Hub、不抢圆屏 collector 的 8790。USB 留 macOS 本机。
- 密码 / IMEI / token 不进 Git。
- Tab5/Passport 的 `reply.submit` 只进 `test-inbox`，`side_effect_allowed=false`。不能把这条回程接到真 Agent。

---

## 承重现状（本产品已有）

对照 `ai-terminal/q10_monitor.py`，不是印象：

| 能力 | 本仓 | 位置 |
|---|---|---|
| 三页限额 / 任务 / 待处理 | 已有 | `PAGES` L28；渲染 `render_page` L2179 |
| 同一份 `aindle.snapshot.v2` | 已有 | `SNAPSHOT_SCHEMA` L20；`fetch_first_snapshot` L1527 |
| USB → 局域网 → 信箱换源 | 已有 | `docs/MAILBOX.md`；`list_hub_urls` 路径 |
| 失败保留旧画面、标离线 | 已有 | `mark_offline` L804；主循环 L2402 |
| 采集失败 / 缺失不写 0% | 已有 | `_quota_item` L654–661；测试 `test_error_and_missing_are_not_zero` |
| 花费 ≠ 限额、账户不加总 | 已有 | L671–676；文案 L184 |
| 待处理不提交、请在电脑处理 | 已有 | `_ask_body` L1967、L1993、L1997；`no_chat` L169 |
| 新待处理自动跳页 | **已有且与对方相反** | `ask_jump` L2119；启动 L2355；刷新 L2398 |
| 用量数字夹到 0–100 | **已有且比对方更假** | `used_pct` L381–390 |
| 无百分比的窗口直接丢掉 | **已有缺口** | `_windows` L598–601 |
| PTT / 设备录音 | 未对应 | `docs/AI_TERMINAL_OPTIONS.md`；`SHARED_FOUNDATION.md` §5 |
| Octoooo 配对 / 租约投影 | 没有 | 本仓无 binding 文件、无 `/v2/sync` |

---

## 能力表

编号只覆盖本次读过的 Tab5 / Passport 相关模块。裁决：A 直接借 / B 改造借 / C 不借。

| # | 对方能力 | 出处 | 本仓 | 裁决 | 理由 |
|---|---|---|---|---|---|
| 1 | `used_percent` 原值可 >100；条只截 0–100；`null` 显示「—」不画 0 | Tab5 `octo_ui.c` L1081–1130；`octo_network.c` `parse_quota` L235–240 | `used_pct` 夹到 100；`pct is None` 则丢窗口 | **A** | 同一份 Aindle `windows[].pct`，改解析/画条即可 |
| 2 | 空/未知窗口仍占一行 | 同上；Passport 用量 `--` / 「旧」 | `_windows` 丢 `None` | **A** | 与 #1 同一刀；现测试未覆盖 132% / null |
| 3 | 用量/设置页不被新事项打断，只更新计数 | Tab5 `octo_ui.c` L984–987 | `ask_jump` 启动和刷新都切到待处理 | **B** | 口袋机「等你」要不要抢焦点是产品选择；页脚已有 `待处理(N)`（`render_page` L2198） |
| 4 | 首次同步不抢个人页；阅读/确认中不打断；息屏不自动切走 | Passport `octo_ui.c` L207、L1683–1685 | 启动即跳 | **B** | 可借「首次基线不响/不跳、之后才提示」；不要借名牌首页 |
| 5 | 租约 60s 到期清事项；撤销/401/403 清投影；断连才清空用量 | Tab5 `octo_network.c` L580–599、L816、L1483–1489；schema `expires_at` | Aindle 轮询，无 lease | **B** | 只在将来接 Octoooo 弱投影时用。现在套 60s 清屏会误伤 USB/信箱缓存 |
| 6 | 分页事项不覆盖 `quota.sync` | Tab5 `octo_network.c` L248–249 | 单源快照 | **C** | 本仓没有第二条用量通道；重复 |
| 7 | 弱认证只读；已读/关闭/固定回复进 test-inbox | Tab5 README；合约 `side_effect_allowed=false` | 已明确不提交 | **C** | 重复。把 test-inbox 接真 Agent 是红线 |
| 8 | 详情截断则禁用操作，要求电脑看全文 | Passport `octo_ui.c` L1694–1698、L776 | 待处理已写「请在电脑处理」，无详情页 | **B** | 只有以后加长文详情才落地；现在不必为它开详情 |
| 9 | 提交后等 ACK；`request_id` 对齐；12s 未确认可返回、不自动重试未知结果 | Passport `octo_wait.h`；README 等待反馈节 | 无回写 | **B** | 等信箱/PTT 真有回程再借。现在无动作可确认 |
| 10 | 语音：能力 / 服务 / 权限三轴；旧网关当不支持；迟到 `audio_id`/`turn_id` 丢弃；改状态要 `assistant.confirm` | `docs/contracts/voice-assistant.md`；`firmware/shared/octo_assistant/octo_assistant_client.c` L339、L366 | PTT 未对应 | **B** | 借诚实入口与迟到丢弃，不借 Tab5 WS/`audio.chunk`。STT 在 Mac |
| 11 | Passport 本地模拟聆听 + 剧本 HITL + 麦克风只打波纹 | Passport README「语音模拟交互」 | 无 | **C** | 会把假转写当成助手。红线 |
| 12 | Tab5 480KB PSRAM 整段录音；Passport 明确不能照搬 | Tab5 README 回复页；Passport README 实现范围 | Q10 无已验证麦 API | **C** | 无 PTT 证据前不搬录音栈 |
| 13 | 三皮肤、SD 音乐/照片、唤醒八音盒、天气、名牌插画、开发者二维码 | 两份固件 README 大部 | Term49 文本 TUI | **C** | 板级娱乐面，不增加监视器信息 |
| 14 | Wi-Fi 配对码、NVS token、C6 hosted | Tab5 README Stage 2 | USB 网卡 / SSH / 信箱 token 640 | **C** | 底座不能共用（同 `SHARED_FOUNDATION.md`） |
| 15 | 联网息屏 / 背光 / 唤醒手势消费 | Passport idle 节 | Term49 常亮会话 | **C** | 终端生命周期不同；省电不是本阶段目标 |
| 16 | Host 离屏 LVGL 状态矩阵（0/1/16/17、132%、unknown、过期） | Tab5 `scripts/verify-tab5-render.py`；Passport `ui_check` | `test_q10_monitor.py` 已有基线，缺超限/空窗/不抢焦点负例 | **B** | 借场景清单，不借 C 测试桩 |
| 17 | 用量条 >90 琥珀 / ≥100 红；重置倒计时每秒刷新 | Tab5 README §3.5；`octo_ui.c` L1118–1122 | 重置是时钟点 `format_reset` L410 | **B** | 终端可用 `!` / 倒计时文案；非第一刀 |
| 18 | 用 Octoooo 网关替换 Aindle 8787 | Tab5 绑 `OCTO_PORT=8787` | Hub 合同已定 | **C** | 端口碰巧同号，协议不是同一份 JSON |
| 19 | r6 为 Q10 设计的 HTTPS binding + 弱投影 | `r6-surfaces.md` Q10 行 | 本仓未落地 | **B** | 可选第二源，0600 文件。不替换 Hub，不自动启用 |

---

## 计数

- **A 2**（#1、#2，实施时算一刀）
- **B 7**（#3、#4、#5、#8、#9、#10、#16；#17、#19 为后续 B）
- **C 8**（#6、#7、#11–#15、#18）

表内 #17/#19 也是 B，若计入 **B=9**。上面主计数按「现在还值得排期」的 B=7，加上两个后置 B。

## 第一刀

**限额数字诚实**（A #1+#2），只改 `ai-terminal/q10_monitor.py` + 现有 unittest：

1. `used_pct` 保留有限数字原值（允许 132），不要 `min(100)`。
2. 画条仍截 0–100（已有 `art_bar`）。
3. `_windows` 在 key 合法但 `pct is None` 时保留一行，单元格走已有 `?` / 「缺失」，不要静默丢行。
4. 补测试：`132` 显示 132% 且条满；`null` 窗口仍在列表；账户仍不加总。

不改真机、不改 Hub、不引入 Octoooo 客户端。

第二刀（需你拍板，不自动做）：`ask_jump` 是否改为「用量页只加页脚角标，不切页；仅启动时若已有待处理才落在待处理」。Tab5 选不打断；Passport 选后续新未读才切。Q10 是口袋「等你」终端，抢焦点可能仍正确——这不是默认 A。

## 不借清单

- LVGL / ESP-IDF / 配对 / NVS / C6 / Wi-Fi WebSocket 固件整棵。
- 皮肤、SD 媒体、天气、名牌、二维码、息屏音乐。
- Passport 假语音与剧本回复。
- Tab5 `test-inbox` 回发、已读/关闭写回。
- 用 Octoooo 网关替换 Aindle Hub（8787 同号 ≠ 同合同）。
- 设备侧 STT / LLM / 整段录音缓冲。
- 未批准的 root / 新 BAR / Berry Browser。
- 把 Tab5 USB 或圆屏帧协议套到 RIM `0x0FCA:0x8017`。

## 对方实现摘记（避免以后凭印象）

Tab5（ESP32-P4，1280×720）：WS 认证 + HTTP `/v2/sync/snapshot` 分页（每页最多 16）+ `/v1/quota`；用量是默认落地页；语音助手走 `firmware/shared/octo_assistant`，改事项要确认卡。若干 UI/语音项在其 README 仍标 ⚠️ 待实机。

Passport（ESP32-C3，240×320，三键）：保留旧 WS，**没有** Tab5 那套分页 HTTP；用量轨道 + 事项 + 设置。真实用量同步有实机日志。语音在本会话所读 README 里仍是「麦克风幅度 + 预设剧本」，不是网关 STT。无 PSRAM，明确不能搬 Tab5 录音缓存。

两块屏共享的、真正和 Q10 同构的东西只有：**弱端只看、未知/过期诚实、权威在电脑、动作要么没有要么二次确认。** 板级 UI 与运输层不要搬。
