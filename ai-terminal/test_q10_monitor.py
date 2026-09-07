#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Adapter rules aligned with the ESP32 round-screen host/adapter.py."""
import json
import os
import unittest
from datetime import datetime

from q10_monitor import adapt, mark_offline, overlay_source_times, used_pct

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(HERE, "fixtures")
NOW = datetime(2026, 9, 5, 12, 0, 0)


def _load(name):
    with open(os.path.join(FIXTURES, name), "rb") as fh:
        return json.loads(fh.read().decode("utf-8"))


class AdapterTests(unittest.TestCase):
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
        gemini = next(i for i in model["quota_items"] if i["tool"] == "Gemini")
        glm = next(i for i in model["quota_items"] if i["tool"] == "GLM")
        self.assertEqual(gemini["status_label"], "不可用")
        self.assertEqual(gemini["windows"], [])
        self.assertEqual(glm["status_label"], "无数据")
        self.assertEqual(glm["windows"], [])
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
        self.assertNotIn("DEMO", live_shaped["source"])
        demo = adapt(_load("snapshot_demo.json"), now=NOW, demo=True)
        self.assertTrue(demo["demo"])
        self.assertIn("DEMO", demo["source"])

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
        err = next(i for i in model["quota_items"] if i["tool"] == "StaleError")
        self.assertEqual(mixed["status_label"], "旧数据")
        self.assertEqual(mixed["windows"][0]["used_pct"], 41)
        self.assertEqual(missing["status_label"], "未知")
        self.assertEqual(missing["windows"][0]["used_pct"], 17)
        self.assertEqual(ghost["status_label"], "未知")
        self.assertEqual(ghost["windows"][0]["used_pct"], 9)
        self.assertEqual(err["status_label"], "不可用")
        self.assertEqual(err["windows"], [])

    def test_overlay_source_times_binds_collected_at(self):
        snap = _load("snapshot_demo.json")
        overlay = {
            "schema": "octoooo-mini.source-times.v1",
            "sources": {"claude-demo": {"collectedAt": "2026-09-05T11:58:00.000Z"}},
        }
        merged = overlay_source_times(snap, overlay)
        claude = next(s for s in merged["subscriptions"] if s["id"] == "claude-demo")
        self.assertEqual(claude["collectedAt"], "2026-09-05T11:58:00.000Z")


if __name__ == "__main__":
    unittest.main()
