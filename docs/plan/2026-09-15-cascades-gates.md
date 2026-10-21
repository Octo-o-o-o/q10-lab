# Cascades 两道闸：怎么推进（不碰 Octoooo）

日期：2026-09-15  
范围：只推进 **编译** 与 **安装**。Octoooo 仓库另有在途工作，合同对接放到最后。本仓先用 Aindle 夹具 / 8787 做界面预览。

## 闸 1：编译 — 不要在这台 Mac 上找 `qcc`

### 今天核对过的事实

| 证据 | 结果 |
|---|---|
| 本机 | Darwin **arm64** 27.0。Catalina 之后 macOS **不能跑 32 位** |
| 已下 Momentics 2.1.2 Mac DMG | 只读挂载后是 641MB `Momentics.app`，主程序 `qde` 为 **x86_64**。**没有** `qcc` / `qmake` / `bbndk-env` |
| 历史完整安装 | `qcc` 在 `/Applications/Momentics.app/host_10_3_1_12/darwin/x86/usr/bin/`，路径是 **darwin/x86（32 位 Intel）**。即便把 NDK 装进这台机，也很可能直接无法执行 |
| IA `bbdevtools` | 只有 **win32**：`bbndk.win32.tools.10.3.1.12.zip`（305MB）+ `bbndk.win32.libraries.10.3.1.995.zip`（1.61GB）。无 `bbndk.macosx.*` / `bbndk.linux.*` |
| IA `native-SDK-for-blackberry10` | 各平台 **Momentics IDE**（含已有 macosx DMG、linux `.run`）。体积与 Mac DMG 同级，按本次挂载结果应视为 IDE，不是 NDK 库 |
| 官方签名 / 下载站 | EOL；macosx NDK 直链空 |

结论：**C2 的编译宿主改成 Windows x64（WoW64 跑 win32 NDK）。这台 Mac 只负责 USB `blackberry-deploy`。** 不再把「找到 darwin NDK」当本机必过项。

### 怎么推进（按顺序）

1. **准备一台 Windows 10/11 x64**。2026-09-15 从这台 Mac 免密 SSH 已通（AMD64 + WoW64，有 curl / git / python / scp）。**编译继续在 Mac 会话里远程操作 Windows**，不必为了 C2 去那边装 Cursor。USB 仍留 Mac，不要把 Q10 插进 WSL，也不要为了编译把 Q10 插 Windows。
2. 在 Windows 下校验后下载（哈希记入 `docs/SOURCES.md` 再解压）：
   - https://archive.org/download/bbdevtools/bbndk.win32.tools.10.3.1.12.zip
   - https://archive.org/download/bbdevtools/bbndk.win32.libraries.10.3.1.995.zip
3. **2026-09-15 已做**：三份 zip 与 IA `files.xml` 的 size/MD5/SHA1 一致，解到 `C:\q10-lab\ndk\bbndk`。`qcc -V` 列出 4.6.3/4.8.3；`qmake` 见 Qt 4.8.6；ARM hello 为 ELF32。C3 未签名 `downloads/console-0.0.1.bar`。C4 未签名 `downloads/console-0.0.2.bar`（三页 + 轮询 + 夹具）。
4. Mac 上只 `./scripts/q10-deploy.sh`——**在 C7 批准之前不要对真机 `-installApp`**。官方 zip 里没有 `bbndk-env_*.bat`，用 `scripts/windows-ndk-env.cmd`。Java 21 默认跑不了 packager，要用本机 **Java 17** + `java.xml` add-opens。QNX `make` 的 `rm -f` / `ln` 在这台 Windows 上会挂，编 BAR 用 `scripts/windows-ndk-link-console.ps1`。

备援（未核到包，不排期）：Linux x86_64 Momentics `.run` 若安装后同样拉不到 libraries，不要赌。旧 Mac（≤10.14）跑 32 位 `qcc` 理论可行，这台 arm64 不是那台机器。

未校验哈希的 NDK 不执行。

## 闸 2：安装 — 官方 token 已死，库存机装不了未签名包

### 今天核对过的事实

| 路 | 状态 |
|---|---|
| 官方 debug token / 签名钥匙 | 社区 2025-10 称生成器与 seed 服务器已销毁。本机设备信息：`no debug token found` |
| 生产签名 | 一套未建；Term49 能装是因为 **2021 年已签好的 BAR** |
| 库存机未签名 BAR | 拒（社区 Chromium 881：缺 RDK/AUTHOR） |
| 未签名能装 | 社区 2025–2026 路线（bb10.root.sx / AutoRoot）。要改系统映像，**等于 C7** |

Developer Mode **不能**代替 debug token。它只打开 USB 网卡和 `blackberry-connect`。

### 怎么推进

在 Windows 能编出 BAR 之前，安装闸不必开。BAR 有了之后你用**一句话**选：

**A. 这台 SQN100-3 继续库存**  
只保留未签名制品，真机不装 Console。日常仍是 `Z` → Term49。预览走本仓 720 页 + 出厂浏览器。

**B. 炮灰 Q10 走社区未签名/root 包**  
另机、另批、先 G0 备份。这台收藏机不动。Console 的录音/通知在炮灰上验收。

**C. 点名「刷这台 SQN100-3」**  
才进入 Autoloader / AutoRoot 评估。默认不选。

**2026-09-15 已选 B。** 这台 SQN100-3 继续库存。G0 清单：`docs/plan/2026-09-15-g0-autoloader-3216.md`。7z 哈希已交叉，包还没下到本机。没有炮灰机之前不跑 Autoloader。

## 本仓先做完（Octoooo 最后）

| 做 | 不做 |
|---|---|
| `cascades/preview/`：720 页 + `q10.console.projection.v1`，数据来自夹具或 Aindle 8787 | 不改 `~/WorkSpace/Octoooo` |
| 两道闸写进本文件与选型文档 | 不改 `~/WorkSpace/Octoooo` |
| Term49 监视器保持对照 | 不 `-installApp` 未签名 BAR |

以后接 Octoooo（**对方仓库空闲后再做，本次不改那边**）：

1. 对方出同一份 `q10.console.projection.v1`，或本仓加一层 adapter。
2. 预览 `--hub` 换成 Octoooo URL；Cascades 只换 base URL。
3. 对齐 r6：只读、未知不归零、过期标旧、无读态操作。USB/LAN 用 HTTP，不把 Tab5 WebSocket 当第一版。
4. 监视器可继续并行读 Aindle 8787。Console 权威源再切到 Octoooo。
