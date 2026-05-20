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

## Blind Training Sample 039 - 2023-03-23 01:25 EST Start

Settings:
- EURUSD 5-minute candles.
- `BB(5, 4 std)`.
- New York time.
- Future hidden after Box 2.
- Mixed blind selection with duplicate-window guard.
- Older-year validation sample: March 2023.
- Shorter candidate pass: max 12 bars / 60 minutes.

Original model boxes:
- Box 1: 01:25-02:10 EST, aspect 5.75, range 8.7 pips.
- Box 2: 06:45-07:35 EST, aspect 5.00, range 11.0 pips.

User feedback:
- Box 1 is correct.
- Box 2 is correct.
- Model missed two additional compression shelves.
- My first missed-box guess at 02:40-02:55 EST was wrong. It chased the shelf too close to the upside spike/high churn.
- My lower-shelf guess at 05:35-06:00 EST was correct.
- The other missed box was between those two guesses: 03:55-04:15 EST.
- User confirmed the corrected four-box chart is all correct.

Corrected additional boxes:
- Corrected Box 3: 03:55-04:15 EST, aspect 2.25, range 11.1 pips, progress 0.9 pips, travel ratio 0.45, median BB width 9.14 pips.
- Corrected Box 4: 05:35-06:00 EST, aspect 3.57, range 8.4 pips, progress 6.6 pips, travel ratio 1.37, median BB width 16.80 pips.

Rule note:
- This is a recall failure, not a precision-only problem. The detector found good boxes but did not find all visually important compression shelves.
- The wrong 02:40-02:55 EST box was too soon after expansion and sat in high-area churn. Reject shelves that are still part of the spike aftermath.
- The accepted 03:55-04:15 EST box is short and fails the current hard aspect floor, but visually it is a clean shelf: tiny net progress, low internal travel, and BB width contraction directly before another push.
- Do not overfit this into a complicated exception. The robust rule is: after expansion/churn, wait for the market to calm into a contained shelf; a short shelf can count if it has very low progress/travel and obvious BB contraction.

## Blind Training Sample 040 - 2023-06-08 08:35 EST Start

Settings:
- EURUSD 5-minute candles.
- `BB(5, 4 std)`.
- New York time.
- Future hidden after Box 2.
- Mixed blind selection with duplicate-window guard.
- Older-year validation sample: June 2023.
- Shorter candidate pass: max 12 bars / 60 minutes.

Model boxes:
- Box 1: 12:20-13:15 EST, aspect 7.89, range 7.6 pips.
- Box 2: 13:45-14:40 EST, aspect 12.50, range 4.8 pips.

User feedback:
- Box 1 is correct.
- Box 2 is correct.

Rule note:
- This sample validates compression late in a slow grind-up day, before the excluded late-NY window.
- A clean shelf near the top of a move is acceptable when candles remain contained and BB width stays compressed/low.
- The very narrow Box 2 reinforces that quiet, low-width shelves are valid even when there is not much immediate dramatic context visible.

## Blind Training Sample 041 - 2023-09-28 06:35 EST Start

Settings:
- EURUSD 5-minute candles.
- `BB(5, 4 std)`.
- New York time.
- Future hidden after Box 2.
- Mixed blind selection with duplicate-window guard.
- Older-year validation sample: September 2023.
- Shorter candidate pass: max 12 bars / 60 minutes.

Model boxes:
- Box 1: 07:05-08:00 EST, aspect 4.84, range 12.4 pips.
- Box 2: 13:30-14:10 EST, aspect 5.17, range 8.7 pips.

User feedback:
- Box 1 is correct.
- Box 2 is correct.

Rule note:
- Third 2023 validation sample passed.
- Box 1 is a lower-aspect but still correct compression: flat enough, contained enough, and directly before a violent expansion/headfake sequence.
- Box 2 is a clean late-window shelf after a larger trend sequence. The compression logic is still holding in a different year and volatility regime.

## 2023 Validation Checkpoint

Status:
- Sample 039: final corrected set accepted after recall correction.
- Sample 040: both boxes accepted.
- Sample 041: both boxes accepted.

Learning:
- The current rules are not merely fitted to 2024. They survived March, June, and September 2023.
- Main weakness is recall around short shelves after volatility settles. The model can miss valid compressions when the hard aspect threshold is too strict.
- Keep the rule simple: contained shelf, low net progress/travel, BB width low or contracting, and no obvious spike-aftershock churn.

## Blind Training Sample 042 - 2025-03-13 01:50 EST Start

Settings:
- EURUSD 5-minute candles.
- `BB(5, 4 std)`.
- New York time.
- Future hidden after Box 2.
- Mixed blind selection with duplicate-window guard.
- Forward-year validation sample: March 2025.
- Shorter candidate pass: max 12 bars / 60 minutes.

Model boxes:
- Box 1: 02:05-02:30 EST, aspect 5.00, range 6.0 pips.
- Box 2: 06:20-06:50 EST, aspect 5.30, range 6.6 pips.

User feedback:
- Box 1 is correct.
- Box 2 is correct.

Rule note:
- First 2025 validation sample passed.
- Both boxes are shorter shelves, which supports the reduced max-duration direction.
- Box 1 is a clean early-session shelf before downside follow-through. Box 2 is a later compressed shelf after a volatility fade, with BB width contracting into the box.

## Blind Training Sample 043 - 2025-06-26 00:50 EST Start

Settings:
- EURUSD 5-minute candles.
- `BB(5, 4 std)`.
- New York time.
- Future hidden after Box 2.
- Mixed blind selection with duplicate-window guard.
- Forward-year validation sample: June 2025.
- Shorter candidate pass: max 12 bars / 60 minutes.

Model boxes:
- Box 1: 00:50-01:35 EST, aspect 5.38, range 9.3 pips.
- Box 2: 05:40-06:20 EST, aspect 5.17, range 8.7 pips.

User feedback:
- Box 1 is correct.
- Box 2 is correct.

Rule note:
- Second 2025 validation sample passed.
- Box 1 is a pre-expansion base before a sustained upside move.
- Box 2 is a compressed shelf after the trend move and pullback. It is still valid because the candles settle into a contained rectangle and BB width contracts sharply into the box.

## Blind Training Sample 044 - 2025-09-18 11:10 EST Start

Settings:
- EURUSD 5-minute candles.
- `BB(5, 4 std)`.
- New York time.
- Future hidden after Box 2.
- Mixed blind selection with duplicate-window guard.
- Forward-year validation sample: September 2025.
- Shorter candidate pass: max 12 bars / 60 minutes.

Model boxes:
- Box 1: 13:00-13:55 EST, aspect 7.14, range 8.4 pips.
- Box 2: 18:00-18:55 EST, aspect 11.54, range 5.2 pips.

User feedback:
- Box 1 is maybe.
- Box 2 is correct.

Rule note:
- This is the first non-clean 2025 validation result.
- Box 1 has acceptable numeric compression stats, but visually it is not a clean automatic yes. It follows a volatile spike/rotation area and the shelf is less obvious than the prior accepted examples.
- Box 2 is a clean, low-width shelf and remains a strong yes.
- Rule impact: borderline boxes should not be converted into hard rejects or hard accepts too quickly. For trading, this argues for a confidence tier: strong compression versus marginal compression, with marginal boxes requiring stronger expansion confirmation.

## 2025 Validation Checkpoint

Status:
- Sample 042: both boxes accepted.
- Sample 043: both boxes accepted.
- Sample 044: Box 1 maybe, Box 2 accepted.

Learning:
- The core compression definition continued to hold forward in 2025.
- The weak spot is not the clean shelf. The weak spot is deciding whether a post-volatility pause has settled enough to count.
- Next phase should deliberately include borderline/trap samples so the rule learns when to downgrade marginal shelves rather than force a yes/no.

## Blind Training Sample 045 - 2022-04-25 17:30 EST Start

Settings:
- EURUSD 5-minute candles.
- `BB(5, 4 std)`.
- New York time.
- Future hidden after Box 2.
- Mixed blind selection with duplicate-window guard.
- Older high-volatility regime sample: April 2022.
- Shorter candidate pass: max 12 bars / 60 minutes.

Model boxes:
- Box 1: 17:55-18:50 EST, aspect 11.54, range 5.2 pips.
- Box 2: 23:05-00:00 EST, aspect 8.00, range 7.5 pips.

User feedback:
- Box 1 is correct.
- Box 2 is correct.

Rule note:
- First 2022 stress sample passed.
- Box 1 is a very low-width shelf before the larger upside expansion sequence.
- Box 2 is a later compression shelf near the top of the move. It remains valid because price stays contained and BB width is controlled, even though the preceding regime has already expanded.
- This supports the core idea: compression can appear before or after expansion; the compression effect is the key condition, not a guaranteed first breakout direction.

## Blind Training Sample 046 - 2022-09-21 19:30 EST Start

Settings:
- EURUSD 5-minute candles.
- `BB(5, 4 std)`.
- New York time.
- Future hidden after Box 2.
- Mixed blind selection with duplicate-window guard.
- Older high-volatility regime sample: September 2022.
- Shorter candidate pass: max 12 bars / 60 minutes.

Model boxes:
- Box 1: 21:40-22:35 EST, aspect 5.13, range 11.7 pips.
- Box 2: 00:20-00:45 EST, aspect 5.08, range 5.9 pips.

User feedback:
- Box 1 is correct.
- Box 2 is correct.

Rule note:
- Second 2022 stress sample passed.
- Box 1 is a broader, lower-quality but still valid shelf after a strong downside move. It is not a tiny low-volatility box; it is a contained pause in a higher-volatility regime.
- Box 2 is a short clean shelf after later expansion. Very low progress/travel keeps it valid despite the larger surrounding volatility.
- This reinforces proportional/contextual compression: a valid 2022 box can be wider in pips than a quiet 2024/2025 box, as long as it is visually contained relative to its local regime.

## Blind Training Sample 047 - 2021-06-10 00:35 EST Start

Settings:
- EURUSD 5-minute candles.
- `BB(5, 4 std)`.
- New York time.
- Future hidden after Box 2.
- Mixed blind selection with duplicate-window guard.
- Older-regime sample: June 2021.
- Shorter candidate pass: max 12 bars / 60 minutes.

Model boxes:
- Box 1: 01:10-01:50 EST, aspect 10.71, range 4.2 pips.
- Box 2: 04:45-05:40 EST, aspect 8.00, range 7.5 pips.

User feedback:
- Box 1 is correct.
- Box 2 is correct.

Rule note:
- Third older-regime stress sample passed.
- Box 1 is a textbook quiet shelf: narrow range, low travel, low BB width, and clear containment before the later larger move.
- Box 2 is a wider but still contained late shelf after expansion. It has more internal travel, but net progress is tiny and the outline still reads as a rectangle.
- The compression definition remains stable across 2021, 2022, 2023, 2024, and 2025 samples.

## Older-Regime Stress Checkpoint

Status:
- Sample 045: both boxes accepted.
- Sample 046: both boxes accepted.
- Sample 047: both boxes accepted.

Learning:
- The proportional/contextual approach is holding. Fixed pip width alone would be wrong because each year/regime has different normal volatility.
- Strong/clean compression examples are now well-covered.
- Next training should emphasize borderline and trap cases: post-spike churn, shelves with too much internal travel, and boxes that look rectangular numerically but do not visually settle.

## Blind Training Sample 048 - 2024-03-04 09:00 EST Start

Settings:
- EURUSD 5-minute candles.
- `BB(5, 4 std)`.
- New York time.
- Future hidden after Box 2.
- Borderline-style selection: same BB/candidate constraints, but lower-ranked candidates selected to pressure-test gray areas.
- Shorter candidate pass: max 12 bars / 60 minutes.

Model boxes:
- Box 1: 10:20-10:55 EST, aspect 7.02, range 5.7 pips.
- Box 2: 12:45-13:35 EST, aspect 11.46, range 4.8 pips.

User feedback:
- Box 1 is correct.
- Box 2 is correct.

Rule note:
- Borderline-style sample still passed.
- Box 1 is a compact shelf after an upside push. It is valid because progress/travel are very low and candles are visually contained.
- Box 2 is a quiet low-width shelf after a drift/chop sequence. It is valid because the final rectangle is clean even though surrounding price action is not dramatic.
- The gray-area test did not break the simple compression definition.

## Compression v0.1 Visual Rule

Current working definition:
- Use EURUSD 5-minute candles with `BB(5, 4 std)` for this training phase.
- Compression is a visually contained shelf/rectangle, usually 6-12 candles / 30-60 minutes.
- The box should be horizontally biased. Square blobs are weak. Long or medium rectangles are acceptable.
- Range must be judged proportionally to local volatility. Fixed pip width is not robust across 2021-2025 regimes.
- Net progress inside the box should be small. Internal travel can exist, but if it reads as churn instead of containment, downgrade it.
- BB width is context, not the whole signal. Low or contracting BB width strengthens the box; wide BB can still be acceptable if the box is proportionally contained in a high-volatility regime.
- Reject or downgrade shelves that are still part of immediate spike-aftershock churn. Wait until price actually settles.
- Compression can appear before expansion or after an expansion pause. The first breakout can headfake; the important effect is that compression is usually near a higher-expansion period.

Confidence tiers:
- Strong compression: clean rectangle, low progress/travel, BB width low or contracting, no obvious spike-aftershock churn.
- Marginal compression: rectangular enough but visually choppier, immediately after volatility, or less settled. It may be usable only with stronger expansion confirmation later.
- Reject: square/non-horizontal area, excessive internal churn, clear directional drift masquerading as a shelf, or a pause that is still part of the spike itself.

Training conclusion:
- The compression rule has now held across 2021, 2022, 2023, 2024, and 2025 samples.
- The largest model risk is recall: missing short clean shelves after volatility settles.
- The largest trading risk is overaccepting marginal shelves without requiring expansion confirmation.
- Next logical phase: define expansion/headfake confirmation after compression, instead of adding more compression filters.

## Full 12-Hour Rule Test 049 - 2022-02-28 18:40 EST Start

Format:
- Full 12-hour window visible.
- EURUSD 5-minute candles.
- `BB(5, 4 std)`.
- New York time.
- Boxes drawn by Compression v0.1 rules before user review.

Model boxes:
- Box 1: 19:10-19:40 EST, strong, aspect 6.86, range 5.1 pips.
- Box 2: 21:30-22:00 EST, strong, aspect 8.97, range 3.9 pips.
- Box 3: 23:20-23:55 EST, strong, aspect 8.33, range 4.8 pips.
- Box 4: 00:35-01:30 EST, strong, aspect 7.89, range 7.6 pips.

User feedback:
- All boxes are fine.

Rule note:
- First full-window, future-visible rule test passed.
- The rule correctly found clustered compressions before a later larger expansion/downside move.
- Box 1 was close to the left edge and slightly drifted down, but still accepted. This supports allowing mild drift when containment is clean.

## Full 12-Hour Rule Test 050 - 2023-11-29 04:55 EST Start

Format:
- Full 12-hour window visible.
- EURUSD 5-minute candles.
- `BB(5, 4 std)`.
- New York time.
- Boxes drawn by Compression v0.1 rules before user review.

Model boxes:
- Box 1: 05:40-06:25 EST, strong, aspect 7.25, range 6.9 pips.
- Box 2: 07:25-08:05 EST, strong, aspect 6.08, range 7.4 pips.
- Box 3: 11:10-11:50 EST, strong, aspect 5.17, range 8.7 pips.
- Box 4: 12:10-12:40 EST, strong, aspect 7.45, range 4.7 pips.

User feedback:
- All four boxes are good.

Rule note:
- Second full-window, future-visible rule test passed.
- Box 3 followed a sharp expansion/drop and still settled enough to count.
- Current rule continues to separate actual shelves from surrounding directional movement without needing extra filters.

## Full 12-Hour Rule Test 051 - 2024-02-07 12:25 EST Start

Format:
- Full 12-hour window visible.
- EURUSD 5-minute candles.
- `BB(5, 4 std)`.
- New York time.
- Boxes drawn by Compression v0.1 rules before user review.

Model boxes:
- Box 1: 14:00-14:55 EST, strong, aspect 11.11, range 5.4 pips.
- Box 2: 17:25-18:10 EST, strong, aspect 13.16, range 3.8 pips.
- Box 3: 19:30-20:25 EST, strong, aspect 15.38, range 3.9 pips.
- Box 4: 23:50-00:20 EST, strong, aspect 7.95, range 4.4 pips.

User feedback:
- Accepted / fine.

Rule note:
- Third full-window test passed.
- Box 4 was visually more edge-case because it was short and appeared near the far right after a local peak/pullback, but user accepted it.
- The current rule is still broadly aligned, though far-right short shelves should remain watched for overacceptance once expansion confirmation is added.

## Full 12-Hour Rule Test 052 - 2024-11-26 02:05 EST Start

Format:
- Full 12-hour window visible.
- EURUSD 5-minute candles.
- `BB(5, 4 std)`.
- New York time.
- Boxes drawn by Compression v0.1 rules before user review.

Model boxes:
- Box 1: 02:15-02:40 EST, strong, aspect 2.42, range 12.4 pips.
- Box 2: 05:20-06:15 EST, strong, aspect 5.04, range 11.9 pips.
- Box 3: 09:45-10:10 EST, strong, aspect 2.17, range 13.8 pips.
- Box 4: 12:15-13:10 EST, strong, aspect 5.83, range 10.3 pips.

User feedback:
- Box 1 is correct.
- Box 2 is correct.
- Box 3 is wrong.
- Box 4 is correct.

Rule note:
- Box 3 exposed a weakness in the short-clean shelf exception.
- Low progress/travel by itself is not enough for a short box. Box 3 was too stubby and too wide for only 30 minutes, and it sat in an active directional leg rather than a settled shelf.
- Rule adjustment: short-clean exceptions now require stricter horizontal shape/context: max 13.0 pips, aspect at least 2.3, and no excessive travel in the prior six candles.
- Short-clean exceptions that do not meet the normal rectangle rule should be treated as marginal, not strong. Normal 45-60 minute rectangles still use the proportional rule.

## Full 12-Hour Rule Test 053 - 2025-06-24 21:50 EST Start

Format:
- Full 12-hour window visible.
- EURUSD 5-minute candles.
- `BB(5, 4 std)`.
- New York time.
- Boxes drawn by Compression v0.1 rules before user review.

Model boxes:
- Box 1: 22:50-23:40 EST, strong, aspect 9.65, range 5.7 pips.
- Box 2: 00:15-01:10 EST, strong, aspect 9.84, range 6.1 pips.
- Box 3: 06:30-07:00 EST, strong, aspect 5.07, range 6.9 pips.
- Box 4: 07:40-08:20 EST, strong, aspect 5.23, range 8.6 pips.

User feedback:
- Box 1 is correct.
- Box 2 is correct.
- Box 3 is not accepted.
- Box 4 is correct.

Rule note:
- Box 3 is a precision miss after the short-shelf fix.
- Unlike Sample 052 Box 3, this one passed the normal rectangle criteria numerically. The issue is visual/contextual: it sits inside an upswing pause and does not read like a settled compression shelf.
- Do not add a brittle numeric patch off this one case. This belongs in the next layer: compression confidence should be downgraded when the box is merely a pause inside a still-active swing rather than a settled shelf.
- Expansion/headfake confirmation should help separate tradable compression from ordinary trend pauses.

## Full 12-Hour Rule Test 054 - 2024-02-07 05:25 EST Start

Format:
- Full 12-hour window visible.
- EURUSD 5-minute candles.
- `BB(5, 4 std)`.
- New York time.
- Boxes drawn by Compression v0.1 rules before user review.

Model boxes:
- Box 1: 05:40-06:20 EST, strong, aspect 5.29, range 8.5 pips.
- Box 2: 06:40-07:35 EST, strong, aspect 7.50, range 8.0 pips.
- Box 3: 12:10-12:55 EST, strong, aspect 7.81, range 6.4 pips.
- Box 4: 14:00-14:55 EST, strong, aspect 11.11, range 5.4 pips.

User feedback:
- Box 1 is correct.
- Box 2 is correct.
- Box 3 is correct.
- Box 4 is correct.

Rule note:
- Full-window test passed cleanly after the short-shelf fix.
- The accepted boxes include both pre-move shelves and post-volatility compression shelves.
- No compression-rule change needed from this sample.

## Full 12-Hour Rule Test 055 - 2021-09-30 11:00 EST Start

Format:
- Full 12-hour window visible.
- EURUSD 5-minute candles.
- `BB(5, 4 std)`.
- New York time.
- Boxes drawn by Compression v0.1 rules before user review.

Model boxes:
- Box 1: 13:40-14:30 EST, strong, aspect 6.11, range 9.0 pips.
- Box 2: 17:20-18:15 EST, strong, aspect 12.50, range 4.8 pips.
- Box 3: 19:30-20:25 EST, strong, aspect 7.89, range 7.6 pips.
- Box 4: 21:55-22:50 EST, strong, aspect 7.89, range 7.6 pips.

User feedback:
- Box 1 is questionable.
- Box 2 is correct.
- Box 3 is correct.
- Box 4 is correct.

Rule note:
- Box 1 should be treated as a confidence downgrade, not a hard failure.
- The box is numerically valid but visually rougher: it appears after a sharp move and has more uneven internal candles than the clean shelves.
- Do not add a new hard filter from this. It supports the existing strong/marginal distinction: shelves after heavier volatility or with messier internal structure should require better expansion confirmation.

## Full 12-Hour Rule Test 056 - 2022-08-28 22:45 EST Start

Format:
- Full 12-hour window visible.
- EURUSD 5-minute candles.
- `BB(5, 4 std)`.
- New York time.
- Boxes drawn by Compression v0.1 rules before user review.

Original model boxes:
- Box 1: 23:15-00:10 EST, strong, aspect 9.09, range 6.6 pips.
- Box 2: 00:35-01:20 EST, strong, aspect 7.94, range 6.3 pips.

User feedback:
- Box 1 is correct.
- Box 2 is correct.
- User noted a likely missed box around 04:00 EST.

Corrected additional box:
- Box 3: 03:35-04:05 EST, marginal, aspect 2.92, range 12.0 pips.

Final user feedback:
- Box 1 is correct.
- Box 2 is correct.
- Box 3 is correct.

Rule note:
- This is a recall miss, not a false positive problem.
- The added 03:35-04:05 EST box is a short/wider marginal shelf with BB width contraction, followed by a downside headfake and then upside expansion.
- The base selector missed it because it preferred only two cleaner early shelves in that window.
- Keep this as a marginal compression class: valid enough to watch, but it should require stronger expansion/headfake confirmation before becoming a trade trigger.

## Full 12-Hour Rule Test 057 - 2021-12-26 23:55 EST Start

Format:
- Full 12-hour window visible.
- EURUSD 5-minute candles.
- `BB(5, 4 std)`.
- New York time.
- Boxes drawn by Compression v0.1 rules before user review.

Model boxes:
- Box 1: 00:35-01:30 EST, strong, aspect 14.63, range 4.1 pips.
- Box 2: 01:50-02:20 EST, strong, aspect 8.33, range 4.2 pips.
- Box 3: 04:10-04:50 EST, strong, aspect 6.72, range 6.7 pips.
- Box 4: 08:10-09:00 EST, strong, aspect 10.38, range 5.3 pips.

User feedback:
- Box 1 is correct.
- Box 2 is correct.
- Box 3 is correct.
- Box 4 is correct.
- User note: this is the last compression chart because further samples are now wasting time.

Rule note:
- Final full-window compression test passed.
- Stop additional compression-only visual training for now. The detector is aligned enough for the next stage.
- Next useful work is expansion/headfake confirmation after compression, not more compression box sampling.

## Compression Training Stop Point

Decision:
- Compression v0.1 is good enough to freeze for now.
- Do not keep grinding random compression charts unless a later backtest exposes a specific failure mode.
- Current known issues are acceptable as confidence-tier problems: questionable shelves and marginal short shelves should require stronger expansion confirmation.

Next phase:
- Define expansion after compression.
- Explicitly model headfake behavior: first break can fail, then the real expansion can continue the other way.
- Build entries/exits around compression plus expansion confirmation, not compression alone.

## Expansion Audit 001 - Fixed Forward Windows

Question:
- A compression is supposed to be followed by expansion. Test whether reviewed compression boxes actually produce more forward expansion than random same-window controls.

Method:
- Use reviewed full-window rule-test boxes from Samples 049-057.
- Include accepted and questionable boxes. Exclude rejected boxes.
- Compare each reviewed compression box against a random same-window control segment with similar duration.
- Measure fixed forward windows after the box end: 30, 60, 90, and 120 minutes.
- Use proportional expansion, not fixed pips:
  - `max_extension_r = max(upside extension, downside extension) / compression box range`.
  - `realized_range_r = post-window high-low range / compression box range`.
  - `bb_expand_ratio = max post-window BB width / box median BB width`.
- Track first close break direction and whether the first break was opposite the dominant 120-minute expansion direction.

First-pass results:
- Sample size: 33 reviewed compression boxes versus 33 random controls.
- 60-minute median max extension:
  - Compression: 1.074R.
  - Random control: 0.348R.
- 60-minute 1R hit rate:
  - Compression: 56.2%.
  - Random control: 6.1%.
- 120-minute median max extension:
  - Compression: 1.642R.
  - Random control: 0.572R.
- 120-minute 1R hit rate:
  - Compression: 75.0%.
  - Random control: 21.2%.
- 120-minute 1.5R hit rate:
  - Compression: 59.4%.
  - Random control: 6.1%.
- 120-minute median BB expansion ratio:
  - Compression: 3.264x.
  - Random control: 2.058x.
- First-break headfake rate over 120 minutes:
  - Compression: 17.2%.
  - Random control: 3.8%.

Interpretation:
- Compression boxes are showing materially more forward expansion than random same-window slices.
- The result supports the compression > expansion premise enough to proceed to expansion logic.
- Do not call this profitability proof. This is a small visually trained set, and the control is simple.
- The headfake rate is real enough to matter. First break direction cannot be trusted blindly.

Next rule-development step:
- Define expansion confirmation after a compression:
  - basic expansion label: hit at least 1R within 120 minutes;
  - stronger expansion label: hit at least 1.5R within 120 minutes and BB width expands meaningfully;
  - headfake handling: first break can be wrong, so entry logic must not assume first close outside the box is the final direction.

## Breakout Audit 001 - Breakout v0.1

Definition tested:
- `H` = compression box high.
- `L` = compression box low.
- `R` = `H - L`.
- Up breakout attempt: first 5-minute close above `H + 0.10R`.
- Down breakout attempt: first 5-minute close below `L - 0.10R`.
- Use closes only. Ignore wick-only breaks.
- Basic expansion target: first side to reach `1.0R` beyond the box within 120 minutes after the box ends.

Results on accepted/questionable compression boxes:
- Total boxes: 33.
- First close breakout count: 29.
- First close breakout rate: 87.9%.
- Median first breakout time: 10 minutes after box end.
- First breakout timing:
  - 69.0% of breakouts occurred within 15 minutes.
  - 93.1% of breakouts occurred within 30 minutes.
  - 100.0% of breakouts occurred within 60 minutes.
- First breakout reached some `1.0R` target afterward: 82.8% of first-break cases.
- Same-direction `1.0R` after first break: 87.5% of target-hit cases.
- Opposite-direction `1.0R` after first break: 12.5% of target-hit cases.
- No `1.0R` target after first break: 17.2% of first-break cases.
- Median first `1.0R` target time: 47.5 minutes after box end.

Breakout outcomes:
- Break continuation: 21 boxes.
- Headfake: 3 boxes.
- Break but no `1.0R`: 5 boxes.
- No breakout: 4 boxes.

Random-control comparison:
- Random control first break rate: 78.8%.
- Random control first break median time: 35 minutes.
- Random controls reached a `1.0R` target after break only 23.1% of the time.
- Compression first breaks reached a `1.0R` target after break 82.8% of the time.

Rule decision:
- Breakout v0.1 is valid enough for first backtest implementation.
- Breakout attempt must happen within 60 minutes after compression ends.
- If no breakout by 60 minutes, skip the setup.
- First break direction is useful but not perfect; model must allow headfake logic.
- Do not add more filters yet. Next test should be trade mechanics: entry on close break, stop logic, time stop, and target handling.

## Trade Mechanics Test 001 - Breakout Band Pullback v0

User-defined mechanics:
- Enter on pullback after breakout.
- Breakout sequence: breakout from compression, candle close outside BB band, then pullback to 2 pips outside the band.
- Entry: limit order.
- Stop: `1R`.
- Take profit: `1R`.
- Round-turn spread/transaction cost: 1.2 pips.
- Target exit: limit order.
- Stop exit: market stop.
- If stop and target both occur in the same candle, count the stop loss.

Implementation assumptions:
- Compression box remains the same reviewed box.
- `R` = compression box height.
- Breakout from compression requires close beyond box by `0.10R`.
- The breakout-band close is tested separately from compression bands.
- Pullback entry uses the breakout candle's band value as a fixed limit order:
  - long entry = breakout upper band + 2 pips;
  - short entry = breakout lower band - 2 pips.
- The entry is valid only if it is a real pullback:
  - long entry must be below the breakout candle close;
  - short entry must be above the breakout candle close.
- Entry order expires 120 minutes after compression box end.
- If filled but neither stop nor target hits by 120 minutes after box end, exit at final close and subtract spread.

Finding 1:
- Using current compression bands `BB(5, 4 std)` for "close outside BB band" produces zero signals.
- This is expected. With a 5-bar rolling window and 4 standard deviations, a close outside the band is effectively impossible when the current close is included in the band calculation.
- Therefore `BB(5, 4 std)` is useful for visual compression context, but not for close-outside-band breakout entry.

Finding 2:
- Using default/classic `BB(20, 2 std)` for breakout-band confirmation produced:
  - boxes tested: 33;
  - breakout-band signals: 27;
  - filled pullback trades: 3;
  - targets: 2;
  - stops: 1;
  - time exits: 0;
  - target rate on filled trades: 66.7%;
  - total net pips after 1.2 pip round-turn cost: -2.9 pips;
  - average net per filled trade: -0.97 pips.

Interpretation:
- The rule as stated is too restrictive for this sample.
- The problem is not the band breakout signal; 27 of 33 boxes produced a `BB(20, 2)` breakout-band signal.
- The problem is the pullback price. Most breakout closes were not far enough outside the band for "2 pips outside the band" to be a valid non-marketable pullback limit order.
- Example logic issue: if the upper band is 1.1000 and the breakout closes at 1.1001, a long limit at 1.1002 is above current price, not a pullback.

Decision:
- Do not treat this as a profitable 1:1 rule.
- Do not optimize the offset from this tiny sample.
- Next clean test should clarify whether the intended pullback is:
  - 2 pips outside the band after a stronger band extension; or
  - 2 pips inside the band / back toward the band, which is a true pullback order.

## Trade Mechanics Test 002 - Outside-Band Pullback Offset Sweep

Reason:
- The prior test produced 27 `BB(20, 2)` breakout-band signals but only 3 filled trades.
- User correctly identified the pullback logic as the bottleneck.
- Test requested: keep the rule as "outside the band" and sweep the outside-band pullback offset from `+2` pips, in 5 pip steps, up to `+30` pips.

Offsets tested:
- `+2`, `+7`, `+12`, `+17`, `+22`, `+27`, `+30` pips outside the breakout band.

Unchanged mechanics:
- EURUSD 5-minute candles.
- Reviewed accepted/questionable compression boxes only.
- Compression visual context remains `BB(5, 4 std)`.
- Breakout-band close uses `BB(20, 2 std)`.
- Compression breakout requires close beyond box by `0.10R`.
- Entry is a limit order after breakout candle close.
- Stop = `1R`.
- Target = `1R`.
- Spread/transaction cost = 1.2 pips per completed round turn.
- Same-candle stop and target = pessimistic stop loss.

Sweep result:

| Pullback offset outside band | Signals | Filled trades | Targets | Stops | Net pips |
|---:|---:|---:|---:|---:|---:|
| +2 pips | 27 | 3 | 2 | 1 | -2.9 |
| +7 pips | 27 | 0 | 0 | 0 | 0.0 |
| +12 pips | 27 | 0 | 0 | 0 | 0.0 |
| +17 pips | 27 | 0 | 0 | 0 | 0.0 |
| +22 pips | 27 | 0 | 0 | 0 | 0.0 |
| +27 pips | 27 | 0 | 0 | 0 | 0.0 |
| +30 pips | 27 | 0 | 0 | 0 | 0.0 |

Diagnostic:
- The 27 breakout-band signals barely close outside the `BB(20, 2)` band.
- Average breakout close distance beyond the band: about `0.91` pip.
- Maximum breakout close distance beyond the band: `3.94` pips.
- Therefore every offset `+7` pips or wider is invalid as a true pullback order on this sample; the limit entry would sit beyond the breakout close rather than behind it.

Decision:
- Outside-band pullback entries are not viable as stated.
- The phrase "outside the band" is the wrong side of the band for this dataset unless we first require a much stronger extension candle.
- Do not add a stronger-extension filter yet; that would be curve fitting on a tiny reviewed sample.
- Next robust test should move the pullback to the band itself or inside/back toward the band.

## Trade Mechanics Test 003 - Breakout Close Entry Stop Sweep

Reason:
- User asked how the 29 breakout signals were generated and whether actual trades could be tested from them.
- The 29 signals came from the breakout v0 audit:
  - first 5-minute close beyond the compression box by `0.10R`;
  - signal within 60 minutes after compression box end;
  - rejected visual boxes excluded.
- The prior 82.8% number was not a trade win rate. It was a forward expansion label.

Trade conversion:
- Entry = breakout signal candle close.
- Stop = swept in `R` multiples from entry.
- Spread/transaction cost = 1.2 pips round turn.
- Same-candle stop and target = pessimistic stop loss.
- Trade deadline = 120 minutes after compression box end.

Stop sizes:
- `0.25R`, `0.50R`, `0.75R`, `1.00R`, `1.25R`, `1.50R`, `2.00R`.

Two target modes tested:
- `entry_r`: target is `1R` from the entry close.
- `box_extension_r`: target is the original audit target, `box_high + 1R` for longs and `box_low - 1R` for shorts.

Entry-based target results:

| Stop | Signals | Targets | Stops | Time exits | Net pips |
|---:|---:|---:|---:|---:|---:|
| 0.25R | 29 | 6 | 22 | 1 | -33.39 |
| 0.50R | 29 | 10 | 18 | 1 | -30.10 |
| 0.75R | 29 | 13 | 13 | 3 | -13.44 |
| 1.00R | 29 | 13 | 12 | 4 | -32.90 |
| 1.25R | 29 | 13 | 10 | 6 | -51.01 |
| 1.50R | 29 | 13 | 9 | 7 | -61.35 |
| 2.00R | 29 | 17 | 5 | 7 | -33.00 |

Box-extension target results:

| Stop | Signals | Targets | Stops | Time exits | Net pips |
|---:|---:|---:|---:|---:|---:|
| 0.25R | 29 | 12 | 17 | 0 | -18.40 |
| 0.50R | 29 | 15 | 14 | 0 | -23.85 |
| 0.75R | 29 | 17 | 11 | 1 | -20.39 |
| 1.00R | 29 | 17 | 10 | 2 | -35.20 |
| 1.25R | 29 | 17 | 8 | 4 | -48.66 |
| 1.50R | 29 | 17 | 7 | 5 | -54.35 |
| 2.00R | 29 | 21 | 3 | 5 | -23.60 |

Interpretation:
- Every tested stop size loses after spread.
- The best entry-based target result was `0.75R` stop at `-13.44` pips.
- The best box-extension target result was `0.25R` stop at `-18.40` pips.
- Costs matter heavily because many compression boxes are only about 4 to 9 pips tall.
- Raw breakout-close entry is not enough. The compression premise may still be useful, but direct chase entry is weak.

Decision:
- Do not treat the 29 breakout signals as a tradable edge by themselves.
- Continue testing entry improvement, especially pullback/retest logic, rather than adding more confirmation filters.

## Trade Mechanics Test 004 - Extended Stop Sweep With 1R Target

Request:
- Test `0.25R`, `0.33R`, `0.50R`, `0.75R` stops.
- Then test `1.00R` through `3.00R` stops in `0.25R` increments.
- Keep take profit at `1R`.
- Show results by stop size, ROI, max drawdown, etc.

Equity assumption:
- ROI and drawdown use `0.5%` account risk per trade with compounding.
- Net pips remain fixed-unit pips after the 1.2 pip round-turn cost.

Entry-based target results:

| Stop | Win rate | Net pips | Sum risk R | ROI | Max DD |
|---:|---:|---:|---:|---:|---:|
| 0.25R | 20.7% | -33.39 | -16.974 | -8.29% | 11.35% |
| 0.33R | 31.0% | -16.36 | -6.101 | -3.13% | 5.46% |
| 0.50R | 34.5% | -30.10 | -7.488 | -3.75% | 5.29% |
| 0.75R | 44.8% | -13.44 | -0.925 | -0.51% | 2.70% |
| 1.00R | 44.8% | -32.90 | -2.629 | -1.34% | 2.55% |
| 1.25R | 44.8% | -51.01 | -4.040 | -2.03% | 2.97% |
| 1.50R | 44.8% | -61.35 | -4.360 | -2.18% | 2.96% |
| 1.75R | 55.2% | -38.06 | -0.309 | -0.17% | 1.84% |
| 2.00R | 58.6% | -33.00 | 0.479 | 0.23% | 1.29% |
| 2.25R | 58.6% | -44.70 | -0.132 | -0.08% | 1.26% |
| 2.50R | 58.6% | -44.85 | 0.569 | 0.28% | 1.23% |
| 2.75R | 58.6% | -47.93 | 0.573 | 0.28% | 1.21% |
| 3.00R | 58.6% | -57.00 | 0.276 | 0.13% | 1.19% |

Box-extension target results:

| Stop | Win rate | Net pips | Sum risk R | ROI | Max DD |
|---:|---:|---:|---:|---:|---:|
| 0.25R | 41.4% | -18.40 | -9.626 | -4.81% | 7.03% |
| 0.33R | 44.8% | -19.63 | -8.103 | -4.05% | 5.75% |
| 0.50R | 51.7% | -23.85 | -7.515 | -3.74% | 4.87% |
| 0.75R | 58.6% | -20.39 | -3.796 | -1.91% | 3.11% |
| 1.00R | 58.6% | -35.20 | -4.284 | -2.14% | 2.80% |
| 1.25R | 58.6% | -48.66 | -4.965 | -2.47% | 2.97% |
| 1.50R | 58.6% | -54.35 | -4.801 | -2.39% | 2.81% |
| 1.75R | 69.0% | -32.41 | -1.105 | -0.56% | 1.91% |
| 2.00R | 72.4% | -23.60 | -0.039 | -0.03% | 1.29% |
| 2.25R | 72.4% | -30.65 | -0.370 | -0.19% | 1.26% |
| 2.50R | 72.4% | -26.15 | 0.553 | 0.27% | 1.23% |
| 2.75R | 72.4% | -32.23 | 0.320 | 0.16% | 1.21% |
| 3.00R | 72.4% | -38.30 | 0.124 | 0.06% | 1.19% |

Interpretation:
- Tight stops under `0.75R` are not surviving enough trades.
- Wider stops around `2.0R` to `2.75R` produce tiny positive risk-normalized ROI in some cases, but this is not robust.
- Raw fixed-unit net pips remain negative across every tested stop size.
- Stop tweaking is not enough. The signal needs a better entry or a better way to avoid the deep adverse-excursion subset.

## Stop Requirement Test 001 - Stops Needed To Capture 1R Expansion Wins

Question:
- The expansion audit showed compression 120-minute `1R` hit rate of `75.0%` versus random-control `21.2%`.
- User asked what stop size is required to capture `50%`, `70%`, and `90%` of those wins.

Clarification:
- The `75.0%` figure was not a trade win rate.
- It used non-null forward windows:
  - reviewed compression boxes: `33`;
  - usable 120-minute forward windows: `32`;
  - boxes that hit `1R` within 120 minutes: `24`;
  - non-null hit rate: `24 / 32 = 75.0%`;
  - raw all-box hit rate: `24 / 33 = 72.7%`.

Model 1 - box-boundary entry in eventual target direction:
- For an up `1R` hit, assume entry at the box high.
- For a down `1R` hit, assume entry at the box low.
- Direction is the eventual `1R` target direction.
- Stop required is maximum adverse excursion before target.
- This directly interrogates the expansion statistic, but it is partly theoretical because direction is known from the eventual winner.

Results:

| Capture goal | Wins measured | Required stop |
|---:|---:|---:|
| 50% | 24 | `0.596R` |
| 70% | 24 | `0.899R` |
| 90% | 24 | `1.538R` |

Model 2 - first breakout close, same-direction target:
- Entry is the first close beyond the box by `0.10R`.
- Target is the same-side box-extension `1R`.
- Only same-direction target wins are measured.
- This is closer to a tradable signal.

Results:

| Capture goal | Wins measured | Required stop |
|---:|---:|---:|
| 50% | 21 | `0.216R` |
| 70% | 21 | `0.433R` |
| 90% | 21 | `1.706R` |

Interpretation:
- Capturing the easy half of expansion winners requires little room.
- Capturing 70% is still sub-`1R` in both models.
- Capturing 90% requires a stop larger than the `1R` target.
- A `1R` target with a `1.5R+` stop is poor reward/risk before spread.
- The right direction is not "catch all expansions"; it is to isolate the subset that reaches `1R` without deep adverse excursion.
