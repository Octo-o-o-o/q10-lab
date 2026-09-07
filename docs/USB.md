# BB10 USB 工作原理（以这台 Q10 实测为准）

BlackBerry 10 **不是 Android**。不要用 ADB。

## 这条链

```
Q10 (BB10 10.3.3.3216 / QNX)
  │  USB 2.0 High Speed
  │  VID 0x0FCA  PID 0x8017  Product "BlackBerry"
  ▼
macOS 原生 CDC/NCM 网卡
  Hardware Port: BlackBerry
  ▼
USB IPv4（每次插拔都可能换 /30，不要写死）
  未开 Dev Mode（第一次）：Host 169.254.57.114/30  ↔  设备 169.254.57.113
  已开 Dev Mode：          Host 169.254.0.2        ↔  设备 169.254.0.1
  再次插入未开 Dev Mode：  Host 169.254.134.222/30 ↔  设备 169.254.134.221
  ▼
开放端口
  80 / 443 / 8443   设备 HTTP(S)，TLSv1 + 自签名
  139 / 445         SMB（USB 共享存储）
  4455              QConn（blackberry-connect 目标）
  22                仅当 blackberry-connect 进程活着
  ▼
host tools
  blackberry-deploy  → HTTPS / appInstaller（列信息、列应用、装 BAR）
  blackberry-connect → <当前 USB IP>:4455 + 设备密码 + 无注释 RSA 公钥
  ▼
ssh -F /dev/null -o KexAlgorithms=diffie-hellman-group14-sha1 \
    -o Ciphers=aes128-ctr -o HostKeyAlgorithms=ssh-rsa \
    -i ~/.ssh/q10-usb  devuser@<当前 USB IP>
  对端：OpenSSH_6.2 QNX_Secure_Shell-20130711
  若让 OpenSSH 10.3 选 ecdh-sha2-nistp256 + GCM，设备会在 KEX 断开
```

## 来源冲突

| 说法 | 来源 | 这台机器 |
|---|---|---|
| USB 开发地址固定 `169.254.0.1` | 大量 2013–2017 教程 | **未开 Dev Mode 时 `.1` 丢包**，对端是 `.113`。**打开之后**才变成屏幕上的 `.1` |
| 必须先装 BlackBerry Link / Desktop 驱动 | Windows 社区、DBBT 说明 | **Mac 已原生出现 `Hardware Port: BlackBerry`** |
| Developer Mode 关闭则 4455 connection refused | onetwentyseven001 等笔记 | 4455 **TCP 仍开**；`Connect.jar` 认证阶段才报 `Development mode is not enabled` |
| 关掉 USB Mass Storage 后 App Manager / DBBT 才稳定 | 2022 CrackBerry / DBBT 讨论 | SMB `media` / `removable_SDCARD` **当前开着**。网络和 4455 仍通。先不改手机设置 |
| 公钥文件可直接丢 `id_rsa.pub` | 多数教程 | 带注释会 `Invalid contents after ssh key`，必须剥成 `ssh-rsa <blob>` |

## 各组件关系

- **USB Networking**：系统把手机枚举成以太网卡，给 link-local。没有它，deploy/connect 都没 IP。
- **Developer Mode**：Settings → Security and Privacy → Development Mode。给 QConn / deploy 授权，通常要设备密码。重启或约 10 天后可能关掉。打开后 USB IP 会从 `.113` 跳到 `.1`。
- **QConn `:4455`**：Momentics / `blackberry-connect` 的调试通道。官方 connect 必须保持进程活着，临时 sshd 才在。Cursor 普通前台 shell 结束会杀进程组，所以 connect 用独立 session 拉起。
- **`blackberry-deploy`**：列应用、装/卸已签名 BAR。走 HTTPS（这台 443/8443 都响应 CGI）。
- **`blackberry-connect`**：把 **公钥** 推到设备并维持会话。SSH 用 **私钥**、用户 **`devuser`**。
- **USB Mass Storage / SMB**：方便拷文件，但是另一条通道。社区有“关掉它 deploy 更稳”的经验；这台先保持现状，真出冲突再请用户改设置。

## Mac 上不要做的事

- 不要把 USB 网卡桥进 WSL。
- 访问设备 IP 必须绕过本机 HTTP 代理（`NO_PROXY=*`）。否则 HTTPS 会先 `200 Connection established` 再打歪。
- 设备 HTTPS 是 **TLSv1 + 自签名证书**。Java 17 默认禁用 TLS 1.0 时，`BarDeploy.jar` 报 `peer not authenticated`。包装脚本用 `tools/bb10/java.security.override` 只为这套工具打开 TLSv1。
- 不要假设下一根线、下一次插拔仍是同一个 169.254 地址。以 `./scripts/q10-detect.sh` 为准。
- 8790 是 **Mac 上的 Aindle hub**，不是手机端口。Q10 经 USB 网卡 GET `http://<Mac-USB-IP>:8790/snapshot.json`。Hub 须听在 `*` 或 USB 地址；只听 `127.0.0.1` 时手机摸不到。
- `ps` 里 Java 命令行会露出 `-password`。这是官方工具限制，不要把那段输出贴进仓库。
