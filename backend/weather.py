import os
import requests
from datetime import datetime
from models import WeatherConditions, WeatherImpact
from dotenv import load_dotenv
load_dotenv()    

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY") 
GEOCODE_URL = "https://api.openweathermap.org/geo/1.0/direct"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"

def geocode_location(city: str, state: str = "", country: str = "US") -> tuple[float, float] | None:
    if not OPENWEATHER_API_KEY:
        raise ValueError("OPENWEATHER_API_KEY not set in environment")

    # Build location with city, (state optional), country
    query_parts = [city]
    if state: query_parts.append(state)
    query_parts.append(country)
    query = ",".join(query_parts)

    params = {"q": query, "limit": 1, "appid": OPENWEATHER_API_KEY}

    try:                                                                      
        response = requests.get(GEOCODE_URL, params=params)
        response.raise_for_status()
        data = response.json()

        if not data:
            print(f"Location not found: {query}")
            return None

        return (data[0]["lat"], data[0]["lon"])                               

    except requests.RequestException as e:
        print(f"Geocoding API error: {e}")
        return None

def fetch_weather_forecast(lat: float, lon: float, race_date: datetime) ->  WeatherConditions | None:                                                                  
    if not OPENWEATHER_API_KEY:
        raise ValueError("OPENWEATHER_API_KEY not set in environment")

    # Check if race date is within 5-day forecast window
    days_until_race = (race_date.date() - datetime.now().date()).days
    if days_until_race > 5:
        print(f"Race date {race_date.date()} is beyond 5-day forecast window")
        return None
    if days_until_race < 0:
        print(f"Race date {race_date.date()} is in the past")
        return None

    params = {"lat": lat, "lon": lon, "units": "imperial", "appid": OPENWEATHER_API_KEY}

    try:
        # Get 5 days of 8x 3-hour blocks of weather data
        response = requests.get(FORECAST_URL, params=params)                  
        response.raise_for_status()
        data = response.json()

        # Find the forecast block closest to race start time
        race_timestamp = race_date.timestamp()
        best_forecast = None                                                          
        best_time = 0

        for forecast in data["list"]:
            forecast_time = forecast["dt"]
            # Only consider forecasts at or before race time
            if forecast_time <= race_timestamp and forecast_time > best_time:
                best_time = forecast_time
                best_forecast = forecast

        # Fallback: if race is before first forecast, use first available
        if not best_forecast:
            best_forecast = data["list"][0]

        # Extract weather conditions                                          
        return WeatherConditions(
            temperature_f=best_forecast["main"]["temp"],
            temperature_c=(best_forecast["main"]["temp"] - 32) * 5 / 9,
            feels_like_f=best_forecast["main"]["feels_like"],
            feels_like_c=(best_forecast["main"]["feels_like"] - 32) * 5 / 9,
            wind_speed_mph=best_forecast["wind"]["speed"],
            wind_gust_mph=best_forecast["wind"].get("gust"),
            conditions=best_forecast["weather"][0]["description"],
            precipitation_mm=best_forecast.get("rain", {}).get("3h", 0)
        )

    except requests.RequestException as e:
        print(f"Weather API error: {e}")
        return None

def assess_weather_impacts(weather: WeatherConditions) -> WeatherImpact:
    temperature_impact = 0
    wind_impact = 0
    risk_factors = []

    temp = weather.feels_like_f
    if (temp > 60): temperature_impact = 0.01 * (temp - 60) / 5
    elif (temp < 30): temperature_impact = 0.01 * (30 - temp) / 3
    else: temperature_impact = 0
    
    wind_speed = weather.wind_speed_mph
    if (wind_speed >= 20): wind_impact = 0.05
    elif (wind_speed >= 15): wind_impact = 0.025
    elif (wind_speed >= 10): wind_impact = 0.01
    else: wind_impact = 0

    # Identify possible risk factors
    precipitation = weather.precipitation_mm
    gust_speed = weather.wind_gust_mph
    if (precipitation is not None and precipitation >= 12): risk_factors.append("Heavy Rain")
    if temp >= 80: risk_factors.append("High Heat")
    if temp <= 25: risk_factors.append("Extreme Cold")
    if (gust_speed is not None and gust_speed >= 20): risk_factors.append("Strong Gusts")
    
    return WeatherImpact(
        weather=weather,
        wind_impact=wind_impact,
        temperature_impact=temperature_impact,
        total_impact=(wind_impact + temperature_impact),
        risk_factors=risk_factors
    )

def get_race_weather(city: str, state: str, race_date: datetime, country: str = "US") -> tuple[WeatherConditions, WeatherImpact] | None:
      coords = geocode_location(city, state, country)
      if not coords:
          return None
      
      lat, lon = coords
      weather = fetch_weather_forecast(lat, lon, race_date)
      if (weather == None): return None
      weather_impact = assess_weather_impacts(weather)
      return (weather, weather_impact)