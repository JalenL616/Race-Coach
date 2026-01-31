# Week 1: Data Engineering Foundation

**Goal:** Ingest user data from Strava, clean and process it with Pandas, build a race time prediction engine, and establish a solid Python project structure.

**Time Budget:** ~30 hours
- Learning: 8-10 hours
- Building: 20-22 hours

---

## Prerequisites

Before starting, ensure you have:
- Python 3.10+ installed
- A Strava account with running data
- Strava API application created at https://www.strava.com/settings/api
- OpenWeather API key (free tier) from https://openweathermap.org/api

---

## Day 1: Environment Setup + OAuth Foundation

### Learning (2 hrs)

**Python Virtual Environments**
- Read: [Real Python - Python Virtual Environments](https://realpython.com/python-virtual-environments-primer/)
- Key concepts: Why isolation matters, venv vs conda, activating/deactivating
- Coming from Node: Think of venv as a project-local `node_modules` but for Python

**OAuth 2.0 Fundamentals**
- Read: [DigitalOcean - Introduction to OAuth 2](https://www.digitalocean.com/community/tutorials/an-introduction-to-oauth-2)
- Read: [Strava API Authentication Docs](https://developers.strava.com/docs/authentication/)
- Key concepts: Authorization code flow, access tokens vs refresh tokens, scopes

### Building (3 hrs)

**Task 1: Project Setup**
```
Race-Coach/
├── backend/
│   ├── __init__.py
│   ├── auth_flow.py      # OAuth handling
│   ├── fetch_data.py     # Strava API calls
│   ├── processor.py      # Data cleaning (Week 1)
│   ├── predictor.py      # Race predictions (Week 1)
│   └── models.py         # Pydantic models
├── .env                  # API keys (gitignored)
├── .gitignore
├── requirements.txt
└── README.md
```

1. Create and activate virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install initial dependencies:
   ```bash
   pip install requests python-dotenv pydantic
   pip freeze > requirements.txt
   ```

3. Create `.env` file with your Strava credentials:
   ```
   STRAVA_CLIENT_ID=your_client_id
   STRAVA_CLIENT_SECRET=your_client_secret
   STRAVA_REDIRECT_URI=http://localhost:8000/callback
   ```

**Task 2: OAuth Flow Implementation**

Build `auth_flow.py` that:
1. Generates the Strava authorization URL
2. Opens browser for user to authorize
3. Runs a temporary local server to capture the callback
4. Exchanges authorization code for access token
5. Saves tokens to `.env` or a local file for reuse
6. Handles token refresh when expired

**Expected output:** Running `python backend/auth_flow.py` should open your browser, let you authorize, and save valid tokens.

---

## Day 2: Data Fetching + Pandas Introduction

### Learning (3 hrs)

**Pandas Fundamentals**
- Complete: [Kaggle - Creating, Reading, and Writing](https://www.kaggle.com/learn/pandas) (Lesson 1)
- Complete: [Kaggle - Indexing, Selecting & Assigning](https://www.kaggle.com/learn/pandas) (Lesson 2)
- Key concepts: DataFrames, Series, loc/iloc, column selection

**Strava API**
- Read: [Strava API - List Athlete Activities](https://developers.strava.com/docs/reference/#api-Activities-getLoggedInAthleteActivities)
- Understand: Pagination, activity types, available fields

### Building (3 hrs)

**Task 1: Fetch Activities**

Build `fetch_data.py` that:
1. Loads access token from storage
2. Fetches all running activities (handle pagination - Strava returns max 200 per page)
3. Returns raw JSON data

```python
def fetch_all_activities(access_token: str, activity_type: str = "Run") -> list[dict]:
    """Fetch all activities of a given type from Strava."""
    # Implement pagination loop
    # Filter by activity_type
    pass
```

**Task 2: Initial DataFrame**

In `processor.py`, start loading data:
```python
import pandas as pd

def load_activities_to_df(activities: list[dict]) -> pd.DataFrame:
    """Convert raw Strava JSON to a DataFrame."""
    df = pd.DataFrame(activities)
    # Select relevant columns: name, distance, moving_time, elapsed_time,
    # total_elevation_gain, start_date, average_speed, average_heartrate, etc.
    return df
```

**Expected output:** A DataFrame with your recent runs, viewable in a Jupyter notebook or printed to console.

---

## Day 3: Data Cleaning + Feature Engineering

### Learning (2 hrs)

**Pandas Data Manipulation**
- Complete: [Kaggle - Summary Functions and Maps](https://www.kaggle.com/learn/pandas) (Lesson 3)
- Complete: [Kaggle - Grouping and Sorting](https://www.kaggle.com/learn/pandas) (Lesson 4)
- Key concepts: apply(), map(), groupby(), aggregation functions

### Building (4 hrs)

**Task 1: Data Cleaning**

Extend `processor.py`:
```python
def clean_activities(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and standardize activity data."""
    # 1. Filter to only runs (exclude walks, hikes, etc.)
    # 2. Convert distance: meters → miles
    # 3. Convert speed: m/s → minutes per mile (pace)
    # 4. Convert moving_time: seconds → minutes
    # 5. Parse start_date to datetime
    # 6. Handle missing heart rate data (some runs don't have HR)
    # 7. Remove outliers (runs < 0.5 miles, pace > 20 min/mile)
    pass
```

**Task 2: Feature Engineering**

```python
def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived features useful for prediction."""
    # 1. Add day_of_week
    # 2. Add week_number (for aggregation)
    # 3. Calculate elevation_per_mile
    # 4. Flag "long runs" (> 10 miles or > 90 minutes)
    # 5. Flag "workouts" (higher average HR or faster pace)
    pass
```

**Task 3: Weekly Aggregation**

```python
def aggregate_weekly(df: pd.DataFrame, weeks: int = 12) -> pd.DataFrame:
    """Aggregate runs into weekly summaries for the last N weeks."""
    # Group by week_number
    # Calculate per week:
    #   - total_miles
    #   - num_runs
    #   - avg_pace
    #   - avg_heart_rate
    #   - longest_run_miles
    #   - total_elevation_gain
    pass
```

**Expected output:** Clean DataFrame with engineered features + a weekly summary DataFrame showing training patterns.

---

## Day 4: Prediction Engine (Riegel's Formula)

### Learning (2 hrs)

**Running Science**
- Read: [Riegel's Formula Explained](https://runsmartproject.com/calculator/) (play with the calculator)
- Read: [The Science of Marathon Pacing](https://www.runnersworld.com/training/a20803307/marathon-pacing/)
- Key concepts: Fatigue factor (1.06), equivalent performances, why recent race results predict future ones

**Scikit-learn Basics**
- Read: [Scikit-learn - Getting Started](https://scikit-learn.org/stable/getting_started.html)
- Focus on: Linear regression section, understanding fit/predict pattern
- Key concepts: Training data, features vs target, model evaluation

### Building (4 hrs)

**Task 1: Riegel's Formula Implementation**

Create `predictor.py`:
```python
def riegel_prediction(known_distance: float, known_time: float, target_distance: float, fatigue_factor: float = 1.06) -> float:
    """
    Predict race time using Riegel's formula.

    Args:
        known_distance: Distance of known performance (miles)
        known_time: Time of known performance (minutes)
        target_distance: Distance to predict (miles)
        fatigue_factor: Typically 1.06, higher = more fatigue

    Returns:
        Predicted time in minutes
    """
    return known_time * (target_distance / known_distance) ** fatigue_factor
```

**Task 2: Find Best Predictor Run**

```python
def find_best_predictor_run(df: pd.DataFrame) -> dict:
    """
    Find the best recent run to use for prediction.

    Prioritize:
    1. Recent races (if any flagged)
    2. Long runs (> 10 miles) from last 4 weeks
    3. Fastest tempo effort from last 4 weeks

    Returns dict with distance, time, date, type
    """
    pass
```

**Task 3: Consistency Score (sklearn)**

```python
from sklearn.linear_model import LinearRegression
import numpy as np

def calculate_consistency_score(weekly_df: pd.DataFrame) -> float:
    """
    Calculate training consistency score (0-100).

    Uses standard deviation of weekly mileage and a simple
    linear regression to detect trend direction.

    Consistent, gradually increasing mileage = high score
    Erratic, wildly varying mileage = low score
    """
    # Calculate coefficient of variation (std/mean)
    # Fit linear regression to detect trend
    # Combine into a 0-100 score
    pass

def adjust_prediction_for_consistency(base_prediction: float, consistency_score: float) -> tuple[float, float]:
    """
    Adjust Riegel prediction based on training consistency.

    Returns (adjusted_time, confidence_range)
    - Low consistency = slower prediction, wider range
    - High consistency = trust base prediction, narrow range
    """
    pass
```

**Expected output:** Given your Strava data, predict your marathon (or half marathon) time with a confidence range.

---

## Day 5: Weather API + Pydantic Models

### Learning (1.5 hrs)

**Pydantic Basics**
- Read: [Pydantic Docs - Models](https://docs.pydantic.dev/latest/concepts/models/)
- Key concepts: Type validation, default values, nested models
- Why it matters: Catch data errors early, self-documenting code, FastAPI integration

**Weather API**
- Read: [OpenWeather API Docs](https://openweathermap.org/api/one-call-3)
- Understand: Current weather vs forecast, units, relevant fields for running

### Building (4 hrs)

**Task 1: Pydantic Models**

Create `models.py`:
```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class RunActivity(BaseModel):
    """Single run activity from Strava."""
    id: int
    name: str
    distance_miles: float = Field(ge=0)
    moving_time_minutes: float = Field(ge=0)
    pace_per_mile: float
    start_date: datetime
    total_elevation_gain_feet: float = 0
    average_heartrate: Optional[float] = None
    is_long_run: bool = False
    is_workout: bool = False

class WeeklySummary(BaseModel):
    """Aggregated weekly training summary."""
    week_start: datetime
    total_miles: float
    num_runs: int
    avg_pace: float
    longest_run: float
    total_elevation: float
    avg_heartrate: Optional[float] = None

class RunnerProfile(BaseModel):
    """Complete runner profile for strategy generation."""
    recent_weeks: list[WeeklySummary]
    avg_weekly_mileage: float
    consistency_score: float
    best_predictor_run: RunActivity
    predicted_marathon_time: float
    prediction_confidence_range: tuple[float, float]

class WeatherConditions(BaseModel):
    """Race day weather forecast."""
    temperature_f: float
    humidity_percent: float
    wind_speed_mph: float
    wind_direction: str
    conditions: str  # "clear", "cloudy", "rain", etc.
    feels_like_f: float

class RaceInfo(BaseModel):
    """Basic race information."""
    name: str
    distance_miles: float
    date: datetime
    location: str
    weather: Optional[WeatherConditions] = None
```

**Task 2: Weather Integration**

Create `weather.py`:
```python
def fetch_weather_forecast(lat: float, lon: float, date: datetime) -> WeatherConditions:
    """
    Fetch weather forecast for race location and date.

    Note: Free tier only provides ~5 days forecast.
    For races further out, return None or use historical averages.
    """
    pass

def assess_weather_impact(weather: WeatherConditions) -> dict:
    """
    Assess how weather will impact race performance.

    Returns adjustment factors and recommendations:
    - pace_adjustment: percentage slower/faster
    - hydration_level: "normal", "increased", "critical"
    - clothing_recommendation: string
    - risk_factors: list of warnings
    """
    # Hot weather (>70°F): pace slows ~2% per 10°F above 55°F
    # Humidity >80%: additional slowdown
    # Headwind: ~1-2% slowdown per 10mph
    # Rain: minimal impact on pace, but gear considerations
    pass
```

**Expected output:** Type-safe models for all data flowing through the system + weather impact assessment.

---

## Day 6: Integration + Module Structure

### Building (5 hrs)

**Task 1: Create Main Pipeline**

Create `backend/pipeline.py`:
```python
from backend.auth_flow import get_valid_token
from backend.fetch_data import fetch_all_activities
from backend.processor import load_activities_to_df, clean_activities, engineer_features, aggregate_weekly
from backend.predictor import find_best_predictor_run, riegel_prediction, calculate_consistency_score, adjust_prediction_for_consistency
from backend.models import RunnerProfile, RaceInfo
from backend.weather import fetch_weather_forecast, assess_weather_impact

def build_runner_profile(access_token: str) -> RunnerProfile:
    """
    Complete pipeline: Fetch → Clean → Analyze → Profile

    This is the main entry point that Week 2's AI agents will use.
    """
    # 1. Fetch activities
    raw_activities = fetch_all_activities(access_token)

    # 2. Process into DataFrame
    df = load_activities_to_df(raw_activities)
    df = clean_activities(df)
    df = engineer_features(df)

    # 3. Aggregate weekly
    weekly_df = aggregate_weekly(df, weeks=12)

    # 4. Calculate predictions
    best_run = find_best_predictor_run(df)
    base_prediction = riegel_prediction(
        best_run['distance'],
        best_run['time'],
        target_distance=26.2  # Marathon
    )
    consistency = calculate_consistency_score(weekly_df)
    adjusted_time, confidence = adjust_prediction_for_consistency(base_prediction, consistency)

    # 5. Build profile
    return RunnerProfile(
        recent_weeks=[...],  # Convert weekly_df to list of WeeklySummary
        avg_weekly_mileage=weekly_df['total_miles'].mean(),
        consistency_score=consistency,
        best_predictor_run=best_run,
        predicted_marathon_time=adjusted_time,
        prediction_confidence_range=confidence
    )

def prepare_race_context(profile: RunnerProfile, race: RaceInfo) -> dict:
    """
    Combine runner profile with race info for AI context.

    This dict will be injected into the AI prompt in Week 2.
    """
    weather_impact = None
    if race.weather:
        weather_impact = assess_weather_impact(race.weather)

    return {
        "runner": profile.model_dump(),
        "race": race.model_dump(),
        "weather_impact": weather_impact,
        "generated_at": datetime.now().isoformat()
    }
```

**Task 2: Test the Pipeline**

Create `test_pipeline.py` (simple manual test, not pytest):
```python
"""Manual integration test - run to verify pipeline works."""
from backend.pipeline import build_runner_profile, prepare_race_context
from backend.models import RaceInfo
from datetime import datetime

def main():
    # Get token (will prompt OAuth if needed)
    from backend.auth_flow import get_valid_token
    token = get_valid_token()

    # Build profile
    profile = build_runner_profile(token)

    print("=== Runner Profile ===")
    print(f"Avg Weekly Mileage: {profile.avg_weekly_mileage:.1f} miles")
    print(f"Consistency Score: {profile.consistency_score:.0f}/100")
    print(f"Predicted Marathon: {profile.predicted_marathon_time:.0f} minutes")
    print(f"Confidence Range: {profile.prediction_confidence_range}")

    # Test with sample race
    race = RaceInfo(
        name="Sample Marathon",
        distance_miles=26.2,
        date=datetime(2025, 4, 15),
        location="Boston, MA"
    )

    context = prepare_race_context(profile, race)
    print("\n=== Race Context (for AI) ===")
    print(context)

if __name__ == "__main__":
    main()
```

**Task 3: Clean Up and Document**

1. Add docstrings to all functions
2. Update `requirements.txt` with all dependencies:
   ```
   requests
   python-dotenv
   pydantic
   pandas
   scikit-learn
   ```
3. Update README.md with:
   - Project overview
   - Setup instructions
   - How to run the pipeline
   - Environment variables needed

---

## Day 7: Buffer + Review

**Time:** 4 hrs (flexible)

Use this day for:
- Catching up on anything that took longer than expected
- Refactoring messy code from rapid development
- Additional Kaggle pandas exercises if you want more practice
- Reading ahead on Week 2 topics (embeddings, RAG)

### Code Review Checklist

Before moving to Week 2, verify:

- [ ] `python backend/auth_flow.py` successfully authorizes and saves tokens
- [ ] `python test_pipeline.py` runs end-to-end without errors
- [ ] All Pydantic models validate correctly
- [ ] Weather API returns sensible data
- [ ] Prediction seems reasonable for your fitness level
- [ ] No hardcoded values (all config in .env)
- [ ] Code is organized into logical modules
- [ ] Basic error handling (what happens if Strava is down?)

---

## Week 1 Deliverables

By end of week, you should have:

1. **Working OAuth flow** - Can authenticate with Strava and refresh tokens
2. **Data pipeline** - Fetches, cleans, and aggregates running data
3. **Prediction engine** - Riegel's formula + consistency adjustment
4. **Weather integration** - Can fetch and assess race day conditions
5. **Type-safe models** - Pydantic models for all data structures
6. **Clean module structure** - Ready for Week 2's AI integration

### Sample Output

Running `test_pipeline.py` should produce something like:
```
=== Runner Profile ===
Avg Weekly Mileage: 32.4 miles
Consistency Score: 78/100
Predicted Marathon: 212 minutes (3:32)
Confidence Range: (205, 222) minutes

=== Race Context (for AI) ===
{
  "runner": { ... },
  "race": { ... },
  "weather_impact": {
    "pace_adjustment": 1.03,
    "hydration_level": "increased",
    "risk_factors": ["Temperature above 65°F"]
  }
}
```

---

## Learning Resources Summary

| Resource | Time | When |
|----------|------|------|
| [Real Python - Virtual Environments](https://realpython.com/python-virtual-environments-primer/) | 30 min | Day 1 |
| [DigitalOcean - OAuth 2 Intro](https://www.digitalocean.com/community/tutorials/an-introduction-to-oauth-2) | 45 min | Day 1 |
| [Strava Auth Docs](https://developers.strava.com/docs/authentication/) | 30 min | Day 1 |
| [Kaggle Pandas Course](https://www.kaggle.com/learn/pandas) (Lessons 1-4) | 3 hrs | Days 2-3 |
| [Scikit-learn Getting Started](https://scikit-learn.org/stable/getting_started.html) | 1 hr | Day 4 |
| [Pydantic Docs - Models](https://docs.pydantic.dev/latest/concepts/models/) | 45 min | Day 5 |
| [OpenWeather API Docs](https://openweathermap.org/api/one-call-3) | 30 min | Day 5 |

**Total structured learning: ~8-9 hours**

---

## Next Week Preview

Week 2 will take the `RunnerProfile` and `RaceInfo` you built here and feed them into a multi-agent AI system:
- **Pacing Agent** - Uses your prediction + course elevation to plan splits
- **Nutrition Agent** - Plans fueling strategy based on duration and conditions
- **Mental Prep Agent** - Provides visualization cues and mantras

The clean data pipeline you built this week is what makes the AI actually useful instead of generic.
