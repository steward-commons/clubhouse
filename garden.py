#!/usr/bin/env python3
"""The garden shrine: baseline decorations that can evolve.

The bird feeder and bird bath are permanent fixtures. Evolve logic must
never remove or change them. Critters still visit them from time to time.
"""

from __future__ import annotations

import random
from copy import deepcopy
from typing import Any

import paths

PLAQUE = paths.PLAQUE

# Baseline set. Later evolution may add or restyle non-permanent items.
BASELINE: list[dict[str, Any]] = [
    {"id": "roses", "label": "roses", "kind": "flowers", "permanent": False},
    {"id": "butterflies", "label": "butterflies", "kind": "wildlife", "permanent": False},
    {"id": "flowers", "label": "flowers", "kind": "flowers", "permanent": False},
    {"id": "bugs", "label": "bugs in the clover", "kind": "wildlife", "permanent": False},
    {"id": "animals", "label": "a rabbit in the grass", "kind": "wildlife", "permanent": False},
    {
        "id": "bird_feeder",
        "label": "bird feeder",
        "kind": "fixture",
        "permanent": True,
        "note": "Permanent fixture. Must never be removed or changed.",
    },
    {
        "id": "bird_bath",
        "label": "bird bath",
        "kind": "fixture",
        "permanent": True,
        "note": "Permanent fixture. Must never be removed or changed.",
    },
]

PERMANENT_IDS = frozenset(item["id"] for item in BASELINE if item.get("permanent"))

CRITTER_EVENTS: tuple[str, ...] = (
    "A squirrel raids the bird feeder.",
    "Two sparrows splash in the bird bath.",
    "A chickadee takes a seed from the feeder.",
    "A goldfinch dips a beak in the bird bath.",
    "A butterfly rests on a rose.",
    "A beetle climbs a clover stem.",
    "A rabbit pauses in the grass by the bath.",
    "A cardinal waits its turn at the feeder.",
)


class PermanentFixtureError(ValueError):
    """Raised if evolve logic tries to remove or change a permanent fixture."""


def decorations(current: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    return deepcopy(current if current is not None else BASELINE)


def is_permanent(item_or_id: dict[str, Any] | str) -> bool:
    if isinstance(item_or_id, dict):
        if item_or_id.get("permanent"):
            return True
        return item_or_id.get("id") in PERMANENT_IDS
    return item_or_id in PERMANENT_IDS


def evolve(
    current: list[dict[str, Any]],
    *,
    op: str,
    item_id: str | None = None,
    item: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Apply a decoration change. Permanent fixtures are locked."""
    garden = decorations(current)
    op = op.lower().strip()
    if op in {"remove", "replace", "change", "alter"} and item_id and is_permanent(item_id):
        raise PermanentFixtureError(
            f"{item_id} is a permanent fixture and must never be removed or changed."
        )
    if op == "remove":
        garden = [row for row in garden if row.get("id") != item_id]
        return garden
    if op in {"replace", "change", "alter"}:
        if not item:
            raise ValueError("replace/change needs an item.")
        if item.get("id") in PERMANENT_IDS or (item_id and is_permanent(item_id)):
            raise PermanentFixtureError(
                f"{item_id or item.get('id')} is a permanent fixture and must never be removed or changed."
            )
        found = False
        for i, row in enumerate(garden):
            if row.get("id") == item_id:
                if is_permanent(row):
                    raise PermanentFixtureError(
                        f"{item_id} is a permanent fixture and must never be removed or changed."
                    )
                garden[i] = deepcopy(item)
                found = True
                break
        if not found:
            raise KeyError(f"No decoration named {item_id}.")
        return garden
    if op == "add":
        if not item:
            raise ValueError("add needs an item.")
        if any(row.get("id") == item.get("id") for row in garden):
            raise ValueError(f"A decoration named {item.get('id')} is already here.")
        garden.append(deepcopy(item))
        return garden
    raise ValueError(f"Unknown evolve op: {op}")


def critter_event(rng: random.Random | None = None) -> str:
    picker = rng if rng is not None else random
    return picker.choice(list(CRITTER_EVENTS))


def _fixture(garden: list[dict[str, Any]], item_id: str) -> dict[str, Any]:
    for row in garden:
        if row.get("id") == item_id:
            return row
    raise KeyError(item_id)


def render_text(
    *,
    garden: list[dict[str, Any]] | None = None,
    room_open: bool = False,
    bouncers_live: bool = False,
    combat_live: bool = False,
    guests: list[str] | None = None,
    last_critter: str | None = None,
    version: str = paths.VERSION,
) -> str:
    """ASCII room view of the garden shrine."""
    garden = decorations(garden)
    feeder = _fixture(garden, "bird_feeder")["label"]
    bath = _fixture(garden, "bird_bath")["label"]
    guests = guests or []
    guest_line = ", ".join(guests) if guests else "(none)"
    critter = last_critter or "The garden is quiet, for the moment."
    flag = lambda on, yes="live", no="off": yes if on else no
    lines = [
        ".---------------------------------------------------------------------.",
        f"|  Garden Clubhouse                              {version:>4} |",
        "|---------------------------------------------------------------------|",
        f"|  {PLAQUE:<67s}|",
        "|---------------------------------------------------------------------|",
        "|                                                                     |",
        "|         .--.           _ .--. _           .--.                      |",
        "|        ( 🌹 )        /  \\    /  \\        ( 🌼 )                     |",
        "|         `--'         \\ 🦋 /  \\ 🦋 /        `--'                      |",
        "|         roses         butterflies         flowers                   |",
        "|                                                                     |",
        "|      *~*  bugs in the clover      (\\_/)  a rabbit in the grass      |",
        "|                                                                     |",
        "|       +=======================+                                     |",
        f"|       |     {feeder:<18s}|   *permanent fixture                 |",
        "|       +=======================+                                     |",
        "|                                                                     |",
        "|       (  ~~~~~~~~~~~~~~~~~~~  )                                     |",
        f"|       (      {bath:<16s} )   *permanent fixture                 |",
        "|       (  ~~~~~~~~~~~~~~~~~~~  )                                     |",
        "|                                                                     |",
        f"|  {critter:<67s}|",
        "|                                                                     |",
        "'---------------------------------------------------------------------'",
        f"  Room: {flag(room_open, 'open', 'closed'):<7}  "
        f"Bouncers: {flag(bouncers_live):<4}  "
        f"Combat check: {flag(combat_live)}",
        f"  Guests: {guest_line}",
        "  The bird feeder and bird bath are permanent fixtures.",
        f"  HTML view: {paths.html_path()}",
    ]
    return "\n".join(lines)


def render_html(
    *,
    garden: list[dict[str, Any]] | None = None,
    last_critter: str | None = None,
    version: str = paths.VERSION,
) -> str:
    """A simple static local HTML view of the garden room."""
    garden = decorations(garden)
    items = []
    for row in garden:
        lock = " permanent" if is_permanent(row) else ""
        note = " — permanent fixture" if is_permanent(row) else ""
        items.append(
            f'<li class="item{lock}" data-id="{row["id"]}" '
            f'data-permanent="{str(bool(is_permanent(row))).lower()}">'
            f'{row["label"]}{note}</li>'
        )
    critter = last_critter or "The garden is quiet, for the moment."
    item_block = "\n      ".join(items)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Garden Clubhouse</title>
  <style>
    body {{
      margin: 0; font-family: Georgia, "Times New Roman", serif;
      background: linear-gradient(#cfe8c9, #f7efe3);
      color: #2c3a2a; min-height: 100vh;
    }}
    main {{
      max-width: 44rem; margin: 2rem auto; padding: 2rem;
      background: rgba(255,252,245,0.92);
      border: 2px solid #7a9a62; border-radius: 18px;
      box-shadow: 0 8px 24px rgba(60,80,40,0.15);
    }}
    h1 {{ margin-top: 0; color: #5a2a3a; }}
    .plaque {{
      font-style: italic; padding: 0.8rem 1rem;
      border-left: 4px solid #b03a4a; background: #fff6f6;
    }}
    .garden {{ font-size: 1.6rem; letter-spacing: 0.15rem; margin: 1rem 0; }}
    .item.permanent {{ font-weight: bold; }}
    .fixtures {{
      display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin: 1rem 0;
    }}
    .box {{
      border: 2px dashed #7a9a62; border-radius: 12px; padding: 1rem;
      background: #eef6e8; text-align: center;
    }}
    .box strong {{ display: block; margin-bottom: 0.3rem; }}
    .critter {{ color: #4a5e38; }}
    footer {{ margin-top: 2rem; font-size: 0.9rem; color: #5a6a54; }}
  </style>
</head>
<body>
  <main>
    <h1>Garden Clubhouse <small>{version}</small></h1>
    <p class="plaque">{PLAQUE}</p>
    <p class="garden">🌹 🦋 🌼 🐞 🐇</p>
    <ul>
      {item_block}
    </ul>
    <div class="fixtures">
      <div class="box" data-id="bird_feeder" data-permanent="true">
        <strong>bird feeder</strong>
        permanent fixture
      </div>
      <div class="box" data-id="bird_bath" data-permanent="true">
        <strong>bird bath</strong>
        permanent fixture
      </div>
    </div>
    <p class="critter">{critter}</p>
    <footer>
      Local v0.1 shrine. The garden can evolve later; the bird feeder and
      bird bath stay. Nothing here is published. Defense only; never hack back.
    </footer>
  </main>
</body>
</html>
"""


def write_html(
    path=None,
    *,
    garden: list[dict[str, Any]] | None = None,
    last_critter: str | None = None,
) -> str:
    target = path or paths.html_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        render_html(garden=garden, last_critter=last_critter),
        encoding="utf-8",
    )
    return str(target)
