import pandas as pd
import numpy as np

SAFE_ZONE_CV = 0.15
BASE_PENALTY = 0.005

# Difference in race performance for inconsistency will be greater in longe races
DISTANCE_MULTIPLIERS = {                                                                
    "5K": 0.5,      # Low risk - VO2max dominates
    "10K": 0.8,     # Medium risk 
    "half_marathon": 1.2,  # High risk
    "marathon": 2.5,       # Critical risk
}       

def calculate_coefficient_of_variance(miles):
    return np.std(miles) / np.mean(miles)

def calculate_consistency_penalty(weekly_df: pd.DataFrame, race_type: str) -> dict:
    miles = weekly_df["total_miles"].values

    cv = calculate_coefficient_of_variance(miles)

    if cv <= SAFE_ZONE_CV:                                                              
         return 1.0
    
    excess_cv = (cv - SAFE_ZONE_CV)
    multiplier = DISTANCE_MULTIPLIERS.get(race_type, 1.0)
    penalty = excess_cv * multiplier * BASE_PENALTY

    return penalty