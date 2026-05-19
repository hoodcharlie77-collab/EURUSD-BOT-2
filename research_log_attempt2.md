# Attempt 2 Research Log

## 2026-05-19 - Compression / Expansion Read

Scope reset:
- EURUSD only.
- Daytrading context.
- Timeframe still under review.
- Current visual training chart: 5-minute candles.
- Current Bollinger setting under review: `BB(5, 4 std)`.

Current shared hypothesis:

```text
compression box
-> first expansion attempt
-> possible headfake / liquidity probe
-> failure back through compression
-> opposite-side expansion may be the real move
```

Important correction:
- The edge is probably not simple Bollinger breakout continuation.
- The first expansion out of compression may be bait.
- A failed first expansion followed by an opposite-side break may be more valuable than the first break itself.

Visual definition being trained:
- Compression: overlapping candles, reduced progress, contained price, and comparatively narrow Bollinger structure.
- Expansion: directional displacement out of that contained area with bands opening.
- Headfake: first displacement fails to hold and price re-enters or crosses back through the compression area.

Process:
- Before numerical backtests, repeatedly mark 12-hour chart samples.
- Compare human and model annotations.
- Convert only the agreed visual behavior into code.

## Training Sample 001 - 2024-02-07 01:00-13:00 UTC

Settings:
- EURUSD 5-minute candles.
- `BB(5, 4 std)`.
- 12-hour visual window.

Model annotations:
- A: 01:45-03:10 UTC compression/balance, followed by downside expansion into 04:15.
- B: 04:10-05:20 UTC base compression, followed by upside expansion into 06:10.
- C: 06:05-06:55 UTC chop/coil. Downside probe fails, then upside expansion becomes the real move into 07:35.
- D: 07:35-08:10 UTC high compression/distribution, followed by downside expansion into 08:45.
- 09:35-11:05 UTC marked as messy/no clean read, not a clean compression signal.

Open review:
- User should challenge any box or arrow that does not match the visual read.
- Especially review C, because failed probe -> opposite-side real expansion is central to the emerging hypothesis.

## Training Sample 002 - 2024-02-29 10:05-22:05 UTC

Settings:
- EURUSD 5-minute candles.
- `BB(5, 4 std)`.
- 12-hour visual window.

User correction:
- Use only the core visual compression rule for this pass.
- Mark overlapping/no-progress areas.
- Box the selected candle overlap range.
- Do not add expansion arrows, headfake labels, or messy-zone labels.

Model compression boxes:
- A: 11:00-11:40 UTC.
- B: 12:05-13:05 UTC.
- C: 17:25-18:10 UTC.
- D: 18:45-19:25 UTC.
- E: 20:05-22:00 UTC.

Open review:
- A and B are weaker because they occur inside broader directional movement.
- C, D, and E are cleaner balance/compression candidates.

User feedback:
- Keep boxes 2, 3, 4, and 5.
- Reject box 1.
- All chart labels and logs should move to New York time (`America/New_York`).
- End of the New York session is slow/garbage and should be filtered out.

Implementation note:
- Unless corrected, use `15:00-17:00 New York time` as the late-NY exclusion window.
- Any compression inside that time window can be visually noted, but should not become a valid training/backtest signal.

## Training Sample 003 - 2024-02-27 17:35-2024-02-28 05:35 EST

Settings:
- EURUSD 5-minute candles.
- `BB(5, 4 std)`.
- 12-hour visual window.
- Chart labels in New York time.
- Late New York exclusion applied: window does not overlap `15:00-17:00 America/New_York`.

Model compression boxes using only overlap/no-progress rule:
- A: 22:45-00:15 EST.
- B: 00:50-01:35 EST.
- C: 04:30-04:55 EST.

Model note:
- This sample is mostly a directional downtrend.
- Do not force compression boxes into the directional sections.
- A is the cleanest low-width compression.
- B is acceptable but occurs during continued bearish drift.
- C is a possible base after the selloff, but BB width is already elevated, so price overlap and BB-width compression disagree.

User feedback:
- All three Sample 003 boxes are correct.

## Training Sample 004 - 2024-02-07 02:30-14:30 EST

Settings:
- EURUSD 5-minute candles.
- `BB(5, 4 std)`.
- 12-hour visual window.
- Chart labels in New York time.
- Late New York exclusion applied: window does not overlap `15:00-17:00 America/New_York`.

Model compression boxes using only overlap/no-progress rule:
- A: 02:35-03:00 EST.
- B: 03:30-04:25 EST.
- C: 04:45-05:45 EST.
- D: 06:25-07:45 EST.
- E: 09:05-10:45 EST.
- F: 11:25-12:35 EST.
- G: 13:10-14:25 EST.

Model note:
- This sample is choppy/rangy with several legitimate balance zones.
- E is the weakest candidate because it contains a wide spike/large intrabox range, but it still has overlapping rotation and no clean directional progress until the break.

User feedback:
- A, B, C, and D are correct.
- E and F are wrong.
- G is correct.

Rule refinement:
- Do not box broad rotational chop just because it is sideways.
- Compression needs tight overlapping candles, not wide swings inside a large range.

## Training Sample 005 - 2024-02-06 01:30-13:30 EST

Settings:
- EURUSD 5-minute candles.
- `BB(5, 4 std)`.
- 12-hour visual window.
- Chart labels in New York time.
- Late New York exclusion applied: window does not overlap `15:00-17:00 America/New_York`.

Model compression boxes using tightened overlap/no-progress rule:
- A: 02:25-03:25 EST.
- B: 05:10-06:15 EST.
- C: 08:20-09:15 EST.
- D: 10:20-11:10 EST.
- E: 11:45-13:05 EST.

Model note:
- Avoided boxing the fast directional selloff from 03:40-05:00 and the sharp swings around 07:00-08:10 and 09:20-10:00.
- A and C may be borderline because they sit near wider recent movement.
- E is the cleanest tight high-level compression.

User feedback:
- A, C, D, and E are correct.
- B is wrong.

Rule refinement:
- A box can be valid even if it follows/preceds expansion, but the candles inside must compress tightly.
- Reject boxes that are really loose countertrend chop with too much intrabox travel.

## Training Sample 006 - 2024-02-13 18:05-2024-02-14 06:05 EST

Settings:
- EURUSD 5-minute candles.
- `BB(5, 4 std)`.
- 12-hour visual window.
- Chart labels in New York time.
- Late New York exclusion applied: window does not overlap `15:00-17:00 America/New_York`.

Model compression boxes:
- A: 18:10-19:15 EST.
- B: 20:30-21:25 EST.
- C: 21:35-01:45 EST.
- D: 04:15-05:45 EST.

Model note:
- A is tight and clean.
- B is acceptable but follows a spike; the box itself is overlap/no-progress.
- C is a long low-volatility compression shelf before the 02:00 expansion.
- D is a post-expansion lower balance; possible but less clean because the prior volatility regime is elevated.

User feedback:
- A, C, and D are correct.
- B is wrong.

Rule refinement:
- Be stricter on post-spike recovery areas.
- Do not box the early transition after a spike unless the candles settle into a clearly tight overlap.

## Training Sample 007 - 2024-02-09 01:00-13:00 EST

Settings:
- EURUSD 5-minute candles.
- `BB(5, 4 std)`.
- 12-hour visual window.
- Chart labels in New York time.
- Late New York exclusion applied: window does not overlap `15:00-17:00 America/New_York`.

Model compression boxes:
- A: 01:05-01:45 EST.
- B: 02:15-03:05 EST.
- C: 04:55-06:35 EST.
- D: 06:45-08:20 EST.
- E: 09:55-11:45 EST.
- F: 11:55-13:00 EST.

Model note:
- The 08:30-09:45 expansion spike is intentionally unboxed.
- E begins only after post-spike candles settle into overlap.
- D is the most questionable because it is a pre-spike base but has a wider intrabox range than A/C.

User feedback:
- A, B, C, E, and F are correct.
- D is wrong.

Rule refinement:
- Do not box a broad pre-spike transition just because it precedes expansion.
- Pre-expansion compression still needs tight overlap; anticipation is not enough.

## Training Sample 008 - 2024-02-22 21:05-2024-02-23 09:05 EST

Settings:
- EURUSD 5-minute candles.
- `BB(5, 4 std)`.
- 12-hour visual window.
- Chart labels in New York time.
- Late New York exclusion applied: window does not overlap `15:00-17:00 America/New_York`.

Model compression boxes:
- A: 21:45-22:35 EST.
- B: 22:45-00:15 EST.
- C: 00:35-01:25 EST.
- D: 02:20-03:25 EST.
- E: 04:45-05:25 EST.
- F: 06:35-07:20 EST.
- G: 08:10-09:00 EST.

Model note:
- The 07:30 expansion candle sequence is intentionally unboxed.
- B is the cleanest low-volatility shelf.
- E may be questionable because it contains the reversal from the selloff low rather than a fully settled shelf.
- G is post-spike settling; included because candles overlap after the impulse, but it may be too loose.

## Blind Training Sample 009 - 2024-02-01 21:00 EST Start

Settings:
- EURUSD 5-minute candles.
- `BB(5, 4 std)`.
- New York time.
- Future hidden after the final displayed box.
- Boxes shown outline-only so price bars remain visible.

Model boxes:
- Box 1: 21:15-23:10 EST.
- Box 2: 23:40-01:35 EST.

User feedback:
- Box 1: maybe correct.
- Box 2: wrong.

Rule refinement:
- Reject boxes with too much internal directional travel, even if the broad high-low range looks bounded.
- Relative context helps, but future after the current evaluated box should remain hidden.

## Blind Training Sample 010 - 2024-02-09 03:00 EST Start

Settings:
- EURUSD 5-minute candles.
- `BB(5, 4 std)`.
- New York time.
- Future hidden after Box 2.
- Boxes shown outline-only so price bars remain visible.

Model boxes:
- Box 1: 03:45-04:30 EST.
- Box 2: 05:10-06:15 EST.

User feedback:
- Box 1 is correct.
- Box 2 is correct.

Rule refinement:
- Add explicit box shape awareness: `aspect = duration_minutes / range_pips`.
- Square-looking boxes are bad.
- Long rectangles are preferred.
- Medium rectangles are valid.
- Short rectangles are maybe, but can be correct when internal overlap is clean.

## Blind Training Sample 011 - 2024-02-02 00:00 EST Start

Settings:
- EURUSD 5-minute candles.
- `BB(5, 4 std)`.
- New York time.
- Future hidden after Box 2.
- Shape rule active: `aspect = duration_minutes / range_pips`.

Model boxes:
- Box 1: 00:35-01:40 EST, aspect 10.61.
- Box 2: 02:20-03:05 EST, aspect 5.38.

User feedback:
- Box 1 is strong yes.
- Box 2 is yes.

Rule note:
- Long rectangles are high-confidence when internal overlap is clean.
- Short rectangles can still be valid when the internal travel is contained and the candles overlap.

## Blind Training Sample 012 - 2024-02-01 01:30 EST Start

Settings:
- EURUSD 5-minute candles.
- `BB(5, 4 std)`.
- New York time.
- Future hidden after Box 2.
- Shape rule active: `aspect = duration_minutes / range_pips`.

Model boxes:
- Box 1: 02:20-02:45 EST, aspect 5.45, range 5.5 pips.
- Box 2: 04:45-05:45 EST, aspect 7.39, range 8.8 pips.

User feedback:
- Box 1 is strong yes.
- Box 2 is yes.

Rule note:
- Aspect around 5.4 can still be strong when the rectangle is short but the candle overlap is tight and price travel is contained.
- A medium/long shelf near aspect 7+ remains valid when progress is minimal relative to range.

## Blind Training Sample 013 - 2024-02-15 01:05 EST Start

Settings:
- EURUSD 5-minute candles.
- `BB(5, 4 std)`.
- New York time.
- Future hidden after Box 2.
- Shape rule active: `aspect = duration_minutes / range_pips`.

Model boxes:
- Box 1: 04:30-05:45 EST, aspect 12.90, range 6.2 pips.
- Box 2: 06:05-07:20 EST, aspect 11.76, range 6.8 pips.

User feedback:
- Box 1 is correct.
- Box 2 is correct.

Rule note:
- Long, narrow rectangles with contained net progress remain strong compression candidates.
- The user accepted both boxes even though Box 1 included some internal wick travel, so the shape/containment rule can tolerate controlled internal noise when the shelf is obvious.

## Blind Training Sample 014 - 2024-02-25 23:40 EST Start

Settings:
- EURUSD 5-minute candles.
- `BB(5, 4 std)`.
- New York time.
- Future hidden after Box 2.
- Shape rule active: `aspect = duration_minutes / range_pips`.

Model boxes:
- Box 1: 23:40-01:20 EST, aspect 18.10, range 5.8 pips.
- Box 2: 05:30-07:10 EST, aspect 10.82, range 9.7 pips.

User feedback:
- Box 1 is correct.
- Box 2 is correct.

Rule note:
- Very long, flat rectangles remain high-confidence compression when the range stays tight.
- A higher box with modest upward drift can still count as compression if the candles stay contained and the BB width is not expanding aggressively.

## Blind Training Sample 015 - 2024-02-27 20:35 EST Start

Settings:
- EURUSD 5-minute candles.
- `BB(5, 4 std)`.
- New York time.
- Future hidden after Box 2.
- Shape rule active: `aspect = duration_minutes / range_pips`.

Model boxes:
- Box 1: 20:40-22:00 EST, aspect 18.09, range 4.7 pips.
- Box 2: 22:30-00:10 EST, aspect 25.61, range 4.1 pips.

User feedback:
- Box 1 is correct.
- Box 2 is correct.
- User note: boxes can be shorter horizontally; these accepted boxes are quite long.

Rule note:
- Long shelves are valid, but future samples should include shorter compression boxes so the detector does not overfit to only obvious long rectangles.
- Next sampling pass should cap box duration around 80 minutes unless a longer candidate is specifically being tested.

## Blind Training Sample 016 - 2024-02-07 22:15 EST Start

Settings:
- EURUSD 5-minute candles.
- `BB(5, 4 std)`.
- New York time.
- Future hidden after Box 2.
- Shorter box-width pass: max 16 bars / 80 minutes.

Model boxes:
- Box 1: 22:20-23:35 EST, aspect 11.76, range 6.8 pips.
- Box 2: 00:30-01:35 EST, aspect 14.00, range 5.0 pips.

User feedback:
- Box 1 is wrong.
- Box 2 is correct.

Rule note:
- Aspect alone is not enough. Box 1 had a valid rectangle ratio, but it covered too much internal two-way rotation and a visible upswing/downturn cycle rather than a clean compression shelf.
- Box 2 is valid because the candles settle into a tighter, more horizontal shelf after the prior directional push.
- Add stronger penalty for internal swing structure inside the box: compression should look like contained overlap, not a mini range cycle with a rounded top/bottom.

## Anti-Curve-Fit Protocol

Goal:
- Build an evergreen, classic compression detector, not a one-month curve-fit.

Simple rule stack:
- Use only a small number of durable visual concepts: range compression, time containment, clean overlap, and BB-width context.
- Do not add a custom filter for every wrong sample.
- Use wrong samples to clarify broad concepts only.
- Mix obvious, medium, and borderline candidates in blind charts so the model is not trained only on easy wins.

Current caution:
- The model is overconfident on long flat shelves.
- The next batch must include shorter and borderline candidates while keeping the same `BB(5, 4 std)` context.

## Blind Training Sample 017 - 2024-02-08 23:55 EST Start

Settings:
- EURUSD 5-minute candles.
- `BB(5, 4 std)`.
- New York time.
- Future hidden after Box 2.
- Mixed blind selection: one stronger candidate plus one mid-ranked/borderline candidate where possible.

Model boxes:
- Box 1: 00:15-01:25 EST, aspect 17.44, range 4.3 pips.
- Box 2: 05:30-06:45 EST, aspect 10.81, range 7.4 pips.

User feedback:
- Box 1 is correct.
- Box 2 is correct.

Strategy-level note:
- The setup is compression > expansion, but the breakout between compression and expansion can headfake.
- The important effect is the compression itself, which is usually preceded by or followed by a higher-expansion/trend period.
- Do not later code expansion as "the first breakout candle after compression must be the real move." That would be curve-fit bullshit.
- Expansion should be treated as a nearby volatility/trend regime around compression, not just the first band break.

## Blind Training Sample 018 - 2024-02-02 01:25 EST Start

Settings:
- EURUSD 5-minute candles.
- `BB(5, 4 std)`.
- New York time.
- Future hidden after Box 2.
- Mixed blind selection: one stronger candidate plus one mid-ranked/borderline candidate where possible.

Model boxes:
- Box 1: 01:25-02:05 EST, aspect 6.72, range 6.7 pips.
- Box 2: 06:25-07:35 EST, aspect 11.36, range 6.6 pips.

User feedback:
- Box 1 is correct.
- Box 2 is correct.

Rule note:
- A 45-minute box can be valid if candles stay contained and overlap cleanly.
- The lower acceptable aspect boundary is not a hard rejection around 6-7 when visual containment is clear.

## Blind Training Sample 020 - 2024-02-28 22:40 EST Start

Settings:
- EURUSD 5-minute candles.
- `BB(5, 4 std)`.
- New York time.
- Future hidden after Box 2.
- Mixed blind selection with duplicate-window guard.

Model boxes:
- Box 1: 00:10-01:20 EST, aspect 14.42, range 5.2 pips.
- Box 2: 01:45-02:40 EST, aspect 7.69, range 7.8 pips.

User feedback:
- Box 1 is maybe correct.
- Box 2 is wrong.

Rule note:
- Do not treat low net progress as compression by itself.
- Box 2 had contained price, but BB width was still elevated and the candles were too volatile inside the box.
- Robust rule refinement: compression needs contained price plus quieting/contracted volatility context. A wide-band noisy pause after volatility expansion is not enough.

## Blind Training Sample 021 - 2024-02-22 22:35 EST Start

Settings:
- EURUSD 5-minute candles.
- `BB(5, 4 std)`.
- New York time.
- Future hidden after Box 2.
- Mixed blind selection with duplicate-window guard.

Model boxes:
- Box 1: 23:20-00:30 EST, aspect 17.44, range 4.3 pips.
- Box 2: 00:50-02:05 EST, aspect 12.50, range 6.4 pips.

User feedback:
- Box 1 is maybe correct.
- Box 2 is wrong.

Rule note:
- This repeats the Sample 020 problem: a rectangle with decent aspect can still be wrong when the box captures a volatile pause / internal swing instead of quiet overlap.
- Box 2 had too much directional structure and BB-width noise inside the rectangle.
- Keep the rule simple: valid compression is a quiet shelf. It is not just "price stayed inside a rectangle."

## Blind Training Sample 022 - 2024-02-21 19:45 EST Start

Settings:
- EURUSD 5-minute candles.
- `BB(5, 4 std)`.
- New York time.
- Future hidden after Box 2.
- Mixed blind selection with duplicate-window guard.

Model boxes:
- Box 1: 19:45-20:50 EST, aspect 13.73, range 5.1 pips.
- Box 2: 22:10-23:20 EST, aspect 16.67, range 4.5 pips.

User feedback:
- Box 1 is correct.
- Box 2 is correct.

Rule note:
- Both boxes support the simple shelf rule: contained price, modest internal movement, and quieter BB-width context.
- Do not reject a valid shelf only because it has a mild slope or occurs after hours; the visual compression quality is still primary.

## Blind Training Sample 023 - 2024-02-04 21:35 EST Start

Settings:
- EURUSD 5-minute candles.
- `BB(5, 4 std)`.
- New York time.
- Future hidden after Box 2.
- Mixed blind selection with duplicate-window guard.

Model boxes:
- Box 1: 22:10-23:25 EST, aspect 12.50, range 6.4 pips.
- Box 2: 23:55-00:50 EST, aspect 9.52, range 6.3 pips.

User feedback:
- Box 1 is correct.
- Box 2 is probably correct.

Rule note:
- Treat Box 2 as a weak yes / lower-confidence acceptance.
- BB width is context, not an automatic hard reject. If price action forms a usable shelf, elevated or imperfect BB-width behavior can still be acceptable.
- Keep the simple hierarchy: visual shelf quality first, BB-width quieting second.

## Blind Training Sample 024 - 2024-02-21 03:25 EST Start

Settings:
- EURUSD 5-minute candles.
- `BB(5, 4 std)`.
- New York time.
- Future hidden after Box 2.
- Mixed blind selection with duplicate-window guard.

Model boxes:
- Box 1: 05:25-06:20 EST, aspect 10.34, range 5.8 pips.
- Box 2: 06:40-07:50 EST, aspect 9.15, range 8.2 pips.

User feedback:
- Box 1 is correct.
- Box 2 is correct.

Rule note:
- Mild slope is acceptable when the candles remain contained and the band context is quiet enough.
- Aspect around 9-10 remains valid when the shelf is visually clean.

## Blind Training Sample 025 - 2024-02-20 00:40 EST Start

Settings:
- EURUSD 5-minute candles.
- `BB(5, 4 std)`.
- New York time.
- Future hidden after Box 2.
- Mixed blind selection with duplicate-window guard.

Model boxes:
- Box 1: 01:20-02:20 EST, aspect 11.02, range 5.9 pips.
- Box 2: 06:10-07:15 EST, aspect 7.69, range 9.1 pips.

User feedback:
- Box 1 is correct.
- Box 2 is correct.

Rule note:
- Box 2 confirms that a wider shelf can still be valid when it is visually contained after an expansion/trend leg.
- The core rule remains simple: contained shelf first, BB context second, no bespoke curve-fit filters.

## Generalization Step

Reason:
- The February-only duplicate guard started timing out by Sample 026.
- Continuing to mine the same month risks curve fitting the detector to February structure.

Protocol update:
- Keep the same compression settings and visual rules.
- Start adding out-of-Feb blind samples.
- Do not change BB settings just because the sample month changes.
- The detector should survive different calendar periods if the rule is truly evergreen.

## Blind Training Sample 026 - 2024-03-08 00:30 EST Start

Settings:
- EURUSD 5-minute candles.
- `BB(5, 4 std)`.
- New York time.
- Future hidden after Box 2.
- Mixed blind selection with duplicate-window guard.
- First out-of-Feb generalization sample: March 2024.

Model boxes:
- Box 1: 00:35-01:50 EST, aspect 16.00, range 5.0 pips.
- Box 2: 06:40-07:55 EST, aspect 11.27, range 7.1 pips.

User feedback:
- Box 1 is correct.
- Box 2 is correct.

Rule note:
- First March sample validates that the simple compression definition is not purely February-specific.
- Both boxes support the evergreen rule: contained shelf first, BB context second, no bespoke filters.

## Blind Training Sample 027 - 2024-03-27 20:20 EST Start

Settings:
- EURUSD 5-minute candles.
- `BB(5, 4 std)`.
- New York time.
- Future hidden after Box 2.
- Mixed blind selection with duplicate-window guard.
- Out-of-Feb generalization sample: March 2024.

Model boxes:
- Box 1: 22:15-23:30 EST, aspect 15.69, range 5.1 pips.
- Box 2: 23:55-01:10 EST, aspect 20.00, range 4.0 pips.

User feedback:
- Box 1 is correct.
- Box 2 is correct.

Rule note:
- Second March sample supports generalization of the simple shelf rule.
- Very tight, low-BB-width shelves remain high-confidence compression even after an earlier directional push.

## Blind Training Sample 028 - 2024-03-14 23:35 EST Start

Settings:
- EURUSD 5-minute candles.
- `BB(5, 4 std)`.
- New York time.
- Future hidden after Box 2.
- Mixed blind selection with duplicate-window guard.
- Out-of-Feb generalization sample: March 2024.

Model boxes:
- Box 1: 00:40-01:55 EST, aspect 19.05, range 4.2 pips.
- Box 2: 06:40-07:35 EST, aspect 12.00, range 5.0 pips.

User feedback:
- Box 1 is correct.
- Box 2 is correct.

Rule note:
- Third March validation supports the same compact compression rule.
- Shorter 60-minute shelves remain valid when price is contained and the band context has quieted after expansion.
- Next samples should move beyond March so the training set keeps testing generalization instead of memorizing one month.

## Blind Training Sample 029 - 2024-04-11 05:55 EST Start

Settings:
- EURUSD 5-minute candles.
- `BB(5, 4 std)`.
- New York time.
- Future hidden after Box 2.
- Mixed blind selection with duplicate-window guard.
- Out-of-Feb/out-of-March generalization sample: April 2024.

Model boxes:
- Box 1: 06:45-08:00 EST, aspect 8.99, range 8.9 pips.
- Box 2: 12:05-12:40 EST, aspect 6.67, range 6.0 pips.

User feedback:
- Box 1 is correct.
- Box 2 is correct.

Rule note:
- First April sample validates that the compact compression rule still transfers.
- A 40-minute shelf can be valid when overlap is clean and progress is minimal.
- Aspect around 6-7 is acceptable when the visual shelf is obvious; do not set a brittle hard cutoff above that.

## Blind Training Sample 030 - 2024-04-30 00:05 EST Start

Settings:
- EURUSD 5-minute candles.
- `BB(5, 4 std)`.
- New York time.
- Future hidden after Box 2.
- Mixed blind selection with duplicate-window guard.
- Generalization sample: April 2024.

Model boxes:
- Box 1: 00:10-01:25 EST, aspect 18.18, range 4.4 pips.
- Box 2: 02:50-04:05 EST, aspect 8.33, range 9.6 pips.

User feedback:
- Box 1 is correct.
- Box 2 is correct.

Rule note:
- Second April sample supports generalization.
- A wider 9-10 pip box can still be valid when it follows/contains the compression shelf cleanly and net progress is small.
- Keep the detector simple: no hard pip-width cutoff yet; width must be judged relative to context and shelf quality.

## Blind Training Sample 031 - 2024-05-15 21:40 EST Start

Settings:
- EURUSD 5-minute candles.
- `BB(5, 4 std)`.
- New York time.
- Future hidden after Box 2.
- Mixed blind selection with duplicate-window guard.
- Generalization sample: May 2024.

Model boxes:
- Box 1: 23:10-00:25 EST, aspect 15.09, range 5.3 pips.
- Box 2: 02:15-03:15 EST, aspect 11.61, range 5.6 pips.

User feedback:
- Box 1 is correct.
- Box 2 is correct.

Rule note:
- First May sample supports generalization beyond February/March/April.
- Both boxes fit the compact rule: clean shelf, contained range, minimal progress, and quiet enough BB context.

## Blind Training Sample 032 - 2024-06-10 23:40 EST Start

Settings:
- EURUSD 5-minute candles.
- `BB(5, 4 std)`.
- New York time.
- Future hidden after Box 2.
- Mixed blind selection with duplicate-window guard.
- Generalization sample: June 2024.

Model boxes:
- Box 1: 00:50-02:05 EST, aspect 14.04, range 5.7 pips.
- Box 2: 03:15-04:10 EST, aspect 7.69, range 7.8 pips.

User feedback:
- Box 1 is correct.
- Box 2 is wrong.

Rule note:
- Box 2 reinforces the noisy-pause rejection: it came after sharper movement with elevated BB width and did not read like a quiet shelf.
- Do not label post-expansion volatility as compression just because price is temporarily bounded.
- Keep this as a broad rule, not a custom filter: valid compression needs contained candles plus a visibly calmer volatility state.

## Blind Training Sample 033 - 2024-07-29 20:20 EST Start

Settings:
- EURUSD 5-minute candles.
- `BB(5, 4 std)`.
- New York time.
- Future hidden after Box 2.
- Mixed blind selection with duplicate-window guard.
- Generalization sample: July 2024.

Model boxes:
- Box 1: 21:35-22:45 EST, aspect 17.86, range 4.2 pips.
- Box 2: 00:40-01:50 EST, aspect 15.00, range 5.0 pips.

User feedback:
- Box 1 is correct.
- Box 2 is correct.

Rule note:
- First July sample supports generalization after the June miss.
- Both boxes were accepted despite Box 2 having some drift; the visual shelf remained contained and quiet enough.
- Keep rejecting noisy pauses, but do not reject mild drift inside a clean shelf.

## Blind Training Sample 034 - 2024-08-13 21:55 EST Start

Settings:
- EURUSD 5-minute candles.
- `BB(5, 4 std)`.
- New York time.
- Future hidden after Box 2.
- Mixed blind selection with duplicate-window guard.
- Generalization sample: August 2024.

Model boxes:
- Box 1: 23:10-00:25 EST, aspect 19.05, range 4.2 pips.
- Box 2: 00:45-01:45 EST, aspect 14.77, range 4.4 pips.

User feedback:
- Box 1 is correct.
- Box 2 is wrong.
- User note: boxes can be shorter; reducing candle count inside the box is okay.

Rule note:
- Box 2 was too stretched. It captured a small transition/mini-cycle rather than a cleaner shorter shelf.
- Do not force compression boxes to use the maximum available duration.
- Next pass should cap candidate boxes closer to 60 minutes so the detector can mark the clean shelf without swallowing nearby structure.

## Blind Training Sample 035 - 2024-09-19 08:20 EST Start

Settings:
- EURUSD 5-minute candles.
- `BB(5, 4 std)`.
- New York time.
- Future hidden after Box 2.
- Mixed blind selection with duplicate-window guard.
- Generalization sample: September 2024.
- Shorter candidate pass: max 12 bars / 60 minutes.

Model boxes:
- Box 1: 12:50-13:45 EST, aspect 7.50, range 8.0 pips.
- Box 2: 14:05-14:50 EST, aspect 7.46, range 6.7 pips.

User feedback:
- Box 1 is correct.
- Box 2 is correct.

Rule note:
- First shorter-box pass is accepted. Compression boxes do not need to be 75-80 minutes.
- Aspect around 7.5 is still acceptable when the box is short, contained, and visually clean.
- Continue with shorter boxes to avoid swallowing nearby structure.

## Blind Training Sample 036 - 2024-10-03 22:50 EST Start

Settings:
- EURUSD 5-minute candles.
- `BB(5, 4 std)`.
- New York time.
- Future hidden after Box 2.
- Mixed blind selection with duplicate-window guard.
- Generalization sample: October 2024.
- Shorter candidate pass: max 12 bars / 60 minutes.

Model boxes:
- Box 1: 23:55-00:50 EST, aspect 13.04, range 4.6 pips.
- Box 2: 05:55-06:30 EST, aspect 9.52, range 4.2 pips.

User feedback:
- Box 1 is correct.
- Box 2 is correct.
- User note: Git does not need to update every sample; batch every three samples to save time.

Rule note:
- October sample validates the shorter-box pass again.
- A 40-minute compression can be valid when it is clean and does not swallow too much surrounding structure.

## Git Logging Cadence

Protocol update:
- Continue logging each reviewed sample locally immediately.
- Push to GitHub in batches, roughly every three reviewed samples, unless a major rule change or code change needs immediate preservation.

## Blind Training Sample 037 - 2024-11-14 18:05 EST Start

Settings:
- EURUSD 5-minute candles.
- `BB(5, 4 std)`.
- New York time.
- Future hidden after Box 2.
- Mixed blind selection with duplicate-window guard.
- Generalization sample: November 2024.
- Shorter candidate pass: max 12 bars / 60 minutes.

Model boxes:
- Box 1: 21:55-22:45 EST, aspect 10.19, range 5.4 pips.
- Box 2: 23:40-00:35 EST, aspect 12.77, range 4.7 pips.

User feedback:
- Box 1 is correct.
- Box 2 is correct.

Rule note:
- Second shorter-box validation after September/October. Shorter boxes are working better and reduce over-selection.
- Compression can still be valid with mild drift if the internal candles remain contained and the volatility context is calm enough.

## Blind Training Sample 038 - 2024-12-24 00:35 EST Start

Settings:
- EURUSD 5-minute candles.
- `BB(5, 4 std)`.
- New York time.
- Future hidden after Box 2.
- Mixed blind selection with duplicate-window guard.
- Generalization sample: December 2024.
- Shorter candidate pass: max 12 bars / 60 minutes.

Model boxes:
- Box 1: 01:30-02:25 EST, aspect 11.32, range 5.3 pips.
- Box 2: 04:55-05:50 EST, aspect 8.11, range 7.4 pips.

User feedback:
- Box 1 is correct.
- Box 2 is correct.

Rule note:
- Fourth shorter-box validation across late-2024 months.
- The shorter cap is doing useful work: it keeps boxes focused without losing valid compression shelves.
- Next samples should move to older-year validation, starting with 2023, to test whether the rule is evergreen beyond 2024.
