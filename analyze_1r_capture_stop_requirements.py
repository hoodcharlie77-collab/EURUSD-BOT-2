from __future__ import annotations

import argparse
import math
from pathlib import Path

import pandas as pd

from audit_compression_expansion import load_boxes, parse_est, sample_dir
from make_blind_bb_training_sample import NY, PIP


CAPTURE_LEVELS = [0.50, 0.70, 0.90]


def box_stats(window: pd.DataFrame, start_utc: pd.Timestamp, end_utc: pd.Timestamp) -> dict:
    chunk = window[(window["timestamp"] >= start_utc) & (window["timestamp"] <= end_utc)].copy()
    if chunk.empty:
        raise ValueError(f"No box bars between {start_utc} and {end_utc}")
    high = float(chunk["high"].max())
    low = float(chunk["low"].min())
    r_price = high - low
    return {"high": high, "low": low, "r_price": r_price, "r_pips": r_price / PIP}


def first_1r_target(
    post: pd.DataFrame,
    box_low: float,
    box_high: float,
    r_price: float,
) -> tuple[str | None, int | None, pd.Timestamp | None]:
    for idx, row in post.iterrows():
        up_hit = float(row["high"]) >= box_high + r_price
        down_hit = float(row["low"]) <= box_low - r_price
        if up_hit and down_hit:
            direction = "up" if float(row["close"]) >= (box_high + box_low) / 2 else "down"
            return direction, int(idx), row["timestamp"]
        if up_hit:
            return "up", int(idx), row["timestamp"]
        if down_hit:
            return "down", int(idx), row["timestamp"]
    return None, None, None


def first_close_break(
    post: pd.DataFrame,
    box_low: float,
    box_high: float,
    r_price: float,
) -> tuple[str | None, int | None, pd.Timestamp | None, float | None]:
    buffer_price = max(0.5 * PIP, r_price * 0.10)
    for idx, row in post.iterrows():
        close = float(row["close"])
        if close > box_high + buffer_price:
            return "up", int(idx), row["timestamp"], close
        if close < box_low - buffer_price:
            return "down", int(idx), row["timestamp"], close
    return None, None, None, None


def boundary_entry_stop_r(
    window: pd.DataFrame,
    direction: str,
    target_i: int,
    box_low: float,
    box_high: float,
    r_price: float,
    box_end_utc: pd.Timestamp,
) -> tuple[float, float, pd.Timestamp]:
    post_to_target = window[(window["timestamp"] > box_end_utc) & (window.index <= target_i)].copy()
    if direction == "up":
        entry_candidates = post_to_target[post_to_target["high"] >= box_high]
        if entry_candidates.empty:
            raise ValueError("Up target hit without boundary entry")
        entry_i = int(entry_candidates.index[0])
        trade_bars = window[(window.index >= entry_i) & (window.index <= target_i)].copy()
        adverse_price = max(0.0, box_high - float(trade_bars["low"].min()))
    else:
        entry_candidates = post_to_target[post_to_target["low"] <= box_low]
        if entry_candidates.empty:
            raise ValueError("Down target hit without boundary entry")
        entry_i = int(entry_candidates.index[0])
        trade_bars = window[(window.index >= entry_i) & (window.index <= target_i)].copy()
        adverse_price = max(0.0, float(trade_bars["high"].max()) - box_low)

    return adverse_price / r_price, adverse_price / PIP, window.loc[entry_i, "timestamp"]


def breakout_close_entry_stop_r(
    window: pd.DataFrame,
    break_dir: str,
    break_i: int,
    entry_price: float,
    box_low: float,
    box_high: float,
    r_price: float,
    box_end_utc: pd.Timestamp,
) -> tuple[bool, float, float, pd.Timestamp | None]:
    target = box_high + r_price if break_dir == "up" else box_low - r_price
    deadline = box_end_utc + pd.Timedelta(minutes=120)
    after_entry = window[(window.index > break_i) & (window["timestamp"] <= deadline)].copy()
    target_i = None
    for idx, row in after_entry.iterrows():
        if break_dir == "up" and float(row["high"]) >= target:
            target_i = int(idx)
            break
        if break_dir == "down" and float(row["low"]) <= target:
            target_i = int(idx)
            break

    if target_i is None:
        return False, math.nan, math.nan, None

    trade_bars = window[(window.index > break_i) & (window.index <= target_i)].copy()
    if break_dir == "up":
        adverse_price = max(0.0, entry_price - float(trade_bars["low"].min()))
    else:
        adverse_price = max(0.0, float(trade_bars["high"].max()) - entry_price)

    return True, adverse_price / r_price, adverse_price / PIP, window.loc[target_i, "timestamp"]


def threshold_rows(rows: pd.DataFrame, label: str) -> pd.DataFrame:
    ordered = rows.sort_values("required_stop_r").reset_index(drop=True)
    out_rows = []
    n = len(ordered)
    for level in CAPTURE_LEVELS:
        rank = max(1, math.ceil(level * n))
        picked = ordered.iloc[rank - 1]
        captured = int((ordered["required_stop_r"] <= picked["required_stop_r"]).sum())
        out_rows.append(
            {
                "model": label,
                "wins_measured": n,
                "capture_goal": level,
                "required_stop_r": round(float(picked["required_stop_r"]), 3),
                "required_stop_pips_at_threshold_case": round(float(picked["required_stop_pips"]), 2),
                "captured_wins": captured,
                "captured_rate": round(captured / n, 3) if n else 0.0,
            }
        )
    return pd.DataFrame(out_rows)


def analyze(feedback_path: Path, root: Path, out_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    feedback = pd.read_csv(feedback_path)
    boundary_rows = []
    breakout_rows = []
    all_boxes = []

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

            box = match.iloc[0]
            start_utc = parse_est(str(box["start_new_york"]))
            end_utc = parse_est(str(box["end_new_york"]))
            stats = box_stats(window, start_utc, end_utc)
            post_120 = window[
                (window["timestamp"] > end_utc) & (window["timestamp"] <= end_utc + pd.Timedelta(minutes=120))
            ].copy()
            target_dir, target_i, target_time = first_1r_target(post_120, stats["low"], stats["high"], stats["r_price"])

            base = {
                "sample": int(sample),
                "box": box_num,
                "status": status,
                "box_start_new_york": start_utc.tz_convert(NY).strftime("%Y-%m-%d %H:%M EST"),
                "box_end_new_york": end_utc.tz_convert(NY).strftime("%Y-%m-%d %H:%M EST"),
                "box_range_pips": round(stats["r_pips"], 2),
                "hit_1r_120m": bool(target_dir),
                "target_dir": target_dir or "",
                "target_time_new_york": target_time.tz_convert(NY).strftime("%Y-%m-%d %H:%M EST")
                if target_time is not None
                else "",
            }
            all_boxes.append(base.copy())

            if target_dir and target_i is not None:
                stop_r, stop_pips, entry_time = boundary_entry_stop_r(
                    window,
                    target_dir,
                    target_i,
                    stats["low"],
                    stats["high"],
                    stats["r_price"],
                    end_utc,
                )
                boundary_rows.append(
                    {
                        **base,
                        "entry_model": "box_boundary_in_eventual_target_direction",
                        "entry_time_new_york": entry_time.tz_convert(NY).strftime("%Y-%m-%d %H:%M EST"),
                        "required_stop_r": stop_r,
                        "required_stop_pips": stop_pips,
                    }
                )

            post_60 = window[
                (window["timestamp"] > end_utc) & (window["timestamp"] <= end_utc + pd.Timedelta(minutes=60))
            ].copy()
            break_dir, break_i, break_time, entry_price = first_close_break(post_60, stats["low"], stats["high"], stats["r_price"])
            if break_dir and break_i is not None and entry_price is not None:
                same_dir_target, stop_r, stop_pips, same_dir_target_time = breakout_close_entry_stop_r(
                    window,
                    break_dir,
                    break_i,
                    entry_price,
                    stats["low"],
                    stats["high"],
                    stats["r_price"],
                    end_utc,
                )
                if same_dir_target:
                    breakout_rows.append(
                        {
                            **base,
                            "entry_model": "first_breakout_close_same_direction_target",
                            "first_break_dir": break_dir,
                            "entry_time_new_york": break_time.tz_convert(NY).strftime("%Y-%m-%d %H:%M EST"),
                            "entry_price": round(float(entry_price), 5),
                            "same_direction_target_time_new_york": same_dir_target_time.tz_convert(NY).strftime(
                                "%Y-%m-%d %H:%M EST"
                            )
                            if same_dir_target_time is not None
                            else "",
                            "required_stop_r": stop_r,
                            "required_stop_pips": stop_pips,
                        }
                    )

    out_dir.mkdir(parents=True, exist_ok=True)
    all_boxes_df = pd.DataFrame(all_boxes)
    boundary_df = pd.DataFrame(boundary_rows)
    breakout_df = pd.DataFrame(breakout_rows)
    thresholds = pd.concat(
        [
            threshold_rows(boundary_df, "box_boundary_in_eventual_target_direction"),
            threshold_rows(breakout_df, "first_breakout_close_same_direction_target"),
        ],
        ignore_index=True,
    )
    all_boxes_df.to_csv(out_dir / "all_compression_boxes_1r_hits.csv", index=False)
    boundary_df.to_csv(out_dir / "boundary_entry_required_stops.csv", index=False)
    breakout_df.to_csv(out_dir / "breakout_close_required_stops.csv", index=False)
    thresholds.to_csv(out_dir / "required_stop_thresholds.csv", index=False)
    return all_boxes_df, boundary_df, breakout_df, thresholds


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--feedback", type=Path, default=Path("compression_expansion_feedback_full_window.csv"))
    parser.add_argument("--root", type=Path, default=Path("training_samples"))
    parser.add_argument("--out-dir", type=Path, default=Path("stop_requirements_1r_capture"))
    args = parser.parse_args()

    all_boxes, boundary, breakout, thresholds = analyze(args.feedback, args.root, args.out_dir)
    print(f"compression_boxes={len(all_boxes)} hit_1r_120m={int(all_boxes['hit_1r_120m'].sum())}")
    print(f"boundary_wins_measured={len(boundary)} breakout_close_same_direction_wins_measured={len(breakout)}")
    print(thresholds.to_string(index=False))
    print(args.out_dir / "required_stop_thresholds.csv")


if __name__ == "__main__":
    main()
