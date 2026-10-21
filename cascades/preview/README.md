# Q10 Console 预览（本仓，不接 Octoooo）

720×720 只读页 + `q10.console.projection.v1`。数据来自 Aindle 夹具或本机 `8787`。以后换 Octoooo 只改 `/projection.json` 的上游。

不要占用 `8787` / `8790`，不要另起 Hub。

## 验收

```sh
cd cascades/preview && python3 -m unittest test_project.py
python3 cascades/preview/project.py > ../assets/projection.json
./scripts/q10-console-preview.sh          # http://127.0.0.1:8786/
./scripts/q10-console-preview.sh --hub    # 读现有 Aindle
./scripts/q10-console-preview.sh --lan    # 0.0.0.0，出厂浏览器可开 http://169.254.0.2:8786/
```

Mac 浏览器：`Q` 限额，`2`/`E` 任务，`3`/`R` 待处理，`t` 刷新。不把 `1`/`W` 当产品键（出厂语音信箱）。

真机出厂 `B` 打开 USB 地址前，预览须 `--lan`，Hub 仍是既有 8787。
