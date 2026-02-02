# Week 2: AI Agent + Knowledge Base (Simplified)

**Goal:** Build a single intelligent agent with running expertise embedded in its context. The agent receives all runner data and produces a comprehensive race strategy.

**Time Budget:** ~30 hours
- Learning: 8-10 hours
- Building: 20-22 hours

---

## Prerequisites

Before starting, ensure you have:
- Week 1 complete with working `RunnerProfile` pipeline
- OpenAI API key from https://platform.openai.com (or Anthropic key)
- Add to `.env`:
  ```
  OPENAI_API_KEY=sk-...
  ```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     RACE COACH AGENT                         │
│                                                              │
│  System Prompt:                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ • Running expertise (pacing, nutrition, mental)     │    │
│  │ • Tool definitions (calculate_splits, etc.)         │    │
│  │ • Output format instructions                        │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  User Message:                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ • RunnerProfile (VDOT, weekly mileage, etc.)        │    │
│  │ • RaceInfo (distance, date, location)               │    │
│  │ • WeatherConditions (temp, wind, humidity)          │    │
│  │ • CourseAnalysis (elevation profile)                │    │
│  │ • User preferences (gel brand, pacing style)        │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  Tools Available:                                            │
│  • calculate_splits(goal_time, distance, strategy)          │
│  • calculate_nutrition(duration, temperature)               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │       Complete Strategy        │
              │  • Pacing plan with splits     │
              │  • Nutrition schedule          │
              │  • Mental preparation          │
              │  • Weather adjustments         │
              └───────────────────────────────┘
```

**Why One Agent Instead of Three:**
- Single agent produces more coherent, integrated strategy
- Avoids coordination overhead between agents
- Simpler to debug and iterate on prompts
- The three "domains" are just sections of one output

---

## Day 1-2: Knowledge Curation + System Prompt

### Learning (3 hrs)

**Prompt Engineering Fundamentals**
- Read: [OpenAI - Prompt Engineering Guide](https://platform.openai.com/docs/guides/prompt-engineering)
- Read: [Anthropic - Prompt Design](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching)
- Key concepts:
  - System vs user messages
  - Few-shot examples
  - Chain-of-thought reasoning
  - Output formatting (JSON, markdown)

**Context Window Management**
- GPT-4o: 128K tokens (~100 pages of text)
- Claude 3: 200K tokens
- Your knowledge base should be < 20K tokens (plenty of room for runner data)

### Building (5 hrs)

**Task 1: Create Knowledge Base Directory**

```
backend/
├── knowledge/
│   ├── pacing.md          # Pacing strategies and guidelines
│   ├── nutrition.md       # Fueling and hydration advice
│   ├── mental.md          # Mental preparation techniques
│   └── sources.md         # Attribution
```

**Task 2: Curate Pacing Knowledge**

Create `backend/knowledge/pacing.md`:
```markdown
# Pacing Expertise

## Core Principles

### Even Pacing
The most efficient strategy for flat courses. Run each mile at the same pace.
- Physiologically optimal: consistent oxygen consumption
- Mentally manageable: no dramatic pace changes
- Best for: experienced runners on flat courses

### Negative Splits
Run the second half faster than the first. Start conservatively.
- First half: 2-3% slower than goal pace
- Second half: gradually increase to 2-3% faster
- Best for: hilly courses (hills often in first half), hot weather

### Positive Splits
Run the first half faster than the second. Common but often unintentional.
- Often results from going out too fast
- Acceptable if: course has significant downhill start
- Warning: going out more than 5% fast often leads to "blowing up"

## Pacing by Distance

### 5K
- Start at goal pace or slightly faster (5-10 sec/mile)
- Middle mile: settle into rhythm
- Final mile: push if you have it
- Short enough that mistakes are survivable

### 10K
- First mile: goal pace (resist urge to go fast)
- Miles 2-5: settle, stay relaxed
- Mile 6+: gradually increase effort
- "If you feel good at mile 2, you're probably going too fast"

### Half Marathon
- First 3 miles: slightly conservative (10-15 sec/mile slow)
- Miles 4-10: goal pace, find your rhythm
- Miles 11-13.1: race it if you feel good
- Key: don't waste energy in crowded start

### Marathon
- Miles 1-6: 10-20 sec/mile slower than goal (bank NOTHING)
- Miles 7-16: goal pace, steady
- Miles 17-20: maintain, don't surge
- Miles 21-26.2: whatever you have left
- "The first half is run with your legs, the second half with your head"

## Hill Pacing

### Uphills
- Maintain EFFORT, not pace
- Expect 15-30 sec/mile slower on moderate hills
- Shorten stride, increase cadence
- Lean slightly forward from ankles

### Downhills
- Don't brake excessively (quad damage)
- Lean forward, let gravity help
- Control, don't hammer
- Save your quads for later miles

## Weather Adjustments

| Temperature | Pace Adjustment |
|-------------|-----------------|
| 40-50°F | Optimal, no change |
| 50-60°F | +0-10 sec/mile |
| 60-70°F | +10-20 sec/mile |
| 70-80°F | +20-40 sec/mile |
| 80°F+ | +40-60 sec/mile or DNS |

Humidity over 70%: add additional 10-20 sec/mile
Wind over 15 mph: add 5-15 sec/mile (depends on direction)
```

**Task 3: Curate Nutrition Knowledge**

Create `backend/knowledge/nutrition.md`:
```markdown
# Nutrition Expertise

## Core Principles

### The 60-90g/hour Rule
- For efforts over 60 minutes: consume 60-90g carbs per hour
- Trained athletes can absorb more with practice
- Start conservative, build tolerance in training

### Timing Matters
- First gel: 30-45 minutes into race (not at start)
- Subsequent gels: every 30-45 minutes
- Stop fueling 15-20 min before finish (won't help, may cause GI issues)

## By Race Distance

### 5K-10K
- No fueling needed during race
- Pre-race: light meal 2-3 hours before
- Hydration: small amount before, none during (unless very hot)

### Half Marathon
- 1-2 gels total for most runners
- First gel: mile 5-6
- Second gel: mile 10 (optional)
- Water at aid stations as needed

### Marathon
- 3-5 gels typical (or equivalent)
- Gel schedule: miles 5, 10, 15, 20
- Practice your exact race-day nutrition in long runs
- Mix gels with water, not sports drink (sugar overload)

## Hydration

### General Guidelines
- 4-8 oz every 15-20 minutes in hot conditions
- Thirst is a decent guide for trained runners
- Clear urine pre-race = well hydrated

### Aid Station Strategy
- Slow down slightly to drink properly
- Pinch cup to create a spout
- Walk through if needed (30 sec won't ruin your race)
- Don't skip stations in hot weather

### Electrolytes
- Important in hot weather (70°F+) or efforts over 90 min
- Salt tabs: 1 every 45-60 min in heat
- Sports drink can replace some gels

## Pre-Race Nutrition

### Night Before
- Carb-rich dinner (pasta, rice, bread)
- Nothing exotic or unusual
- Moderate portion (don't overeat)
- Limit fiber

### Morning Of
- 2-3 hours before start
- 200-400 calories, mostly carbs
- Toast, banana, oatmeal, bagel
- Avoid fat, protein, fiber
- Coffee is fine if you're used to it

## GI Distress Prevention

### Common Causes
- New foods on race day
- High fiber within 24 hours
- Too much fat/protein morning of
- Gels without water
- Anxiety (train your gut too!)

### Solutions
- Stick to trained foods
- Take gels with water
- Consider multiple small sips vs big drinks
- Know where porta-potties are on course
```

**Task 4: Curate Mental Knowledge**

Create `backend/knowledge/mental.md`:
```markdown
# Mental Preparation Expertise

## Core Principles

### Process Over Outcome
- Focus on controllables: effort, form, breathing
- Don't obsess over splits every mile
- Outcome goals (time) vs process goals (smooth running)

### Chunking
- Break the race into manageable segments
- Marathon: "I just need to get to mile 10, then reassess"
- Never think about the total distance remaining

## Pre-Race Mental Prep

### The Week Before
- Visualization: run the race in your mind
- Review your pacing plan so it's automatic
- Accept nervousness as excitement
- Trust your training (the hay is in the barn)

### Race Morning
- Stick to routines
- Avoid making decisions (have everything planned)
- Warm up as trained
- Find your calm

### At the Start Line
- Deep breaths: 4 count in, 6 count out
- Positive self-talk: "I'm ready, I've trained for this"
- Start slow, let excitement settle
- Don't chase others at the start

## During the Race

### Miles 1-6 (Marathon) / First Third
- "Patience, patience, patience"
- This should feel easy
- If you're breathing hard, you're going too fast
- Hold back even if you feel amazing

### Middle Miles
- Find your rhythm
- Zone out or zone in (both work)
- Stay present (not "18 more miles to go")
- Mantras: "Smooth and steady", "Relax and run"

### The Hard Miles (Marathon 18-22 / The "Wall")
- This is where the race is won
- Expect it to hurt—that's normal
- Shorten your focus: "just this mile"
- Count steps, focus on form
- "I can do anything for 10 minutes"

### Final Miles
- Now you can push
- Draw on the crowd/course energy
- "This is what you trained for"
- Pain is temporary, finishing is forever

## Managing Crisis Moments

### "I Want to Stop"
1. First, take inventory: am I injured or just hurting?
2. If just hurting: keep moving, slow down if needed
3. Focus on the next aid station, not the finish
4. Talk to yourself: "This will pass"

### Hitting the Wall
1. Slow down (seriously, slow down)
2. Take in calories immediately (gel + water)
3. Walk an aid station if needed
4. Shorten stride, increase cadence
5. Focus on running form, not pace

### Weather/Course Surprise
1. Adjust expectations immediately
2. New goal: finish smart
3. It's the same conditions for everyone
4. Run YOUR race, not someone else's

## Mantras by Situation

| Situation | Mantra |
|-----------|--------|
| Starting too fast | "Patience wins races" |
| Middle mile boredom | "Smooth is fast" |
| It's getting hard | "I can do hard things" |
| Wanting to quit | "Trust the training" |
| Final push | "Leave it all out there" |
```

**Task 5: Create Sources Attribution**

Create `backend/knowledge/sources.md`:
```markdown
# Knowledge Base Sources

## Pacing
- Jack Daniels' Running Formula (VDOT methodology)
- Pfitzinger & Douglas - Advanced Marathoning
- Fellrnr Wiki - Pacing strategies
- Various running coach interviews and blogs

## Nutrition
- Asker Jeukendrup research on carbohydrate intake
- Sports Nutrition for Endurance Athletes (Ryan)
- Runners Connect - Marathon fueling guides
- Science of Ultra podcast (nutrition episodes)

## Mental Preparation
- Matt Fitzgerald - How Bad Do You Want It?
- Sports psychology research on self-talk
- r/AdvancedRunning community wisdom
- Professional runner interviews

All content synthesized and adapted for this educational project.
```

**Expected output:** Three markdown files totaling < 5000 words (well under 20K tokens)

---

## Day 3: System Prompt Engineering

### Learning (2 hrs)

**Function Calling**
- Read: [OpenAI - Function Calling](https://platform.openai.com/docs/guides/function-calling)
- Key concepts:
  - Define function schemas (JSON)
  - LLM decides when to call
  - You execute and return results
  - LLM incorporates into response

### Building (4 hrs)

**Task 1: Create Tool Definitions**

Create `backend/agent/tools.py`:
```python
"""
Tools available to the Race Coach agent.
"""
from typing import Optional

# ============== TOOL SCHEMAS (for LLM) ==============

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
                    "description": "Pacing strategy"
                },
                "elevation_adjustments": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Optional: pace adjustment per mile for elevation (positive = slower)"
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
        "description": "Calculate fueling needs for a race based on duration and conditions.",
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
                }
            },
            "required": ["expected_duration_minutes"]
        }
    }
}

AGENT_TOOLS = [CALCULATE_SPLITS_SCHEMA, CALCULATE_NUTRITION_SCHEMA]

# ============== TOOL IMPLEMENTATIONS ==============

def calculate_splits(
    goal_time_minutes: float,
    distance_miles: float,
    strategy: str,
    elevation_adjustments: Optional[list[float]] = None
) -> dict:
    """Calculate mile splits based on strategy."""
    base_pace = goal_time_minutes / distance_miles
    splits = []

    for mile in range(1, int(distance_miles) + 1):
        pace = base_pace

        # Adjust for strategy
        if strategy == "negative":
            progress = mile / distance_miles
            adjustment = 1.03 - (0.06 * progress)  # Start 3% slow, end 3% fast
            pace *= adjustment
        elif strategy == "positive":
            progress = mile / distance_miles
            adjustment = 0.98 + (0.04 * progress)  # Start 2% fast, slow down
            pace *= adjustment

        # Apply elevation adjustment if provided
        if elevation_adjustments and mile <= len(elevation_adjustments):
            pace += elevation_adjustments[mile - 1]

        splits.append({
            "mile": mile,
            "pace_minutes": round(pace, 2),
            "cumulative_time": round(sum(s["pace_minutes"] for s in splits) + pace, 2)
        })

    # Handle partial final mile
    remaining = distance_miles - int(distance_miles)
    if remaining > 0:
        final_pace = base_pace  # Use base pace for partial
        partial_time = final_pace * remaining
        splits.append({
            "mile": f"{int(distance_miles)}-{distance_miles}",
            "pace_minutes": round(final_pace, 2),
            "cumulative_time": round(splits[-1]["cumulative_time"] + partial_time, 2)
        })

    return {
        "splits": splits,
        "average_pace": round(goal_time_minutes / distance_miles, 2),
        "strategy": strategy
    }


def calculate_nutrition(
    expected_duration_minutes: float,
    temperature_f: float = 60
) -> dict:
    """Calculate nutrition plan based on duration and conditions."""
    hours = expected_duration_minutes / 60

    # Base carb needs
    if hours < 1:
        gels_needed = 0
    else:
        carbs_per_hour = 45  # Conservative estimate
        total_carbs = (hours - 0.5) * carbs_per_hour  # Don't count first 30 min
        gels_needed = max(0, int(total_carbs / 25))  # ~25g per gel

    # Hydration adjustments for heat
    base_fluid_oz_per_hour = 20
    if temperature_f > 70:
        base_fluid_oz_per_hour += (temperature_f - 70) * 0.5
    total_fluid_oz = base_fluid_oz_per_hour * hours

    # Build gel schedule
    gel_schedule = []
    if gels_needed > 0:
        first_gel = 35  # minutes
        interval = 35  # minutes between gels
        for i in range(gels_needed):
            time = first_gel + (i * interval)
            if time < expected_duration_minutes - 15:  # Don't take one too close to finish
                gel_schedule.append({
                    "number": i + 1,
                    "time_minutes": time,
                    "note": "with water"
                })

    return {
        "total_gels": len(gel_schedule),
        "gel_schedule": gel_schedule,
        "total_fluid_oz": round(total_fluid_oz),
        "fluid_per_hour_oz": round(base_fluid_oz_per_hour),
        "electrolyte_note": "salt tabs recommended" if temperature_f > 75 else "standard sports drink sufficient"
    }


# Tool registry for execution
TOOL_REGISTRY = {
    "calculate_splits": calculate_splits,
    "calculate_nutrition": calculate_nutrition,
}
```

**Task 2: Create System Prompt Builder**

Create `backend/agent/prompts.py`:
```python
"""
System prompt construction for the Race Coach agent.
"""
from pathlib import Path

def load_knowledge() -> str:
    """Load all knowledge files into a single string."""
    knowledge_dir = Path(__file__).parent.parent / "knowledge"

    sections = []
    for filename in ["pacing.md", "nutrition.md", "mental.md"]:
        filepath = knowledge_dir / filename
        if filepath.exists():
            sections.append(filepath.read_text())

    return "\n\n---\n\n".join(sections)


SYSTEM_PROMPT_TEMPLATE = """You are an expert running coach creating a personalized race strategy.

## Your Expertise

{knowledge}

---

## Your Task

Create a comprehensive race strategy with THREE sections:

### 1. Pacing Strategy
- Recommend overall approach (even, negative, positive splits) with reasoning
- Provide mile-by-mile or segment-by-segment targets
- Account for course elevation and weather
- Include contingency advice (what if ahead/behind target)

### 2. Nutrition Plan
- Pre-race fueling (night before, morning of)
- During-race nutrition schedule with specific times/miles
- Hydration strategy at aid stations
- Adjustments for weather conditions

### 3. Mental Preparation
- Pre-race visualization and routine
- 2-3 personalized mantras based on this runner's situation
- Strategies for different race segments
- Crisis management techniques

## Guidelines

- Be SPECIFIC to this runner's fitness level and race
- Use the calculate_splits tool for pace calculations
- Use the calculate_nutrition tool for fueling calculations
- Ground all advice in the expertise above
- Be encouraging but realistic
- Format output in clear markdown with headers

## Output Format

Structure your response with clear headers:
```
## Pacing Strategy
[content]

## Nutrition Plan
[content]

## Mental Preparation
[content]
```
"""


def build_system_prompt() -> str:
    """Build the complete system prompt with embedded knowledge."""
    knowledge = load_knowledge()
    return SYSTEM_PROMPT_TEMPLATE.format(knowledge=knowledge)


def build_user_message(
    runner_profile: dict,
    race_info: dict,
    weather: dict = None,
    course_analysis: dict = None,
    user_preferences: dict = None
) -> str:
    """Build the user message with all context."""
    parts = []

    parts.append("## Runner Profile")
    parts.append(f"- Recent VDOT: {runner_profile.get('vdot_max', 'Unknown')}")
    parts.append(f"- Average weekly mileage: {runner_profile.get('avg_weekly_mileage', 'Unknown')} miles")
    parts.append(f"- Training consistency (CV): {runner_profile.get('coefficient_of_variance', 'Unknown')}")
    if runner_profile.get('predicted_race_times'):
        parts.append("- Predicted race times:")
        for pred in runner_profile['predicted_race_times']:
            parts.append(f"  - {pred['race']}: {pred['ideal_time']:.1f} min")

    parts.append("\n## Target Race")
    parts.append(f"- Race: {race_info.get('name', 'Unknown')}")
    parts.append(f"- Distance: {race_info.get('distance_miles', 'Unknown')} miles")
    parts.append(f"- Date: {race_info.get('date', 'Unknown')}")
    parts.append(f"- Location: {race_info.get('location', 'Unknown')}")

    if weather:
        parts.append("\n## Weather Forecast")
        parts.append(f"- Temperature: {weather.get('temperature_f', 'Unknown')}°F")
        parts.append(f"- Feels like: {weather.get('feels_like_f', 'Unknown')}°F")
        parts.append(f"- Wind: {weather.get('wind_speed_mph', 'Unknown')} mph")
        parts.append(f"- Conditions: {weather.get('conditions', 'Unknown')}")

    if course_analysis:
        parts.append("\n## Course Analysis")
        parts.append(f"- Total elevation gain: {course_analysis.get('total_elevation_gain_ft', 'Unknown')} ft")
        parts.append(f"- Difficulty: {course_analysis.get('difficulty_rating', 'Unknown')}")
        if course_analysis.get('key_segments'):
            parts.append("- Key segments:")
            for seg in course_analysis['key_segments']:
                parts.append(f"  - Mile {seg['mile']}: {seg['advice']}")

    if user_preferences:
        parts.append("\n## Runner Preferences")
        for key, value in user_preferences.items():
            parts.append(f"- {key.replace('_', ' ').title()}: {value}")

    parts.append("\n---")
    parts.append("\nCreate a complete race strategy for this runner.")

    return "\n".join(parts)
```

---

## Day 4-5: Agent Implementation

### Learning (2 hrs)

**Complete Learning**
- Read: [Anthropic - Tool Use](https://docs.anthropic.com/en/docs/build-with-claude/tool-use) (if using Claude)
- Practice: Make a few API calls with function calling

### Building (8 hrs)

**Task 1: Create Agent Class**

Create `backend/agent/coach.py`:
```python
"""
Race Coach agent - single unified agent for strategy generation.
"""
from openai import OpenAI
import json
import os
from dotenv import load_dotenv
from typing import Optional

from .prompts import build_system_prompt, build_user_message
from .tools import AGENT_TOOLS, TOOL_REGISTRY

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class RaceCoachAgent:
    """
    Single unified agent for generating race strategies.

    Handles:
    - System prompt with embedded running knowledge
    - User context injection
    - Tool calling loop
    - Response generation
    """

    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        self.system_prompt = build_system_prompt()
        self.tools = AGENT_TOOLS

    def _execute_tool(self, tool_name: str, arguments: dict) -> str:
        """Execute a tool and return result as string."""
        if tool_name not in TOOL_REGISTRY:
            return f"Error: Unknown tool {tool_name}"

        try:
            result = TOOL_REGISTRY[tool_name](**arguments)
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"

    def generate_strategy(
        self,
        runner_profile: dict,
        race_info: dict,
        weather: dict = None,
        course_analysis: dict = None,
        user_preferences: dict = None,
        max_tool_calls: int = 5
    ) -> str:
        """
        Generate a complete race strategy.

        Args:
            runner_profile: Dict with VDOT, mileage, predictions
            race_info: Dict with race name, distance, date, location
            weather: Optional weather forecast
            course_analysis: Optional GPX analysis
            user_preferences: Optional dict of user preferences
            max_tool_calls: Limit tool calling loops

        Returns:
            Complete strategy as markdown string
        """
        # Build messages
        user_message = build_user_message(
            runner_profile, race_info, weather, course_analysis, user_preferences
        )

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_message}
        ]

        tool_calls_made = 0

        while tool_calls_made < max_tool_calls:
            # Call LLM
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools,
                tool_choice="auto"
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

                print(f"[Agent] Calling: {tool_name}({list(arguments.keys())})")

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


# Singleton for easy access
agent = RaceCoachAgent()
```

**Task 2: Create Integration Module**

Create `backend/agent/__init__.py`:
```python
"""
Agent module for Race Coach.
"""
from .coach import RaceCoachAgent, agent
from .tools import calculate_splits, calculate_nutrition

__all__ = [
    "RaceCoachAgent",
    "agent",
    "calculate_splits",
    "calculate_nutrition",
]
```

**Task 3: Create End-to-End Test**

Create `backend/test_agent.py`:
```python
"""Test the Race Coach agent with real data."""
from agent import agent
from pipeline import build_runner_profile
from models import RaceInfo
from datetime import datetime

def test_with_sample_data():
    """Test with hardcoded sample data (no Strava needed)."""
    sample_profile = {
        "vdot_max": 45.2,
        "avg_weekly_mileage": 32.5,
        "coefficient_of_variance": 0.23,
        "predicted_race_times": [
            {"race": "5K", "ideal_time": 22.5},
            {"race": "10K", "ideal_time": 46.8},
            {"race": "half_marathon", "ideal_time": 103.5},
            {"race": "marathon", "ideal_time": 215.0}
        ]
    }

    race_info = {
        "name": "Chicago Marathon",
        "distance_miles": 26.2,
        "date": "2025-10-12",
        "location": "Chicago, IL"
    }

    weather = {
        "temperature_f": 55,
        "feels_like_f": 52,
        "wind_speed_mph": 12,
        "conditions": "Partly cloudy"
    }

    user_prefs = {
        "gel_brand": "Maurten",
        "pacing_style": "conservative"
    }

    print("Generating strategy...")
    print("=" * 60)

    strategy = agent.generate_strategy(
        runner_profile=sample_profile,
        race_info=race_info,
        weather=weather,
        user_preferences=user_prefs
    )

    print(strategy)

    # Save to file for review
    with open("test_strategy_output.md", "w") as f:
        f.write(strategy)
    print("\n" + "=" * 60)
    print("Strategy saved to test_strategy_output.md")


def test_with_strava():
    """Test with real Strava data."""
    print("Building runner profile from Strava...")
    profile = build_runner_profile()

    # Convert to dict for agent
    profile_dict = {
        "vdot_max": max((w.vdot_max for w in profile.recent_weeks if w.vdot_max), default=None),
        "avg_weekly_mileage": profile.avg_weekly_mileage,
        "coefficient_of_variance": profile.coefficient_of_variance,
        "predicted_race_times": [
            {"race": p.race, "ideal_time": p.ideal_time}
            for p in profile.predicted_race_times
        ] if profile.predicted_race_times else []
    }

    race_info = {
        "name": "Spring Half Marathon",
        "distance_miles": 13.1,
        "date": "2025-04-15",
        "location": "Local City"
    }

    print("Generating strategy...")
    strategy = agent.generate_strategy(
        runner_profile=profile_dict,
        race_info=race_info
    )

    print(strategy)


if __name__ == "__main__":
    # Test with sample data first
    test_with_sample_data()

    # Uncomment to test with Strava
    # test_with_strava()
```

---

## Day 6-7: Testing + Polish

### Building (4-6 hrs)

**Task 1: Test Different Scenarios**

Test the agent with various inputs:
- Different race distances (5K, half, marathon)
- Different fitness levels (VDOT 35 vs 50)
- Hot weather vs cold weather
- Flat course vs hilly course
- Different user preferences

**Task 2: Refine System Prompt**

Based on outputs, iterate on:
- Knowledge content (add missing info)
- Output format instructions
- Tool usage guidance
- Tone and specificity

**Task 3: Verify Tool Outputs**

Make sure:
- `calculate_splits` produces reasonable pace targets
- `calculate_nutrition` gives appropriate gel counts
- Edge cases handled (very short races, very long races)

---

## Week 2 Deliverables

By end of week, you should have:

1. **Curated knowledge base** - 3 markdown files with running expertise
2. **System prompt** - Well-structured prompt with embedded knowledge
3. **Tool definitions** - `calculate_splits` and `calculate_nutrition` with schemas
4. **Agent implementation** - Single `RaceCoachAgent` class
5. **Working end-to-end** - Sample data → Agent → Complete strategy

### File Structure After Week 2

```
backend/
├── __init__.py
├── pipeline.py
├── models.py
├── auth_flow.py
├── fetch_data.py
├── weather.py
├── data_processing/
│   ├── __init__.py
│   ├── processor.py
│   ├── clean_data.py
│   ├── categorize_activities.py
│   ├── calculate_vdot.py
│   └── calculate_race_performances.py
├── knowledge/
│   ├── pacing.md
│   ├── nutrition.md
│   ├── mental.md
│   └── sources.md
├── agent/
│   ├── __init__.py
│   ├── coach.py
│   ├── prompts.py
│   └── tools.py
└── test_agent.py
```

---

## Learning Resources Summary

| Resource | Time | When |
|----------|------|------|
| [OpenAI Prompt Engineering](https://platform.openai.com/docs/guides/prompt-engineering) | 1.5 hrs | Day 1 |
| [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling) | 1 hr | Day 3 |
| Running knowledge research | 2-3 hrs | Days 1-2 |
| Practice API calls | 1-2 hrs | Days 3-4 |

**Total structured learning: ~8-10 hours**

---

## Next Week Preview

Week 3 will wrap this agent in a production API:
- FastAPI endpoints for strategy generation
- GPX file upload for course analysis
- PostgreSQL for user preferences and strategies
- Railway deployment
