# r6 Q10 / Term49 profile

继续使用既有 `ai-terminal/q10_monitor.py`，不新建 BB10 原生客户端。新增输入格式 `octoooo.weak.v1` 来自受控 Aindle 输出服务，已经在 Core 完成对象授权和最小投影，不能将原始账号/任务正文直接映射成公共屏内容。

设置 `Q10_OCTOOOO_BINDING_FILE` 为本地私有 JSON 路径，包含 `url`、`device_id`、`token`。url 必须是准确 HTTPS `/projection.json`，与 `--url` 参数完全相同；文件应为 0600。凭据通过 curl stdin config 进入 HTTP 请求头，不出现在进程参数、URL 或终端画面。不要用 owner/source token。

显式离线软件验证：`python3 ai-terminal/q10_monitor.py --file <合成投影.json> --all`。记录由共同 fixture 生成，不能因文件格式正确而声称连接真实 Core。完整回归：`python3 -m unittest ai-terminal/test_q10_monitor.py`。q10 既有按键/页码逻辑保留；超过一页的事项可翻页，idle 来源保留为 idle，未知用量不为零，过期/撤销清空本次投影且不写关注历史缓存。静态旧画面的物理残留仍须人工/真机验收。

C2 指定真实 Q10、Term49/Python/curl 版本、CA 与准确 HTTPS 入口后，先备份旧脚本和启动配置，再拷入候选脚本与独立身份。恢复时退出本次进程、撤销新身份、恢复旧脚本与入口，不清除个人历史或其他应用。未在 QNX/实际键盘上运行本候选，不把 macOS Python 测试冒充真机能力。
