"""Driver counterexamples use saved real A/A traces without rerunning the matrix."""

import copy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

P1 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P1 / "scripts"))
import experiment_v2 as ex


class Goal2RDriverTests(unittest.TestCase):
    def setUp(self):
        self.rows = ex.read_records(P1 / "evidence/measurement/goal2r/aa-01-F-A1.jsonl")
        self.metadata = self.rows[0]["metadata"]
        self.job = dict(config=next(r["config"] for r in self.rows if r["type"] == "trial_start"))

    def test_all_eight_actual_aa_traces_rebuild_from_raw(self):
        paths = sorted((P1 / "evidence/measurement/goal2r").glob("aa-*.jsonl"))
        self.assertEqual(len(paths), 8)
        for path in paths:
            rows = ex.read_records(path)
            ex.validate_trace(rows, rows[0]["metadata"], {})

    def test_missing_or_tampered_integer_kernel_boundaries_are_rejected(self):
        for change in ("missing", "field"):
            rows = copy.deepcopy(self.rows)
            measurement = next(r for r in rows if r["type"] == "measurement")
            if change == "missing":
                measurement["stdout"] = "\n".join(line for line in measurement["stdout"].splitlines()
                                                       if not line.startswith("kernel_")) + "\n"
            else:
                measurement["kernel_start_ns"] += 1
            with self.assertRaises(ValueError):
                ex.validate_trace(rows, self.metadata, self.job)

    def test_valid_raw_trace_survives_auxiliary_clock_reversal(self):
        rows = copy.deepcopy(self.rows)
        measurement = next(r for r in rows if r["type"] == "measurement")
        measurement["clock_end_ns"]["CLOCK_REALTIME"] = measurement["clock_start_ns"]["CLOCK_REALTIME"] - 1000000000
        measurement["clock_deltas_s"]["CLOCK_REALTIME"] = -1.0
        measurement["auxiliary_clock_anomalies"] = ["CLOCK_REALTIME"]
        ex.validate_trace(rows, self.metadata, self.job)

    def test_supplementary_cost_reserve_blocks_start_before_cap(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(ex, "MAX_SECONDS", 1):
            root = Path(directory)
            with self.assertRaisesRegex(ValueError, "resource cap"):
                ex.controlled([sys.executable, "-c", "raise SystemExit(99)"], root, "never-start", "test",
                              ledger=root / "ledger.jsonl", resource_reserve_s=1)
            self.assertFalse((root / "ledger.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
