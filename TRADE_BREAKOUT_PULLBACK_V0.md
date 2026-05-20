# Trade Rule: Breakout Pullback v0

## Inputs

- EURUSD 5-minute candles.
- Compression box already identified.
- `H` = compression box high.
- `L` = compression box low.
- `R` = `H - L`.
- Compression Bollinger settings: `BB(5, 4 std)`.
- Breakout-band test settings:
  - `BB(5, 4 std)` is not usable for close-outside-band breakout signals because closes do not get outside that band in the reviewed sample.
  - First practical test uses classic/default `BB(20, 2 std)` for the breakout-band close.
- Pip size: `0.0001`.

## Breakout Signal

After the compression box ends, scan the next 60 minutes.

Long signal:

- candle close is above `H + 0.10R`;
- candle close is above that candle's breakout upper BB band.

Short signal:

- candle close is below `L - 0.10R`;
- candle close is below that candle's breakout lower BB band.

Use closes only. Ignore wick-only breaks.

## Pullback Entry

After a valid breakout signal candle closes:

- Long limit entry = breakout candle upper BB band + 2 pips.
- Short limit entry = breakout candle lower BB band - 2 pips.

The order is placed only after the breakout candle closes.

To be a true pullback order:

- Long entry price must be below the breakout candle close.
- Short entry price must be above the breakout candle close.

If not, skip that signal as not having enough distance for a pullback.

Entry order expires 120 minutes after the compression box ends.

## Risk and Reward

- Stop loss distance = `1R` from entry.
- Take profit distance = `1R` from entry.
- Long stop = `entry - R`.
- Long target = `entry + R`.
- Short stop = `entry + R`.
- Short target = `entry - R`.

## Costs and Fill Rules

- Spread/transaction cost = 1.2 pips per round turn.
- Entry is a limit order.
- Take profit is a limit order.
- Stop loss is a market stop order.
- If stop and target both occur in the same candle, count the stop loss.
- If entry and stop/target happen in the same candle, use the same pessimistic rule.

## Time Exit

If entry fills but neither stop nor target hits by 120 minutes after the compression box ends:

- exit at the last close in the 120-minute window;
- subtract the 1.2 pip round-turn cost.

## Why This Rule Exists

This tests whether compression plus a true band breakout plus a pullback gives a cleaner 1R trade than entering blindly on the first breakout close.

This is not yet final strategy logic. It is a first mechanics test.
