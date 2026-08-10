"""
Time & Temperature Agent
------------------------
Returns the current local time and temperature for a given location.

Uses:
  - Nominatim (OpenStreetMap) for geocoding — no API key needed
  - Open-Meteo for current weather & timezone — no API key needed
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import TypedDict, Optional

import httpx
from langgraph.graph import StateGraph, START, END


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

class AgentState(TypedDict):
    # Input
    location: str                   # e.g. "Paris" or "New York"

    # Resolved
    latitude: Optional[float]
    longitude: Optional[float]
    timezone: Optional[str]
    display_name: Optional[str]     # human-friendly place name from geocoder

    # Weather data
    temperature: Optional[float]
    temperature_unit: Optional[str]
    local_time: Optional[str]

    # Output
    result: str
    error: Optional[str]


# ---------------------------------------------------------------------------
# Node 1 — Resolve location name → coordinates
# ---------------------------------------------------------------------------

def resolve_location(state: AgentState) -> AgentState:
    location = (state.get("location") or "").strip()
    if not location:
        return {**state, "error": "No location provided. Please specify a city or place name."}

    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": location, "format": "json", "limit": 1}
    headers = {"User-Agent": "OrkestTimeWeatherAgent/1.0"}

    try:
        resp = httpx.get(url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if not data:
            return {**state, "error": f"Could not find location: '{location}'. Try a more specific name."}

        place = data[0]
        return {
            **state,
            "latitude": float(place["lat"]),
            "longitude": float(place["lon"]),
            "display_name": place.get("display_name", location),
            "error": None,
        }
    except httpx.HTTPError as exc:
        return {**state, "error": f"Geocoding request failed: {exc}"}


# ---------------------------------------------------------------------------
# Node 2 — Fetch weather and local time from Open-Meteo
# ---------------------------------------------------------------------------

def fetch_weather_and_time(state: AgentState) -> AgentState:
    if state.get("error"):
        return state

    lat = state["latitude"]
    lon = state["longitude"]

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m",
        "temperature_unit": "celsius",
        "timezone": "auto",          # Open-Meteo infers timezone from coordinates
    }

    try:
        resp = httpx.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        current = data.get("current", {})
        units = data.get("current_units", {})

        temperature = current.get("temperature_2m")
        temp_unit = units.get("temperature_2m", "°C")
        timezone = data.get("timezone", "UTC")

        # Open-Meteo returns local time as "YYYY-MM-DDTHH:MM" in the location's timezone
        raw_time = current.get("time", "")
        try:
            dt = datetime.fromisoformat(raw_time)
            local_time = dt.strftime("%A, %B %d %Y — %I:%M %p")
        except ValueError:
            local_time = raw_time

        return {
            **state,
            "temperature": temperature,
            "temperature_unit": temp_unit,
            "timezone": timezone,
            "local_time": local_time,
            "error": None,
        }
    except httpx.HTTPError as exc:
        return {**state, "error": f"Weather request failed: {exc}"}


# ---------------------------------------------------------------------------
# Node 3 — Format the final response
# ---------------------------------------------------------------------------

def format_response(state: AgentState) -> AgentState:
    if state.get("error"):
        return {**state, "result": f"❌ {state['error']}"}

    # Shorten the display name to just the city/country portion
    display = state.get("display_name", state.get("location", "Unknown"))
    short_name = ", ".join(p.strip() for p in display.split(",")[:2])

    temp = state.get("temperature")
    unit = state.get("temperature_unit", "°C")
    local_time = state.get("local_time", "N/A")
    timezone = state.get("timezone", "")

    # Celsius → Fahrenheit for a friendly dual display
    try:
        temp_f = round(temp * 9 / 5 + 32, 1)
        temp_str = f"{temp}{unit}  ({temp_f}°F)"
    except (TypeError, ValueError):
        temp_str = f"{temp}{unit}"

    result = (
        f"📍 {short_name}\n"
        f"🕐 Local time : {local_time}\n"
        f"🌡️  Temperature : {temp_str}\n"
        f"🌐 Timezone    : {timezone}"
    )

    return {**state, "result": result}


# ---------------------------------------------------------------------------
# Routing helpers
# ---------------------------------------------------------------------------

def route_after_resolve(state: AgentState) -> str:
    return "error_end" if state.get("error") else "fetch_weather_and_time"

def route_after_weather(state: AgentState) -> str:
    return "format_response"   # format_response handles errors too


# ---------------------------------------------------------------------------
# Graph definition
# ---------------------------------------------------------------------------

builder = StateGraph(AgentState)

builder.add_node("resolve_location", resolve_location)
builder.add_node("fetch_weather_and_time", fetch_weather_and_time)
builder.add_node("format_response", format_response)

# Error short-circuit node — just passes state through to END
builder.add_node("error_end", format_response)

builder.add_edge(START, "resolve_location")
builder.add_conditional_edges("resolve_location", route_after_resolve)
builder.add_edge("fetch_weather_and_time", "format_response")
builder.add_edge("format_response", END)
builder.add_edge("error_end", END)

graph = builder.compile()
