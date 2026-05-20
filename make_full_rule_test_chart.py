from __future__ import annotations

import argparse
import random
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw

from make_blind_bb_training_sample import (
    NY,
    PIP,
    draw_polyline,
    in_late_ny_garbage,
    load_5m_bars,
    load_font,
    nice_price,
)


def score_candidates(window: pd.DataFrame) -> tuple[list[dict], float, float, float]:
    local_median_bb = float(window["bb_width_pips"].median())
    local_q25_bb = float(window["bb_width_pips"].quantile(0.25))
    local_q75_bb = float(window["bb_width_pips"].quantile(0.75))
    candidates: list[dict] = []
    n = len(window)

    for start_i in range(0, n - 3):
        for bars_count in range(4, 13):
            end_i = start_i + bars_count - 1
            if end_i >= n:
                continue

            chunk = window.iloc[start_i : end_i + 1]
            if any(in_late_ny_garbage(ts) for ts in chunk["timestamp"]):
                continue

            low = float(chunk["low"].min())
            high = float(chunk["high"].max())
            range_pips = (high - low) / PIP
            if range_pips < 3.5:
                continue

            max_range = max(13.0, min(18.0, local_q75_bb * 0.75))
            if range_pips > max_range:
                continue

            duration_min = bars_count * 5
            aspect = duration_min / range_pips if range_pips else 0.0
            progress_pips = abs(float(chunk["close"].iloc[-1] - chunk["open"].iloc[0])) / PIP
            progress_ratio = progress_pips / range_pips if range_pips else 999.0
            travel_pips = float(abs(chunk["close"].astype(float).diff()).sum()) / PIP
            travel_ratio = travel_pips / range_pips if range_pips else 999.0
            bb_med = float(chunk["bb_width_pips"].median())
            bb_start = float(chunk["bb_width_pips"].iloc[0])
            bb_end = float(chunk["bb_width_pips"].iloc[-1])
            contraction = bb_end <= bb_start * 0.9 or bb_med <= local_q25_bb * 1.15
            prior = window.iloc[max(0, start_i - 6) : start_i]
            if len(prior) >= 4:
                prior_travel_pips = float(abs(prior["close"].astype(float).diff()).sum()) / PIP
                prior_quiet_enough = prior_travel_pips <= range_pips * 1.5
            else:
                prior_quiet_enough = True

            normal_rect = aspect >= 4.8 and progress_ratio <= 0.55 and travel_ratio <= 2.8
            short_clean = (
                bars_count <= 6
                and range_pips <= 13.0
                and aspect >= 2.3
                and progress_ratio <= 0.25
                and travel_ratio <= 1.15
                and contraction
                and prior_quiet_enough
            )
            if not (normal_rect or short_clean):
                continue

            inner_high = float(chunk["high"].quantile(0.80))
            inner_low = float(chunk["low"].quantile(0.20))
            inner_range = (inner_high - inner_low) / PIP
            overlap = max(0.0, (range_pips - inner_range) / range_pips)
            bb_bonus = max(0.0, min(2.0, (local_median_bb - bb_med) / 4.0))
            contraction_bonus = 1.0 if contraction else 0.0
            short_penalty = 0.8 if bars_count < 6 else 0.0
            score = (
                aspect
                + 3.0 * (1.0 - progress_ratio)
                + 2.0 * overlap
                + bb_bonus
                + contraction_bonus
                - max(0.0, travel_ratio - 1.8)
                - short_penalty
            )
            tier = "strong" if (
                normal_rect
                and progress_ratio <= 0.35
                and travel_ratio <= 2.2
                and (bb_med <= local_median_bb or contraction)
            ) else "marginal"

            candidates.append(
                {
                    "start_i": start_i,
                    "end_i": end_i,
                    "low": low,
                    "high": high,
                    "bars": bars_count,
                    "duration_min": duration_min,
                    "range_pips": round(range_pips, 1),
                    "aspect": round(aspect, 2),
                    "progress_pips": round(progress_pips, 1),
                    "progress_ratio": round(progress_ratio, 2),
                    "travel_ratio": round(travel_ratio, 2),
                    "bb_width_median": round(bb_med, 2),
                    "score": round(score, 2),
                    "tier": tier,
                }
            )

    candidates.sort(key=lambda item: item["score"], reverse=True)
    return candidates, local_median_bb, local_q25_bb, local_q75_bb


def separate(candidate: dict, picked: list[dict]) -> bool:
    return all(
        candidate["end_i"] < prior["start_i"] - 3 or candidate["start_i"] > prior["end_i"] + 3
        for prior in picked
    )


def pick_boxes(candidates: list[dict], max_boxes: int) -> list[dict]:
    picked: list[dict] = []
    for pool in ([c for c in candidates if c["tier"] == "strong"], candidates):
        for candidate in pool:
            if separate(candidate, picked):
                picked.append(candidate)
                if len(picked) == max_boxes:
                    break
        if len(picked) == max_boxes:
            break
    return sorted(picked, key=lambda item: item["start_i"])


def draw_chart(
    window: pd.DataFrame,
    picked: list[dict],
    out_path: Path,
    sample_id: int,
) -> None:
    n = len(window)
    width, height = 2200, 1300
    left, right = 120, 2140
    price_top, price_bottom = 105, 850
    width_top, width_bottom = 950, 1145
    axis_color = "#111827"
    grid_color = "#e5e7eb"
    bull = "#147d52"
    bear = "#a13d3d"
    band = "#2f66b3"
    mid = "#6b7280"
    strong_color = "#f2a000"
    marginal_color = "#6b7280"

    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    title_font = load_font(28, True)
    font = load_font(20)
    small_font = load_font(17)
    label_font = load_font(24, True)

    start_ny = window.iloc[0]["timestamp"].tz_convert(NY)
    end_ny = window.iloc[-1]["timestamp"].tz_convert(NY)
    draw.text(
        (left, 35),
        f"EURUSD 12-hour Rule Test {sample_id:03d} | 5-minute | BB(5, 4 std) | New York time",
        fill=axis_color,
        font=title_font,
    )
    draw.text(
        (right - 560, price_bottom - 34),
        f"{start_ny:%b %d %H:%M} to {end_ny:%b %d %H:%M} EST | full window visible",
        fill="#374151",
        font=small_font,
    )

    ymin = min(float(window["low"].min()), float(window["bb_lower"].min()))
    ymax = max(float(window["high"].max()), float(window["bb_upper"].max()))
    pad_y = (ymax - ymin) * 0.13
    ymin -= pad_y
    ymax += pad_y
    x_step = (right - left) / max(n - 1, 1)
    candle_w = max(3, min(12, int(x_step * 0.62)))

    def x_at(i: int) -> float:
        return left + i * x_step

    def y_price(value: float) -> float:
        return price_bottom - ((value - ymin) / (ymax - ymin)) * (price_bottom - price_top)

    max_width = max(1.0, float(window["bb_width_pips"].max()) * 1.15)

    def y_width(value: float) -> float:
        return width_bottom - (value / max_width) * (width_bottom - width_top)

    for frac in [0.0, 0.25, 0.5, 0.75, 1.0]:
        y = price_bottom - frac * (price_bottom - price_top)
        price = ymin + frac * (ymax - ymin)
        draw.line((left, y, right, y), fill=grid_color, width=1)
        draw.text((38, y - 11), nice_price(price), fill="#4b5563", font=small_font)

    for frac in [0.0, 0.5, 1.0]:
        y = width_bottom - frac * (width_bottom - width_top)
        draw.line((left, y, right, y), fill=grid_color, width=1)
        draw.text((55, y - 11), f"{frac * max_width:.1f}", fill="#4b5563", font=small_font)

    for i in sorted({round(j * (n - 1) / 7) for j in range(8)}):
        x = x_at(i)
        ts = window.iloc[i]["timestamp"].tz_convert(NY)
        draw.line((x, price_top, x, price_bottom), fill=grid_color, width=1)
        draw.line((x, width_top, x, width_bottom), fill=grid_color, width=1)
        draw.text(
            (x - 35, width_bottom + 15),
            ts.strftime("%b %d\n%H:%M"),
            fill="#4b5563",
            font=small_font,
            align="center",
        )

    for i, row in window.iterrows():
        x = x_at(i)
        color = bull if row["close"] >= row["open"] else bear
        draw.line((x, y_price(row["low"]), x, y_price(row["high"])), fill=color, width=2)
        body_top = y_price(max(row["open"], row["close"]))
        body_bottom = y_price(min(row["open"], row["close"]))
        if abs(body_bottom - body_top) < 2:
            body_bottom = body_top + 2
        draw.rectangle(
            (x - candle_w / 2, body_top, x + candle_w / 2, body_bottom),
            fill=color,
            outline=color,
            width=1,
        )

    draw_polyline(draw, [(x_at(i), y_price(row["bb_upper"])) for i, row in window.iterrows()], band, 3)
    draw_polyline(draw, [(x_at(i), y_price(row["bb_mid"])) for i, row in window.iterrows()], mid, 2)
    draw_polyline(draw, [(x_at(i), y_price(row["bb_lower"])) for i, row in window.iterrows()], band, 3)

    width_points = [(x_at(i), y_width(row["bb_width_pips"])) for i, row in window.iterrows()]
    draw.polygon(
        [(int(x), int(y)) for x, y in [(left, width_bottom)] + width_points + [(x_at(n - 1), width_bottom)]],
        fill="#e5e7eb",
    )
    draw_polyline(draw, width_points, "#4b5563", 3)

    for idx, candidate in enumerate(picked, 1):
        color = strong_color if candidate["tier"] == "strong" else marginal_color
        x1 = x_at(candidate["start_i"]) - candle_w * 0.75
        x2 = x_at(candidate["end_i"]) + candle_w * 0.75
        y1 = y_price(candidate["high"] + 0.000035)
        y2 = y_price(candidate["low"] - 0.000035)
        draw.rectangle((x1, y1, x2, y2), outline=color, width=6)
        label_y = max(price_top + 5, y1 - 34)
        draw.rectangle((x1, label_y, x1 + 34, label_y + 30), fill="white", outline=color, width=3)
        draw.text((x1 + 10, label_y + 1), str(idx), fill=axis_color, font=label_font)
        draw.rectangle((x1, width_top, x2, width_bottom), outline=color, width=4)

    draw.rectangle((left, price_top, right, price_bottom), outline="#9ca3af", width=2)
    draw.rectangle((left, width_top, right, width_bottom), outline="#9ca3af", width=2)
    draw.text((20, 430), "Price", fill=axis_color, font=font)
    draw.text((18, 1005), "BB width\n(pips)", fill=axis_color, font=small_font)
    draw.line((left + 20, 75, left + 90, 75), fill=band, width=4)
    draw.text((left + 100, 63), "BB upper/lower", fill="#374151", font=small_font)
    draw.line((left + 270, 75, left + 340, 75), fill=mid, width=3)
    draw.text((left + 350, 63), "BB mid", fill="#374151", font=small_font)
    draw.rectangle((left + 520, 61, left + 590, 81), outline=strong_color, width=4)
    draw.text((left + 602, 63), "strong compression", fill="#374151", font=small_font)
    draw.rectangle((left + 800, 61, left + 870, 81), outline=marginal_color, width=4)
    draw.text((left + 882, 63), "marginal compression", fill="#374151", font=small_font)

    image.save(out_path, "JPEG", quality=95, optimize=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample-id", type=int, required=True)
    parser.add_argument("--out-root", type=Path, default=Path("training_samples"))
    parser.add_argument("--max-boxes", type=int, default=4)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--data", type=Path)
    parser.add_argument("--range-start")
    parser.add_argument("--range-end")
    args = parser.parse_args()

    rng = random.Random(args.seed if args.seed is not None else 50_000 + args.sample_id)
    if args.data:
        data_files = [args.data]
    else:
        data_files = [Path(f"EURUSD_{year}.csv") for year in [2021, 2022, 2023, 2024, 2025]]
        data_files = [path for path in data_files if path.exists()]
    chosen_data = rng.choice(data_files)
    bars = load_5m_bars(chosen_data)

    if args.range_start and args.range_end:
        mask = (bars["timestamp_ny"] >= pd.Timestamp(args.range_start, tz=NY)) & (
            bars["timestamp_ny"] < pd.Timestamp(args.range_end, tz=NY)
        )
        source = bars[mask].copy().reset_index(drop=True)
    else:
        source = bars

    possible = list(range(0, max(len(source) - 1, 0), 12))
    rng.shuffle(possible)
    selected = None
    for start_i in possible[:900]:
        start_ts = source.iloc[start_i]["timestamp"]
        start_ny = start_ts.tz_convert(NY)
        if start_ny.hour in (13, 14, 15, 16):
            continue
        end_ts = start_ts + pd.Timedelta(hours=12)
        window = source[(source["timestamp"] >= start_ts) & (source["timestamp"] < end_ts)].copy().reset_index(drop=True)
        if len(window) < 130:
            continue
        actual_span = window.iloc[-1]["timestamp"] - window.iloc[0]["timestamp"]
        if actual_span > pd.Timedelta(hours=12) or actual_span < pd.Timedelta(hours=10, minutes=45):
            continue
        max_gap = window["timestamp"].diff().dropna().max()
        if pd.notna(max_gap) and max_gap > pd.Timedelta(minutes=10):
            continue
        late_count = sum(15 <= ts.tz_convert(NY).hour < 17 for ts in window["timestamp"])
        if late_count > 36:
            continue
        candidates, med, q25, q75 = score_candidates(window)
        if len(candidates) < args.max_boxes:
            continue
        picked = pick_boxes(candidates, args.max_boxes)
        if len(picked) >= 2:
            selected = (window, picked, candidates, med, q25, q75)
            break

    if selected is None:
        raise RuntimeError("No rule-test window found")

    window, picked, candidates, med, q25, q75 = selected
    out_dir = args.out_root / f"bb5_x4_5min_12h_rule_test_{args.sample_id:03d}"
    out_dir.mkdir(parents=True, exist_ok=True)
    chart_path = out_dir / "full_12h_rule_boxes.jpg"
    draw_chart(window, picked, chart_path, args.sample_id)

    box_rows = []
    for idx, candidate in enumerate(picked, 1):
        row = {
            "box": idx,
            "tier": candidate["tier"],
            "start_new_york": window.iloc[candidate["start_i"]]["timestamp"].tz_convert(NY).strftime("%Y-%m-%d %H:%M EST"),
            "end_new_york": window.iloc[candidate["end_i"]]["timestamp"].tz_convert(NY).strftime("%Y-%m-%d %H:%M EST"),
        }
        for key in [
            "bars",
            "duration_min",
            "range_pips",
            "aspect",
            "progress_pips",
            "progress_ratio",
            "travel_ratio",
            "bb_width_median",
            "score",
        ]:
            row[key] = candidate[key]
        box_rows.append(row)

    pd.DataFrame(box_rows).to_csv(out_dir / "rule_boxes.csv", index=False)
    window.to_csv(out_dir / "full_12h_bars.csv", index=False)
    pd.DataFrame(
        [
            {
                "sample": args.sample_id,
                "data": str(chosen_data),
                "start_new_york": window.iloc[0]["timestamp"].tz_convert(NY).strftime("%Y-%m-%d %H:%M EST"),
                "end_new_york": window.iloc[-1]["timestamp"].tz_convert(NY).strftime("%Y-%m-%d %H:%M EST"),
                "local_median_bb_width_pips": round(med, 2),
                "local_q25_bb_width_pips": round(q25, 2),
                "local_q75_bb_width_pips": round(q75, 2),
                "candidate_count": len(candidates),
                "picked_count": len(picked),
            }
        ]
    ).to_csv(out_dir / "summary.csv", index=False)

    print(chart_path)
    print(pd.DataFrame(box_rows).to_string(index=False))


if __name__ == "__main__":
    main()
