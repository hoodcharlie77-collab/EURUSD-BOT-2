from __future__ import annotations

import argparse
import math
import random
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw

from forward_test_time_filter_random30 import (
    MIN_TRADE_BOX_BARS,
    STOP_PIPS,
    SPREAD_PIPS,
    resolve_trade,
    target_distance_price,
    time_block,
)
from make_blind_bb_training_sample import NY, PIP, fmt_est, load_5m_bars, load_font, nice_price
from make_full_rule_test_chart import score_candidates


def entry_filter_label(signal_time: pd.Timestamp) -> str:
    hour = signal_time.tz_convert(NY).hour
    if 3 <= hour < 6:
        return "FILTERED 03:00-06:00"
    if 15 <= hour < 17:
        return "FILTERED 15:00-17:00"
    return "PASS"


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
                "box_break_buffer_pips": buffer_price / PIP,
            }
        if close < box_low - buffer_price:
            return {
                "signal_i": int(idx),
                "signal_time": row["timestamp"],
                "direction": "short",
                "entry_price": close,
                "box_break_buffer_pips": buffer_price / PIP,
            }
    return None


def separated(candidate: dict, picked: list[dict], pad_bars: int = 6) -> bool:
    return all(
        candidate["end_i"] < prior["start_i"] - pad_bars or candidate["start_i"] > prior["end_i"] + pad_bars
        for prior in picked
    )


def pick_day_boxes(window: pd.DataFrame, max_boxes: int = 10) -> list[dict]:
    candidates, _, _, _ = score_candidates(window)
    picked: list[dict] = []
    for pool in ([c for c in candidates if c["tier"] == "strong"], candidates):
        for candidate in pool:
            if separated(candidate, picked):
                picked.append(candidate)
                if len(picked) >= max_boxes:
                    break
        if len(picked) >= max_boxes:
            break
    return sorted(picked, key=lambda item: item["start_i"])


def trade_from_box(window: pd.DataFrame, box: dict, trade_id: int) -> dict | None:
    if int(box["bars"]) < MIN_TRADE_BOX_BARS:
        return None
    if box["end_i"] > len(window) - 25:
        return None

    chunk = window.iloc[box["start_i"] : box["end_i"] + 1]
    box_low = float(chunk["low"].min())
    box_high = float(chunk["high"].max())
    r_price = box_high - box_low
    r_pips = r_price / PIP
    if r_pips <= 0:
        return None

    box_end_utc = window.iloc[box["end_i"]]["timestamp"]
    signal = first_close_break(window, box_end_utc, box_high, box_low, r_price)
    if signal is None:
        return None

    entry_price = float(signal["entry_price"])
    stop_offset = STOP_PIPS * PIP
    target_distance = target_distance_price(r_price)
    if signal["direction"] == "long":
        stop_price = entry_price - stop_offset
        target_price = entry_price + target_distance
    else:
        stop_price = entry_price + stop_offset
        target_price = entry_price - target_distance

    resolved = resolve_trade(
        window,
        int(signal["signal_i"]),
        entry_price,
        signal["direction"],
        stop_price,
        target_price,
        box_end_utc,
    )

    after_entry = window[window["timestamp"] > signal["signal_time"]]
    after_exit = window[window["timestamp"] > resolved["exit_time"]] if not pd.isna(resolved["exit_time"]) else after_entry.iloc[0:0]
    up_1r = box_high + r_price
    down_1r = box_low - r_price
    if signal["direction"] == "long":
        same_dir_target_after_exit = bool((after_exit["high"] >= target_price).any())
        opposite_1r_after_entry = bool((after_entry["low"] <= down_1r).any())
    else:
        same_dir_target_after_exit = bool((after_exit["low"] <= target_price).any())
        opposite_1r_after_entry = bool((after_entry["high"] >= up_1r).any())
    any_1r_after_entry = bool((after_entry["high"] >= up_1r).any() or (after_entry["low"] <= down_1r).any())
    if resolved["outcome"] == "target":
        later_1r_note = "target hit"
    elif same_dir_target_after_exit:
        later_1r_note = "same-dir target later"
    elif opposite_1r_after_entry:
        later_1r_note = "opposite 1R later"
    elif any_1r_after_entry:
        later_1r_note = "1R later"
    else:
        later_1r_note = ""

    signal_hour = signal["signal_time"].tz_convert(NY).hour
    return {
        "trade_id": trade_id,
        "box_start_i": int(box["start_i"]),
        "box_end_i": int(box["end_i"]),
        "box_low": box_low,
        "box_high": box_high,
        "box_range_pips": round(r_pips, 2),
        "box_bars": int(box["bars"]),
        "tier": box["tier"],
        "entry_i": int(signal["signal_i"]),
        "entry_time": signal["signal_time"],
        "entry_time_new_york": fmt_est(signal["signal_time"]),
        "entry_hour_new_york": signal_hour,
        "time_block": time_block(signal_hour),
        "entry_filter": entry_filter_label(signal["signal_time"]),
        "direction": signal["direction"],
        "entry_price": entry_price,
        "stop_price": stop_price,
        "target_price": target_price,
        "target_pips": round(target_distance / PIP, 2),
        "exit_time": resolved["exit_time"],
        "exit_time_new_york": fmt_est(resolved["exit_time"]) if not pd.isna(resolved["exit_time"]) else "",
        "exit_price": float(resolved["exit_price"]) if not pd.isna(resolved["exit_price"]) else math.nan,
        "outcome": resolved["outcome"],
        "gross_pips": round(float(resolved["gross_pips"]), 2),
        "net_pips": round(float(resolved["net_pips"]), 2),
        "spread_pips_round_turn": SPREAD_PIPS,
        "same_dir_target_after_exit_same_day": same_dir_target_after_exit,
        "opposite_1r_after_entry_same_day": opposite_1r_after_entry,
        "any_1r_after_entry_same_day": any_1r_after_entry,
        "later_1r_note": later_1r_note,
    }


def find_random_day_with_trades(bars: pd.DataFrame, seed: int, min_trades: int) -> tuple[pd.Timestamp, pd.DataFrame, list[dict]]:
    rng = random.Random(seed)
    first_date = bars.iloc[0]["timestamp_ny"].date()
    last_date = bars.iloc[-1]["timestamp_ny"].date()
    starts = list(pd.date_range(pd.Timestamp(first_date), pd.Timestamp(last_date), freq="D", tz=NY))
    rng.shuffle(starts)

    for day_start_ny in starts:
        day_end_ny = day_start_ny + pd.Timedelta(days=1)
        window = bars[
            (bars["timestamp_ny"] >= day_start_ny) & (bars["timestamp_ny"] < day_end_ny)
        ].copy().reset_index(drop=True)
        if len(window) < 230:
            continue
        max_gap = window["timestamp"].diff().dropna().max()
        if pd.notna(max_gap) and max_gap > pd.Timedelta(minutes=10):
            continue

        trades: list[dict] = []
        for box in pick_day_boxes(window, max_boxes=12):
            trade = trade_from_box(window, box, len(trades) + 1)
            if trade is not None:
                trades.append(trade)
        if len(trades) >= min_trades:
            return day_start_ny, window, trades

    raise RuntimeError(f"No random day found with at least {min_trades} trades")


def draw_chart(window: pd.DataFrame, trades: list[dict], day_start_ny: pd.Timestamp, out_path: Path) -> None:
    width, height = 2400, 1540
    left, right = 120, 2320
    price_top, price_bottom = 120, 930
    table_top = 1060
    axis_color = "#111827"
    grid_color = "#e5e7eb"
    bull = "#147d52"
    bear = "#a13d3d"
    band = "#2f66b3"
    mid = "#6b7280"
    pass_color = "#16803c"
    filter_color = "#c83a2b"
    box_color = "#f2a000"
    stop_color = "#c83a2b"
    target_color = "#16803c"
    time_color = "#6b7280"

    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    title_font = load_font(34, True)
    font = load_font(22)
    small_font = load_font(18)
    label_font = load_font(24, True)
    table_font = load_font(18)

    title = f"EURUSD Random Day Entry/Exit Audit | {day_start_ny:%Y-%m-%d %Z}"
    draw.text((left, 38), title, fill=axis_color, font=title_font)
    draw.text(
        (left, 82),
        "BB(5, 4 std) compression boxes | first breakout close | 10 pip stop | target = max(box R, stop)",
        fill="#374151",
        font=font,
    )

    ymin = min(float(window["low"].min()), float(window["bb_lower"].min()))
    ymax = max(float(window["high"].max()), float(window["bb_upper"].max()))
    pad_y = (ymax - ymin) * 0.12
    ymin -= pad_y
    ymax += pad_y
    n = len(window)
    x_step = (right - left) / max(n - 1, 1)
    candle_w = max(2, min(9, int(x_step * 0.60)))

    def x_at(i: int) -> float:
        return left + i * x_step

    def y_price(value: float) -> float:
        return price_bottom - ((value - ymin) / (ymax - ymin)) * (price_bottom - price_top)

    def index_at_time(ts: pd.Timestamp) -> int | None:
        if pd.isna(ts):
            return None
        matches = window.index[window["timestamp"] == ts]
        if len(matches):
            return int(matches[0])
        diffs = (window["timestamp"] - ts).abs()
        if len(diffs):
            return int(diffs.idxmin())
        return None

    # Entry filter time shading.
    for start_hour, end_hour, color, label in [
        (3, 6, "#fee2e2", "03-06 filtered"),
        (15, 17, "#f3f4f6", "late NY avoid"),
    ]:
        start = day_start_ny + pd.Timedelta(hours=start_hour)
        end = day_start_ny + pd.Timedelta(hours=end_hour)
        mask = (window["timestamp_ny"] >= start) & (window["timestamp_ny"] < end)
        if mask.any():
            x1 = x_at(int(window.index[mask][0]))
            x2 = x_at(int(window.index[mask][-1]))
            draw.rectangle((x1, price_top, x2, price_bottom), fill=color)
            draw.text((x1 + 6, price_top + 8), label, fill="#6b7280", font=small_font)

    for frac in [0, 0.25, 0.5, 0.75, 1.0]:
        y = price_bottom - frac * (price_bottom - price_top)
        price = ymin + frac * (ymax - ymin)
        draw.line((left, y, right, y), fill=grid_color, width=1)
        draw.text((38, y - 11), nice_price(price), fill="#4b5563", font=small_font)

    for hour in range(0, 25, 3):
        ts = day_start_ny + pd.Timedelta(hours=hour)
        mask = window["timestamp_ny"] >= ts
        if not mask.any():
            continue
        i = int(window.index[mask][0])
        x = x_at(i)
        draw.line((x, price_top, x, price_bottom), fill=grid_color, width=1)
        draw.text((x - 25, price_bottom + 16), f"{hour:02d}:00", fill="#4b5563", font=small_font)

    for i, row in window.iterrows():
        x = x_at(i)
        color = bull if row["close"] >= row["open"] else bear
        draw.line((x, y_price(row["low"]), x, y_price(row["high"])), fill=color, width=1)
        body_top = y_price(max(row["open"], row["close"]))
        body_bottom = y_price(min(row["open"], row["close"]))
        if abs(body_bottom - body_top) < 2:
            body_bottom = body_top + 2
        draw.rectangle((x - candle_w / 2, body_top, x + candle_w / 2, body_bottom), fill=color, outline=color)

    def draw_poly(points: list[tuple[float, float]], color: str, width_px: int) -> None:
        clean = [(int(x), int(y)) for x, y in points if math.isfinite(x) and math.isfinite(y)]
        if len(clean) > 1:
            draw.line(clean, fill=color, width=width_px)

    draw_poly([(x_at(i), y_price(row["bb_upper"])) for i, row in window.iterrows()], band, 2)
    draw_poly([(x_at(i), y_price(row["bb_mid"])) for i, row in window.iterrows()], mid, 1)
    draw_poly([(x_at(i), y_price(row["bb_lower"])) for i, row in window.iterrows()], band, 2)

    for trade in trades:
        x1 = x_at(trade["box_start_i"])
        x2 = x_at(trade["box_end_i"])
        y1 = y_price(trade["box_high"] + 0.00003)
        y2 = y_price(trade["box_low"] - 0.00003)
        draw.rectangle((x1, y1, x2, y2), outline=box_color, width=4)
        draw.text((x1 + 3, max(price_top + 4, y1 - 27)), f"B{trade['trade_id']}", fill=axis_color, font=small_font)

        entry_x = x_at(trade["entry_i"])
        entry_y = y_price(trade["entry_price"])
        passed = trade["entry_filter"] == "PASS"
        entry_color = pass_color if passed else filter_color
        direction = trade["direction"]
        if direction == "long":
            pts = [(entry_x, entry_y - 16), (entry_x - 10, entry_y + 10), (entry_x + 10, entry_y + 10)]
        else:
            pts = [(entry_x, entry_y + 16), (entry_x - 10, entry_y - 10), (entry_x + 10, entry_y - 10)]
        draw.polygon(pts, fill=entry_color)
        draw.text((entry_x + 8, entry_y - 32), f"E{trade['trade_id']}", fill=entry_color, font=label_font)

        exit_i = index_at_time(trade["exit_time"])
        if exit_i is not None and math.isfinite(trade["exit_price"]):
            exit_x = x_at(exit_i)
            exit_y = y_price(trade["exit_price"])
            outcome = trade["outcome"]
            out_color = target_color if outcome == "target" else stop_color if outcome == "stop" else time_color
            draw.ellipse((exit_x - 9, exit_y - 9, exit_x + 9, exit_y + 9), fill="white", outline=out_color, width=4)
            label = "T" if outcome == "target" else "S" if outcome == "stop" else "X"
            draw.text((exit_x + 8, exit_y - 28), f"{label}{trade['trade_id']}", fill=out_color, font=label_font)

    draw.rectangle((left, price_top, right, price_bottom), outline="#9ca3af", width=2)

    # Legend.
    legend_y = 970
    draw.rectangle((left, legend_y, left + 28, legend_y + 28), fill=pass_color)
    draw.text((left + 40, legend_y), "entry passes filter", fill=axis_color, font=small_font)
    draw.rectangle((left + 260, legend_y, left + 288, legend_y + 28), fill=filter_color)
    draw.text((left + 300, legend_y), "entry filtered by time window", fill=axis_color, font=small_font)
    draw.rectangle((left + 600, legend_y + 4, left + 640, legend_y + 24), outline=box_color, width=4)
    draw.text((left + 652, legend_y), "compression box", fill=axis_color, font=small_font)
    draw.ellipse((left + 870, legend_y + 5, left + 892, legend_y + 27), outline=target_color, width=4)
    draw.text((left + 902, legend_y), "target", fill=axis_color, font=small_font)
    draw.ellipse((left + 1010, legend_y + 5, left + 1032, legend_y + 27), outline=stop_color, width=4)
    draw.text((left + 1042, legend_y), "stop", fill=axis_color, font=small_font)
    draw.ellipse((left + 1150, legend_y + 5, left + 1172, legend_y + 27), outline=time_color, width=4)
    draw.text((left + 1182, legend_y), "time exit", fill=axis_color, font=small_font)

    # Table.
    headers = ["#", "Filter", "Time ET", "Dir", "Outcome", "Net pips", "Block", "Bars", "Later target"]
    xs = [left, left + 45, left + 245, left + 420, left + 500, left + 645, left + 770, left + 935, left + 1015]
    draw.text((left, table_top - 40), "Trade marks", fill=axis_color, font=label_font)
    for x, header in zip(xs, headers):
        draw.text((x, table_top), header, fill=axis_color, font=small_font)
    draw.line((left, table_top + 30, right, table_top + 30), fill="#9ca3af", width=2)
    for row_i, trade in enumerate(trades[:12]):
        y = table_top + 45 + row_i * 34
        vals = [
            trade["trade_id"],
            trade["entry_filter"],
            trade["entry_time_new_york"][11:17],
            trade["direction"],
            trade["outcome"],
            f"{trade['net_pips']:.1f}",
            trade["time_block"],
            str(trade["box_bars"]),
            trade["later_1r_note"],
        ]
        row_color = filter_color if trade["entry_filter"] != "PASS" else axis_color
        for x, val in zip(xs, vals):
            draw.text((x, y), str(val), fill=row_color, font=table_font)

    image.save(out_path, "JPEG", quality=95, optimize=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=Path("EURUSD_2026.csv"))
    parser.add_argument("--out-dir", type=Path, default=Path("random_day_entry_exit_audit"))
    parser.add_argument("--seed", type=int, default=20260521)
    parser.add_argument("--min-trades", type=int, default=3)
    args = parser.parse_args()

    bars = load_5m_bars(args.data)
    day_start, window, trades = find_random_day_with_trades(bars, args.seed, args.min_trades)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    trades_df = pd.DataFrame(trades)
    trades_path = args.out_dir / "random_day_trades.csv"
    chart_path = args.out_dir / "random_day_entries_exits_filters.jpg"
    summary_path = args.out_dir / "summary.csv"
    trades_df.to_csv(trades_path, index=False)
    pd.DataFrame(
        [
            {
                "data": args.data.name,
                "seed": args.seed,
                "day_start_new_york": fmt_est(day_start),
                "day_end_new_york": fmt_est(day_start + pd.Timedelta(days=1)),
                "trades_marked": len(trades),
                "passes_filter": int((trades_df["entry_filter"] == "PASS").sum()),
                "filtered_entries": int((trades_df["entry_filter"] != "PASS").sum()),
                "pass_net_pips": round(float(trades_df.loc[trades_df["entry_filter"] == "PASS", "net_pips"].sum()), 2),
                "filtered_net_pips": round(float(trades_df.loc[trades_df["entry_filter"] != "PASS", "net_pips"].sum()), 2),
            }
        ]
    ).to_csv(summary_path, index=False)
    draw_chart(window, trades, day_start, chart_path)

    print(chart_path)
    print(pd.read_csv(summary_path).to_string(index=False))
    print(
        trades_df[
            [
                "trade_id",
                "entry_filter",
                "entry_time_new_york",
                "direction",
                "outcome",
                "net_pips",
                "time_block",
                "box_bars",
                "later_1r_note",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
