# Q10 键盘 AI Monitor

Q10 是 **Interface**，不是 Intelligence。读 Aindle Hub 同一份 `aindle.snapshot.v2`（默认 `http://<Mac-USB>:8787/snapshot.json`，端口跟 `AINDLE_PORT`）。不做小 ChatGPT，不在 QNX 上跑 LLM / Whisper。端口改了会探测 last-good 和 `Q10_HUB_PORTS`（8787 再 8790），不要在本仓库另起 Hub。

## 页面对齐圆屏

| 键 | 不按 Alt | 页 | 圆屏对应 |
|---|---|---|---|
| `1` | `W` | 限额 | 窗口 **已用 %**；`spend` 不混进限额 |
| `2` | `E` | 任务 | 默认进行中；`a/i/d/u` 筛选；一行一条，标题居左，`项目·Agent` 右齐 |
| `3` | `R` | 待处理 | 仅 `wait + direct + needs_input`；提示在电脑处理 |
| `4` | `S` | 待处理 | 现三页，与 `3`/`R` 相同 |

任务页默认只看进行中，不在每行写状态。底栏 `j下 k上` 右侧：`a进行 i空闲 d完成 u全部`（当前筛选用大写）。任务一行一条：标题居左，项目与 Agent 缩写成一个右齐列（如 `Octo·CLD`）；标题与项目同名时该项目不重复出现。一行放不下就按词界截断加 `…`，不折第二行；页内有「等你」任务时行首留 `●` 槽位，没有则槽位让给标题。限额页底部不再写口径说明。`t` 刷新（不用 `R`），`x` 退出。有待处理时启动落在待处理页；未处理用 `█` 和 `●待处理` 高亮，别处处理完留「已处理」。

排版对齐 Kindle 那一屏：页眉左页名、右链路·主机（`USB · Mini` 的 Mini 是 Mac mini），下面一条 `─` 实线（推送的等宽字体已把 `─` 字形横向拉满格，不断线）；限额条是 `█` 满格块加 `·` 空槽，同一工具多窗口只写一次名字，百分比右齐。任务行不写状态列；超长标题优先在空格、连字符或中英文边界截断，截不断再硬切，`项目·Agent` 始终贴在行尾右齐。屏幕装不下时按行高分页，`j/k` 翻页。`--lang en` 时结构字符退回纯 ASCII（`-` `.` `#` `*`）。

默认界面是中文。任务标题本身也可能是中文。Term49 按字母 `X` 的宽度画格子、逐字形贴格（不支持双宽字符），系统黑体汉字更宽会叠在一起。推送时会做成等宽 `q10-cjk-mono.ttf`：所有字形统一成汉字宽的格子，拉丁/数字/标点的字形横向拉宽（约 1.6×、上限 90% 格宽）并在格内居中，否则英文字距会显得特别大。手机里按 `x` 只退监视器，**不会**换字体。信箱 token 须 640。

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
