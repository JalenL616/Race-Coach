import pandas as pd
from categorize_activities import categorize_activities
from calculate_vdot import calculate_vdot
from pathlib import Path                                                               
                                                                                         
DATA_URL = Path(__file__).parent.parent / "data" / "raw_activities.json"   
DESIRED_COLUMNS = ["name", "type", "distance", "moving_time", "average_heartrate", "total_elevation_gain", "workout_type", "start_date_local"]
METERS_PER_MILE = 1609.34

def load_data() -> pd.DataFrame:
    try:
        df = pd.read_json(DATA_URL, orient="records")
        return df
    except ValueError:
        print("Error: JSON file is malformed or empty.")
        return None

def clean_data(df: pd.DataFrame) -> pd.DataFrame: 
    # Toss out undesired data
    df = df[DESIRED_COLUMNS]

    # Filter only runs
    df = df.loc[df["type"] == "Run"]

    # Convert to minutes and miles
    df.moving_time /= 60
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

def aggregate_weekly(df: pd.DataFrame) -> pd.DataFrame:
    weekly = df.groupby("week_start").agg(                                             
        total_miles=("distance", "sum"),
        num_runs=("distance", "count"),
        total_time=("moving_time", "sum"),
        vdot_max=("vdot", "max")
    ).reset_index()    

    weekly["avg_pace"] = weekly["total_time"] / weekly["total_miles"]                      
    weekly["mileage_change"] = weekly["total_miles"].pct_change()   

    return weekly                    


def print_data():
    df = pd.read_json(DATA_URL)
    df = clean_data(df)
    df = categorize_activities(df)
    print(df.to_string())
    with open("output.csv", "w") as f: 
        df.to_csv(f, index=False)
    weekly_df = aggregate_weekly(df)
    print(weekly_df.to_string())

if __name__ == "__main__":
    print_data()