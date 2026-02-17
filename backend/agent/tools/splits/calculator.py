from .helpers import calculate_mile_pace, generate_mile_splits, apply_pace_strategy, apply_elevation_adjustments
from ..formatters import format_mile_splits, format_pace, format_time
from ...models import SplitsResponse
from typing import Literal

def calculate_splits (
        pace_strategy: Literal["even", "negative", "positive"],
        goal_time_minutes: float,
        distance_miles: float,
        elevation_adjustment: list[float] | None = None
        ):
    avg_pace = calculate_mile_pace(distance_miles, goal_time_minutes)

    splits = generate_mile_splits(distance_miles, avg_pace)

    apply_pace_strategy(splits, pace_strategy)

    if elevation_adjustment is not None: 
        apply_elevation_adjustments(splits, elevation_adjustment=elevation_adjustment)

    split_entry_list = format_mile_splits(splits)

    response = SplitsResponse(splits=split_entry_list, 
                              avg_pace=avg_pace, 
                              pace_formatted=format_pace(avg_pace),
                              pace_strategy=pace_strategy,
                              goal_time_minutes=goal_time_minutes,
                              goal_time_formatted=format_time(goal_time_minutes))
    
    return response