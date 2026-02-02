# Week 3: Backend System + Database (Simplified)

**Goal:** Wrap the AI agent in a production-ready API with GPX course analysis, PostgreSQL persistence for users/preferences/strategies, and deploy to Railway.

**Time Budget:** ~30 hours
- Learning: 4-6 hours
- Building: 24-26 hours

---

## Prerequisites

Before starting, ensure you have:
- Week 2 complete with working `RaceCoachAgent`
- Railway account from https://railway.app
- Add to `.env`:
  ```
  DATABASE_URL=postgresql://...  # Railway will provide this
  ```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI Backend                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  GET  /auth/strava/url        ← Get OAuth URL                   │
│  POST /auth/strava/callback   ← Exchange code for token         │
│  POST /course/analyze-gpx     ← GPX upload → elevation analysis │
│  POST /strategy/generate      ← Full strategy generation        │
│  GET  /strategy/{id}          ← Retrieve saved strategy         │
│  GET  /user/preferences       ← Get user preferences            │
│  PUT  /user/preferences       ← Update user preferences         │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ GPX Parser   │  │ Race Coach   │  │ Weather      │          │
│  │ (elevation)  │  │   Agent      │  │ Service      │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                        PostgreSQL                                │
│  users | user_preferences | strategies                           │
└─────────────────────────────────────────────────────────────────┘
```

**What We're NOT Building (Cut for simplicity):**
- ❌ Vision/image analysis (GPT-4V)
- ❌ Semantic caching layer
- ❌ Mapbox elevation API (use GPX data directly)
- ❌ Streaming endpoints

---

## Day 1: FastAPI Fundamentals + Project Setup

### Learning (2 hrs)

**FastAPI Essentials**
- Read: [FastAPI - First Steps](https://fastapi.tiangolo.com/tutorial/first-steps/)
- Read: [FastAPI - Request Body](https://fastapi.tiangolo.com/tutorial/body/)
- Read: [FastAPI - File Uploads](https://fastapi.tiangolo.com/tutorial/request-files/)
- Key concepts: Automatic validation, OpenAPI docs, async/await

**Why FastAPI:**
- Native async support (important for AI calls)
- Pydantic integration (you already have models)
- Auto-generated Swagger docs at `/docs`
- Type hints = fewer bugs

### Building (4 hrs)

**Task 1: Install Dependencies**

```bash
pip install fastapi uvicorn python-multipart gpxpy asyncpg
pip freeze > requirements.txt
```

**Task 2: Create API Structure**

```
backend/
├── api/
│   ├── __init__.py
│   ├── main.py              # FastAPI app + CORS
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py          # Strava OAuth endpoints
│   │   ├── course.py        # GPX analysis
│   │   ├── strategy.py      # Strategy generation
│   │   └── user.py          # User preferences
│   └── schemas.py           # Request/response models
```

**Task 3: Basic FastAPI Setup**

Create `backend/api/main.py`:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.api.routes import auth, course, strategy, user
from backend.database.db import init_db, close_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    print("Starting Race Coach API...")
    await init_db()
    yield
    print("Shutting down...")
    await close_db()

app = FastAPI(
    title="Race Coach API",
    description="AI-powered race strategy generator",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
# In production, replace with your Vercel domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(course.router, prefix="/course", tags=["Course Analysis"])
app.include_router(strategy.router, prefix="/strategy", tags=["Strategy"])
app.include_router(user.router, prefix="/user", tags=["User"])

@app.get("/health")
async def health_check():
    """Health check endpoint for Railway."""
    return {"status": "healthy", "version": "1.0.0"}

# Run with: uvicorn backend.api.main:app --reload
```

**Task 4: Create Request/Response Schemas**

Create `backend/api/schemas.py`:
```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# ============== Auth Schemas ==============

class StravaAuthRequest(BaseModel):
    code: str = Field(..., description="Authorization code from Strava OAuth")

class StravaAuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_at: int
    athlete_id: int

# ============== Course Schemas ==============

class ElevationPoint(BaseModel):
    mile: float
    elevation_ft: float
    grade_percent: float

class CourseAnalysis(BaseModel):
    total_distance_miles: float
    total_elevation_gain_ft: float
    total_elevation_loss_ft: float
    elevation_profile: list[ElevationPoint]
    difficulty_rating: str  # "easy", "moderate", "hard", "very_hard"
    key_segments: list[dict]  # Notable hills, flats, descents

# ============== Strategy Schemas ==============

class RaceInfoRequest(BaseModel):
    name: str
    distance_miles: float
    date: datetime
    location: str

class GenerateStrategyRequest(BaseModel):
    race_info: RaceInfoRequest
    course_analysis: Optional[CourseAnalysis] = None

class StrategyResponse(BaseModel):
    id: str
    race_name: str
    generated_at: datetime
    strategy_content: str  # Full markdown strategy
    course_analysis: Optional[CourseAnalysis] = None
    predicted_finish_time: Optional[float] = None

# ============== User Schemas ==============

class UserPreference(BaseModel):
    key: str
    value: str

class UserPreferencesResponse(BaseModel):
    preferences: dict[str, str]
```

**Task 5: Test the Setup**

```bash
uvicorn backend.api.main:app --reload
# Visit http://localhost:8000/docs to see Swagger UI
```

**Expected output:** FastAPI running with Swagger docs showing your endpoints.

---

## Day 2: GPX Parsing + Course Analysis

### Learning (1 hr)

**GPX Format**
- GPX files contain track points (trkpt) with lat/long/elevation
- Most race GPX files from Strava/Garmin include elevation
- We'll extract elevation directly from the file (no Mapbox needed)

### Building (4 hrs)

**Task 1: Create Course Analyzer**

Create `backend/course/analyzer.py`:
```python
import gpxpy
import math
from backend.api.schemas import CourseAnalysis, ElevationPoint

METERS_TO_FEET = 3.28084
METERS_TO_MILES = 0.000621371

def parse_gpx(file_content: bytes) -> CourseAnalysis:
    """
    Parse GPX file and extract elevation profile.

    Returns CourseAnalysis with mile-by-mile elevation data.
    """
    gpx = gpxpy.parse(file_content.decode('utf-8'))

    # Extract all points with cumulative distance
    points = []
    total_distance_m = 0
    prev_point = None

    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                if prev_point:
                    total_distance_m += _haversine_distance(
                        prev_point.latitude, prev_point.longitude,
                        point.latitude, point.longitude
                    )

                points.append({
                    "distance_m": total_distance_m,
                    "elevation_m": point.elevation or 0
                })
                prev_point = point

    total_distance_miles = total_distance_m * METERS_TO_MILES

    # Sample at each mile marker
    elevation_profile = []
    current_mile = 1

    for point in points:
        point_miles = point["distance_m"] * METERS_TO_MILES
        if point_miles >= current_mile and current_mile <= total_distance_miles:
            elevation_ft = point["elevation_m"] * METERS_TO_FEET
            elevation_profile.append({
                "mile": current_mile,
                "elevation_ft": round(elevation_ft, 1),
                "elevation_m": point["elevation_m"]
            })
            current_mile += 1

    # Calculate elevation changes and grades
    total_gain_ft = 0
    total_loss_ft = 0
    elevation_points = []

    for i, marker in enumerate(elevation_profile):
        if i == 0:
            grade = 0
        else:
            elevation_change = marker["elevation_ft"] - elevation_profile[i-1]["elevation_ft"]
            grade = (elevation_change / 5280) * 100  # Grade as percentage

            if elevation_change > 0:
                total_gain_ft += elevation_change
            else:
                total_loss_ft += abs(elevation_change)

        elevation_points.append(ElevationPoint(
            mile=marker["mile"],
            elevation_ft=marker["elevation_ft"],
            grade_percent=round(grade, 1)
        ))

    # Identify key segments
    key_segments = _identify_key_segments(elevation_points)

    # Calculate difficulty
    difficulty = _calculate_difficulty(total_gain_ft, total_distance_miles)

    return CourseAnalysis(
        total_distance_miles=round(total_distance_miles, 2),
        total_elevation_gain_ft=round(total_gain_ft),
        total_elevation_loss_ft=round(total_loss_ft),
        elevation_profile=elevation_points,
        difficulty_rating=difficulty,
        key_segments=key_segments
    )


def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two GPS points in meters."""
    R = 6371000  # Earth's radius in meters

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def _identify_key_segments(profile: list[ElevationPoint]) -> list[dict]:
    """Identify notable hills, flats, and descents."""
    segments = []

    for point in profile:
        if point.grade_percent > 3:
            segments.append({
                "mile": point.mile,
                "type": "uphill",
                "grade": point.grade_percent,
                "advice": f"Mile {point.mile}: Climb ({point.grade_percent}% grade). Ease back on pace, maintain effort."
            })
        elif point.grade_percent < -3:
            segments.append({
                "mile": point.mile,
                "type": "downhill",
                "grade": point.grade_percent,
                "advice": f"Mile {point.mile}: Descent ({point.grade_percent}% grade). Control pace, don't hammer quads."
            })

    return segments


def _calculate_difficulty(total_gain_ft: float, distance_miles: float) -> str:
    """Rate course difficulty based on elevation gain per mile."""
    if distance_miles == 0:
        return "unknown"

    gain_per_mile = total_gain_ft / distance_miles

    if gain_per_mile < 30:
        return "easy"
    elif gain_per_mile < 60:
        return "moderate"
    elif gain_per_mile < 100:
        return "hard"
    else:
        return "very_hard"
```

**Task 2: Create Course Routes**

Create `backend/api/routes/course.py`:
```python
from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.api.schemas import CourseAnalysis
from backend.course.analyzer import parse_gpx

router = APIRouter()

@router.post("/analyze-gpx", response_model=CourseAnalysis)
async def analyze_gpx_file(file: UploadFile = File(...)):
    """
    Upload and analyze a GPX file.

    Returns elevation profile, difficulty rating, and key segments.
    """
    if not file.filename.endswith('.gpx'):
        raise HTTPException(status_code=400, detail="File must be a .gpx file")

    try:
        content = await file.read()
        analysis = parse_gpx(content)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse GPX: {str(e)}")
```

**Expected output:** Upload a GPX file → receive elevation analysis with difficulty rating.

---

## Day 3: Database Setup + User Preferences

### Learning (1 hr)

**asyncpg Basics**
- Read: [asyncpg - Getting Started](https://magicstack.github.io/asyncpg/current/)
- Key concepts: Connection pools, parameterized queries, transactions

### Building (5 hrs)

**Task 1: Create Database Module**

Create `backend/database/db.py`:
```python
import asyncpg
import os
from typing import Optional
import json

# Connection pool (initialized on startup)
pool: Optional[asyncpg.Pool] = None

async def init_db():
    """Initialize database connection pool and create tables."""
    global pool
    pool = await asyncpg.create_pool(
        os.getenv("DATABASE_URL"),
        min_size=2,
        max_size=10
    )

    async with pool.acquire() as conn:
        # Users table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                strava_athlete_id BIGINT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        # User preferences table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                preference_key VARCHAR(100) NOT NULL,
                preference_value TEXT,
                updated_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(user_id, preference_key)
            )
        """)

        # Strategies table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS strategies (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id INTEGER REFERENCES users(id),
                race_name VARCHAR(255) NOT NULL,
                race_distance_miles FLOAT NOT NULL,
                race_date DATE,
                strategy_content TEXT NOT NULL,
                course_analysis JSONB,
                weather_data JSONB,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

    print("Database initialized")


async def close_db():
    """Close database connection pool."""
    global pool
    if pool:
        await pool.close()


# ============== User Operations ==============

async def get_or_create_user(strava_athlete_id: int) -> int:
    """Get or create user by Strava athlete ID. Returns user_id."""
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id FROM users WHERE strava_athlete_id = $1",
            strava_athlete_id
        )

        if row:
            return row["id"]

        row = await conn.fetchrow(
            "INSERT INTO users (strava_athlete_id) VALUES ($1) RETURNING id",
            strava_athlete_id
        )
        return row["id"]


# ============== Preferences Operations ==============

async def get_user_preferences(user_id: int) -> dict[str, str]:
    """Get all preferences for a user."""
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT preference_key, preference_value FROM user_preferences WHERE user_id = $1",
            user_id
        )
        return {row["preference_key"]: row["preference_value"] for row in rows}


async def set_user_preference(user_id: int, key: str, value: str) -> None:
    """Set a single user preference (upsert)."""
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO user_preferences (user_id, preference_key, preference_value, updated_at)
            VALUES ($1, $2, $3, NOW())
            ON CONFLICT (user_id, preference_key)
            DO UPDATE SET preference_value = $3, updated_at = NOW()
        """, user_id, key, value)


async def set_user_preferences(user_id: int, preferences: dict[str, str]) -> None:
    """Set multiple user preferences."""
    for key, value in preferences.items():
        await set_user_preference(user_id, key, value)


# ============== Strategy Operations ==============

async def save_strategy(
    user_id: int,
    race_name: str,
    race_distance: float,
    race_date,
    strategy_content: str,
    course_analysis: dict = None,
    weather_data: dict = None
) -> str:
    """Save a generated strategy. Returns strategy ID."""
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO strategies
            (user_id, race_name, race_distance_miles, race_date, strategy_content, course_analysis, weather_data)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id
        """,
            user_id, race_name, race_distance, race_date,
            strategy_content,
            json.dumps(course_analysis) if course_analysis else None,
            json.dumps(weather_data) if weather_data else None
        )
        return str(row["id"])


async def get_strategy(strategy_id: str) -> Optional[dict]:
    """Get a strategy by ID."""
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM strategies WHERE id = $1",
            strategy_id
        )
        if row:
            return dict(row)
        return None


async def get_user_strategies(user_id: int, limit: int = 10) -> list[dict]:
    """Get recent strategies for a user."""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, race_name, race_distance_miles, race_date, created_at
            FROM strategies
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT $2
        """, user_id, limit)
        return [dict(row) for row in rows]
```

**Task 2: Create User Routes**

Create `backend/api/routes/user.py`:
```python
from fastapi import APIRouter, HTTPException, Depends
from backend.api.schemas import UserPreference, UserPreferencesResponse
from backend.database.db import get_user_preferences, set_user_preferences

router = APIRouter()

# TODO: In production, get user_id from auth token
# For now, accept it as a parameter

@router.get("/preferences", response_model=UserPreferencesResponse)
async def get_preferences(user_id: int):
    """Get all preferences for a user."""
    preferences = await get_user_preferences(user_id)
    return UserPreferencesResponse(preferences=preferences)


@router.put("/preferences")
async def update_preferences(user_id: int, preferences: dict[str, str]):
    """Update user preferences."""
    await set_user_preferences(user_id, preferences)
    return {"status": "updated"}
```

---

## Day 4: Strategy Generation Endpoint

### Building (5 hrs)

**Task 1: Create Auth Routes**

Create `backend/api/routes/auth.py`:
```python
from fastapi import APIRouter, HTTPException
from backend.api.schemas import StravaAuthRequest, StravaAuthResponse
import os
import httpx

router = APIRouter()

@router.get("/strava/url")
async def get_strava_auth_url():
    """Get the Strava OAuth authorization URL."""
    client_id = os.getenv("STRAVA_CLIENT_ID")
    redirect_uri = os.getenv("STRAVA_REDIRECT_URI")

    auth_url = (
        f"https://www.strava.com/oauth/authorize"
        f"?client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&scope=activity:read_all"
    )

    return {"auth_url": auth_url}


@router.post("/strava/callback", response_model=StravaAuthResponse)
async def strava_callback(request: StravaAuthRequest):
    """Exchange authorization code for access token."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://www.strava.com/oauth/token",
            data={
                "client_id": os.getenv("STRAVA_CLIENT_ID"),
                "client_secret": os.getenv("STRAVA_CLIENT_SECRET"),
                "code": request.code,
                "grant_type": "authorization_code"
            }
        )

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to exchange code")

    data = response.json()
    return StravaAuthResponse(
        access_token=data["access_token"],
        refresh_token=data["refresh_token"],
        expires_at=data["expires_at"],
        athlete_id=data["athlete"]["id"]
    )
```

**Task 2: Create Strategy Routes**

Create `backend/api/routes/strategy.py`:
```python
from fastapi import APIRouter, HTTPException
from backend.api.schemas import (
    GenerateStrategyRequest, StrategyResponse, CourseAnalysis
)
from backend.agent import agent
from backend.pipeline import build_runner_profile
from backend.weather import get_weather_forecast
from backend.database.db import (
    get_or_create_user, get_user_preferences, save_strategy, get_strategy
)
from datetime import datetime

router = APIRouter()

@router.post("/generate", response_model=StrategyResponse)
async def generate_strategy(
    request: GenerateStrategyRequest,
    strava_token: str,
    strava_athlete_id: int
):
    """
    Generate a complete race strategy.

    Requires Strava token for runner profile data.
    """
    try:
        # Get or create user
        user_id = await get_or_create_user(strava_athlete_id)

        # Get user preferences
        preferences = await get_user_preferences(user_id)

        # Build runner profile from Strava
        profile = build_runner_profile()  # Uses stored token

        # Convert profile to dict for agent
        profile_dict = {
            "vdot_max": max(
                (w.vdot_max for w in profile.recent_weeks if w.vdot_max),
                default=None
            ),
            "avg_weekly_mileage": profile.avg_weekly_mileage,
            "coefficient_of_variance": profile.coefficient_of_variance,
            "predicted_race_times": [
                {"race": p.race, "ideal_time": p.ideal_time}
                for p in (profile.predicted_race_times or [])
            ]
        }

        # Get weather if we have location
        weather = None
        if request.race_info.location:
            try:
                # Use your existing weather module
                weather = {
                    "temperature_f": 55,  # TODO: actual weather API call
                    "feels_like_f": 52,
                    "wind_speed_mph": 8,
                    "conditions": "Partly cloudy"
                }
            except Exception:
                pass  # Weather is optional

        # Convert course analysis if provided
        course_dict = None
        if request.course_analysis:
            course_dict = {
                "total_elevation_gain_ft": request.course_analysis.total_elevation_gain_ft,
                "difficulty_rating": request.course_analysis.difficulty_rating,
                "key_segments": request.course_analysis.key_segments
            }

        # Generate strategy with agent
        race_info_dict = {
            "name": request.race_info.name,
            "distance_miles": request.race_info.distance_miles,
            "date": request.race_info.date.isoformat(),
            "location": request.race_info.location
        }

        strategy_content = agent.generate_strategy(
            runner_profile=profile_dict,
            race_info=race_info_dict,
            weather=weather,
            course_analysis=course_dict,
            user_preferences=preferences
        )

        # Save to database
        strategy_id = await save_strategy(
            user_id=user_id,
            race_name=request.race_info.name,
            race_distance=request.race_info.distance_miles,
            race_date=request.race_info.date,
            strategy_content=strategy_content,
            course_analysis=course_dict,
            weather_data=weather
        )

        # Extract predicted time from profile
        predicted_time = None
        if profile_dict["predicted_race_times"]:
            # Find matching distance or closest
            for pred in profile_dict["predicted_race_times"]:
                if pred["race"] == "marathon" and request.race_info.distance_miles > 20:
                    predicted_time = pred["ideal_time"]
                elif pred["race"] == "half_marathon" and 10 < request.race_info.distance_miles <= 20:
                    predicted_time = pred["ideal_time"]
                elif pred["race"] == "10K" and 5 < request.race_info.distance_miles <= 10:
                    predicted_time = pred["ideal_time"]
                elif pred["race"] == "5K" and request.race_info.distance_miles <= 5:
                    predicted_time = pred["ideal_time"]

        return StrategyResponse(
            id=strategy_id,
            race_name=request.race_info.name,
            generated_at=datetime.now(),
            strategy_content=strategy_content,
            course_analysis=request.course_analysis,
            predicted_finish_time=predicted_time
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy_by_id(strategy_id: str):
    """Retrieve a previously generated strategy."""
    strategy = await get_strategy(strategy_id)

    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    # Parse course analysis from JSON if present
    course_analysis = None
    if strategy.get("course_analysis"):
        course_analysis = CourseAnalysis(**strategy["course_analysis"])

    return StrategyResponse(
        id=str(strategy["id"]),
        race_name=strategy["race_name"],
        generated_at=strategy["created_at"],
        strategy_content=strategy["strategy_content"],
        course_analysis=course_analysis,
        predicted_finish_time=None
    )
```

---

## Day 5: Railway Deployment

### Learning (1 hr)

**Railway Basics**
- Read: [Railway - Getting Started](https://docs.railway.app/getting-started)
- Read: [Railway - Deploying Python](https://docs.railway.app/guides/python)

### Building (4 hrs)

**Task 1: Create Railway Configuration**

Create `railway.toml`:
```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
healthcheckTimeout = 100
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 3
```

**Task 2: Update Requirements**

Ensure `requirements.txt` includes:
```
fastapi>=0.109.0
uvicorn>=0.27.0
python-multipart>=0.0.6
pydantic>=2.5.0
pandas>=2.1.0
numpy>=1.26.0
requests>=2.31.0
python-dotenv>=1.0.0
openai>=1.10.0
gpxpy>=1.6.0
asyncpg>=0.29.0
httpx>=0.26.0
```

**Task 3: Deploy to Railway**

1. Create Railway account and project
2. Connect GitHub repository
3. Add Postgres plugin: Railway dashboard → New → Database → PostgreSQL
4. Configure environment variables:
   ```
   OPENAI_API_KEY=sk-...
   STRAVA_CLIENT_ID=...
   STRAVA_CLIENT_SECRET=...
   STRAVA_REDIRECT_URI=https://your-app.railway.app/auth/strava/callback
   DATABASE_URL=${{Postgres.DATABASE_URL}}
   ```
5. Deploy and get your Railway URL

**Task 4: Test Deployed API**

```bash
# Health check
curl https://your-app.railway.app/health

# View docs
open https://your-app.railway.app/docs
```

---

## Day 6-7: Testing + Polish

### Building (4-6 hrs)

**Task 1: End-to-End Testing**

Create `backend/tests/test_api.py`:
```python
"""Test API endpoints."""
import httpx
import asyncio

BASE_URL = "http://localhost:8000"  # Or Railway URL

async def test_health():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        print("✓ Health check passed")

async def test_gpx_upload():
    # Create minimal test GPX
    test_gpx = """<?xml version="1.0" encoding="UTF-8"?>
    <gpx version="1.1">
        <trk><trkseg>
            <trkpt lat="42.3601" lon="-71.0589"><ele>10</ele></trkpt>
            <trkpt lat="42.3611" lon="-71.0599"><ele>15</ele></trkpt>
            <trkpt lat="42.3621" lon="-71.0609"><ele>12</ele></trkpt>
        </trkseg></trk>
    </gpx>
    """

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/course/analyze-gpx",
            files={"file": ("test.gpx", test_gpx, "application/gpx+xml")}
        )
        assert response.status_code == 200
        data = response.json()
        assert "elevation_profile" in data
        print("✓ GPX upload passed")

async def run_tests():
    await test_health()
    await test_gpx_upload()
    print("\n✓ All tests passed!")

if __name__ == "__main__":
    asyncio.run(run_tests())
```

**Task 2: Code Review Checklist**

Before moving to Week 4, verify:
- [ ] `uvicorn backend.api.main:app --reload` runs locally
- [ ] Swagger docs at `/docs` show all endpoints
- [ ] GPX upload returns valid course analysis
- [ ] Strategy generation calls agent and saves to DB
- [ ] User preferences persist across requests
- [ ] Railway deployment is live and healthy
- [ ] No API keys exposed in responses

---

## Week 3 Deliverables

By end of week, you should have:

1. **FastAPI backend** with clean route structure
2. **GPX course analysis** with elevation profiling
3. **PostgreSQL persistence** for users, preferences, strategies
4. **Strategy generation endpoint** that ties everything together
5. **Live deployment** on Railway

### File Structure After Week 3

```
backend/
├── api/
│   ├── __init__.py
│   ├── main.py
│   ├── schemas.py
│   └── routes/
│       ├── __init__.py
│       ├── auth.py
│       ├── course.py
│       ├── strategy.py
│       └── user.py
├── agent/
│   └── ... (from Week 2)
├── course/
│   ├── __init__.py
│   └── analyzer.py
├── database/
│   ├── __init__.py
│   └── db.py
├── data_processing/
│   └── ... (from Week 1)
├── knowledge/
│   └── ... (from Week 2)
├── models.py
├── pipeline.py
├── weather.py
├── requirements.txt
└── railway.toml
```

### API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/auth/strava/url` | Get OAuth URL |
| POST | `/auth/strava/callback` | Exchange code for token |
| POST | `/course/analyze-gpx` | Upload and analyze GPX file |
| POST | `/strategy/generate` | Generate full strategy |
| GET | `/strategy/{id}` | Get saved strategy |
| GET | `/user/preferences` | Get user preferences |
| PUT | `/user/preferences` | Update user preferences |

---

## Learning Resources Summary

| Resource | Time | When |
|----------|------|------|
| [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/) | 2 hrs | Day 1 |
| [asyncpg Docs](https://magicstack.github.io/asyncpg/current/) | 1 hr | Day 3 |
| [Railway Getting Started](https://docs.railway.app/getting-started) | 1 hr | Day 5 |

**Total structured learning: ~4-5 hours**

---

## Next Week Preview

Week 4 will build the frontend:
- Next.js React frontend
- Elevation profile chart (Recharts)
- Strategy display with markdown rendering
- Browser-based PDF export
- Vercel deployment
