from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from services.analytics import (
    compute_summary,
    equity_curve_from_r,
    compute_summary_from_trades,
)


router = APIRouter()


class TradeInput(BaseModel):
    r_multiple: float = Field(..., description="Trade result in units of R")


class MetricsSummaryRequest(BaseModel):
    trades: List[TradeInput]


class MetricsSummaryResponse(BaseModel):
    total_trades: int
    win_rate: float
    avg_r: float
    best_r: float
    worst_r: float
    expectancy: float
    equity_curve: List[float]


@router.get("/ping")
def ping() -> dict:
    return {"status": "ok"}


@router.post("/summary", response_model=MetricsSummaryResponse)
def summary(body: MetricsSummaryRequest) -> MetricsSummaryResponse:
    trades_r = [t.r_multiple for t in body.trades]
    s = compute_summary(trades_r)
    return MetricsSummaryResponse(**s)


class EquityCurveRequest(BaseModel):
    r: List[float]


class EquityCurveResponse(BaseModel):
    equity_curve: List[float]


@router.post("/equity-curve", response_model=EquityCurveResponse)
def equity_curve(body: EquityCurveRequest) -> EquityCurveResponse:
    return EquityCurveResponse(equity_curve=equity_curve_from_r(body.r))


class TradeFull(BaseModel):
    entry: float
    stop: float
    exit: float
    direction: Optional[str] = None  # 'long' | 'short' optional


class MetricsFromTradesRequest(BaseModel):
    trades: List[TradeFull]


@router.post("/summary-from-trades", response_model=MetricsSummaryResponse)
def summary_from_trades(body: MetricsFromTradesRequest) -> MetricsSummaryResponse:
    # Convert to dicts to satisfy TypedDict usage
    trades_dicts = [t.model_dump() for t in body.trades]
    s = compute_summary_from_trades(trades_dicts)
    return MetricsSummaryResponse(**s)
