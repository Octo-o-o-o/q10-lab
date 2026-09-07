# Q10 一键启动（真机审查）

结论先说：**主屏按一个字母可以打开 Term49；默认不能按 `1`。**  
`1` / `W` 出厂是语音信箱。没有侧边 Convenience Key（那是 KEYone/KEY2）。  
SSH `devuser` **写不进** Term49 沙箱 `$HOME`，所以我不能在你不打开一次 Term49 的情况下，把监视器设成开机即跑。

## 最快路径（推荐 `Z`）

官方：[Create or change a keyboard shortcut](https://blackberry-q10.berrydoc.net/en/settings/blackberry-keyboard-and-typing/create-or-change-a-keyboard-shortcut/)

1. 主屏按一下还没有快捷键的字母（**`Z` 出厂表里没有**）。系统会提示创建。
2. 选 **App Launch Shortcut** → **Term49**。
3. 以后在主屏或 Hub 按 `Z` 就打开 Term49。

若要从设置里改：下拉 → Settings → Shortcuts and Speed Dial → 长按字母。

出厂占用（不要当空键）：`A` 联系人，`B` 浏览器，`C`/`9` 写邮件，`D`/`5` Remember，`H` Help，`K` 锁屏，`L` 日历，`M` Hub，`N` BBM，`O` 设置，`P` 电话，`Q` 情景，`R`/`3` 时钟，`T` 任务，`U` 计算器，`W`/`1` 语音信箱。

## 打开 Term49 之后自动进监视器

沙箱 HOME 只有 Term49 自己写得动。在 Term49 里跑一次：

```sh
. /accounts/1000/shared/misc/q10-autostart.sh
```

之后再按 `Z`：Term49 开 → 监视器。`x` 退回 shell。`Q10_NOMON=1` 可跳过。

## Mac 上能替你按的

```sh
./scripts/q10-launch.sh     # deploy -launchApp Term49（手机亮屏到终端）
./scripts/q10-monitor.sh    # USB SSH 打一屏，不是手机 UI
```

`-launchApp` 不能往 Term49 里打字。

## 启动依赖

| 项 | 手机监视器 | Mac SSH 监视器 |
|---|---|---|
| USB + Developer Mode | 要（猜 Mac `169.254.*.2:8790`） | 要 |
| Mac 8790 听在 `*` 或 USB 地址 | 要 | 要 |
| `blackberry-connect` / SSH | 不要 | 要 |
| 主屏 `Z` → Term49 | 要（一次设置） | 不要 |

8790 只听 `127.0.0.1` 时手机是摸不到的。本机刚才是 `*:8790`。

## 做不到 / 故意不做

- 从 USB 改系统快捷键表（没有公开 API，也不 root）
- 把 `1` 当空键（出厂语音信箱）
- BerryCore `settings homescreen-on`（只往 `.profile` 塞 pin pack，不是键盘快捷键）
- 独立 sshd、Berry Browser、设备侧 LLM / PTT
