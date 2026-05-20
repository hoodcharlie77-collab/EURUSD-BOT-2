from __future__ import annotations

import argparse
import math
from pathlib import Path

import pandas as pd

from audit_compression_expansion import load_boxes, parse_est, sample_dir
from make_blind_bb_training_sample import NY, PIP


SPREAD_PIPS = 1.2


def parse_float_list(raw: str) -> list[float]:
    values = []
    for item in raw.split(","):
        item = item.strip()
        if item:
            values.append(float(item))
    if not values:
        raise ValueError("No values supplied")
    return values


def ratio_label(value: float) -> str:
    return f"{value:g}".replace(".", "p")


def box_stats(window: pd.DataFrame, start_utc: pd.Timestamp, end_utc: pd.Timestamp) -> dict:
    chunk = window[(window["timestamp"] >= start_utc) & (window["timestamp"] <= end_utc)].copy()
    if chunk.empty:
        raise ValueError(f"No box bars between {start_utc} and {end_utc}")
    high = float(chunk["high"].max())
    low = float(chunk["low"].min())
    range_price = high - low
    return {
        "high": high,
        "low": low,
        "range_price": range_price,
        "range_pips": range_price / PIP,
    }


def first_close_break(
    window: pd.DataFrame,
    box_end_utc: pd.Timestamp,
    box_high: float,
    box_low: float,
    r_price: float,
) -> dict | None:
    start = box_end_utc + pd.Timedelta(minutes=5)
    deadline = box_end_utc + pd.Timedelta(minutes=60)
    post = window[(window["timestamp"] >= start) & (window["timestamp"] <= deadline)].copy()
    buffer_price = max(0.5 * PIP, r_price * 0.10)

    for idx, row in post.iterrows():
        close = float(row["close"])
        if close > box_high + buffer_price:
            return {
                "signal_i": int(idx),
                "signal_time": row["timestamp"],
                "direction": "long",
                "entry_price": close,
                "breakout_close": close,
                "box_break_buffer_pips": buffer_price / PIP,
            }
        if close < box_low - buffer_price:
            return {
                "signal_i": int(idx),
                "signal_time": row["timestamp"],
                "direction": "short",
                "entry_price": close,
                "breakout_close": close,
                "box_break_buffer_pips": buffer_price / PIP,
            }
    return None


def resolve_trade(
    window: pd.DataFrame,
    signal_i: int,
    entry_price: float,
    direction: str,
    stop_price: float,
    target_price: float,
    box_end_utc: pd.Timestamp,
) -> dict:
    deadline = box_end_utc + pd.Timedelta(minutes=120)
    trade_bars = window[(window.index > signal_i) & (window["timestamp"] <= deadline)].copy()

    for _, row in trade_bars.iterrows():
        high = float(row["high"])
        low = float(row["low"])
        if direction == "long":
            stop_hit = low <= stop_price
            target_hit = high >= target_price
        else:
            stop_hit = high >= stop_price
            target_hit = low <= target_price

        if stop_hit:
            gross_pips = -abs(entry_price - stop_price) / PIP
            return {
                "outcome": "stop",
                "exit_time": row["timestamp"],
                "exit_price": stop_price,
                "gross_pips": gross_pips,
                "net_pips": gross_pips - SPREAD_PIPS,
            }
        if target_hit:
            gross_pips = abs(target_price - entry_price) / PIP
            return {
                "outcome": "target",
                "exit_time": row["timestamp"],
                "exit_price": target_price,
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


def backtest_box(
    window: pd.DataFrame,
    sample: int,
    box_row: pd.Series,
    status: str,
    note: str,
    stop_r: float,
    target_r: float,
    target_mode: str,
) -> dict:
    box_num = int(box_row["box"])
    start_utc = parse_est(str(box_row["start_new_york"]))
    end_utc = parse_est(str(box_row["end_new_york"]))
    stats = box_stats(window, start_utc, end_utc)
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
        "entry_rule": "first_close_breakout",
        "stop_r": stop_r,
        "target_r": target_r,
        "target_mode": target_mode,
    }

    signal = first_close_break(window, end_utc, stats["high"], stats["low"], r_price)
    if signal is None:
        result.update({"trade_status": "no_signal"})
        return result

    entry_price = float(signal["entry_price"])

    if signal["direction"] == "long":
        stop_price = entry_price - stop_r * r_price
        if target_mode == "entry_r":
            target_price = entry_price + target_r * r_price
        elif target_mode == "box_extension_r":
            target_price = stats["high"] + target_r * r_price
        else:
            raise ValueError(f"Unknown target mode: {target_mode}")
    else:
        stop_price = entry_price + stop_r * r_price
        if target_mode == "entry_r":
            target_price = entry_price - target_r * r_price
        elif target_mode == "box_extension_r":
            target_price = stats["low"] - target_r * r_price
        else:
            raise ValueError(f"Unknown target mode: {target_mode}")

    risk_pips = abs(entry_price - stop_price) / PIP
    reward_pips = abs(target_price - entry_price) / PIP
    if reward_pips <= 0:
        result.update(
            {
                "trade_status": "no_trade",
                "direction": signal["direction"],
                "signal_time_new_york": signal["signal_time"].tz_convert(NY).strftime("%Y-%m-%d %H:%M EST"),
                "signal_minutes_after_box": round((signal["signal_time"] - end_utc) / pd.Timedelta(minutes=1), 1),
                "entry_price": round(entry_price, 5),
                "box_break_buffer_pips": round(float(signal["box_break_buffer_pips"]), 2),
                "outcome": "entry_beyond_target",
            }
        )
        return result

    resolved = resolve_trade(
        window,
        int(signal["signal_i"]),
        entry_price,
        signal["direction"],
        stop_price,
        target_price,
        end_utc,
    )
    net_r_vs_box = resolved["net_pips"] / r_pips if r_pips else math.nan
    expectancy_risk_r = resolved["net_pips"] / risk_pips if risk_pips else math.nan

    result.update(
        {
            "trade_status": "filled",
            "direction": signal["direction"],
            "signal_time_new_york": signal["signal_time"].tz_convert(NY).strftime("%Y-%m-%d %H:%M EST"),
            "signal_minutes_after_box": round((signal["signal_time"] - end_utc) / pd.Timedelta(minutes=1), 1),
            "entry_price": round(entry_price, 5),
            "box_break_buffer_pips": round(float(signal["box_break_buffer_pips"]), 2),
            "stop_price": round(stop_price, 5),
            "target_price": round(target_price, 5),
            "risk_pips": round(risk_pips, 2),
            "reward_pips": round(reward_pips, 2),
            "outcome": resolved["outcome"],
            "exit_time_new_york": resolved["exit_time"].tz_convert(NY).strftime("%Y-%m-%d %H:%M EST")
            if not pd.isna(resolved["exit_time"])
            else "",
            "exit_price": round(resolved["exit_price"], 5) if not pd.isna(resolved["exit_price"]) else "",
            "gross_pips": round(resolved["gross_pips"], 2),
            "net_pips": round(resolved["net_pips"], 2),
            "net_r_vs_box": round(net_r_vs_box, 3),
            "net_risk_r": round(expectancy_risk_r, 3),
            "spread_pips_round_turn": SPREAD_PIPS,
        }
    )
    return result


def equity_stats(filled: pd.DataFrame, risk_per_trade: float) -> dict:
    if filled.empty or "net_risk_r" not in filled.columns:
        return {
            "sum_net_risk_r": 0.0,
            "roi_pct": 0.0,
            "max_drawdown_pct": 0.0,
            "ending_equity_index": 100.0,
        }

    ordered = filled.copy()
    if "signal_time_new_york" in ordered.columns:
        ordered["_signal_time"] = ordered["signal_time_new_york"].apply(lambda value: parse_est(str(value)))
        ordered = ordered.sort_values(["_signal_time", "sample", "box"])
    else:
        ordered = ordered.sort_values(["sample", "box"])

    equity = 1.0
    peak = 1.0
    max_dd = 0.0
    for r_mult in ordered["net_risk_r"].fillna(0.0):
        equity *= 1.0 + risk_per_trade * float(r_mult)
        peak = max(peak, equity)
        if peak:
            max_dd = max(max_dd, (peak - equity) / peak)

    return {
        "sum_net_risk_r": round(float(ordered["net_risk_r"].sum()), 3),
        "roi_pct": round((equity - 1.0) * 100.0, 2),
        "max_drawdown_pct": round(max_dd * 100.0, 2),
        "ending_equity_index": round(equity * 100.0, 2),
    }


def summarize_trades(
    trades: pd.DataFrame,
    stop_r: float,
    target_r: float,
    target_mode: str,
    risk_per_trade: float,
) -> dict:
    filled = trades[trades["trade_status"] == "filled"].copy()
    targets = filled[filled["outcome"] == "target"] if "outcome" in filled.columns else filled.iloc[0:0]
    stops = filled[filled["outcome"] == "stop"] if "outcome" in filled.columns else filled.iloc[0:0]
    time_exits = filled[filled["outcome"] == "time_exit"] if "outcome" in filled.columns else filled.iloc[0:0]
    losers = filled[filled["net_pips"] < 0] if "net_pips" in filled.columns else filled.iloc[0:0]
    winners = filled[filled["net_pips"] > 0] if "net_pips" in filled.columns else filled.iloc[0:0]
    gross_profit = float(winners["net_pips"].sum()) if len(winners) else 0.0
    gross_loss = abs(float(losers["net_pips"].sum())) if len(losers) else 0.0
    curve = equity_stats(filled, risk_per_trade)

    return {
        "stop_r": stop_r,
        "target_r": target_r,
        "target_mode": target_mode,
        "risk_per_trade_pct": round(risk_per_trade * 100.0, 3),
        "boxes_tested": len(trades),
        "signals": len(filled),
        "targets": len(targets),
        "stops": len(stops),
        "time_exits": len(time_exits),
        "win_rate": round(len(targets) / len(filled), 3) if len(filled) else 0.0,
        "positive_net_trades": len(winners),
        "negative_net_trades": len(losers),
        "positive_net_rate": round(len(winners) / len(filled), 3) if len(filled) else 0.0,
        "gross_pips_total": round(float(filled["gross_pips"].sum()), 2) if len(filled) else 0.0,
        "gross_pips_avg": round(float(filled["gross_pips"].mean()), 2) if len(filled) else 0.0,
        "net_pips_total": round(float(filled["net_pips"].sum()), 2) if len(filled) else 0.0,
        "net_pips_avg": round(float(filled["net_pips"].mean()), 2) if len(filled) else 0.0,
        "net_risk_r_avg": round(float(filled["net_risk_r"].mean()), 3) if len(filled) else 0.0,
        "profit_factor_net_pips": round(gross_profit / gross_loss, 3) if gross_loss else math.inf,
        **curve,
    }


def run_backtest(
    feedback_path: Path,
    root: Path,
    out_dir: Path,
    stop_r: float,
    target_r: float,
    target_mode: str,
    risk_per_trade: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    feedback = pd.read_csv(feedback_path)
    rows = []

    for sample, group in feedback.groupby("sample"):
        path = sample_dir(root, int(sample))
        window = pd.read_csv(path / "full_12h_bars.csv", parse_dates=["timestamp", "timestamp_ny"])
        boxes = load_boxes(path)
        for _, fb in group.iterrows():
            status = str(fb["status"])
            if status == "rejected":
                continue
            box_num = int(fb["box"])
            match = boxes[boxes["box"] == box_num]
            if match.empty:
                raise ValueError(f"Missing sample {sample} box {box_num}")
            rows.append(
                backtest_box(window, int(sample), match.iloc[0], status, str(fb["note"]), stop_r, target_r, target_mode)
            )

    trades = pd.DataFrame(rows)
    out_dir.mkdir(parents=True, exist_ok=True)
    trades.to_csv(out_dir / "breakout_close_trades.csv", index=False)
    summary = pd.DataFrame([summarize_trades(trades, stop_r, target_r, target_mode, risk_per_trade)])
    summary.to_csv(out_dir / "summary.csv", index=False)
    return trades, summary


def run_sweep(
    feedback_path: Path,
    root: Path,
    out_dir: Path,
    stop_values: list[float],
    target_r: float,
    target_mode: str,
    risk_per_trade: float,
) -> pd.DataFrame:
    out_dir.mkdir(parents=True, exist_ok=True)
    summaries = []
    for stop_r in stop_values:
        stop_dir = out_dir / f"stop_{ratio_label(stop_r)}r"
        _, summary = run_backtest(feedback_path, root, stop_dir, stop_r, target_r, target_mode, risk_per_trade)
        summaries.append(summary.iloc[0].to_dict())
    sweep = pd.DataFrame(summaries)
    sweep.to_csv(out_dir / "stop_sweep_summary.csv", index=False)
    return sweep


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--feedback", type=Path, default=Path("compression_expansion_feedback_full_window.csv"))
    parser.add_argument("--root", type=Path, default=Path("training_samples"))
    parser.add_argument("--out-dir", type=Path, default=Path("trade_backtest_breakout_close_stop_sweep"))
    parser.add_argument("--stop-r-values", default="0.25,0.5,0.75,1.0,1.25,1.5,2.0")
    parser.add_argument("--target-r", type=float, default=1.0)
    parser.add_argument("--target-mode", choices=["entry_r", "box_extension_r"], default="entry_r")
    parser.add_argument("--risk-per-trade", type=float, default=0.005)
    args = parser.parse_args()

    sweep = run_sweep(
        args.feedback,
        args.root,
        args.out_dir,
        parse_float_list(args.stop_r_values),
        args.target_r,
        args.target_mode,
        args.risk_per_trade,
    )
    print(sweep.to_string(index=False))
    print(args.out_dir / "stop_sweep_summary.csv")


if __name__ == "__main__":
    main()
