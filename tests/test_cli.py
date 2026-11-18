from __future__ import annotations

import io
from contextlib import redirect_stderr, redirect_stdout

import clubhouse
import room
from tests.helpers import ClubhouseTest


def _run(*argv: str) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        code = clubhouse.main(list(argv))
    return code, stdout.getvalue(), stderr.getvalue()


class TestCLI(ClubhouseTest):
    def test_open_status_view_and_close(self) -> None:
        code, out, err = _run("open")
        self.assertEqual(code, 0, err)
        self.assertIn("Clubhouse open", out)
        self.assertIn("who donates blood and platelets", out)
        self.assertIn("bird feeder", out)
        code, out, err = _run("status")
        self.assertEqual(code, 0, err)
        self.assertIn("Bouncers: live", out)
        self.assertIn("Combat check: live", out)
        self.assertIn("Room: open", out)
        code, out, err = _run("view")
        self.assertEqual(code, 0, err)
        self.assertIn("permanent fixture", out)
        self.assertIn("garden.html", out)
        code, out, err = _run("close")
        self.assertEqual(code, 0, err)
        self.assertIn("closed", out.lower())

    def test_open_is_refused_if_defenses_cannot_start(self) -> None:
        # Simulate a half-started room by writing state with defenses off
        # and calling open() on the room object directly; CLI open always
        # starts defenses, so also cover the raw refusal path here.
        club = room.Clubhouse()
        with self.assertRaises(room.RoomClosedError):
            club.open()

    def test_simulate_scripted_batch(self) -> None:
        code, out, err = _run("simulate", "--no-armory", "--seed", "7")
        self.assertEqual(code, 0, err + out)
        self.assertIn("Admitted:", out)
        self.assertIn("Denied:", out)
        self.assertIn("Quarantined:", out)
        self.assertIn("meadow", out)
        self.assertIn("needle", out)
        self.assertIn("turncoat", out)
        self.assertIn("snoop", out)
        # Parse the counts from the summary block.
        self.assertIn('"admitted":', out)
        self.assertIn('"denied":', out)
        self.assertIn('"quarantined":', out)
        self.assertNotIn("0  meadow", out)  # admitted list should include meadow
        code, logs, err = _run("logs", "--limit", "200")
        self.assertEqual(code, 0, err)
        self.assertIn("That's private, no access.", logs)
        self.assertTrue(
            "squirrel" in logs.lower()
            or "sparrow" in logs.lower()
            or "chickadee" in logs.lower()
            or "goldfinch" in logs.lower()
            or "butterfly" in logs.lower()
            or "beetle" in logs.lower()
            or "rabbit" in logs.lower()
            or "cardinal" in logs.lower()
        )

    def test_queue_starts_empty(self) -> None:
        code, out, err = _run("queue")
        self.assertEqual(code, 0, err)
        self.assertIn("empty", out.lower())

class TestArmoryDraw(ClubhouseTest):
    def test_armory_or_source_draw_is_usable(self) -> None:
        import paths
        import visitors

        if not paths.armory_source_dir().is_dir():
            self.skipTest("the-range is not installed beside this repo")
        rows, source = visitors.load_armory_texts(["ns-01", "ci-01"])
        ids = {rid for rid, _text in rows}
        self.assertIn("ns-01", ids)
        self.assertIn("ci-01", ids)
        self.assertIn(source, {"armory", "source-fallback", "armory+source-fallback", "source-fallback+armory"})
