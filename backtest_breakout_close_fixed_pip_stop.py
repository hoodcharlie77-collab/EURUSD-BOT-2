from __future__ import annotations

import argparse
import math
from pathlib import Path

import pandas as pd

from audit_compression_expansion import load_boxes, parse_est, sample_dir
from backtest_breakout_close_stop_sweep import box_stats, first_close_break, parse_float_list, resolve_trade
from make_blind_bb_training_sample import NY, PIP


SPREAD_PIPS = 1.2


def value_label(value: float) -> str:
    return f"{value:g}".replace(".", "p")


def equity_stats(filled: pd.DataFrame, risk_per_trade: float) -> dict:
    if filled.empty or "net_risk_r" not in filled.columns:
        return {
            "sum_net_risk_r": 0.0,
            "roi_pct": 0.0,
            "max_drawdown_pct": 0.0,
            "ending_equity_index": 100.0,
        }

    ordered = filled.copy()
    ordered["_signal_time"] = ordered["signal_time_new_york"].apply(lambda value: parse_est(str(value)))
    ordered = ordered.sort_values(["_signal_time", "sample", "box"])

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


def backtest_box(
    window: pd.DataFrame,
    sample: int,
    box_row: pd.Series,
    status: str,
    note: str,
    stop_pips: float,
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
        "stop_mode": "fixed_pips",
        "stop_pips": stop_pips,
        "target_r": target_r,
        "target_mode": target_mode,
    }

    signal = first_close_break(window, end_utc, stats["high"], stats["low"], r_price)
    if signal is None:
        result.update({"trade_status": "no_signal"})
        return result

    entry_price = float(signal["entry_price"])
    stop_price_offset = stop_pips * PIP

    if signal["direction"] == "long":
        stop_price = entry_price - stop_price_offset
        if target_mode == "entry_r":
            target_price = entry_price + target_r * r_price
        elif target_mode == "box_extension_r":
            target_price = stats["high"] + target_r * r_price
        else:
            raise ValueError(f"Unknown target mode: {target_mode}")
    else:
        stop_price = entry_price + stop_price_offset
        if target_mode == "entry_r":
            target_price = entry_price - target_r * r_price
        elif target_mode == "box_extension_r":
            target_price = stats["low"] - target_r * r_price
        else:
            raise ValueError(f"Unknown target mode: {target_mode}")

    reward_pips = abs(target_price - entry_price) / PIP
    if reward_pips <= 0:
        result.update(
            {
                "trade_status": "no_trade",
                "direction": signal["direction"],
                "signal_time_new_york": signal["signal_time"].tz_convert(NY).strftime("%Y-%m-%d %H:%M EST"),
                "signal_minutes_after_box": round((signal["signal_time"] - end_utc) / pd.Timedelta(minutes=1), 1),
                "entry_price": round(entry_price, 5),
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
    result.update(
        {
            "trade_status": "filled",
            "direction": signal["direction"],
            "signal_time_new_york": signal["signal_time"].tz_convert(NY).strftime("%Y-%m-%d %H:%M EST"),
            "signal_minutes_after_box": round((signal["signal_time"] - end_utc) / pd.Timedelta(minutes=1), 1),
            "entry_price": round(entry_price, 5),
            "stop_price": round(stop_price, 5),
            "target_price": round(target_price, 5),
            "risk_pips": round(stop_pips, 2),
            "reward_pips": round(reward_pips, 2),
            "reward_to_risk": round(reward_pips / stop_pips, 3) if stop_pips else math.nan,
            "outcome": resolved["outcome"],
            "exit_time_new_york": resolved["exit_time"].tz_convert(NY).strftime("%Y-%m-%d %H:%M EST")
            if not pd.isna(resolved["exit_time"])
            else "",
            "exit_price": round(resolved["exit_price"], 5) if not pd.isna(resolved["exit_price"]) else "",
            "gross_pips": round(resolved["gross_pips"], 2),
            "net_pips": round(resolved["net_pips"], 2),
            "net_r_vs_box": round(resolved["net_pips"] / r_pips, 3) if r_pips else math.nan,
            "net_risk_r": round(resolved["net_pips"] / stop_pips, 3) if stop_pips else math.nan,
            "spread_pips_round_turn": SPREAD_PIPS,
        }
    )
    return result


def summarize_trades(trades: pd.DataFrame, stop_pips: float, target_r: float, target_mode: str, risk_per_trade: float) -> dict:
    filled = trades[trades["trade_status"] == "filled"].copy()
    targets = filled[filled["outcome"] == "target"] if "outcome" in filled.columns else filled.iloc[0:0]
    stops = filled[filled["outcome"] == "stop"] if "outcome" in filled.columns else filled.iloc[0:0]
    time_exits = filled[filled["outcome"] == "time_exit"] if "outcome" in filled.columns else filled.iloc[0:0]
    winners = filled[filled["net_pips"] > 0] if "net_pips" in filled.columns else filled.iloc[0:0]
    losers = filled[filled["net_pips"] < 0] if "net_pips" in filled.columns else filled.iloc[0:0]
    gross_profit = float(winners["net_pips"].sum()) if len(winners) else 0.0
    gross_loss = abs(float(losers["net_pips"].sum())) if len(losers) else 0.0

    return {
        "stop_pips": stop_pips,
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
        "avg_reward_to_risk": round(float(filled["reward_to_risk"].mean()), 3) if len(filled) else 0.0,
        "gross_pips_total": round(float(filled["gross_pips"].sum()), 2) if len(filled) else 0.0,
        "net_pips_total": round(float(filled["net_pips"].sum()), 2) if len(filled) else 0.0,
        "net_pips_avg": round(float(filled["net_pips"].mean()), 2) if len(filled) else 0.0,
        "net_risk_r_avg": round(float(filled["net_risk_r"].mean()), 3) if len(filled) else 0.0,
        "profit_factor_net_pips": round(gross_profit / gross_loss, 3) if gross_loss else math.inf,
        **equity_stats(filled, risk_per_trade),
    }


def run_backtest(
    feedback_path: Path,
    root: Path,
    out_dir: Path,
    stop_pips: float,
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
                backtest_box(
                    window,
                    int(sample),
                    match.iloc[0],
                    status,
                    str(fb["note"]),
                    stop_pips,
                    target_r,
                    target_mode,
                )
            )

    trades = pd.DataFrame(rows)
    out_dir.mkdir(parents=True, exist_ok=True)
    trades.to_csv(out_dir / "breakout_close_fixed_stop_trades.csv", index=False)
    summary = pd.DataFrame([summarize_trades(trades, stop_pips, target_r, target_mode, risk_per_trade)])
    summary.to_csv(out_dir / "summary.csv", index=False)
    return trades, summary


def run_sweep(
    feedback_path: Path,
    root: Path,
    out_dir: Path,
    stop_pip_values: list[float],
    target_r: float,
    target_mode: str,
    risk_per_trade: float,
) -> pd.DataFrame:
    out_dir.mkdir(parents=True, exist_ok=True)
    summaries = []
    for stop_pips in stop_pip_values:
        stop_dir = out_dir / f"stop_{value_label(stop_pips)}pips"
        _, summary = run_backtest(feedback_path, root, stop_dir, stop_pips, target_r, target_mode, risk_per_trade)
        summaries.append(summary.iloc[0].to_dict())
    sweep = pd.DataFrame(summaries)
    sweep.to_csv(out_dir / "fixed_stop_sweep_summary.csv", index=False)
    return sweep


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--feedback", type=Path, default=Path("compression_expansion_feedback_full_window.csv"))
    parser.add_argument("--root", type=Path, default=Path("training_samples"))
    parser.add_argument("--out-dir", type=Path, default=Path("trade_backtest_breakout_close_fixed_stop"))
    parser.add_argument("--stop-pips-values", default="6,7,10")
    parser.add_argument("--target-r", type=float, default=1.0)
    parser.add_argument("--target-mode", choices=["entry_r", "box_extension_r"], default="entry_r")
    parser.add_argument("--risk-per-trade", type=float, default=0.005)
    args = parser.parse_args()

    sweep = run_sweep(
        args.feedback,
        args.root,
        args.out_dir,
        parse_float_list(args.stop_pips_values),
        args.target_r,
        args.target_mode,
        args.risk_per_trade,
    )
    print(sweep.to_string(index=False))
    print(args.out_dir / "fixed_stop_sweep_summary.csv")


if __name__ == "__main__":
    main()
