import os
import json
import urllib.request
import urllib.parse
from typing import TypedDict
from langgraph.graph import StateGraph, END


class WeatherState(TypedDict):
    city: str
    weather_data: dict
    error: str


def fetch_weather(state: WeatherState) -> WeatherState:
    city = state.get("city", "").strip()
    if not city:
        return {**state, "error": "No city provided.", "weather_data": {}}

    api_key = os.environ.get("OPENWEATHER_API_KEY", "")
    if not api_key:
        return {**state, "error": "OPENWEATHER_API_KEY is not set.", "weather_data": {}}

    encoded_city = urllib.parse.quote(city)
    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?q={encoded_city}&appid={api_key}&units=metric"
    )

    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            raw = response.read()
            data = json.loads(raw)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        try:
            err_data = json.loads(body)
            msg = err_data.get("message", str(e))
        except Exception:
            msg = str(e)
        return {**state, "error": f"API error: {msg}", "weather_data": {}}
    except Exception as e:
        return {**state, "error": f"Request failed: {str(e)}", "weather_data": {}}

    weather = data.get("weather", [{}])[0]
    main = data.get("main", {})
    wind = data.get("wind", {})
    sys = data.get("sys", {})
    clouds = data.get("clouds", {})

    result = {
        "city": data.get("name", city),
        "country": sys.get("country", ""),
        "condition": weather.get("main", ""),
        "description": weather.get("description", "").capitalize(),
        "temperature_c": main.get("temp"),
        "feels_like_c": main.get("feels_like"),
        "temp_min_c": main.get("temp_min"),
        "temp_max_c": main.get("temp_max"),
        "humidity_percent": main.get("humidity"),
        "pressure_hpa": main.get("pressure"),
        "wind_speed_mps": wind.get("speed"),
        "wind_direction_deg": wind.get("deg"),
        "cloudiness_percent": clouds.get("all"),
        "visibility_m": data.get("visibility"),
    }

    return {**state, "weather_data": result, "error": ""}


def build_graph():
    builder = StateGraph(WeatherState)
    builder.add_node("fetch_weather", fetch_weather)
    builder.set_entry_point("fetch_weather")
    builder.add_edge("fetch_weather", END)
    return builder.compile()


graph = build_graph()
