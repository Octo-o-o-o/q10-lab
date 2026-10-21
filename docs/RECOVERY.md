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

真机现 OS 是 **10.3.3.3216**（`docs/Q10_BASELINE.md` 设备读回）。口述 10.3.3.2137 已被否定。  
IA `blackberry10-autoloaders` 里和 SQN100-3 对得上的是 **Dev Alpha C / 10.3.3.498**，不能当这台量产机的恢复包。量产 3216 的官方 7z 清单与期望哈希在 [G0](plan/2026-09-15-g0-autoloader-3216.md)。**7z 尚未本机校验**，不能当已备好的退路。选项 B：这份包只给以后的炮灰机，不刷这台收藏 SQN100-3。

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
| Root / AutoRoot / 改 bootloader / NVRAM / radio | 高风险；回官方靠再刷，不是一键撤销 | 禁止 |

## Root 之后能不能回官方 ROM

社区常规：**可以**，靠再刷一份**匹配的官方 Autoloader**（OS + radio）整包覆盖，回到库存签名系统。未签名 BAR 会再次被拒。这不是设置里的「撤销 root」。

做不到 / 不要当成退路的：

- **Security Wipe / 恢复出厂**去不掉 PathTrust / 签名补丁，只清用户数据。
- 本实验室**没有**已校验的官方 Autoloader，也**从未**在这台机演练刷入 + radio + 回官方。
- 刷回哪一版，取决于你手里那份包。没有校验过的 3216 包，就不能保证回到现在的 **10.3.3.3216**。
- 官方 Autoloader 会重写用户分区，Term49 / BerryCore / 监视器都没，要再走 bring-up。BB10 云备份已 EOL。
- AutoRoot v3（[bb10.root.sx，2026-09-10](https://bb10.root.sx/blog/pre-rooted-autoloaders-v3)）写明：必须先用**对应版本的官方库存固件**做输入；主要在 **10.3.3.3216** 测过；产出是 `_root_v3.exe`（用户文件系统）再刷 `_radio.exe`。没有原版包，既做不成可复现的 root，也没有对称的回退。
- 不要用带 `mod_nvram` / 解锁 / 降级的预打 root 包。不改 NVRAM。
- Autoloader 要 **Windows 本机 USB**。社区称虚拟机常不行。刷机窗口里 Q10 不插 Mac。

因此：想保收藏机可回官方，**先备好并校验「这台 SQN100-3 + 目标版本」的完整官方包**，再谈 root。现在没有这份包，root 的退路只是口头存在。

## Bootloader / 恢复键

公开笔记里 BB10 砖机常见现象是黑屏 + LED 红闪，Autoloader 等 `Connecting to Bootrom`。不同机型按键组合不统一，**未在这台 Q10 上试**。需要时再单独查 SQN100-3，不猜测。

## Windows 驱动恢复路径（备用）

若以后必须用 Windows：BlackBerry Link / Device Manager 驱动只为 USB 通信，不依赖已关云端。Mac 当前已通，不作为前置。

## 若将来必须破坏性操作

停下来写清：为什么、会改什么、风险、怎么恢复、是否丢掉 BB10 activation/setup、有无更安全替代。等用户一句明确批准。
