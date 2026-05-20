from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def breakout_summary(metrics: pd.DataFrame) -> pd.DataFrame:
    usable = metrics[metrics["status"].isin(["accepted", "questionable"])].copy()
    rows = []
    for label, group in usable.groupby("label"):
        breakable = group[group["first_close_break_dir"].fillna("") != ""].copy()
        with_target = breakable[breakable["first_1r_target_dir"].fillna("") != ""].copy()
        same_target = with_target["first_close_break_dir"] == with_target["first_1r_target_dir"]
        opposite_target = with_target["first_close_break_dir"] != with_target["first_1r_target_dir"]
        no_target = breakable["first_1r_target_dir"].fillna("") == ""

        rows.append(
            {
                "label": label,
                "n_total": len(group),
                "n_first_break": len(breakable),
                "first_break_rate": round(len(breakable) / len(group), 3) if len(group) else 0.0,
                "median_first_break_min": round(float(breakable["first_close_break_min"].median()), 1)
                if len(breakable)
                else "",
                "n_first_1r_target": len(with_target),
                "first_1r_target_rate_after_break": round(len(with_target) / len(breakable), 3)
                if len(breakable)
                else 0.0,
                "same_direction_1r_rate_after_break": round(float(same_target.mean()), 3) if len(with_target) else 0.0,
                "opposite_direction_1r_rate_after_break": round(float(opposite_target.mean()), 3) if len(with_target) else 0.0,
                "no_1r_target_after_break_rate": round(float(no_target.mean()), 3) if len(breakable) else 0.0,
                "median_first_1r_target_min": round(float(with_target["first_1r_target_min"].median()), 1)
                if len(with_target)
                else "",
                "headfake_rate_vs_dominant_120m": round(float(breakable["first_break_headfake_120m"].mean()), 3)
                if len(breakable)
                else 0.0,
            }
        )

    return pd.DataFrame(rows).sort_values("label")


def per_box_labels(metrics: pd.DataFrame) -> pd.DataFrame:
    usable = metrics[(metrics["label"] == "compression") & metrics["status"].isin(["accepted", "questionable"])].copy()
    rows = []
    for _, row in usable.iterrows():
        raw_break = row.get("first_close_break_dir", "")
        raw_target = row.get("first_1r_target_dir", "")
        first_break = "" if pd.isna(raw_break) else str(raw_break)
        first_target = "" if pd.isna(raw_target) else str(raw_target)
        if not first_break:
            breakout_result = "no_break"
        elif not first_target:
            breakout_result = "break_no_1r"
        elif first_break == first_target:
            breakout_result = "break_continuation"
        else:
            breakout_result = "headfake"

        rows.append(
            {
                "sample": int(row["sample"]),
                "box": int(row["box"]),
                "status": row["status"],
                "start_new_york": row["start_new_york"],
                "end_new_york": row["end_new_york"],
                "box_range_pips": row["box_range_pips"],
                "first_break_dir": first_break,
                "first_break_min": row["first_close_break_min"],
                "first_1r_target_dir": first_target,
                "first_1r_target_min": row["first_1r_target_min"],
                "max_extension_r_120m": row["max_extension_r_120m"],
                "bb_expand_ratio_120m": row["bb_expand_ratio_120m"],
                "dominant_dir_120m": row["dominant_dir_120m"],
                "breakout_result": breakout_result,
                "note": row["note"],
            }
        )
    return pd.DataFrame(rows).sort_values(["sample", "box"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metrics", type=Path, default=Path("expansion_audit/expansion_metrics_full_window.csv"))
    parser.add_argument("--out-dir", type=Path, default=Path("breakout_audit"))
    args = parser.parse_args()

    metrics = pd.read_csv(args.metrics)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    summary = breakout_summary(metrics)
    labels = per_box_labels(metrics)
    summary.to_csv(args.out_dir / "breakout_v0_summary.csv", index=False)
    labels.to_csv(args.out_dir / "breakout_v0_box_labels.csv", index=False)

    print(summary.to_string(index=False))
    print(args.out_dir / "breakout_v0_summary.csv")
    print(args.out_dir / "breakout_v0_box_labels.csv")


if __name__ == "__main__":
    main()
