from typing import Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.risk_calc import (
    RiskCalculation,
    compute_risk,
)


router = APIRouter()


class RiskCalcRequest(BaseModel):
    entry: float = Field(..., gt=0)
    stop: float = Field(..., gt=0)
    equity: float = Field(..., gt=0, description="Total account equity in currency units")
    risk_pct: float = Field(..., gt=0, lt=1, description="Risk per trade as a fraction (e.g., 0.01 for 1%)")
    target: Optional[float] = Field(None, gt=0)
    direction: Optional[Literal["long", "short"]] = None


class RiskCalcResponse(BaseModel):
    direction: Literal["long", "short"]
    risk_per_share: float
    risk_amount: float
    position_size: int
    r_multiple_stop: float
    r_multiple_target: Optional[float] = None
    projected_pnl: Optional[float] = None


@router.post("/calc", response_model=RiskCalcResponse)
def calc_risk(payload: RiskCalcRequest):
    if payload.entry == payload.stop:
        raise HTTPException(status_code=400, detail="entry and stop cannot be equal")

    if payload.target is not None and payload.target <= 0:
        raise HTTPException(status_code=400, detail="target must be > 0 when provided")

    try:
        result: RiskCalculation = compute_risk(
            entry=payload.entry,
            stop=payload.stop,
            equity=payload.equity,
            risk_pct=payload.risk_pct,
            target=payload.target,
            direction=payload.direction,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return RiskCalcResponse(**result.model_dump())

