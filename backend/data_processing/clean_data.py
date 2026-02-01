import pandas as pd
from .calculate_vdot import calculate_vdot

DESIRED_COLUMNS = ["name", "type", "distance", "elapsed_time", "moving_time", "average_heartrate", "total_elevation_gain", "workout_type", "start_date_local"]
METERS_PER_MILE = 1609.34

def clean_data(df: pd.DataFrame) -> pd.DataFrame: 
    # Toss out undesired data
    df = df[DESIRED_COLUMNS]

    # Filter only runs
    df = df.loc[df["type"] == "Run"]

    # Convert to minutes and miles
    df.moving_time /= 60
    df.elapsed_time /= 60
    df.distance /= METERS_PER_MILE

    # Add a column for pace in minutes / mile
    df["mile_pace"] = df.moving_time / df.distance

    # Convert ISO8601 to Datetime
    df["start_date_local"] = pd.to_datetime(df["start_date_local"]).dt.tz_localize(None)

    # Group runs by week (first day of the week)
    df["week_start"] = df["start_date_local"].dt.to_period("W-SUN").dt.start_time          
    
    # Calculate the vdot for each run
    df["vdot"] = df.apply(calculate_vdot, axis=1)

    return df
