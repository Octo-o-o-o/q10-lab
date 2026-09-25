#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Adapter rules aligned with the ESP32 round-screen host/adapter.py."""
import json
import os
import tempfile
import unittest
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from datetime import datetime

from q10_monitor import (
    SNAPSHOT_SCHEMA,
    _mailbox_token,
    adapt,
    ask_jump,
    build_parser,
    expand_http_ports,
    fetch_first_snapshot,
    filter_hub_urls,
    guess_hub_url,
    hub_link_kind,
    hub_ports,
    mark_offline,
    header_alert,
    merge_ask_history,
    overlay_source_times,
    page_window,
    quota_item_visible,
    read_last_hub_url,
    remember_attention,
    _PROJ_ABBR,
    _TOOL_ABBR,
    abbrev_token,
    filter_tasks,
    short_token,
    task_card_lines,
    task_filter_for_key,
    task_row_lines,
    render_page,
    replace_url_port,
    resolve_hub_urls,
    set_ui_lang,
    used_pct,
    is_refresh_key,
    page_for_key,
    window_key_label,
    write_last_hub_url,
)

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(HERE, "fixtures")
NOW = datetime(2026, 9, 5, 12, 0, 0)


def _load(name):
    with open(os.path.join(FIXTURES, name), "rb") as fh:
        return json.loads(fh.read().decode("utf-8"))


class AdapterTests(unittest.TestCase):
    def setUp(self):
        set_ui_lang("zh")
        fd, self._last_file = tempfile.mkstemp()
        os.close(fd)
        os.remove(self._last_file)
        self._old_last = os.environ.get("Q10_HUB_LAST_FILE")
        self._old_ports = os.environ.get("Q10_HUB_PORTS")
        self._old_aindle = os.environ.get("AINDLE_PORT")
        os.environ["Q10_HUB_LAST_FILE"] = self._last_file
        os.environ.pop("Q10_HUB_PORTS", None)
        os.environ.pop("AINDLE_PORT", None)

    def tearDown(self):
        if self._old_last is None:
            os.environ.pop("Q10_HUB_LAST_FILE", None)
        else:
            os.environ["Q10_HUB_LAST_FILE"] = self._old_last
        if self._old_ports is None:
            os.environ.pop("Q10_HUB_PORTS", None)
        else:
            os.environ["Q10_HUB_PORTS"] = self._old_ports
        if self._old_aindle is None:
            os.environ.pop("AINDLE_PORT", None)
        else:
            os.environ["AINDLE_PORT"] = self._old_aindle
        if os.path.isfile(self._last_file):
            os.remove(self._last_file)

    def test_pct_is_used_not_remaining(self):
        self.assertEqual(used_pct(64), 64)
        self.assertIsNone(used_pct(None))
        self.assertIsNone(used_pct("x"))
        model = adapt(_load("snapshot_demo.json"), now=NOW, demo=True, quota_limit=10)
        claude = next(i for i in model["quota_items"] if i["tool"] == "Claude")
        self.assertTrue(claude["windows"][0]["used_label"].startswith("已用"))
        top = max(claude["windows"], key=lambda w: w["used_pct"])
        self.assertEqual(top["used_pct"], 64)
        self.assertNotIn("剩余", top["used_label"])

    def test_spend_not_mixed_as_quota(self):
        model = adapt(_load("snapshot_demo.json"), now=NOW, demo=True)
        self.assertFalse(any(i["kind"] == "spend" for i in model["quota_items"]))
        self.assertTrue(
            any(i["kind"] == "spend" and "非订阅限额" in i["note"] for i in model["spend_items"])
        )

    def test_error_and_missing_are_not_zero(self):
        model = adapt(_load("snapshot_demo.json"), now=NOW, demo=True, quota_limit=10)
        tools = [i["tool"] for i in model["quota_items"]]
        self.assertNotIn("Gemini", tools)
        self.assertNotIn("GLM", tools)
        self.assertTrue(all(quota_item_visible(i) for i in model["quota_items"]))
        kimi = next(i for i in model["quota_items"] if i["tool"] == "Kimi")
        self.assertTrue(any(w["used_pct"] == 0 and w["used_label"] == "已用 0%" for w in kimi["windows"]))

    def test_stale_host_excluded_from_current_stats(self):
        model = adapt(_load("snapshot_demo.json"), now=NOW, demo=True, task_limit=10)
        self.assertEqual(model["freshness"], "新鲜")
        self.assertEqual(model["waiting"], 1)
        self.assertEqual(model["human"], 2)
        self.assertTrue(any(t["octoooo"] and not t["is_stale_record"] for t in model["tasks"]))
        stale = next(t for t in model["tasks"] if t["host_id"] == "old-host")
        self.assertTrue(stale["is_stale_record"])
        self.assertEqual(stale["state_label"], "旧记录")
        self.assertFalse(stale["waiting_you"])

    def test_all_stale_snapshot_is_old_not_live(self):
        model = adapt(_load("snapshot_stale.json"), now=NOW)
        self.assertEqual(model["freshness"], "旧数据")
        self.assertEqual(model["waiting"], 0)
        self.assertEqual(model["human"], 0)
        self.assertTrue(all(t["is_stale_record"] for t in model["tasks"]))
        self.assertTrue(all(t["state_label"] == "旧记录" for t in model["tasks"]))
        self.assertIn("不冒充实时", model["note"])
        self.assertIn("采集", model["collected_label"])
        self.assertIn("Hub生成", model["hub_generated_label"])

    def test_wait_badge_requires_direct_needs_input(self):
        model = adapt(_load("snapshot_demo.json"), now=NOW, demo=True, task_limit=10)
        waiting = [t for t in model["tasks"] if t["waiting_you"]]
        self.assertEqual(len(waiting), 1)
        self.assertEqual(waiting[0]["title"], "需要你确认下一步")
        fake = next(t for t in model["tasks"] if "derived wait" in t["title"])
        self.assertFalse(fake["waiting_you"])
        self.assertNotEqual(fake["state_label"], "等你")

    def test_offline_keeps_old_and_relabels(self):
        model = adapt(_load("snapshot_demo.json"), now=NOW, demo=True)
        offline = mark_offline(model)
        self.assertTrue(offline["offline"])
        self.assertEqual(offline["freshness"], "离线")
        self.assertIn("保留旧画面", offline["note"])
        self.assertEqual(len(offline["quota_items"]), len(model["quota_items"]))

    def test_bad_schema_unavailable(self):
        model = adapt({"schema": "nope"}, now=NOW)
        self.assertFalse(model["schema_ok"])
        self.assertEqual(model["freshness"], "不可用")
        self.assertEqual(model["quota_items"], [])

    def test_demo_flag_is_explicit(self):
        live_shaped = adapt(_load("snapshot_demo.json"), now=NOW, demo=False)
        self.assertFalse(live_shaped["demo"])
        self.assertNotIn("演示", live_shaped["source"])
        demo = adapt(_load("snapshot_demo.json"), now=NOW, demo=True)
        self.assertTrue(demo["demo"])
        self.assertIn("演示", demo["source"])

    def test_windows_not_summed(self):
        model = adapt(_load("snapshot_demo.json"), now=NOW, demo=True, quota_limit=10)
        cursor = next(i for i in model["quota_items"] if i["tool"] == "Cursor")
        total = sum(w["used_pct"] for w in cursor["windows"])
        shown = max(w["used_pct"] for w in cursor["windows"])
        self.assertEqual(shown, 100)
        self.assertGreater(total, shown)

    def test_stale_host_only_subscription_not_fresh(self):
        snap = _load("snapshot_demo.json")
        snap["subscriptions"].append(
            {
                "id": "stale-only",
                "tool": "StaleOnly",
                "label": "Stale Host Quota",
                "kind": "quota",
                "source": "local",
                "confidence": "live",
                "hostIds": ["old-host"],
                "windows": [{"key": "5h", "pct": 88, "resetsAt": "2026-09-05T16:00:00.000Z"}],
            }
        )
        model = adapt(snap, now=NOW, demo=True, quota_limit=20)
        live = next(i for i in model["quota_items"] if i["tool"] == "Claude")
        self.assertEqual(live["status_label"], "新鲜")
        item = next(i for i in model["quota_items"] if i["tool"] == "StaleOnly")
        self.assertEqual(item["status_label"], "旧数据")
        self.assertEqual(item["windows"][0]["used_pct"], 88)

    def test_mixed_missing_unknown_hostids_not_forged(self):
        snap = _load("snapshot_demo.json")
        snap["subscriptions"].extend(
            [
                {
                    "id": "mixed-hosts",
                    "tool": "Mixed",
                    "label": "Mixed Hosts",
                    "kind": "quota",
                    "source": "local",
                    "confidence": "live",
                    "hostIds": ["desk", "old-host"],
                    "windows": [{"key": "5h", "pct": 41}],
                },
                {
                    "id": "missing-hosts",
                    "tool": "MissingHosts",
                    "label": "Missing Hosts",
                    "kind": "quota",
                    "source": "local",
                    "confidence": "live",
                    "windows": [{"key": "5h", "pct": 17}],
                },
                {
                    "id": "ghost-hosts",
                    "tool": "Ghost",
                    "label": "Unknown Hosts",
                    "kind": "quota",
                    "source": "local",
                    "confidence": "live",
                    "hostIds": ["ghost"],
                    "windows": [{"key": "5h", "pct": 9}],
                },
                {
                    "id": "stale-error",
                    "tool": "StaleError",
                    "label": "Stale Error",
                    "kind": "quota",
                    "source": "local",
                    "confidence": "error",
                    "hostIds": ["old-host"],
                    "windows": [{"key": "5h", "pct": 3}],
                },
            ]
        )
        model = adapt(snap, now=NOW, demo=True, quota_limit=20)
        mixed = next(i for i in model["quota_items"] if i["tool"] == "Mixed")
        missing = next(i for i in model["quota_items"] if i["tool"] == "MissingHosts")
        ghost = next(i for i in model["quota_items"] if i["tool"] == "Ghost")
        tools = [i["tool"] for i in model["quota_items"]]
        self.assertNotIn("StaleError", tools)
        self.assertEqual(mixed["status_label"], "旧数据")
        self.assertEqual(mixed["windows"][0]["used_pct"], 41)
        self.assertEqual(missing["status_label"], "未知")
        self.assertEqual(missing["windows"][0]["used_pct"], 17)
        self.assertEqual(ghost["status_label"], "未知")
        self.assertEqual(ghost["windows"][0]["used_pct"], 9)

    def test_overlay_source_times_binds_collected_at(self):
        snap = _load("snapshot_demo.json")
        overlay = {
            "schema": "octoooo-mini.source-times.v1",
            "sources": {"claude-demo": {"collectedAt": "2026-09-05T11:58:00.000Z"}},
        }
        merged = overlay_source_times(snap, overlay)
        claude = next(s for s in merged["subscriptions"] if s["id"] == "claude-demo")
        self.assertEqual(claude["collectedAt"], "2026-09-05T11:58:00.000Z")

    def test_cli_default_is_chinese(self):
        self.assertEqual(build_parser().get_default("lang"), "zh")
        self.assertEqual(build_parser().get_default("page"), "quota")

    def test_q10_letter_keys_match_numbers(self):
        self.assertEqual(page_for_key("1"), "quota")
        self.assertEqual(page_for_key("w"), "quota")
        self.assertEqual(page_for_key("W"), "quota")
        self.assertEqual(page_for_key("2"), "tasks")
        self.assertEqual(page_for_key("e"), "tasks")
        self.assertEqual(page_for_key("3"), "ask")
        self.assertEqual(page_for_key("r"), "ask")
        self.assertEqual(page_for_key("4"), "ask")
        self.assertEqual(page_for_key("s"), "ask")
        self.assertIsNone(page_for_key("t"))
        self.assertTrue(is_refresh_key("t"))
        self.assertTrue(is_refresh_key("T"))
        self.assertTrue(is_refresh_key(None))
        self.assertFalse(is_refresh_key("r"))

    def test_chinese_tasks_and_quota_copy(self):
        model = adapt(_load("snapshot_demo.json"), now=NOW, demo=True, quota_limit=10)
        tasks = render_page(model, "tasks", width=42)
        quota = render_page(model, "quota", width=42)
        self.assertIn("任务", tasks)
        self.assertIn("进行", tasks)
        self.assertIn("后台", tasks)
        self.assertNotIn("新鲜", tasks)
        self.assertNotIn("采集", tasks)
        self.assertNotIn("人手", tasks)
        self.assertNotIn("ASK/", tasks)
        self.assertNotIn("+--", tasks)
        self.assertNotIn("Gemini", quota)
        self.assertNotIn("GLM", quota)
        self.assertNotIn("| ERR|", quota)
        self.assertNotIn("+--", quota)
        self.assertIn("t刷新", tasks)
        self.assertIn("x关闭", tasks)

    def test_window_keys_ascii_in_english(self):
        set_ui_lang("en")
        self.assertEqual(window_key_label("三方"), "3rd")
        self.assertEqual(window_key_label("自有"), "own")
        self.assertEqual(window_key_label("本周"), "week")
        self.assertEqual(window_key_label("月"), "mo")
        self.assertEqual(window_key_label("5h"), "5h")
        set_ui_lang("zh")
        self.assertEqual(window_key_label("三方"), "三方")

    def test_english_quota_table_not_zero_for_errors(self):
        set_ui_lang("en")
        model = adapt(_load("snapshot_demo.json"), now=NOW, demo=True, quota_limit=10, lang="en")
        page = render_page(model, "quota", width=42)
        self.assertIn("3rd", page)
        self.assertIn("own", page)
        self.assertNotIn("Gemini", page)
        self.assertNotIn("GLM", page)
        self.assertIn("DeepSeek", page)
        self.assertNotIn("+--", page)
        self.assertNotIn("collect failed", page)
        tools = [i["tool"] for i in model["quota_items"]]
        self.assertNotIn("Gemini", tools)

    def test_english_status_and_tasks_are_tables(self):
        model = adapt(_load("snapshot_demo.json"), now=NOW, demo=True, task_limit=10, lang="en")
        tasks = render_page(model, "tasks", width=42)
        ask = render_page(model, "ask", width=42)
        self.assertIn("run", tasks)
        self.assertIn("bg", tasks)
        self.assertNotIn("fresh", tasks.lower())
        self.assertIn("CLD", tasks)
        self.assertIn("Arun", tasks)
        self.assertNotIn("+--", tasks)
        self.assertIn("1 QUOTA  2 TASK  3 ASK", tasks)

    def test_mailbox_token_skips_unreadable(self):
        fd, path = tempfile.mkstemp()
        os.write(fd, b"secret\n")
        os.close(fd)
        os.chmod(path, 0)
        old_file = os.environ.get("Q10_MAILBOX_TOKEN_FILE")
        old_tok = os.environ.get("Q10_MAILBOX_TOKEN")
        os.environ["Q10_MAILBOX_TOKEN_FILE"] = path
        os.environ.pop("Q10_MAILBOX_TOKEN", None)
        try:
            self.assertEqual(_mailbox_token(), "")
        finally:
            if old_file is None:
                os.environ.pop("Q10_MAILBOX_TOKEN_FILE", None)
            else:
                os.environ["Q10_MAILBOX_TOKEN_FILE"] = old_file
            if old_tok is None:
                os.environ.pop("Q10_MAILBOX_TOKEN", None)
            else:
                os.environ["Q10_MAILBOX_TOKEN"] = old_tok
            os.chmod(path, 0o600)
            os.remove(path)

    def test_guess_hub_url_forced_beats_mailbox(self):
        old = {}
        for key in ("Q10_MONITOR_URL", "Q10_LAN_HUB_URL", "Q10_MAILBOX_URL"):
            old[key] = os.environ.get(key)
        os.environ["Q10_MONITOR_URL"] = "http://forced.test/snapshot.json"
        os.environ["Q10_LAN_HUB_URL"] = "http://lan.test/snapshot.json"
        os.environ["Q10_MAILBOX_URL"] = "https://mb.test/snapshot.json"
        try:
            self.assertEqual(guess_hub_url(), "http://forced.test/snapshot.json")
        finally:
            for key, value in old.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_filter_hub_urls_skips_lan_off_subnet(self):
        usb = "http://169.254.0.2:8787/snapshot.json"
        lan = "http://192.168.31.132:8787/snapshot.json"
        mailbox = "https://mb.test/snapshot.json"
        home = filter_hub_urls("", usb, lan, mailbox, ["169.254.0.1", "192.168.31.106"])
        self.assertEqual(home, [usb, lan, mailbox])
        away = filter_hub_urls("", "", lan, mailbox, ["10.20.30.40"])
        self.assertEqual(away, [mailbox])
        wifi_only = filter_hub_urls("", "", lan, mailbox, ["192.168.31.106"])
        self.assertEqual(wifi_only, [lan, mailbox])

    def test_fetch_first_snapshot_fails_over(self):
        good = {"schema": SNAPSHOT_SCHEMA, "hosts": []}
        calls = []

        def fake(url, timeout):
            calls.append((url, timeout))
            if url.endswith("/dead"):
                raise IOError("down")
            return good

        snap, url = fetch_first_snapshot(
            ["http://x/dead", "http://x/ok"], fetch_fn=fake
        )
        self.assertEqual(url, "http://x/ok")
        self.assertEqual(snap["schema"], SNAPSHOT_SCHEMA)
        self.assertEqual([c[0] for c in calls], ["http://x/dead", "http://x/ok"])

    def test_hub_link_kind(self):
        set_ui_lang("zh")
        self.assertEqual(hub_link_kind("http://169.254.0.2:8787/snapshot.json"), "USB")
        self.assertEqual(hub_link_kind("http://192.168.31.132:8787/snapshot.json"), "局域网")
        self.assertEqual(hub_link_kind("https://mb.test/snapshot.json"), "信箱")

    def test_hub_ports_keeps_aindle_then_legacy(self):
        self.assertEqual(hub_ports(""), [8787, 8790])
        self.assertEqual(hub_ports("9000"), [9000, 8787, 8790])
        os.environ["AINDLE_PORT"] = "9100"
        self.assertEqual(hub_ports(), [9100, 8787, 8790])

    def test_expand_http_ports_skips_https(self):
        url = "https://mb.test/snapshot.json"
        self.assertEqual(expand_http_ports(url), [url])

    def test_expand_http_ports_adds_sibling(self):
        url = "http://169.254.0.2:8787/snapshot.json"
        out = expand_http_ports(url, ports=(8787, 8790))
        self.assertEqual(out[0], url)
        self.assertEqual(out[1], "http://169.254.0.2:8790/snapshot.json")
        self.assertEqual(
            replace_url_port("http://192.168.1.10:8790/snapshot.json", 8787),
            "http://192.168.1.10:8787/snapshot.json",
        )

    def test_resolve_last_dead_port_then_sibling(self):
        last = "http://169.254.0.2:8790/snapshot.json"
        usb = "http://169.254.0.2:8787/snapshot.json"
        out = resolve_hub_urls("", usb, "", "", ["169.254.0.1"], last=last, ports=(8787, 8790))
        self.assertEqual(out[0], last)
        self.assertEqual(out[1], usb)

    def test_resolve_skips_mailbox_last_when_usb_present(self):
        last = "https://mb.test/snapshot.json"
        usb = "http://169.254.0.2:8787/snapshot.json"
        mailbox = last
        out = resolve_hub_urls(
            "", usb, "", mailbox, ["169.254.0.1"], last=last, ports=(8787,)
        )
        self.assertEqual(out[0], usb)
        self.assertIn(mailbox, out)
        self.assertGreater(out.index(mailbox), 0)

    def test_last_hub_roundtrip_and_reject_junk(self):
        self.assertEqual(read_last_hub_url(), "")
        self.assertTrue(write_last_hub_url("http://169.254.0.2:8787/snapshot.json"))
        self.assertEqual(read_last_hub_url(), "http://169.254.0.2:8787/snapshot.json")
        self.assertFalse(write_last_hub_url("not-a-url"))
        self.assertEqual(read_last_hub_url(), "http://169.254.0.2:8787/snapshot.json")

    def test_fetch_first_snapshot_writes_last(self):
        good = {"schema": SNAPSHOT_SCHEMA, "hosts": []}

        def fake(url, timeout):
            if url.endswith("/ok"):
                return good
            raise IOError("down")

        snap, url = fetch_first_snapshot(
            ["http://x/dead", "http://x/ok"], fetch_fn=fake
        )
        self.assertEqual(url, "http://x/ok")
        self.assertEqual(snap["schema"], SNAPSHOT_SCHEMA)
        self.assertEqual(read_last_hub_url(), "http://x/ok")

    def test_layout_rules_and_width(self):
        model = adapt(_load("snapshot_demo.json"), now=NOW, demo=True, quota_limit=10)
        for page in ("quota", "tasks", "ask"):
            out = render_page(model, page, width=36)
            lines = out.splitlines()
            self.assertEqual(lines[0], lines[0][:36])
            self.assertEqual(lines[1], "─" * 36)
            self.assertEqual(lines[-2], "─" * 36)
            for ln in lines:
                self.assertLessEqual(len(ln), 36)
        quota = render_page(model, "quota", width=36)
        self.assertIn("█", quota)
        tasks = render_page(model, "tasks", width=36)
        self.assertIn("·", tasks)

    def test_ask_banner_and_footer_badge(self):
        model = adapt(_load("snapshot_demo.json"), now=NOW, demo=True)
        ask = render_page(model, "ask", width=36)
        self.assertIn("█" * 36, ask)
        self.assertIn("待处理(", ask)
        self.assertIn("●", ask)
        stale = adapt(_load("snapshot_stale.json"), now=NOW)
        calm = render_page(stale, "ask", width=36)
        self.assertNotIn("█" * 36, calm)
        self.assertIn("没有待处理", calm)

    def test_ask_jump_only_on_new_items(self):
        model = adapt(_load("snapshot_demo.json"), now=NOW, demo=True)
        jump, seen = ask_jump(set(), model)
        self.assertTrue(jump)
        jump2, seen2 = ask_jump(seen, model)
        self.assertFalse(jump2)
        self.assertEqual(seen, seen2)
        empty = adapt(_load("snapshot_stale.json"), now=NOW)
        jump3, seen3 = ask_jump(seen2, empty)
        self.assertFalse(jump3)
        self.assertEqual(seen3, set())
        model2 = dict(model)
        model2["attention"] = list(model["attention"]) + [{"id": "new-1", "title": "x"}]
        jump4, _seen4 = ask_jump(seen, model2)
        self.assertTrue(jump4)

    def test_height_trims_rows_with_hint(self):
        model = adapt(_load("snapshot_demo.json"), now=NOW, demo=True)
        out = render_page(model, "quota", width=36, height=10)
        self.assertIn("第", out)
        self.assertLessEqual(len(out.splitlines()), 10)
        full = render_page(model, "quota", width=36)
        self.assertGreater(len(full.splitlines()), 10)

    def test_english_layout_is_ascii(self):
        set_ui_lang("en")
        model = adapt(_load("snapshot_demo.json"), now=NOW, demo=True, lang="en")
        out = render_page(model, "quota", width=42)
        lines = out.splitlines()
        self.assertEqual(lines[1], "-" * 42)
        self.assertIn("#", out)
        set_ui_lang("zh")

    def test_header_hides_fresh_shows_alert(self):
        model = adapt(_load("snapshot_demo.json"), now=NOW, demo=True)
        self.assertEqual(header_alert(model), "")
        head = render_page(model, "tasks", width=42).splitlines()[0]
        self.assertIn("进行", head)
        self.assertIn("后台", head)
        self.assertNotIn("新鲜", head)
        offline = mark_offline(model)
        self.assertEqual(header_alert(offline), "离线")
        bad = adapt({"schema": "nope"}, now=NOW)
        self.assertEqual(header_alert(bad), "不可用")

    def test_task_row_abbrev_and_wrap(self):
        item = {
            "title": "为humanusage项目重新设计官网并部署至Cloudflare",
            "project": "YouUsage",
            "tool": "ZCode",
            "state": "active",
            "waiting_you": False,
        }
        lines = task_row_lines(item, 36)
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].startswith("  为"))
        self.assertFalse(lines[0].startswith("ZCD"))
        self.assertTrue(lines[0].endswith("YU·ZCD"))
        self.assertFalse(lines[0].endswith("Clo"))
        self.assertIn("…", lines[0])
        self.assertLessEqual(len(lines[0]), 36)
        short = task_row_lines(
            {
                "title": "审查并优化设备项目",
                "project": "waveshare-ESP32-S3-Touch-AMOLED-1.75C",
                "tool": "Codex",
                "state": "active",
            },
            36,
        )
        self.assertEqual(len(short), 1)
        self.assertEqual(short[0], "  审查并优化设备项目".ljust(30) + "WS·CDX")
        wrapped = task_row_lines(
            {
                "title": "(2) BlackBerry Q10 development lab",
                "project": "lab",
                "tool": "Cursor",
                "state": "idle",
            },
            36,
        )
        self.assertEqual(len(wrapped), 1)
        self.assertTrue(wrapped[0].startswith("  (2) BlackBerry"))
        self.assertTrue(wrapped[0].endswith("lab·CUR"))
        dupe = task_row_lines(
            {"title": "OctoDesk", "project": "OctoDesk", "tool": "Claude", "state": "active"},
            36,
        )
        self.assertEqual(dupe[0], "  OctoDesk".ljust(33) + "CLD")
        bare = task_row_lines(
            {
                "title": "Contexpect 接续实施下一阶段",
                "project": "Contexpect",
                "tool": "Claude",
                "state": "active",
                "waiting_you": True,
            },
            36,
        )
        self.assertEqual(bare[0], "● 接续实施下一阶段".ljust(29) + "Ctx·CLD")
        alias = task_row_lines(
            {
                "title": "Contexpect 接续实施下一阶段",
                "project": "ContextView",
                "tool": "Claude",
                "state": "active",
                "waiting_you": True,
            },
            36,
        )
        self.assertEqual(alias[0], bare[0])
        marked = task_row_lines(
            {"title": "Fix chat create request lost", "project": "OctoDesk", "tool": "Grok",
             "state": "active", "waiting_you": True},
            36,
        )
        self.assertEqual(marked[0], "● Fix chat create…".ljust(23) + "OctoDesk·GROK")
        self.assertEqual(short_token("Grok", _TOOL_ABBR, 4), "GROK")
        self.assertEqual(short_token("OctoDesk-t115-phase0", _PROJ_ABBR, 8), "OctoDesk")
        self.assertEqual(abbrev_token("OctoWorkFlow", 4, _PROJ_ABBR), "OWF ")
        self.assertEqual(abbrev_token("ContextView", 4, _PROJ_ABBR), "Ctx ")
        self.assertEqual(
            abbrev_token("waveshare-ESP32-S3-Touch-AMOLED-1.75C", 4, _PROJ_ABBR),
            "WS  ",
        )
        self.assertEqual(task_filter_for_key("a"), "active")
        shown = filter_tasks(
            [{"state": "active"}, {"state": "idle"}, {"state": "done"}],
            "active",
        )
        self.assertEqual([i["state"] for i in shown], ["active"])

    def test_quota_hides_legend_line(self):
        model = adapt(_load("snapshot_demo.json"), now=NOW, demo=True)
        quota = render_page(model, "quota", width=36)
        self.assertNotIn("失败/缺失不是 0%", quota)
        self.assertNotIn("花费≠限额", quota)
        self.assertIn("DeepSeek", quota)

    def test_page_window_pages(self):
        items = list(range(5))
        shown, page_i, n_pages = page_window(items, 1, 2)
        self.assertEqual(n_pages, 3)
        self.assertEqual(page_i, 1)
        self.assertEqual(shown, [2, 3])

    def test_ask_history_keeps_processed(self):
        fd, path = tempfile.mkstemp()
        os.close(fd)
        os.remove(path)
        old = os.environ.get("Q10_ASK_HISTORY_FILE")
        os.environ["Q10_ASK_HISTORY_FILE"] = path
        try:
            current = [{"id": "a1", "title": "请确认", "project": "P", "tool": "Claude"}]
            first = merge_ask_history(current, [], True)
            self.assertEqual(first[0]["open"], True)
            later = merge_ask_history([], first, True)
            self.assertEqual(later[0]["open"], False)
            self.assertEqual(later[0]["title"], "请确认")
            model = adapt(_load("snapshot_demo.json"), now=NOW, demo=True)
            remember_attention(model)
            self.assertTrue(model["ask_open"] >= 1)
            ask = render_page(model, "ask", width=36)
            self.assertIn("待处理", ask)
            self.assertIn("●", ask)
            model["attention"] = []
            model["offline"] = False
            model["schema_ok"] = True
            remember_attention(model)
            ask2 = render_page(model, "ask", width=36)
            self.assertIn("已处理", ask2)
        finally:
            if old is None:
                os.environ.pop("Q10_ASK_HISTORY_FILE", None)
            else:
                os.environ["Q10_ASK_HISTORY_FILE"] = old
            if os.path.isfile(path):
                os.remove(path)


class OctooooProjectionTests(unittest.TestCase):
    def test_projection_expiry_and_minimum_content(self):
        import tempfile
        import octoooo_projection as projection
        frame = {'schema': 'octoooo.display.v1', 'available': True, 'generated_at': 1000, 'expires_at': 31000, 'pending': 17, 'running': 1, 'completed': 0, 'body': 'NESTED_SECRET', 'usage': [{'provider': 'SECRET', 'account': 'SECRET', 'window': 'SECRET', 'value': 132, 'stale': True}, {'provider': 'codex', 'account': '账号 2', 'window': 'weekly', 'value': None, 'stale': True}]}
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, 'projection.json')
            with open(path, 'w', encoding='utf-8') as stream:
                json.dump(frame, stream)
            value = projection.read_projection(path, 2000)
            text = projection.render_projection(value)
            self.assertIn('132%', text)
            self.assertIn('未知', text)
            self.assertNotIn('SECRET', text)
            self.assertEqual(value['pending'], 17)
            self.assertIsNone(projection.read_projection(path, 31001))

    def test_projection_timezone_freshness_and_keyboard_pages(self):
        import octoooo_projection as projection
        from unittest.mock import patch
        from types import SimpleNamespace
        self.assertEqual(projection.sample_ms('2026-09-12T08:00:00+08:00'), projection.sample_ms('2026-09-12T00:00:00Z'))
        self.assertIsNone(projection.sample_ms('not-a-time'))
        value = {'synthetic': True, 'pending': 100, 'running': 1, 'completed': 2, 'usage': [
            {'provider': 'codex', 'account': '账号 {0}'.format(i), 'window': 'weekly', 'percent': 132 if i == 16 else i, 'stale': True}
            for i in range(17)]}
        output = []
        keys = iter(['N','P','K','Q'])
        args = SimpleNamespace(octoooo_file='unused',once=False,all=False,interval=1)
        with patch.object(projection, 'read_projection', return_value=value), patch.object(projection.sys.stdin, 'isatty', return_value=True):
            self.assertEqual(projection.run_monitor(args, lambda timeout: next(keys), output.append, lambda: None),0)
        self.assertIn('第 1/5 页',output[0]); self.assertIn('第 2/5 页',output[1]); self.assertIn('第 1/5 页',output[2]); self.assertIn('第 5/5 页',output[3]); self.assertIn('132%',output[3])

if __name__ == "__main__":
    unittest.main()
