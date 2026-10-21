# Sources

记录可核验来源。下载后补 SHA256 与本机时间。不从随机网盘执行二进制。

## 2026-09-07 已交叉核对

| 对象 | 来源 | 版本 / 标识 | 备注 |
|---|---|---|---|
| BerryCore latest | https://api.github.com/repos/sw7ft/BerryCore/releases/latest | **v0.90.1**（2026-09-02） | Prompt 里的 v0.87.2 过期。仓库首页 snippet 也曾写 0.87.2，以 releases API 为准 |
| BerryCore zip | https://github.com/sw7ft/BerryCore/releases/download/v0.90.1/berrycore.zip | GitHub digest `sha256:170dd86b3ef12485540fa0d79ef19ef186442dc91201db82782fb8d7bbcfaa6a` | 315029377 bytes。**2026-09-07 已下并装**（zip 不进 Git） |
| BerryCore install.sh | https://github.com/sw7ft/BerryCore/releases/download/v0.90.1/install.sh | GitHub digest `sha256:452d91947da6cd8e178772dc62f50d9f07670f5e930f73389473cb02a16d8eba` | 12831 bytes。**2026-09-07 已下并跑** |
| Term49 latest | https://github.com/BerryFarm/Term49/releases/download/0.4.1.7/Term49.bar | **0.4.1.7**（2021-04-01） | size 3497186，SHA256 `48156c7b09edee42dc028484f862a048c9601c5859a407c3d5ba27a2e9913022`。生产签名（Development-Mode false）。**2026-09-07 已安装**，`listInstalledApps` 可见 `com.example.Term49`，`result::success`，已 `-launchApp` |
| Momentics IDE Mac | https://archive.org/download/native-SDK-for-blackberry10/Momentics%20IDE/momentics-2.1.2-201503050937.macosx.x86_64.dmg | 2.1.2-201503050937 | 2026-09-07 已下。size 407625099，MD5/SHA1 与 IA 一致，SHA256 `3c801d2f26cb8452331507325503d635518c0375e35e392b165d613c5b52f8bb`。IDE 本身不含 NDK host 目录；CLI 在 `plugins/com.qnx.tools.bbt.clt_2.0.0.v201412090104`：`BarDeploy.jar` 1.5.0、`Connect.jar` 1.2.0 |
| Win32 NDK tools | https://archive.org/download/bbdevtools/bbndk.win32.tools.10.3.1.12.zip | 10.3.1.12 | 2026-09-15 Windows 已下并校验。size 304910772，SHA256 `c10a1bf0be7d0f5fce58ab6c6b8d9f09819185bcd58d13b78fce8399f37dd237`。Mac 不执行其中的 exe |
| Win32 NDK libraries | https://archive.org/download/bbdevtools/bbndk.win32.libraries.10.3.1.995.zip | 10.3.1.995 | 2026-09-15 Windows 已下并校验。size 1607600440，SHA256 `0b2fd17e62eee6890ca0d470487bc2467ec97432538d04a7a1a299683978a33e` |
| Win32 NDK qconfigmk | https://archive.org/download/bbdevtools/bbndk.win32.qconfigmk.10.3.1.995.zip | 10.3.1.995 | 2026-09-15 Windows 已下并校验。size 5492，SHA256 `97cf4b34af5af9b34365c33cdadcc08b6af20a34a7603f44fef4bd1d9384fe7d` |
| BB10 官方服务 EOL | https://www.blackberry.com/en/secure-communications/support/end-of-life | 2022-01-04 | Link / 云端 / 电话短信不可依赖。只要本地 USB 工具 |

## Host tools 冲突

- **A.** Cordova / 官方旧文档：Mac 路径 `/Applications/Momentics.app` 或 `/Applications/bbndk/host_*/darwin/x86/usr/bin/`，`source bbndk-env_10_3_1_995.sh`。
- **B.** 2018 离线教程与 archive.org `bbdevtools`：公开列出的是 **win32** `bbndk.win32.tools.10.3.1.12.zip`，不是 `bbndk.macosx.tools.*`。
- **C.** Wayback CDX 对 `downloads.blackberry.com/.../*macosx*` 今日查询返回空数组。
- **本机实测**：IA 上的 Momentics 2.1.2 Mac DMG 校验通过后，CLI 在 IDE 插件 `com.qnx.tools.bbt.clt` 里，不是 `host_10_3_1_12/darwin/x86/usr/bin`。已抽到 `tools/bb10/`，用 Java 17 + 允许 TLSv1 的 `java.security.override` 包装。完整 GUI 未安装。

## 协议与 SSH（文档，待工具 help 复核）

| 说法 | 来源 |
|---|---|
| `blackberry-deploy -listInstalledApps -device <ip> -password <pw>` | peterhansen.ca、CrackBerry、Unity BB10 FAQ |
| `blackberry-connect <ip> -password <pw> -sshPublicKey <file.pub>` | Qt Wiki、PocketMagic、onetwentyseven001 |
| 公钥至少 RSA 4096；私钥留在 host；用户 `devuser` | 上述 + gist diorahman/4334311 的更正 |
| connect 连的是 `:4455` | onetwentyseven001 实机日志 |
| connect 进程必须保持 | 官方工具提示原文被多篇笔记引用 |

本机 `BarDeploy.jar` / `Connect.jar` help（2014 BlackBerry Limited，Java 17 跑通）：

- deploy 1.5.0：`-listInstalledApps <device>`，`-listDeviceInfo <device>`，`<device>` = `[-device] <host> [-password <password>]`
- connect 1.2.0：`<target-host> -password <device-password> -sshPublicKey <ssh-public-key>`；默认公钥路径会印出本机 `$HOME/.ssh/id_rsa.pub`，本实验室改用专用 `~/.ssh/q10-usb`

2026-09-07 无密码探测回报：`Device is not in the Development Mode` / `Development mode is not enabled on the device.`  
开 Developer Mode 并给密码后：`listDeviceInfo` / `listInstalledApps` 成功；`connect` 带注释公钥失败（`Invalid contents after ssh key`），剥注释后 `Successfully connected`。  
本机 OpenSSH 10.3 对 `OpenSSH_6.2 QNX_Secure_Shell-20130711`：协商 `ecdh-sha2-nistp256` + GCM 会在 `KEX_ECDH_REPLY` 被对端断开。强制 `diffie-hellman-group14-sha1` + `aes128-ctr` + `ssh-rsa` 后 `uname` 成功。macOS `/etc/ssh/crypto.conf` 会盖掉 `Host` 里的 KEX，脚本用 `-F /dev/null`。

## 驱动

- **Mac 2026-09-07 实测**：无需 BlackBerry Desktop / Link。系统已登记 `Hardware Port: BlackBerry` → `en13`。
- **Windows（备用）**：社区仍用 BlackBerry Link 里的 USB 驱动 / Device Manager，只为通信，不依赖已关云端。未在本机验证。

## 社区索引（第二优先）

- https://github.com/sw7ft/BerryCore
- https://berrystore.sw7ft.com/
- https://github.com/BerryFarm/Term49
- https://www.gridbook.org/pb-app-mgr/ （PlayBook / BB10 App Manager，浏览器侧，不作默认工具链）
- CrackBerry 历史帖只作补充

## 明确不采用的下载

- 教程里写死的 BerryCore v0.6 / v0.72
- 随机网盘 Autoloader / pre-rooted ROM
- 未校验哈希的 NDK 可执行文件

## 2026-09-15 Cascades 主界面

已采纳 `cascades/`（`com.q10lab.console`）。C2：Windows 上 IA win32 NDK 已校验并解到 `C:\q10-lab\ndk\bbndk`。`qcc -V` 列出 4.6.3/4.8.3 armv7/x86；`qmake` 见 Qt 4.8.6；`qcc -V4.8.3,gcc_ntoarmv7le` 编出 ELF32 ARM。C3：未签名 `-devMode` `downloads/console-0.0.1.bar`。C4：未签名 `downloads/console-0.0.2.bar`（SHA256 `f8e3651546f85dd5ae61a869362daf61f3de19cee510bfe9f0ff4d4b916dafce`）。未批准 C7，真机不 `-installApp`。正本 `docs/plan/2026-09-15-cascades-gates.md`。

C7 选 **B**（炮灰机）。G0 3216 官方 7z 期望哈希见 `checksums/q10-10.3.3.3216-autoloader.md`。2026-09-15：`lunarproject.org` 已停；现活目录是 MEGA `ERomDKaT`。**7z 尚未本机校验。** 不要用 IA 10.3.3.498。
