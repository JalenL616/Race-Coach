# Race Coach: 4-Week Project Plan

A web app that uses a multi-agent AI system to plan race strategies for runners based on their training data, course analysis, weather conditions, and expert running knowledge.

## Time Budget

- **Total:** 30 hrs/week × 4 weeks = 120 hours
- **Learning:** ~30% (28-36 hours)
- **Building:** ~70% (84-92 hours)

---

## Scope

### Included

| Core | AI/Advanced | Polish (Last Priority) |
|------|-------------|------------------------|
| Strava OAuth + data fetching | Multi-agent architecture (Pacing, Nutrition, Mental) | Streaming UI |
| Pandas processing | RAG pipeline with Pinecone | Export as PDF |
| Prediction engine (Riegel + sklearn) | Agent orchestration + function calling | Shareable links |
| Weather API integration | Multi-modal vision input | Loading state animations |
| FastAPI backend | Semantic caching layer | Demo video |
| GPX parsing + Mapbox elevation | | |
| Basic Postgres persistence | | |
| Simple React frontend + 2D charts | | |
| Vercel + Railway deployment | | |

---

## Weekly Overview

### Week 1: Data Engineering Foundation

**Goal:** Ingest user data, build prediction engine, establish Python backend patterns

| Element | Notes |
|---------|-------|
| Python env + Strava OAuth | Manual OAuth flow to understand it |
| Data fetching + Pandas cleaning | Filter runs, convert units, aggregate weekly |
| Prediction engine | Riegel's formula + consistency scoring with sklearn |
| Weather API integration | OpenWeather for race-day conditions |
| Pydantic validation | Type-safe data models |
| Module structure | Clean imports for Week 2+ |

**Learning focus:** Pandas (Kaggle), sklearn basics, OAuth 2.0

---

### Week 2: Multi-Agent AI Architecture

**Goal:** Build the "brain" - multiple specialized agents with orchestration

| Element | Notes |
|---------|-------|
| Knowledge base curation | Running wikis, blogs, open-access content |
| Chunking + embeddings | LangChain splitters, OpenAI embeddings |
| Pinecone vector store | With metadata for filtering by topic |
| Agent design | Pacing Agent, Nutrition Agent, Mental Prep Agent |
| Function calling / tool use | Each agent has specific tools it can invoke |
| Orchestrator | Routes queries, combines agent outputs |
| Prompt engineering | System prompts for each agent persona |

**Learning focus:** Embeddings theory, vector similarity, DeepLearning.AI RAG course, function calling patterns, agent architectures

---

### Week 3: Backend System + Advanced AI

**Goal:** API layer, course analysis, vision input, caching

| Element | Notes |
|---------|-------|
| FastAPI setup | Async endpoints, proper error handling |
| GPX parsing + Mapbox elevation | Course difficulty analysis |
| Master `/generate-strategy` endpoint | Orchestrates all agents + data sources |
| Multi-modal vision input | Upload course photo, extract insights via GPT-4V/Claude |
| Semantic caching layer | Cache embeddings + similar query results |
| Basic Postgres persistence | Store strategies, user data |
| Deployment (Railway) | Get backend live early |

**Learning focus:** FastAPI docs, vision model APIs, caching strategies

---

### Week 4: Frontend + Polish

**Goal:** Usable UI, streaming experience, export features, ship it

| Element | Priority | Notes |
|---------|----------|-------|
| React frontend scaffold | High | Next.js, basic routing |
| 2D elevation profile chart | High | Recharts or similar |
| Strava OAuth flow in UI | High | Login → fetch data |
| Strategy generation UI | High | Form → results display |
| Streaming responses | Medium | Typewriter effect, "thinking" steps |
| Export as PDF | Medium | react-pdf or server-side generation |
| Shareable links | Low | Unique URLs for strategies |
| Vercel deployment | High | Connect to Railway backend |
| Documentation + demo video | High | README, Loom recording |

**Learning focus:** Streaming/SSE patterns, Mapbox basics (2D only)

---

## Learning Time Budget

| Week | Learning Hours | Key Resources |
|------|----------------|---------------|
| 1 | 8-10 hrs | Kaggle Pandas, sklearn docs, OAuth guides |
| 2 | 10-12 hrs | DeepLearning.AI RAG course, agent architecture blogs, function calling docs |
| 3 | 6-8 hrs | FastAPI tutorial, vision API docs |
| 4 | 4-6 hrs | Streaming patterns, deployment guides |
| **Total** | **28-36 hrs** | ~25-30% of 120 hrs |

---

## Skills Demonstrated to Employers

1. **Agent orchestration** - Multi-agent coordination, not just "call GPT"
2. **RAG with evaluation mindset** - Vector search + confidence thresholds
3. **Multi-modal AI** - Vision input is cutting-edge
4. **Production patterns** - Caching, streaming, proper API design
5. **Full-stack AI** - Data engineering → AI → backend → frontend
6. **Cost awareness** - Caching shows you think about API costs

---

## Detailed Plans

- [Week 1: Data Engineering Foundation](./WEEK1.md)
- Week 2: Multi-Agent AI Architecture (TODO)
- Week 3: Backend System + Advanced AI (TODO)
- Week 4: Frontend + Polish (TODO)
