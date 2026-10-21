# Q10 Console（Cascades）

本目录是 Q10 Console 的 Cascades 工程。C2 编译在 Windows win32 NDK 上已经跑通；C4 未签名 BAR 在 `downloads/console-0.0.2.bar`，**未装真机**。C7 选 B：这台 SQN100-3 不装。

方向与闸门：[docs/plan/2026-09-15-cascades-octoooo-surface-plan.md](../docs/plan/2026-09-15-cascades-octoooo-surface-plan.md)。  
两道闸怎么走：[docs/plan/2026-09-15-cascades-gates.md](../docs/plan/2026-09-15-cascades-gates.md)。  
本仓预览（不接 Octoooo）：[preview/](preview/)。

## 现在不要期望

`tools/bb10/` 仍只有 Mac 侧 deploy / connect。`qcc` / `qmake` / packager 在 Windows `C:\q10-lab\ndk\bbndk`。库存机装不了未签名 BAR。

## 包

| 项 | 值 |
|---|---|
| id | `com.q10lab.console` |
| 显示名 | Q10 Console |
| 权限 | `access_internet` `access_shared` `record_audio` `post_notification` `run_when_backgrounded` |

不申请相机、电话、PIM、`_sys_run_headless`。Headless 守护若以后要，另开条目。

## Windows 上 `qcc -V` 之后

1. 校验 win32 NDK 哈希并记入 `docs/SOURCES.md` / `checksums/`。
2. 在 Windows 编未签名 / `-devMode` BAR，拷回 Mac `downloads/`。
3. C4 已补三页 + 轮询 `projection.json`（默认 `http://169.254.0.2:8786/projection.json`，失败用 `assets/projection.json`）。键：`Q` 限额，`2`/`E` 任务，`3`/`R` 待处理，`t` 刷新。不抢 `1`/`W`。
4. 未批准 C7 时，真机不 `-installApp`。炮灰机退路包见 `docs/plan/2026-09-15-g0-autoloader-3216.md`。

数据：先读本仓 `preview/` 的 `projection.json`（夹具或 Aindle）。Octoooo 放到最后再换上游。密钥只在 `local-config/` 或设备 `shared/misc`，640，不进 Git。
