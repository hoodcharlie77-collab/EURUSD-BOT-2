# Breakout v0 Rules

## Inputs

- EURUSD 5-minute candles.
- Compression box already identified and accepted.
- `H` = compression box high.
- `L` = compression box low.
- `R` = `H - L`.

## Breakout Attempt

Use closes only. Ignore wick-only breaks.

- Up breakout attempt: first 5-minute candle close above `H + 0.10R`.
- Down breakout attempt: first 5-minute candle close below `L - 0.10R`.
- Breakout attempt must happen within 60 minutes after the compression box ends.
- If no breakout attempt within 60 minutes, skip the setup.

## Expansion Labels

- Basic expansion: price reaches `1.0R` beyond either side of the box within 120 minutes after the box ends.
- Strong expansion: price reaches `1.5R` beyond either side of the box within 120 minutes and BB width expands meaningfully.
- Break continuation: first breakout attempt direction equals the first `1.0R` expansion direction.
- Headfake: first breakout attempt direction is opposite the first `1.0R` expansion direction.
- Failed breakout: first breakout attempt occurs, but neither side reaches `1.0R` within 120 minutes.

## Trading Implication

Compression alone is not an entry.

Breakout v0 gives a simple first entry candidate:

- Enter only after a close breaks the box by `0.10R`.
- Do not chase if the break comes after 60 minutes.
- Treat marginal compression boxes as requiring stronger confirmation than clean/strong boxes.
- Expect headfakes. First break direction is useful, but not guaranteed.

## Current Evidence

Reviewed full-window compression sample:

- 33 accepted/questionable compression boxes.
- 29 produced a first close breakout within 120 minutes.
- All 29 first breaks happened within 60 minutes.
- Median first break time: 10 minutes.
- 21 boxes were break continuations.
- 3 boxes were headfakes.
- 5 boxes broke but did not reach `1.0R`.
- 4 boxes produced no breakout.

Compared with same-window random controls:

- Compression first-breaks reached `1.0R` after break far more often than random controls.
- Compression: 82.8% of first breaks eventually reached a `1.0R` target.
- Random control: 23.1% of first breaks eventually reached a `1.0R` target.

Conclusion:

- First close breakout after valid compression is a real signal worth testing.
- It is not enough by itself to prove profitability.
- Next step is to test entry, stop, and exit handling around this breakout label.
