from pydantic import BaseModel, Field
from typing import Optional, Literal

class SplitEntry (BaseModel):
    mile: int | str
    distance: float = Field(default=1.0, ge=0, le=1.0)
    pace_minutes: float = Field(ge=0)
    pace_formatted: str
    cumulative_time: float = Field(ge=0)
    cumulative_formatted: str

class SplitsResponse (BaseModel):
    splits: list[SplitEntry]
    avg_pace: float = Field(ge=0)
    pace_formatted: str
    pace_strategy: Literal["even", "negative", "positive"]
    goal_time_minutes: float = Field(ge=0)
    goal_time_formatted: str
