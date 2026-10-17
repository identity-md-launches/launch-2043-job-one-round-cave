#!/usr/bin/env python3
"""Offline checks for exact target searches."""

import copy
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest

import rewardtarget as rt


class RewardTargetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.metadata = rt.rs.read_json(rt.rr.ROOT / "zto-mainnet.json")

    def request(self, budget=25):
        return {"budget": rt.rs.display_units(budget, 18),
                "contributors": [{"id": name, "weight": str(weight)} for name, weight in
                                 zip("abcdef", (1500, 1500, 900, 500, 500, 200))]}

    def test_nonmonotonic_demo(self):
        result = rt.demo()["search"]
        self.assertEqual(result["budgets_checked"], 4)
        self.assertEqual(result["budgets_meeting_all_targets"], 2)
        self.assertEqual(result["matching_intervals"], [
            {"first_budget_units": "25", "last_budget_units": "25"},
            {"first_budget_units": "28", "last_budget_units": "28"}])
        self.assertEqual(result["first_match"]["budget_units"], "25")

    def test_no_match_and_boundary(self):
        request = self.request(26)
        targets = {"minimum_units": [{"id": "d", "units": "3"},
                                     {"id": "e", "units": "3"}]}
        result = rt.search(request, targets, self.metadata, 1)
        self.assertIsNone(result["first_match"])
        self.assertEqual(result["matching_intervals"], [])
        found = rt.search(request, targets, self.metadata, 2)
        self.assertEqual(found["first_match"]["budget_units"], "28")
        self.assertEqual(rt.verify(request, targets, self.metadata, found)["budgets_checked"], 3)

    def test_strict_limits_and_targets(self):
        request = self.request()
        good = {"minimum_units": [{"id": "d", "units": "3"}]}
        for steps in (-1, 257, True, "2", 2.0, None):
            with self.subTest(steps=steps), self.assertRaises(rt.rs.Invalid):
                rt.search(request, good, self.metadata, steps)
        for targets in (
            {}, {"minimum_units": []}, {"minimum_units": [{"id": "d", "units": "0"}]},
            {"minimum_units": [{"id": "unknown", "units": "1"}]},
            {"minimum_units": [{"id": "d", "units": "01"}]},
            {"minimum_units": [{"id": "d", "units": 3}]},
            {"minimum_units": [{"id": "d", "units": "1"}, {"id": "d", "units": "2"}]},
            {"minimum_units": [{"id": "d", "units": str(rt.rs.UINT256_MAX + 1)}]},
            {"minimum_units": [{"id": "d", "units": "1", "address": "none"}]},
        ):
            with self.subTest(targets=targets), self.assertRaises(rt.rs.Invalid):
                rt.search(request, targets, self.metadata, 1)
        request["budget"] = rt.rs.display_units(rt.rs.UINT256_MAX, 18)
        with self.assertRaisesRegex(rt.rs.Invalid, "uint256"):
            rt.search(request, good, self.metadata, 1)

    def test_complete_recomputation_and_tamper(self):
        request = self.request()
        targets = {"minimum_units": [{"id": "d", "units": "3"}]}
        report = rt.search(request, targets, self.metadata, 4)
        for change in (
            lambda r: r.update(extra=True),
            lambda r: r.update(budgets_meeting_all_targets=0),
            lambda r: r["matching_intervals"].pop(),
            lambda r: r["first_match"].update(allocation_sha256="0"),
            lambda r: r.update(budgets_checked=True),
        ):
            changed = copy.deepcopy(report)
            change(changed)
            with self.assertRaises(rt.rs.Invalid):
                rt.verify(request, targets, self.metadata, changed)
        changed_targets = {"minimum_units": [{"id": "d", "units": "4"}]}
        with self.assertRaises(rt.rs.Invalid):
            rt.verify(request, changed_targets, self.metadata, report)

    def test_seeded_oracle(self):
        rng = random.Random(31)
        for _ in range(100):
            count = rng.randrange(2, 10)
            start = rng.randrange(1, 70)
            steps = rng.randrange(0, 20)
            request = {"budget": rt.rs.display_units(start, 18),
                       "contributors": [{"id": "role%02d" % i,
                                         "weight": str(rng.randrange(0, 30))}
                                        for i in range(count)]}
            if not any(int(row["weight"]) for row in request["contributors"]):
                request["contributors"][0]["weight"] = "1"
            target_ids = rng.sample([row["id"] for row in request["contributors"]],
                                    rng.randrange(1, min(4, count) + 1))
            targets = {"minimum_units": [{"id": i, "units": str(rng.randrange(1, 12))}
                                         for i in target_ids]}
            report = rt.search(request, targets, self.metadata, steps)
            oracle = []
            for units in range(start, start + steps + 1):
                candidate = rt.rs.allocate(dict(request, budget=rt.rs.display_units(units, 18)),
                                           self.metadata)
                shares = {row["id"]: int(row["units"]) for row in candidate["allocations"]}
                if all(shares[row["id"]] >= int(row["units"])
                       for row in targets["minimum_units"]):
                    oracle.append(units)
            self.assertEqual(report["budgets_meeting_all_targets"], len(oracle))
            self.assertEqual(None if not oracle else int(report["first_match"]["budget_units"]),
                             None if not oracle else oracle[0])
            from_intervals = [n for row in report["matching_intervals"]
                              for n in range(int(row["first_budget_units"]),
                                             int(row["last_budget_units"]) + 1)]
            self.assertEqual(from_intervals, oracle)
            rt.verify(request, targets, self.metadata, report)

    def test_cli_roundtrip(self):
        scratch = Path.cwd() / "test" / "scratch"
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as temp:
            root = Path(temp)
            (root / "request.json").write_text(json.dumps(self.request()))
            (root / "targets.json").write_text(json.dumps({"minimum_units": [
                {"id": "d", "units": "3"}, {"id": "e", "units": "3"}]}))
            command = [sys.executable, "-B", str(Path(rt.__file__)), "search",
                       "--request", str(root / "request.json"),
                       "--targets", str(root / "targets.json"), "--steps", "3",
                       "--output", str(root / "result.json")]
            run = lambda args: subprocess.run(args, capture_output=True, text=True)
            self.assertEqual(run(command).returncode, 0)
            self.assertEqual(run(command).returncode, 2)
            check = [sys.executable, "-B", str(Path(rt.__file__)), "verify",
                     "--request", str(root / "request.json"),
                     "--targets", str(root / "targets.json"),
                     "--report", str(root / "result.json")]
            self.assertEqual(run(check).returncode, 0)
            (root / "result.json").write_text('{"budgets_checked":4,"budgets_checked":3}')
            self.assertEqual(run(check).returncode, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
