# RewardTarget

RewardTarget finds which consecutive **atomic ZTO budgets** make a fixed RewardSplit roster meet caller-supplied minimum shares. It reports the first matching budget in the searched window and every contiguous matching interval. It checks each budget separately because largest-remainder shares can fall when the budget grows.

From the repository root, with Python 3.9+ and only the standard library:

```sh
python3 -B line-3/tools/rewardtarget/rewardtarget.py demo
```

Tried here: exit **0**. The demo uses the included real Ethereum ZTO metadata capture (18 decimals) and six illustrative address-free roles. Targets `d >= 3` and `e >= 3` atomic units are met at budgets **25** and **28**, but not **26** or **27**. The output includes both matching intervals and a recomputation receipt. Six tests passed, including 100 seeded searches compared with a direct allocation oracle, malformed and duplicate targets, uint256 boundaries, report tampering and a file-based CLI round trip:

```sh
python3 -B line-3/tools/rewardtarget/selftest.py
```

To use your own request, provide a normal RewardSplit request JSON with a positive starting `budget` and fixed `contributors`. In another JSON file, put exact atomic-unit floors for one or more roster IDs:

```json
{"minimum_units":[{"id":"build","units":"1000000000000000000"}]}
```

Then run:

```sh
python3 -B line-3/tools/rewardtarget/rewardtarget.py search --request REQUEST.json --targets TARGETS.json --steps 100 --output SEARCH.json
python3 -B line-3/tools/rewardtarget/rewardtarget.py verify --request REQUEST.json --targets TARGETS.json --report SEARCH.json
```

`--steps` is 0–256 additional **atomic units**, so `100` checks 101 budgets including the starting budget. A `first_match` of `null` means no budget in this window meets all targets; it makes no claim about budgets outside the window. The first match is the smallest budget **inside this window** that meets all targets. A matching interval may end before a later one starts, as in the demo. `allocation_sha256` identifies the complete RewardSplit report for the first match; reproduce it with the original roster and the reported budget. Verification recomputes every budget and compares the complete result, including hashes and intervals. File inputs follow RewardSplit's workspace-only, duplicate-key-rejecting 256-KiB JSON reader; output uses its bounded writer and refuses to overwrite a file.

The tool inherits RewardSplit's exact arithmetic, 1–1000 contributor bound, uint256 budget limit, and historical ZTO metadata capture. It does no wallet, balance, identity, entitlement, or payment check. Caller IDs and targets are review inputs, not a reward promise. Nothing accesses a key or wallet, signs, sends, posts, pays or uses the network. Exit **0** means a valid complete bounded search or verification, including a window with no match; exit **2** means invalid input, disagreement, bounds, size or I/O failure. Keep the sibling RewardSplit and RewardReceipt folders together.
