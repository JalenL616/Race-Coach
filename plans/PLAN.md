# Race Coach: 4-Week Project Plan (Simplified)

A web app that uses AI to plan race strategies for runners based on their training data, course analysis, weather conditions, and expert running knowledge.

## Time Budget

- **Total:** 30 hrs/week × 4 weeks = 120 hours
- **Learning:** ~25% (25-30 hours)
- **Building:** ~75% (90-95 hours)

---

## Architecture Philosophy

**Keep it simple.** This project demonstrates AI engineering skills without unnecessary complexity.

### What We're Building
```
┌─────────────────────────────────────────────────────────────┐
│                    React Frontend (Vercel)                   │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTPS
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (Railway)                 │
│                                                              │
│  ┌────────────────┐    ┌────────────────┐                   │
│  │ Data Pipeline  │───▶│  Single Agent  │                   │
│  │ (Strava→VDOT)  │    │  (Claude/GPT)  │                   │
│  └────────────────┘    └────────────────┘                   │
│           │                    │                             │
│           ▼                    ▼                             │
│  ┌────────────────────────────────────────┐                 │
│  │              PostgreSQL                 │                 │
│  │  users | preferences | strategies       │                 │
│  └────────────────────────────────────────┘                 │
└─────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Agent architecture | Single unified agent | One agent produces more coherent output; multi-agent is overkill for this scope |
| Knowledge base | Embedded in system prompt | < 20K tokens total; no need for vector search infrastructure |
| Database | PostgreSQL | Persists user preferences and strategies across sessions |
| PDF export | Browser print CSS | Simpler than react-pdf, works everywhere |
| Streaming | Optional/simple | Nice-to-have, not core to demonstrating AI skills |

### What We're NOT Building (Intentionally Cut)
- ❌ Multi-agent orchestration (Pacing/Nutrition/Mental agents)
- ❌ Pinecone vector database
- ❌ LangChain framework
- ❌ Vision/image analysis (GPT-4V)
- ❌ Semantic caching layer
- ❌ Mapbox elevation API (use GPX data directly)
- ❌ Complex streaming UI with typewriter effects

---

## Scope

### Included

| Core | AI | Polish (If Time) |
|------|-----|------------------|
| Strava OAuth + data fetching | Single unified agent with tools | Streaming responses |
| Pandas processing + VDOT | Knowledge embedded in prompt | Shareable links |
| Weather API integration | Function calling for calculations | Loading animations |
| GPX parsing (elevation from file) | User preference persistence | Demo video |
| FastAPI backend | | |
| PostgreSQL (users, preferences, strategies) | | |
| Simple React frontend + elevation chart | | |
| Vercel + Railway deployment | | |
| Browser-based PDF export | | |

---

## Weekly Overview

### Week 1: Data Engineering Foundation ✅

**Goal:** Ingest user data, build prediction engine, establish Python backend patterns

| Element | Notes |
|---------|-------|
| Python env + Strava OAuth | Manual OAuth flow |
| Data fetching + Pandas cleaning | Filter runs, convert units, aggregate weekly |
| VDOT-based prediction engine | Race time predictions from fitness |
| Weather API integration | OpenWeather for race-day conditions |
| Pydantic validation | Type-safe data models |

**Status:** Complete with adjustments (VDOT instead of Riegel, categorize_activities added)

---

### Week 2: AI Agent + Knowledge Base

**Goal:** Build a single intelligent agent with running expertise embedded in its context

| Element | Notes |
|---------|-------|
| Curate running knowledge | 15-20 high-quality sources on pacing, nutrition, mental prep |
| Format as system prompt | Structured markdown, fits in context window |
| Single agent implementation | One agent handles all three domains |
| Function calling / tools | calculate_splits, calculate_nutrition |
| Prompt engineering | System prompt with runner context injection |
| Test with real data | End-to-end: Strava → Agent → Strategy |

**Learning focus:** Prompt engineering, function calling, context window management

---

### Week 3: Backend System + Database

**Goal:** API layer, course analysis, database persistence, deployment

| Element | Notes |
|---------|-------|
| FastAPI setup | Async endpoints, proper error handling |
| GPX parsing | Extract elevation from uploaded files |
| `/generate-strategy` endpoint | Calls agent with all context |
| PostgreSQL setup | users, preferences, strategies tables |
| User preferences | Persist gel brand, pacing style, etc. |
| Railway deployment | Get backend live |

**Learning focus:** FastAPI, asyncpg, Railway deployment

---

### Week 4: Frontend + Polish

**Goal:** Usable UI, PDF export, deploy everything

| Element | Priority | Notes |
|---------|----------|-------|
| React frontend scaffold | High | Next.js, basic routing |
| Elevation profile chart | High | Recharts |
| Strava OAuth flow in UI | High | Login → fetch data |
| Strategy generation UI | High | Form → results display |
| Browser-based PDF export | Medium | Print-optimized CSS |
| Vercel deployment | High | Connect to Railway backend |
| Documentation + demo | High | README, architecture diagram |

**Learning focus:** Next.js App Router, Recharts, deployment

---

## Learning Time Budget

| Week | Learning Hours | Key Resources |
|------|----------------|---------------|
| 1 | 8-10 hrs | Pandas, VDOT theory, OAuth guides |
| 2 | 8-10 hrs | Prompt engineering, function calling docs |
| 3 | 4-6 hrs | FastAPI tutorial, asyncpg |
| 4 | 4-6 hrs | Next.js, Recharts, deployment |
| **Total** | **24-32 hrs** | ~20-25% of 120 hrs |

---

## Skills Demonstrated to Employers

1. **AI Engineering** - Prompt engineering, function calling, context management
2. **Full-Stack Development** - React, FastAPI, PostgreSQL
3. **API Integration** - Strava OAuth, OpenAI/Anthropic, weather APIs
4. **Data Processing** - Pandas, VDOT calculations, GPX parsing
5. **Production Deployment** - Vercel, Railway, environment management
6. **Software Design** - Knowing when NOT to over-engineer

---

## Database Schema

```sql
-- Users linked to Strava
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    strava_athlete_id BIGINT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- User preferences (persisted across sessions)
CREATE TABLE user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    preference_key VARCHAR(100) NOT NULL,
    preference_value TEXT,
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, preference_key)
);

-- Generated strategies
CREATE TABLE strategies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER REFERENCES users(id),
    race_name VARCHAR(255) NOT NULL,
    race_distance_miles FLOAT NOT NULL,
    race_date DATE,
    strategy_content TEXT NOT NULL,
    course_analysis JSONB,
    weather_data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

Example preferences:
- `gel_brand`: "Maurten"
- `pacing_style`: "conservative"
- `caffeine_tolerance`: "high"
- `stomach_sensitivity`: "moderate"

---

## Detailed Plans

- [Week 1: Data Engineering Foundation](./WEEK1.md) ✅
- [Week 1 Post-Mortem](./WEEK1POST.md) ✅
- [Week 2: AI Agent + Knowledge Base](./WEEK2.md)
- [Week 3: Backend System + Database](./WEEK3.md)
- [Week 4: Frontend + Polish](./WEEK4.md)
