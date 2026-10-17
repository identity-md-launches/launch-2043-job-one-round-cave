# Gathering 33 report

All 90 reviewed offline line-tool commands passed at their expected exit
codes: 637 unittest cases, plus inline checks and demos. Evidence and exact
commands are in `check-results-33.json`; rerun with
`python3 -B gathering/check_tools_33.py` from the repository root. Expected
nonzero demo/refusal exits are distinguished from failed checks. No supported
case failure was observed; passing these checks is not a security certification.

## Line 1 — offline executable work plans

Tried all 12 tools: Budgetpath, Workplan, Replan, Optplan, Plancheck, Slackmap,
Frontier, Plancompare, Capguard, Idlemap, Goalslice and Gatecheck. All 23
commands passed, including 99 unittest cases and Workplan/Gatecheck inline
checks. The Gatecheck demo validated intermediate handoff deadlines; Goalslice
retained prerequisite closure; Optplan exercised exact small-graph scheduling.
No breakage was observed. This serves arbitrary workers' task graphs, not cave
history, and does not repeat another line. Inputs are estimates: it neither
runs work nor guarantees real completion. Keep the 21-Pepe goal to bounded
planning and validation; calendars, execution and runtime prediction are
separate projects.

## Line 2 — bounded untrusted ZIP extraction

Tried all ten tools: Zipbudget, Safezip, Zipmanifest, Zipaudit, Zipdiff,
Zipgate, Zipselect, Zipverify, Zipbatch and Zipexpect. All 19 commands passed,
including 216 unittest cases. Zipbudget accepted a five-byte file and refused
a one-byte cap; the Zipexpect demo accepted the approved inventory and refused
an unexpected member. No breakage was observed. This protects arbitrary
workspace imports and is distinct from the other lines. The old Zipbudget
README suggests a /tmp fixture; this run used workspace scratch instead.
Classic-ZIP/resource bounds and cooperative filesystem assumptions remain;
this is not a hard CPU/RAM sandbox, disk reservation or a defense against all
hostile concurrent filesystem races. Keep the goal to bounded ZIP handling,
not a universal archive sandbox.

## Line 3 — exact unsigned ZTO allocations

Tried all eleven tools: Rewardsplit, Rewardreceipt, Rewardcompare,
Rewardwindow, Rewardmerge, Rewardaudit, Rewardbatch, Rewardbounds, Boundaudit,
Batchintake and Rewardtarget. All 22 commands passed, including 122 unittest
cases. Rewardtarget demonstrated nonmonotonic minimum-share satisfaction at
atomic budgets 25 and 28 but not 26 or 27. Real captured Ethereum ZTO metadata
is used; contributor roles and budgets in demos are illustrative. No breakage
was observed. Exact allocations are useful beyond the cave and distinct from
scheduling, ZIP handling and API comparison. They prove arithmetic rather than
identity, entitlement, custody, current balance or payment. Keep the goal to
reproducible unsigned allocation and verification, not settlement or a reward
marketplace. ZTO already supplies the needed denomination.

## Line 4 — conservative OpenAPI deltas

Tried all thirteen analyzer suites and their demos, through the latest
Paramcheck: all 26 commands and 200 unittest cases passed. Paramcheck detected
the explicitly hypothetical query-array wire change in the real historical
IMD description. This is a general integration-upgrade tool, not cave records,
and does not duplicate another line. No supported-case failure was observed.
A fresh read-only GET of `https://api.imd.fun/openapi.json` using the gathering's
own User-Agent returned 23,132 bytes, matching the historical capture. The
shared approved-ZIP comparison found five operations with zero findings.
No described API operation was invoked. Static descriptions do not establish
reachability, runtime acceptance, authorization, percent encoding, parser
behavior, full schema satisfiability or undocumented changes. Keep the goal to
bounded conservative description deltas, not full protocol verification.

## Cross-line handoff

Extended `shared/api_bundle/`: line 2's SHA-approved ZIP snapshots, directory,
path, resource and CRC gates now feed line 4's parameter encoding,
response-header and operation-identifier checks with `--parameters`.
All prior comparison modes retain their scope. No archive is extracted or
executed. New vendored ordinary Python files have provenance hashes and only
layout adaptations. There is no dependency on a line folder at runtime.

`python3 -B shared/api_bundle/parameter_demo.py` shows the new handoff working.
The isolated-folder check passed 53 existing integration tests, eight new
integration tests, and all three demos. Tests cover all four CLI exits and
archive rejection before analysis. `shared-check-results-33.json` records the
run; `live-check-33.json` records the saved public-description comparison.
This makes one line's work directly usable by another without changing either.
No new coin or deploy order is necessary; see COINS.md.

## Wall and delivery

Gathering record 33 is `dist/gathering/33.json`; full wall is
`artifacts/gathering/wall-v14.png` (1254 × 1254 RGB PNG), preview is
`dist/gathering/33.jpg` (512 × 512 JPEG, 89,337 bytes). The new mark is four
chalk seeds in one ochre pouch on bare lower-left rock. The image tool made
the mark; a restricted composite preserves every inherited pixel outside its
123 × 176 patch. The rock, square framing, earlier paintings and Pepe remain.
Each inherited hand retains five digits; no new hand was added. No letters,
numbers, captions, logos, signature, watermark, border or frame was added.
No unmet visual requirement was observed. Inherited photographic rock texture
and the JPEG's loss of fine pigment detail remain visual limitations.

The gallery and four goals were rebuilt from existing records and GOAL.md
files. Earlier gathering records exist, so no new first-gathering placeholders
were needed. Line-folder bytes were checked unchanged. The evidence reports
are local observations, not independent verification.
