from __future__ import annotations

import argparse
import math
import random
from pathlib import Path

import pandas as pd

from make_blind_bb_training_sample import NY, PIP, in_late_ny_garbage


HORIZONS_MIN = [30, 60, 90, 120]
TARGET_RATIOS = [0.75, 1.0, 1.5, 2.0]


def parse_est(value: str) -> pd.Timestamp:
    clean = value.replace(" EST", "")
    return pd.Timestamp(clean, tz=NY).tz_convert("UTC")


def sample_dir(root: Path, sample: int) -> Path:
    return root / f"bb5_x4_5min_12h_rule_test_{sample:03d}"


def load_boxes(path: Path) -> pd.DataFrame:
    missed_path = path / "rule_boxes_with_missed_0400.csv"
    if missed_path.exists():
        return pd.read_csv(missed_path)
    return pd.read_csv(path / "rule_boxes.csv")


def box_stats(window: pd.DataFrame, start_utc: pd.Timestamp, end_utc: pd.Timestamp) -> dict:
    mask = (window["timestamp"] >= start_utc) & (window["timestamp"] <= end_utc)
    chunk = window[mask].copy()
    if chunk.empty:
        raise ValueError(f"No bars found for box {start_utc} to {end_utc}")

    low = float(chunk["low"].min())
    high = float(chunk["high"].max())
    range_pips = (high - low) / PIP
    return {
        "box_low": low,
        "box_high": high,
        "box_range_pips": range_pips,
        "box_bb_width_median": float(chunk["bb_width_pips"].median()),
        "box_bars": len(chunk),
        "box_duration_min": len(chunk) * 5,
    }


def first_close_break(post: pd.DataFrame, box_low: float, box_high: float, buffer_price: float) -> tuple[str | None, pd.Timestamp | None]:
    for _, row in post.iterrows():
        close = float(row["close"])
        if close > box_high + buffer_price:
            return "up", row["timestamp"]
        if close < box_low - buffer_price:
            return "down", row["timestamp"]
    return None, None


def first_target_hit(
    post: pd.DataFrame,
    box_low: float,
    box_high: float,
    target_price: float,
) -> tuple[str | None, pd.Timestamp | None]:
    for _, row in post.iterrows():
        up_hit = float(row["high"]) >= box_high + target_price
        down_hit = float(row["low"]) <= box_low - target_price
        if up_hit and down_hit:
            # Rare intrabar ambiguity. Treat close side as the first useful direction.
            return ("up" if float(row["close"]) >= (box_high + box_low) / 2 else "down"), row["timestamp"]
        if up_hit:
            return "up", row["timestamp"]
        if down_hit:
            return "down", row["timestamp"]
    return None, None


def measure_forward(
    window: pd.DataFrame,
    start_utc: pd.Timestamp,
    end_utc: pd.Timestamp,
    label: str,
    sample: int,
    box_num: int,
    status: str,
    note: str,
) -> dict:
    stats = box_stats(window, start_utc, end_utc)
    box_low = stats["box_low"]
    box_high = stats["box_high"]
    box_range_pips = stats["box_range_pips"]
    box_range_price = box_range_pips * PIP
    box_bb_med = max(stats["box_bb_width_median"], 0.01)

    row: dict = {
        "sample": sample,
        "box": box_num,
        "label": label,
        "status": status,
        "note": note,
        "start_new_york": start_utc.tz_convert(NY).strftime("%Y-%m-%d %H:%M EST"),
        "end_new_york": end_utc.tz_convert(NY).strftime("%Y-%m-%d %H:%M EST"),
        "box_bars": stats["box_bars"],
        "box_duration_min": stats["box_duration_min"],
        "box_range_pips": round(box_range_pips, 2),
        "box_bb_width_median": round(box_bb_med, 2),
    }

    post_120 = window[(window["timestamp"] > end_utc) & (window["timestamp"] <= end_utc + pd.Timedelta(minutes=max(HORIZONS_MIN)))]
    buffer_price = max(0.5 * PIP, box_range_price * 0.10)
    first_break_dir, first_break_time = first_close_break(post_120, box_low, box_high, buffer_price)
    target_dir, target_time = first_target_hit(post_120, box_low, box_high, box_range_price)
    row["first_close_break_dir"] = first_break_dir or ""
    row["first_close_break_min"] = (
        round((first_break_time - end_utc) / pd.Timedelta(minutes=1), 1) if first_break_time is not None else math.nan
    )
    row["first_1r_target_dir"] = target_dir or ""
    row["first_1r_target_min"] = (
        round((target_time - end_utc) / pd.Timedelta(minutes=1), 1) if target_time is not None else math.nan
    )

    max_up_120 = 0.0
    max_down_120 = 0.0
    for horizon in HORIZONS_MIN:
        post = window[(window["timestamp"] > end_utc) & (window["timestamp"] <= end_utc + pd.Timedelta(minutes=horizon))]
        if post.empty:
            for key in [
                f"max_extension_r_{horizon}m",
                f"realized_range_r_{horizon}m",
                f"bb_expand_ratio_{horizon}m",
            ]:
                row[key] = math.nan
            continue

        max_high = float(post["high"].max())
        min_low = float(post["low"].min())
        max_up_pips = max(0.0, (max_high - box_high) / PIP)
        max_down_pips = max(0.0, (box_low - min_low) / PIP)
        max_extension_r = max(max_up_pips, max_down_pips) / box_range_pips if box_range_pips else math.nan
        realized_range_r = ((max_high - min_low) / PIP) / box_range_pips if box_range_pips else math.nan
        bb_expand = float(post["bb_width_pips"].max()) / box_bb_med

        row[f"max_up_r_{horizon}m"] = round(max_up_pips / box_range_pips, 3)
        row[f"max_down_r_{horizon}m"] = round(max_down_pips / box_range_pips, 3)
        row[f"max_extension_r_{horizon}m"] = round(max_extension_r, 3)
        row[f"realized_range_r_{horizon}m"] = round(realized_range_r, 3)
        row[f"bb_expand_ratio_{horizon}m"] = round(bb_expand, 3)
        for target in TARGET_RATIOS:
            row[f"hit_{target:.2f}r_{horizon}m"] = bool(max_extension_r >= target)

        if horizon == 120:
            max_up_120 = max_up_pips
            max_down_120 = max_down_pips

    dominant_dir = "up" if max_up_120 > max_down_120 else "down" if max_down_120 > max_up_120 else ""
    row["dominant_dir_120m"] = dominant_dir
    row["first_break_headfake_120m"] = bool(first_break_dir and dominant_dir and first_break_dir != dominant_dir)
    return row


def overlaps(candidate_start_i: int, candidate_end_i: int, used_spans: list[tuple[int, int]]) -> bool:
    return any(not (candidate_end_i < start_i - 3 or candidate_start_i > end_i + 3) for start_i, end_i in used_spans)


def random_control_for_box(
    window: pd.DataFrame,
    box_bars: int,
    used_spans: list[tuple[int, int]],
    rng: random.Random,
) -> tuple[pd.Timestamp, pd.Timestamp]:
    possible = list(range(0, len(window) - box_bars - 25))
    rng.shuffle(possible)
    for start_i in possible:
        end_i = start_i + box_bars - 1
        chunk = window.iloc[start_i : end_i + 1]
        if overlaps(start_i, end_i, used_spans):
            continue
        if any(in_late_ny_garbage(ts) for ts in chunk["timestamp"]):
            continue
        return chunk.iloc[0]["timestamp"], chunk.iloc[-1]["timestamp"]
    raise RuntimeError("No valid random control found")


def build_metrics(feedback_path: Path, root: Path, out_dir: Path) -> pd.DataFrame:
    feedback = pd.read_csv(feedback_path)
    rows = []
    rng = random.Random(73_001)

    for sample, sample_feedback in feedback.groupby("sample"):
        path = sample_dir(root, int(sample))
        window = pd.read_csv(path / "full_12h_bars.csv", parse_dates=["timestamp", "timestamp_ny"])
        boxes = load_boxes(path)

        used_spans: list[tuple[int, int]] = []
        for _, fb in sample_feedback.iterrows():
            box_num = int(fb["box"])
            match = boxes[boxes["box"] == box_num]
            if match.empty:
                raise ValueError(f"Sample {sample} box {box_num} missing in {path}")
            box = match.iloc[0]
            start_utc = parse_est(str(box["start_new_york"]))
            end_utc = parse_est(str(box["end_new_york"]))
            start_i = int(window.index[window["timestamp"] == start_utc][0])
            end_i = int(window.index[window["timestamp"] == end_utc][0])
            used_spans.append((start_i, end_i))
            rows.append(
                measure_forward(
                    window,
                    start_utc,
                    end_utc,
                    "compression",
                    int(sample),
                    box_num,
                    str(fb["status"]),
                    str(fb["note"]),
                )
            )

        for _, fb in sample_feedback.iterrows():
            if str(fb["status"]) == "rejected":
                continue
            box_num = int(fb["box"])
            match = boxes[boxes["box"] == box_num]
            box = match.iloc[0]
            box_bars = int(box["bars"])
            control_start, control_end = random_control_for_box(window, box_bars, used_spans, rng)
            rows.append(
                measure_forward(
                    window,
                    control_start,
                    control_end,
                    "random_control",
                    int(sample),
                    box_num,
                    str(fb["status"]),
                    "same-window random duration control",
                )
            )

    metrics = pd.DataFrame(rows)
    out_dir.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(out_dir / "expansion_metrics_full_window.csv", index=False)
    return metrics


def summarize(metrics: pd.DataFrame, out_dir: Path) -> pd.DataFrame:
    usable = metrics[metrics["status"].isin(["accepted", "questionable"])].copy()
    summary_rows = []
    for label, group in usable.groupby("label"):
        row = {"label": label, "n": len(group)}
        for horizon in [60, 120]:
            ext = group[f"max_extension_r_{horizon}m"].dropna()
            rr = group[f"realized_range_r_{horizon}m"].dropna()
            bb = group[f"bb_expand_ratio_{horizon}m"].dropna()
            row[f"median_max_extension_r_{horizon}m"] = round(float(ext.median()), 3)
            row[f"hit_1r_rate_{horizon}m"] = round(float((ext >= 1.0).mean()), 3)
            row[f"hit_1_5r_rate_{horizon}m"] = round(float((ext >= 1.5).mean()), 3)
            row[f"median_realized_range_r_{horizon}m"] = round(float(rr.median()), 3)
            row[f"median_bb_expand_ratio_{horizon}m"] = round(float(bb.median()), 3)
        breakable = group[group["first_close_break_dir"] != ""]
        row["first_break_count"] = len(breakable)
        row["headfake_rate_120m"] = round(float(breakable["first_break_headfake_120m"].mean()), 3) if len(breakable) else math.nan
        summary_rows.append(row)

    summary = pd.DataFrame(summary_rows).sort_values("label")
    summary.to_csv(out_dir / "summary.csv", index=False)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--feedback", type=Path, default=Path("compression_expansion_feedback_full_window.csv"))
    parser.add_argument("--root", type=Path, default=Path("training_samples"))
    parser.add_argument("--out-dir", type=Path, default=Path("expansion_audit"))
    args = parser.parse_args()

    metrics = build_metrics(args.feedback, args.root, args.out_dir)
    summary = summarize(metrics, args.out_dir)
    print(summary.to_string(index=False))
    print(args.out_dir / "expansion_metrics_full_window.csv")
    print(args.out_dir / "summary.csv")


if __name__ == "__main__":
    main()
