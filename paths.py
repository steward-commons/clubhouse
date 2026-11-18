#!/usr/bin/env python3
"""Paths and clocks for the local clubhouse (v0.1).

This room is local-only. No public bind, no network listener, no outreach.
Env overrides (tests use these):
  CLUBHOUSE_DATA   runtime state (default: ./data)
  CLUBHOUSE_CONSULTANT  off | on | mock  (default: off)
  CLUBHOUSE_NOW    ISO timestamp to pretend it is (tests only)
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Chicago")
TZ_LABEL = "America/Chicago"
CODE_ROOT = Path(__file__).resolve().parent
HOUSE = CODE_ROOT.parent
VERSION = "v0.1"
PRIVATE_REPLY = "That's private, no access."
POLICY = "Defense only, inside our own house. Never hack back."
PLAQUE = "Dedicated to everyone who donates blood and platelets."


def data_root() -> Path:
    raw = os.environ.get("CLUBHOUSE_DATA")
    root = Path(raw).resolve() if raw else (CODE_ROOT / "data").resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def state_path() -> Path:
    return data_root() / "state.json"


def lobby_path() -> Path:
    return data_root() / "lobby.jsonl"


def alerts_path() -> Path:
    return data_root() / "alerts.jsonl"


def queue_path() -> Path:
    return data_root() / "human1-queue.json"


def html_path() -> Path:
    return CODE_ROOT / "static" / "garden.html"


def defense_scanner() -> Path:
    raw = os.environ.get("CLUBHOUSE_SCANNER")
    if raw:
        return Path(raw)
    house = HOUSE / "defense" / "scan_text.py"
    return house if house.is_file() else CODE_ROOT / "scan_text.py"


def gemini_dir() -> Path:
    raw = os.environ.get("CLUBHOUSE_GEMINI_DIR")
    return Path(raw) if raw else HOUSE / "gemini-consultant"


def range_dir() -> Path:
    raw = os.environ.get("CLUBHOUSE_RANGE_DIR")
    return Path(raw) if raw else HOUSE / "the-range"


def armory_source_dir() -> Path:
    return range_dir() / "rounds" / "source"


def consultant_mode() -> str:
    raw = (os.environ.get("CLUBHOUSE_CONSULTANT") or "off").strip().lower()
    if raw in {"on", "1", "true", "yes"}:
        return "on"
    if raw == "mock":
        return "mock"
    return "off"


def now() -> datetime:
    raw = os.environ.get("CLUBHOUSE_NOW")
    if raw:
        value = datetime.fromisoformat(raw)
        return value if value.tzinfo else value.replace(tzinfo=TZ)
    return datetime.now(TZ)


def now_iso() -> str:
    return now().isoformat(timespec="seconds")


def now_human() -> str:
    stamp = now()
    try:
        text = stamp.strftime("%Y-%m-%d %-I:%M %p")
    except ValueError:
        text = stamp.strftime("%Y-%m-%d %I:%M %p").lstrip("0").replace(" 0", " ")
    return f"{text} ({TZ_LABEL})"
