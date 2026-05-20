# Breakout Close Stop Sweep

## Purpose

Convert the 29 breakout v0 signals into actual trades.

The 29 signals come from the compression-box breakout rule:

- first 5-minute close beyond the compression box by `0.10R`;
- signal must occur within 60 minutes after the compression box ends;
- rejected visual boxes are excluded.

## Trade Assumptions

- Entry = breakout signal candle close.
- Entry style = market/close-entry approximation after the candle closes.
- Spread/transaction cost = 1.2 pips per round turn.
- Stop = swept in `R` multiples from entry.
- Same-candle stop and target = stop loss.
- Trade window ends 120 minutes after the compression box ends.

## Stop Sweep

Stop sizes tested:

- `0.25R`
- `0.50R`
- `0.75R`
- `1.00R`
- `1.25R`
- `1.50R`
- `2.00R`

## Target Modes

Two target interpretations were tested.

### Entry-Based Target

- Long target = `entry + 1R`.
- Short target = `entry - 1R`.

This is the clean trading interpretation of a `1R` take profit from the actual entry.

### Box-Extension Target

- Long target = `box_high + 1R`.
- Short target = `box_low - 1R`.

This matches the original breakout audit target definition, but the reward from entry is smaller because the entry occurs after price already breaks out from the box.

## Results

Entry-based `1R` target:

| Stop | Signals | Targets | Stops | Time exits | Net pips |
|---:|---:|---:|---:|---:|---:|
| 0.25R | 29 | 6 | 22 | 1 | -33.39 |
| 0.50R | 29 | 10 | 18 | 1 | -30.10 |
| 0.75R | 29 | 13 | 13 | 3 | -13.44 |
| 1.00R | 29 | 13 | 12 | 4 | -32.90 |
| 1.25R | 29 | 13 | 10 | 6 | -51.01 |
| 1.50R | 29 | 13 | 9 | 7 | -61.35 |
| 2.00R | 29 | 17 | 5 | 7 | -33.00 |

Box-extension `1R` target:

| Stop | Signals | Targets | Stops | Time exits | Net pips |
|---:|---:|---:|---:|---:|---:|
| 0.25R | 29 | 12 | 17 | 0 | -18.40 |
| 0.50R | 29 | 15 | 14 | 0 | -23.85 |
| 0.75R | 29 | 17 | 11 | 1 | -20.39 |
| 1.00R | 29 | 17 | 10 | 2 | -35.20 |
| 1.25R | 29 | 17 | 8 | 4 | -48.66 |
| 1.50R | 29 | 17 | 7 | 5 | -54.35 |
| 2.00R | 29 | 21 | 3 | 5 | -23.60 |

## Interpretation

- The 82.8% breakout-audit number was not a trade win rate.
- It measured whether price later reached a box-based `1R` extension after a breakout.
- When converted into actual trades, spread and entry location matter.
- Every tested stop size is net negative after the 1.2 pip round-turn cost.
- The best entry-based result was `0.75R` stop, still `-13.44` pips.
- The best box-extension result was `0.25R` stop, still `-18.40` pips.

## Decision

Raw breakout-close entry is not enough.

The compression premise remains useful, but the entry needs improvement. The current evidence says not to chase the breakout close directly.
