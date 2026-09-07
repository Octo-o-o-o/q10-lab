# Q10 Device Lab

默认中文。唯一目标设备是这台真实 **BlackBerry Q10 SQN100-3**。不要把 ESP32 圆屏仓库的端口、PID、固件或协议套过来。

- 第一原则：未获用户明确批准，禁止 wipe / Autoloader / 升降级 / root / 改 NVRAM / 改 radio / 改 bootloader / 删除系统应用。
- Host 当前是 **macOS**。USB-facing 操作留在 macOS 本机，不要把 USB 放进 WSL。Windows 只在 Mac 工具链走不通时再开。
- 密码、IMEI、token 不进 Git、不进脚本、不进日志。运行时 prompt 或 `local-config/`。
- 完成必须有证据：USB 枚举、ping、工具输出、SSH 回显、用户肉眼，是不同证据。
- 网上 2013–2020 教程与 2025–2026 社区资料会冲突。冲突时并列来源，以这台真机为准。
- 第一阶段目标是可重复的 USB / `blackberry-deploy` / `blackberry-connect` / SSH，不是尽快装软件。
- Phase 1 已完成。用户已授权先装 Term49；BerryCore / AI Terminal 仍须另一次点头。未批准禁止 wipe / Autoloader / 升降级。
