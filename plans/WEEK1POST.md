# Week 1 Post-Mortem: Data Engineering Foundation

**Completed:** February 1, 2026

---

## Summary

Week 1 focused on building the data pipeline that ingests Strava running data, processes it, and produces a `RunnerProfile` with race predictions. The core architecture was completed with some significant deviations from the original plan.

---

## What Was Built

### Data Pipeline

```
Strava API → fetch_data.py → raw_activities.json
                                    ↓
                            clean_data.py
                            - Filter to runs only
                            - Convert meters → miles
                            - Convert seconds → minutes
                            - Calculate pace (min/mile)
                            - Parse dates, group by week
                            - Calculate VDOT per activity
                                    ↓
                            categorize_activities.py
                            - Classify: Race / Long Run / Workout / Easy / Warmup
                            - Calculate pace & distance percentiles
                                    ↓
                            processor.py → aggregate_weekly()
                            - Weekly totals: miles, runs, time, elevation
                            - Weekly max VDOT
                            - Pace averages
                                    ↓
                            pipeline.py → RunnerProfile
                            - Last 12 calendar weeks
                            - Coefficient of variance
                            - Race predictions (5K, 10K, Half, Marathon)
```

### Files Created

| File | Purpose |
|------|---------|
| `backend/pipeline.py` | Main entry point - builds `RunnerProfile` |
| `backend/calculate_race_performances.py` | VDOT → race time predictions |
| `backend/models.py` | Pydantic models for type safety |
| `backend/weather.py` | OpenWeather API integration |
| `backend/auth_flow.py` | Strava OAuth 2.0 flow |
| `backend/fetch_data.py` | Strava API data fetching |
| `backend/data_processing/clean_data.py` | Data cleaning & unit conversion |
| `backend/data_processing/categorize_activities.py` | Run classification |
| `backend/data_processing/calculate_vdot.py` | VO2max fitness metric |
| `backend/data_processing/calculate_consistency.py` | Training consistency penalty |
| `backend/data_processing/processor.py` | Data loading & weekly aggregation |

---

## Key Deviations from Plan

### 1. VDOT Instead of Riegel's Formula

**Planned:** Use Riegel's formula (`T2 = T1 × (D2/D1)^1.06`) to predict race times from a single known performance.

**Implemented:** VDOT (VO2max-based) calculation using Jack Daniels' running formula:
- Calculate oxygen cost from velocity
- Calculate %VO2max sustainable at a given duration
- VDOT = VO2 cost / %VO2max

**Why:** VDOT is more sophisticated - it accounts for the physiological reality that the percentage of VO2max you can sustain decreases with duration. It's also what serious runners use.

**Trade-off:** VDOT requires solving numerically (binary search) to get race predictions, whereas Riegel is a direct calculation.

### 2. No `predictor.py` - Different Architecture

**Planned:** Single `predictor.py` with `riegel_prediction()`, `find_best_predictor_run()`, `calculate_consistency_score()`.

**Implemented:** Split across multiple files:
- `calculate_vdot.py` - VDOT calculation per activity
- `calculate_consistency.py` - CV-based consistency penalty
- `calculate_race_performances.py` - Combines VDOT + consistency for predictions

**Why:** Cleaner separation of concerns. VDOT is calculated per-activity during cleaning, not as a separate prediction step.

### 3. No "Best Predictor Run" Selection

**Planned:** Find the single best recent run (race > long run > tempo) to base predictions on.

**Implemented:** Use `vdot_max` across all weeks - the highest VDOT from any qualifying run in the past 12 weeks.

**Why:** Simpler and arguably more accurate. Your fitness is best represented by your best recent effort, regardless of which specific run it was.

### 4. VDOT Filtering for Accuracy

**Added (not in plan):** Filters to exclude activities that produce unreliable VDOT:
- Skip runs < 3.5 minutes (too anaerobic)
- Skip runs where `(elapsed_time - moving_time) / moving_time > 0.2` (interval workouts with rest)

**Why:** Short sprints (400m) and interval sessions were producing inflated VDOT values (70+ when actual fitness is ~45-50). The VDOT formula is only valid for continuous efforts of 3.5+ minutes.

### 5. Simplified RunnerProfile Model

**Planned:**
```python
class RunnerProfile:
    predicted_marathon_time: float
    prediction_confidence_range: tuple[float, float]
    best_predictor_run: RunActivity
```

**Implemented:**
```python
class RunnerProfile:
    predicted_race_times: list[RacePrediction]  # 5K, 10K, Half, Marathon
    # No confidence range
    # No best predictor run reference
```

**Why:** Predicting multiple distances is more useful. Confidence ranges can be added later based on CV.

### 6. 12 Calendar Weeks, Not 12 Training Weeks

**Clarified during implementation:** `recent_weeks` filters by date (`datetime.now() - timedelta(weeks=12)`) rather than taking the most recent 12 weeks with training data.

**Why:** If someone took 4 weeks off, that gap matters for fitness assessment. Calendar weeks reflect actual training recency.

---

## Technical Decisions

### Unit Handling

All internal calculations use:
- **Distance:** miles
- **Time:** minutes
- **Pace:** minutes per mile

Strava returns meters and seconds, converted in `clean_data.py`.

VDOT formulas expect meters per minute for velocity, so `calculate_vdot.py` converts miles back to meters.

### Activity Classification Logic

Priority order in `categorize_activities.py`:
1. User-set Strava tags (respected first)
2. Workout keywords (tempo, intervals, etc.)
3. Warmup/cooldown (by keyword or short+slow)
4. Easy runs (by keyword or short+moderate pace)
5. Races (by keyword, race distance, or fast pace)
6. Long runs (by distance percentile)
7. Default: "None"

Percentiles are calculated excluding warmups/cooldowns to avoid skewing.

### Weather Integration

Implemented but not yet integrated into `RunnerProfile`:
- Geocoding (city/state → lat/lon)
- 5-day forecast fetching
- Impact assessment (temperature, wind, risk factors)

Ready for Week 2 agents to use when given race info.

---

## Metrics

- **Files created:** 12 Python files
- **Pydantic models:** 7 (RunActivity, WeeklySummary, RacePrediction, RunnerProfile, WeatherConditions, WeatherImpact, RaceInfo)
- **External APIs integrated:** 2 (Strava, OpenWeather)
- **Unit conversions:** 4 (meters→miles, seconds→minutes, Fahrenheit→Celsius, meters/min velocity)

---

## Ready for Week 2

The pipeline produces a complete `RunnerProfile`:

```python
RunnerProfile(
    recent_weeks=[WeeklySummary(...)],  # Last 12 calendar weeks
    avg_weekly_mileage=25.5,
    coefficient_of_variance=0.35,
    predicted_race_times=[
        RacePrediction(race="5K", ideal_time=22.5, consistency_penalty=0.002),
        RacePrediction(race="10K", ideal_time=47.1, consistency_penalty=0.003),
        RacePrediction(race="half_marathon", ideal_time=104.2, consistency_penalty=0.005),
        RacePrediction(race="marathon", ideal_time=218.5, consistency_penalty=0.010)
    ]
)
```

This is the data structure Week 2's AI agents will consume to generate personalized race strategies.
