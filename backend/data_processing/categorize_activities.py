import pandas as pd

RACE_DISTANCES = {"5K": 3.1, "10K": 6.2, "15K": 9.3, "10 mile": 10.0, "half": 13.1, "marathon": 26.2, "50K": 31.1, "50 mile": 50.0, "100K": 62.1, "100 mile": 100.0,}   
RACE_DISTANCE_KEYWORDS = ["5k", "10k", "half", "marathon", "mile"]
RACE_KEYWORDS = ["race", "pr", "pb", "personal record", "personal best"]
WORKOUT_KEYWORDS = ["tempo", "race pace", "fartlek", "intervals", "repeat", "progress", "threshold", "800", "400"]
WARMUP_COOLDOWN_KEYWORDS = ["warm", "wu", "cool", "cd"]
EASY_RUN_KEYWORDS = ["easy", "rest", "recovery", "shakeout", "zone 2"]

FAST_RUN_PERCENTILE = 0.85
LONG_RUN_PERCENTILE = 0.90
WORKOUT_RUN_PERCENTILE = 0.80
EASY_DISTANCE_PERCENTILE = 0.50

WARMUP_COOLDOWN_DISTANCE = 1.0
workout_type = {None: "None", 0: "None", 1: "Race", 2: "Long Run", 3: "Workout", 4: "Warmup/Cooldown"}

def is_race_distance(miles: int):
    for race_miles in RACE_DISTANCES.values():                               
        if abs(miles - race_miles) <= (race_miles * 0.1):                                       
            return True                                                  
    return False

def has_keyword(name: str, keywords: list):
    if any(keyword in name for keyword in keywords):
        return True
    return False

def classify_run(row):
    name = row["name"].lower()
    tag = row["workout_type"]                                                 
    distance = row["distance"]
    is_fast = row["pace_percentile"] >= FAST_RUN_PERCENTILE
    is_easy = row["distance_percentile"] <= EASY_DISTANCE_PERCENTILE

    # Return user selected tags first and foremost
    if (tag != "None"): return tag

    # Check workouts first since workouts inculde race keywords but races don't!
    if has_keyword(name, WORKOUT_KEYWORDS): return "Workout"
    
    # Warmup / cooldowns
    if has_keyword(name, WARMUP_COOLDOWN_KEYWORDS): return "Warmup/Cooldown"
    if row["is_warmup_cooldown"]: return "Warmup/Cooldown" 

    # Easy Runs
    if has_keyword(name, EASY_RUN_KEYWORDS): return "Easy Run"
    if is_easy and row["pace_percentile"] <= WORKOUT_RUN_PERCENTILE: return "Easy Run"
    
    # Races
    if has_keyword(name, RACE_KEYWORDS): return "Race"
    if has_keyword(name, RACE_DISTANCE_KEYWORDS) and is_fast: return "Race"
    if is_race_distance(distance) and is_fast: return "Race"

    # Long Runs
    if row["distance_percentile"] >= LONG_RUN_PERCENTILE: return "Long Run"
    if ("long run" in name): return "Long Run"
    
    # Failed to classify / regular run
    return "None"

def categorize_activities(df: pd.DataFrame) -> pd.DataFrame: 
    # Map Strava default integer workout types to strings
    df["workout_type"] = df["workout_type"].map(workout_type).fillna("None")
                                             
    # Mark warmups and cooldowns to ignore for percentiles  
    median_pace = df["mile_pace"].median()
    df["is_warmup_cooldown"] = (df["distance"] < WARMUP_COOLDOWN_DISTANCE) & (df["mile_pace"] >= median_pace)

    # Calculate percentiles only for non-warmup/cooldown runs                          
    clean_mask = ~df["is_warmup_cooldown"]                                             
                                                                                        
    # Initialize percentile columns as NaN (blank)                                     
    df["pace_percentile"] = pd.NA                                                      
    df["distance_percentile"] = pd.NA                                                  
                                                                                        
    # Calculate percentiles only for clean runs (rank among themselves)                                                                      
    df.loc[clean_mask, "pace_percentile"] = df.loc[clean_mask, "mile_pace"].rank(pct=True, ascending=False)                                           
    df.loc[clean_mask, "distance_percentile"] = df.loc[clean_mask, "distance"].rank(pct=True)   

    # Classfiy the remaining runs
    df["workout_type"] = df.apply(classify_run, axis=1)
    return df
