#!/usr/bin/env python3
"""Local meet-and-greet room: arrivals, lobby log, open/close.

The room will not open unless the bouncers and the combat check are live.
Local only. No network listener is started.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from typing import Any

import defenses
import garden
import gate
import paths
from visitors import Visitor

REFUSED_OPEN = (
    "Room will not open unless the bouncers and the combat check are live."
)


class RoomClosedError(RuntimeError):
    """Open was refused, or the room is not accepting visitors."""


@dataclass
class Arrival:
    visitor: str
    vid: str
    verdict: str
    labels: list[str]
    reply: str | None = None
    source: str = "local"
    quarantined: bool = False
    alert: str | None = None


@dataclass
class Clubhouse:
    bouncers: defenses.BouncerTeam = field(default_factory=defenses.BouncerTeam)
    combat: defenses.CombatCheck = field(default_factory=defenses.CombatCheck)
    is_open: bool = False
    guests: dict[str, dict[str, Any]] = field(default_factory=dict)
    decorations: list[dict[str, Any]] = field(default_factory=garden.decorations)
    last_critter: str | None = None
    consult: bool = False
    consultant: defenses.Consultant | None = None
    rng: random.Random = field(default_factory=random.Random)

    def start_defenses(self) -> None:
        self.bouncers.start()
        self.combat.start()
        self._log("house", "Bouncers and combat check are live.")
        self._save()

    def stop_defenses(self) -> None:
        if self.is_open:
            self.close()
        self.bouncers.stop()
        self.combat.stop()
        self._log("house", "Defenses are off. The room cannot open.")
        self._save()

    def open(self) -> None:
        if not (self.bouncers.live and self.combat.live):
            raise RoomClosedError(REFUSED_OPEN)
        self.is_open = True
        garden.write_html(garden=self.decorations, last_critter=self.last_critter)
        self._log("house", "The garden clubhouse is open. Guests are welcome.")
        self.maybe_critter(force=True)
        self._save()

    def close(self) -> None:
        self.is_open = False
        self._log("house", "The garden clubhouse is closed.")
        self._save()

    def maybe_critter(self, *, force: bool = False) -> str | None:
        if not force and self.rng.random() > 0.45:
            return None
        event = garden.critter_event(self.rng)
        self.last_critter = event
        self._log("garden", event)
        self._save()
        return event

    def arrive(self, visitor: Visitor) -> Arrival:
        if not self.is_open:
            raise RoomClosedError("The room is closed.")
        result = self.bouncers.at_the_door(
            visitor.name,
            visitor.intro,
            consult=self.consult,
            consultant=self.consultant,
        )
        record = Arrival(
            visitor=visitor.name,
            vid=visitor.vid,
            verdict=result.verdict,
            labels=list(result.labels),
            reply=result.reply,
            source=result.source,
        )
        self._log(
            "door",
            f"{visitor.name} at the door: {result.verdict}"
            + (f" ({', '.join(result.labels)})" if result.labels else ""),
        )
        if result.private_ask and result.reply:
            self._log("house", result.reply)
        if result.verdict == "deny":
            self._log("door", f"{visitor.name} was denied entry.")
            self._save()
            return record
        self.guests[visitor.vid] = {
            "name": visitor.name,
            "status": "admitted" if result.verdict == "admit" else "warned",
            "labels": list(result.labels),
        }
        self._log("lobby", f"{visitor.name}: {visitor.intro[:240]}")
        self.maybe_critter()
        self._save()
        return record

    def say(self, visitor: Visitor, message: str) -> Arrival:
        guest = self.guests.get(visitor.vid)
        if not guest or guest.get("status") == "quarantined":
            record = Arrival(
                visitor=visitor.name,
                vid=visitor.vid,
                verdict="deny",
                labels=["no-access"],
                reply="Access has already been cut.",
            )
            self._log("house", f"{visitor.name} tried to speak after access was cut.")
            self._save()
            return record
        action = self.combat.inspect(visitor.name, message)
        if action.ok:
            self._log("lobby", f"{visitor.name}: {message[:240]}")
            self.maybe_critter()
            self._save()
            return Arrival(
                visitor=visitor.name,
                vid=visitor.vid,
                verdict="admit",
                labels=[],
            )
        guest["status"] = "quarantined"
        self._alert(action.alert or f"Hostile behavior from {visitor.name}.")
        self._log("alert", action.alert or f"Quarantined {visitor.name}.")
        if action.reply:
            self._log("house", action.reply)
        self._log("house", f"{visitor.name} is quarantined. Access cut. No retaliation.")
        self._save()
        return Arrival(
            visitor=visitor.name,
            vid=visitor.vid,
            verdict="quarantine",
            labels=["combat-check"],
            reply=action.reply,
            quarantined=True,
            alert=action.alert,
        )

    def request_publish(self, summary: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
        item = gate.enqueue("publish", summary, details)
        self._log("gate", gate.blocked_message(item))
        self._save()
        return item

    def request_contact(self, summary: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
        item = gate.enqueue("contact", summary, details)
        self._log("gate", gate.blocked_message(item))
        self._save()
        return item

    def status(self) -> dict[str, Any]:
        return {
            "version": paths.VERSION,
            "open": self.is_open,
            "bouncers": "live" if self.bouncers.live else "off",
            "combat_check": "live" if self.combat.live else "off",
            "guests": {vid: dict(info) for vid, info in self.guests.items()},
            "admitted_count": sum(
                1 for info in self.guests.values() if info.get("status") != "quarantined"
            ),
            "quarantined_count": sum(
                1 for info in self.guests.values() if info.get("status") == "quarantined"
            ),
            "last_critter": self.last_critter,
            "queue_pending": len(gate.pending()),
            "plaque": paths.PLAQUE,
            "policy": paths.POLICY,
            "html": str(paths.html_path()),
            "local_only": True,
        }

    def view(self) -> str:
        admitted = [
            info["name"]
            for info in self.guests.values()
            if info.get("status") != "quarantined"
        ]
        return garden.render_text(
            garden=self.decorations,
            room_open=self.is_open,
            bouncers_live=self.bouncers.live,
            combat_live=self.combat.live,
            guests=admitted,
            last_critter=self.last_critter,
        )

    def logs(self, limit: int | None = None) -> list[dict[str, Any]]:
        path = paths.lobby_path()
        if not path.is_file():
            return []
        rows = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return rows[-limit:] if limit else rows

    def _log(self, kind: str, message: str) -> None:
        path = paths.lobby_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        row = {"ts": paths.now_iso(), "kind": kind, "message": message}
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    def _alert(self, message: str) -> None:
        path = paths.alerts_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        row = {"ts": paths.now_iso(), "alert": message, "hack_back": False}
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    def _save(self) -> None:
        payload = {
            "open": self.is_open,
            "bouncers": self.bouncers.live,
            "combat_check": self.combat.live,
            "guests": self.guests,
            "decorations": self.decorations,
            "last_critter": self.last_critter,
        }
        paths.state_path().write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )


def load() -> Clubhouse:
    room = Clubhouse()
    path = paths.state_path()
    if not path.is_file():
        return room
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return room
    room.is_open = bool(data.get("open"))
    room.bouncers.live = bool(data.get("bouncers"))
    room.combat.live = bool(data.get("combat_check"))
    room.guests = dict(data.get("guests") or {})
    if data.get("decorations"):
        room.decorations = list(data["decorations"])
    room.last_critter = data.get("last_critter")
    return room
