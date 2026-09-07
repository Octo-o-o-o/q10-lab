# AI Terminal 实现选项

Phase 1 已完成。实现选型仍等 Term49 能在本机跑通、BerryCore 是否安装之后再定，避免先入为主。

已冻结的产品约束（与圆屏 AI Monitor 对齐）：

- Q10 是 Interface，不是 Intelligence。
- 数据源是 Mac 上的 `aindle.snapshot.v2`（默认 `http://<Mac-USB-or-LAN>:8790/snapshot.json`），不是另一套协议。
- 首页按 Agent / Task / Run / Usage / Machine 状态面板，不做小 ChatGPT。
- 键盘快捷键与全局 PTT 必须以 BB10/QNX 实机 API 验证，不假设能 hook。
- BB10 Browser 的 TLS 不能当默认运输层。
