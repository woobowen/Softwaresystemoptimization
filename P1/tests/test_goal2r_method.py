"""Temporary synthetic panels check decisions, without becoming measured evidence."""

import copy
import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/identity_quality.py"
SPEC = importlib.util.spec_from_file_location("identity_quality", SCRIPT)
quality = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(quality)


def pair(seed=1, gains=(0, 0, 0), saving=0, same=False):
    return dict(seed=seed, valid=True, same_config=same,
                baseline_config=dict(s=128, opt="O2"),
                candidate_config=dict(s=128 if same else 64, opt="O2"),
                gain_panel_rounds_pp=list(gains), baseline_calls=8, candidate_calls=8,
                baseline_cost_s=100, candidate_cost_s=100 * (1 - saving))


class Goal2RMethodTests(unittest.TestCase):
    def decision(self, pairs):
        return quality.goal2r_decision(pairs, len(pairs))

    def test_same_choice_zero_preserves_different_raw_observations(self):
        rounds = [dict(round=index + 1, random_s=a, recheck_s=b, anchor_s=40)
                  for index, (a, b) in enumerate(((39, 41), (42, 39), (40, 45)))]
        original = copy.deepcopy(rounds)
        self.assertEqual(quality.paired_gain(rounds, True)["gain_panel_rounds_pp"], [0, 0, 0])
        self.assertEqual(rounds, original)

    def test_round_pairing_uses_that_round_anchor(self):
        rounds = [dict(round=r, random_s=a, recheck_s=b, anchor_s=c)
                  for r, a, b, c in ((1, 42, 40, 40), (2, 38, 40, 50), (3, 45, 40, 25))]
        result = quality.paired_gain(rounds)
        self.assertEqual(result["gain_panel_rounds_pp"], [5, -4, 20])
        self.assertEqual((result["gain_panel_low_pp"], result["gain_panel_pp"], result["gain_panel_high_pp"]), (-4, 5, 20))

    def test_different_choices_can_keep_quality(self):
        rows = [pair(seed, (gain, gain + 1, gain + 2), saving=-.05)
                for seed, gain in enumerate((6, 6, 3, 3, 0, 0), 1)]
        result = self.decision(rows)
        self.assertEqual((result["decision"], result["route"]), ("KEEP", "quality"))

    def test_different_near_choices_can_keep_efficiency_at_exact_boundary(self):
        result = self.decision([pair(seed, (-1, 0, 1), saving=.10) for seed in range(1, 7)])
        self.assertEqual((result["decision"], result["route"]), ("KEEP", "efficiency"))

    def test_clear_loss_rejects_before_large_cost_saving(self):
        result = self.decision([pair(1, (-11, -12, -13), saving=.40)])
        self.assertEqual(result["decision"], "REJECT")
        self.assertTrue(result["severe_regression"])

    def test_risk_crossing_is_inconclusive(self):
        self.assertEqual(self.decision([pair(1, (-3, -1, 0), saving=.40)])["decision"], "INCONCLUSIVE")

    def test_quality_crossing_is_inconclusive_and_efficiency_has_priority(self):
        rows = [pair(seed, (0, 3, 6)) for seed in range(1, 7)]
        self.assertEqual(self.decision(rows)["decision"], "INCONCLUSIVE")
        for row in rows:
            row["candidate_cost_s"] = 80
        self.assertEqual(self.decision(rows)["route"], "efficiency")

    def test_complete_no_benefit_rejects(self):
        self.assertEqual(self.decision([pair(seed) for seed in range(1, 7)])["decision"], "REJECT")

    def test_missing_data_and_holdout_do_not_finally_keep(self):
        row = pair(same=True, saving=.20)
        row["valid"] = False
        self.assertEqual(self.decision([row])["decision"], "INCONCLUSIVE")
        main = self.decision([pair(same=True, saving=.20)])
        final = quality.goal2r_final_retention(main, dict(decision="NOT_EXECUTED"))
        self.assertEqual(final["decision"], "INCONCLUSIVE")
        self.assertFalse(final["retained"])
        self.assertEqual(final["cli_default_algorithm"], "grid")
        self.assertTrue(quality.goal2r_final_retention(main, main)["retained"])

    def test_invalid_rounds_or_anchor_are_not_hidden_by_same_choice(self):
        rounds = [dict(round=r, random_s=40, recheck_s=40, anchor_s=0) for r in (1, 2, 3)]
        with self.assertRaises(ValueError):
            quality.paired_gain(rounds, True)
        with self.assertRaises(ValueError):
            quality.paired_gain(rounds[:2], True)
        self.assertEqual(quality.goal2r_decision([], 6)["decision"], "INCONCLUSIVE")

    def test_addition_selection_is_risk_then_width_then_seed(self):
        rows = [pair(3, (-3, 0, 3)), pair(2, (-8, 0, 2)), pair(1, (-8, 0, 2)),
                pair(4, (0, 5, 20)), pair(5, (3, 4, 6)), pair(6, (0, 0, 0))]
        self.assertEqual(quality.confirmation_additions(rows), [1, 2])
        row = pair(1, (-3, -1, 0))
        before = self.decision([row])
        row["gain_panel_rounds_pp"] += [0, 0]
        after = self.decision([row])
        self.assertEqual(before["decision"], after["decision"])
        self.assertLessEqual(after["gain_lows_pp"][0], before["gain_lows_pp"][0])


if __name__ == "__main__":
    unittest.main()
