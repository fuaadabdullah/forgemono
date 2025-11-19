from typing import Literal, List

import os
from goblinos_ingestion_market_data import create_market_data_provider
from fastapi import APIRouter, HTTPException, Query

router = APIRouter()


Timeframe = Literal["1D", "1W", "1M"]


@router.get("/ohlc")
def get_ohlc(
    symbol: str = Query(..., min_length=1),
    timeframe: Timeframe = Query("1D"),
) -> List[dict]:
    """Return OHLCV candles for a symbol and timeframe.

    Uses the GoblinOS ingestion package with Polygon API.
    - 1D: 5-minute candles for the last market day window (~1 day lookback)
    - 1W: 1-day candles for 7 days
    - 1M: 1-day candles for 30 days
    """

    # Create market data provider with API keys from environment
    config = {
        "polygon_key": os.getenv("POLYGON_API_KEY"),
    }

    provider = create_market_data_provider(config)

    # Map timeframe to limit for ingestion package
    limit_map = {"1D": 100, "1W": 7, "1M": 30}
    limit = limit_map.get(timeframe, 100)

    try:
        candles = provider.get_ohlc(symbol, timeframe, limit)
        if not candles:
            raise HTTPException(status_code=404, detail="No data available")
        return candles
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Data fetch error: {exc}") from exc
