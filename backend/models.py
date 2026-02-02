from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Literal

class RunActivity(BaseModel):
    id: int
    name: str
    type: str = "Run"
    distance_miles: float = Field(ge=0)
    moving_time: float = Field(ge=0)
    mile_pace: float = Field(ge=0)
    start_date_local: datetime
    total_elevation_gain: float = 0
    average_heartrate: Optional[float] = None
    pace_percentile: float = Field(ge=0, le=1)
    distance_percentile: float = Field(ge=0, le=1)
    workout_type: Literal["None", "Race", "Long Run", "Workout", "Warmup/Cooldown"]
    is_warmup_cooldown: bool
    vdot: float = Field(ge=0)

class WeeklySummary(BaseModel):
    week_start: datetime
    total_miles: float = Field(ge=0)
    num_runs: int = Field(ge=0)
    total_time: float = Field(ge=0)
    avg_pace: float = Field(ge=0)
    total_elevation: float
    vdot_max: Optional[float] = None

class RacePrediction(BaseModel):
    race: Literal["5K", "10K", "half_marathon", "marathon"]
    ideal_time: float
    consistency_penalty: float

class RunnerProfile(BaseModel):
    recent_weeks: list[WeeklySummary]
    avg_weekly_mileage: float = Field(ge=0)
    coefficient_of_variance: float = Field(ge=0)
    predicted_race_times: Optional[list[RacePrediction]] = []

class WeatherConditions(BaseModel):
    temperature_f: float
    temperature_c: float
    wind_speed_mph: float = Field(ge=0)
    wind_gust_mph: Optional[float] = Field(default=None, ge=0)                
    precipitation_mm: float = Field(default=0, ge=0) 
    conditions: str 
    feels_like_f: float
    feels_like_c: float

class WeatherImpact(BaseModel):
    weather: WeatherConditions
    wind_impact: Optional[float] = 0
    temperature_impact: Optional[float] = 0
    total_impact: Optional[float] = 0
    risk_factors: Optional[list[str]] = []

class RaceInfo(BaseModel):
    name: str
    distance_miles: float = Field(ge=0)
    date: datetime
    location: str
    lat: Optional[float] = None
    lon: Optional[float] = None
    weather: Optional[WeatherConditions] = None
