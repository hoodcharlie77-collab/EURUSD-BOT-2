# Breakout Close Extended Stop Sweep

## Test

Entry rule:

- reviewed compression boxes only;
- first 5-minute close beyond the box by `0.10R`;
- signal must occur within 60 minutes after the box ends;
- rejected boxes excluded.

Trade mechanics:

- stop sizes: `0.25R`, `0.33R`, `0.50R`, `0.75R`, then `1.00R` through `3.00R` in `0.25R` steps;
- take profit: `1R`;
- round-turn spread/transaction cost: `1.2` pips;
- stop and target in same candle: count stop;
- equity metrics assume `0.5%` account risk per trade with compounding.

## Entry-Based Target Results

Target = `1R` from entry.

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

## Box-Extension Target Results

Target = original audit target, `box_high + 1R` for longs and `box_low - 1R` for shorts.

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

## Read

- Tight stops below `0.75R` get chopped.
- The `0.75R` stop remains the least-bad tight/moderate entry-based stop, but it is still negative.
- Wider stops around `2.0R` to `2.75R` barely cross positive on risk-normalized ROI, but the edge is tiny and raw pips remain negative.
- This is not robust enough to call tradable.
- The compression signal needs a better entry, not just a stop-size tweak.
