from __future__ import annotations

import argparse
import math
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw

from make_blind_bb_training_sample import NY, PIP, load_5m_bars, load_font, nice_price


def draw_dashed_line(draw: ImageDraw.ImageDraw, xy: tuple[float, float, float, float], fill: str, width: int = 2) -> None:
    x1, y1, x2, y2 = xy
    dash = 14
    gap = 8
    if abs(y2 - y1) < 1:
        x = x1
        while x < x2:
            draw.line((x, y1, min(x + dash, x2), y2), fill=fill, width=width)
            x += dash + gap
    else:
        draw.line(xy, fill=fill, width=width)


def marker_triangle(draw: ImageDraw.ImageDraw, x: float, y: float, direction: str, fill: str) -> None:
    size = 18
    if direction == "long":
        points = [(x, y - size), (x - size, y + size), (x + size, y + size)]
    else:
        points = [(x, y + size), (x - size, y - size), (x + size, y - size)]
    draw.polygon(points, fill=fill)


def draw_trade_zoom(
    day_bars: pd.DataFrame,
    trade: pd.Series,
    out_path: Path,
) -> None:
    trade_id = f"B{int(trade['box'])}-{str(trade['variant']).upper()}"
    entry_i = int(float(trade["entry_i"]))
    exit_time = pd.Timestamp(trade["exit_time"])
    exit_matches = day_bars.index[day_bars["timestamp"] == exit_time]
    exit_i = int(exit_matches[0]) if len(exit_matches) else entry_i
    box_start_i = int(trade["box_start_i"])
    box_end_i = int(trade["box_end_i"])
    signal_i = int(trade["signal_i"])

    start_i = max(0, min(box_start_i, signal_i, entry_i, exit_i) - 14)
    end_i = min(len(day_bars) - 1, max(box_end_i, signal_i, entry_i, exit_i) + 18)
    if end_i - start_i < 42:
        pad = (42 - (end_i - start_i)) // 2 + 1
        start_i = max(0, start_i - pad)
        end_i = min(len(day_bars) - 1, end_i + pad)

    view = day_bars.iloc[start_i : end_i + 1].copy().reset_index(drop=True)
    index_offset = start_i

    W, H = 1700, 1020
    left, right = 110, 1590
    top, bottom = 120, 720
    table_top = 790
    img = Image.new("RGB", (W, H), "white")
    draw = ImageDraw.Draw(img)

    title_font = load_font(34, True)
    font = load_font(22)
    small_font = load_font(18)
    label_font = load_font(24, True)
    table_font = load_font(20)

    direction = str(trade["direction"])
    outcome = str(trade["outcome"])
    entry_price = float(trade["entry_price"])
    stop_price = float(trade["stop_price"])
    target_price = float(trade["target_price"])
    exit_price = float(trade["exit_price"])
    box_low = float(trade["box_low"])
    box_high = float(trade["box_high"])
    box_mid = float(trade["box_mid"])

    ymin = min(
        float(view["low"].min()),
        float(view["bb_lower"].min()),
        box_low,
        stop_price,
        target_price,
        exit_price,
    )
    ymax = max(
        float(view["high"].max()),
        float(view["bb_upper"].max()),
        box_high,
        stop_price,
        target_price,
        exit_price,
    )
    pad_y = max((ymax - ymin) * 0.18, 0.00018)
    ymin -= pad_y
    ymax += pad_y

    n = len(view)
    x_step = (right - left) / max(n - 1, 1)
    candle_w = max(7, min(18, int(x_step * 0.62)))

    def x_at_absolute(i: int) -> float:
        return left + (i - index_offset) * x_step

    def x_at_local(i: int) -> float:
        return left + i * x_step

    def y_price(value: float) -> float:
        return bottom - ((value - ymin) / (ymax - ymin)) * (bottom - top)

    # Header.
    outcome_color = "#16803c" if outcome == "target" else "#c83a2b" if outcome == "stop" else "#6b7280"
    draw.text(
        (left, 38),
        f"{trade_id} Retest Entry Zoom | {direction.upper()} | {outcome.upper()} | {float(trade['net_pips']):+.1f} pips",
        fill="#111827",
        font=title_font,
    )
    draw.text(
        (left, 82),
        f"Entry {trade['entry_time_new_york']} | Exit {trade['exit_time_new_york']} | Filter: {trade['entry_filter']}",
        fill="#374151",
        font=font,
    )

    # Grid.
    for frac in [0, 0.25, 0.5, 0.75, 1]:
        y = bottom - frac * (bottom - top)
        price = ymin + frac * (ymax - ymin)
        draw.line((left, y, right, y), fill="#e5e7eb", width=1)
        draw.text((28, y - 11), nice_price(price), fill="#4b5563", font=small_font)

    # Candles.
    for i, row in view.iterrows():
        x = x_at_local(i)
        color = "#147d52" if row["close"] >= row["open"] else "#a13d3d"
        draw.line((x, y_price(row["low"]), x, y_price(row["high"])), fill=color, width=2)
        body_top = y_price(max(row["open"], row["close"]))
        body_bottom = y_price(min(row["open"], row["close"]))
        if abs(body_bottom - body_top) < 2:
            body_bottom = body_top + 2
        draw.rectangle((x - candle_w / 2, body_top, x + candle_w / 2, body_bottom), fill=color, outline=color)

    # Bollinger bands.
    def poly(col: str, color: str, width: int) -> None:
        pts = [(int(x_at_local(i)), int(y_price(row[col]))) for i, row in view.iterrows()]
        if len(pts) > 1:
            draw.line(pts, fill=color, width=width)

    poly("bb_upper", "#2f66b3", 2)
    poly("bb_mid", "#6b7280", 1)
    poly("bb_lower", "#2f66b3", 2)

    # Box and levels.
    x_box1 = x_at_absolute(box_start_i)
    x_box2 = x_at_absolute(box_end_i)
    draw.rectangle((x_box1, y_price(box_high), x_box2, y_price(box_low)), outline="#f2a000", width=5)
    draw.line((x_box1, y_price(box_mid), x_box2, y_price(box_mid)), fill="#7c3aed", width=3)
    draw.text((x_box1 + 4, y_price(box_high) - 28), "COMPRESSION BOX", fill="#111827", font=small_font)

    for price, label, color in [
        (entry_price, "ENTRY", "#16803c" if str(trade["entry_filter"]) == "PASS" else "#c83a2b"),
        (stop_price, "STOP", "#c83a2b"),
        (target_price, "TARGET", "#16803c"),
    ]:
        y = y_price(price)
        draw_dashed_line(draw, (left, y, right, y), color, width=3)
        draw.rectangle((right - 142, y - 16, right - 6, y + 16), fill="white", outline=color, width=2)
        draw.text((right - 132, y - 13), f"{label} {nice_price(price)}", fill=color, font=small_font)

    # Signal, entry, exit markers.
    sig_x = x_at_absolute(signal_i)
    sig_y = y_price(box_high if direction == "long" else box_low)
    draw.ellipse((sig_x - 10, sig_y - 10, sig_x + 10, sig_y + 10), fill="#7c3aed")
    draw.text((sig_x + 12, sig_y - 28), "BREAKOUT CLOSE", fill="#7c3aed", font=small_font)

    entry_x = x_at_absolute(entry_i)
    entry_y = y_price(entry_price)
    entry_color = "#16803c" if str(trade["entry_filter"]) == "PASS" else "#c83a2b"
    marker_triangle(draw, entry_x, entry_y, direction, entry_color)
    entry_label_x = entry_x + 16 if entry_x < right - 180 else entry_x - 110
    draw.text((entry_label_x, entry_y - 36), "ENTRY", fill=entry_color, font=label_font)

    exit_x = x_at_absolute(exit_i)
    exit_y = y_price(exit_price)
    draw.ellipse((exit_x - 18, exit_y - 18, exit_x + 18, exit_y + 18), fill="white", outline=outcome_color, width=6)
    exit_label = f"EXIT: {outcome.upper()}"
    exit_label_x = exit_x + 18 if exit_x < right - 280 else exit_x - 245
    draw.text((exit_label_x, exit_y - 36), exit_label, fill=outcome_color, font=label_font)

    # Time ticks.
    tick_count = min(7, max(3, n // 8))
    tick_indices = sorted({round(i * (n - 1) / max(tick_count - 1, 1)) for i in range(tick_count)})
    for i in tick_indices:
        x = x_at_local(i)
        ts = view.iloc[i]["timestamp"].tz_convert(NY)
        draw.line((x, bottom, x, bottom + 8), fill="#6b7280", width=1)
        draw.text((x - 30, bottom + 14), ts.strftime("%H:%M"), fill="#4b5563", font=small_font)

    draw.rectangle((left, top, right, bottom), outline="#9ca3af", width=2)

    # Bottom fact table.
    facts = [
        ("Variant", str(trade["variant"])),
        ("Box bars", str(int(trade["box_bars"]))),
        ("Box range", f"{float(trade['box_range_pips']):.1f} pips"),
        ("Entry", nice_price(entry_price)),
        ("Stop", nice_price(stop_price)),
        ("Target", nice_price(target_price)),
        ("Exit", nice_price(exit_price)),
        ("Net", f"{float(trade['net_pips']):+.1f} pips"),
    ]
    draw.text((left, table_top - 35), "Trade Details", fill="#111827", font=label_font)
    x = left
    for idx, (k, v) in enumerate(facts):
        col = idx % 4
        row = idx // 4
        x = left + col * 365
        y = table_top + row * 52
        draw.text((x, y), k, fill="#6b7280", font=small_font)
        draw.text((x + 110, y), v, fill="#111827", font=table_font)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "JPEG", quality=94, optimize=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=Path("EURUSD_2026.csv"))
    parser.add_argument("--trades", type=Path, default=Path("random_day_retest_entry_audit/random_day_retest_trades.csv"))
    parser.add_argument("--out-dir", type=Path, default=Path("random_day_retest_entry_audit/trade_zoom_jpegs"))
    args = parser.parse_args()

    trades = pd.read_csv(args.trades, parse_dates=["signal_time", "entry_time", "exit_time"])
    filled = trades[trades["trade_status"] == "filled"].copy()
    bars = load_5m_bars(args.data)
    day_start = filled["entry_time"].min().tz_convert(NY).normalize()
    day_end = day_start + pd.Timedelta(days=1)
    day_bars = bars[(bars["timestamp_ny"] >= day_start) & (bars["timestamp_ny"] < day_end)].copy().reset_index(drop=True)

    rows = []
    for _, trade in filled.iterrows():
        name = f"box_{int(trade['box']):02d}_{str(trade['variant'])}_trade_zoom.jpg"
        out_path = args.out_dir / name
        draw_trade_zoom(day_bars, trade, out_path)
        rows.append({"box": int(trade["box"]), "variant": trade["variant"], "path": str(out_path)})

    pd.DataFrame(rows).to_csv(args.out_dir / "index.csv", index=False)
    print(pd.DataFrame(rows).to_string(index=False))


if __name__ == "__main__":
    main()
