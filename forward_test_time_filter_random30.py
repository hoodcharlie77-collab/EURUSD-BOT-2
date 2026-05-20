from __future__ import annotations

import argparse
import math
import random
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw

from make_blind_bb_training_sample import NY, PIP, fmt_est, load_5m_bars, load_font
from make_full_rule_test_chart import pick_boxes, score_candidates


SPREAD_PIPS = 1.2
STOP_PIPS = 10.0
RISK_PER_TRADE = 0.005
TIME_BLOCKS = [
    ("00:00-03:00", 0, 3),
    ("03:00-06:00", 3, 6),
    ("06:00-09:00", 6, 9),
    ("09:00-12:00", 9, 12),
    ("12:00-15:00", 12, 15),
    ("15:00-17:00", 15, 17),
    ("17:00-24:00", 17, 24),
]


def time_block(hour: int) -> str:
    for label, start, end in TIME_BLOCKS:
        if start <= hour < end:
            return label
    raise ValueError(f"Bad hour: {hour}")


def equity_stats(filled: pd.DataFrame) -> dict:
    if filled.empty:
        return {
            "sum_net_risk_r": 0.0,
            "roi_pct": 0.0,
            "max_drawdown_pct": 0.0,
            "ending_equity_index": 100.0,
        }

    equity = 1.0
    peak = 1.0
    max_dd = 0.0
    for r_mult in filled["net_risk_r"].fillna(0.0):
        equity *= 1.0 + RISK_PER_TRADE * float(r_mult)
        peak = max(peak, equity)
        if peak:
            max_dd = max(max_dd, (peak - equity) / peak)

    return {
        "sum_net_risk_r": round(float(filled["net_risk_r"].sum()), 3),
        "roi_pct": round((equity - 1.0) * 100.0, 2),
        "max_drawdown_pct": round(max_dd * 100.0, 2),
        "ending_equity_index": round(equity * 100.0, 2),
    }


def summarize(name: str, trades: pd.DataFrame) -> dict:
    filled = trades.copy()
    targets = filled[filled["outcome"] == "target"]
    stops = filled[filled["outcome"] == "stop"]
    time_exits = filled[filled["outcome"] == "time_exit"]
    winners = filled[filled["net_pips"] > 0]
    losers = filled[filled["net_pips"] < 0]
    gross_profit = float(winners["net_pips"].sum()) if len(winners) else 0.0
    gross_loss = abs(float(losers["net_pips"].sum())) if len(losers) else 0.0
    return {
        "test": name,
        "trades": len(filled),
        "targets": len(targets),
        "stops": len(stops),
        "time_exits": len(time_exits),
        "target_hit_rate": round(len(targets) / len(filled), 3) if len(filled) else 0.0,
        "positive_net_trades": len(winners),
        "negative_net_trades": len(losers),
        "positive_net_rate": round(len(winners) / len(filled), 3) if len(filled) else 0.0,
        "net_pips": round(float(filled["net_pips"].sum()), 2) if len(filled) else 0.0,
        "avg_net_pips": round(float(filled["net_pips"].mean()), 2) if len(filled) else 0.0,
        "profit_factor_net_pips": round(gross_profit / gross_loss, 3) if gross_loss else math.inf,
        **equity_stats(filled),
    }


def box_overlaps(start: pd.Timestamp, end: pd.Timestamp, used: list[tuple[pd.Timestamp, pd.Timestamp]]) -> bool:
    pad = pd.Timedelta(minutes=30)
    return any(not (end < prior_start - pad or start > prior_end + pad) for prior_start, prior_end in used)


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
        return {
            "outcome": "time_exit",
            "exit_time": pd.NaT,
            "exit_price": math.nan,
            "gross_pips": 0.0,
            "net_pips": -SPREAD_PIPS,
        }

    final = trade_bars.iloc[-1]
    exit_price = float(final["close"])
    if direction == "long":
        gross_pips = (exit_price - entry_price) / PIP
    else:
        gross_pips = (entry_price - exit_price) / PIP
    return {
        "outcome": "time_exit",
        "exit_time": final["timestamp"],
        "exit_price": exit_price,
        "gross_pips": gross_pips,
        "net_pips": gross_pips - SPREAD_PIPS,
    }


def trade_from_candidate(
    window: pd.DataFrame,
    candidate: dict,
    data_file: str,
    window_start: pd.Timestamp,
    trade_id: int,
) -> dict | None:
    if candidate["end_i"] > len(window) - 25:
        return None

    chunk = window.iloc[candidate["start_i"] : candidate["end_i"] + 1]
    box_low = float(chunk["low"].min())
    box_high = float(chunk["high"].max())
    r_price = box_high - box_low
    r_pips = r_price / PIP
    if r_pips <= 0:
        return None

    box_end_utc = window.iloc[candidate["end_i"]]["timestamp"]
    signal = first_close_break(window, box_end_utc, box_high, box_low, r_price)
    if signal is None:
        return None

    entry_price = float(signal["entry_price"])
    stop_offset = STOP_PIPS * PIP
    if signal["direction"] == "long":
        stop_price = entry_price - stop_offset
        target_price = entry_price + r_price
    else:
        stop_price = entry_price + stop_offset
        target_price = entry_price - r_price

    reward_pips = abs(target_price - entry_price) / PIP
    if reward_pips <= 0:
        return None

    resolved = resolve_trade(
        window,
        int(signal["signal_i"]),
        entry_price,
        signal["direction"],
        stop_price,
        target_price,
        box_end_utc,
    )
    signal_hour = signal["signal_time"].tz_convert(NY).hour
    return {
        "trade_id": trade_id,
        "data_file": data_file,
        "window_start_new_york": fmt_est(window_start),
        "window_end_new_york": fmt_est(window.iloc[-1]["timestamp"]),
        "box_start_new_york": fmt_est(window.iloc[candidate["start_i"]]["timestamp"]),
        "box_end_new_york": fmt_est(box_end_utc),
        "tier": candidate["tier"],
        "box_range_pips": round(r_pips, 2),
        "box_bars": int(candidate["bars"]),
        "box_score": float(candidate["score"]),
        "direction": signal["direction"],
        "signal_time_new_york": fmt_est(signal["signal_time"]),
        "signal_hour_new_york": signal_hour,
        "time_block": time_block(signal_hour),
        "excluded_0300_0600": bool(3 <= signal_hour < 6),
        "entry_price": round(entry_price, 5),
        "stop_price": round(stop_price, 5),
        "target_price": round(target_price, 5),
        "risk_pips": STOP_PIPS,
        "reward_pips": round(reward_pips, 2),
        "reward_to_risk": round(reward_pips / STOP_PIPS, 3),
        "outcome": resolved["outcome"],
        "exit_time_new_york": fmt_est(resolved["exit_time"]) if not pd.isna(resolved["exit_time"]) else "",
        "exit_price": round(float(resolved["exit_price"]), 5) if not pd.isna(resolved["exit_price"]) else "",
        "gross_pips": round(float(resolved["gross_pips"]), 2),
        "net_pips": round(float(resolved["net_pips"]), 2),
        "net_risk_r": round(float(resolved["net_pips"]) / STOP_PIPS, 3),
        "spread_pips_round_turn": SPREAD_PIPS,
    }


def collect_random_trades(data_path: Path, trade_count: int, seed: int, count_mode: str) -> pd.DataFrame:
    rng = random.Random(seed)
    bars = load_5m_bars(data_path)
    possible_starts = list(range(0, max(len(bars) - 170, 0), 12))
    rng.shuffle(possible_starts)

    used_boxes: list[tuple[pd.Timestamp, pd.Timestamp]] = []
    trades: list[dict] = []
    filtered_target = count_mode == "filtered"

    def target_met() -> bool:
        if filtered_target:
            return sum(not trade["excluded_0300_0600"] for trade in trades) >= trade_count
        return len(trades) >= trade_count

    for start_i in possible_starts:
        if target_met():
            break

        start_ts = bars.iloc[start_i]["timestamp"]
        end_ts = start_ts + pd.Timedelta(hours=12)
        window = bars[(bars["timestamp"] >= start_ts) & (bars["timestamp"] < end_ts)].copy().reset_index(drop=True)
        if len(window) < 130:
            continue
        max_gap = window["timestamp"].diff().dropna().max()
        if pd.notna(max_gap) and max_gap > pd.Timedelta(minutes=10):
            continue

        candidates, _, _, _ = score_candidates(window)
        if not candidates:
            continue

        for candidate in pick_boxes(candidates, 4):
            if target_met():
                break
            box_start = window.iloc[candidate["start_i"]]["timestamp"]
            box_end = window.iloc[candidate["end_i"]]["timestamp"]
            if box_overlaps(box_start, box_end, used_boxes):
                continue
            trade = trade_from_candidate(window, candidate, data_path.name, start_ts, len(trades) + 1)
            if trade is None:
                continue
            trades.append(trade)
            used_boxes.append((box_start, box_end))

    found = sum(not trade["excluded_0300_0600"] for trade in trades) if filtered_target else len(trades)
    if found < trade_count:
        raise RuntimeError(f"Only found {found} requested trades from {data_path}")
    return pd.DataFrame(trades)


def block_summary(trades: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for label, _, _ in TIME_BLOCKS:
        chunk = trades[trades["time_block"] == label]
        rows.append(
            {
                "time_block": label,
                "positive_net_wins": int((chunk["net_pips"] > 0).sum()),
                "negative_net_losses": int((chunk["net_pips"] < 0).sum()),
                "flat": int((chunk["net_pips"] == 0).sum()),
                "net_pips": round(float(chunk["net_pips"].sum()), 2) if len(chunk) else 0.0,
            }
        )
    return pd.DataFrame(rows)


def draw_results_chart(summary: pd.DataFrame, blocks: pd.DataFrame, out_path: Path, title: str) -> None:
    width, height = 1700, 1050
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    title_font = load_font(44, True)
    subtitle_font = load_font(24)
    label_font = load_font(22)
    small_font = load_font(18)
    table_font = load_font(20)

    left, right = 110, 1550
    top, bottom = 155, 700
    chart_w = right - left
    chart_h = bottom - top
    y_max = max(6, int(max(blocks["positive_net_wins"].max(), blocks["negative_net_losses"].max())) + 1)

    draw.text((left, 42), title, fill="#111827", font=title_font)
    draw.text(
        (left, 96),
        "EURUSD compression breakout | 10 pip stop | 1R target from entry | New York / Toronto Eastern time",
        fill="#374151",
        font=subtitle_font,
    )

    for y in range(y_max + 1):
        yy = bottom - (y / y_max) * chart_h
        draw.line((left, yy, right, yy), fill="#E5E7EB", width=1)
        draw.text((left - 45, yy - 12), str(y), fill="#4B5563", font=small_font)
    draw.line((left, top, left, bottom), fill="#111827", width=2)
    draw.line((left, bottom, right, bottom), fill="#111827", width=2)

    group_w = chart_w / len(TIME_BLOCKS)
    bar_w = 58
    gap = 16
    green = "#17803D"
    red = "#C83A2B"
    for i, row in blocks.iterrows():
        center = left + group_w * (i + 0.5)
        for value, x0, color in [
            (int(row["positive_net_wins"]), center - bar_w - gap / 2, green),
            (int(row["negative_net_losses"]), center + gap / 2, red),
        ]:
            x1 = x0 + bar_w
            y1 = bottom
            y0 = bottom - (value / y_max) * chart_h
            if value > 0:
                draw.rounded_rectangle((x0, y0, x1, y1), radius=4, fill=color)
            draw.text(
                (x0 + bar_w / 2 - 7, y0 - 30 if value > 0 else bottom - 24),
                str(value),
                fill="#111827",
                font=label_font,
            )
        draw.text((center - 62, bottom + 22), str(row["time_block"]), fill="#111827", font=small_font)

    legend_y = 760
    draw.rectangle((left, legend_y, left + 28, legend_y + 28), fill=green)
    draw.text((left + 40, legend_y - 1), "Positive-net wins", fill="#111827", font=label_font)
    draw.rectangle((left + 310, legend_y, left + 338, legend_y + 28), fill=red)
    draw.text((left + 350, legend_y - 1), "Negative-net losses", fill="#111827", font=label_font)

    table_y = 825
    headers = ["Test", "Trades", "Target hit", "Positive net", "Net pips", "ROI", "Max DD"]
    xs = [110, 505, 635, 800, 990, 1130, 1260]
    for x, header in zip(xs, headers):
        draw.text((x, table_y), header, fill="#111827", font=label_font)
    draw.line((110, table_y + 34, 1500, table_y + 34), fill="#9CA3AF", width=2)
    for idx, row in summary.iterrows():
        y = table_y + 52 + idx * 42
        vals = [
            str(row["test"]),
            str(int(row["trades"])),
            f"{row['target_hit_rate'] * 100:.1f}%",
            f"{row['positive_net_rate'] * 100:.1f}%",
            f"{row['net_pips']:.1f}",
            f"{row['roi_pct']:.2f}%",
            f"{row['max_drawdown_pct']:.2f}%",
        ]
        for x, val in zip(xs, vals):
            draw.text((x, y), val, fill="#111827", font=table_font)

    image.save(out_path, "JPEG", quality=95, optimize=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=Path("EURUSD_2026.csv"))
    parser.add_argument("--out-dir", type=Path, default=Path("forward_test_time_filter_random30_2026"))
    parser.add_argument("--trade-count", type=int, default=30)
    parser.add_argument("--seed", type=int, default=20260520)
    parser.add_argument("--count-mode", choices=["baseline", "filtered"], default="baseline")
    args = parser.parse_args()

    trades = collect_random_trades(args.data, args.trade_count, args.seed, args.count_mode)
    filtered = trades[~trades["excluded_0300_0600"]].copy()
    excluded = trades[trades["excluded_0300_0600"]].copy()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    trades.to_csv(args.out_dir / "random30_trades_baseline.csv", index=False)
    filtered.to_csv(args.out_dir / "random30_trades_excluding_0300_0600.csv", index=False)
    excluded.to_csv(args.out_dir / "random30_excluded_0300_0600_trades.csv", index=False)

    if args.count_mode == "filtered":
        summary_rows = [
            summarize("All collected before filter", trades),
            summarize("Filtered random 30", filtered),
            summarize("Excluded 03:00-06:00 only", excluded),
        ]
        title = "Forward Test: 2026 Random 30 Filtered Trades"
    else:
        summary_rows = [
            summarize("Baseline random 30", trades),
            summarize("Exclude 03:00-06:00", filtered),
            summarize("Excluded 03:00-06:00 only", excluded),
        ]
        title = "Forward Test: 2026 Random 30 Trades"

    summary = pd.DataFrame(summary_rows)
    blocks = block_summary(trades)
    summary.to_csv(args.out_dir / "summary.csv", index=False)
    blocks.to_csv(args.out_dir / "winners_losers_by_time_block.csv", index=False)

    chart_path = args.out_dir / "random30_winners_vs_losers_by_time_block.jpg"
    draw_results_chart(summary, blocks, chart_path, title)

    print(summary.to_string(index=False))
    print()
    print(blocks.to_string(index=False))
    print()
    print(chart_path)


if __name__ == "__main__":
    main()
