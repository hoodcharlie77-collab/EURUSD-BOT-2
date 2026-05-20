from __future__ import annotations

import argparse
import math
from pathlib import Path

import pandas as pd

from audit_compression_expansion import load_boxes, parse_est, sample_dir
from make_blind_bb_training_sample import NY, PIP, load_5m_bars


SPREAD_PIPS = 1.2


def compression_stats(window: pd.DataFrame, start_utc: pd.Timestamp, end_utc: pd.Timestamp) -> dict:
    chunk = window[(window["timestamp"] >= start_utc) & (window["timestamp"] <= end_utc)].copy()
    if chunk.empty:
        raise ValueError(f"No compression bars between {start_utc} and {end_utc}")
    high = float(chunk["high"].max())
    low = float(chunk["low"].min())
    range_pips = (high - low) / PIP
    return {"high": high, "low": low, "range_price": high - low, "range_pips": range_pips}


def add_breakout_bands(bars: pd.DataFrame, period: int, std_mult: float) -> pd.DataFrame:
    bars = bars.copy()
    bars["breakout_bb_mid"] = bars["close"].rolling(period).mean()
    bars["breakout_bb_std"] = bars["close"].rolling(period).std(ddof=0)
    bars["breakout_bb_upper"] = bars["breakout_bb_mid"] + std_mult * bars["breakout_bb_std"]
    bars["breakout_bb_lower"] = bars["breakout_bb_mid"] - std_mult * bars["breakout_bb_std"]
    return bars


def load_rule_test_window(path: Path, breakout_bb_period: int, breakout_bb_std: float) -> pd.DataFrame:
    summary = pd.read_csv(path / "summary.csv")
    if not summary.empty and "data" in summary.columns:
        data_path = Path(str(summary.iloc[0]["data"]))
        if data_path.exists():
            bars = add_breakout_bands(load_5m_bars(data_path), breakout_bb_period, breakout_bb_std)
            start_utc = parse_est(str(summary.iloc[0]["start_new_york"]))
            end_utc = parse_est(str(summary.iloc[0]["end_new_york"]))
            return bars[(bars["timestamp"] >= start_utc) & (bars["timestamp"] <= end_utc)].copy().reset_index(drop=True)

    window = pd.read_csv(path / "full_12h_bars.csv", parse_dates=["timestamp", "timestamp_ny"])
    return add_breakout_bands(window, breakout_bb_period, breakout_bb_std)


def find_breakout_signal(window: pd.DataFrame, end_utc: pd.Timestamp, box_high: float, box_low: float, r_price: float) -> dict | None:
    start = end_utc + pd.Timedelta(minutes=5)
    deadline = end_utc + pd.Timedelta(minutes=60)
    post = window[(window["timestamp"] >= start) & (window["timestamp"] <= deadline)].copy()
    buffer_price = max(0.5 * PIP, r_price * 0.10)

    for idx, row in post.iterrows():
        close = float(row["close"])
        upper_band = float(row["breakout_bb_upper"])
        lower_band = float(row["breakout_bb_lower"])
        if math.isnan(upper_band) or math.isnan(lower_band):
            continue
        if close > box_high + buffer_price and close > upper_band:
            entry = upper_band + 2.0 * PIP
            if entry < close:
                return {
                    "signal_i": int(idx),
                    "signal_time": row["timestamp"],
                    "direction": "long",
                    "signal_close": close,
                    "signal_band": upper_band,
                    "entry_price": entry,
                }
            return {
                "signal_i": int(idx),
                "signal_time": row["timestamp"],
                "direction": "long",
                "signal_close": close,
                "signal_band": upper_band,
                "entry_price": entry,
                "skip_reason": "signal_close_not_far_enough_for_pullback",
            }
        if close < box_low - buffer_price and close < lower_band:
            entry = lower_band - 2.0 * PIP
            if entry > close:
                return {
                    "signal_i": int(idx),
                    "signal_time": row["timestamp"],
                    "direction": "short",
                    "signal_close": close,
                    "signal_band": lower_band,
                    "entry_price": entry,
                }
            return {
                "signal_i": int(idx),
                "signal_time": row["timestamp"],
                "direction": "short",
                "signal_close": close,
                "signal_band": lower_band,
                "entry_price": entry,
                "skip_reason": "signal_close_not_far_enough_for_pullback",
            }
    return None


def find_entry(window: pd.DataFrame, signal: dict, box_end_utc: pd.Timestamp) -> tuple[int, pd.Series] | tuple[None, None]:
    signal_i = int(signal["signal_i"])
    entry = float(signal["entry_price"])
    deadline = box_end_utc + pd.Timedelta(minutes=120)
    post = window[(window.index > signal_i) & (window["timestamp"] <= deadline)].copy()

    for idx, row in post.iterrows():
        if signal["direction"] == "long":
            if float(row["low"]) <= entry <= float(row["high"]):
                return int(idx), row
        else:
            if float(row["low"]) <= entry <= float(row["high"]):
                return int(idx), row
    return None, None


def resolve_trade(
    window: pd.DataFrame,
    entry_i: int,
    entry_price: float,
    direction: str,
    r_price: float,
    box_end_utc: pd.Timestamp,
) -> dict:
    deadline = box_end_utc + pd.Timedelta(minutes=120)
    trade_bars = window[(window.index >= entry_i) & (window["timestamp"] <= deadline)].copy()

    if direction == "long":
        stop = entry_price - r_price
        target = entry_price + r_price
    else:
        stop = entry_price + r_price
        target = entry_price - r_price

    for _, row in trade_bars.iterrows():
        high = float(row["high"])
        low = float(row["low"])
        if direction == "long":
            stop_hit = low <= stop
            target_hit = high >= target
        else:
            stop_hit = high >= stop
            target_hit = low <= target

        if stop_hit:
            gross_pips = -r_price / PIP
            return {
                "outcome": "stop",
                "exit_time": row["timestamp"],
                "exit_price": stop,
                "gross_pips": gross_pips,
                "net_pips": gross_pips - SPREAD_PIPS,
            }
        if target_hit:
            gross_pips = r_price / PIP
            return {
                "outcome": "target",
                "exit_time": row["timestamp"],
                "exit_price": target,
                "gross_pips": gross_pips,
                "net_pips": gross_pips - SPREAD_PIPS,
            }

    if trade_bars.empty:
        gross_pips = 0.0
        exit_time = pd.NaT
        exit_price = math.nan
    else:
        final = trade_bars.iloc[-1]
        exit_time = final["timestamp"]
        exit_price = float(final["close"])
        if direction == "long":
            gross_pips = (exit_price - entry_price) / PIP
        else:
            gross_pips = (entry_price - exit_price) / PIP

    return {
        "outcome": "time_exit",
        "exit_time": exit_time,
        "exit_price": exit_price,
        "gross_pips": gross_pips,
        "net_pips": gross_pips - SPREAD_PIPS,
    }


def backtest_box(window: pd.DataFrame, sample: int, box_row: pd.Series, status: str, note: str) -> dict:
    box_num = int(box_row["box"])
    start_utc = parse_est(str(box_row["start_new_york"]))
    end_utc = parse_est(str(box_row["end_new_york"]))
    stats = compression_stats(window, start_utc, end_utc)
    r_price = stats["range_price"]
    r_pips = stats["range_pips"]

    result = {
        "sample": sample,
        "box": box_num,
        "status": status,
        "note": note,
        "box_start_new_york": start_utc.tz_convert(NY).strftime("%Y-%m-%d %H:%M EST"),
        "box_end_new_york": end_utc.tz_convert(NY).strftime("%Y-%m-%d %H:%M EST"),
        "box_range_pips": round(r_pips, 2),
    }

    signal = find_breakout_signal(window, end_utc, stats["high"], stats["low"], r_price)
    if signal is None:
        result.update({"trade_status": "no_signal"})
        return result

    result.update(
        {
            "signal_time_new_york": signal["signal_time"].tz_convert(NY).strftime("%Y-%m-%d %H:%M EST"),
            "direction": signal["direction"],
            "signal_close": round(signal["signal_close"], 5),
            "signal_band": round(signal["signal_band"], 5),
            "entry_price": round(signal["entry_price"], 5),
            "signal_minutes_after_box": round((signal["signal_time"] - end_utc) / pd.Timedelta(minutes=1), 1),
        }
    )

    if "skip_reason" in signal:
        result.update({"trade_status": "no_trade", "outcome": signal["skip_reason"]})
        return result

    entry_i, entry_row = find_entry(window, signal, end_utc)
    if entry_i is None:
        result.update({"trade_status": "no_trade", "outcome": "entry_not_filled"})
        return result

    entry_time = entry_row["timestamp"]
    resolved = resolve_trade(window, entry_i, float(signal["entry_price"]), signal["direction"], r_price, end_utc)
    net_r = resolved["net_pips"] / r_pips if r_pips else math.nan

    result.update(
        {
            "trade_status": "filled",
            "entry_time_new_york": entry_time.tz_convert(NY).strftime("%Y-%m-%d %H:%M EST"),
            "entry_minutes_after_signal": round((entry_time - signal["signal_time"]) / pd.Timedelta(minutes=1), 1),
            "stop_price": round(float(signal["entry_price"]) - r_price, 5)
            if signal["direction"] == "long"
            else round(float(signal["entry_price"]) + r_price, 5),
            "target_price": round(float(signal["entry_price"]) + r_price, 5)
            if signal["direction"] == "long"
            else round(float(signal["entry_price"]) - r_price, 5),
            "outcome": resolved["outcome"],
            "exit_time_new_york": resolved["exit_time"].tz_convert(NY).strftime("%Y-%m-%d %H:%M EST")
            if not pd.isna(resolved["exit_time"])
            else "",
            "exit_price": round(resolved["exit_price"], 5) if not pd.isna(resolved["exit_price"]) else "",
            "gross_pips": round(resolved["gross_pips"], 2),
            "net_pips": round(resolved["net_pips"], 2),
            "net_r": round(net_r, 3),
            "spread_pips_round_turn": SPREAD_PIPS,
        }
    )
    return result


def run_backtest(
    feedback_path: Path,
    root: Path,
    out_dir: Path,
    breakout_bb_period: int,
    breakout_bb_std: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    feedback = pd.read_csv(feedback_path)
    rows = []

    for sample, group in feedback.groupby("sample"):
        path = sample_dir(root, int(sample))
        window = load_rule_test_window(path, breakout_bb_period, breakout_bb_std)
        boxes = load_boxes(path)
        for _, fb in group.iterrows():
            status = str(fb["status"])
            if status == "rejected":
                continue
            box_num = int(fb["box"])
            match = boxes[boxes["box"] == box_num]
            if match.empty:
                raise ValueError(f"Missing sample {sample} box {box_num}")
            rows.append(backtest_box(window, int(sample), match.iloc[0], status, str(fb["note"])))

    trades = pd.DataFrame(rows)
    out_dir.mkdir(parents=True, exist_ok=True)
    trades.to_csv(out_dir / "breakout_pullback_v0_trades.csv", index=False)

    filled = trades[trades["trade_status"] == "filled"].copy()
    if "outcome" in filled.columns:
        targets = filled[filled["outcome"] == "target"]
        stops = filled[filled["outcome"] == "stop"]
        time_exits = filled[filled["outcome"] == "time_exit"]
    else:
        targets = filled.iloc[0:0]
        stops = filled.iloc[0:0]
        time_exits = filled.iloc[0:0]

    summary = pd.DataFrame(
        [
            {
                "boxes_tested": len(trades),
                "signals": int(trades["signal_time_new_york"].notna().sum()) if "signal_time_new_york" in trades else 0,
                "filled_trades": len(filled),
                "targets": len(targets),
                "stops": len(stops),
                "time_exits": len(time_exits),
                "target_rate_filled": round(len(targets) / len(filled), 3) if len(filled) else 0.0,
                "stop_rate_filled": round(len(stops) / len(filled), 3) if len(filled) else 0.0,
                "fill_rate_per_box": round(len(filled) / len(trades), 3) if len(trades) else 0.0,
                "net_pips_total": round(float(filled["net_pips"].sum()), 2)
                if len(filled) and "net_pips" in filled.columns
                else 0.0,
                "net_pips_avg": round(float(filled["net_pips"].mean()), 2)
                if len(filled) and "net_pips" in filled.columns
                else 0.0,
                "net_r_avg": round(float(filled["net_r"].mean()), 3)
                if len(filled) and "net_r" in filled.columns
                else 0.0,
                "profit_factor_gross_pips": round(
                    float(filled[filled["net_pips"] > 0]["net_pips"].sum())
                    / abs(float(filled[filled["net_pips"] < 0]["net_pips"].sum())),
                    3,
                )
                if len(filled) and "net_pips" in filled.columns and len(filled[filled["net_pips"] < 0])
                else math.inf,
                "breakout_bb_period": breakout_bb_period,
                "breakout_bb_std": breakout_bb_std,
            }
        ]
    )
    summary.to_csv(out_dir / "summary.csv", index=False)
    return trades, summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--feedback", type=Path, default=Path("compression_expansion_feedback_full_window.csv"))
    parser.add_argument("--root", type=Path, default=Path("training_samples"))
    parser.add_argument("--out-dir", type=Path, default=Path("trade_backtest_breakout_pullback_v0"))
    parser.add_argument("--breakout-bb-period", type=int, default=20)
    parser.add_argument("--breakout-bb-std", type=float, default=2.0)
    args = parser.parse_args()

    trades, summary = run_backtest(args.feedback, args.root, args.out_dir, args.breakout_bb_period, args.breakout_bb_std)
    print(summary.to_string(index=False))
    if not trades.empty:
        cols = [col for col in ["sample", "box", "trade_status", "direction", "outcome", "net_pips", "net_r"] if col in trades.columns]
        print(trades[cols].to_string(index=False))
    print(args.out_dir / "breakout_pullback_v0_trades.csv")
    print(args.out_dir / "summary.csv")


if __name__ == "__main__":
    main()
