# Week 3: Backend System + Advanced AI

**Goal:** Wrap the AI system in a production-ready API with course analysis, vision input, caching, and database persistence. Deploy to Railway.

**Time Budget:** ~30 hours
- Learning: 6-8 hours
- Building: 22-24 hours

---

## Prerequisites

Before starting, ensure you have:
- Week 2 complete with working orchestrator
- Mapbox account (free tier) from https://www.mapbox.com
- Railway account from https://railway.app
- Add to `.env`:
  ```
  MAPBOX_ACCESS_TOKEN=pk.xxx
  DATABASE_URL=postgresql://...  # Railway will provide this
  ```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI Backend                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  POST /auth/strava          ← OAuth callback                     │
│  POST /analyze-course       ← GPX upload → elevation analysis    │
│  POST /analyze-image        ← Course photo → vision extraction   │
│  POST /generate-strategy    ← Full strategy generation           │
│  GET  /strategies/{id}      ← Retrieve saved strategy            │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │ Course       │  │ Semantic     │  │ Strategy     │           │
│  │ Analyzer     │  │ Cache        │  │ Generator    │           │
│  │ (Mapbox)     │  │ (Redis-like) │  │ (Orchestrator)│          │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                        PostgreSQL                                │
│  users | strategies | course_analyses                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Day 1: FastAPI Fundamentals + Project Setup

### Learning (3 hrs)

**FastAPI Essentials**
- Read: [FastAPI - First Steps](https://fastapi.tiangolo.com/tutorial/first-steps/)
- Read: [FastAPI - Path Parameters](https://fastapi.tiangolo.com/tutorial/path-params/)
- Read: [FastAPI - Request Body](https://fastapi.tiangolo.com/tutorial/body/)
- Read: [FastAPI - File Uploads](https://fastapi.tiangolo.com/tutorial/request-files/)
- Key concepts: Automatic validation, OpenAPI docs, async/await, dependency injection

**Why FastAPI over Flask/Express:**
- Native async support (important for AI calls that take seconds)
- Pydantic integration (you already have models from Week 1)
- Auto-generated Swagger docs at `/docs`
- Type hints = fewer bugs

### Building (3 hrs)

**Task 1: Install Dependencies**

```bash
pip install fastapi uvicorn python-multipart aiofiles
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
│   │   ├── course.py        # GPX + vision analysis
│   │   └── strategy.py      # Strategy generation
│   ├── dependencies.py      # Shared dependencies
│   └── schemas.py           # Request/response models
```

**Task 3: Basic FastAPI Setup**

Create `backend/api/main.py`:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from backend.api.routes import auth, course, strategy

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup: initialize connections
    print("Starting Race Coach API...")
    yield
    # Shutdown: cleanup
    print("Shutting down...")

app = FastAPI(
    title="Race Coach API",
    description="AI-powered race strategy generator",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
# In production, replace "*" with your Vercel domain
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
app.include_router(strategy.router, prefix="/strategy", tags=["Strategy Generation"])

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

class ImageAnalysisRequest(BaseModel):
    image_url: Optional[str] = None  # URL or base64

class ImageAnalysisResponse(BaseModel):
    extracted_info: dict
    confidence: float
    raw_description: str

# ============== Strategy Schemas ==============

class RaceInfoRequest(BaseModel):
    name: str
    distance_miles: float
    date: datetime
    location: str
    gpx_file_id: Optional[str] = None  # Reference to uploaded GPX
    course_image_id: Optional[str] = None  # Reference to analyzed image

class GenerateStrategyRequest(BaseModel):
    race_info: RaceInfoRequest
    access_token: str  # Strava token

class StrategyResponse(BaseModel):
    id: str
    race_name: str
    generated_at: datetime
    pacing_strategy: str
    nutrition_plan: str
    mental_preparation: str
    course_analysis: Optional[CourseAnalysis] = None
    predicted_finish_time: float

class StrategyListItem(BaseModel):
    id: str
    race_name: str
    generated_at: datetime
    distance_miles: float
```

**Task 5: Create Auth Routes**

Create `backend/api/routes/auth.py`:
```python
from fastapi import APIRouter, HTTPException
from backend.api.schemas import StravaAuthRequest, StravaAuthResponse
from backend.auth_flow import exchange_code_for_token, refresh_access_token
import os

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
    try:
        tokens = await exchange_code_for_token(request.code)
        return StravaAuthResponse(**tokens)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/strava/refresh", response_model=StravaAuthResponse)
async def refresh_token(refresh_token: str):
    """Refresh an expired access token."""
    try:
        tokens = await refresh_access_token(refresh_token)
        return StravaAuthResponse(**tokens)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

**Task 6: Test the Setup**

```bash
uvicorn backend.api.main:app --reload
# Visit http://localhost:8000/docs to see Swagger UI
```

**Expected output:** FastAPI running with Swagger docs showing your endpoints.

---

## Day 2: GPX Parsing + Course Analysis

### Learning (1 hr)

**GPX Format**
- Read: [GPX Format Overview](https://www.topografix.com/gpx.asp)
- Key concepts: Track points (trkpt), elevation, timestamps
- Most race GPX files contain lat/long/elevation for the entire course

**Mapbox Elevation API**
- Read: [Mapbox Tilequery API](https://docs.mapbox.com/api/maps/tilequery/)
- Alternative: Use GPX elevation directly if available
- Why Mapbox: GPS elevation is often inaccurate; Mapbox provides ground truth

### Building (4 hrs)

**Task 1: Install GPX Library**

```bash
pip install gpxpy
pip freeze > requirements.txt
```

**Task 2: Create Course Analyzer**

Create `backend/course/analyzer.py`:
```python
import gpxpy
import gpxpy.gpx
from typing import Optional
import math
import httpx
import os
from backend.api.schemas import CourseAnalysis, ElevationPoint

async def parse_gpx_file(file_content: bytes) -> dict:
    """
    Parse GPX file and extract track points.

    Returns dict with:
    - points: list of (lat, lon, elevation) tuples
    - total_distance_meters: float
    """
    gpx = gpxpy.parse(file_content.decode('utf-8'))

    points = []
    total_distance = 0
    prev_point = None

    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                points.append({
                    "lat": point.latitude,
                    "lon": point.longitude,
                    "elevation_m": point.elevation,
                    "distance_m": total_distance
                })

                if prev_point:
                    # Calculate distance between points
                    total_distance += _haversine_distance(
                        prev_point.latitude, prev_point.longitude,
                        point.latitude, point.longitude
                    )

                prev_point = point

    return {
        "points": points,
        "total_distance_meters": total_distance
    }

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

async def get_mapbox_elevation(lat: float, lon: float) -> Optional[float]:
    """Query Mapbox for accurate elevation at a point."""
    token = os.getenv("MAPBOX_ACCESS_TOKEN")

    url = (
        f"https://api.mapbox.com/v4/mapbox.mapbox-terrain-v2/tilequery/"
        f"{lon},{lat}.json"
        f"?layers=contour"
        f"&access_token={token}"
    )

    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code == 200:
            data = response.json()
            if data.get("features"):
                # Get the highest accuracy contour
                elevations = [f["properties"].get("ele", 0) for f in data["features"]]
                return max(elevations) if elevations else None

    return None

def analyze_course(points: list[dict], total_distance_m: float) -> CourseAnalysis:
    """
    Analyze course profile and generate insights.

    Calculates:
    - Mile-by-mile elevation
    - Total gain/loss
    - Difficulty rating
    - Key segments (hills, flats, descents)
    """
    total_distance_miles = total_distance_m * 0.000621371

    # Sample points at each mile marker
    mile_markers = []
    current_mile = 1

    for point in points:
        point_miles = point["distance_m"] * 0.000621371
        if point_miles >= current_mile and current_mile <= total_distance_miles:
            elevation_ft = (point["elevation_m"] or 0) * 3.28084
            mile_markers.append({
                "mile": current_mile,
                "elevation_ft": elevation_ft
            })
            current_mile += 1

    # Calculate elevation changes
    elevation_profile = []
    total_gain = 0
    total_loss = 0

    for i, marker in enumerate(mile_markers):
        if i == 0:
            grade = 0
        else:
            elevation_change = marker["elevation_ft"] - mile_markers[i-1]["elevation_ft"]
            grade = (elevation_change / 5280) * 100  # Grade as percentage

            if elevation_change > 0:
                total_gain += elevation_change
            else:
                total_loss += abs(elevation_change)

        elevation_profile.append(ElevationPoint(
            mile=marker["mile"],
            elevation_ft=marker["elevation_ft"],
            grade_percent=round(grade, 1)
        ))

    # Identify key segments
    key_segments = _identify_key_segments(elevation_profile)

    # Calculate difficulty rating
    difficulty = _calculate_difficulty(total_gain, total_distance_miles)

    return CourseAnalysis(
        total_distance_miles=round(total_distance_miles, 2),
        total_elevation_gain_ft=round(total_gain),
        total_elevation_loss_ft=round(total_loss),
        elevation_profile=elevation_profile,
        difficulty_rating=difficulty,
        key_segments=key_segments
    )

def _identify_key_segments(profile: list[ElevationPoint]) -> list[dict]:
    """Identify notable hills, flats, and descents."""
    segments = []

    for i, point in enumerate(profile):
        if point.grade_percent > 3:
            segments.append({
                "mile": point.mile,
                "type": "uphill",
                "grade": point.grade_percent,
                "advice": f"Mile {point.mile}: Significant climb ({point.grade_percent}% grade). Ease back on pace."
            })
        elif point.grade_percent < -3:
            segments.append({
                "mile": point.mile,
                "type": "downhill",
                "grade": point.grade_percent,
                "advice": f"Mile {point.mile}: Downhill ({point.grade_percent}% grade). Control pace, don't hammer quads."
            })

    return segments

def _calculate_difficulty(total_gain_ft: float, distance_miles: float) -> str:
    """Rate course difficulty based on elevation gain per mile."""
    gain_per_mile = total_gain_ft / distance_miles if distance_miles > 0 else 0

    if gain_per_mile < 30:
        return "easy"
    elif gain_per_mile < 60:
        return "moderate"
    elif gain_per_mile < 100:
        return "hard"
    else:
        return "very_hard"
```

**Task 3: Create Course Routes**

Create `backend/api/routes/course.py`:
```python
from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.api.schemas import CourseAnalysis, ImageAnalysisRequest, ImageAnalysisResponse
from backend.course.analyzer import parse_gpx_file, analyze_course
from backend.course.vision import analyze_course_image
import uuid

router = APIRouter()

# In-memory storage for demo (use database in production)
course_analyses: dict[str, CourseAnalysis] = {}

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
        parsed = await parse_gpx_file(content)
        analysis = analyze_course(parsed["points"], parsed["total_distance_meters"])

        # Store for later reference
        analysis_id = str(uuid.uuid4())
        course_analyses[analysis_id] = analysis

        return analysis

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse GPX: {str(e)}")

@router.post("/analyze-image", response_model=ImageAnalysisResponse)
async def analyze_course_image_endpoint(request: ImageAnalysisRequest):
    """
    Analyze a course map/elevation image using vision AI.

    Extracts key course features from photos or elevation charts.
    """
    try:
        result = await analyze_course_image(request.image_url)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Image analysis failed: {str(e)}")

@router.get("/analysis/{analysis_id}", response_model=CourseAnalysis)
async def get_course_analysis(analysis_id: str):
    """Retrieve a previously analyzed course."""
    if analysis_id not in course_analyses:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return course_analyses[analysis_id]
```

**Expected output:** Upload a GPX file → receive detailed elevation analysis with difficulty rating.

---

## Day 3: Multi-Modal Vision Input

### Learning (1.5 hrs)

**Vision APIs**
- Read: [OpenAI - Vision Guide](https://platform.openai.com/docs/guides/vision)
- Read: [Anthropic - Vision](https://docs.anthropic.com/en/docs/build-with-claude/vision)
- Key concepts: Base64 encoding, image URLs, prompt engineering for vision
- Use case: User uploads photo of course map or elevation chart

**Why Vision Matters:**
- Not all races have GPX files available
- Users might photograph the course map from a race guide
- Elevation profile screenshots from race websites
- Shows cutting-edge AI skills to employers

### Building (4 hrs)

**Task 1: Create Vision Analyzer**

Create `backend/course/vision.py`:
```python
from openai import OpenAI
import base64
import httpx
import os
from dotenv import load_dotenv
from backend.api.schemas import ImageAnalysisResponse

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

COURSE_ANALYSIS_PROMPT = """You are analyzing an image of a running race course. This could be:
- An elevation profile chart
- A course map
- A race brochure or flyer
- A screenshot from a race website

Extract as much relevant information as possible for race planning:

1. **Course Profile**: Is it hilly, flat, rolling? Any notable elevation changes?
2. **Key Landmarks**: Start/finish locations, major turns, aid stations if visible
3. **Distance Markers**: Any mile/km markers shown?
4. **Terrain**: Road, trail, mixed? Any notable surface changes?
5. **Potential Challenges**: Sharp turns, narrow sections, exposed areas?

Return your analysis in a structured format. Be specific about mile markers and elevation if visible.
If you cannot determine something from the image, say so explicitly.

Respond in JSON format:
{
    "course_type": "flat|rolling|hilly|mountainous",
    "estimated_elevation_gain_ft": number or null,
    "key_segments": [
        {"mile_range": "0-5", "description": "...", "difficulty": "easy|moderate|hard"}
    ],
    "landmarks": ["..."],
    "terrain_type": "road|trail|mixed",
    "notable_challenges": ["..."],
    "confidence_notes": "What you couldn't determine from the image"
}"""

async def analyze_course_image(image_source: str) -> ImageAnalysisResponse:
    """
    Analyze a course image using GPT-4 Vision.

    Args:
        image_source: Either a URL or base64-encoded image data

    Returns:
        ImageAnalysisResponse with extracted course information
    """
    # Determine if URL or base64
    if image_source.startswith("http"):
        image_content = {"type": "image_url", "image_url": {"url": image_source}}
    else:
        # Assume base64
        image_content = {
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{image_source}"}
        }

    response = client.chat.completions.create(
        model="gpt-4o",  # Vision-capable model
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": COURSE_ANALYSIS_PROMPT},
                    image_content
                ]
            }
        ],
        max_tokens=1000
    )

    raw_response = response.choices[0].message.content

    # Parse JSON from response
    try:
        import json
        # Find JSON in response (might be wrapped in markdown code blocks)
        json_str = raw_response
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0]
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0]

        extracted_info = json.loads(json_str.strip())
        confidence = 0.8  # Base confidence

        # Reduce confidence if many unknowns
        if extracted_info.get("estimated_elevation_gain_ft") is None:
            confidence -= 0.1
        if "couldn't determine" in extracted_info.get("confidence_notes", "").lower():
            confidence -= 0.1

    except json.JSONDecodeError:
        extracted_info = {"raw_text": raw_response, "parse_error": True}
        confidence = 0.5

    return ImageAnalysisResponse(
        extracted_info=extracted_info,
        confidence=confidence,
        raw_description=raw_response
    )

async def encode_image_from_url(url: str) -> str:
    """Download image and encode as base64."""
    async with httpx.AsyncClient() as http_client:
        response = await http_client.get(url)
        response.raise_for_status()
        return base64.b64encode(response.content).decode('utf-8')

async def encode_image_from_file(file_content: bytes) -> str:
    """Encode uploaded file as base64."""
    return base64.b64encode(file_content).decode('utf-8')
```

**Task 2: Update Course Route for File Upload**

Update `backend/api/routes/course.py`:
```python
# Add to existing imports
from backend.course.vision import analyze_course_image, encode_image_from_file

# Add new endpoint
@router.post("/analyze-image-upload", response_model=ImageAnalysisResponse)
async def analyze_uploaded_image(file: UploadFile = File(...)):
    """
    Upload and analyze a course image (map, elevation chart, etc.).

    Accepts: JPEG, PNG, WebP
    """
    allowed_types = ["image/jpeg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"File must be an image. Allowed: {allowed_types}"
        )

    try:
        content = await file.read()
        base64_image = await encode_image_from_file(content)
        result = await analyze_course_image(base64_image)
        return result

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Image analysis failed: {str(e)}")
```

**Task 3: Test Vision Analysis**

Create `backend/course/test_vision.py`:
```python
"""Test vision analysis with sample images."""
import asyncio
from backend.course.vision import analyze_course_image

# Test with a public race elevation chart URL
TEST_URLS = [
    # Replace with actual test images
    "https://example.com/boston-marathon-elevation.png",
]

async def test_vision():
    for url in TEST_URLS:
        print(f"\nAnalyzing: {url}")
        print("=" * 60)

        try:
            result = await analyze_course_image(url)
            print(f"Confidence: {result.confidence}")
            print(f"Extracted: {result.extracted_info}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_vision())
```

**Expected output:** Upload course image → AI extracts elevation, terrain, and key segments.

---

## Day 4: Semantic Caching Layer

### Learning (1 hr)

**Why Caching Matters:**
- OpenAI API calls cost money ($0.01-0.03 per strategy generation)
- Similar questions often have similar answers
- Reduces latency for repeat queries

**Semantic vs Exact Caching:**
- Exact: "What pace for marathon?" ≠ "marathon pacing advice" (cache miss)
- Semantic: Both queries have similar embeddings → cache hit
- We'll use embeddings to find "similar enough" cached responses

**Implementation Options:**
- Redis with vector search (production)
- In-memory with numpy (good enough for this project)
- SQLite with embedding column (middle ground)

### Building (4 hrs)

**Task 1: Create Cache Module**

Create `backend/cache/semantic_cache.py`:
```python
import numpy as np
from typing import Optional, Tuple
import json
import hashlib
from datetime import datetime, timedelta
from backend.rag.embedder import generate_embedding

class SemanticCache:
    """
    Semantic caching for AI responses.

    Uses embedding similarity to find cached responses for similar queries.
    """

    def __init__(
        self,
        similarity_threshold: float = 0.92,
        max_entries: int = 1000,
        ttl_hours: int = 24
    ):
        self.similarity_threshold = similarity_threshold
        self.max_entries = max_entries
        self.ttl = timedelta(hours=ttl_hours)

        # In-memory storage
        # Production: Use Redis with vector search
        self.cache: dict[str, dict] = {}
        self.embeddings: dict[str, list[float]] = {}

    def _compute_cache_key(self, query: str, context_hash: str) -> str:
        """Generate a unique key for the query + context combination."""
        combined = f"{query}:{context_hash}"
        return hashlib.md5(combined.encode()).hexdigest()

    def _context_to_hash(self, context: dict) -> str:
        """Create a hash of context to differentiate same query for different users."""
        # Only hash the parts that affect the answer
        relevant = {
            "weekly_mileage": context.get("runner", {}).get("avg_weekly_mileage"),
            "goal_time": context.get("runner", {}).get("predicted_marathon_time"),
            "race_distance": context.get("race", {}).get("distance_miles"),
        }
        return hashlib.md5(json.dumps(relevant, sort_keys=True).encode()).hexdigest()[:8]

    async def get(
        self,
        query: str,
        context: Optional[dict] = None
    ) -> Optional[str]:
        """
        Check cache for a similar query.

        Returns cached response if found, None otherwise.
        """
        if not self.cache:
            return None

        context_hash = self._context_to_hash(context) if context else ""

        # Generate embedding for the query
        query_embedding = generate_embedding(query)
        query_vector = np.array(query_embedding)

        best_match: Optional[Tuple[str, float]] = None

        for key, entry in self.cache.items():
            # Check if context matches
            if entry.get("context_hash") != context_hash:
                continue

            # Check TTL
            if datetime.now() > entry["expires_at"]:
                continue

            # Calculate similarity
            cached_vector = np.array(self.embeddings[key])
            similarity = self._cosine_similarity(query_vector, cached_vector)

            if similarity >= self.similarity_threshold:
                if best_match is None or similarity > best_match[1]:
                    best_match = (key, similarity)

        if best_match:
            print(f"[Cache] HIT - similarity: {best_match[1]:.3f}")
            return self.cache[best_match[0]]["response"]

        print("[Cache] MISS")
        return None

    async def set(
        self,
        query: str,
        response: str,
        context: Optional[dict] = None
    ) -> None:
        """
        Store a query-response pair in cache.
        """
        context_hash = self._context_to_hash(context) if context else ""
        cache_key = self._compute_cache_key(query, context_hash)

        # Generate and store embedding
        query_embedding = generate_embedding(query)

        self.cache[cache_key] = {
            "query": query,
            "response": response,
            "context_hash": context_hash,
            "created_at": datetime.now(),
            "expires_at": datetime.now() + self.ttl
        }
        self.embeddings[cache_key] = query_embedding

        # Evict old entries if over limit
        if len(self.cache) > self.max_entries:
            self._evict_oldest()

        print(f"[Cache] Stored response for query: {query[:50]}...")

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    def _evict_oldest(self) -> None:
        """Remove oldest entries when cache is full."""
        sorted_entries = sorted(
            self.cache.items(),
            key=lambda x: x[1]["created_at"]
        )

        # Remove oldest 10%
        to_remove = max(1, len(sorted_entries) // 10)
        for key, _ in sorted_entries[:to_remove]:
            del self.cache[key]
            del self.embeddings[key]

    def stats(self) -> dict:
        """Return cache statistics."""
        now = datetime.now()
        valid_entries = sum(1 for e in self.cache.values() if e["expires_at"] > now)

        return {
            "total_entries": len(self.cache),
            "valid_entries": valid_entries,
            "expired_entries": len(self.cache) - valid_entries,
            "similarity_threshold": self.similarity_threshold
        }

# Global cache instance
strategy_cache = SemanticCache(
    similarity_threshold=0.92,
    max_entries=500,
    ttl_hours=48
)
```

**Task 2: Integrate Cache with Orchestrator**

Update `backend/agents/orchestrator.py`:
```python
# Add import at top
from backend.cache.semantic_cache import strategy_cache

class RaceCoachOrchestrator:
    # ... existing code ...

    async def answer_question_cached(
        self,
        question: str,
        access_token: Optional[str] = None,
        race_info: Optional[RaceInfo] = None
    ) -> Tuple[str, bool]:
        """
        Answer a question with caching.

        Returns (response, was_cached).
        """
        # Build context for cache key
        context = None
        if access_token and race_info:
            profile = build_runner_profile(access_token)
            context = prepare_race_context(profile, race_info)

        # Check cache
        cached = await strategy_cache.get(question, context)
        if cached:
            return (cached, True)

        # Generate fresh response
        response = self.answer_question(question, access_token, race_info)

        # Store in cache
        await strategy_cache.set(question, response, context)

        return (response, False)
```

**Task 3: Add Cache Stats Endpoint**

Update `backend/api/main.py`:
```python
from backend.cache.semantic_cache import strategy_cache

@app.get("/cache/stats")
async def cache_statistics():
    """View cache statistics."""
    return strategy_cache.stats()

@app.post("/cache/clear")
async def clear_cache():
    """Clear the semantic cache (admin only in production)."""
    strategy_cache.cache.clear()
    strategy_cache.embeddings.clear()
    return {"status": "cleared"}
```

**Expected output:** Second request for similar question returns instantly from cache.

---

## Day 5: Database Persistence

### Learning (1 hr)

**Simple Database Options:**
- Raw SQL with `asyncpg` (what we'll use - simple, fast)
- SQLModel (Pydantic + SQLAlchemy - overkill for this project)
- Prisma for Python (good, but another dependency)

**Why Postgres over SQLite:**
- Railway provides managed Postgres
- Better for concurrent requests
- You'll use it in co-op jobs

### Building (4 hrs)

**Task 1: Install Database Dependencies**

```bash
pip install asyncpg
pip freeze > requirements.txt
```

**Task 2: Create Database Module**

Create `backend/database/db.py`:
```python
import asyncpg
import os
from datetime import datetime
from typing import Optional
import json

# Connection pool (initialized on startup)
pool: Optional[asyncpg.Pool] = None

async def init_db():
    """Initialize database connection pool."""
    global pool
    pool = await asyncpg.create_pool(
        os.getenv("DATABASE_URL"),
        min_size=2,
        max_size=10
    )

    # Create tables if they don't exist
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                strava_athlete_id BIGINT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS strategies (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id INTEGER REFERENCES users(id),
                race_name VARCHAR(255) NOT NULL,
                race_distance_miles FLOAT NOT NULL,
                race_date DATE,
                pacing_strategy TEXT,
                nutrition_plan TEXT,
                mental_preparation TEXT,
                course_analysis JSONB,
                predicted_finish_minutes FLOAT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS course_analyses (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                gpx_filename VARCHAR(255),
                analysis_data JSONB NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

    print("Database initialized")

async def close_db():
    """Close database connection pool."""
    global pool
    if pool:
        await pool.close()

async def get_or_create_user(strava_athlete_id: int) -> int:
    """Get or create user by Strava athlete ID."""
    async with pool.acquire() as conn:
        # Try to get existing user
        row = await conn.fetchrow(
            "SELECT id FROM users WHERE strava_athlete_id = $1",
            strava_athlete_id
        )

        if row:
            return row["id"]

        # Create new user
        row = await conn.fetchrow(
            "INSERT INTO users (strava_athlete_id) VALUES ($1) RETURNING id",
            strava_athlete_id
        )
        return row["id"]

async def save_strategy(
    user_id: int,
    race_name: str,
    race_distance: float,
    race_date: Optional[datetime],
    pacing: str,
    nutrition: str,
    mental: str,
    course_analysis: Optional[dict],
    predicted_time: float
) -> str:
    """Save a generated strategy and return its ID."""
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO strategies
            (user_id, race_name, race_distance_miles, race_date,
             pacing_strategy, nutrition_plan, mental_preparation,
             course_analysis, predicted_finish_minutes)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING id
            """,
            user_id, race_name, race_distance, race_date,
            pacing, nutrition, mental,
            json.dumps(course_analysis) if course_analysis else None,
            predicted_time
        )
        return str(row["id"])

async def get_strategy(strategy_id: str) -> Optional[dict]:
    """Retrieve a strategy by ID."""
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
        rows = await conn.fetch(
            """
            SELECT id, race_name, race_distance_miles, race_date,
                   predicted_finish_minutes, created_at
            FROM strategies
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT $2
            """,
            user_id, limit
        )
        return [dict(row) for row in rows]
```

**Task 3: Update Main App with Database Lifecycle**

Update `backend/api/main.py`:
```python
from backend.database.db import init_db, close_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    print("Starting Race Coach API...")
    await init_db()
    yield
    # Shutdown
    print("Shutting down...")
    await close_db()
```

**Task 4: Create Strategy Routes**

Create `backend/api/routes/strategy.py`:
```python
from fastapi import APIRouter, HTTPException, BackgroundTasks
from backend.api.schemas import (
    GenerateStrategyRequest, StrategyResponse, StrategyListItem
)
from backend.agents.orchestrator import RaceCoachOrchestrator, generate_strategy_summary
from backend.models import RaceInfo
from backend.database.db import save_strategy, get_strategy, get_user_strategies, get_or_create_user
from backend.pipeline import build_runner_profile
from datetime import datetime
import json

router = APIRouter()
orchestrator = RaceCoachOrchestrator()

@router.post("/generate", response_model=StrategyResponse)
async def generate_strategy(request: GenerateStrategyRequest):
    """
    Generate a complete race strategy.

    This is the main endpoint - calls all agents and returns combined strategy.
    """
    try:
        # Convert request to internal model
        race_info = RaceInfo(
            name=request.race_info.name,
            distance_miles=request.race_info.distance_miles,
            date=request.race_info.date,
            location=request.race_info.location
        )

        # Generate strategy
        strategy = orchestrator.generate_full_strategy(
            access_token=request.access_token,
            race_info=race_info
        )

        # Get user for database
        profile = build_runner_profile(request.access_token)
        # Note: You'll need to store athlete_id during OAuth
        # For now, use a placeholder
        user_id = await get_or_create_user(12345)  # TODO: Get from OAuth

        # Save to database
        strategy_id = await save_strategy(
            user_id=user_id,
            race_name=race_info.name,
            race_distance=race_info.distance_miles,
            race_date=race_info.date,
            pacing=strategy["pacing_strategy"],
            nutrition=strategy["nutrition_plan"],
            mental=strategy["mental_preparation"],
            course_analysis=strategy.get("course_analysis"),
            predicted_time=strategy["runner_profile"]["predicted_time_minutes"]
        )

        return StrategyResponse(
            id=strategy_id,
            race_name=race_info.name,
            generated_at=datetime.now(),
            pacing_strategy=strategy["pacing_strategy"],
            nutrition_plan=strategy["nutrition_plan"],
            mental_preparation=strategy["mental_preparation"],
            course_analysis=strategy.get("course_analysis"),
            predicted_finish_time=strategy["runner_profile"]["predicted_time_minutes"]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy_by_id(strategy_id: str):
    """Retrieve a previously generated strategy."""
    strategy = await get_strategy(strategy_id)

    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    return StrategyResponse(
        id=str(strategy["id"]),
        race_name=strategy["race_name"],
        generated_at=strategy["created_at"],
        pacing_strategy=strategy["pacing_strategy"],
        nutrition_plan=strategy["nutrition_plan"],
        mental_preparation=strategy["mental_preparation"],
        course_analysis=strategy.get("course_analysis"),
        predicted_finish_time=strategy["predicted_finish_minutes"]
    )

@router.get("/user/history", response_model=list[StrategyListItem])
async def get_user_history(user_id: int, limit: int = 10):
    """Get a user's recent strategies."""
    strategies = await get_user_strategies(user_id, limit)

    return [
        StrategyListItem(
            id=str(s["id"]),
            race_name=s["race_name"],
            generated_at=s["created_at"],
            distance_miles=s["race_distance_miles"]
        )
        for s in strategies
    ]

@router.post("/question")
async def ask_question(question: str, access_token: str = None):
    """
    Ask a specific question to the coach.

    Routes to appropriate agent and uses caching.
    """
    response, was_cached = await orchestrator.answer_question_cached(
        question=question,
        access_token=access_token
    )

    return {
        "answer": response,
        "cached": was_cached
    }
```

**Expected output:** Strategies are persisted to Postgres and can be retrieved by ID.

---

## Day 6: Railway Deployment

### Learning (1 hr)

**Railway Basics**
- Read: [Railway - Getting Started](https://docs.railway.app/getting-started)
- Read: [Railway - Deploying Python](https://docs.railway.app/guides/python)
- Key concepts: Services, environment variables, Postgres plugin, domains

**Deployment Checklist:**
- `requirements.txt` with all dependencies
- `Procfile` or `railway.toml` for start command
- Environment variables configured in Railway dashboard
- CORS configured for your frontend domain

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

Create `Procfile` (alternative):
```
web: uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT
```

**Task 2: Update Requirements**

Ensure `requirements.txt` is complete:
```
fastapi==0.109.0
uvicorn==0.27.0
python-multipart==0.0.6
aiofiles==23.2.1
pydantic==2.5.3
requests==2.31.0
python-dotenv==1.0.0
pandas==2.1.4
scikit-learn==1.4.0
openai==1.10.0
pinecone-client==3.0.0
langchain==0.1.0
langchain-openai==0.0.5
tiktoken==0.5.2
httpx==0.26.0
gpxpy==1.6.1
asyncpg==0.29.0
numpy==1.26.3
```

**Task 3: Create Production Config**

Create `backend/config.py`:
```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings from environment variables."""

    # Environment
    environment: str = "development"
    debug: bool = False

    # API Keys
    openai_api_key: str
    pinecone_api_key: str
    pinecone_environment: str = "us-east-1"
    mapbox_access_token: str

    # Strava
    strava_client_id: str
    strava_client_secret: str
    strava_redirect_uri: str

    # Database
    database_url: str

    # CORS
    allowed_origins: str = "*"  # Comma-separated in production

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

Update `backend/api/main.py` to use settings:
```python
from backend.config import get_settings

settings = get_settings()

# Update CORS
origins = settings.allowed_origins.split(",") if settings.allowed_origins != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Task 4: Deploy to Railway**

1. Create Railway account and project
2. Connect GitHub repository
3. Add Postgres plugin (Railway dashboard → New → Database → PostgreSQL)
4. Configure environment variables in Railway dashboard:
   ```
   OPENAI_API_KEY=sk-...
   PINECONE_API_KEY=...
   PINECONE_ENVIRONMENT=us-east-1
   MAPBOX_ACCESS_TOKEN=pk.xxx
   STRAVA_CLIENT_ID=...
   STRAVA_CLIENT_SECRET=...
   STRAVA_REDIRECT_URI=https://your-app.railway.app/auth/strava/callback
   DATABASE_URL=${{Postgres.DATABASE_URL}}  # Railway auto-injects
   ENVIRONMENT=production
   ALLOWED_ORIGINS=https://your-frontend.vercel.app
   ```
5. Deploy and get your Railway URL

**Task 5: Test Deployed API**

```bash
# Health check
curl https://your-app.railway.app/health

# View docs
open https://your-app.railway.app/docs
```

**Task 6: Update Strava OAuth Redirect**

Go to Strava API settings and update the redirect URI to your Railway URL.

**Expected output:** API live on Railway with working endpoints and database.

---

## Day 7: Buffer + Integration Testing

**Time:** 4 hrs (flexible)

### End-to-End Testing

Create `backend/tests/test_e2e.py`:
```python
"""End-to-end tests for the deployed API."""
import httpx
import asyncio

BASE_URL = "https://your-app.railway.app"  # Or localhost for local testing

async def test_health():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        print("✓ Health check passed")

async def test_gpx_upload():
    # Create a minimal test GPX file
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

async def test_cache_stats():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/cache/stats")
        assert response.status_code == 200
        print("✓ Cache stats passed")

async def run_all_tests():
    await test_health()
    await test_gpx_upload()
    await test_cache_stats()
    print("\n✓ All tests passed!")

if __name__ == "__main__":
    asyncio.run(run_all_tests())
```

### Code Review Checklist

Before moving to Week 4, verify:

- [ ] `uvicorn backend.api.main:app --reload` runs locally without errors
- [ ] Swagger docs at `/docs` show all endpoints
- [ ] GPX upload returns valid course analysis
- [ ] Image upload returns AI-extracted course info
- [ ] Strategy generation calls all three agents
- [ ] Strategies are saved to and retrieved from Postgres
- [ ] Semantic cache reduces repeat query latency
- [ ] Railway deployment is live and healthy
- [ ] CORS is configured for your frontend domain
- [ ] No API keys are exposed in responses or logs

### Production Hardening (Optional)

If you have extra time:
- Add request logging middleware
- Add rate limiting (slowapi library)
- Add error tracking (Sentry)
- Add API key authentication for your frontend

---

## Week 3 Deliverables

By end of week, you should have:

1. **FastAPI backend** with clean route structure
2. **GPX course analysis** with elevation profiling
3. **Vision-based course analysis** for photos/screenshots
4. **Semantic caching** reducing API costs and latency
5. **Postgres persistence** for strategies and users
6. **Live deployment** on Railway

### File Structure After Week 3

```
backend/
├── api/
│   ├── __init__.py
│   ├── main.py
│   ├── schemas.py
│   ├── dependencies.py
│   └── routes/
│       ├── __init__.py
│       ├── auth.py
│       ├── course.py
│       └── strategy.py
├── agents/
│   └── ... (from Week 2)
├── rag/
│   └── ... (from Week 2)
├── course/
│   ├── __init__.py
│   ├── analyzer.py
│   └── vision.py
├── cache/
│   ├── __init__.py
│   └── semantic_cache.py
├── database/
│   ├── __init__.py
│   └── db.py
├── config.py
├── models.py
├── pipeline.py
└── ... (from Week 1)
├── requirements.txt
├── railway.toml
└── Procfile
```

### API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/auth/strava/url` | Get OAuth URL |
| POST | `/auth/strava/callback` | Exchange code for token |
| POST | `/course/analyze-gpx` | Upload GPX file |
| POST | `/course/analyze-image` | Analyze course image |
| POST | `/strategy/generate` | Generate full strategy |
| GET | `/strategy/{id}` | Get saved strategy |
| POST | `/strategy/question` | Ask specific question |
| GET | `/cache/stats` | View cache stats |

---

## Learning Resources Summary

| Resource | Time | When |
|----------|------|------|
| [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/) | 2 hrs | Day 1 |
| [GPX Format Overview](https://www.topografix.com/gpx.asp) | 30 min | Day 2 |
| [OpenAI Vision Guide](https://platform.openai.com/docs/guides/vision) | 45 min | Day 3 |
| [Railway Getting Started](https://docs.railway.app/getting-started) | 1 hr | Day 6 |

**Total structured learning: ~6-7 hours**

---

## Next Week Preview

Week 4 will build the frontend and polish:
- Next.js React frontend
- 2D elevation chart visualization
- Streaming AI responses (typewriter effect)
- PDF export of strategies
- Shareable strategy links
- Vercel deployment
- Demo video and documentation
