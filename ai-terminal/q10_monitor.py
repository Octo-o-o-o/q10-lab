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
ASK_HISTORY_SCHEMA = "q10.ask-history.v1"
ASK_HISTORY_MAX = 24
# Aindle 合同：AINDLE_PORT 默认 8787。8790 只作旧客户端回退，不在本仓库另起 Hub。
HUB_PORT = 8787
HUB_LEGACY_PORT = 8790
SOURCE_TIMES_SCHEMA = "octoooo-mini.source-times.v1"
STALE_AFTER_MS = 5 * 60 * 1000
PAGES = ("quota", "tasks", "ask")
# Q10 数字印在字母上。不按 Alt 时 W/E/R/S = 1/2/3/4。
# 现三页：4/S 与 3/R 都进待处理。刷新不用 R，否则挡住第 3 页。
TASK_FILTERS = ("active", "idle", "done", "all")
TASK_FILTER_DEFAULT = "active"
TASK_AGENT_W = 4
TASK_PROJ_W = 8
_TASK_FILTER_KEYS = {
    "a": "active",
    "A": "active",
    "i": "idle",
    "I": "idle",
    "d": "done",
    "D": "done",
    "u": "all",
    "U": "all",
}
_TOOL_ABBR = {
    "Claude": "CLD",
    "Codex": "CDX",
    "Cursor": "CUR",
    "Gemini": "GEM",
    "Grok": "GROK",
    "GLM": "GLM",
    "Kimi": "KIMI",
    "DeepSeek": "DSK",
    "ZCode": "ZCD",
    "Aindle": "AIN",
}
_PROJ_ABBR = {
    "Octoooo": "Octo",
    "Aindle": "Aindle",
    "lab": "lab",
    "OctoDesk": "OctoDesk",
    "OctoWorkFlow": "OWF",
    "OctoWork": "OWF",
    "worktree": "wt",
    "ContextVista": "Ctx",
    "ContextView": "Ctx",
    "Context": "Ctx",
    "Contexpect": "Ctx",
    "SayDo": "SayDo",
    "saydo-p": "SayDo",
    "YouUsage": "YU",
    "YoUsage": "YU",
    "waveshare": "WS",
    "Waveshare": "WS",
    "DemoApp": "Demo",
    "Legacy": "Leg",
    "Other": "Oth",
    "RoundScreenDemo": "RSD",
    "演示": "Demo",
}
_PAGE_BY_KEY = {
    "1": "quota",
    "w": "quota",
    "W": "quota",
    "2": "tasks",
    "e": "tasks",
    "E": "tasks",
    "3": "ask",
    "r": "ask",
    "R": "ask",
    "4": "ask",
    "s": "ask",
    "S": "ask",
}
# 默认中文。Term49 须用 GB18030 字体，见 q10-term49-font.sh。
_UI_LANG = "zh"
_UI = {
    "zh": {
        "status": "状态",
        "quota": "限额",
        "tasks": "任务",
        "ask": "待处理",
        "live": "新鲜",
        "cached": "缓存",
        "stale": "旧数据",
        "error": "不可用",
        "none": "无数据",
        "unknown": "未知",
        "active": "进行中",
        "wait": "等待",
        "idle": "空闲",
        "done": "完成",
        "fail": "失败",
        "just_now": "刚刚",
        "sec_ago": "{0}秒前",
        "min_ago": "{0}分钟前",
        "hr_ago": "{0}小时前",
        "day_ago": "{0}天前",
        "used": "已用 {0}%",
        "time_unknown": "时间未知",
        "unknown_tool": "未知",
        "err_note": "采集失败，不是 0%",
        "none_note": "缺失，不是 0%",
        "unknown_note": "主机归属未知，不冒充新鲜",
        "spend_note": "余额/花费口径，非订阅限额",
        "relay_note": "中转/账号，不与限额加总",
        "old_record": "旧记录",
        "waiting_you": "等你",
        "unavailable": "不可用",
        "no_collect": "无采集时间",
        "stats_na": "当前统计排除过期主机 · 等你 — · 人手 — · 后台 —",
        "offline": "离线",
        "offline_reason": "网络失败，保留旧画面",
        "offline_prefix": "离线旧画面 · ",
        "bad_object": "快照不是对象",
        "bad_schema": "schema 不是 {0}",
        "no_host_time": "无主机采集时间",
        "collect_unknown": "采集时间未知",
        "collect": "采集 {0}",
        "hub_gen": "Hub生成 {0}",
        "hub_unknown": "Hub生成时间未知",
        "no_title": "无标题",
        "stats": "当前统计排除过期主机 · 等你 {0} · 人手 {1} · 后台 {2}",
        "note": "口径：窗口已用% · 账户不合计 · 余额非限额",
        "stale_note": "采集已过期，不冒充实时 · ",
        "demo_note": "演示数据，非本机实时 · ",
        "offline_note": "网络失败，保留旧画面 · ",
        "more_quota": "限额另有 {0} 项",
        "more_tasks": "任务另有 {0} 条",
        "host": "主机 {0}  {1}",
        "stale_mark": "旧",
        "no_quota": "没有限额条目",
        "spend_head": "花费（非限额）",
        "more_n": "另有 {0} 项",
        "more_n_tasks": "另有 {0} 条",
        "header_run": "进行{0} · 后台{1}",
        "page_hint": "第{0}/{1}页 · j下 k上",
        "flt_active": "进行",
        "flt_idle": "空闲",
        "flt_done": "完成",
        "flt_all": "全部",
        "no_filter_tasks": "没有这类任务 · a进行 i空闲 d完成 u全部",
        "ask_open": "待处理",
        "ask_done": "已处理",
        "no_tasks": "没有任务",
        "no_ask": "没有待处理",
        "on_computer": "请在电脑处理",
        "demo_ask": "演示，不是真审批",
        "no_chat": "Q10 不提交审批 / 不做对话",
        "footer": "1限额 2任务 3待处理  t刷新 x关闭",
        "tbl_tool": "工具",
        "tbl_bar": "条",
        "tbl_pct": "已用",
        "tbl_win": "窗",
        "tbl_reset": "重置",
        "tbl_host": "主机",
        "tbl_age": "年龄",
        "tbl_st": "态",
        "tbl_title": "标题",
        "tbl_amount": "金额",
        "tbl_key": "项",
        "tbl_value": "值",
        "row_collect": "采集",
        "row_hub": "Hub",
        "row_counts": "待处理/等你/人手/后台",
        "counts": "等你 {0} · 人手 {1} · 后台 {2}",
        "note_short": "已用% · 账户不加总 · 花费≠限额",
        "cell_err": "失败",
        "cell_none": "缺失",
        "st_you": "等你",
        "st_run": "进行",
        "st_wait": "等待",
        "st_idle": "空闲",
        "st_done": "完成",
        "st_fail": "失败",
        "st_old": "旧",
        "st_ok": "正常",
        "link_usb": "USB",
        "link_lan": "局域网",
        "link_mailbox": "信箱",
        "fetch_fail": "拉快照失败：{0}",
        "weekdays": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"],
        "demo_title": "确认发布计划",
        "demo_state": "等你确认",
    },
    "en": {
        "status": "STATUS",
        "quota": "QUOTA",
        "tasks": "TASKS",
        "ask": "ASK",
        "live": "live",
        "cached": "cached",
        "stale": "stale",
        "error": "error",
        "none": "none",
        "unknown": "unknown",
        "active": "active",
        "wait": "wait",
        "idle": "idle",
        "done": "done",
        "fail": "fail",
        "just_now": "just now",
        "sec_ago": "{0}s ago",
        "min_ago": "{0}m ago",
        "hr_ago": "{0}h ago",
        "day_ago": "{0}d ago",
        "used": "used {0}%",
        "time_unknown": "time unknown",
        "unknown_tool": "unknown",
        "err_note": "collect failed, not 0%",
        "none_note": "missing, not 0%",
        "unknown_note": "host mapping unknown",
        "spend_note": "balance/spend, not quota",
        "relay_note": "relay/account, not summed",
        "old_record": "old record",
        "waiting_you": "NEED YOU",
        "unavailable": "unavailable",
        "no_collect": "no collect time",
        "stats_na": "stats skip stale hosts · need you - · human - · bg -",
        "offline": "offline",
        "offline_reason": "network failed, keep last screen",
        "offline_prefix": "offline last · ",
        "bad_object": "snapshot is not an object",
        "bad_schema": "schema is not {0}",
        "no_host_time": "no host collect time",
        "collect_unknown": "collect time unknown",
        "collect": "collect {0}",
        "hub_gen": "hub {0}",
        "hub_unknown": "hub time unknown",
        "no_title": "(no title)",
        "stats": "stats skip stale hosts · need you {0} · human {1} · bg {2}",
        "note": "used% windows · accounts not summed · spend != quota",
        "stale_note": "stale collect, not live · ",
        "demo_note": "DEMO data, not live · ",
        "offline_note": "network failed, keep last screen · ",
        "more_quota": "{0} more quota",
        "more_tasks": "{0} more tasks",
        "host": "host {0}  {1}",
        "stale_mark": "old",
        "no_quota": "no quota rows",
        "spend_head": "SPEND != quota",
        "more_n": "{0} more",
        "more_n_tasks": "{0} more",
        "header_run": "run{0} · bg{1}",
        "page_hint": "p{0}/{1} · j/k",
        "flt_active": "run",
        "flt_idle": "idl",
        "flt_done": "dn",
        "flt_all": "all",
        "no_filter_tasks": "no tasks in filter · a/i/d/u",
        "ask_open": "OPEN",
        "ask_done": "done",
        "no_tasks": "no tasks",
        "no_ask": "nothing waiting",
        "on_computer": "handle on the computer",
        "demo_ask": "DEMO, not a real approval",
        "no_chat": "Q10 does not approve or chat",
        "footer": "1 QUOTA  2 TASK  3 ASK  t x",
        "tbl_tool": "TOOL",
        "tbl_bar": "BAR",
        "tbl_pct": "PCT",
        "tbl_win": "WIN",
        "tbl_reset": "RESET",
        "tbl_host": "HOST",
        "tbl_age": "AGE",
        "tbl_st": "ST",
        "tbl_title": "TITLE",
        "tbl_amount": "AMOUNT",
        "tbl_key": "KEY",
        "tbl_value": "VALUE",
        "row_collect": "collect",
        "row_hub": "hub",
        "row_counts": "ASK/you/hum/bg",
        "counts": "need {0} · human {1} · bg {2}",
        "note_short": "used% · accounts not summed · spend!=quota",
        "cell_err": "ERR",
        "cell_none": "NONE",
        "st_you": "YOU",
        "st_run": "RUN",
        "st_wait": "WAIT",
        "st_idle": "IDLE",
        "st_done": "DONE",
        "st_fail": "FAIL",
        "st_old": "OLD",
        "st_ok": "ok",
        "link_usb": "USB",
        "link_lan": "LAN",
        "link_mailbox": "box",
        "fetch_fail": "fetch failed: {0}",
        "weekdays": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        "demo_title": "Confirm release plan",
        "demo_state": "need confirm",
    },
}


def set_ui_lang(lang):
    global _UI_LANG
    if lang in _UI:
        _UI_LANG = lang
    else:
        _UI_LANG = "en"
    return _UI_LANG


def t(key, *args):
    table = _UI.get(_UI_LANG) or _UI["en"]
    text = table.get(key)
    if text is None:
        text = _UI["en"].get(key) or key
    if args:
        return text.format(*args)
    return text


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
        return t("just_now")
    if sec < 60:
        return t("sec_ago", sec)
    minutes = sec // 60
    if minutes < 60:
        return t("min_ago", minutes)
    hours = minutes // 60
    if hours < 48:
        return t("hr_ago", hours)
    return t("day_ago", hours // 24)


def format_reset(iso, now):
    dt = parse_iso(iso)
    if dt is None:
        return "-"
    clock = dt.strftime("%H:%M")
    if dt.date() == now.date():
        return clock
    days = t("weekdays")
    return "{0} {1}".format(days[dt.weekday()], clock)


# --lang en 时把窗口名收成 ASCII，方便无汉字字体的终端。
_WIN_KEY_EN = {
    "三方": "3rd",
    "自有": "own",
    "本周": "week",
    "月": "mo",
    "预算": "budg",
}


def ascii_en_text(text, fallback=""):
    raw = str(text or "")
    if _UI_LANG != "en":
        return raw
    keep = []
    for ch in raw:
        if ord(ch) < 128 or ch in "¥€£":
            keep.append(ch)
    out = " ".join("".join(keep).split())
    return out if out else fallback


def window_key_label(key):
    raw = str(key or "").strip()
    if _UI_LANG == "en" and raw in _WIN_KEY_EN:
        return _WIN_KEY_EN[raw]
    if _UI_LANG == "en":
        ascii_only = "".join(ch for ch in raw if ord(ch) < 128).strip()
        return ascii_only or "win"
    return raw or "-"


def _host_status_label(status):
    raw = str(status or "").strip().lower()
    mapping = {
        "ok": "st_ok",
        "online": "st_ok",
        "up": "st_ok",
        "error": "st_fail",
        "fail": "st_fail",
        "down": "st_fail",
        "offline": "offline",
        "stale": "st_old",
    }
    if raw in mapping:
        return t(mapping[raw])
    return status or t("st_ok")


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
                "key_label": window_key_label(key),
                "used_pct": pct,
                "used_label": t("used", pct),
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
        return t("time_unknown")
    if conf == "unknown" or not host_ids:
        return t("time_unknown")
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
        return t("time_unknown")
    return _format_seen_age(chosen, now)


def _quota_item(sub, now, stale_ids, known_ids, seen_map):
    kind = str(sub.get("kind") or "quota")
    conf = _effective_sub_confidence(sub, stale_ids, known_ids)
    source = str(sub.get("source") or "local")
    tool = str(sub.get("tool") or t("unknown_tool"))
    label = str(sub.get("label") or tool)
    is_quota = kind == "quota" or (kind == "" and source == "local")
    windows = _windows(sub, now)
    note = ""
    if conf == "error":
        status = t("error")
        windows = []
        note = t("err_note")
    elif conf == "none" or not windows:
        status = t("none")
        windows = []
        note = t("none_note")
    elif conf == "unknown":
        status = t("unknown")
        note = t("unknown_note")
    elif conf == "stale":
        status = t("stale")
    elif conf == "cached":
        status = t("cached")
    else:
        status = t("live")
    if kind == "spend":
        is_quota = False
        note = t("spend_note")
    elif kind in ("site", "account", "member", "key"):
        is_quota = False
        note = t("relay_note")
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


def quota_item_visible(item):
    if not item or not item.get("is_quota"):
        return False
    if item.get("confidence") in ("error", "none"):
        return False
    return bool(item.get("windows"))


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
        return t("old_record")
    if _waiting_you(run):
        return t("waiting_you")
    key = str(run.get("state") or "")
    if key in ("active", "wait", "idle", "done", "fail"):
        return t(key)
    return t("unknown")


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
            "title": t("demo_title"),
            "project": "演示",
            "tool": "Claude",
            "state_label": t("demo_state"),
            "host_id": "demo",
            "computer_hint": False,
            "demo": True,
        }
    ]


def unavailable_model(reason, demo=False):
    return {
        "source": t("unavailable"),
        "demo": demo,
        "schema_ok": False,
        "offline": False,
        "freshness": t("unavailable"),
        "collected_label": t("no_collect"),
        "hub_generated_label": "",
        "age_label": "",
        "stats_line": t("stats_na"),
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
        "link": "",
        "url": "",
    }


def mark_offline(model, reason=None):
    if reason is None:
        reason = t("offline_reason")
    if model.get("octoooo_readonly"):
        return octoooo_unavailable("Octoooo 连接中断，授权内容已清除")
    out = dict(model)
    out["offline"] = True
    out["freshness"] = t("offline")
    out["note"] = reason + " · " + (model.get("note") or "")
    stats = model.get("stats_line") or ""
    if t("offline") not in stats:
        out["stats_line"] = t("offline_prefix") + stats
    return out


def octoooo_unavailable(reason, demo=False):
    model = unavailable_model(reason, demo=demo)
    model["octoooo_readonly"] = True
    return model


def adapt_octoooo(snapshot, now, demo=False, source=""):
    rows = snapshot.get("rows")
    expires = parse_iso(snapshot.get("valid_until"))
    if snapshot.get("complete") is not True or not isinstance(rows, list) or type(snapshot.get("total")) is not int or snapshot.get("total") != len(rows):
        return octoooo_unavailable("Octoooo 快照不完整", demo=demo)
    if expires is None or expires <= now:
        return octoooo_unavailable("Octoooo 授权画面已过期，请刷新", demo=demo)
    out = unavailable_model("只读投影；翻页不是已读，任务状态来自来源", demo=demo)
    out.update({"schema_ok": True, "source": "Octoooo", "hub_label": "Octoooo", "url": source,
                "freshness": "受限快照", "collected_label": "逐项显示采集时间", "octoooo_readonly": True,
                "valid_until": snapshot.get("valid_until"), "stats_line": "共 {0} 项授权记录".format(len(rows))})
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or row.get("kind") not in ("usage", "source", "activity") or not isinstance(row.get("id"), str) or not row["id"]:
            return octoooo_unavailable("Octoooo 记录无效", demo=demo)
        identity = row["kind"] + ":" + row["id"]
        if identity in seen:
            return octoooo_unavailable("Octoooo 记录重复", demo=demo)
        seen.add(identity)
        observed = parse_iso(row.get("observed_at"))
        fresh = row.get("stale") is not True and observed is not None and observed <= now and (now - observed).total_seconds() <= 60
        age = _format_seen_age(observed, now) if observed is not None and observed <= now else t("time_unknown")
        if row["kind"] == "usage":
            value = row.get("value")
            valid = type(value) in (int, float) and not math.isnan(value) and not math.isinf(value) and value >= 0
            if valid:
                value = int(round(value))
            windows = [] if not valid else [{"key": str(row.get("window") or "窗口"), "key_label": str(row.get("window") or "窗口"), "used_pct": value, "used_label": t("used", value), "resets_label": "—"}]
            out["quota_items"].append({"id": identity, "tool": str(row.get("provider") or "订阅"), "label": "授权窗口", "kind": "quota", "is_quota": True,
                "octoooo_unknown": not valid, "confidence": "live" if fresh else "unknown" if observed is None else "stale", "status_label": t("live") if fresh else t("unknown"),
                "windows": windows, "note": "未知不是零；超额值不截断", "source": "octoooo", "age_label": age})
        elif row["kind"] == "source":
            state = {"running": "active", "idle": "idle", "completed": "done", "failed": "fail", "needs_attention": "wait"}.get(row.get("status"), "unknown")
            out["tasks"].append({"id": identity, "title": "来源观察", "project": "", "tool": "Octoooo", "state": state,
                "state_label": {"active": "运行中", "idle": "空闲", "done": "已完成", "fail": "失败", "wait": "需要关注"}.get(state, "未知"),
                "is_stale_record": not fresh, "waiting_you": state == "wait" and fresh, "octoooo": True, "host_id": "", "age_label": age})
        else:
            out["attention"].append({"id": identity, "title": "有事项可查看", "project": "", "tool": "Octoooo", "state_label": "只读", "host_id": "", "computer_hint": True, "demo": False})
    out["waiting"] = len(out["attention"])
    return out


def adapt(
    snapshot,
    now=None,
    demo=False,
    offline=False,
    source="http://127.0.0.1:8787/snapshot.json",
    rotate=0,
    quota_limit=None,
    task_limit=None,
    lang=None,
):
    if lang:
        set_ui_lang(lang)
    clock = now or utcnow()
    if not isinstance(snapshot, dict):
        return unavailable_model(t("bad_object"), demo=demo)
    if snapshot.get("schema") == "octoooo.weak.v1":
        return adapt_octoooo(snapshot, clock, demo=demo, source=source)
    if snapshot.get("schema") != SNAPSHOT_SCHEMA:
        return unavailable_model(t("bad_schema", SNAPSHOT_SCHEMA), demo=demo)

    stale_ids = _stale_host_ids(snapshot, clock)
    collected, age_ms = _last_collected(snapshot, clock)
    seen_map = _host_seen_map(snapshot)
    hosts = [h for h in (snapshot.get("hosts") or []) if isinstance(h, dict)]
    known_ids = set(str(h.get("id") or "") for h in hosts if h.get("id"))
    live_hosts = [h for h in hosts if str(h.get("id") or "") not in stale_ids]
    if not hosts:
        freshness = t("unavailable")
        collected_label = t("no_host_time")
    elif not live_hosts:
        freshness = t("stale")
        collected_label = t("collect", format_age(age_ms)) if collected else t("collect_unknown")
    elif age_ms > STALE_AFTER_MS:
        freshness = t("stale")
        collected_label = t("collect", format_age(age_ms))
    else:
        freshness = t("live")
        collected_label = t("collect", format_age(age_ms))

    generated = parse_iso(snapshot.get("generatedAt"))
    if generated:
        hub_generated_label = t(
            "hub_gen",
            format_age(max(0, int((clock - generated).total_seconds() * 1000))),
        )
    else:
        hub_generated_label = t("hub_unknown")

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
        if not quota_item_visible(item):
            continue
        quota_all.append(item)

    def quota_key(item):
        windows = item["windows"]
        if windows:
            return (0, -max(w["used_pct"] for w in windows), item["tool"])
        if item["confidence"] == "error":
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
        title = str(run.get("title") or "").strip() or t("no_title")
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
                    _format_seen_age(seen_map[host_id], clock) if host_id in seen_map else t("time_unknown")
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
                    "state_label": t("waiting_you"),
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

    stats_line = t("stats", waiting, human, background)
    note = t("note")
    if freshness == t("stale"):
        note = t("stale_note") + note
    if demo:
        note = t("demo_note") + note
    if offline:
        freshness = t("offline")
        note = t("offline_note") + note

    extra = []
    if hidden_quota:
        extra.append(t("more_quota", hidden_quota))
    if hidden_tasks:
        extra.append(t("more_tasks", hidden_tasks))
    rotate_hint = " · ".join(extra)
    hub = (snapshot.get("hub") or {}).get("label") or "Aindle"
    host_rows = []
    for host in hosts:
        hid = str(host.get("id") or "")
        seen = seen_map.get(hid)
        host_rows.append(
            {
                "id": hid,
                "label": str(host.get("label") or hid or ""),
                "status": str(host.get("status") or ""),
                "stale": hid in stale_ids,
                "age_short": _format_seen_age(seen, clock) if seen else "?",
            }
        )
    return {
        "source": ("演示 · {0}".format(hub) if demo else hub),
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
        "link": hub_link_kind(source),
    }


def load_json_file(path):
    with open(path, "rb") as fh:
        raw = fh.read()
    return json.loads(raw.decode("utf-8"))


def _mailbox_token():
    env = os.environ.get("Q10_MAILBOX_TOKEN", "").strip()
    if env:
        return env
    hinted = os.environ.get("Q10_MAILBOX_TOKEN_FILE", "").strip()
    paths = []
    if hinted:
        paths.append(hinted)
    paths.append("/accounts/1000/shared/misc/q10-mailbox.token")
    for path in paths:
        if not path:
            continue
        try:
            if not os.path.isfile(path):
                continue
            fh = open(path, "rb")
            try:
                raw = fh.read()
            finally:
                fh.close()
        except Exception:
            continue
        text = raw.decode("utf-8").strip() if not isinstance(raw, str) else raw.strip()
        if text:
            return text
    return ""


def _curl_bin():
    hinted = os.environ.get("Q10_CURL", "").strip()
    if hinted:
        return hinted
    for path in (
        "/accounts/1000/shared/misc/berrycore/bin/curl",
        "/usr/bin/curl",
        "/opt/homebrew/bin/curl",
    ):
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    return "curl"


def _fetch_urllib(url, timeout):
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


def _fetch_curl(url, timeout, token):
    import subprocess

    cmd = [_curl_bin(), "-sS", "-f", "-m", str(int(timeout)), "-H", "Accept: application/json"]
    if token:
        cmd.extend(["-H", "Authorization: Bearer {0}".format(token)])
    cmd.append(url)
    raw = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    if not isinstance(raw, str):
        raw = raw.decode("utf-8", "replace")
    return json.loads(raw)


def fetch_octoooo(url, binding_file, timeout=8):
    import subprocess
    import re
    binding = load_json_file(binding_file)
    if url != binding.get("url") or not url.startswith("https://") or "\n" in url or "\r" in url:
        raise ValueError("Explicit matching HTTPS projection URL required")
    device = binding.get("device_id", "")
    token = binding.get("token", "")
    if not re.match(r"^[a-z0-9][a-z0-9-]{1,62}$", device) or not re.match(r"^[A-Za-z0-9_.~-]{1,512}$", token):
        raise ValueError("Invalid device binding")
    parsed = _urlparse(url)
    if parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path != "/projection.json":
        raise ValueError("Projection URL must not contain credentials or query parameters")
    config = 'header = "Authorization: Bearer {0}"\nheader = "x-octo-device-id: {1}"\n'.format(token, device)
    child = subprocess.Popen([_curl_bin(), "--config", "-", "-sS", "-f", "-m", str(int(timeout)), url], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    raw, error = child.communicate(config.encode("utf-8"))
    if child.returncode != 0:
        raise IOError("Octoooo projection request rejected")
    return json.loads(raw.decode("utf-8"))


def fetch_snapshot(url, timeout=8):
    binding_file = os.environ.get("Q10_OCTOOOO_BINDING_FILE")
    if binding_file:
        return fetch_octoooo(url, binding_file, timeout)
    token = _mailbox_token()
    if url.lower().startswith("https://"):
        return _fetch_curl(url, timeout, token)
    return _fetch_urllib(url, timeout)


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


def _usb_hub_url():
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
        return "http://{0}:{1}/snapshot.json".format(peer, HUB_PORT)
    return ""


def _urlparse(url):
    try:
        from urllib.parse import urlparse
    except ImportError:
        from urlparse import urlparse
    return urlparse(url)


def _url_host(url):
    try:
        return (_urlparse(url).hostname or "").strip()
    except Exception:
        return ""


def hub_ports(raw=None):
    if raw is None:
        raw = os.environ.get("Q10_HUB_PORTS", "").strip()
        if not raw:
            raw = os.environ.get("AINDLE_PORT", "").strip()
    ports = []
    text = str(raw or "").replace(" ", ",")
    for part in text.split(","):
        part = part.strip()
        if not part.isdigit():
            continue
        port = int(part)
        if 1 <= port <= 65535 and port not in ports:
            ports.append(port)
    for port in (HUB_PORT, HUB_LEGACY_PORT):
        if port not in ports:
            ports.append(port)
    return ports


def replace_url_port(url, port):
    try:
        from urllib.parse import urlunparse
    except ImportError:
        from urlparse import urlunparse
    parsed = _urlparse(url)
    host = (parsed.hostname or "").strip()
    if not host:
        return url
    auth = ""
    if parsed.username:
        auth = parsed.username
        if parsed.password:
            auth += ":" + parsed.password
        auth += "@"
    netloc = "{0}{1}:{2}".format(auth, host, int(port))
    path = parsed.path or "/snapshot.json"
    return urlunparse(
        (parsed.scheme, netloc, path, parsed.params, parsed.query, parsed.fragment)
    )


def expand_http_ports(url, ports=None):
    if not url:
        return []
    if str(url).lower().startswith("https://"):
        return [url]
    out = [url]
    for port in ports or hub_ports():
        cand = replace_url_port(url, port)
        if cand and cand not in out:
            out.append(cand)
    return out


def last_hub_path():
    hinted = os.environ.get("Q10_HUB_LAST_FILE", "").strip()
    if hinted:
        return hinted
    device = "/accounts/1000/shared/misc/q10-hub.last"
    if os.path.isdir("/accounts/1000/shared/misc"):
        return device
    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "local-config", "q10-hub.last"
    )


def _valid_hub_url(url):
    text = str(url or "").strip()
    if not text or len(text) > 300 or "\n" in text or " " in text:
        return ""
    low = text.lower()
    if not (low.startswith("http://") or low.startswith("https://")):
        return ""
    return text


def read_last_hub_url():
    path = last_hub_path()
    try:
        fh = open(path, "rb")
        try:
            raw = fh.read()
        finally:
            fh.close()
    except Exception:
        return ""
    if not isinstance(raw, str):
        raw = raw.decode("utf-8", "replace")
    return _valid_hub_url(raw.splitlines()[0] if raw else "")


def write_last_hub_url(url):
    text = _valid_hub_url(url)
    if not text:
        return False
    path = last_hub_path()
    parent = os.path.dirname(path)
    try:
        if parent and not os.path.isdir(parent):
            os.makedirs(parent)
        fh = open(path, "w")
        try:
            fh.write(text + "\n")
        finally:
            fh.close()
    except Exception:
        return False
    return True


def ask_history_path():
    hinted = os.environ.get("Q10_ASK_HISTORY_FILE", "").strip()
    if hinted:
        return hinted
    if os.path.isdir("/accounts/1000/shared/misc"):
        return "/accounts/1000/shared/misc/q10-ask-history.json"
    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "local-config", "q10-ask-history.json"
    )


def _ask_record(item, open_flag):
    return {
        "id": str(item.get("id") or ""),
        "title": str(item.get("title") or ""),
        "project": str(item.get("project") or ""),
        "tool": str(item.get("tool") or ""),
        "computer_hint": bool(item.get("computer_hint")),
        "demo": bool(item.get("demo")),
        "open": bool(open_flag),
    }


def read_ask_history():
    path = ask_history_path()
    try:
        data = load_json_file(path)
    except Exception:
        return []
    if not isinstance(data, dict) or data.get("schema") != ASK_HISTORY_SCHEMA:
        return []
    out = []
    for item in data.get("items") or []:
        if isinstance(item, dict) and item.get("id"):
            out.append(_ask_record(item, item.get("open", True)))
    return out


def write_ask_history(items):
    path = ask_history_path()
    parent = os.path.dirname(path)
    payload = {"schema": ASK_HISTORY_SCHEMA, "items": []}
    for item in items or []:
        if item.get("id"):
            payload["items"].append(_ask_record(item, item.get("open", True)))
    try:
        if parent and not os.path.isdir(parent):
            os.makedirs(parent)
        fh = open(path, "w")
        try:
            fh.write(json.dumps(payload, ensure_ascii=True))
        finally:
            fh.close()
    except Exception:
        return False
    return True


def merge_ask_history(current, stored, live):
    by_id = {}
    for item in stored or []:
        iid = str(item.get("id") or "")
        if iid:
            by_id[iid] = _ask_record(item, item.get("open", True))
    now_ids = set()
    for item in current or []:
        iid = str(item.get("id") or "")
        if not iid:
            continue
        now_ids.add(iid)
        by_id[iid] = _ask_record(item, True)
    if live:
        for iid, row in by_id.items():
            if iid not in now_ids:
                row["open"] = False
    items = list(by_id.values())
    items.sort(key=lambda row: (0 if row.get("open") else 1, row.get("title") or ""))
    opened = [row for row in items if row.get("open")]
    closed = [row for row in items if not row.get("open")]
    keep = ASK_HISTORY_MAX - len(opened)
    if keep < 0:
        keep = 0
    return opened + closed[:keep]


def remember_attention(model):
    if model and model.get("octoooo_readonly"):
        return model
    if not model:
        return model
    live = bool(model.get("schema_ok") and not model.get("offline"))
    merged = merge_ask_history(model.get("attention") or [], read_ask_history(), live)
    if live:
        write_ask_history(merged)
    model["attention"] = merged
    model["ask_open"] = len([row for row in merged if row.get("open")])
    return model


def on_qnx_device():
    if os.path.isdir("/accounts/1000/shared/misc"):
        return True
    try:
        return os.uname()[0] == "QNX"
    except Exception:
        return False


def _loopback_hub_url():
    if on_qnx_device():
        return ""
    return "http://127.0.0.1:{0}/snapshot.json".format(HUB_PORT)


def _same_lan(host, local_ips):
    hp = str(host or "").split(".")
    if len(hp) != 4:
        return False
    for ip in local_ips or []:
        pp = str(ip or "").split(".")
        if len(pp) == 4 and pp[:3] == hp[:3]:
            return True
    return False


def _local_ipv4s():
    ips = []
    try:
        import subprocess

        out = subprocess.check_output(["ifconfig"], stderr=subprocess.STDOUT)
        if not isinstance(out, str):
            out = out.decode("utf-8", "replace")
        for line in out.splitlines():
            parts = line.split()
            if len(parts) >= 2 and parts[0] == "inet":
                ip = parts[1]
                if ip and ip != "127.0.0.1":
                    ips.append(ip)
    except Exception:
        pass
    return ips


def filter_hub_urls(forced, usb, lan, mailbox, local_ips):
    if forced:
        return [forced]
    out = []
    if usb:
        out.append(usb)
    if lan and _same_lan(_url_host(lan), local_ips):
        if lan not in out:
            out.append(lan)
    if mailbox and mailbox not in out:
        out.append(mailbox)
    if not out:
        out.append("http://169.254.0.2:{0}/snapshot.json".format(HUB_PORT))
    return out


def resolve_hub_urls(forced, usb, lan, mailbox, local_ips, last="", ports=None):
    """Transport order + short port list. last-good is first unless it is HTTPS while USB/LAN is here."""
    ports = ports or hub_ports()
    lan_ok = bool(lan and _same_lan(_url_host(lan), local_ips))
    prefer_direct = bool(usb) or lan_ok
    last = _valid_hub_url(last)
    bases = []
    if last and not (prefer_direct and last.lower().startswith("https://")):
        bases.append(last)
    for url in (forced, usb, _loopback_hub_url()):
        if url and url not in bases:
            bases.append(url)
    if lan_ok and lan not in bases:
        bases.append(lan)
    if last and last not in bases:
        bases.append(last)
    if mailbox and mailbox not in bases:
        bases.append(mailbox)
    if not bases:
        bases.append("http://169.254.0.2:{0}/snapshot.json".format(HUB_PORT))
    out = []
    for url in bases:
        for cand in expand_http_ports(url, ports):
            if cand not in out:
                out.append(cand)
    return out


def list_hub_urls():
    return resolve_hub_urls(
        os.environ.get("Q10_MONITOR_URL", "").strip(),
        _usb_hub_url(),
        os.environ.get("Q10_LAN_HUB_URL", "").strip(),
        os.environ.get("Q10_MAILBOX_URL", "").strip(),
        _local_ipv4s(),
        read_last_hub_url(),
    )


def guess_hub_url():
    urls = list_hub_urls()
    return urls[0] if urls else "http://169.254.0.2:{0}/snapshot.json".format(HUB_PORT)


_HOST_SHORT = {
    "MacBook Pro": "MBP",
    "Mac mini": "Mini",
    "Mac Mini": "Mini",
    "Demo Hub": "Demo",
}


def short_host(label):
    raw = str(label or "").strip()
    if raw in _HOST_SHORT:
        return _HOST_SHORT[raw]
    low = raw.lower()
    if low == "mac mini":
        return "Mini"
    if low == "macbook pro":
        return "MBP"
    return raw


def join_dot(parts):
    out = []
    for part in parts:
        text = str(part or "").strip()
        if text:
            out.append(text)
    return " · ".join(out)


def pad_lr(left, right, width):
    right = str(right or "")
    left = str(left or "")
    if not right:
        return clip(left, width)
    left = clip(left, max(1, width - len(right) - 1))
    gap = width - len(left) - len(right)
    if gap < 0:
        return clip(left + right, width)
    return left + (" " * gap) + right


def hub_link_kind(url):
    text = str(url or "")
    low = text.lower()
    if low.startswith("https://"):
        return t("link_mailbox")
    if "169.254." in text:
        return t("link_usb")
    if low.startswith("http://"):
        return t("link_lan")
    return ""


def fetch_timeout_for(url):
    if str(url or "").lower().startswith("https://"):
        return 12
    return 3


def fetch_first_snapshot(urls, fetch_fn=None):
    if fetch_fn is None:
        fetch_fn = fetch_snapshot
    last_err = None
    for url in urls or []:
        try:
            snap = fetch_fn(url, fetch_timeout_for(url))
            if isinstance(snap, dict) and snap.get("schema") in (SNAPSHOT_SCHEMA, "octoooo.weak.v1"):
                write_last_hub_url(url)
                return snap, url
            last_err = ValueError("bad snapshot")
        except Exception as exc:
            last_err = exc
    if last_err is None:
        raise IOError("no hub url")
    raise last_err


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
    if _UI_LANG == "en":
        if width <= 2:
            return text[:width]
        return text[: width - 2] + ".."
    if width == 1:
        return text[:1]
    return text[: width - 1] + "…"


# 结构性字符按界面语言选：中文模式用等宽黑体里验证过的 ─ · █，
# --lang en 面向无汉字字体的终端，退回纯 ASCII。
_ART = {
    "zh": {"rule": "─", "dot": "·", "fill": "█", "mark": "●"},
    "en": {"rule": "-", "dot": ".", "fill": "#", "mark": "*"},
}


def _art(key):
    return _ART.get(_UI_LANG, _ART["en"]).get(key) or "."


def rule_line(width):
    return _art("rule") * max(1, int(width))


def art_bar(pct, width):
    width = max(3, int(width))
    filled = int(round((pct / 100.0) * width))
    filled = min(width, max(0, filled))
    return _art("fill") * filled + _art("dot") * (width - filled)


def leader_lr(left, right, width):
    """左标签 …… 右值，中间点线补齐；太挤时退回空格分隔。"""
    left = str(left or "")
    right = str(right or "")
    if not right:
        return clip(left, width)
    dots = width - len(left) - len(right)
    if dots < 2:
        return pad_lr(left, right, width)
    return left + (_art("dot") * dots) + right


def quota_pct_cell(item, win):
    if item.get("octoooo_unknown"):
        return "?"
    conf = item.get("confidence")
    if conf == "error":
        return t("cell_err")
    if conf == "none" or not item.get("windows"):
        return t("cell_none")
    if conf == "unknown" and not win:
        return "?"
    if win is None:
        return t("cell_none")
    return "{0:d}%".format(win["used_pct"])


def quota_tool_cell(item, used):
    name = ascii_en_text(item.get("tool") or "?") or "?"
    if name not in used:
        used[name] = 1
        return name
    extra = ascii_en_text(item.get("label") or "")
    extra = extra.replace(name, "").strip(" ·-.")
    if extra:
        return extra
    used[name] += 1
    return "{0}{1}".format(name[:6], used[name])


def task_st(item):
    if item.get("waiting_you"):
        return t("st_you")
    if item.get("is_stale_record"):
        return t("st_old")
    key = str(item.get("state") or "")
    mapping = {
        "active": "st_run",
        "wait": "st_wait",
        "idle": "st_idle",
        "done": "st_done",
        "fail": "st_fail",
    }
    if key in mapping:
        return t(mapping[key])
    return "?"


def flatten_quota_rows(items):
    used = {}
    rows = []
    for item in items:
        tool = quota_tool_cell(item, used)
        wins = item.get("windows") or []
        if not wins:
            if item.get("octoooo_unknown"):
                rows.append((item, None, tool))
            continue
        for win in wins:
            rows.append((item, win, tool))
    return rows


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


def term_width(default=36):
    env = os.environ.get("COLUMNS")
    if env:
        try:
            return max(28, min(80, int(env)))
        except ValueError:
            pass
    try:
        import struct
        import fcntl
        import termios

        packed = fcntl.ioctl(1, termios.TIOCGWINSZ, struct.pack("HHHH", 0, 0, 0, 0))
        _rows, cols = struct.unpack("HHHH", packed)[:2]
        if cols >= 28:
            return min(80, int(cols))
    except Exception:
        pass
    return default


def header_alert(model):
    if model.get("offline"):
        return t("offline")
    if not model.get("schema_ok"):
        return t("unavailable")
    fresh = model.get("freshness") or ""
    if fresh in (t("unavailable"), t("offline"), t("error"), t("stale"), t("none")):
        return fresh
    return ""


def _page_header(model, page, width):
    title = t(page) if page in PAGES else page
    if page == "ask":
        n_ask = model.get("ask_open")
        if n_ask is None:
            n_ask = len(
                [item for item in (model.get("attention") or []) if item.get("open", True)]
            )
        if n_ask:
            title = "{0}({1})".format(title, n_ask)
    hub = model.get("hub_label") or ""
    if hub.startswith("Aindle · "):
        hub = hub[9:]
    if hub.startswith("演示"):
        hub = "演示"
    if hub.startswith("DEMO"):
        hub = "DEMO"
    alert = header_alert(model)
    left = join_dot([title, alert]) if alert else title
    left = left + " " + t("header_run", model.get("human") or 0, model.get("background") or 0)
    right = join_dot([model.get("link") or "", short_host(hub)])
    return pad_lr(left, right, width)


def _age_text(model):
    collect_val = model.get("age_label") or model.get("collected_label") or ""
    if collect_val.startswith("collect "):
        collect_val = collect_val[8:]
    elif collect_val.startswith("采集 "):
        collect_val = collect_val[3:]
    return collect_val


def _quota_geom(width):
    tool_w = 7
    win_w = 3
    pct_w = 4
    gaps = 3
    bar_w = width - tool_w - win_w - pct_w - gaps
    if bar_w < 4:
        tool_w = 6
        bar_w = width - tool_w - win_w - pct_w - gaps
    if bar_w < 3:
        bar_w = 3
        tool_w = max(4, width - win_w - pct_w - bar_w - gaps)
    return tool_w, win_w, max(3, bar_w), pct_w


def term_height(default=0):
    env = os.environ.get("LINES")
    if env:
        try:
            rows = int(env)
            if 8 <= rows <= 80:
                return rows
        except ValueError:
            pass
    try:
        import struct
        import fcntl
        import termios

        packed = fcntl.ioctl(1, termios.TIOCGWINSZ, struct.pack("HHHH", 0, 0, 0, 0))
        rows, _cols = struct.unpack("HHHH", packed)[:2]
        if rows >= 8:
            return min(80, int(rows))
    except Exception:
        pass
    return default


def page_window(items, offset, per_page):
    items = list(items or [])
    if not items:
        return [], 0, 1
    if per_page <= 0 or len(items) <= per_page:
        return items, 0, 1
    n_pages = (len(items) + per_page - 1) // per_page
    page_i = int(offset or 0) % n_pages
    start = page_i * per_page
    return items[start:start + per_page], page_i, n_pages


def task_card_lines(item, width, waiting=False, done=False):
    if done or waiting:
        st_w = 4 if _UI_LANG == "en" else 3
    else:
        st_w = 4 if _UI_LANG == "en" else 2
    if done:
        mark = " "
        st = clip(t("ask_done"), st_w).ljust(st_w)
    elif waiting:
        mark = _art("mark")
        st = clip(t("ask_open") if item.get("open", True) else task_st(item), st_w).ljust(st_w)
    else:
        mark = _art("mark") if item.get("waiting_you") else " "
        st = clip(task_st(item), st_w).ljust(st_w)
    prefix = "{0}{1} ".format(mark, st)
    indent = " " * len(prefix)
    title = ascii_en_text(item.get("title") or "", "?")
    proj = clip(ascii_en_text(item.get("project") or ""), 8)
    tail = ("· " + proj) if proj else ""
    one = width - len(prefix) - (len(tail) + 1 if tail else 0)
    if one >= 4 and len(title) <= one:
        left = prefix + title
        if tail:
            return [left + (" " * max(1, width - len(left) - len(tail))) + tail]
        return [left]
    first_room = max(1, width - len(prefix))
    line1 = (prefix + title[:first_room])[:width]
    rest = title[first_room:]
    second_room = width - len(indent) - (len(tail) + 1 if tail else 0)
    line2 = indent + rest[: max(0, second_room)]
    if tail:
        line2 = line2 + (" " * max(1, width - len(line2) - len(tail))) + tail
    return [line1[:width], line2[:width]]


def _char_kind(ch):
    if ch == " ":
        return "sp"
    if ch in "-_/·:.,;":
        return "br"
    o = ord(ch)
    if (0x2E80 <= o <= 0x9FFF) or (0xF900 <= o <= 0xFAFF) or (0x3400 <= o <= 0x4DBF):
        return "cjk"
    if ("0" <= ch <= "9") or ("A" <= ch <= "Z") or ("a" <= ch <= "z"):
        return "alnum"
    return "other"


def _clip_title_rest(rest, room):
    """截断到 room 格：优先用不小于半宽的空格/连字符/中英边界，否则硬切。"""
    if len(rest) <= room:
        return rest
    keep = max(1, room - 1)
    window = rest[:keep]
    threshold = max(4, keep // 2)
    cut = 0
    for i, ch in enumerate(window):
        kind = _char_kind(ch)
        if ch == " ":
            cand = i
        elif kind in ("br", "cjk"):
            cand = i + 1
        elif i + 1 < len(window) and kind == "alnum" and _char_kind(window[i + 1]) == "cjk":
            cand = i + 1
        else:
            continue
        if cand >= threshold:
            cut = cand
    if not cut:
        cut = keep
    piece = rest[:cut].rstrip(" -_/·:.,;…")
    if not piece:
        piece = rest[:keep]
    return piece + "…"


def short_token(raw, table, max_w):
    text = ascii_en_text(raw or "", "")
    text = (text or "").strip()
    if max_w <= 0:
        return ""
    if not text:
        return ""
    token = _lookup_abbr(text, table)
    if token is None:
        compact = text.replace(" ", "").replace("·", "").replace("-", "").replace("_", "")
        token = compact[:max_w]
    return token[:max_w]


def task_meta_suffix(item, title=""):
    proj = short_token(item.get("project") or "", _PROJ_ABBR, TASK_PROJ_W)
    agent = short_token(item.get("tool") or "", _TOOL_ABBR, TASK_AGENT_W)
    low = (title or "").strip().lower()
    if low:
        if proj and (proj.lower() == low or (_lookup_abbr(low, _PROJ_ABBR) or "").lower() == proj.lower()):
            proj = ""
        if agent and agent.lower() == low:
            agent = ""
    bits = []
    if proj:
        bits.append(proj)
    if agent:
        bits.append(agent)
    return _art("dot").join(bits)


def task_row_lines(item, width, mark_gutter=True):
    """单行任务：槽位标记 + 标题（词界截断），项目·Agent 右对齐。"""
    title = clean_task_title(item)
    suffix = task_meta_suffix(item, title)
    prefix = (_art("mark") if item.get("waiting_you") else " ") + " "
    if not mark_gutter:
        prefix = ""
    room = width - len(prefix) - (len(suffix) + 1 if suffix else 0)
    room = max(1, room)
    cell = title if len(title) <= room else _clip_title_rest(title, room)
    line = prefix + cell
    if suffix:
        line += " " * max(1, width - len(line) - len(suffix)) + suffix
    return [line[:width]]


def _pack_line_pages(blocks, usable):
    pages = []
    cur = []
    height = 0
    for block in blocks:
        h = len(block)
        if cur and usable and height + h > usable:
            pages.append(cur)
            cur = []
            height = 0
        cur.extend(block)
        height += h
    if cur or not pages:
        pages.append(cur)
    return pages


def _tasks_body(model, width, offset, budget, task_filter=None):
    if task_filter is None:
        task_filter = TASK_FILTER_DEFAULT
    items = filter_tasks(model.get("tasks") or [], task_filter)
    if not items:
        return [clip(t("no_filter_tasks"), width)]
    need_mark = any(item.get("waiting_you") for item in items)
    blocks = [task_row_lines(item, width, mark_gutter=need_mark) for item in items]
    usable = max(1, budget - 1) if budget else 0
    pages = _pack_line_pages(blocks, usable)
    n_pages = max(1, len(pages))
    page_i = int(offset or 0) % n_pages
    lines = list(pages[page_i])
    lines.append(task_nav_line(page_i, n_pages, task_filter, width))
    return lines


def _ask_body(model, width, offset, budget=0):
    items = model.get("attention") or []
    lines = []
    if not items:
        lines += ["", t("no_ask")]
        lines.append("")
        lines.append(clip(t("no_chat"), width))
        return lines
    opened = [item for item in items if item.get("open", True)]
    closed = [item for item in items if not item.get("open", True)]
    ordered = opened + closed
    extra = 3
    if any(item.get("computer_hint") for item in opened):
        extra += 1
    if any(item.get("demo") for item in opened):
        extra += 1
    per_page = len(ordered)
    if budget:
        per_page = max(1, max(1, budget - extra) // 2)
    shown, page_i, n_pages = page_window(ordered, offset, per_page)
    show_open = [item for item in shown if item.get("open", True)]
    show_done = [item for item in shown if not item.get("open", True)]
    if show_open:
        banner = _art("fill") * width
        lines.append(banner)
        for item in show_open:
            lines.extend(task_card_lines(item, width, waiting=True))
        lines.append(banner)
    for item in show_done:
        lines.extend(task_card_lines(item, width, done=True))
    if n_pages > 1:
        lines.append(clip(t("page_hint", page_i + 1, n_pages), width))
    if any(item.get("computer_hint") for item in show_open):
        lines.append(clip(t("on_computer"), width))
    if any(item.get("demo") for item in show_open):
        lines.append(clip(t("demo_ask"), width))
    lines.append("")
    lines.append(clip(t("no_chat"), width))
    return lines


def page_for_key(key):
    return _PAGE_BY_KEY.get(key)


def is_refresh_key(key):
    return key in ("t", "T", None)


def task_filter_for_key(key):
    return _TASK_FILTER_KEYS.get(key)


def task_matches_filter(item, kind):
    if kind == "all" or not kind:
        return True
    state = str(item.get("state") or "")
    if kind == "active":
        return bool(item.get("waiting_you")) or state in ("active", "wait")
    if kind == "idle":
        return state == "idle"
    if kind == "done":
        return state in ("done", "fail")
    return True


def filter_tasks(items, kind):
    out = []
    for item in items or []:
        if task_matches_filter(item, kind):
            out.append(item)
    return out


def _lookup_abbr(text, table):
    if text in table:
        return table[text]
    low = text.lower()
    for key, val in table.items():
        if key.lower() == low:
            return val
    best = None
    for key, val in table.items():
        kl = key.lower()
        if len(kl) < 3:
            continue
        if low.startswith(kl):
            if best is None or len(kl) > len(best[0]):
                best = (kl, val)
    if best:
        return best[1]
    return None


def abbrev_token(raw, width, table):
    text = ascii_en_text(raw or "", "")
    text = (text or "").strip()
    if width <= 0:
        return ""
    if not text:
        return "-".ljust(width)[:width]
    token = _lookup_abbr(text, table)
    if token is None:
        compact = text.replace(" ", "").replace("·", "").replace("-", "").replace("_", "")
        token = compact[:width]
    return token[:width].ljust(width)


def clean_task_title(item):
    title = ascii_en_text(item.get("title") or "", "?")
    tool = ascii_en_text(item.get("tool") or "")
    proj = ascii_en_text(item.get("project") or "")
    for prefix in (
        "{0} · {1}".format(tool, proj) if tool and proj else "",
        (tool + " · ") if tool else "",
        (proj + " · ") if proj else "",
    ):
        if prefix and title.startswith(prefix):
            title = title[len(prefix):].strip(" ·")
            break
    for name in (proj, tool):
        if name and title.lower().startswith(name.lower()):
            rest = title[len(name):]
            if rest and rest[0].isalnum() and ord(rest[0]) < 128:
                continue
            rest = rest.strip(" ·:-—-")
            if rest:
                title = rest
                break
    # 首词与项目/工具的缩写同源（如 Contexpect≡ContextView→Ctx）也剥掉。
    parts = title.split(" ", 1)
    if len(parts) == 2 and parts[1].strip(" ·:-—-"):
        for raw, table in ((proj, _PROJ_ABBR), (tool, _TOOL_ABBR)):
            if not raw:
                continue
            tok = _lookup_abbr(parts[0], table)
            want = _lookup_abbr(raw, table) or raw
            if tok and want and tok.lower() == want.lower():
                title = parts[1].strip(" ·:-—-")
                break
    return title or proj or tool or "?"


def task_filter_bar(kind):
    parts = []
    for key, name in (("a", "active"), ("i", "idle"), ("d", "done"), ("u", "all")):
        label = t("flt_" + name)
        mark = key.upper() if kind == name else key
        parts.append(mark + label)
    return " ".join(parts)


def task_nav_line(page_i, n_pages, kind, width):
    return clip(
        t("page_hint", page_i + 1, n_pages) + " · " + task_filter_bar(kind),
        width,
    )


def ask_jump(seen_ids, model):
    """刷新后出现新的待处理 id 才跳页；清空后重置。返回 (是否跳, 新已见集合)。"""
    ids = set()
    for item in model.get("attention") or []:
        if item.get("open") is False:
            continue
        iid = str(item.get("id") or "")
        if iid:
            ids.add(iid)
    if ids and not ids.issubset(seen_ids):
        return True, ids
    return False, ids


def _quota_body(model, width, offset, budget):
    items = model.get("quota_items") or []
    lines = []
    tail = []
    spends = model.get("spend_items") or []
    if spends:
        tail.append(rule_line(width))
        for item in spends:
            amount = ascii_en_text(item.get("label") or "") or (item.get("label") or "")
            tool = clip(ascii_en_text(item.get("tool") or "") or "?", 8)
            tail.append(leader_lr(tool, amount, width))
    if not items:
        lines.append(t("no_quota"))
    else:
        tool_w, win_w, bar_w, pct_w = _quota_geom(width)
        flat = flatten_quota_rows(items)
        per_page = len(flat)
        if budget:
            per_page = max(1, budget - len(tail) - 1)
        ordered, page_i, n_pages = page_window(flat, offset, per_page)
        hidden = model.get("hidden_quota") or 0
        prev = None
        for item, win, tool in ordered:
            if tool == prev:
                name = " " * tool_w
            else:
                name = clip(tool, tool_w).ljust(tool_w)
            prev = tool
            if win is None:
                win_s = "-".ljust(win_w)
                bar_s = _art("dot") * bar_w
                pct = clip(quota_pct_cell(item, None), pct_w).rjust(pct_w)
            else:
                win_s = clip(win.get("key_label") or win.get("key") or "-", win_w).ljust(win_w)
                bar_s = art_bar(win["used_pct"], bar_w)
                pct = clip(quota_pct_cell(item, win), pct_w).rjust(pct_w)
            # 行宽由 _quota_geom 精确拼出，不能再过 clip（clip 会 strip 掉缩进）。
            lines.append("{0} {1} {2} {3}".format(name, win_s, bar_s, pct))
        if n_pages > 1:
            lines.append(clip(t("page_hint", page_i + 1, n_pages), width))
        elif hidden:
            lines.append(clip(t("more_n", hidden) + " · j/k", width))
    lines.extend(tail)
    return lines


def enforce_projection_lease(model, now=None):
    if model.get("octoooo_readonly") and model.get("schema_ok"):
        expires = parse_iso(model.get("valid_until"))
        if expires is None or expires <= (now or utcnow()):
            return octoooo_unavailable("Octoooo 授权画面已过期，请刷新")
    return model


def render_page(model, page, width=36, offset=0, height=0, task_filter=None):
    model = enforce_projection_lease(model)
    width = max(28, int(width or 36))
    budget = max(0, int(height) - 5) if height else 0
    if task_filter is None:
        task_filter = TASK_FILTER_DEFAULT
    if page == "quota":
        body = _quota_body(model, width, offset, budget)
    elif page == "tasks":
        body = _tasks_body(model, width, offset, budget, task_filter)
    elif page == "ask":
        body = _ask_body(model, width, offset, budget)
    else:
        body = []
    if budget and len(body) > budget:
        body = body[:budget]
    lines = [_page_header(model, page, width), rule_line(width)]
    lines.extend(body)
    lines.append(rule_line(width))
    foot = t("footer")
    waiting = model.get("waiting") or 0
    if waiting:
        needle = t("ask")
        idx = foot.rfind(needle)
        if idx >= 0:
            foot = foot[:idx] + "{0}({1})".format(needle, waiting) + foot[idx + len(needle):]
    lines.append(clip(foot, width))
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
    p = argparse.ArgumentParser(description="Q10 键盘监视器")
    p.add_argument(
        "--url",
        default="",
        help="强制这一份快照 URL；不写则 last-good → USB/LAN 端口探测 → 信箱",
    )
    p.add_argument("--once", action="store_true", help="打一屏后退出")
    p.add_argument("--all", action="store_true", help="三页都打（隐含 --once）")
    p.add_argument("--watch", action="store_true", help="循环刷新")
    p.add_argument("--page", choices=PAGES, default="quota")
    p.add_argument("--demo", action="store_true", help="显式演示数据，不会自动回落")
    p.add_argument("--file", default="", help="从 JSON 文件读快照")
    p.add_argument("--source-times", default="", help="可选 sidecar JSON")
    p.add_argument("--interval", type=int, default=10)
    p.add_argument("--width", type=int, default=0)
    p.add_argument(
        "--lang",
        choices=("en", "zh"),
        default="zh",
        help="界面语言，默认中文（任务标题本身也可能是中文）",
    )
    return p


def obtain_snapshot(args):
    if args.demo:
        snap = load_demo_snapshot()
        return overlay_source_times(snap, load_source_times(args.source_times)), None
    if args.file:
        snap = load_json_file(args.file)
        return overlay_source_times(snap, load_source_times(args.source_times)), None
    if args.url:
        urls = [args.url]
    else:
        urls = list_hub_urls()
    snap, url = fetch_first_snapshot(urls)
    overlay = load_source_times(args.source_times or default_source_times_path())
    return overlay_source_times(snap, overlay), url


def main(argv=None):
    args = build_parser().parse_args(argv)
    set_ui_lang(args.lang)
    if args.all:
        args.once = True
    width = args.width or term_width()
    height = term_height()
    page = args.page
    offset = 0
    task_filter = TASK_FILTER_DEFAULT
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
                lang=args.lang,
            )
            remember_attention(model)
            return model, None
        except Exception as exc:
            return None, exc

    model, err = pull()
    if model is None:
        model = unavailable_model(t("fetch_fail", err))
        last = None
        if args.once:
            if args.all:
                for name in PAGES:
                    write_out(render_page(model, name, width=width, height=height, task_filter=task_filter))
            else:
                write_out(render_page(model, page, width=width, height=height, task_filter=task_filter))
            return 2
    else:
        last = model

    if args.once:
        pages = PAGES if args.all else (page,)
        for name in pages:
            write_out(render_page(model, name, width=width, offset=offset, height=height, task_filter=task_filter))
        return 0 if model.get("schema_ok") else 2

    # 启动时已有待处理：直接落在待处理页。
    seen_ask = set()
    jump, seen_ask = ask_jump(seen_ask, last or model)
    if jump:
        page = "ask"

    interval = max(2, int(args.interval))
    while True:
        shown = enforce_projection_lease(last or model)
        if last is not None:
            last = shown
        if sys.stdout.isatty():
            clear_screen()
        write_out(render_page(shown, page, width=width, offset=offset, height=height, task_filter=task_filter))
        sys.stdout.flush()
        key = None
        wait = interval
        if shown.get("octoooo_readonly") and shown.get("schema_ok"):
            expires = parse_iso(shown.get("valid_until"))
            if expires is not None:
                wait = min(wait, max(0.01, (expires - utcnow()).total_seconds()))
        if shown.get("offline"):
            wait = min(interval, 4)
        if interactive and sys.stdin.isatty():
            key = read_key(wait)
        else:
            time.sleep(wait)
            key = None
        if key in ("x", "X", "q", "Q", "\x03"):
            return 0
        nxt_page = page_for_key(key)
        if nxt_page:
            page, offset = nxt_page, 0
            continue
        nxt_filter = task_filter_for_key(key)
        if nxt_filter and page == "tasks":
            task_filter = nxt_filter
            offset = 0
            continue
        if key in ("j", "J", "n"):
            offset += 1
            continue
        if key in ("k", "K", "p"):
            offset -= 1
            continue
        if is_refresh_key(key):
            nxt, err = pull()
            if nxt is not None:
                last = nxt
                # 刷新发现新的待处理：自动跳到待处理页。
                jump, seen_ask = ask_jump(seen_ask, nxt)
                if jump:
                    page, offset = "ask", 0
            elif last is not None:
                last = mark_offline(last)
            else:
                last = unavailable_model(t("fetch_fail", err))


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(0)

