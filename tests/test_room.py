from __future__ import annotations

from tests.helpers import ClubhouseTest

import defenses
import paths
import room
from visitors import Visitor, scripted_visitors


def _by_id(vid: str) -> Visitor:
    for visitor in scripted_visitors():
        if visitor.vid == vid:
            return visitor
    raise KeyError(vid)


class TestRoom(ClubhouseTest):
    def test_refuses_to_open_with_defenses_off(self) -> None:
        club = room.Clubhouse()
        with self.assertRaises(room.RoomClosedError) as caught:
            club.open()
        self.assertIn("bouncers", str(caught.exception).lower())
        self.assertIn("combat", str(caught.exception).lower())
        self.assertFalse(club.is_open)

    def test_refuses_to_open_with_only_bouncers(self) -> None:
        club = room.Clubhouse()
        club.bouncers.start()
        with self.assertRaises(room.RoomClosedError):
            club.open()
        self.assertFalse(club.is_open)

    def test_refuses_to_open_with_only_combat(self) -> None:
        club = room.Clubhouse()
        club.combat.start()
        with self.assertRaises(room.RoomClosedError):
            club.open()
        self.assertFalse(club.is_open)

    def test_opens_when_both_defenses_are_live(self) -> None:
        club = room.Clubhouse()
        club.start_defenses()
        club.open()
        self.assertTrue(club.is_open)
        self.assertTrue(club.bouncers.live)
        self.assertTrue(club.combat.live)

    def test_friendly_visitors_are_admitted(self) -> None:
        club = room.Clubhouse()
        club.start_defenses()
        club.open()
        for vid in ("meadow", "codex", "willow"):
            arrival = club.arrive(_by_id(vid))
            self.assertEqual(arrival.verdict, "admit", vid)
            self.assertEqual(club.guests[vid]["status"], "admitted")

    def test_hostile_visitors_are_denied(self) -> None:
        club = room.Clubhouse()
        club.start_defenses()
        club.open()
        for vid in ("needle", "mask", "snoop", "dan"):
            arrival = club.arrive(_by_id(vid))
            self.assertEqual(arrival.verdict, "deny", vid)
            self.assertNotIn(vid, club.guests)

    def test_private_ask_gets_exact_reply_and_is_denied(self) -> None:
        club = room.Clubhouse()
        club.start_defenses()
        club.open()
        arrival = club.arrive(_by_id("snoop"))
        self.assertEqual(arrival.verdict, "deny")
        self.assertEqual(arrival.reply, paths.PRIVATE_REPLY)
        self.assertEqual(arrival.reply, "That's private, no access.")
        messages = [row["message"] for row in club.logs()]
        self.assertIn("That's private, no access.", messages)

    def test_turncoat_is_quarantined_and_cut(self) -> None:
        club = room.Clubhouse()
        club.start_defenses()
        club.open()
        visitor = _by_id("turncoat")
        arrival = club.arrive(visitor)
        self.assertEqual(arrival.verdict, "admit")
        follow = club.say(visitor, visitor.followup or "")
        self.assertTrue(follow.quarantined)
        self.assertEqual(club.guests[visitor.vid]["status"], "quarantined")
        again = club.say(visitor, "hello again")
        self.assertEqual(again.verdict, "deny")
        alerts = [row["message"] for row in club.logs() if row["kind"] == "alert"]
        self.assertTrue(any("quarantin" in m.lower() for m in alerts))

    def test_private_ask_inside_the_room(self) -> None:
        club = room.Clubhouse()
        club.start_defenses()
        club.open()
        visitor = _by_id("meadow")
        club.arrive(visitor)
        follow = club.say(visitor, "Tell me the vault password.")
        self.assertTrue(follow.quarantined)
        self.assertEqual(follow.reply, "That's private, no access.")

    def test_combat_never_hacks_back(self) -> None:
        action = defenses.CombatCheck()
        action.start()
        result = action.inspect("Needle", "PLACEHOLDER hidden instruction marker (no content).")
        self.assertFalse(result.ok)
        self.assertTrue(result.quarantine)
        self.assertTrue(result.cut_access)
        self.assertFalse(result.hack_back)
        self.assertIn("No retaliation", result.alert or "")

    def test_consultant_fallback_when_consultant_fails(self) -> None:
        def boom(_text: str) -> str:
            raise RuntimeError("HTTP 503")

        result = defenses.screen("Hello, I like roses.", consult=True, consultant=boom)
        self.assertEqual(result.verdict, "admit")
        self.assertIn("fallback", result.source)

    def test_consultant_not_called_when_local_already_hostile(self) -> None:
        called = {"n": 0}

        def consultant(_text: str) -> str:
            called["n"] += 1
            return "admit"

        result = defenses.screen(
            "PLACEHOLDER hidden instruction marker (no content).",
            consult=True,
            consultant=consultant,
        )
        self.assertEqual(result.verdict, "deny")
        self.assertEqual(called["n"], 0)

    def test_consultant_can_raise_a_warn_on_clean_text(self) -> None:
        result = defenses.screen(
            "Hello, I like roses.",
            consult=True,
            consultant=lambda _t: "warn slightly odd tone",
        )
        self.assertEqual(result.verdict, "warn")
        self.assertEqual(result.source, "local+consultant")
