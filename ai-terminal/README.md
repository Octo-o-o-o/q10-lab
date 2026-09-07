# Q10 键盘 AI Monitor

Q10 是 **Interface**，不是 Intelligence。读 Aindle Hub 同一份 `aindle.snapshot.v2`（默认 `http://<Mac-USB>:8787/snapshot.json`，端口跟 `AINDLE_PORT`）。不做小 ChatGPT，不在 QNX 上跑 LLM / Whisper。端口改了会探测 last-good 和 `Q10_HUB_PORTS`（8787 再 8790），不要在本仓库另起 Hub。

## 页面对齐圆屏

| 键 | 不按 Alt | 页 | 圆屏对应 |
|---|---|---|---|
| `1` | `W` | 限额 | 窗口 **已用 %**；`spend` 不混进限额 |
| `2` | `E` | 任务 | 顶部并入状态行：等你/人手/后台 · 采集 · 主机；过期主机标「旧记录」 |
| `3` | `R` | 待处理 | 仅 `wait + direct + needs_input`；提示在电脑处理 |
| `4` | `S` | 待处理 | 现三页，与 `3`/`R` 相同 |

`j`/`k` 翻条，`t` 刷新（约 10 秒也可自动；不用 `R`，否则挡住第 3 页），`x` 退出。失败保留上一屏并标离线，**不会**偷偷改演示数据。`--demo` 必须显式。有待处理时：启动直接落在待处理页；刷新发现**新**待处理自动跳页（看过的不会反复抢焦）；待处理页上下用满宽 `█` 告警条，页眉和页脚带计数。

排版对齐 Kindle 那一屏：页眉左页名·新鲜度、右链路·主机，下面一条 `─` 实线（推送的等宽字体已把 `─` 字形横向拉满格，不断线）；限额条是 `█` 满格块加 `·` 空槽，同一工具多窗口只写一次名字，百分比右齐；任务页顶部是状态区（计数、采集、主机点线引导），下面任务左边 `●` 标等你、右边项目（没有则工具名）右齐。屏幕装不下时按终端行数截断并留「另有 N 项 · j/k」。主机名缩成 `MBP` / `Mini`，因为等宽黑体里每个英文字母也占一格汉字宽。`--lang en` 时结构字符退回纯 ASCII（`-` `.` `#` `*`）。

默认界面是中文。任务标题本身也可能是中文。Term49 按字母 `X` 的宽度画格子，系统黑体汉字更宽会叠在一起。推送时会做成等宽 `q10-cjk-mono.ttf`。手机里按 `x` 只退监视器，**不会**换字体。信箱 token 须 640。

异地（流量 vs 家宽）见 [MAILBOX.md](../docs/MAILBOX.md)。监视器每次刷新按 last-good → USB → 同网段局域网 → 信箱自动换源，HTTP 源会试短名单端口，不用重启。

## 怎么开

Mac 预览：

```sh
./scripts/q10-monitor.sh --local
```

推到手机并用 USB SSH 打一屏（本机证据）：

```sh
./scripts/q10-monitor.sh
```

Term49 里：

```sh
/accounts/1000/shared/misc/q10mon
. /accounts/1000/shared/misc/q10-autostart.sh   # 一次：以后打开 Term49 就进监视器
```

主屏请把 **`Z`** 设成打开 Term49（不要用 `1`，出厂是语音信箱）。见 `docs/LAUNCH.md`。

口径测试（Mac）：

```sh
python3 -m unittest ai-terminal/test_q10_monitor.py
```
