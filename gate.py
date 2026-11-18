#!/usr/bin/env python3
"""Human 1 gate: nothing is published or contacted without approval.

v0.1 is a stub queue. Requests are recorded and stay blocked. This module
never sends a message, never opens a listener, and never talks to a host.
"""

from __future__ import annotations

import json
from typing import Any

import paths

KINDS = frozenset({"publish", "contact"})


def _empty() -> dict[str, Any]:
    return {"pending": [], "blocked": True, "note": "Awaiting Human 1 approval."}


def load(path=None) -> dict[str, Any]:
    target = path or paths.queue_path()
    if not target.is_file():
        return _empty()
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return _empty()
    data.setdefault("pending", [])
    data["blocked"] = True
    return data


def save(data: dict[str, Any], path=None) -> None:
    target = path or paths.queue_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(data)
    payload["blocked"] = True
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def enqueue(
    kind: str,
    summary: str,
    details: dict[str, Any] | None = None,
    path=None,
) -> dict[str, Any]:
    """Queue a publish or contact request. Always returns blocked."""
    if kind not in KINDS:
        raise ValueError(f"Unsupported gate kind: {kind}")
    data = load(path)
    request_id = f"H1-{len(data['pending']) + 1:04d}"
    item = {
        "id": request_id,
        "kind": kind,
        "summary": summary,
        "details": details or {},
        "status": "blocked",
        "queued_at": paths.now_iso(),
        "note": "Blocked pending Human 1 approval. Nothing was sent or published.",
    }
    data["pending"].append(item)
    save(data, path)
    return item


def pending(path=None) -> list[dict[str, Any]]:
    return list(load(path).get("pending") or [])


def blocked_message(item: dict[str, Any]) -> str:
    return (
        f"{item['id']} ({item['kind']}) is blocked pending Human 1 approval. "
        "Nothing was sent or published."
    )
