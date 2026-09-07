# Q10 键盘 AI Monitor

Q10 是 **Interface**，不是 Intelligence。读圆屏同一份 `http://<Mac-USB>:8790/snapshot.json`（`aindle.snapshot.v2`）。不做小 ChatGPT，不在 QNX 上跑 LLM / Whisper。

## 页面对齐圆屏

| 键 | 页 | 圆屏对应 |
|---|---|---|
| `1` | 状态 | 表盘信息：新鲜度、主机、ASK n |
| `2` | 限额 | 窗口 **已用 %**；`spend` 不混进限额 |
| `3` | 任务 | 过期主机标「旧记录」 |
| `4` | 待处理 | 仅 `wait + direct + needs_input`；提示在电脑处理 |

`j`/`k` 翻条，`r` 刷新（约 10 秒也可自动），`x` 退出。失败保留上一屏并标离线，**不会**偷偷改 DEMO。`--demo` 必须显式。

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
