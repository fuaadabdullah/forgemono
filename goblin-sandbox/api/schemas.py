from __future__ import annotations

from pydantic import BaseModel, Field


class RunReq(BaseModel):
    language: str = Field(..., min_length=1)
    code: str = Field(..., min_length=1)
    timeout: int = Field(3, ge=1, le=60)


class RunResp(BaseModel):
    job_id: str


class StatusResp(BaseModel):
    job_id: str
    status: str
    created_at: float | None = None
    started_at: float | None = None
    finished_at: float | None = None


class ResultData(BaseModel):
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    timed_out: bool = False
    duration_ms: int | None = None
    truncated_stdout: bool = False
    truncated_stderr: bool = False


class ResultResp(BaseModel):
    job_id: str
    status: str
    result: ResultData | None = None
    error: str | None = None


class HealthResp(BaseModel):
    status: str
    redis: str
