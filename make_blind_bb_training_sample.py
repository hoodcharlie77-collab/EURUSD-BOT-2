from __future__ import annotations

import argparse
import math
import random
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from zoneinfo import ZoneInfo


NY = ZoneInfo("America/New_York")
PIP = 0.0001


@dataclass(frozen=True)
class Box:
    start_i: int
    end_i: int
    low: float
    high: float
    bars: int
    duration_min: int
    range_pips: float
    aspect: float
    progress_pips: float
    travel_ratio: float
    bb_width_median: float
    score: float


def load_5m_bars(csv_path: Path) -> pd.DataFrame:
    bars_1m = pd.read_csv(csv_path, parse_dates=["timestamp"])
    bars_1m["timestamp"] = pd.to_datetime(bars_1m["timestamp"], utc=True)
    bars_1m = bars_1m.set_index("timestamp").sort_index()

    bars = bars_1m.resample("5min").agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
    )
    bars = bars.dropna().reset_index()
    bars["timestamp_ny"] = bars["timestamp"].dt.tz_convert(NY)
    bars["bb_mid"] = bars["close"].rolling(5).mean()
    bars["bb_std"] = bars["close"].rolling(5).std(ddof=0)
    bars["bb_upper"] = bars["bb_mid"] + (4.0 * bars["bb_std"])
    bars["bb_lower"] = bars["bb_mid"] - (4.0 * bars["bb_std"])
    bars["bb_width_pips"] = (bars["bb_upper"] - bars["bb_lower"]) / PIP
    return bars.dropna().reset_index(drop=True)


def in_late_ny_garbage(ts: pd.Timestamp) -> bool:
    hour = ts.tz_convert(NY).hour
    return 15 <= hour < 17


def window_candidates(df: pd.DataFrame, min_bars: int, max_bars: int) -> list[Box]:
    candidates: list[Box] = []
    n = len(df)

    for start_i in range(0, n - 5):
        for bars in range(min_bars, max_bars + 1):
            end_i = start_i + bars - 1
            if end_i >= n:
                continue

            chunk = df.iloc[start_i : end_i + 1]
            if any(in_late_ny_garbage(ts) for ts in chunk["timestamp"]):
                continue

            low = float(chunk["low"].min())
            high = float(chunk["high"].max())
            range_pips = (high - low) / PIP
            duration_min = bars * 5
            if not (4.0 <= range_pips <= 13.0):
                continue

            aspect = duration_min / range_pips if range_pips else 0.0
            if aspect < 4.8:
                continue

            progress_pips = abs(float(chunk["close"].iloc[-1] - chunk["open"].iloc[0])) / PIP
            progress_ratio = progress_pips / range_pips if range_pips else 999.0
            if progress_ratio > 0.55:
                continue

            closes = chunk["close"].to_numpy()
            travel_pips = float(abs(pd.Series(closes).diff()).sum()) / PIP
            travel_ratio = travel_pips / range_pips if range_pips else 999.0
            if travel_ratio > 2.8:
                continue

            inner_high = float(chunk["high"].quantile(0.80))
            inner_low = float(chunk["low"].quantile(0.20))
            inner_range = (inner_high - inner_low) / PIP
            overlap_score = max(0.0, (range_pips - inner_range) / range_pips)

            bb_width_median = float(chunk["bb_width_pips"].median())
            bb_width_window_median = float(df["bb_width_pips"].median())
            bb_bonus = max(0.0, min(2.0, (bb_width_window_median - bb_width_median) / 4.0))

            score = (
                aspect
                + (3.0 * (1.0 - progress_ratio))
                + (2.0 * overlap_score)
                + bb_bonus
                - max(0.0, travel_ratio - 1.8)
            )

            candidates.append(
                Box(
                    start_i=start_i,
                    end_i=end_i,
                    low=low,
                    high=high,
                    bars=bars,
                    duration_min=duration_min,
                    range_pips=round(range_pips, 1),
                    aspect=round(aspect, 2),
                    progress_pips=round(progress_pips, 1),
                    travel_ratio=round(travel_ratio, 2),
                    bb_width_median=round(bb_width_median, 2),
                    score=round(score, 2),
                )
            )

    candidates.sort(key=lambda b: b.score, reverse=True)
    return candidates


def is_separate(box: Box, picked: list[Box]) -> bool:
    for prior in picked:
        overlap = not (box.end_i < prior.start_i - 3 or box.start_i > prior.end_i + 3)
        if overlap:
            return False
    return True


def choose_boxes(
    df: pd.DataFrame,
    min_bars: int,
    max_bars: int,
    rng: random.Random,
    selection_mode: str,
) -> list[Box]:
    ranked = window_candidates(df, min_bars, max_bars)
    picked: list[Box] = []

    if selection_mode == "mixed":
        # Avoid training only on obvious winners: take one strong candidate and
        # one mid-ranked candidate, then fill from the top if needed.
        bands = [ranked[:10], ranked[10:40] or ranked[5:25], ranked[:50]]
        for band in bands[:2]:
            shuffled = list(band)
            rng.shuffle(shuffled)
            for box in shuffled:
                if is_separate(box, picked):
                    picked.append(box)
                    break
    elif selection_mode == "borderline":
        # Pull from lower-ranked candidates to pressure-test marginal shelves.
        # This keeps the same hard candidate constraints but avoids only
        # showing the cleanest boxes.
        bands = [
            ranked[35:120] or ranked[15:70] or ranked[:40],
            ranked[120:260] or ranked[50:160] or ranked[20:100] or ranked[:60],
        ]
        for band in bands:
            shuffled = list(band)
            rng.shuffle(shuffled)
            for box in shuffled:
                if is_separate(box, picked):
                    picked.append(box)
                    break

    for box in ranked:
        if is_separate(box, picked):
            picked.append(box)
            if len(picked) == 2:
                break

    return sorted(picked, key=lambda b: b.start_i)


def load_prior_sample_starts(out_root: Path) -> list[pd.Timestamp]:
    starts: list[pd.Timestamp] = []
    if not out_root.exists():
        return starts

    for summary_path in out_root.glob("bb5_x4_5min_12h_sample_*_blind2/summary.csv"):
        try:
            summary = pd.read_csv(summary_path)
        except Exception:
            continue
        if "start_utc" not in summary.columns or summary.empty:
            continue
        starts.append(pd.Timestamp(summary.iloc[0]["start_utc"]))
    return starts


def is_too_close_to_prior(start_utc: pd.Timestamp, prior_starts: list[pd.Timestamp], gap_hours: float) -> bool:
    for prior in prior_starts:
        if abs(start_utc - prior) < pd.Timedelta(hours=gap_hours):
            return True
    return False


def find_sample_window(
    bars: pd.DataFrame,
    sample_id: int,
    min_bars: int,
    max_bars: int,
    selection_mode: str,
    prior_starts: list[pd.Timestamp],
    prior_gap_hours: float,
    range_start: str,
    range_end: str,
) -> tuple[pd.Timestamp, pd.DataFrame, list[Box]]:
    sample_pool = bars[
        (bars["timestamp_ny"] >= pd.Timestamp(range_start, tz=NY))
        & (bars["timestamp_ny"] < pd.Timestamp(range_end, tz=NY))
    ].copy()
    if len(sample_pool) < 144:
        raise RuntimeError(f"Date range {range_start} to {range_end} has fewer than 144 5-minute bars")

    possible_starts = list(sample_pool.iloc[:-144]["timestamp"])
    rng = random.Random(10_000 + sample_id)
    rng.shuffle(possible_starts)

    used_starts = {
        "2024-02-01 02:00:00+00:00",
        "2024-02-01 06:30:00+00:00",
        "2024-02-02 05:00:00+00:00",
        "2024-02-09 08:00:00+00:00",
    }

    for start_utc in possible_starts:
        start_utc = pd.Timestamp(start_utc)
        if str(start_utc) in used_starts:
            continue
        if is_too_close_to_prior(start_utc, prior_starts, prior_gap_hours):
            continue

        end_utc = start_utc + pd.Timedelta(hours=12)
        window = bars[(bars["timestamp"] >= start_utc) & (bars["timestamp"] < end_utc)].copy()
        if len(window) < 130:
            continue

        # Avoid charts that are mostly the dead late-NY window in the visible section.
        start_hour = start_utc.tz_convert(NY).hour
        if start_hour in (13, 14, 15, 16):
            continue

        boxes = choose_boxes(window.reset_index(drop=True), min_bars, max_bars, rng, selection_mode)
        if len(boxes) != 2:
            continue

        if boxes[1].end_i < 30:
            continue

        hidden_after = window.iloc[boxes[1].end_i]["timestamp"]
        visible_hours = (hidden_after - start_utc) / pd.Timedelta(hours=1)
        if 3.0 <= visible_hours <= 8.0:
            return start_utc, window.reset_index(drop=True), boxes

    raise RuntimeError("Could not find a valid blind training window")


def fmt_est(ts: pd.Timestamp) -> str:
    """Format in the New York/Toronto Eastern market clock.

    Keep the legacy name because existing scripts import it, but do not
    hard-code EST. Summer dates must print EDT.
    """
    return ts.tz_convert(NY).strftime("%Y-%m-%d %H:%M %Z")


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def nice_price(value: float) -> str:
    return f"{value:.5f}"


def draw_polyline(draw: ImageDraw.ImageDraw, points: list[tuple[float, float]], fill: str, width: int) -> None:
    clean = [(int(round(x)), int(round(y))) for x, y in points if math.isfinite(x) and math.isfinite(y)]
    if len(clean) >= 2:
        draw.line(clean, fill=fill, width=width, joint="curve")


def plot_chart(window: pd.DataFrame, boxes: list[Box], out_path: Path, sample_id: int) -> pd.DataFrame:
    hidden_i = boxes[1].end_i
    visible = window.iloc[: hidden_i + 1].copy().reset_index(drop=True)

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
    box_color = "#f2a000"

    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    title_font = load_font(28, bold=True)
    font = load_font(20)
    small_font = load_font(17)
    label_font = load_font(24, bold=True)

    draw.text(
        (left, 35),
        f"EURUSD 5-minute Blind Compression Training {sample_id:03d} | BB(5, 4 std) | New York time",
        fill=axis_color,
        font=title_font,
    )
    draw.text((right - 300, price_bottom - 34), "Future hidden after Box 2", fill="#374151", font=small_font)

    ymin = min(float(visible["low"].min()), float(visible["bb_lower"].min()))
    ymax = max(float(visible["high"].max()), float(visible["bb_upper"].max()))
    pad_y = (ymax - ymin) * 0.13
    ymin -= pad_y
    ymax += pad_y

    n = len(visible)
    x_step = (right - left) / max(n - 1, 1)
    candle_w = max(7, min(24, int(x_step * 0.62)))

    def x_at(i: int) -> float:
        return left + (i * x_step)

    def y_price(value: float) -> float:
        return price_bottom - ((value - ymin) / (ymax - ymin)) * (price_bottom - price_top)

    max_width = max(1.0, float(visible["bb_width_pips"].max()) * 1.15)

    def y_width(value: float) -> float:
        return width_bottom - (value / max_width) * (width_bottom - width_top)

    for frac in [0.0, 0.25, 0.5, 0.75, 1.0]:
        y = price_bottom - frac * (price_bottom - price_top)
        price = ymin + frac * (ymax - ymin)
        draw.line((left, y, right, y), fill=grid_color, width=1)
        draw.text((38, y - 11), nice_price(price), fill="#4b5563", font=small_font)

    for frac in [0.0, 0.5, 1.0]:
        y = width_bottom - frac * (width_bottom - width_top)
        val = frac * max_width
        draw.line((left, y, right, y), fill=grid_color, width=1)
        draw.text((55, y - 11), f"{val:.1f}", fill="#4b5563", font=small_font)

    tick_count = min(7, max(3, n // 10))
    tick_indices = sorted({round(i * (n - 1) / max(tick_count - 1, 1)) for i in range(tick_count)})
    for i in tick_indices:
        x = x_at(i)
        draw.line((x, price_top, x, price_bottom), fill=grid_color, width=1)
        draw.line((x, width_top, x, width_bottom), fill=grid_color, width=1)
        ts = visible.iloc[i]["timestamp"].tz_convert(NY)
        draw.text((x - 35, width_bottom + 15), ts.strftime("%b %d\n%H:%M"), fill="#4b5563", font=small_font, align="center")

    for i, row in visible.iterrows():
        x = x_at(i)
        color = bull if row["close"] >= row["open"] else bear
        draw.line((x, y_price(row["low"]), x, y_price(row["high"])), fill=color, width=2)
        body_top = y_price(max(row["open"], row["close"]))
        body_bottom = y_price(min(row["open"], row["close"]))
        if abs(body_bottom - body_top) < 3:
            body_bottom = body_top + 3
        draw.rectangle(
            (x - candle_w / 2, body_top, x + candle_w / 2, body_bottom),
            fill=color,
            outline=color,
            width=1,
        )

    draw_polyline(draw, [(x_at(i), y_price(row["bb_upper"])) for i, row in visible.iterrows()], band, 3)
    draw_polyline(draw, [(x_at(i), y_price(row["bb_mid"])) for i, row in visible.iterrows()], mid, 2)
    draw_polyline(draw, [(x_at(i), y_price(row["bb_lower"])) for i, row in visible.iterrows()], band, 3)

    width_points = [(x_at(i), y_width(row["bb_width_pips"])) for i, row in visible.iterrows()]
    if len(width_points) >= 2:
        fill_points = [(left, width_bottom)] + width_points + [(x_at(n - 1), width_bottom)]
        draw.polygon([(int(x), int(y)) for x, y in fill_points], fill="#e5e7eb")
    draw_polyline(draw, width_points, "#4b5563", 3)

    for idx, box in enumerate(boxes, start=1):
        x1 = x_at(box.start_i) - candle_w * 0.75
        x2 = x_at(box.end_i) + candle_w * 0.75
        pad = 0.000035
        y1 = y_price(box.high + pad)
        y2 = y_price(box.low - pad)
        draw.rectangle((x1, y1, x2, y2), outline=box_color, width=6)

        label_x = x1
        label_y = max(price_top + 5, y1 - 34)
        draw.rectangle((label_x, label_y, label_x + 34, label_y + 30), fill="white", outline=box_color, width=3)
        draw.text((label_x + 10, label_y + 1), str(idx), fill=axis_color, font=label_font)

        draw.rectangle((x1, width_top, x2, width_bottom), outline=box_color, width=4)

    draw.rectangle((left, price_top, right, price_bottom), outline="#9ca3af", width=2)
    draw.rectangle((left, width_top, right, width_bottom), outline="#9ca3af", width=2)
    draw.text((20, 430), "Price", fill=axis_color, font=font)
    draw.text((18, 1005), "BB width\n(pips)", fill=axis_color, font=small_font)
    draw.line((left + 20, 75, left + 90, 75), fill=band, width=4)
    draw.text((left + 100, 63), "BB upper/lower", fill="#374151", font=small_font)
    draw.line((left + 270, 75, left + 340, 75), fill=mid, width=3)
    draw.text((left + 350, 63), "BB mid", fill="#374151", font=small_font)

    image.save(out_path, "JPEG", quality=95, optimize=True)
    return visible


def write_outputs(out_dir: Path, sample_id: int, start_utc: pd.Timestamp, window: pd.DataFrame, boxes: list[Box]) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    chart_path = out_dir / "blind_two_boxes_outline_only_hidden_after_box2.jpg"
    visible = plot_chart(window, boxes, chart_path, sample_id)

    visible.to_csv(out_dir / "visible_bars_until_box2.csv", index=False)
    window.to_csv(out_dir / "full_12h_bars_hidden_future.csv", index=False)

    box_rows = []
    for idx, box in enumerate(boxes, start=1):
        box_rows.append(
            {
                "box": idx,
                "start_new_york": fmt_est(window.iloc[box.start_i]["timestamp"]),
                "end_new_york": fmt_est(window.iloc[box.end_i]["timestamp"]),
                "low": round(box.low, 5),
                "high": round(box.high, 5),
                "bars": box.bars,
                "duration_min": box.duration_min,
                "range_pips": box.range_pips,
                "aspect_min_per_pip": box.aspect,
                "progress_pips": box.progress_pips,
                "travel_ratio": box.travel_ratio,
                "bb_width_median": box.bb_width_median,
                "score": box.score,
            }
        )
    pd.DataFrame(box_rows).to_csv(out_dir / "boxes_1_2.csv", index=False)

    hidden_after = window.iloc[boxes[1].end_i]["timestamp"]
    summary = pd.DataFrame(
        [
            {
                "sample": f"{sample_id:03d}_blind2",
                "start_utc": str(start_utc),
                "end_utc": str(start_utc + pd.Timedelta(hours=12)),
                "start_new_york": fmt_est(start_utc),
                "hidden_after_new_york": fmt_est(hidden_after),
                "visible_candles": len(visible),
                "full_12h_candles": len(window),
            }
        ]
    )
    summary.to_csv(out_dir / "summary.csv", index=False)
    return chart_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample-id", type=int, required=True)
    parser.add_argument("--data", type=Path, default=Path("EURUSD_2024.csv"))
    parser.add_argument("--out-root", type=Path, default=Path("training_samples"))
    parser.add_argument("--min-bars", type=int, default=6, help="Minimum box width in 5-minute candles")
    parser.add_argument("--max-bars", type=int, default=16, help="Maximum box width in 5-minute candles")
    parser.add_argument("--range-start", default="2024-02-01", help="New York date/time start for sample pool")
    parser.add_argument("--range-end", default="2024-03-01", help="New York date/time end for sample pool")
    parser.add_argument("--prior-gap-hours", type=float, default=8.0, help="Minimum gap from prior blind sample starts")
    parser.add_argument(
        "--allow-near-prior",
        action="store_true",
        help="Allow samples within 8 hours of prior generated blind samples",
    )
    parser.add_argument(
        "--selection-mode",
        choices=["best", "mixed", "borderline"],
        default="mixed",
        help="best picks the top boxes; mixed adds one mid-ranked candidate; borderline samples lower-ranked valid candidates",
    )
    args = parser.parse_args()

    bars = load_5m_bars(args.data)
    prior_starts = [] if args.allow_near_prior else load_prior_sample_starts(args.out_root)
    start_utc, window, boxes = find_sample_window(
        bars,
        args.sample_id,
        args.min_bars,
        args.max_bars,
        args.selection_mode,
        prior_starts,
        args.prior_gap_hours,
        args.range_start,
        args.range_end,
    )
    out_dir = args.out_root / f"bb5_x4_5min_12h_sample_{args.sample_id:03d}_blind2"
    chart_path = write_outputs(out_dir, args.sample_id, start_utc, window, boxes)
    print(chart_path)


if __name__ == "__main__":
    main()
