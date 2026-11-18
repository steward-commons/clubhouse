"""Test helpers: isolate runtime state under a temp directory."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class ClubhouseTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.data = Path(self._tmpdir.name)
        os.environ["CLUBHOUSE_DATA"] = str(self.data)
        os.environ["CLUBHOUSE_CONSULTANT"] = "off"
        # Fresh modules that cache nothing important; paths read env live.

    def tearDown(self) -> None:
        self._tmpdir.cleanup()
        os.environ.pop("CLUBHOUSE_DATA", None)
