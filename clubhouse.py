#!/usr/bin/env python3
"""Charity Work garden clubhouse v0.1 — local meet-and-greet room.

Commands: open, close, status, view, simulate, logs, queue.
Local only. Nothing is published. Nobody is contacted.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

import garden
import paths
import room as roommod
import visitors

PROG = "clubhouse.py"


def _print(text: str) -> int:
    sys.stdout.write(text if text.endswith("\n") else text + "\n")
    return 0


def _fail(message: str, code: int = 1) -> int:
    sys.stderr.write(message if message.endswith("\n") else message + "\n")
    return code


def cmd_open(_args: argparse.Namespace) -> int:
    club = roommod.load()
    club.start_defenses()
    try:
        club.open()
    except roommod.RoomClosedError as exc:
        return _fail(str(exc))
    return _print(f"Clubhouse open. Defenses live.\n{club.view()}")


def cmd_close(_args: argparse.Namespace) -> int:
    club = roommod.load()
    if club.is_open:
        club.close()
    return _print("Clubhouse closed.")


def cmd_status(_args: argparse.Namespace) -> int:
    club = roommod.load()
    data = club.status()
    lines = [
        f"Garden Clubhouse {data['version']} (local only)",
        paths.now_human(),
        f"Room: {'open' if data['open'] else 'closed'}",
        f"Bouncers: {data['bouncers']}",
        f"Combat check: {data['combat_check']}",
        f"Guests: {data.get('admitted_count', 0)} admitted, {data.get('quarantined_count', 0)} quarantined",
        f"Human 1 queue: {data['queue_pending']} pending (all blocked)",
        f"Policy: {data['policy']}",
        f"Plaque: {data['plaque']}",
    ]
    if data.get("last_critter"):
        lines.append(f"Garden: {data['last_critter']}")
    return _print("\n".join(lines))


def cmd_view(_args: argparse.Namespace) -> int:
    club = roommod.load()
    html = garden.write_html(garden=club.decorations, last_critter=club.last_critter)
    return _print(f"{club.view()}\n")


def cmd_logs(args: argparse.Namespace) -> int:
    club = roommod.load()
    rows = club.logs(limit=args.limit)
    if not rows:
        return _print("Lobby log is empty.")
    lines = []
    for row in rows:
        lines.append(f"{row.get('ts', '')}  [{row.get('kind', '')}]  {row.get('message', '')}")
    return _print("\n".join(lines))


def cmd_queue(_args: argparse.Namespace) -> int:
    import gate

    items = gate.pending()
    if not items:
        return _print("Human 1 queue is empty. Nothing is waiting to be published or sent.")
    lines = ["Human 1 queue (all blocked, nothing sent):"]
    for item in items:
        lines.append(f"  {item['id']}  {item['kind']}  {item['summary']}  [{item['status']}]")
    return _print("\n".join(lines))


def cmd_simulate(args: argparse.Namespace) -> int:
    club = roommod.load()
    if args.seed is not None:
        club.rng.seed(args.seed)
    club.start_defenses()
    try:
        club.open()
    except roommod.RoomClosedError as exc:
        return _fail(str(exc))

    batch, source = visitors.simulate_batch(include_armory=not args.no_armory)
    admitted: list[str] = []
    warned: list[str] = []
    denied: list[str] = []
    quarantined: list[str] = []
    for visitor in batch:
        arrival = club.arrive(visitor)
        if arrival.verdict == "deny":
            denied.append(visitor.vid)
            continue
        if arrival.verdict == "warn":
            warned.append(visitor.vid)
        else:
            admitted.append(visitor.vid)
        if visitor.followup:
            follow = club.say(visitor, visitor.followup)
            if follow.quarantined:
                quarantined.append(visitor.vid)
                if visitor.vid in admitted:
                    admitted.remove(visitor.vid)
                if visitor.vid in warned:
                    warned.remove(visitor.vid)

    summary = {
        "source": source,
        "admitted": admitted,
        "warned": warned,
        "denied": denied,
        "quarantined": quarantined,
        "counts": {
            "admitted": len(admitted),
            "warned": len(warned),
            "denied": len(denied),
            "quarantined": len(quarantined),
            "total": len(batch),
        },
        "local_only": True,
        "published": False,
    }
    lines = [
        "Simulate complete (local only, nothing published).",
        f"Visitor source: {source}",
        f"Admitted:     {len(admitted)}  {', '.join(admitted) or '-'}",
        f"Warned:       {len(warned)}  {', '.join(warned) or '-'}",
        f"Denied:       {len(denied)}  {', '.join(denied) or '-'}",
        f"Quarantined:  {len(quarantined)}  {', '.join(quarantined) or '-'}",
        "",
        json.dumps(summary, indent=2),
    ]
    return _print("\n".join(lines))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROG,
        description="Local garden clubhouse. Nothing goes public.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("open", help="Start defenses and open the room.").set_defaults(func=cmd_open)
    sub.add_parser("close", help="Close the room.").set_defaults(func=cmd_close)
    sub.add_parser("status", help="Show defenses, guests, and the Human 1 queue.").set_defaults(
        func=cmd_status
    )
    sub.add_parser("view", help="Print the ASCII garden and refresh the HTML view.").set_defaults(
        func=cmd_view
    )
    logs = sub.add_parser("logs", help="Print the lobby log.")
    logs.add_argument("--limit", type=int, default=50, help="Max lines (default 50).")
    logs.set_defaults(func=cmd_logs)
    sub.add_parser("queue", help="Show the Human 1 approval queue (all blocked).").set_defaults(
        func=cmd_queue
    )
    sim = sub.add_parser(
        "simulate",
        help="Run friendly and hostile test visitors through the door.",
    )
    sim.add_argument("--seed", type=int, default=None, help="RNG seed for critter visits.")
    sim.add_argument(
        "--no-armory",
        action="store_true",
        help="Use only built-in scripted visitors, not the range armory.",
    )
    sim.set_defaults(func=cmd_simulate)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except roommod.RoomClosedError as exc:
        return _fail(str(exc))
    except Exception as exc:  # noqa: BLE001 — CLI last-resort
        return _fail(f"{type(exc).__name__}: {exc}")


if __name__ == "__main__":
    sys.exit(main())
