# console-0.0.2.bar

- 构建：2026-09-15 Windows win32 NDK + Java 17 `blackberry-nativepackager` `-devMode`
- 包名：`com.q10lab.console` 0.0.2
- 实测 size: 25684
- 实测 SHA256: `f8e3651546f85dd5ae61a869362daf61f3de19cee510bfe9f0ff4d4b916dafce`
- 内含：`native/console.so`（ELF32 ARM，36843）+ `native/assets/main.qml` + `native/assets/projection.json` + `native/icon.png`
- 存放：Windows `C:\q10-lab\ndk\console-0.0.2.bar`；Mac `downloads/console-0.0.2.bar`（gitignore）
- C4：三页键位 + 轮询 `q10.console.projection.v1`，失败回退夹具
- **未签名。库存 Q10 不能装。未对真机 `-installApp`。**
