from __future__ import annotations

import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from epistemic import format_allowlist_block_result, finalize_hard_allowlist_block


class _Brain:
    pass


class EpistemicTests(unittest.TestCase):
    def test_stop_retry_on_second_hard_block(self) -> None:
        brain = _Brain()
        text, force = finalize_hard_allowlist_block(
            brain,
            "python -c 'pass'",
            guidance={"reason": "not on allowlist", "alternative_tool": None, "alternative_hint": None},
        )
        self.assertFalse(force)
        text2, force2 = finalize_hard_allowlist_block(
            brain,
            "python -c 'pass'",
            guidance={"reason": "not on allowlist", "alternative_tool": None, "alternative_hint": None},
        )
        self.assertTrue(force2)
        self.assertIn("STOP_RETRY", text2)
        self.assertIn("STATUS:", text)
        self.assertIn("USE_INSTEAD:", text)


if __name__ == "__main__":
    unittest.main()
