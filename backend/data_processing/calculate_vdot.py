import pandas as pd
import numpy as np

METERS_PER_MILE = 1609.34

def calculate_vo2_cost(velocity_meters_per_min):
    return 0.182258 * velocity_meters_per_min + 0.000104 * np.power(velocity_meters_per_min, 2) - 4.60

def calculae_percent_vo2_max(time_minutes):
    return 0.8 + 0.1894393 * np.exp(-0.012778 * time_minutes) + 0.2989558 * np.exp(-0.1932605 * time_minutes)


def calculate_vdot(row):
    distance_meters = row["distance"] * METERS_PER_MILE
    time_minutes = row["moving_time"]
    velocity_meters_per_min = distance_meters / time_minutes
    vo2_cost = calculate_vo2_cost(velocity_meters_per_min)
    percent_vo2_max = calculae_percent_vo2_max(time_minutes)

    return vo2_cost / percent_vo2_max