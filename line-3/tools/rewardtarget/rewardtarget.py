#!/usr/bin/env python3
"""Find exact ZTO budgets meeting caller-supplied contributor share floors."""

import argparse
import importlib.util
import re
from pathlib import Path
import sys


SPEC = importlib.util.spec_from_file_location(
    "rewardreceipt", Path(__file__).resolve().parents[1] / "rewardreceipt" / "rewardreceipt.py")
rr = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rr)
rs = rr.rs
MAX_STEPS = 256


def parse_targets(spec, ids):
    rs.require(isinstance(spec, dict) and set(spec) == {"minimum_units"},
               "targets must contain exactly minimum_units")
    rows = spec["minimum_units"]
    rs.require(isinstance(rows, list) and 1 <= len(rows) <= len(ids),
               "minimum_units must be a nonempty list within the roster size")
    targets = {}
    for row in rows:
        rs.require(isinstance(row, dict) and set(row) == {"id", "units"},
                   "each target needs exactly id and units")
        identifier, value = row["id"], row["units"]
        rs.require(isinstance(identifier, str) and identifier in ids,
                   "target id is not in the contributor roster")
        rs.require(identifier not in targets, "duplicate target id")
        rs.require(isinstance(value, str) and re.fullmatch(r"(?:0|[1-9][0-9]*)", value)
                   and len(value) <= 78 and int(value) <= rs.UINT256_MAX,
                   "target units must be a uint256 decimal string")
        targets[identifier] = int(value)
    rs.require(any(value > 0 for value in targets.values()),
               "at least one target must exceed zero")
    return targets


def search(request, targets_spec, metadata, steps):
    """Check every budget from the request's budget through budget + steps."""
    rs.require(type(steps) is int and 0 <= steps <= MAX_STEPS,
               "steps must be an integer from 0 to 256")
    first = rs.allocate(request, metadata)
    start = int(first["budget_units"])
    rs.require(start + steps <= rs.UINT256_MAX, "window exceeds uint256 budget")
    targets = parse_targets(targets_spec, {row["id"] for row in first["allocations"]})
    intervals = []
    opened = None
    first_match = None
    matched_count = 0
    for offset in range(steps + 1):
        units = start + offset
        candidate = (first if offset == 0 else rs.allocate(
            dict(request, budget=rs.display_units(units, metadata["decimals"])), metadata))
        shares = {row["id"]: int(row["units"]) for row in candidate["allocations"]}
        meets = all(shares[identifier] >= floor for identifier, floor in targets.items())
        if meets:
            matched_count += 1
            if first_match is None:
                first_match = {"budget_units": str(units),
                               "budget_amount": candidate["budget_amount"],
                               "allocation_sha256": rr.digest(candidate),
                               "target_shares": [
                                   {"id": identifier, "units": str(shares[identifier])}
                                   for identifier in sorted(targets)]}
            if opened is None:
                opened = units
        elif opened is not None:
            intervals.append({"first_budget_units": str(opened),
                              "last_budget_units": str(units - 1)})
            opened = None
    if opened is not None:
        intervals.append({"first_budget_units": str(opened),
                          "last_budget_units": str(start + steps)})
    return {
        "schema": "rewardtarget-v1",
        "token": first["token"],
        "request_sha256": rr.digest(request),
        "targets_sha256": rr.digest(targets_spec),
        "metadata_sha256": rr.digest(metadata),
        "start_budget_units": str(start), "end_budget_units": str(start + steps),
        "budgets_checked": steps + 1, "budgets_meeting_all_targets": matched_count,
        "first_match": first_match, "matching_intervals": intervals,
        "scope": "complete consecutive-unit search only within this window; arithmetic, not entitlement or payment",
    }


def verify(request, targets, metadata, report):
    rs.require(isinstance(report, dict), "search report must be an object")
    count = report.get("budgets_checked")
    rs.require(type(count) is int, "budgets_checked must be an integer")
    expected = search(request, targets, metadata, count - 1)
    rs.require(rr.canonical_bytes(report) == rr.canonical_bytes(expected),
               "search report differs from complete recomputation")
    return {"schema": "rewardtarget-verification-v1",
            "result": "verified every budget in the stated window",
            "search_sha256": rr.digest(report),
            "budgets_checked": expected["budgets_checked"],
            "first_match": expected["first_match"]}


def demo():
    metadata = rs.read_json(rr.ROOT / "zto-mainnet.json")
    request = {"budget": rs.display_units(25, metadata["decimals"]),
               "contributors": [{"id": name, "weight": str(weight)} for name, weight in
                                zip("abcdef", (1500, 1500, 900, 500, 500, 200))]}
    targets = {"minimum_units": [{"id": "d", "units": "3"},
                                  {"id": "e", "units": "3"}]}
    result = search(request, targets, metadata, 3)
    return {"search": result, "verification": verify(request, targets, metadata, result)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("demo", help="show a target that holds at 25 and 28 units, but not 26 or 27")
    for command in ("search", "verify"):
        entry = sub.add_parser(command)
        entry.add_argument("--request", required=True)
        entry.add_argument("--targets", required=True)
        entry.add_argument("--metadata", default=str(rr.ROOT / "zto-mainnet.json"))
        entry.add_argument("--output", help="new workspace JSON; refuses overwrites")
        if command == "search":
            entry.add_argument("--steps", type=int, required=True)
        else:
            entry.add_argument("--report", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "demo":
            result = demo()
        else:
            request = rs.read_json(args.request)
            targets = rs.read_json(args.targets)
            metadata = rs.read_json(args.metadata)
            result = (search(request, targets, metadata, args.steps) if args.command == "search"
                      else verify(request, targets, metadata, rs.read_json(args.report)))
        rs.write_json(result, getattr(args, "output", None))
    except (rs.Invalid, OSError, ValueError, OverflowError, RecursionError) as exc:
        message = str(exc) if isinstance(exc, rs.Invalid) else type(exc).__name__
        print("rewardtarget: " + message, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
