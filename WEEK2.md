# Week 2: Multi-Agent AI Architecture

**Goal:** Build the AI "brain" - a multi-agent system with RAG (Retrieval-Augmented Generation) that grounds advice in real running expertise rather than hallucinating generic tips.

**Time Budget:** ~30 hours
- Learning: 10-12 hours (heaviest learning week)
- Building: 18-20 hours

---

## Prerequisites

Before starting, ensure you have:
- Week 1 complete with working `RunnerProfile` pipeline
- OpenAI API key from https://platform.openai.com
- Pinecone account (free tier) from https://www.pinecone.io
- Add to `.env`:
  ```
  OPENAI_API_KEY=sk-...
  PINECONE_API_KEY=...
  PINECONE_ENVIRONMENT=...
  ```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      ORCHESTRATOR                            │
│  Receives: RunnerProfile + RaceInfo + User Question          │
│  Routes to appropriate agents, combines responses            │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ PACING AGENT │ │NUTRITION AGT │ │MENTAL PREP   │
│              │ │              │ │    AGENT     │
│ Tools:       │ │ Tools:       │ │ Tools:       │
│ - RAG search │ │ - RAG search │ │ - RAG search │
│ - Calculator │ │ - Calculator │ │              │
│ - Splits gen │ │              │ │              │
└──────────────┘ └──────────────┘ └──────────────┘
        │             │             │
        └─────────────┼─────────────┘
                      ▼
              ┌──────────────┐
              │   PINECONE   │
              │ Vector Store │
              │              │
              │ - Pacing docs│
              │ - Nutrition  │
              │ - Mental     │
              └──────────────┘
```

---

## Day 1: Understanding Embeddings + Knowledge Curation

### Learning (3 hrs)

**What Are Embeddings?**
- Watch: [What are Word Embeddings?](https://www.youtube.com/watch?v=viZrOnJclY0) (15 min)
- Read: [OpenAI - Embeddings Guide](https://platform.openai.com/docs/guides/embeddings)
- Key concept: Text → list of numbers (vector) that captures semantic meaning
- Why it matters: "How should I pace hills?" and "What's my uphill strategy?" have similar vectors even though they share few words

**Vector Similarity**
- Read: [Pinecone - What is Similarity Search?](https://www.pinecone.io/learn/what-is-similarity-search/)
- Key concept: Cosine similarity measures angle between vectors (1.0 = identical meaning, 0 = unrelated)
- Play with: [Tensorflow Embedding Projector](https://projector.tensorflow.org/) to visualize how similar words cluster

**RAG Overview**
- Watch: [RAG Explained in 5 Minutes](https://www.youtube.com/watch?v=T-D1OfcDW1M) (or similar short explainer)
- Key concept: Instead of asking "What's good marathon pacing?" directly, you first RETRIEVE relevant documents, then ask the LLM to answer USING those documents

### Building (2 hrs)

**Task 1: Create Knowledge Base Directory Structure**

```
backend/
├── knowledge/
│   ├── raw/                    # Original sources
│   │   ├── pacing/
│   │   ├── nutrition/
│   │   └── mental/
│   ├── processed/              # Chunked text files
│   └── sources.md              # Attribution and links
```

**Task 2: Curate Knowledge Base**

You need high-quality, open-source running knowledge. Spend time gathering content from:

**Pacing Knowledge:**
- [Runners World - Marathon Pacing Guide](https://www.runnersworld.com/uk/training/marathon/a774868/how-to-pace-a-marathon/)
- [Fellrnr Wiki - Pacing](https://fellrnr.com/wiki/Pacing)
- [r/AdvancedRunning Wiki](https://www.reddit.com/r/AdvancedRunning/wiki/index)
- Key topics: negative splits, positive splits, even pacing, hill strategy, weather adjustments

**Nutrition Knowledge:**
- [Runners Connect - Marathon Fueling](https://runnersconnect.net/marathon-nutrition-race-day/)
- [Science of Ultra - Nutrition](https://www.scienceofultra.com/podcasts) (transcripts)
- Key topics: carb loading, gel timing, hydration, electrolytes, caffeine

**Mental Preparation:**
- [Runners World - Mental Strategies](https://www.runnersworld.com/training/a20865748/mental-strategies-for-marathon-running/)
- Sports psychology basics, visualization techniques, mantras, managing the wall
- Key topics: chunking the race, positive self-talk, focus cues, pain management

Save as `.txt` files in appropriate folders. Each file should be a coherent piece (one article, one wiki section). Don't copy entire websites - pick the most valuable 10-15 sources total.

**Create `sources.md`:**
```markdown
# Knowledge Base Sources

## Pacing
- [Source Name](URL) - Brief description of what it covers
- ...

## Nutrition
- ...

## Mental
- ...

Note: All content used under fair use for educational/personal project purposes.
```

**Expected output:** 10-15 quality text files organized by topic, with proper attribution.

---

## Day 2: Text Chunking + Embedding Generation

### Learning (2 hrs)

**Text Chunking Strategies**
- Read: [LangChain - Text Splitters](https://python.langchain.com/docs/modules/data_connection/document_transformers/)
- Key concepts:
  - Chunk size (how many characters/tokens per chunk)
  - Chunk overlap (how much adjacent chunks share)
  - Why overlap matters: prevents cutting off mid-sentence, preserves context
- Rule of thumb: 500-1000 characters per chunk, 100-200 overlap

**OpenAI Embeddings API**
- Read: [OpenAI - Embeddings API Reference](https://platform.openai.com/docs/api-reference/embeddings)
- Model choice: `text-embedding-3-small` (cheap, good quality, 1536 dimensions)
- Cost awareness: ~$0.02 per 1M tokens - your knowledge base will cost pennies

### Building (4 hrs)

**Task 1: Install Dependencies**

```bash
pip install langchain langchain-openai tiktoken
pip freeze > requirements.txt
```

**Task 2: Build Chunking Pipeline**

Create `backend/rag/chunker.py`:
```python
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pathlib import Path
import json

def load_documents(knowledge_dir: str = "backend/knowledge/raw") -> list[dict]:
    """
    Load all .txt files from knowledge directory.

    Returns list of dicts with:
    - content: the text
    - source: filename
    - category: parent folder (pacing/nutrition/mental)
    """
    documents = []
    knowledge_path = Path(knowledge_dir)

    for category_dir in knowledge_path.iterdir():
        if category_dir.is_dir():
            category = category_dir.name
            for file_path in category_dir.glob("*.txt"):
                content = file_path.read_text(encoding="utf-8")
                documents.append({
                    "content": content,
                    "source": file_path.name,
                    "category": category
                })

    return documents

def chunk_documents(
    documents: list[dict],
    chunk_size: int = 800,
    chunk_overlap: int = 150
) -> list[dict]:
    """
    Split documents into smaller chunks for embedding.

    Preserves metadata (source, category) on each chunk.
    Adds chunk_index for ordering.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]  # Prefer splitting at paragraphs
    )

    chunks = []
    for doc in documents:
        splits = splitter.split_text(doc["content"])
        for i, split in enumerate(splits):
            chunks.append({
                "content": split,
                "source": doc["source"],
                "category": doc["category"],
                "chunk_index": i
            })

    return chunks

def save_chunks(chunks: list[dict], output_path: str = "backend/knowledge/chunks.json"):
    """Save chunks to JSON for inspection and embedding."""
    with open(output_path, "w") as f:
        json.dump(chunks, f, indent=2)
    print(f"Saved {len(chunks)} chunks to {output_path}")
```

**Task 3: Generate Embeddings**

Create `backend/rag/embedder.py`:
```python
from openai import OpenAI
import json
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_embedding(text: str, model: str = "text-embedding-3-small") -> list[float]:
    """Generate embedding for a single text."""
    response = client.embeddings.create(
        input=text,
        model=model
    )
    return response.data[0].embedding

def embed_chunks(chunks: list[dict], batch_size: int = 100) -> list[dict]:
    """
    Generate embeddings for all chunks.

    Batches requests for efficiency.
    Adds 'embedding' field to each chunk.
    """
    embedded_chunks = []

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        texts = [chunk["content"] for chunk in batch]

        # Batch embedding request
        response = client.embeddings.create(
            input=texts,
            model="text-embedding-3-small"
        )

        for j, embedding_data in enumerate(response.data):
            chunk = batch[j].copy()
            chunk["embedding"] = embedding_data.embedding
            embedded_chunks.append(chunk)

        print(f"Embedded {min(i + batch_size, len(chunks))}/{len(chunks)} chunks")

    return embedded_chunks

def save_embeddings(chunks: list[dict], output_path: str = "backend/knowledge/embeddings.json"):
    """Save embedded chunks to JSON."""
    with open(output_path, "w") as f:
        json.dump(chunks, f)
    print(f"Saved {len(chunks)} embeddings to {output_path}")

# Main execution
if __name__ == "__main__":
    from chunker import load_documents, chunk_documents

    # Load and chunk
    docs = load_documents()
    print(f"Loaded {len(docs)} documents")

    chunks = chunk_documents(docs)
    print(f"Created {len(chunks)} chunks")

    # Embed
    embedded = embed_chunks(chunks)
    save_embeddings(embedded)
```

**Expected output:** `embeddings.json` file containing all chunks with their vector embeddings.

---

## Day 3: Pinecone Vector Store

### Learning (2 hrs)

**Vector Databases**
- Read: [Pinecone - What is a Vector Database?](https://www.pinecone.io/learn/vector-database/)
- Key concepts:
  - Index: container for vectors (like a database table)
  - Namespace: partition within an index (optional, for organizing)
  - Metadata filtering: query only vectors matching certain criteria
  - Top-K: return the K most similar results

**Pinecone Quickstart**
- Read: [Pinecone - Quickstart Guide](https://docs.pinecone.io/guides/get-started/quickstart)
- Follow along to create your first index
- Understand: upsert (insert/update), query, delete operations

### Building (3 hrs)

**Task 1: Install Pinecone**

```bash
pip install pinecone-client
pip freeze > requirements.txt
```

**Task 2: Create Index and Upload**

Create `backend/rag/vector_store.py`:
```python
from pinecone import Pinecone, ServerlessSpec
import json
import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

# Initialize Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

INDEX_NAME = "race-coach"
EMBEDDING_DIMENSION = 1536  # text-embedding-3-small dimension

def create_index_if_not_exists():
    """Create the Pinecone index if it doesn't exist."""
    existing_indexes = [idx.name for idx in pc.list_indexes()]

    if INDEX_NAME not in existing_indexes:
        pc.create_index(
            name=INDEX_NAME,
            dimension=EMBEDDING_DIMENSION,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"  # Use free tier region
            )
        )
        print(f"Created index: {INDEX_NAME}")
    else:
        print(f"Index {INDEX_NAME} already exists")

    return pc.Index(INDEX_NAME)

def upload_embeddings(embeddings_path: str = "backend/knowledge/embeddings.json"):
    """Upload all embeddings to Pinecone with metadata."""
    index = create_index_if_not_exists()

    with open(embeddings_path, "r") as f:
        chunks = json.load(f)

    # Prepare vectors for upsert
    vectors = []
    for i, chunk in enumerate(chunks):
        vectors.append({
            "id": f"{chunk['category']}_{chunk['source']}_{chunk['chunk_index']}",
            "values": chunk["embedding"],
            "metadata": {
                "content": chunk["content"],
                "source": chunk["source"],
                "category": chunk["category"],
                "chunk_index": chunk["chunk_index"]
            }
        })

    # Upsert in batches of 100
    batch_size = 100
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i:i + batch_size]
        index.upsert(vectors=batch)
        print(f"Uploaded {min(i + batch_size, len(vectors))}/{len(vectors)} vectors")

    print(f"Upload complete. Index stats: {index.describe_index_stats()}")

def query_similar(
    query_embedding: list[float],
    category: Optional[str] = None,
    top_k: int = 5,
    min_score: float = 0.7
) -> list[dict]:
    """
    Query Pinecone for similar content.

    Args:
        query_embedding: Vector to search for
        category: Optional filter (pacing/nutrition/mental)
        top_k: Number of results to return
        min_score: Minimum similarity score (0-1)

    Returns:
        List of matching chunks with scores
    """
    index = pc.Index(INDEX_NAME)

    # Build filter if category specified
    filter_dict = {"category": category} if category else None

    results = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True,
        filter=filter_dict
    )

    # Filter by minimum score and extract content
    matches = []
    for match in results.matches:
        if match.score >= min_score:
            matches.append({
                "content": match.metadata["content"],
                "source": match.metadata["source"],
                "category": match.metadata["category"],
                "score": match.score
            })

    return matches

# Run upload
if __name__ == "__main__":
    upload_embeddings()
```

**Task 3: Build Retrieval Interface**

Create `backend/rag/retriever.py`:
```python
from backend.rag.vector_store import query_similar
from backend.rag.embedder import generate_embedding
from typing import Optional

def retrieve_context(
    query: str,
    category: Optional[str] = None,
    top_k: int = 5,
    min_score: float = 0.7
) -> list[dict]:
    """
    High-level retrieval: text query → relevant chunks.

    This is what agents will call.
    """
    # Convert query to embedding
    query_embedding = generate_embedding(query)

    # Search Pinecone
    results = query_similar(
        query_embedding=query_embedding,
        category=category,
        top_k=top_k,
        min_score=min_score
    )

    return results

def format_context_for_prompt(chunks: list[dict]) -> str:
    """
    Format retrieved chunks into a string for LLM prompt.

    Includes source attribution for transparency.
    """
    if not chunks:
        return "No relevant expert advice found for this query."

    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        context_parts.append(
            f"[Source {i}: {chunk['source']} (relevance: {chunk['score']:.2f})]\n"
            f"{chunk['content']}"
        )

    return "\n\n---\n\n".join(context_parts)

# Test retrieval
if __name__ == "__main__":
    # Test queries
    test_queries = [
        ("How should I pace the first mile of a marathon?", "pacing"),
        ("When should I take energy gels?", "nutrition"),
        ("How do I stay mentally strong at mile 20?", "mental"),
    ]

    for query, category in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"Category: {category}")
        print("="*60)

        results = retrieve_context(query, category=category, top_k=3)
        formatted = format_context_for_prompt(results)
        print(formatted[:500] + "..." if len(formatted) > 500 else formatted)
```

**Expected output:** Queries return relevant chunks from your knowledge base with similarity scores.

---

## Day 4: Agent Architecture + Function Calling

### Learning (3 hrs)

**Agent Fundamentals**
- Read: [Lilian Weng - LLM Powered Autonomous Agents](https://lilianweng.github.io/posts/2023-06-23-agent/) (sections 1-2)
- Key concepts:
  - Agents = LLM + Memory + Tools
  - ReAct pattern: Reason → Act → Observe → Repeat
  - Tool use: LLM decides WHEN and HOW to call external functions

**Function Calling / Tool Use**
- Read: [OpenAI - Function Calling Guide](https://platform.openai.com/docs/guides/function-calling)
- Read: [Anthropic - Tool Use](https://docs.anthropic.com/en/docs/build-with-claude/tool-use) (similar concepts, different syntax)
- Key concepts:
  - Define function schemas (name, description, parameters)
  - LLM outputs structured JSON to "call" the function
  - You execute the function and return results to the LLM
  - LLM incorporates results into its response

**Start the DeepLearning.AI Course**
- Begin: [LangChain for LLM Application Development](https://www.deeplearning.ai/short-courses/langchain-for-llm-application-development/)
- Complete: Lessons 1-3 (Models, Prompts, Memory)
- This provides hands-on practice with the concepts

### Building (3 hrs)

**Task 1: Define Agent Tool Schemas**

Create `backend/agents/tools.py`:
```python
"""
Tool definitions for Race Coach agents.

Each tool is defined as:
1. A schema (for the LLM to understand)
2. An implementation (actual Python function)
"""

from backend.rag.retriever import retrieve_context, format_context_for_prompt
from typing import Optional

# ============== TOOL SCHEMAS (for LLM) ==============

RETRIEVE_KNOWLEDGE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "retrieve_knowledge",
        "description": "Search the running knowledge base for expert advice on a specific topic. Use this when you need factual information about pacing, nutrition, or mental strategies.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query describing what information you need"
                },
                "category": {
                    "type": "string",
                    "enum": ["pacing", "nutrition", "mental"],
                    "description": "Category to search within for more relevant results"
                }
            },
            "required": ["query"]
        }
    }
}

CALCULATE_SPLITS_SCHEMA = {
    "type": "function",
    "function": {
        "name": "calculate_splits",
        "description": "Calculate mile-by-mile split times for a race given a goal time and pacing strategy.",
        "parameters": {
            "type": "object",
            "properties": {
                "goal_time_minutes": {
                    "type": "number",
                    "description": "Target finish time in minutes"
                },
                "distance_miles": {
                    "type": "number",
                    "description": "Race distance in miles"
                },
                "strategy": {
                    "type": "string",
                    "enum": ["even", "negative", "positive"],
                    "description": "Pacing strategy: even (same pace), negative (faster second half), positive (slower second half)"
                },
                "elevation_profile": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Optional elevation gain per mile in feet"
                }
            },
            "required": ["goal_time_minutes", "distance_miles", "strategy"]
        }
    }
}

CALCULATE_NUTRITION_SCHEMA = {
    "type": "function",
    "function": {
        "name": "calculate_nutrition",
        "description": "Calculate fueling needs (gels, water, electrolytes) for a race based on duration and conditions.",
        "parameters": {
            "type": "object",
            "properties": {
                "expected_duration_minutes": {
                    "type": "number",
                    "description": "Expected race duration in minutes"
                },
                "temperature_f": {
                    "type": "number",
                    "description": "Expected temperature in Fahrenheit"
                },
                "humidity_percent": {
                    "type": "number",
                    "description": "Expected humidity percentage"
                }
            },
            "required": ["expected_duration_minutes"]
        }
    }
}

# ============== TOOL IMPLEMENTATIONS ==============

def retrieve_knowledge(query: str, category: Optional[str] = None) -> str:
    """Execute knowledge retrieval."""
    chunks = retrieve_context(query, category=category, top_k=4)
    return format_context_for_prompt(chunks)

def calculate_splits(
    goal_time_minutes: float,
    distance_miles: float,
    strategy: str,
    elevation_profile: Optional[list[float]] = None
) -> dict:
    """
    Calculate mile splits based on strategy.

    Returns dict with splits array and summary stats.
    """
    base_pace = goal_time_minutes / distance_miles
    splits = []

    for mile in range(1, int(distance_miles) + 1):
        pace = base_pace

        # Adjust for strategy
        if strategy == "negative":
            # Start 3% slower, finish 3% faster
            progress = mile / distance_miles
            adjustment = 1.03 - (0.06 * progress)
            pace *= adjustment
        elif strategy == "positive":
            # Start 2% faster, slow down
            progress = mile / distance_miles
            adjustment = 0.98 + (0.04 * progress)
            pace *= adjustment

        # Adjust for elevation if provided
        if elevation_profile and mile <= len(elevation_profile):
            elevation_gain = elevation_profile[mile - 1]
            # Rough formula: +1.5% per 50ft gain
            elevation_adjustment = 1 + (elevation_gain / 50 * 0.015)
            pace *= elevation_adjustment

        splits.append({
            "mile": mile,
            "pace": round(pace, 2),
            "cumulative_time": round(sum(s["pace"] for s in splits) + pace, 2)
        })

    return {
        "splits": splits,
        "average_pace": round(sum(s["pace"] for s in splits) / len(splits), 2),
        "strategy": strategy,
        "goal_time": goal_time_minutes
    }

def calculate_nutrition(
    expected_duration_minutes: float,
    temperature_f: float = 60,
    humidity_percent: float = 50
) -> dict:
    """
    Calculate nutrition plan based on duration and conditions.

    General guidelines:
    - 30-60g carbs per hour after first hour
    - 1 gel ≈ 25g carbs
    - Hydration: 4-8oz every 15-20 min (more in heat)
    """
    hours = expected_duration_minutes / 60

    # Base carb needs (grams)
    carbs_needed = max(0, (hours - 1) * 45)  # ~45g/hr after first hour
    gels_needed = int(carbs_needed / 25) + 1  # Round up

    # Hydration adjustments for heat
    base_fluid_oz_per_hour = 20
    if temperature_f > 70:
        base_fluid_oz_per_hour += (temperature_f - 70) * 0.5
    if humidity_percent > 60:
        base_fluid_oz_per_hour += (humidity_percent - 60) * 0.1

    total_fluid_oz = base_fluid_oz_per_hour * hours

    # Gel timing
    gel_schedule = []
    if gels_needed > 0:
        # First gel at 45 min, then every 45 min
        gel_times = [45]
        while len(gel_times) < gels_needed and gel_times[-1] + 45 < expected_duration_minutes - 15:
            gel_times.append(gel_times[-1] + 45)
        gel_schedule = [{"minute": t, "item": "energy gel"} for t in gel_times]

    return {
        "total_gels": gels_needed,
        "total_fluid_oz": round(total_fluid_oz),
        "gel_schedule": gel_schedule,
        "fluid_per_aid_station": "6-8 oz" if temperature_f < 70 else "8-10 oz",
        "electrolyte_recommendation": "salt tabs every hour" if temperature_f > 75 or humidity_percent > 70 else "standard sports drink",
        "pre_race_carbs_g": 100  # 2-3 hours before
    }

# Tool registry for easy lookup
TOOL_REGISTRY = {
    "retrieve_knowledge": retrieve_knowledge,
    "calculate_splits": calculate_splits,
    "calculate_nutrition": calculate_nutrition,
}

PACING_AGENT_TOOLS = [RETRIEVE_KNOWLEDGE_SCHEMA, CALCULATE_SPLITS_SCHEMA]
NUTRITION_AGENT_TOOLS = [RETRIEVE_KNOWLEDGE_SCHEMA, CALCULATE_NUTRITION_SCHEMA]
MENTAL_AGENT_TOOLS = [RETRIEVE_KNOWLEDGE_SCHEMA]
```

**Expected output:** Tool schemas the LLM understands + working implementations you can test independently.

---

## Day 5: Individual Agent Implementation

### Learning (1 hr)

**Complete DeepLearning.AI Course**
- Finish: Lessons 4-5 (Chains, Q&A over Documents)
- Key takeaway: How to structure multi-step LLM workflows

### Building (5 hrs)

**Task 1: Create Base Agent Class**

Create `backend/agents/base.py`:
```python
from openai import OpenAI
import json
import os
from dotenv import load_dotenv
from typing import Optional
from backend.agents.tools import TOOL_REGISTRY

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class BaseAgent:
    """
    Base class for specialized agents.

    Handles:
    - System prompt injection
    - Tool calling loop
    - Response generation
    """

    def __init__(
        self,
        name: str,
        system_prompt: str,
        tools: list[dict],
        model: str = "gpt-4o-mini"
    ):
        self.name = name
        self.system_prompt = system_prompt
        self.tools = tools
        self.model = model

    def _execute_tool(self, tool_name: str, arguments: dict) -> str:
        """Execute a tool and return result as string."""
        if tool_name not in TOOL_REGISTRY:
            return f"Error: Unknown tool {tool_name}"

        try:
            result = TOOL_REGISTRY[tool_name](**arguments)
            if isinstance(result, dict):
                return json.dumps(result, indent=2)
            return str(result)
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"

    def run(
        self,
        user_message: str,
        context: Optional[dict] = None,
        max_tool_calls: int = 3
    ) -> str:
        """
        Run the agent on a user message.

        Args:
            user_message: The user's question/request
            context: Optional dict with runner profile, race info, etc.
            max_tool_calls: Prevent infinite tool loops

        Returns:
            Agent's final response string
        """
        # Build messages
        messages = [
            {"role": "system", "content": self._build_system_prompt(context)},
            {"role": "user", "content": user_message}
        ]

        tool_calls_made = 0

        while tool_calls_made < max_tool_calls:
            # Call LLM
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools if self.tools else None,
                tool_choice="auto" if self.tools else None
            )

            assistant_message = response.choices[0].message

            # If no tool calls, we're done
            if not assistant_message.tool_calls:
                return assistant_message.content

            # Process tool calls
            messages.append(assistant_message)

            for tool_call in assistant_message.tool_calls:
                tool_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)

                print(f"[{self.name}] Calling tool: {tool_name}({arguments})")

                result = self._execute_tool(tool_name, arguments)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })

                tool_calls_made += 1

        # If we hit max tool calls, get final response
        response = client.chat.completions.create(
            model=self.model,
            messages=messages
        )

        return response.choices[0].message.content

    def _build_system_prompt(self, context: Optional[dict]) -> str:
        """Inject context into system prompt."""
        prompt = self.system_prompt

        if context:
            context_str = "\n\n## Runner Context\n"
            context_str += f"```json\n{json.dumps(context, indent=2)}\n```"
            prompt += context_str

        return prompt
```

**Task 2: Implement Specialized Agents**

Create `backend/agents/specialists.py`:
```python
from backend.agents.base import BaseAgent
from backend.agents.tools import PACING_AGENT_TOOLS, NUTRITION_AGENT_TOOLS, MENTAL_AGENT_TOOLS

class PacingAgent(BaseAgent):
    """Specialist in race pacing strategy."""

    def __init__(self):
        system_prompt = """You are an expert running coach specializing in race pacing strategy.

Your role is to create personalized pacing plans based on:
- The runner's training data and predicted race time
- The specific course profile (elevation changes)
- Weather conditions on race day

## Guidelines
1. ALWAYS use the retrieve_knowledge tool to ground your advice in expert sources
2. Use calculate_splits to generate specific mile-by-mile targets
3. Consider the runner's experience level when recommending strategy
4. For hilly courses, recommend effort-based pacing rather than strict pace
5. Account for weather impacts (heat = slower pace needed)

## Output Format
Provide your pacing plan with:
- Recommended overall strategy (even/negative/positive) and WHY
- Mile-by-mile splits OR segment-based targets
- Key landmarks to watch (e.g., "ease up on mile 8 hill")
- Contingency advice for if they're ahead/behind target

Always cite the expert sources that informed your recommendations."""

        super().__init__(
            name="PacingAgent",
            system_prompt=system_prompt,
            tools=PACING_AGENT_TOOLS
        )


class NutritionAgent(BaseAgent):
    """Specialist in race nutrition and hydration."""

    def __init__(self):
        system_prompt = """You are an expert sports nutritionist specializing in endurance running.

Your role is to create personalized fueling plans based on:
- Expected race duration
- Weather conditions (temperature, humidity)
- The runner's experience and any stated preferences

## Guidelines
1. ALWAYS use the retrieve_knowledge tool to ground your advice in expert sources
2. Use calculate_nutrition to get baseline requirements
3. Recommend SPECIFIC timing (e.g., "take gel at mile 6, 12, 18")
4. Include pre-race nutrition (night before, morning of)
5. Address hydration strategy for each aid station
6. Consider caffeine timing for late-race boost

## Output Format
Provide your nutrition plan with:
- Pre-race fueling (48hrs before through morning of)
- During-race fueling schedule with specific times/miles
- Hydration strategy
- What to do if stomach issues arise

Always cite the expert sources that informed your recommendations."""

        super().__init__(
            name="NutritionAgent",
            system_prompt=system_prompt,
            tools=NUTRITION_AGENT_TOOLS
        )


class MentalPrepAgent(BaseAgent):
    """Specialist in mental preparation and race psychology."""

    def __init__(self):
        system_prompt = """You are a sports psychologist specializing in endurance running.

Your role is to help runners mentally prepare for their race:
- Build confidence based on their training
- Provide strategies for tough moments
- Create personalized mantras and focus cues

## Guidelines
1. ALWAYS use the retrieve_knowledge tool to ground your advice in expert sources
2. Be specific to THIS runner's situation (use context provided)
3. Address the specific challenges of their goal race
4. Provide actionable techniques, not generic motivation
5. Include strategies for "the wall" (miles 18-22 in marathon)

## Output Format
Provide your mental prep plan with:
- Pre-race visualization routine
- 2-3 personal mantras based on their training
- Mile-segment mental strategies (early, middle, late race)
- Emergency mental tools for crisis moments

Always cite the expert sources that informed your recommendations."""

        super().__init__(
            name="MentalPrepAgent",
            system_prompt=system_prompt,
            tools=MENTAL_AGENT_TOOLS
        )
```

**Task 3: Test Each Agent**

Create `backend/agents/test_agents.py`:
```python
"""Manual testing for agents."""
from backend.agents.specialists import PacingAgent, NutritionAgent, MentalPrepAgent

# Sample context (would come from Week 1 pipeline in real use)
sample_context = {
    "runner": {
        "avg_weekly_mileage": 35,
        "consistency_score": 75,
        "predicted_marathon_time": 225,  # 3:45
        "long_run_pace": 9.5
    },
    "race": {
        "name": "Chicago Marathon",
        "distance_miles": 26.2,
        "date": "2025-10-12"
    },
    "weather": {
        "temperature_f": 55,
        "humidity_percent": 65,
        "wind_mph": 8
    },
    "course": {
        "profile": "flat",
        "notable_features": ["flat and fast", "downtown canyons create wind tunnels"]
    }
}

def test_pacing_agent():
    print("\n" + "="*60)
    print("PACING AGENT TEST")
    print("="*60)

    agent = PacingAgent()
    response = agent.run(
        "Create a pacing strategy for my marathon goal of 3:45",
        context=sample_context
    )
    print(response)

def test_nutrition_agent():
    print("\n" + "="*60)
    print("NUTRITION AGENT TEST")
    print("="*60)

    agent = NutritionAgent()
    response = agent.run(
        "What should my fueling plan be for a 3:45 marathon in 55°F weather?",
        context=sample_context
    )
    print(response)

def test_mental_agent():
    print("\n" + "="*60)
    print("MENTAL PREP AGENT TEST")
    print("="*60)

    agent = MentalPrepAgent()
    response = agent.run(
        "Help me prepare mentally for my first marathon",
        context=sample_context
    )
    print(response)

if __name__ == "__main__":
    test_pacing_agent()
    test_nutrition_agent()
    test_mental_agent()
```

**Expected output:** Each agent should call tools, retrieve relevant knowledge, and produce grounded advice.

---

## Day 6: Orchestrator + Full Integration

### Learning (1 hr)

**Orchestration Patterns**
- Read: [LangChain - Agent Types](https://python.langchain.com/docs/modules/agents/agent_types/)
- Key patterns:
  - Router: Decides which specialist to call
  - Sequential: Calls agents in order
  - Parallel: Calls multiple agents, combines results

### Building (5 hrs)

**Task 1: Build Orchestrator**

Create `backend/agents/orchestrator.py`:
```python
from backend.agents.specialists import PacingAgent, NutritionAgent, MentalPrepAgent
from backend.pipeline import build_runner_profile, prepare_race_context
from backend.models import RaceInfo
from openai import OpenAI
import json
import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class RaceCoachOrchestrator:
    """
    Master orchestrator that coordinates specialist agents.

    Modes:
    1. Full strategy: Calls all agents, combines into complete race plan
    2. Specific query: Routes to most relevant agent
    """

    def __init__(self):
        self.pacing_agent = PacingAgent()
        self.nutrition_agent = NutritionAgent()
        self.mental_agent = MentalPrepAgent()

    def generate_full_strategy(
        self,
        access_token: str,
        race_info: RaceInfo
    ) -> dict:
        """
        Generate a complete race strategy by calling all agents.

        Returns structured dict with all three components.
        """
        # Build context from runner's Strava data
        profile = build_runner_profile(access_token)
        context = prepare_race_context(profile, race_info)

        # Call each agent
        print("[Orchestrator] Generating pacing strategy...")
        pacing_response = self.pacing_agent.run(
            f"Create a detailed pacing strategy for {race_info.name} ({race_info.distance_miles} miles). "
            f"My goal is to finish based on my predicted time.",
            context=context
        )

        print("[Orchestrator] Generating nutrition plan...")
        nutrition_response = self.nutrition_agent.run(
            f"Create a fueling and hydration plan for {race_info.name}.",
            context=context
        )

        print("[Orchestrator] Generating mental prep plan...")
        mental_response = self.mental_agent.run(
            f"Help me mentally prepare for {race_info.name}.",
            context=context
        )

        # Combine into final strategy
        strategy = {
            "race": race_info.model_dump(),
            "runner_profile": {
                "avg_weekly_mileage": profile.avg_weekly_mileage,
                "consistency_score": profile.consistency_score,
                "predicted_time_minutes": profile.predicted_marathon_time,
            },
            "pacing_strategy": pacing_response,
            "nutrition_plan": nutrition_response,
            "mental_preparation": mental_response,
            "generated_at": context["generated_at"]
        }

        return strategy

    def answer_question(
        self,
        question: str,
        access_token: Optional[str] = None,
        race_info: Optional[RaceInfo] = None
    ) -> str:
        """
        Answer a specific question by routing to the best agent.

        Uses a simple classifier to determine routing.
        """
        # Build context if we have credentials
        context = None
        if access_token and race_info:
            profile = build_runner_profile(access_token)
            context = prepare_race_context(profile, race_info)

        # Route to appropriate agent
        agent, category = self._route_question(question)

        print(f"[Orchestrator] Routing to {category} agent...")
        return agent.run(question, context=context)

    def _route_question(self, question: str) -> tuple:
        """
        Classify question and route to appropriate agent.

        Simple keyword-based routing. Could be upgraded to LLM-based.
        """
        question_lower = question.lower()

        pacing_keywords = ["pace", "split", "speed", "fast", "slow", "mile time", "negative split", "hill"]
        nutrition_keywords = ["gel", "fuel", "eat", "drink", "hydration", "nutrition", "carb", "water", "electrolyte"]
        mental_keywords = ["mental", "nervous", "anxiety", "mantra", "focus", "motivation", "wall", "tough", "confidence"]

        pacing_score = sum(1 for kw in pacing_keywords if kw in question_lower)
        nutrition_score = sum(1 for kw in nutrition_keywords if kw in question_lower)
        mental_score = sum(1 for kw in mental_keywords if kw in question_lower)

        if pacing_score >= nutrition_score and pacing_score >= mental_score:
            return (self.pacing_agent, "pacing")
        elif nutrition_score >= mental_score:
            return (self.nutrition_agent, "nutrition")
        else:
            return (self.mental_agent, "mental")


def generate_strategy_summary(strategy: dict) -> str:
    """
    Create a human-readable summary of the full strategy.

    This is what gets displayed to the user.
    """
    summary = f"""
# Race Strategy: {strategy['race']['name']}

**Date:** {strategy['race']['date']}
**Distance:** {strategy['race']['distance_miles']} miles
**Predicted Finish:** {strategy['runner_profile']['predicted_time_minutes']:.0f} minutes

---

## Pacing Strategy

{strategy['pacing_strategy']}

---

## Nutrition Plan

{strategy['nutrition_plan']}

---

## Mental Preparation

{strategy['mental_preparation']}

---

*Generated by Race Coach on {strategy['generated_at']}*
"""
    return summary
```

**Task 2: Create End-to-End Test**

Create `backend/test_full_pipeline.py`:
```python
"""Full integration test: Strava → Agents → Strategy"""
from backend.agents.orchestrator import RaceCoachOrchestrator, generate_strategy_summary
from backend.auth_flow import get_valid_token
from backend.models import RaceInfo
from datetime import datetime
import json

def main():
    # Get Strava token
    print("Getting Strava access token...")
    token = get_valid_token()

    # Define target race
    race = RaceInfo(
        name="Spring Marathon",
        distance_miles=26.2,
        date=datetime(2025, 4, 15),
        location="Boston, MA"
    )

    # Generate full strategy
    print("\nGenerating full race strategy...")
    orchestrator = RaceCoachOrchestrator()
    strategy = orchestrator.generate_full_strategy(token, race)

    # Save raw strategy
    with open("strategy_output.json", "w") as f:
        json.dump(strategy, f, indent=2, default=str)
    print("Raw strategy saved to strategy_output.json")

    # Generate readable summary
    summary = generate_strategy_summary(strategy)
    with open("strategy_summary.md", "w") as f:
        f.write(summary)
    print("Readable summary saved to strategy_summary.md")

    # Also print to console
    print("\n" + "="*60)
    print(summary)

if __name__ == "__main__":
    main()
```

**Expected output:** Complete race strategy document combining all three agents' outputs.

---

## Day 7: Buffer + Polish

**Time:** 4 hrs (flexible)

### Code Review Checklist

Before moving to Week 3, verify:

- [ ] All knowledge base files are saved with proper attribution
- [ ] `python backend/rag/embedder.py` generates embeddings without errors
- [ ] `python backend/rag/vector_store.py` uploads to Pinecone successfully
- [ ] `python backend/rag/retriever.py` returns relevant results for test queries
- [ ] Each agent calls tools and returns grounded advice
- [ ] Orchestrator successfully combines all agents
- [ ] `python backend/test_full_pipeline.py` produces a complete strategy
- [ ] No API keys are committed to git
- [ ] Requirements.txt is up to date

### Polish Tasks

1. Add error handling for API failures (OpenAI, Pinecone)
2. Add retry logic with exponential backoff
3. Improve tool schemas with better descriptions
4. Test edge cases (no running data, very short races, extreme weather)

### Optional Enhancements

If you have extra time:
- Add confidence scores to agent outputs
- Implement conversation memory (multi-turn questions)
- Create a simple CLI interface for testing

---

## Week 2 Deliverables

By end of week, you should have:

1. **Curated knowledge base** - 10-15 quality sources on pacing, nutrition, mental prep
2. **Embedding pipeline** - Chunking → embedding → Pinecone upload
3. **Retrieval system** - Query → relevant chunks with confidence threshold
4. **Three specialist agents** - Pacing, Nutrition, Mental with tool use
5. **Orchestrator** - Routes queries, generates full strategies
6. **Full integration** - Strava data → agents → complete race plan

### File Structure After Week 2

```
backend/
├── __init__.py
├── auth_flow.py
├── fetch_data.py
├── processor.py
├── predictor.py
├── models.py
├── weather.py
├── pipeline.py
├── knowledge/
│   ├── raw/
│   │   ├── pacing/
│   │   ├── nutrition/
│   │   └── mental/
│   ├── processed/
│   ├── chunks.json
│   ├── embeddings.json
│   └── sources.md
├── rag/
│   ├── __init__.py
│   ├── chunker.py
│   ├── embedder.py
│   ├── vector_store.py
│   └── retriever.py
├── agents/
│   ├── __init__.py
│   ├── base.py
│   ├── tools.py
│   ├── specialists.py
│   └── orchestrator.py
└── test_full_pipeline.py
```

---

## Learning Resources Summary

| Resource | Time | When |
|----------|------|------|
| [Word Embeddings Video](https://www.youtube.com/watch?v=viZrOnJclY0) | 15 min | Day 1 |
| [OpenAI Embeddings Guide](https://platform.openai.com/docs/guides/embeddings) | 30 min | Day 1 |
| [Pinecone - Similarity Search](https://www.pinecone.io/learn/what-is-similarity-search/) | 30 min | Day 1 |
| [LangChain Text Splitters](https://python.langchain.com/docs/modules/data_connection/document_transformers/) | 30 min | Day 2 |
| [Pinecone Quickstart](https://docs.pinecone.io/guides/get-started/quickstart) | 45 min | Day 3 |
| [Lilian Weng - Agents](https://lilianweng.github.io/posts/2023-06-23-agent/) | 1 hr | Day 4 |
| [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling) | 45 min | Day 4 |
| [DeepLearning.AI - LangChain Course](https://www.deeplearning.ai/short-courses/langchain-for-llm-application-development/) | 3-4 hrs | Days 4-5 |

**Total structured learning: ~10-11 hours**

---

## Next Week Preview

Week 3 will wrap this AI system in a production API:
- FastAPI endpoints for strategy generation
- GPX file upload for course analysis
- Multi-modal vision input (upload course photos)
- Semantic caching to reduce API costs
- Database persistence for generated strategies
- Deployment to Railway
