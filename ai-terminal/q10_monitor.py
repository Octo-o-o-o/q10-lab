#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Q10 keyboard AI Monitor. Interface, not Intelligence.

Reads the same aindle.snapshot.v2 the ESP32 round screen uses.
Python 3.2.2 (QNX) and modern CPython. No f-strings, no type hints.
Never auto-falls back to DEMO. Fetch failure keeps the last screen and
labels it offline, or prints 不可用 on the first request.
"""
from __future__ import print_function

import argparse
import json
import math
import os
import sys
import time
from datetime import datetime

SNAPSHOT_SCHEMA = "aindle.snapshot.v2"
SOURCE_TIMES_SCHEMA = "octoooo-mini.source-times.v1"
STALE_AFTER_MS = 5 * 60 * 1000
PAGES = ("status", "quota", "tasks", "ask")
PAGE_TITLES = {
    "status": "状态",
    "quota": "限额",
    "tasks": "任务",
    "ask": "待处理",
}
WEEKDAYS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
CONF_LABEL = {
    "live": "新鲜",
    "cached": "缓存",
    "stale": "旧数据",
    "error": "不可用",
    "none": "无数据",
    "unknown": "未知",
}
STATE_LABEL = {
    "active": "进行中",
    "wait": "等待",
    "idle": "空闲",
    "done": "完成",
    "fail": "失败",
}


def utcnow():
    try:
        from datetime import timezone

        return datetime.now(timezone.utc).replace(tzinfo=None)
    except Exception:
        return datetime.utcnow()


def parse_iso(value):
    if not value or not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1]
    elif len(text) > 10 and (text[-6] in "+-") and text[-3] == ":":
        text = text[:-6]
    elif len(text) > 10 and text[-5] in "+-" and text[-4:].isdigit():
        text = text[:-5]
    frac = 0
    if "." in text:
        main, tail = text.split(".", 1)
        digits = ""
        for ch in tail:
            if ch.isdigit():
                digits += ch
            else:
                break
        digits = (digits + "000000")[:6]
        try:
            frac = int(digits)
        except ValueError:
            frac = 0
        text = main
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(text, fmt)
            return dt.replace(microsecond=frac)
        except ValueError:
            continue
    return None


def used_pct(raw):
    if raw is None or raw == "":
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(value):
        return None
    return int(round(min(100.0, max(0.0, value))))


def format_age(ms):
    if ms < 0:
        ms = 0
    sec = ms // 1000
    if sec < 15:
        return "刚刚"
    if sec < 60:
        return "{0}秒前".format(sec)
    minutes = sec // 60
    if minutes < 60:
        return "{0}分钟前".format(minutes)
    hours = minutes // 60
    if hours < 48:
        return "{0}小时前".format(hours)
    return "{0}天前".format(hours // 24)


def format_reset(iso, now):
    dt = parse_iso(iso)
    if dt is None:
        return "—"
    clock = dt.strftime("%H:%M")
    if dt.date() == now.date():
        return clock
    return "{0} {1}".format(WEEKDAYS[dt.weekday()], clock)


def folder_label(project):
    raw = str(project or "").strip()
    if not raw:
        return ""
    try:
        from urllib.parse import unquote

        raw = unquote(raw)
    except Exception:
        pass
    raw = raw.replace("\\", "/").rstrip("/")
    leaf = raw.split("/")[-1] if raw else ""
    return leaf or raw


def is_octoooo(run):
    blob = " ".join(str(run.get(k) or "") for k in ("project", "title", "tool", "detail")).lower()
    return "octoooo" in blob


def overlay_source_times(snapshot, source_times):
    if not isinstance(snapshot, dict):
        return snapshot
    sources = source_times.get("sources") if isinstance(source_times, dict) else None
    if not isinstance(sources, dict) or not sources:
        return snapshot
    if source_times.get("schema") != SOURCE_TIMES_SCHEMA:
        return snapshot
    out = dict(snapshot)
    subs = []
    for raw in out.get("subscriptions") or []:
        if not isinstance(raw, dict):
            subs.append(raw)
            continue
        extra = sources.get(str(raw.get("id") or ""))
        collected = extra.get("collectedAt") if isinstance(extra, dict) else None
        if collected:
            row = dict(raw)
            row["collectedAt"] = collected
            subs.append(row)
        else:
            subs.append(raw)
    out["subscriptions"] = subs
    return out


def _stale_host_ids(snapshot, now):
    stale = set()
    freshness = snapshot.get("freshness") or {}
    for host_id in freshness.get("staleHosts") or []:
        if host_id:
            stale.add(str(host_id))
    for host in snapshot.get("hosts") or []:
        if not isinstance(host, dict):
            continue
        host_id = str(host.get("id") or "")
        if not host_id:
            continue
        if host.get("status") == "stale":
            stale.add(host_id)
        seen = parse_iso(host.get("seenAt"))
        if seen is not None:
            age_ms = int((now - seen).total_seconds() * 1000)
            if age_ms > STALE_AFTER_MS:
                stale.add(host_id)
    return stale


def _host_seen_map(snapshot):
    out = {}
    for host in snapshot.get("hosts") or []:
        if not isinstance(host, dict):
            continue
        host_id = str(host.get("id") or "")
        if not host_id:
            continue
        seen = parse_iso(host.get("seenAt"))
        if seen is not None:
            out[host_id] = seen
    return out


def _last_collected(snapshot, now):
    latest = None
    for host in snapshot.get("hosts") or []:
        if not isinstance(host, dict):
            continue
        seen = parse_iso(host.get("seenAt"))
        if seen is not None and (latest is None or seen > latest):
            latest = seen
    if latest is None:
        return None, 0
    age_ms = max(0, int((now - latest).total_seconds() * 1000))
    return latest, age_ms


def _format_seen_age(seen, now):
    return format_age(max(0, int((now - seen).total_seconds() * 1000)))


def _subscription_host_ids(sub):
    raw = sub.get("hostIds")
    if raw is None or not isinstance(raw, list):
        return None
    return [str(item) for item in raw if str(item).strip()]


def _effective_sub_confidence(sub, stale_ids, known_ids):
    conf = str(sub.get("confidence") or "none")
    if conf in ("error", "none"):
        return conf
    host_ids = _subscription_host_ids(sub)
    if not host_ids:
        return "unknown" if conf == "live" else conf
    live = [h for h in host_ids if h in known_ids and h not in stale_ids]
    stale = [h for h in host_ids if h in stale_ids]
    if stale:
        return "stale"
    if live:
        return conf
    return "unknown" if conf == "live" else conf


def _windows(sub, now):
    out = []
    for raw in sub.get("windows") or []:
        if not isinstance(raw, dict):
            continue
        pct = used_pct(raw.get("pct"))
        key = str(raw.get("key") or "").strip()
        if pct is None or not key:
            continue
        out.append(
            {
                "key": key,
                "used_pct": pct,
                "used_label": "已用 {0}%".format(pct),
                "resets_label": format_reset(raw.get("resetsAt"), now),
            }
        )
    return out


def _quota_age_label(host_ids, conf, seen_map, stale_ids, known_ids, now, collected_at):
    if conf in ("error", "none"):
        return ""
    if collected_at is not None:
        return _format_seen_age(collected_at, now)
    if conf == "cached":
        return "时间未知"
    if conf == "unknown" or not host_ids:
        return "时间未知"
    chosen = None
    for hid in host_ids:
        if hid not in known_ids:
            continue
        seen = seen_map.get(hid)
        if seen is None:
            continue
        if conf == "stale":
            if hid not in stale_ids:
                continue
            if chosen is None or seen < chosen:
                chosen = seen
        else:
            if hid in stale_ids:
                continue
            if chosen is None or seen > chosen:
                chosen = seen
    if chosen is None:
        return "时间未知"
    return _format_seen_age(chosen, now)


def _quota_item(sub, now, stale_ids, known_ids, seen_map):
    kind = str(sub.get("kind") or "quota")
    conf = _effective_sub_confidence(sub, stale_ids, known_ids)
    source = str(sub.get("source") or "local")
    tool = str(sub.get("tool") or "未知")
    label = str(sub.get("label") or tool)
    is_quota = kind == "quota" or (kind == "" and source == "local")
    windows = _windows(sub, now)
    note = ""
    if conf == "error":
        status = "不可用"
        windows = []
        note = "采集失败，不是 0%"
    elif conf == "none" or not windows:
        status = "无数据"
        windows = []
        note = "缺失，不是 0%"
    elif conf == "unknown":
        status = "未知"
        note = "主机归属未知，不冒充新鲜"
    elif conf == "stale":
        status = "旧数据"
    elif conf == "cached":
        status = "缓存"
    else:
        status = "新鲜"
    if kind == "spend":
        is_quota = False
        note = "余额/花费口径，非订阅限额"
    elif kind in ("site", "account", "member", "key"):
        is_quota = False
        note = "中转/账号，不与限额加总"
    return {
        "id": str(sub.get("id") or "{0}:{1}".format(tool, label)),
        "tool": tool,
        "label": label,
        "kind": kind,
        "is_quota": is_quota,
        "confidence": conf,
        "status_label": status,
        "windows": windows,
        "note": note,
        "source": source,
        "age_label": _quota_age_label(
            _subscription_host_ids(sub),
            conf,
            seen_map,
            stale_ids,
            known_ids,
            now,
            parse_iso(sub.get("collectedAt")),
        ),
    }


def _waiting_you(run):
    return (
        run.get("state") == "wait"
        and run.get("stateConfidence") == "direct"
        and run.get("waitReason") == "needs_input"
    )


def _is_current_wait(run, stale_ids, known_ids):
    host_id = str(run.get("hostId") or "")
    if not host_id or host_id not in known_ids or host_id in stale_ids:
        return False
    return _waiting_you(run)


def _state_label(run, stale):
    if stale:
        return "旧记录"
    if _waiting_you(run):
        return "等你"
    return STATE_LABEL.get(str(run.get("state") or ""), "未知")


def _attention_counts(runs):
    waiting = human = background = 0
    for run in runs:
        initiator = run.get("initiator")
        state = run.get("state")
        conf = run.get("stateConfidence")
        if initiator == "human" and state == "wait" and conf == "direct":
            waiting += 1
        elif initiator == "human" and state in ("active", "idle"):
            human += 1
        elif initiator in ("agent", "machine") and state in ("active", "idle", "wait"):
            background += 1
    return waiting, human, background


def _rotate(items, offset, limit):
    if limit <= 0:
        return [], len(items)
    if len(items) <= limit:
        return items, 0
    start = offset % len(items)
    extended = items[start:] + items[:start]
    return extended[:limit], len(items) - limit


def demo_attention_items():
    return [
        {
            "id": "demo-confirm",
            "title": "确认发布计划",
            "project": "Demo",
            "tool": "Claude",
            "state_label": "等你确认",
            "host_id": "demo",
            "computer_hint": False,
            "demo": True,
        }
    ]


def unavailable_model(reason, demo=False):
    return {
        "source": "不可用",
        "demo": demo,
        "schema_ok": False,
        "offline": False,
        "freshness": "不可用",
        "collected_label": "无采集时间",
        "hub_generated_label": "",
        "age_label": "",
        "stats_line": "当前统计排除过期主机 · 等你 — · 人手 — · 后台 —",
        "note": reason,
        "quota_items": [],
        "spend_items": [],
        "hidden_quota": 0,
        "tasks": [],
        "hidden_tasks": 0,
        "attention": [],
        "waiting": 0,
        "human": 0,
        "background": 0,
        "has_stale_records": False,
        "rotate_hint": "",
        "hosts": [],
        "hub_label": "",
    }


def mark_offline(model, reason="网络失败，保留旧画面"):
    out = dict(model)
    out["offline"] = True
    out["freshness"] = "离线"
    out["note"] = reason + " · " + (model.get("note") or "")
    stats = model.get("stats_line") or ""
    if "离线" not in stats:
        out["stats_line"] = stats.replace("当前", "离线旧画面 · 当前")
    return out


def adapt(
    snapshot,
    now=None,
    demo=False,
    offline=False,
    source="http://127.0.0.1:8790/snapshot.json",
    rotate=0,
    quota_limit=None,
    task_limit=None,
):
    clock = now or utcnow()
    if not isinstance(snapshot, dict):
        return unavailable_model("快照不是对象", demo=demo)
    if snapshot.get("schema") != SNAPSHOT_SCHEMA:
        return unavailable_model("schema 不是 {0}".format(SNAPSHOT_SCHEMA), demo=demo)

    stale_ids = _stale_host_ids(snapshot, clock)
    collected, age_ms = _last_collected(snapshot, clock)
    seen_map = _host_seen_map(snapshot)
    hosts = [h for h in (snapshot.get("hosts") or []) if isinstance(h, dict)]
    known_ids = set(str(h.get("id") or "") for h in hosts if h.get("id"))
    live_hosts = [h for h in hosts if str(h.get("id") or "") not in stale_ids]
    if not hosts:
        freshness = "不可用"
        collected_label = "无主机采集时间"
    elif not live_hosts:
        freshness = "旧数据"
        collected_label = "采集 {0}".format(format_age(age_ms)) if collected else "采集时间未知"
    elif age_ms > STALE_AFTER_MS:
        freshness = "旧数据"
        collected_label = "采集 {0}".format(format_age(age_ms))
    else:
        freshness = "新鲜"
        collected_label = "采集 {0}".format(format_age(age_ms))

    generated = parse_iso(snapshot.get("generatedAt"))
    if generated:
        hub_generated_label = "Hub生成 {0}".format(
            format_age(max(0, int((clock - generated).total_seconds() * 1000)))
        )
    else:
        hub_generated_label = "Hub生成时间未知"

    quota_all = []
    spend_all = []
    for sub in snapshot.get("subscriptions") or []:
        if not isinstance(sub, dict):
            continue
        item = _quota_item(sub, clock, stale_ids, known_ids, seen_map)
        if item["kind"] == "spend" or not item["is_quota"]:
            if item["kind"] == "spend" or item["confidence"] == "error":
                spend_all.append(item)
            continue
        quota_all.append(item)

    def quota_key(item):
        windows = item["windows"]
        if windows:
            return (0, -max(w["used_pct"] for w in windows), item["tool"])
        if item["status_label"] == "不可用":
            return (1, 0, item["tool"])
        return (2, 0, item["tool"])

    quota_all.sort(key=quota_key)
    if quota_limit is None:
        shown_quota, hidden_quota = quota_all, 0
    else:
        shown_quota, hidden_quota = _rotate(quota_all, rotate, quota_limit)

    current_runs = [
        r
        for r in (snapshot.get("runs") or [])
        if isinstance(r, dict) and str(r.get("hostId") or "") not in stale_ids
    ]
    waiting, human, background = _attention_counts(current_runs)

    tasks_all = []
    attention_all = []
    for run in snapshot.get("runs") or []:
        if not isinstance(run, dict):
            continue
        host_id = str(run.get("hostId") or "")
        stale = host_id in stale_ids
        title = str(run.get("title") or "").strip() or "无标题"
        is_wait = _is_current_wait(run, stale_ids, known_ids)
        tasks_all.append(
            {
                "id": str(run.get("id") or "{0}:{1}".format(host_id, title)),
                "title": title,
                "project": folder_label(run.get("project")),
                "tool": str(run.get("tool") or ""),
                "state": str(run.get("state") or ""),
                "state_label": _state_label(run, stale),
                "is_stale_record": stale,
                "waiting_you": is_wait,
                "octoooo": is_octoooo(run),
                "host_id": host_id,
                "age_label": (
                    _format_seen_age(seen_map[host_id], clock) if host_id in seen_map else "时间未知"
                ),
            }
        )
        if is_wait:
            attention_all.append(
                {
                    "id": str(run.get("id") or "{0}:{1}".format(host_id, title)),
                    "title": title,
                    "project": folder_label(run.get("project")),
                    "tool": str(run.get("tool") or ""),
                    "state_label": "等你",
                    "host_id": host_id,
                    "computer_hint": True,
                    "demo": False,
                }
            )

    def task_key(item):
        return (
            0 if item["octoooo"] else 1,
            0 if not item["is_stale_record"] else 1,
            0 if item["waiting_you"] else 1,
            item["title"],
        )

    tasks_all.sort(key=task_key)
    if task_limit is None:
        shown_tasks, hidden_tasks = tasks_all, 0
    else:
        shown_tasks, hidden_tasks = _rotate(tasks_all, rotate, task_limit)
    if demo:
        attention_all = demo_attention_items() + attention_all

    stats_line = "当前统计排除过期主机 · 等你 {0} · 人手 {1} · 后台 {2}".format(
        waiting, human, background
    )
    note = "口径：窗口已用% · 账户不合计 · 余额非限额"
    if freshness == "旧数据":
        note = "采集已过期，不冒充实时 · " + note
    if demo:
        note = "DEMO 示例数据，非本机实时 · " + note
    if offline:
        freshness = "离线"
        note = "网络失败，保留旧画面 · " + note

    extra = []
    if hidden_quota:
        extra.append("限额另有 {0} 项".format(hidden_quota))
    if hidden_tasks:
        extra.append("任务另有 {0} 条".format(hidden_tasks))
    rotate_hint = " · ".join(extra)
    hub = (snapshot.get("hub") or {}).get("label") or "Aindle"
    host_rows = []
    for host in hosts:
        host_rows.append(
            {
                "id": str(host.get("id") or ""),
                "label": str(host.get("label") or host.get("id") or ""),
                "status": str(host.get("status") or ""),
                "stale": str(host.get("id") or "") in stale_ids,
            }
        )
    return {
        "source": ("DEMO · {0}".format(hub) if demo else "Aindle · {0}".format(hub)),
        "demo": demo,
        "schema_ok": True,
        "offline": offline,
        "freshness": freshness,
        "collected_label": collected_label,
        "hub_generated_label": hub_generated_label,
        "age_label": format_age(age_ms) if collected else "",
        "stats_line": stats_line,
        "note": note,
        "quota_items": shown_quota,
        "spend_items": spend_all[:2],
        "hidden_quota": hidden_quota,
        "tasks": shown_tasks,
        "hidden_tasks": hidden_tasks,
        "attention": attention_all,
        "waiting": waiting,
        "human": human,
        "background": background,
        "has_stale_records": any(t["is_stale_record"] for t in tasks_all),
        "rotate_hint": rotate_hint,
        "hosts": host_rows,
        "hub_label": hub,
        "url": source,
    }


def load_json_file(path):
    with open(path, "rb") as fh:
        raw = fh.read()
    return json.loads(raw.decode("utf-8"))


def fetch_snapshot(url, timeout=8):
    try:
        from urllib.request import Request, urlopen
    except ImportError:
        from urllib2 import Request, urlopen
    req = Request(url)
    try:
        req.add_header("Accept", "application/json")
    except Exception:
        pass
    fh = urlopen(req, timeout=timeout)
    try:
        raw = fh.read()
    finally:
        fh.close()
    if not isinstance(raw, str):
        raw = raw.decode("utf-8", "replace")
    return json.loads(raw)


def _slash30_peer(ip):
    parts = ip.split(".")
    if len(parts) != 4:
        return None
    try:
        nums = [int(p) for p in parts]
    except ValueError:
        return None
    last = nums[3]
    base = last - (last % 4)
    for host in (base + 1, base + 2):
        if host != last and 0 < host < 255:
            nums[3] = host
            return ".".join(str(n) for n in nums)
    return None


def guess_hub_url():
    hinted = os.environ.get("Q10_MONITOR_URL", "").strip()
    if hinted:
        return hinted
    peer = None
    try:
        import subprocess

        out = subprocess.check_output(["ifconfig"], stderr=subprocess.STDOUT)
        if not isinstance(out, str):
            out = out.decode("utf-8", "replace")
        for line in out.splitlines():
            parts = line.split()
            if len(parts) >= 2 and parts[0] == "inet" and parts[1].startswith("169.254."):
                peer = _slash30_peer(parts[1])
                if peer:
                    break
    except Exception:
        peer = None
    if peer:
        return "http://{0}:8790/snapshot.json".format(peer)
    return "http://169.254.0.2:8790/snapshot.json"


def here(*parts):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), *parts)


def load_demo_snapshot():
    cands = [
        here("fixtures", "snapshot_demo.json"),
        "/accounts/1000/shared/misc/q10-monitor-demo.json",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "q10-monitor-demo.json"),
    ]
    for path in cands:
        if os.path.isfile(path):
            return load_json_file(path)
    raise IOError("DEMO fixture not found")


def clip(text, width):
    text = (text or "").replace("\n", " ").strip()
    if width <= 0:
        return ""
    if len(text) <= width:
        return text
    if width == 1:
        return text[:1]
    return text[: width - 1] + "…"


def bar(pct, width=10):
    width = max(4, int(width))
    filled = int(round((pct / 100.0) * width))
    filled = min(width, max(0, filled))
    return "[" + ("#" * filled) + ("." * (width - filled)) + "]"


def write_out(text):
    if not text.endswith("\n"):
        text = text + "\n"
    try:
        sys.stdout.write(text)
        return
    except UnicodeEncodeError:
        pass
    raw = text.encode("utf-8")
    try:
        sys.stdout.flush()
        os.write(1, raw)
    except Exception:
        sys.stdout.buffer.write(raw)


def clear_screen():
    write_out("\033[2J\033[H")


def term_width(default=42):
    env = os.environ.get("COLUMNS")
    if env:
        try:
            return max(32, min(80, int(env)))
        except ValueError:
            pass
    try:
        import struct
        import fcntl
        import termios

        packed = fcntl.ioctl(1, termios.TIOCGWINSZ, struct.pack("HHHH", 0, 0, 0, 0))
        _rows, cols = struct.unpack("HHHH", packed)[:2]
        if cols >= 32:
            return min(80, int(cols))
    except Exception:
        pass
    return default


def render_page(model, page, width=42, offset=0):
    lines = []
    title = PAGE_TITLES.get(page, page)
    head = "Q10 {0}  {1}  {2}".format(title, model.get("freshness") or "", model.get("source") or "")
    lines.append(clip(head, width))
    lines.append("-" * min(width, 42))
    if page == "status":
        lines.append(clip(model.get("collected_label") or "", width))
        lines.append(clip(model.get("hub_generated_label") or "", width))
        lines.append(clip(model.get("stats_line") or "", width))
        ask_n = len(model.get("attention") or [])
        lines.append("ASK {0}".format(ask_n))
        for host in model.get("hosts") or []:
            mark = "旧" if host.get("stale") else (host.get("status") or "ok")
            lines.append(clip("主机 {0}  {1}".format(host.get("label") or host.get("id"), mark), width))
        lines.append(clip(model.get("note") or "", width))
        if model.get("rotate_hint"):
            lines.append(clip(model.get("rotate_hint"), width))
    elif page == "quota":
        items = model.get("quota_items") or []
        if not items:
            lines.append("没有限额条目")
        else:
            start = offset % len(items) if items else 0
            ordered = items[start:] + items[:start]
            for item in ordered:
                lines.append(
                    clip(
                        "{0}  {1}  {2}".format(
                            item.get("tool"), item.get("status_label"), item.get("age_label") or ""
                        ),
                        width,
                    )
                )
                if item.get("windows"):
                    for win in item["windows"]:
                        chunk = "{0} {1} {2} {3}".format(
                            bar(win["used_pct"], 8),
                            win["used_label"],
                            win["key"],
                            win.get("resets_label") or "",
                        )
                        lines.append("  " + clip(chunk, width - 2))
                if item.get("note"):
                    lines.append("  " + clip(item["note"], width - 2))
        spends = model.get("spend_items") or []
        if spends:
            lines.append(clip("—— 余额（非限额）——", width))
            for item in spends:
                lines.append(clip("{0}  {1}".format(item.get("tool"), item.get("label")), width))
                lines.append("  " + clip(item.get("note") or "", width - 2))
        if model.get("hidden_quota"):
            lines.append("另有 {0} 项".format(model["hidden_quota"]))
    elif page == "tasks":
        items = model.get("tasks") or []
        if not items:
            lines.append("没有任务")
        else:
            start = offset % len(items)
            ordered = items[start:] + items[:start]
            for item in ordered:
                mark = "*" if item.get("waiting_you") else ("·" if not item.get("is_stale_record") else "!")
                line = "{0} {1}  {2}  {3}".format(
                    mark,
                    item.get("state_label"),
                    item.get("tool") or "",
                    item.get("title") or "",
                )
                lines.append(clip(line, width))
                extra = "  {0}  {1}".format(item.get("project") or "", item.get("age_label") or "")
                if extra.strip():
                    lines.append(clip(extra, width))
        if model.get("hidden_tasks"):
            lines.append("另有 {0} 条".format(model["hidden_tasks"]))
    elif page == "ask":
        items = model.get("attention") or []
        if not items:
            lines.append("没有待处理")
        else:
            start = offset % len(items)
            ordered = items[start:] + items[:start]
            for item in ordered:
                lines.append(
                    clip(
                        "* {0}  {1}  {2}".format(
                            item.get("state_label"),
                            item.get("tool") or "",
                            item.get("title") or "",
                        ),
                        width,
                    )
                )
                if item.get("computer_hint"):
                    lines.append("  请在电脑处理")
                if item.get("demo"):
                    lines.append("  DEMO，不是真审批")
        lines.append(clip("Q10 不提交审批 / 不做对话", width))
    lines.append("-" * min(width, 42))
    lines.append("1状态 2限额 3任务 4待处理  j/k  r刷新  x退出")
    return "\n".join(lines) + "\n"


def read_key(timeout):
    try:
        import select
        import termios
        import tty
    except ImportError:
        time.sleep(timeout)
        return None
    fd = sys.stdin.fileno()
    try:
        old = termios.tcgetattr(fd)
    except Exception:
        time.sleep(timeout)
        return None
    try:
        tty.setraw(fd)
        ready, _, _ = select.select([sys.stdin], [], [], timeout)
        if not ready:
            return None
        ch = sys.stdin.read(1)
        if ch == "\x1b":
            select.select([sys.stdin], [], [], 0.02)
            while True:
                more, _, _ = select.select([sys.stdin], [], [], 0)
                if not more:
                    break
                sys.stdin.read(1)
            return None
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def load_source_times(path):
    if not path or not os.path.isfile(path):
        return None
    try:
        data = load_json_file(path)
    except Exception:
        return None
    if not isinstance(data, dict) or data.get("schema") != SOURCE_TIMES_SCHEMA:
        return None
    return data


def default_source_times_path():
    hinted = os.environ.get("OCTOOOO_MINI_SOURCE_TIMES", "").strip()
    if hinted:
        return hinted
    try:
        uid = os.getuid()
    except Exception:
        return ""
    return "/tmp/octoooo-mini-{0}/source-times.json".format(uid)


def build_parser():
    p = argparse.ArgumentParser(description="Q10 keyboard AI Monitor")
    p.add_argument("--url", default="", help="snapshot URL; default guesses USB peer :8790")
    p.add_argument("--once", action="store_true", help="print and exit")
    p.add_argument("--all", action="store_true", help="print every page (implies --once)")
    p.add_argument("--watch", action="store_true", help="refresh loop")
    p.add_argument("--page", choices=PAGES, default="status")
    p.add_argument("--demo", action="store_true", help="explicit DEMO fixture; never automatic")
    p.add_argument("--file", default="", help="read snapshot from a JSON file")
    p.add_argument("--source-times", default="", help="optional sidecar JSON")
    p.add_argument("--interval", type=int, default=10)
    p.add_argument("--width", type=int, default=0)
    return p


def obtain_snapshot(args):
    if args.demo:
        snap = load_demo_snapshot()
        return overlay_source_times(snap, load_source_times(args.source_times)), None
    if args.file:
        snap = load_json_file(args.file)
        return overlay_source_times(snap, load_source_times(args.source_times)), None
    url = args.url or guess_hub_url()
    snap = fetch_snapshot(url)
    overlay = load_source_times(args.source_times or default_source_times_path())
    return overlay_source_times(snap, overlay), url


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.all:
        args.once = True
    width = args.width or term_width()
    page = args.page
    offset = 0
    last = None
    interactive = (not args.once) and (args.watch or (sys.stdin.isatty() and sys.stdout.isatty()))
    if not args.once and not args.watch and not interactive:
        args.once = True
        args.all = True

    def pull():
        try:
            snap, url = obtain_snapshot(args)
            model = adapt(
                snap,
                demo=args.demo,
                source=url or args.file or "demo",
            )
            return model, None
        except Exception as exc:
            return None, exc

    model, err = pull()
    if model is None:
        model = unavailable_model("拉快照失败：{0}".format(err))
        last = None
        if args.once:
            if args.all:
                for name in PAGES:
                    write_out(render_page(model, name, width=width))
            else:
                write_out(render_page(model, page, width=width))
            return 2
    else:
        last = model

    if args.once:
        pages = PAGES if args.all else (page,)
        for name in pages:
            write_out(render_page(model, name, width=width, offset=offset))
        return 0 if model.get("schema_ok") else 2

    interval = max(2, int(args.interval))
    while True:
        shown = last or model
        if sys.stdout.isatty():
            clear_screen()
        write_out(render_page(shown, page, width=width, offset=offset))
        sys.stdout.flush()
        key = None
        if interactive and sys.stdin.isatty():
            key = read_key(interval)
        else:
            time.sleep(interval)
            key = "r"
        if key in ("x", "X", "q", "\x03"):
            return 0
        if key in ("1",):
            page, offset = "status", 0
            continue
        if key in ("2",):
            page, offset = "quota", 0
            continue
        if key in ("3",):
            page, offset = "tasks", 0
            continue
        if key in ("4",):
            page, offset = "ask", 0
            continue
        if key in ("j", "J", "n"):
            offset += 1
            continue
        if key in ("k", "K", "p"):
            offset -= 1
            continue
        if key in ("r", "R", None):
            nxt, err = pull()
            if nxt is not None:
                last = nxt
            elif last is not None:
                last = mark_offline(last)
            else:
                last = unavailable_model("拉快照失败：{0}".format(err))


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(0)
