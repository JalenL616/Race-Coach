from typing import Optional, Literal

CALCULATE_SPLITS_SCHEMA = {
    "type": "function",
    "function": {
        "name": "calculate_splits",
        "description":  """Calculate mile-by-mile split times for a race based on goal time and pacing strategy.
                            Instructions:
                            1. Call this after get_weather_adjusted_pace to generate specific mile-by-mile pacing targets.
                            2. Group the splits array into phases based on your knowledge base (e.g., miles 1-6, 7-20, 21-26 for marathon)
                            3. Add effort levels to each phase from INTENSITY_GUIDELINES.md (e.g., 5/10, 7/10, 9/10)
                            4. Add mental cues from MENTAL_PREP_GUIDE.md for each phase
                            5. Extract average_pace and pass it to calculate_nutrition
                            6. Create a formatted pacing table with Phase headers, Mile numbers, Target Pace, and Cumulative Time

                            Returns:
                            - splits: Use the entire array to create mile-by-mile pacing tables in your output
                            - average_pace: Pass this to calculate_nutrition as average_pace_minutes parameter
                            - pace_formatted: Use these for human-readable output
                            """,
        "parameters": {
            "type": "object",
            "properties": {
                "pace_strategy": {
                    "type": "string",
                    "enum": ["even", "negative", "positive"],
                    "description": "Mile splits progression even (consistent pace), negative "
                                    "(start slower then increase pace), positive (start fast and hold on)"
                },
                "goal_time_minutes": {
                    "type": "number",
                    "description": "Target finish time in minutes"
                },
                "distance_miles": {
                    "type": "number",
                    "description": "Race distance in miles"
                },
                "elevation_adjustments": {
                    "type": "array",
                    "items": {
                        "type": "number"
                    },
                    "description": "Mile by mile pace adjustment in seconds"
                }
            },
            "required": ["goal_time_minutes", "distance_miles", "pace_strategy"]
        }
    }
}

CALCULATE_NUTRITION_SCHEMA = {
    "type": "function",
    "function": {
        "name": "calculate_nutrition",
        "description": """Calculate fueling and hydration strategy based on race duration, weather conditions, 
                    and available aid stations.
                    Instructions:
                    1. Call this function after calculate_splits so you have the average_pace to pass in.
                    2. Use gel_schedule to create a fueling timeline in your strategy
                    3. If aid_stations were provided, emphasize the aid_station_plan
                    4. Use carry_recommendations to tell runner what to pack/carry
                    5. Integrate hydration_schedule into your aid station guidance
                    6. Include the pre_race guidance in your race morning checklist
                
                    Returns: 
                    - gel_schedule: Create a timeline of when to fuel (use both time_minutes and mile for. dual reference)
                    - hydration_schedule: Aid station strategy (what to drink, how much)
                    - aid_station_plan: Mile-by-mile action plan (most useful for runner)
                    - carry_recommendations: Pre-race packing list
                """,
        "parameters": {
            "type": "object",
            "properties": {
                "expected_duration_minutes": {
                    "type": "number",
                    "description": "Expected race duration in minutes"
                },
                "distance_miles": {
                    "type": "number",
                    "description": "Expected race distance in miles to calculate mile markers for gels"
                },
                "temperature_f": {
                    "type": "number",
                    "description": "Temperature on race day in fahrenheit"
                },
                "average_pace_per_mile": {
                    "type": "number",
                    "description": "Average pace per mile to calculate gel time to mile markers"
                },
                "aid_stations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "mile": {
                                "type": "number",
                                "description": "Mile marker where aid station is located"
                            },
                            "water": {
                                "type": "boolean",
                                "description": "Whether water is available"
                            },
                            "electrolyte": {
                                "type": "boolean",
                                "description": "Whether electrolyte drinks are available"
                            },
                            "gels": {
                                "type": "boolean",
                                "description": "Whether gels are available"
                            }
                        },
                        "required": ["mile", "water"]
                    },
                    "description": "Array of aid station locations and what they offer. "
                                    "If not provided, assumes standard spacing with water/electrolyte"
                }
            },
            "required": ["expected_duration_minutes"]
        }
    }
}

AGENT_TOOLS = [
    CALCULATE_SPLITS_SCHEMA,
    CALCULATE_NUTRITION_SCHEMA
]
