import pandas as pd
from .categorize_activities import categorize_activities
from .clean_data import clean_data
from pathlib import Path                                                               
                                                                                         
DATA_URL = Path(__file__).parent.parent / "data" / "raw_activities.json"   

def load_data() -> pd.DataFrame:
    try:
        df = pd.read_json(DATA_URL, orient="records")
        return df
    except ValueError:
        print("Error: JSON file is malformed or empty.")
        return None

def aggregate_weekly(df: pd.DataFrame) -> pd.DataFrame:
    weekly = df.groupby("week_start").agg(                                             
        total_miles=("distance", "sum"),
        num_runs=("distance", "count"),
        total_time=("moving_time", "sum"),
        vdot_max=("vdot", "max"),
        total_elevation=("total_elevation_gain", "sum")
    ).reset_index()    

    weekly["avg_pace"] = weekly["total_time"] / weekly["total_miles"]                      
    weekly["mileage_change"] = weekly["total_miles"].pct_change()   

    return weekly