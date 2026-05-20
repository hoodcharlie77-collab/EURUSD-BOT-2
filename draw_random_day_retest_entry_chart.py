from __future__ import annotations

import argparse
import math
import random
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw

from forward_test_time_filter_random30 import MIN_TRADE_BOX_BARS, STOP_PIPS, SPREAD_PIPS, resolve_trade, time_block
from make_blind_bb_training_sample import NY, PIP, fmt_est, load_5m_bars, load_font, nice_price
from make_full_rule_test_chart import score_candidates


ORDER_TIMEOUT_MIN = 120


def entry_filter_label(ts: pd.Timestamp) -> str:
    hour = ts.tz_convert(NY).hour
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
            return {"signal_i": int(idx), "signal_time": row["timestamp"], "direction": "long"}
        if close < box_low - buffer_price:
            return {"signal_i": int(idx), "signal_time": row["timestamp"], "direction": "short"}
    return None


def separated(candidate: dict, picked: list[dict], pad_bars: int = 6) -> bool:
    return all(
        candidate["end_i"] < prior["start_i"] - pad_bars or candidate["start_i"] > prior["end_i"] + pad_bars
        for prior in picked
    )


def pick_day_boxes(window: pd.DataFrame, max_boxes: int = 10) -> list[dict]:
    candidates, _, _, _ = score_candidates(window)
    candidates = [candidate for candidate in candidates if int(candidate["bars"]) >= MIN_TRADE_BOX_BARS]
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


def find_limit_fill(
    window: pd.DataFrame,
    signal_i: int,
    signal_time: pd.Timestamp,
    direction: str,
    entry_price: float,
) -> tuple[int, pd.Timestamp] | None:
    deadline = signal_time + pd.Timedelta(minutes=ORDER_TIMEOUT_MIN)
    post = window[(window.index > signal_i) & (window["timestamp"] <= deadline)].copy()
    for idx, row in post.iterrows():
        if direction == "long" and float(row["low"]) <= entry_price:
            return int(idx), row["timestamp"]
        if direction == "short" and float(row["high"]) >= entry_price:
            return int(idx), row["timestamp"]
    return None


def trade_variant(
    window: pd.DataFrame,
    box: dict,
    box_num: int,
    variant: str,
    signal: dict,
    box_low: float,
    box_high: float,
    r_price: float,
) -> dict:
    direction = signal["direction"]
    box_mid = (box_high + box_low) / 2.0
    if direction == "long":
        entry_price = box_mid if variant == "mid" else box_low
    else:
        entry_price = box_mid if variant == "mid" else box_high

    fill = find_limit_fill(window, int(signal["signal_i"]), signal["signal_time"], direction, entry_price)
    base = {
        "box": box_num,
        "variant": variant,
        "direction": direction,
        "box_start_i": int(box["start_i"]),
        "box_end_i": int(box["end_i"]),
        "box_low": box_low,
        "box_high": box_high,
        "box_mid": box_mid,
        "box_bars": int(box["bars"]),
        "box_range_pips": round(r_price / PIP, 2),
        "signal_i": int(signal["signal_i"]),
        "signal_time": signal["signal_time"],
        "signal_time_new_york": fmt_est(signal["signal_time"]),
        "entry_price": entry_price,
    }
    if fill is None:
        return {
            **base,
            "trade_status": "not_filled",
            "entry_filter": "",
            "entry_i": math.nan,
            "entry_time": pd.NaT,
            "entry_time_new_york": "",
            "time_block": "",
            "stop_price": math.nan,
            "target_price": math.nan,
            "outcome": "not_filled",
            "exit_time": pd.NaT,
            "exit_time_new_york": "",
            "exit_price": math.nan,
            "gross_pips": 0.0,
            "net_pips": 0.0,
        }

    entry_i, entry_time = fill
    if direction == "long":
        stop_price = entry_price - STOP_PIPS * PIP
        target_price = entry_price + r_price
    else:
        stop_price = entry_price + STOP_PIPS * PIP
        target_price = entry_price - r_price

    resolved = resolve_trade(window, entry_i, entry_price, direction, stop_price, target_price, entry_time)
    return {
        **base,
        "trade_status": "filled",
        "entry_filter": entry_filter_label(entry_time),
        "entry_i": entry_i,
        "entry_time": entry_time,
        "entry_time_new_york": fmt_est(entry_time),
        "time_block": time_block(entry_time.tz_convert(NY).hour),
        "stop_price": stop_price,
        "target_price": target_price,
        "outcome": resolved["outcome"],
        "exit_time": resolved["exit_time"],
        "exit_time_new_york": fmt_est(resolved["exit_time"]) if not pd.isna(resolved["exit_time"]) else "",
        "exit_price": float(resolved["exit_price"]) if not pd.isna(resolved["exit_price"]) else math.nan,
        "gross_pips": round(float(resolved["gross_pips"]), 2),
        "net_pips": round(float(resolved["net_pips"]), 2),
    }


def trades_for_day(window: pd.DataFrame) -> list[dict]:
    rows: list[dict] = []
    for box_num, box in enumerate(pick_day_boxes(window, max_boxes=10), 1):
        chunk = window.iloc[box["start_i"] : box["end_i"] + 1]
        box_low = float(chunk["low"].min())
        box_high = float(chunk["high"].max())
        r_price = box_high - box_low
        if r_price <= 0:
            continue
        signal = first_close_break(window, window.iloc[box["end_i"]]["timestamp"], box_high, box_low, r_price)
        if signal is None:
            continue
        for variant in ["mid", "edge"]:
            rows.append(trade_variant(window, box, box_num, variant, signal, box_low, box_high, r_price))
    return rows


def find_random_day(bars: pd.DataFrame, seed: int, min_filled: int) -> tuple[pd.Timestamp, pd.DataFrame, list[dict]]:
    rng = random.Random(seed)
    first_date = bars.iloc[0]["timestamp_ny"].date()
    last_date = bars.iloc[-1]["timestamp_ny"].date()
    starts = list(pd.date_range(pd.Timestamp(first_date), pd.Timestamp(last_date), freq="D", tz=NY))
    rng.shuffle(starts)

    for day_start in starts:
        day_end = day_start + pd.Timedelta(days=1)
        window = bars[(bars["timestamp_ny"] >= day_start) & (bars["timestamp_ny"] < day_end)].copy().reset_index(drop=True)
        if len(window) < 230:
            continue
        max_gap = window["timestamp"].diff().dropna().max()
        if pd.notna(max_gap) and max_gap > pd.Timedelta(minutes=10):
            continue
        rows = trades_for_day(window)
        if sum(row["trade_status"] == "filled" for row in rows) >= min_filled:
            return day_start, window, rows

    raise RuntimeError(f"No random day found with at least {min_filled} filled retest entries")


def draw_chart(window: pd.DataFrame, rows: list[dict], day_start_ny: pd.Timestamp, out_path: Path) -> None:
    width, height = 2400, 1540
    left, right = 120, 2320
    price_top, price_bottom = 120, 930
    table_top = 1060
    axis_color = "#111827"
    grid_color = "#e5e7eb"
    bull = "#147d52"
    bear = "#a13d3d"
    band = "#2f66b3"
    mid_color = "#6b7280"
    box_color = "#f2a000"
    green = "#16803c"
    red = "#c83a2b"
    gray = "#6b7280"
    purple = "#7c3aed"

    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    title_font = load_font(34, True)
    font = load_font(22)
    small_font = load_font(18)
    label_font = load_font(24, True)
    table_font = load_font(18)

    draw.text((left, 38), f"EURUSD Retest Entry Audit | {day_start_ny:%Y-%m-%d %Z}", fill=axis_color, font=title_font)
    draw.text(
        (left, 82),
        "After breakout: short limits at box mid/high, long limits at box mid/low | 10 pip stop | 1R target",
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
        return int(diffs.idxmin()) if len(diffs) else None

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
    draw_poly([(x_at(i), y_price(row["bb_mid"])) for i, row in window.iterrows()], mid_color, 1)
    draw_poly([(x_at(i), y_price(row["bb_lower"])) for i, row in window.iterrows()], band, 2)

    seen_boxes = set()
    for row in rows:
        box_key = row["box"]
        if box_key not in seen_boxes:
            seen_boxes.add(box_key)
            x1 = x_at(row["box_start_i"])
            x2 = x_at(row["box_end_i"])
            draw.rectangle((x1, y_price(row["box_high"]), x2, y_price(row["box_low"])), outline=box_color, width=4)
            draw.line((x1, y_price(row["box_mid"]), x2, y_price(row["box_mid"])), fill=purple, width=2)
            draw.text((x1 + 3, max(price_top + 4, y_price(row["box_high"]) - 27)), f"B{box_key}", fill=axis_color, font=small_font)
            sig_x = x_at(row["signal_i"])
            sig_y = y_price(row["box_low"] if row["direction"] == "short" else row["box_high"])
            draw.text((sig_x + 4, sig_y - 24), "break", fill=purple, font=small_font)

        if row["trade_status"] != "filled":
            continue
        entry_x = x_at(int(row["entry_i"]))
        entry_y = y_price(row["entry_price"])
        entry_color = red if row["entry_filter"] != "PASS" else green
        label = f"{row['box']}{'M' if row['variant'] == 'mid' else 'E'}"
        draw.rectangle((entry_x - 9, entry_y - 9, entry_x + 9, entry_y + 9), fill=entry_color)
        draw.text((entry_x + 8, entry_y - 30), label, fill=entry_color, font=label_font)
        exit_i = index_at_time(row["exit_time"])
        if exit_i is not None and math.isfinite(float(row["exit_price"])):
            exit_x = x_at(exit_i)
            exit_y = y_price(row["exit_price"])
            out_color = green if row["outcome"] == "target" else red if row["outcome"] == "stop" else gray
            draw.ellipse((exit_x - 8, exit_y - 8, exit_x + 8, exit_y + 8), outline=out_color, width=4)

    draw.rectangle((left, price_top, right, price_bottom), outline="#9ca3af", width=2)

    legend_y = 970
    draw.rectangle((left, legend_y, left + 28, legend_y + 28), fill=green)
    draw.text((left + 40, legend_y), "filled entry passes filter", fill=axis_color, font=small_font)
    draw.rectangle((left + 310, legend_y, left + 338, legend_y + 28), fill=red)
    draw.text((left + 350, legend_y), "filled entry filtered by time", fill=axis_color, font=small_font)
    draw.rectangle((left + 630, legend_y + 4, left + 670, legend_y + 24), outline=box_color, width=4)
    draw.text((left + 682, legend_y), "box, purple midline", fill=axis_color, font=small_font)
    draw.ellipse((left + 930, legend_y + 5, left + 952, legend_y + 27), outline=green, width=4)
    draw.text((left + 962, legend_y), "target exit", fill=axis_color, font=small_font)
    draw.ellipse((left + 1100, legend_y + 5, left + 1122, legend_y + 27), outline=red, width=4)
    draw.text((left + 1132, legend_y), "stop exit", fill=axis_color, font=small_font)

    headers = ["Box", "Var", "Filter", "Entry ET", "Dir", "Outcome", "Net", "Block", "Box R", "Bars"]
    xs = [left, left + 55, left + 120, left + 330, left + 465, left + 545, left + 675, left + 765, left + 930, left + 1035]
    draw.text((left, table_top - 40), "Retest entry fills", fill=axis_color, font=label_font)
    for x, header in zip(xs, headers):
        draw.text((x, table_top), header, fill=axis_color, font=small_font)
    draw.line((left, table_top + 30, right, table_top + 30), fill="#9ca3af", width=2)
    shown = [row for row in rows if row["trade_status"] == "filled"][:12]
    for row_i, row in enumerate(shown):
        y = table_top + 45 + row_i * 34
        vals = [
            row["box"],
            row["variant"],
            row["entry_filter"],
            str(row["entry_time_new_york"])[11:17],
            row["direction"],
            row["outcome"],
            f"{row['net_pips']:.1f}",
            row["time_block"],
            f"{row['box_range_pips']:.1f}",
            row["box_bars"],
        ]
        row_color = red if row["entry_filter"] != "PASS" else axis_color
        for x, val in zip(xs, vals):
            draw.text((x, y), str(val), fill=row_color, font=table_font)

    image.save(out_path, "JPEG", quality=95, optimize=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=Path("EURUSD_2026.csv"))
    parser.add_argument("--out-dir", type=Path, default=Path("random_day_retest_entry_audit"))
    parser.add_argument("--seed", type=int, default=20260522)
    parser.add_argument("--min-filled", type=int, default=4)
    args = parser.parse_args()

    bars = load_5m_bars(args.data)
    day_start, window, rows = find_random_day(bars, args.seed, args.min_filled)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    trades = pd.DataFrame(rows)
    filled = trades[trades["trade_status"] == "filled"].copy()
    chart_path = args.out_dir / "random_day_retest_entries_exits.jpg"
    view_path = args.out_dir / "random_day_retest_entries_exits_viewable.jpg"
    trades.to_csv(args.out_dir / "random_day_retest_trades.csv", index=False)
    pd.DataFrame(
        [
            {
                "data": args.data.name,
                "seed": args.seed,
                "day_start_new_york": fmt_est(day_start),
                "day_end_new_york": fmt_est(day_start + pd.Timedelta(days=1)),
                "orders_tested": len(trades),
                "filled_orders": len(filled),
                "pass_fills": int((filled["entry_filter"] == "PASS").sum()) if len(filled) else 0,
                "filtered_fills": int((filled["entry_filter"] != "PASS").sum()) if len(filled) else 0,
                "pass_net_pips": round(float(filled.loc[filled["entry_filter"] == "PASS", "net_pips"].sum()), 2)
                if len(filled)
                else 0.0,
                "all_filled_net_pips": round(float(filled["net_pips"].sum()), 2) if len(filled) else 0.0,
            }
        ]
    ).to_csv(args.out_dir / "summary.csv", index=False)
    draw_chart(window, rows, day_start, chart_path)

    image = Image.open(chart_path)
    max_w = 1700
    if image.width > max_w:
        image = image.resize((max_w, round(image.height * max_w / image.width)), Image.Resampling.LANCZOS)
    image.save(view_path, "JPEG", quality=92, optimize=True)

    print(view_path)
    print(pd.read_csv(args.out_dir / "summary.csv").to_string(index=False))
    print(
        filled[
            [
                "box",
                "variant",
                "entry_filter",
                "entry_time_new_york",
                "direction",
                "outcome",
                "net_pips",
                "time_block",
                "box_range_pips",
                "box_bars",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
