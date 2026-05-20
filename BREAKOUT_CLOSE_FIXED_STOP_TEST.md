# Breakout Close Fixed-Pip Stop Test

## Test

Entry:

- reviewed compression boxes only;
- first 5-minute close beyond the compression box by `0.10R`;
- signal must occur within 60 minutes after the box ends;
- rejected boxes excluded.

Stops:

- `6` pips;
- `7` pips;
- `10` pips.

Take profit:

- `1R`.

Costs and assumptions:

- round-turn spread/transaction cost: `1.2` pips;
- same-candle stop and target: stop loss;
- ROI and max drawdown assume `0.5%` account risk per trade.

## Entry-Based 1R Target

Target = `1R` from the breakout-close entry.

| Stop | Signals | Targets | Stops | Time exits | Win rate | Net pips | Sum risk R | ROI | Max DD |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 6 pips | 29 | 13 | 13 | 3 | 44.8% | -23.7 | -3.951 | -1.99% | 3.04% |
| 7 pips | 29 | 13 | 12 | 4 | 44.8% | -22.9 | -3.266 | -1.65% | 2.58% |
| 10 pips | 29 | 16 | 7 | 6 | 55.2% | -0.5 | -0.050 | -0.04% | 2.55% |

## Box-Extension 1R Target

Target = original audit target, `box_high + 1R` for longs and `box_low - 1R` for shorts.

| Stop | Signals | Targets | Stops | Time exits | Win rate | Net pips | Sum risk R | ROI | Max DD |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 6 pips | 29 | 17 | 11 | 1 | 58.6% | -32.6 | -5.435 | -2.71% | 3.39% |
| 7 pips | 29 | 17 | 10 | 2 | 58.6% | -29.8 | -4.255 | -2.13% | 2.72% |
| 10 pips | 29 | 20 | 5 | 4 | 69.0% | -7.4 | -0.740 | -0.38% | 2.62% |

## Read

- `10` pips is clearly better than `6` or `7` pips.
- `10` pips still does not prove an edge after spread.
- The entry-based target version is almost breakeven at `10` pips, but it is still negative.
- Fixed `6` or `7` pips is not enough for this breakout-close entry.
- The broader lesson is unchanged: the compression signal has expansion value, but the breakout-close entry is weak.
