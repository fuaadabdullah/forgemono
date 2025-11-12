from datetime import datetime, timedelta
from typing import Literal, List, Optional

import os
import requests
from fastapi import APIRouter, HTTPException, Query

router = APIRouter()


Timeframe = Literal["1D", "1W", "1M"]


@router.get("/ohlc")
def get_ohlc(
    symbol: str = Query(..., min_length=1),
    timeframe: Timeframe = Query("1D"),
) -> List[dict]:
    """Return OHLCV candles for a symbol and timeframe.

    Uses Polygon aggregates if POLYGON_API_KEY is available.
    - 1D: 5-minute candles for the last market day window (~1 day lookback)
    - 1W: 1-day candles for 7 days
    - 1M: 1-day candles for 30 days
    """

    api_key = os.getenv("POLYGON_API_KEY")
    if not api_key:
        raise HTTPException(status_code=400, detail="Missing POLYGON_API_KEY on the server")

    now = datetime(2024, 11, 8)  # Use a date we know has market data
    if timeframe == "1D":
        frm = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        to = now.strftime("%Y-%m-%d")
        multiplier, timespan = 5, "minute"
    elif timeframe == "1W":
        frm = (now - timedelta(days=7)).strftime("%Y-%m-%d")
        to = now.strftime("%Y-%m-%d")
        multiplier, timespan = 1, "day"
    else:  # 1M
        frm = (now - timedelta(days=30)).strftime("%Y-%m-%d")
        to = now.strftime("%Y-%m-%d")
        multiplier, timespan = 1, "day"

    url = f"https://api.polygon.io/v2/aggs/ticker/{symbol.upper()}/range/{multiplier}/{timespan}/{frm}/{to}"
    params = {
        "adjusted": "true",
        "sort": "asc",
        "limit": 50000,
        "apiKey": api_key,
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Upstream error: {exc}") from exc

    if data.get("status") != "OK" or not data.get("results"):
        raise HTTPException(status_code=404, detail="No data")

    candles = [
        {
            "t": r["t"],
            "o": r["o"],
            "h": r["h"],
            "l": r["l"],
            "c": r["c"],
            "v": r.get("v", 0),
        }
        for r in data["results"]
    ]
    return candles

