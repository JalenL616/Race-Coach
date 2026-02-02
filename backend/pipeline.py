import pandas as pd
from datetime import datetime, timedelta
from data_processing.processor import load_data, aggregate_weekly
from data_processing.clean_data import clean_data
from data_processing.categorize_activities import categorize_activities
from data_processing.calculate_race_performances import calculate_race_performances
from models import RunnerProfile, WeeklySummary 

NUMBER_OF_RECENT_WEEKS = 12

def build_runner_profile() -> RunnerProfile:
    # Process activities
    df = load_data()
    df = clean_data(df)
    df = categorize_activities(df)

    # Aggregate into weeks
    weekly_df = aggregate_weekly(df)

    cutoff_date = datetime.now() - timedelta(weeks=NUMBER_OF_RECENT_WEEKS)                            

    # Convert weekly DataFrame rows to WeeklySummary models                   
    recent_weeks = [                                                          
        WeeklySummary(                                                        
            week_start=row["week_start"],
            total_miles=row["total_miles"],
            num_runs=row["num_runs"],
            total_time=row["total_time"],
            avg_pace=row["avg_pace"],
            total_elevation=row["total_elevation"],
            vdot_max=row["vdot_max"]
        )
        for _, row in weekly_df.iterrows()
        if row["week_start"] >= cutoff_date  
    ]

    # Calculate consistency
    cv = weekly_df["total_miles"].std() / weekly_df["total_miles"].mean()

    # Build profile
    return RunnerProfile(
        recent_weeks=recent_weeks,
        avg_weekly_mileage=weekly_df["total_miles"].mean(),
        coefficient_of_variance=cv,
        predicted_race_times=calculate_race_performances(recent_weeks, cv)
    )

if __name__ == "__main__":
    print(build_runner_profile())