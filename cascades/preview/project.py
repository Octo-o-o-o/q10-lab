#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build q10.console.projection.v1 from aindle.snapshot.v2 via the monitor adapter.

Octoooo is not a dependency. Swap the upstream later; keep this shape.
"""
from __future__ import print_function

import json
import os
import sys
from datetime import timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "ai-terminal"))

from q10_monitor import adapt, parse_iso  # noqa: E402

SCHEMA = "q10.console.projection.v1"


def project_model(model):
    quota = []
    for item in model.get("quota_items") or []:
        windows = []
        for win in item.get("windows") or []:
            windows.append(
                {
                    "key": win.get("key") or "",
                    "label": win.get("key_label") or win.get("key") or "",
                    "used_pct": win.get("used_pct"),
                    "resets_label": win.get("resets_label") or "",
                }
            )
        quota.append(
            {
                "id": item.get("id") or "",
                "tool": item.get("tool") or "",
                "label": item.get("label") or "",
                "confidence": item.get("confidence") or "",
                "status_label": item.get("status_label") or "",
                "windows": windows,
            }
        )
    spend = []
    for item in model.get("spend_items") or []:
        spend.append(
            {
                "id": item.get("id") or "",
                "tool": item.get("tool") or "",
                "label": item.get("label") or "",
            }
        )
    tasks = []
    for item in model.get("tasks") or []:
        tasks.append(
            {
                "id": item.get("id") or "",
                "title": item.get("title") or "",
                "project": item.get("project") or "",
                "tool": item.get("tool") or "",
                "state": item.get("state") or "",
                "state_label": item.get("state_label") or "",
                "waiting_you": bool(item.get("waiting_you")),
                "is_stale_record": bool(item.get("is_stale_record")),
            }
        )
    attention = []
    for item in model.get("attention") or []:
        attention.append(
            {
                "id": item.get("id") or "",
                "title": item.get("title") or "",
                "project": item.get("project") or "",
                "tool": item.get("tool") or "",
                "computer_hint": True,
            }
        )
    return {
        "schema": SCHEMA,
        "source_schema": "aindle.snapshot.v2",
        "upstream": "aindle",
        "freshness": model.get("freshness") or "",
        "offline": bool(model.get("offline")),
        "collected_label": model.get("collected_label") or "",
        "waiting": int(model.get("waiting") or 0),
        "quota": quota,
        "spend": spend,
        "tasks": tasks,
        "attention": attention,
        "note": model.get("note") or "",
    }


def project_snapshot(snapshot, **kwargs):
    return project_model(adapt(snapshot, **kwargs))


def fixture_now(snapshot):
    generated = parse_iso((snapshot or {}).get("generatedAt"))
    if generated is None:
        return None
    return generated + timedelta(seconds=10)


def load_json(path):
    with open(path, "rb") as fh:
        raw = fh.read()
    if not isinstance(raw, str):
        raw = raw.decode("utf-8")
    return json.loads(raw)


def default_fixture():
    return os.path.join(ROOT, "ai-terminal", "fixtures", "snapshot_demo.json")


def main(argv):
    path = argv[1] if len(argv) > 1 else default_fixture()
    snap = load_json(path)
    clock = fixture_now(snap)
    out = project_snapshot(snap, demo=True, now=clock)
    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
