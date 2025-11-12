from typing import Dict, List, Literal, Optional, TypedDict

from .risk_calc import infer_direction


def equity_curve_from_r(r_values: List[float]) -> List[float]:
    curve: List[float] = []
    total = 0.0
    for r in r_values:
        total += r
        curve.append(round(total, 6))
    return curve


def compute_summary(r_values: List[float]) -> Dict:
    n = len(r_values)
    if n == 0:
        return {
            "total_trades": 0,
            "win_rate": 0.0,
            "avg_r": 0.0,
            "best_r": 0.0,
            "worst_r": 0.0,
            "expectancy": 0.0,
            "equity_curve": [],
        }

    wins = sum(1 for r in r_values if r > 0)
    win_rate = wins / n
    avg_r = sum(r_values) / n
    best_r = max(r_values)
    worst_r = min(r_values)
    expectancy = avg_r
    curve = equity_curve_from_r(r_values)

    return {
        "total_trades": n,
        "win_rate": round(win_rate, 6),
        "avg_r": round(avg_r, 6),
        "best_r": round(best_r, 6),
        "worst_r": round(worst_r, 6),
        "expectancy": round(expectancy, 6),
        "equity_curve": curve,
    }


class TradeInputDict(TypedDict, total=False):
    entry: float
    stop: float
    exit: float
    direction: Literal["long", "short"]


def r_from_trade(t: TradeInputDict) -> Optional[float]:
    try:
        entry = float(t["entry"])  # type: ignore[index]
        stop = float(t["stop"])  # type: ignore[index]
        exit_px = float(t["exit"])  # type: ignore[index]
    except Exception:
        return None

    if entry <= 0 or stop <= 0:
        return None
    if entry == stop:
        return None

    dirn: Literal["long", "short"] = t.get("direction") or infer_direction(entry, stop)
    risk_per_share = abs(entry - stop)
    if risk_per_share == 0:
        return None

    if dirn == "long":
        r = (exit_px - entry) / risk_per_share
    else:
        r = (entry - exit_px) / risk_per_share
    return float(r)


def compute_summary_from_trades(trades: List[TradeInputDict]) -> Dict:
    r_values: List[float] = []
    for t in trades:
        r = r_from_trade(t)
        if r is not None:
            r_values.append(r)
    return compute_summary(r_values)
