import pandas as pd
from models import WeeklySummary, RacePrediction
from data_processing.calculate_consistency import calculate_consistency_penalty
from data_processing.calculate_vdot import calculate_vo2_cost, calculate_percent_vo2_max

RACE_DISTANCES = {"5K": 5000, "10K": 10000, "half_marathon": 21097.5, "marathon": 42195}

def calculate_ideal_race_time(vdot_max: int, race_type: str):
    distance_meters = RACE_DISTANCES[race_type]
    
    # VDOT is not a reversible formula, binary search for the proper time to hit that vdot
    # Start from 10 minutes (impossible 5K) to 10 hours (very slow marathon)
    low_time = 10.0
    high_time = 600.0

    # Binary search with a tolerance of 10s accuracy
    while (high_time - low_time) > 0.01:
        mid_time = (low_time + high_time) / 2
        velocity = distance_meters / mid_time
        calculated_vdot = calculate_vo2_cost(velocity) / calculate_percent_vo2_max(mid_time)

        if calculated_vdot > vdot_max:
            low_time = mid_time
        else:
            high_time = mid_time

    return (low_time + high_time) / 2

def calculate_race_performances(recent_weeks: list[WeeklySummary], cv: float) -> list[RacePrediction] | None:
    weekly_training = recent_weeks
    if not recent_weeks: return None
    race_performaces = []

    vdot_max = 0
    for week in weekly_training:
        vdot_max = max(vdot_max, week.vdot_max)
    print (vdot_max)
    
    for race in RACE_DISTANCES.keys():
        ideal_race_time = calculate_ideal_race_time(vdot_max, race)
        consistency_penalty = calculate_consistency_penalty(cv, race)
        race_performaces.append(RacePrediction(race=race, ideal_time=ideal_race_time, consistency_penalty=consistency_penalty))
    
    return race_performaces