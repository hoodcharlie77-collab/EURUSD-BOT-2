# 1R Capture Stop Requirements

## Question

The expansion audit showed:

- compression 120-minute `1R` hit rate: `75.0%` on non-null forward windows;
- random-control 120-minute `1R` hit rate: `21.2%`.

This file asks: among the compression boxes that did hit `1R`, what stop size was required to survive the adverse move before the `1R` target?

## Important Clarification

The `75.0%` figure was not a trade win rate. It was a path statistic.

Raw count:

- reviewed compression boxes: `33`;
- boxes with usable 120-minute forward data: `32`;
- boxes that hit `1R` within 120 minutes: `24`;
- non-null hit rate: `24 / 32 = 75.0%`;
- raw all-box hit rate: `24 / 33 = 72.7%`.

## Model 1: Box-Boundary Entry In Eventual Target Direction

This is the cleanest way to interrogate the original 75% expansion statistic.

Assumption:

- for an up `1R` hit, entry is at the box high;
- for a down `1R` hit, entry is at the box low;
- direction is the eventual `1R` target direction;
- stop required is the maximum adverse excursion before the `1R` target is hit.

This is partly theoretical because it uses the eventual winning direction.

| Capture goal | Wins measured | Required stop |
|---:|---:|---:|
| 50% of wins | 24 | `0.596R` |
| 70% of wins | 24 | `0.899R` |
| 90% of wins | 24 | `1.538R` |

Approximate pips using the median winning box size of `6.35` pips:

| Capture goal | Approx stop |
|---:|---:|
| 50% | `3.8` pips |
| 70% | `5.7` pips |
| 90% | `9.8` pips |

## Model 2: First Breakout Close, Same-Direction Target

This is closer to a tradable signal:

- entry is the first close beyond the box by `0.10R`;
- target is the same-side box-extension `1R`;
- only same-direction target wins are measured.

| Capture goal | Wins measured | Required stop |
|---:|---:|---:|
| 50% of wins | 21 | `0.216R` |
| 70% of wins | 21 | `0.433R` |
| 90% of wins | 21 | `1.706R` |

Approximate pips using the median winning box size of `6.30` pips:

| Capture goal | Approx stop |
|---:|---:|
| 50% | `1.4` pips |
| 70% | `2.7` pips |
| 90% | `10.7` pips |

## Read

- The compression expansion edge is real versus random.
- The stop distribution is not smooth.
- Capturing the easy half of winners does not require much room.
- Capturing 90% of winners requires a stop larger than the `1R` target.
- A `1R` target with a `1.5R+` stop is poor reward/risk before spread.
- Therefore the strategy should not aim to capture every expansion. It should identify the subset that works with a tight or moderate stop.
