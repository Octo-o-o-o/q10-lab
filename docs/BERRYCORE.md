# BerryCore v0.90.1（已装）

装于 2026-09-07。`install.sh -y` 由 Mac 经 USB SSH（`devuser`）在设备上跑完，**没有 root**，**没有**装 Berry Browser BAR。

## 装在哪

| 路径 | 作用 |
|---|---|
| `/accounts/1000/shared/misc/berrycore` | userland + `qpkg` |
| `/accounts/1000/shared/misc/clitools` | 指向上面的符号链接 |
| `/accounts/1000/shared/misc/bcllm` | 随包装的本机 AI，**未下载模型、未启用** |
| `/accounts/1000/shared/misc/berrybridge-agent` | 随包装的 agent，post-install 有一处 `_cat` 失败，未当可用 |
| `/accounts/devuser/.profile` | SSH 新会话会 `source` BerryCore |

## 怎么用

Mac（已通）：

```sh
./scripts/q10-shell.sh
# 进来后已有 qpkg / curl / git / vim
```

Term49（个人用户，`.profile` 写不到它的 HOME）打一行：

```sh
. /accounts/1000/shared/misc/use-berrycore.sh
```

键盘监视器（不依赖 BerryCore，走库存 `python3.2`）：

```sh
/accounts/1000/shared/misc/q10mon
```

## 已核验

- 98 个 zip 包装完；`qpkg` / `curl` 8.12.1 / `git` / `vim` 在 PATH
- `curl http://169.254.0.2:8790/snapshot.json` → `aindle.snapshot.v2`
- `/` 用到约 **3.8G / 30%**（装前约 2.8G）

## 已知缺口

- `packages/gcc.zip` 只有 134 字节，是坏包/占位，不是编译器；没有 `gcc`/`cc`
- 登录横幅会打一行 `404: Not Found`（目录网拉失败），不影响命令
- `chmod bin/python` 权限不够，忽略
- 不装 Chromium BAR（要 root）
