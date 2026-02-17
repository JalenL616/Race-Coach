from typing import Literal

# Calculates average mile pace (min / mile) from distance and time 
def calculate_mile_pace (distance_miles: float, goal_time_minutes: float) -> float:
    return goal_time_minutes / distance_miles

# Returns a list with each mile's pace equal to the average pace
def generate_mile_splits(distance_miles: float, avg_pace: float) -> list[tuple[float, float]]:
    splits = []

    # Full miles
    for _ in range(int(distance_miles)):
        splits.append((1.0, avg_pace))

    # Partial miles
    if not distance_miles.is_integer(): 
        remaining_distance = distance_miles % 1
        splits.append((remaining_distance, avg_pace))

    return splits

# Applies pacing strategy to a list of even splits at avg pace
def apply_pace_strategy (
        splits: list[tuple[float, float]], 
        pace_strategy: Literal["even", "negative", "positive"]
        ) -> None:
    
    starting_multiplier = 1
    ending_multiplier = 1
    if pace_strategy == "even": return splits
    if pace_strategy == "positive": 
        starting_multiplier = 0.98
        ending_multiplier = 1.02
    elif pace_strategy == "negative": 
        starting_multiplier = 1.03
        ending_multiplier = 0.97

    multiplier = 1
    # apply starting multiplier
    for mile in range(len(splits)):
        # Apply starting, standard, or ending multiplier depending on distance third
        if (mile < len(splits) / 3): multiplier = starting_multiplier
        elif (mile < 2 * len(splits) / 3): multiplier = 1
        else: 
            multiplier = ending_multiplier
        distance, pace = splits[mile]
        splits[mile] = (distance, pace * multiplier)

# Apply adjustments in seconds to each mile split
def apply_elevation_adjustments (
        splits: list[tuple[float, float]],
        elevation_adjustment: list[float]
        ) -> None:
    for mile in range(len(splits)):
        if mile < len(elevation_adjustment):
            distance, pace = splits[mile]
            splits[mile] = (distance, pace + elevation_adjustment[mile] / 60)