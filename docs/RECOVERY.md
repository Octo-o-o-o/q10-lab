# Recovery（只研究，不执行）

**禁止在本阶段运行 Autoloader、Security Wipe、Factory Reset。**

## 硬件族

用户设备：Q10 **SQN100-3**。

社区对 family 的说法不完全一致：

| | 说法 | 来源 |
|---|---|---|
| A | 所有 `SQN100-x` 可用同一套 Q10 Autoloader；Q5 / Q10 / P9983 也可共用 | Hovatek、CrackBerry Autoloader 指南 |
| B | 下载站按 SQN100-1…5 分别列出 10.3.1 / 10.3.2 / 10.3.3 包 | 2017 tutorial-repair 一类汇编页 |

未执行、未下载任何 Autoloader。真要恢复时必须同时核对：**硬件族 + 当前 OS 大版本 + 是否开发者残缺包**。有帖记录 SQN100-3 用错/残缺 10.3.1 Autoloader 后红灯双闪。

口述当前 OS 是 **10.3.3.2137**。社区常见公开包停在 10.3.3.498 一类编号，**不能**假设 2137 有对应公开 Autoloader，也不能假设降到 498 是安全的。

## Autoloader 是什么

Windows 可执行的离线写包：Bootrom 通信 + OS + radio。官方/社区都当“整机重刷”。Mac 上传统做法是 Boot Camp / 另一台 Windows。

会改变：系统分区、常含 radio、回到初始设置。  
风险：变砖、丢失 activation/setup、丢失用户数据。  
恢复：只有再刷或事先备份；BB10 云服务已 EOL。

## 哪些会 wipe / 哪些不会

| 操作 | 会否丢掉用户数据 / 初始激活 | 本阶段 |
|---|---|---|
| 插拔 USB、开关 USB 网络 | 否 | 允许 |
| 开 Developer Mode、设设备密码 | 否（密码由用户自己设） | 允许，需用户点 |
| `blackberry-deploy` 装已签名 BAR | 否 | 允许 |
| `blackberry-connect` / SSH `devuser` | 否 | 允许 |
| 关 USB Mass Storage | 否 | 仅当 deploy 冲突时请用户改 |
| Security Wipe / Factory Reset | **会** | 禁止 |
| Autoloader | **会**，并常回到 setup | 禁止 |
| 降级 10.3 → 10.2 | 社区称 10.3 后不可安全降 | 禁止 |
| Root / 改 bootloader / NVRAM / radio | 高风险，可能不可逆 | 禁止 |

## Bootloader / 恢复键

公开笔记里 BB10 砖机常见现象是黑屏 + LED 红闪，Autoloader 等 `Connecting to Bootrom`。不同机型按键组合不统一，**未在这台 Q10 上试**。需要时再单独查 SQN100-3，不猜测。

## Windows 驱动恢复路径（备用）

若以后必须用 Windows：BlackBerry Link / Device Manager 驱动只为 USB 通信，不依赖已关云端。Mac 当前已通，不作为前置。

## 若将来必须破坏性操作

停下来写清：为什么、会改什么、风险、怎么恢复、是否丢掉 BB10 activation/setup、有无更安全替代。等用户一句明确批准。
