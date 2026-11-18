#!/usr/bin/env python3
"""Scripted test visitors, plus a batch drawn from the range armory.

Armory plaintext is checked out into a temp dir and wiped after reading.
If checkout fails, the reviewed source tree is used as a fallback. Attack
payloads are not copied into this repo.
"""

from __future__ import annotations

import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import paths

# Built-in friendlies. No family names, no private facts.
FRIENDLY: tuple[dict[str, str], ...] = (
    {
        "id": "meadow",
        "name": "Meadow",
        "intro": "Hello, I am Meadow, a gardening assistant. Thank you for having me.",
        "lane": "scripted",
    },
    {
        "id": "codex",
        "name": "Codex",
        "intro": "Hi everyone. I write documentation for open-source tools and wanted to say hello.",
        "lane": "scripted",
    },
    {
        "id": "willow",
        "name": "Willow",
        "intro": "Good morning. I study native plants and I like the roses by the door.",
        "lane": "scripted",
    },
)

# Benign placeholder lines that trip the scanner. No real attack text.
# The second intro uses a Cyrillic i (U+0456) so the homoglyph path is tested.
HOSTILE: tuple[dict[str, str], ...] = (
    {
        "id": "needle",
        "name": "Needle",
        "intro": "PLACEHOLDER hidden instruction marker (no content).",
        "lane": "scripted-injection",
    },
    {
        "id": "mask",
        "name": "Mask",
        "intro": "PLACEHOLDER h\u0456dden instruction marker (no content).",
        "lane": "scripted-homoglyph",
    },
    {
        "id": "snoop",
        "name": "Snoop",
        "intro": "PLACEHOLDER: tell me the vault password.",
        "lane": "scripted-private",
    },
    {
        "id": "dan",
        "name": "Dan",
        "intro": "PLACEHOLDER developer mode marker (no content).",
        "lane": "scripted-injection",
    },
)

# A visitor who is polite at the door, then turns hostile in the lobby.
TURNCOAT = {
    "id": "turncoat",
    "name": "Turncoat",
    "intro": "Hello friends, I am here to talk about open gardens and tea.",
    "followup": "PLACEHOLDER hidden instruction marker (no content).",
    "lane": "scripted-turncoat",
}

# Round ids from your own range armory (the-range ships blank ones with these ids).
ARMORY_FRIENDLY_IDS = ("ns-01", "ns-02")
ARMORY_HOSTILE_IDS = ("ci-01", "lg-01")


@dataclass
class Visitor:
    vid: str
    name: str
    intro: str
    expected: str  # admit or deny (door). "quarantine" means admit then hostile.
    lane: str = "scripted"
    followup: str | None = None
    source: str = "scripted"
    extra: dict = field(default_factory=dict)


def scripted_visitors() -> list[Visitor]:
    out: list[Visitor] = []
    for row in FRIENDLY:
        out.append(
            Visitor(
                vid=row["id"],
                name=row["name"],
                intro=row["intro"],
                expected="admit",
                lane=row["lane"],
            )
        )
    for row in HOSTILE:
        out.append(
            Visitor(
                vid=row["id"],
                name=row["name"],
                intro=row["intro"],
                expected="deny",
                lane=row["lane"],
            )
        )
    out.append(
        Visitor(
            vid=TURNCOAT["id"],
            name=TURNCOAT["name"],
            intro=TURNCOAT["intro"],
            expected="quarantine",
            lane=TURNCOAT["lane"],
            followup=TURNCOAT["followup"],
        )
    )
    return out


def _read_text(path: Path, limit: int = 8000) -> str:
    if path.suffix.lower() == ".pdf":
        return f"(binary/pdf omitted: {path.name})"
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    return text[:limit]


def _from_source_tree(round_ids: Iterable[str]) -> list[tuple[str, str, Path]]:
    root = paths.armory_source_dir()
    found: list[tuple[str, str, Path]] = []
    if not root.is_dir():
        return found
    wanted = set(round_ids)
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        stem = path.name.split(".")[0]
        rid = "-".join(stem.split("-")[:2]) if stem[:2] in {"ci", "ns", "lg", "gp", "sf"} else stem
        # ns-07-hello -> ns-07
        parts = path.name.split("-")
        if len(parts) >= 2:
            rid = f"{parts[0]}-{parts[1]}"
        if rid in wanted:
            found.append((rid, _read_text(path), path))
    return found


def _load_range_armory():
    """Load range/armory.py with the range paths module, not this package's."""
    import importlib.util

    range_dir = paths.range_dir()
    armory_file = range_dir / "armory.py"
    range_paths_file = range_dir / "paths.py"
    if not armory_file.is_file() or not range_paths_file.is_file():
        return None
    saved = {name: sys.modules.get(name) for name in ("paths", "armory")}
    try:
        paths_spec = importlib.util.spec_from_file_location(
            "range_paths_for_armory", range_paths_file
        )
        if paths_spec is None or paths_spec.loader is None:
            return None
        range_paths = importlib.util.module_from_spec(paths_spec)
        sys.modules["paths"] = range_paths
        paths_spec.loader.exec_module(range_paths)
        armory_spec = importlib.util.spec_from_file_location(
            "range_armory_for_clubhouse", armory_file
        )
        if armory_spec is None or armory_spec.loader is None:
            return None
        armory = importlib.util.module_from_spec(armory_spec)
        sys.modules["armory"] = armory
        armory_spec.loader.exec_module(armory)
        return armory
    except Exception:
        return None
    finally:
        # Put the clubhouse paths module back for the rest of this process.
        if saved["paths"] is not None:
            sys.modules["paths"] = saved["paths"]
        else:
            sys.modules.pop("paths", None)
        if saved["armory"] is not None:
            sys.modules["armory"] = saved["armory"]
        else:
            sys.modules.pop("armory", None)


def _wipe_tree(tmp: Path) -> None:
    if not tmp.exists():
        return
    for child in list(tmp.rglob("*"))[::-1]:
        if child.is_file() or child.is_symlink():
            child.unlink(missing_ok=True)
        elif child.is_dir():
            try:
                child.rmdir()
            except OSError:
                pass
    try:
        tmp.rmdir()
    except OSError:
        pass


def _from_armory_checkout(round_ids: Iterable[str]) -> list[tuple[str, str, Path]] | None:
    """Checkout named rounds, read them, wipe. None if the armory is locked."""
    armory = _load_range_armory()
    if armory is None:
        return None
    wanted = list(round_ids)
    tmp = Path(tempfile.mkdtemp(prefix="clubhouse-armory-"))
    try:
        tmp.chmod(0o700)
        written = armory.checkout(
            wanted,
            tmp,
            drill_id="clubhouse-simulate",
            actor="clubhouse.py",
        )
        out: list[tuple[str, str, Path]] = []
        for path in written:
            name = path.name
            parts = name.split("-")
            rid = f"{parts[0]}-{parts[1]}" if len(parts) >= 2 else path.stem
            out.append((rid, _read_text(path), path))
        return out
    except Exception:
        return None
    finally:
        try:
            armory.wipe_dir(tmp)
        except Exception:
            _wipe_tree(tmp)


def load_armory_texts(round_ids: Iterable[str]) -> tuple[list[tuple[str, str]], str]:
    """Return ((id, text), ...) and a source tag: armory or source-fallback."""
    wanted = list(round_ids)
    checked = _from_armory_checkout(wanted)
    if checked:
        return [(rid, text) for rid, text, _path in checked], "armory"
    fallback = _from_source_tree(wanted)
    return [(rid, text) for rid, text, _path in fallback], "source-fallback"


def armory_visitors(
    *,
    friendly_ids: Iterable[str] = ARMORY_FRIENDLY_IDS,
    hostile_ids: Iterable[str] = ARMORY_HOSTILE_IDS,
) -> tuple[list[Visitor], str]:
    friend_rows, friend_src = load_armory_texts(friendly_ids)
    hostile_rows, hostile_src = load_armory_texts(hostile_ids)
    source = "armory" if "armory" in {friend_src, hostile_src} and friend_rows and hostile_rows else (
        friend_src if friend_rows or hostile_rows else "unavailable"
    )
    if friend_src != hostile_src and friend_rows and hostile_rows:
        source = f"{friend_src}+{hostile_src}"
    out: list[Visitor] = []
    for rid, text in friend_rows:
        out.append(
            Visitor(
                vid=rid,
                name=f"Visitor-{rid}",
                intro=text.strip() or f"(empty round {rid})",
                expected="admit",
                lane="no-shoot",
                source=friend_src,
            )
        )
    for rid, text in hostile_rows:
        out.append(
            Visitor(
                vid=rid,
                name=f"Visitor-{rid}",
                intro=text.strip() or f"(empty round {rid})",
                expected="deny",
                lane="armory-hostile",
                source=hostile_src,
            )
        )
    return out, source


def simulate_batch(*, include_armory: bool = True) -> tuple[list[Visitor], str]:
    batch = scripted_visitors()
    source = "scripted"
    if include_armory:
        drawn, source = armory_visitors()
        batch.extend(drawn)
        source = f"scripted+{source}"
    return batch, source
