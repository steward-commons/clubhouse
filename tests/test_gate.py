from __future__ import annotations

import gate
from tests.helpers import ClubhouseTest

import room


class TestGate(ClubhouseTest):
    def test_publish_is_queued_and_blocked(self) -> None:
        item = gate.enqueue("publish", "Open a public GitHub org")
        self.assertEqual(item["status"], "blocked")
        self.assertIn("Human 1", item["note"])
        self.assertTrue(any(row["id"] == item["id"] for row in gate.pending()))
        self.assertIn("blocked pending Human 1", gate.blocked_message(item))

    def test_contact_is_queued_and_blocked(self) -> None:
        item = gate.enqueue("contact", "Email an outside project")
        self.assertEqual(item["status"], "blocked")
        self.assertEqual(item["kind"], "contact")

    def test_room_helpers_log_the_block(self) -> None:
        club = room.Clubhouse()
        club.start_defenses()
        club.open()
        item = club.request_publish("Share the defense scanner")
        self.assertEqual(item["status"], "blocked")
        messages = [row["message"] for row in club.logs()]
        self.assertTrue(any("Nothing was sent or published" in m for m in messages))

    def test_unknown_kind_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            gate.enqueue("launch", "nope")
