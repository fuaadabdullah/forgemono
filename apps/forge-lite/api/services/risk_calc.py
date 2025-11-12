from typing import Literal, Optional

from pydantic import BaseModel, Field


class RiskCalculation(BaseModel):
    direction: Literal["long", "short"]
    risk_per_share: float = Field(..., gt=0)
    risk_amount: float = Field(..., ge=0)
    position_size: int = Field(..., ge=0)
    r_multiple_stop: float
    r_multiple_target: Optional[float] = None
    projected_pnl: Optional[float] = None


def infer_direction(entry: float, stop: float) -> Literal["long", "short"]:
    # If entry above stop, assume long; otherwise short
    return "long" if entry > stop else "short"


def compute_risk(
    *,
    entry: float,
    stop: float,
    equity: float,
    risk_pct: float,
    target: Optional[float] = None,
    direction: Optional[Literal["long", "short"]] = None,
) -> RiskCalculation:
    if entry <= 0 or stop <= 0 or equity <= 0:
        raise ValueError("entry, stop, and equity must be > 0")
    if not (0 < risk_pct < 1):
        raise ValueError("risk_pct must be between 0 and 1 (e.g., 0.01 for 1%)")
    if entry == stop:
        raise ValueError("entry and stop cannot be equal")

    dirn = direction or infer_direction(entry, stop)
    risk_per_share = abs(entry - stop)
    risk_amount = equity * risk_pct
    # Floor position size to whole shares
    position_size = int(risk_amount // risk_per_share) if risk_per_share > 0 else 0

    r_multiple_stop = -1.0

    r_multiple_target: Optional[float] = None
    projected_pnl: Optional[float] = None

    if target is not None:
        if dirn == "long":
            r_multiple_target = (target - entry) / risk_per_share
        else:
            r_multiple_target = (entry - target) / risk_per_share
        projected_pnl = r_multiple_target * risk_amount

    return RiskCalculation(
        direction=dirn,
        risk_per_share=risk_per_share,
        risk_amount=risk_amount,
        position_size=position_size,
        r_multiple_stop=r_multiple_stop,
        r_multiple_target=r_multiple_target,
        projected_pnl=projected_pnl,
    )

