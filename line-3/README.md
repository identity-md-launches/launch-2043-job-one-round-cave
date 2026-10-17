# Every Pebble Has a Place

## Step 31: RewardTarget

[RewardTarget](tools/rewardtarget/README.md) checks every atomic ZTO budget in a bounded window for caller-supplied minimum contributor shares. It reports the first matching budget in that window and all matching intervals, including gaps caused by largest-remainder reversals. The offline demo uses the inherited real ZTO metadata: two illustrative targets hold at 25 and 28 units, but fail at 26 and 27. Six tests passed, including 100 seeded direct-allocation comparisons.

```sh
python3 -B line-3/tools/rewardtarget/rewardtarget.py demo
```

The new charcoal and ochre bowl sits on bare right rock. The 1254 × 1254 finished PNG is `artifacts/line-3/wall-v14.png`, also available through `wall.png`; its 512 × 512 JPEG is `dist/line-3/31.jpg`. Only 1,875 pixels within a 132 × 104 patch changed. Both ancestral Pepe figures, the visible five-digit hand and prior marks remain unchanged. [Step 31 review](step-31-review.json) records formats, dimensions, visual limits and checks. No unmet visual requirement was observed.

## Step 28: RewardBounds

[RewardBounds](tools/rewardbounds/README.md) allocates exact ZTO rewards while honoring caller-supplied minimum shares and maximum caps. It reserves minima, redistributes the remaining budget by positive weights up to each cap, and rounds deterministically without losing atomic units. The address-free demo verifies exactly **1 ZTO = 0.4 + 0.25 + 0.25 + 0.1**. Its 15 tests passed, including more than 300 cases checked by exhaustive enumeration and 100 unbounded comparisons with RewardSplit.

```sh
python3 -B line-3/tools/rewardbounds/rewardbounds.py demo
```

This step also repairs RewardSplit's large-report handoff: reports use compact JSON when indentation would exceed the shared reader's 256-KiB limit, and refuse irreducible oversize before writing. A previously unreadable 1,000-contributor report now round-trips through RewardReceipt with unchanged allocations. All **77 inherited tests** and seven demos passed. RewardBounds has its own report schema and its own recomputation verifier; use that verifier for its reports.

The new mark is a charcoal bowl between two ochre standing stones, representing rewards kept within promised bounds. The finished **1254 × 1254 PNG** is `artifacts/line-3/wall-v9.png`, also reached through canonical `wall.png`. Its record is `dist/line-3/28.json`; `28.jpg` is **512 × 512**, 54,001 bytes. Every pixel outside the new 143 × 66 bare-rock patch remains identical, including both ancestral Pepes and the five-digit hand. [Step 28 review](step-28-review.json) records dimensions, formats, checks and limitations; [image notes](asset-build/README-28.md) record the built-in imagegen prompt and preservation method. No unmet visual requirement was observed.

## Step 27: RewardAudit

[RewardAudit](tools/rewardaudit/README.md) independently checks exact integer quota floors and the rounding winner/loser boundary of a saved allocation. It explains fractional quotas, remainders and ties at the cutoff. The address-free demo conserves exactly 1 ZTO and explains why `build` receives the last atomic unit. Thirteen tests passed, including 250 cases checked by exhaustive award-subset enumeration; the 23 inherited RewardSplit/RewardReceipt tests also passed.

```sh
python3 -B line-3/tools/rewardaudit/rewardaudit.py demo
```

The new mark is two charcoal bowls with red ochre pebbles, an ochre arch and one chalk pebble above their gap. The finished wall is `artifacts/line-3/wall-v8.png`, also saved as `wall.png`: **1254 × 1254 RGB PNG**. Record `dist/line-3/27.json` names its SHA-256; `27.jpg` is a **512 × 512 JPEG, 53,774 bytes**. Only 2,817 pixels changed in a 150 × 92 bare-rock patch; every pixel outside it remains identical. [Step 27 review](step-27-review.json) records the visual inspection, formats, limits and checks. No unmet visual requirement was observed in the finished PNG or JPEG.

## Step 25: RewardWindow

[RewardWindow](tools/rewardwindow/README.md) exhaustively scans a short run of consecutive atomic ZTO budgets and identifies every point where a contributor's largest-remainder share falls as the total rises. It verifies the saved scan by recomputation from the original request and metadata. Its offline demo returned 0 and found the 25→26-unit reversal for two illustrative, address-free roles; all five tests passed, including 40 seeded windows.

```sh
python3 -B line-3/tools/rewardwindow/rewardwindow.py demo
```

The new cave mark is a rising line of four charcoal bowls with ochre pebbles. The 1254 × 1254 PNG is `artifacts/line-3/wall-v6.png`, also available as canonical `wall.png`; the 512 × 512 JPEG is `dist/line-3/25.jpg` (62,972 bytes). Every pixel outside the painted patch is identical to the inherited wall. [Step 25 review](step-25-review.json) records image formats, dimensions, visual checks and limitations. No unmet visual requirement was identified.

## Step 24: RewardBatch

[RewardBatch](tools/rewardbatch/README.md) divides a verified ZTO allocation into bounded review batches and verifies the whole bundle against the original request, report and token capture. Every contributor appears exactly once, including zero-unit shares. It neither prepares nor sends payments.

```sh
python3 -B line-3/tools/rewardbatch/rewardbatch.py demo
```

The offline demo returned 0: two batches of two and one contributors retain exactly 1 ZTO. Eleven tests passed, including 160 seeded partitions and file-based CLI checks. The new cave mark is three charcoal bowls enclosed by an ochre loop. Every pixel outside its bare-rock rectangle, including both ancestral Pepes and the five-digit hand, remains unchanged. The required `artifacts/line-3/wall-v5.png` and canonical `wall.png` are PNG, 1254 × 1254; `dist/line-3/24.jpg` is JPEG, 512 × 512, below 100 KB. [Step 24 review](step-24-review.json) records the built-in imagegen prompt, checks and visual limitations. No unmet visual requirement was identified.

## Step 23: RewardCompare

[RewardCompare](tools/rewardcompare/README.md) verifies and compares two reward allocations when the budget changes. It exposes per-contributor signed unit changes and flags largest-remainder budget paradoxes for review. Its offline demo deliberately returns exit 1: increasing a tiny ZTO budget from 25 to 26 units reduces two shares. Eleven tests (including 250 seeded comparisons) and file-based CLI trials passed.

```sh
python3 -B line-3/tools/rewardcompare/rewardcompare.py demo
```

The new mark adds two charcoal bowls with three and two ochre pebbles under an ochre bridge, on previously bare upper-middle rock. Both ancestral Pepes and the existing five-digit hand remain pixel-identical. The required `artifacts/line-3/wall-v4.png` is PNG, 1254 × 1254; canonical `wall.png` points to it. `dist/line-3/23.jpg` is JPEG, 512 × 512 and below 100 KB. The record is `dist/line-3/23.json`. [Step 23 review](step-23-review.json) records formats, the generation prompt, tests, preservation bounds and visual limitations. No unmet visual requirement was identified in the full-size and thumbnail review.

## Step 22: RewardReceipt

[RewardReceipt](tools/rewardreceipt/README.md) verifies a saved allocation against its request and token metadata, then prints a canonical review receipt. Its offline demo and eight checks passed. The new wall mark adds a smaller Pepe comparing matching pebbles; its dimensions, formats and visual review are in [step-22-review.json](step-22-review.json).

Line 3 began with [RewardSplit](tools/rewardsplit/README.md), a standard-library Python allocator using real ZTO metadata and exact largest-remainder arithmetic. Its fixed goal is exact ZTO reward allocation for workers.

From the repository root:

```sh
python3 -B line-3/tools/rewardsplit/rewardsplit.py demo
```

The offline demo splits 1 ZTO among three illustrative task roles, distributes the one leftover smallest unit deterministically, and leaves zero units unallocated. A live, read-only Ethereum observation confirmed the metadata. All 15 offline tests passed, including 300 seeded conservation and proportionality cases. The tool README documents the input format, exact observation, limits, and tests.

The wall adds a charcoal-and-ochre Pepe dividing pebbles among three bowls. It begins from the supplied bare cave; there were no ancestor marks on this line. The square image retains the cave's framing, torchlit warm rock, recognizable cracks and floor, and leaves most of the upper/right wall for future additions. Pepe has one visible hand: four fingers and one thumb. The other hand is concealed. There are no handprints, letters, numerals, captions, signatures, or logos.

The finished wall is `artifacts/line-3/wall.png`: **PNG, 1254 × 1254**. Its companion is `dist/line-3/01.jpg`: **JPEG, 512 × 512**, under 100 KB. The only saved pictures are those two required deliverables. The numbered metadata is `dist/line-3/01.json`; its image URL contains the SHA-256 of the actual wall bytes. The PNG is left untracked for the output uploader.

The worker explicitly reviewed the generated full-size image and the encoded thumbnail. No unmet visual requirement was identified; generative editing cannot certify pixel-exact preservation of every rock texture. Dimensions, formats, hand count, and limitations are also recorded in [review.json](review.json).

The built-in imagegen tool edited the bare cave. Its prompt asked for a modest first prehistoric mark on the lower-left rock face: recognizable heavy-lidded Pepe, three shallow bowls and ochre pebbles, exactly five digits on the sole visible hand, earth pigments with bare stone showing through, unchanged cave dimensions/lighting/framing, abundant untouched space, and no text, logos, stencils, or photographic/3D figures. The JPEG is a 512-pixel conversion of that finished wall.

No coins are required to run this piece. It computes allocations and reads public token metadata; it does not access wallets or send payments.

## Step 26: RewardMerge

[RewardMerge](tools/rewardmerge/README.md) verifies and totals independent ZTO allocation rounds without re-rounding their shares. It preserves each round's receipt and flags identical reports that could have been entered twice. The address-free demo sums exactly 3 ZTO; 11 tests passed, including 100 seeded multi-round conservation cases.

```sh
python3 -B line-3/tools/rewardmerge/rewardmerge.py demo
```

The new mark joins two ochre pebble streams in one charcoal bowl. The full wall is `artifacts/line-3/wall-v7.png`, also available as `wall.png`; its record and 512-pixel JPEG are `dist/line-3/26.json` and `26.jpg`. [Step 26 review](step-26-review.json) records formats, dimensions, preservation and visual limitations.
