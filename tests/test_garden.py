from __future__ import annotations

import garden
from tests.helpers import ClubhouseTest


class TestGarden(ClubhouseTest):
    def test_baseline_has_shrine_pieces(self) -> None:
        ids = {row["id"] for row in garden.decorations()}
        for needed in ("roses", "butterflies", "flowers", "bugs", "animals", "bird_feeder", "bird_bath"):
            self.assertIn(needed, ids)
        self.assertTrue(garden.is_permanent("bird_feeder"))
        self.assertTrue(garden.is_permanent("bird_bath"))
        self.assertFalse(garden.is_permanent("roses"))

    def test_permanent_fixtures_cannot_be_removed(self) -> None:
        current = garden.decorations()
        for item_id in ("bird_feeder", "bird_bath"):
            with self.assertRaises(garden.PermanentFixtureError):
                garden.evolve(current, op="remove", item_id=item_id)
        # Still present after the refused change.
        ids = {row["id"] for row in current}
        self.assertIn("bird_feeder", ids)
        self.assertIn("bird_bath", ids)

    def test_permanent_fixtures_cannot_be_changed(self) -> None:
        current = garden.decorations()
        with self.assertRaises(garden.PermanentFixtureError):
            garden.evolve(
                current,
                op="change",
                item_id="bird_feeder",
                item={"id": "bird_feeder", "label": "vending machine", "permanent": True},
            )

    def test_nonpermanent_can_evolve(self) -> None:
        current = garden.decorations()
        updated = garden.evolve(current, op="remove", item_id="bugs")
        self.assertNotIn("bugs", {row["id"] for row in updated})
        updated = garden.evolve(
            updated,
            op="add",
            item={"id": "ferns", "label": "ferns", "kind": "plants", "permanent": False},
        )
        self.assertIn("ferns", {row["id"] for row in updated})
        self.assertIn("bird_feeder", {row["id"] for row in updated})
        self.assertIn("bird_bath", {row["id"] for row in updated})

    def test_view_has_plaque_and_permanent_fixtures(self) -> None:
        text = garden.render_text(last_critter="A squirrel raids the bird feeder.")
        self.assertIn(garden.PLAQUE, text)
        self.assertIn("bird feeder", text)
        self.assertIn("bird bath", text)
        self.assertIn("permanent fixture", text)
        self.assertIn("A squirrel raids the bird feeder.", text)
        self.assertIn("roses", text)
        self.assertIn("butterflies", text)

    def test_html_has_plaque_and_permanent_marks(self) -> None:
        html = garden.render_html(last_critter="Two sparrows splash in the bird bath.")
        self.assertIn(garden.PLAQUE, html)
        self.assertIn('data-id="bird_feeder"', html)
        self.assertIn('data-id="bird_bath"', html)
        self.assertIn('data-permanent="true"', html)
        self.assertIn("Two sparrows splash in the bird bath.", html)

    def test_write_html_and_critters_mention_fixtures(self) -> None:
        path = self.data / "garden.html"
        written = garden.write_html(path, last_critter="A chickadee takes a seed from the feeder.")
        self.assertEqual(written, str(path))
        body = path.read_text(encoding="utf-8")
        self.assertIn("permanent fixture", body)
        mentions = [event for event in garden.CRITTER_EVENTS if "feeder" in event or "bath" in event]
        self.assertGreaterEqual(len(mentions), 4)
