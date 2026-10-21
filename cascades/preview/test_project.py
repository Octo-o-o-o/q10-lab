#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io
import json
import os
import sys
import unittest
from contextlib import redirect_stderr
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "ai-terminal"))

from project import SCHEMA, default_fixture, fixture_now, load_json, project_snapshot  # noqa: E402
from q10_monitor import set_ui_lang  # noqa: E402
from serve import parse_args  # noqa: E402

NOW = datetime(2026, 9, 5, 12, 0, 0)


def _read(path):
    with open(path, "rb") as fh:
        raw = fh.read()
    if not isinstance(raw, str):
        raw = raw.decode("utf-8")
    return raw


class ProjectionTests(unittest.TestCase):
    def setUp(self):
        set_ui_lang("zh")
        self.snap = load_json(default_fixture())

    def test_schema_and_upstream_stay_aindle(self):
        out = project_snapshot(self.snap, now=NOW, demo=True)
        self.assertEqual(out["schema"], SCHEMA)
        self.assertEqual(out["source_schema"], "aindle.snapshot.v2")
        self.assertEqual(out["upstream"], "aindle")
        self.assertFalse(out["offline"])
        self.assertGreaterEqual(out["waiting"], 1)

    def test_quota_keeps_monitor_numbers(self):
        out = project_snapshot(self.snap, now=NOW, demo=True)
        tools = {item["tool"]: item for item in out["quota"]}
        self.assertIn("Claude", tools)
        self.assertIn("Cursor", tools)
        self.assertNotIn("Gemini", tools)
        cursor = {w["key"]: w["used_pct"] for w in tools["Cursor"]["windows"]}
        self.assertEqual(cursor["三方"], 100)
        self.assertEqual(cursor["自有"], 22)
        claude = {w["key"]: w["used_pct"] for w in tools["Claude"]["windows"]}
        self.assertEqual(claude["7d"], 64)

    def test_spend_is_not_quota(self):
        out = project_snapshot(self.snap, now=NOW, demo=True)
        spend_tools = [item["tool"] for item in out["spend"]]
        self.assertIn("DeepSeek", spend_tools)
        self.assertTrue(any("余额" in (item["label"] or "") for item in out["spend"]))

    def test_attention_is_computer_only(self):
        out = project_snapshot(self.snap, now=NOW, demo=True)
        self.assertTrue(out["attention"])
        self.assertTrue(all(item.get("computer_hint") for item in out["attention"]))
        titles = [item["title"] for item in out["attention"]]
        self.assertTrue(any("确认" in title for title in titles))

    def test_stale_task_is_marked(self):
        out = project_snapshot(self.snap, now=NOW, demo=True)
        stale = [item for item in out["tasks"] if item["is_stale_record"]]
        self.assertTrue(stale)
        self.assertTrue(any("过期" in item["title"] for item in stale))

    def test_bad_schema_is_empty_not_zeroed(self):
        out = project_snapshot({"schema": "nope"}, now=NOW)
        self.assertEqual(out["schema"], SCHEMA)
        self.assertEqual(out["quota"], [])
        self.assertEqual(out["waiting"], 0)
        self.assertTrue(out["note"])

    def test_preview_port_refuses_hub_ports(self):
        buf = io.StringIO()
        with redirect_stderr(buf), self.assertRaises(SystemExit):
            parse_args(["--port", "8787"])
        with redirect_stderr(buf), self.assertRaises(SystemExit):
            parse_args(["--port", "8790"])

    def test_hub_flag_without_url_is_aindle_mode(self):
        args = parse_args(["--hub"])
        self.assertEqual(args.mode, "aindle")
        self.assertIsNone(args.hub)

    def test_default_is_fixture(self):
        args = parse_args([])
        self.assertEqual(args.mode, "fixture")
        self.assertEqual(args.port, 8786)

    def test_fixture_clock_keeps_demo_waiting(self):
        clock = fixture_now(self.snap)
        out = project_snapshot(self.snap, now=clock, demo=True)
        self.assertGreaterEqual(out["waiting"], 1)
        self.assertEqual(out["freshness"], "新鲜")

    def test_cascades_fixture_is_same_projection(self):
        path = os.path.join(ROOT, "cascades", "assets", "projection.json")
        with open(path, "rb") as fh:
            packed = json.loads(fh.read().decode("utf-8"))
        clock = fixture_now(self.snap)
        expected = project_snapshot(self.snap, now=clock, demo=True)
        self.assertEqual(packed["schema"], SCHEMA)
        self.assertEqual(packed["waiting"], expected["waiting"])
        self.assertEqual(len(packed["quota"]), len(expected["quota"]))
        self.assertEqual(len(packed["tasks"]), len(expected["tasks"]))
        self.assertEqual(len(packed["attention"]), len(expected["attention"]))
        self.assertEqual([item["title"] for item in packed["attention"]],
                         [item["title"] for item in expected["attention"]])
        self.assertTrue(any(item.get("is_stale_record") for item in packed["tasks"]))

    def test_c4_source_keeps_preview_keys_and_fields(self):
        qml = _read(os.path.join(ROOT, "cascades", "assets", "main.qml"))
        cpp = _read(os.path.join(ROOT, "cascades", "src", "applicationui.cpp"))
        self.assertIn('key: "q"', qml)
        self.assertIn('key: "2"', qml)
        self.assertIn('key: "e"', qml)
        self.assertIn('key: "3"', qml)
        self.assertIn('key: "r"', qml)
        self.assertIn('key: "t"', qml)
        self.assertNotIn('key: "1"', qml)
        self.assertNotIn('key: "w"', qml)
        self.assertIn("q10.console.projection.v1", cpp)
        self.assertIn("169.254.0.2:8786/projection.json", cpp)
        self.assertIn('showPage("quota")', qml)
        self.assertIn('showPage("tasks")', qml)
        self.assertIn('showPage("ask")', qml)
        for field in (
            "freshness",
            "collected_label",
            "waiting",
            "quota",
            "spend",
            "tasks",
            "attention",
            "offline",
            "upstream",
            "status_label",
            "used_pct",
            "waiting_you",
            "is_stale_record",
        ):
            self.assertIn(field, cpp)


if __name__ == "__main__":
    unittest.main()
