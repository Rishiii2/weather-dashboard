"""
weather.py — ForgeTrack Week 2
Weather + Air Quality CLI Dashboard
Uses OpenWeatherMap API (free tier)
"""

import os           # to read environment variables (API key)
import json         # to read/write search history
import requests     # to make HTTP GET requests to the API
from dotenv import load_dotenv  # to load variables from .env file

# ─────────────────────────────────────────────
# STEP 1: Load environment variables from .env
# ─────────────────────────────────────────────
# load_dotenv() reads the .env file and puts all its variables
# into os.environ so we can access them safely.
load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY")

# File where we store search history (last 5 cities)
HISTORY_FILE = "history.json"

# ─────────────────────────────────────────────────────────────────────
# AQI ADVISORY MAP
# The Air Quality Index from OpenWeatherMap goes from 1 to 5.
# We map each number to a label and a human-readable advisory.
# A dict is perfect here — instant lookup by key (the AQI number).
# ─────────────────────────────────────────────────────────────────────
AQI_INFO = {
    1: ("Good",      "Air quality is satisfactory. No precautions needed."),
    2: ("Fair",      "Acceptable quality. Unusually sensitive people should consider reducing prolonged outdoor activity."),
    3: ("Moderate",  "Sensitive individuals should reduce outdoor activity."),
    4: ("Poor",      "Everyone should reduce prolonged outdoor exertion."),
    5: ("Very Poor", "Everyone should avoid outdoor activity."),
}


# ═══════════════════════════════════════════════════════
#  SECTION A — FILE I/O (Reading & Writing JSON history)
# ═══════════════════════════════════════════════════════

def load_history() -> list:
    """
    Reads history.json from disk and returns a list of past searches.
    If the file doesn't exist yet (first run), returns an empty list.

    The "try/except" here catches:
     - FileNotFoundError  →  first time the app runs, no file yet
     - json.JSONDecodeError →  file exists but is corrupted / empty
    """
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)      # parse JSON text → Python list
    except (FileNotFoundError, json.JSONDecodeError):
        return []                    # safe default: pretend history is empty


def save_history(history: list) -> None:
    """
    Writes the history list to history.json.
    json.dump() converts a Python object → JSON text.
    indent=2 makes the file human-readable (pretty-printed).
    """
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


def add_to_history(entry: dict) -> None:
    """
    Adds one search result (a dict) to the front of history.
    Keeps only the last 5 entries.

    Why a list of dicts?
      - List  → ordered, so we keep chronological order
      - Dict  → each entry has named fields (city, temp, etc.)
    """
    history = load_history()
    history.insert(0, entry)   # insert at position 0 = newest first
    history = history[:5]      # slice: keep only the first 5 items
    save_history(history)


# ══════════════════════════════════════════
#  SECTION B — API CALLS (requests library)
# ══════════════════════════════════════════

def get_weather(city: str) -> dict | None:
    """
    Calls the OpenWeatherMap 'Current Weather' endpoint.

    HOW REST APIs WORK:
      - We send an HTTP GET request to a URL
      - The URL has "query parameters" (key=value pairs after the ?)
      - The server responds with JSON text
      - requests.get() fetches it; .json() converts it to a Python dict

    URL structure:
      https://api.openweathermap.org/data/2.5/weather
        ?q=Mumbai          ← city name
        &appid=YOUR_KEY    ← your API key
        &units=metric      ← °C instead of °F
    """
    url = "https://api.openweathermap.org/data/2.5/weather"

    # "params" dict → requests automatically appends them as ?key=value
    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric",   # metric = Celsius; imperial = Fahrenheit
    }

    try:
        # make the actual HTTP GET request; timeout=10 avoids hanging forever
        response = requests.get(url, params=params, timeout=10)

        # ── STATUS CODE HANDLING ──────────────────────────────────────
        # 200 = OK  →  parse and return the data
        # 404 = Not Found  →  bad city name
        # 401 = Unauthorized  →  wrong API key
        # Any other 4xx/5xx  →  something else went wrong
        # ─────────────────────────────────────────────────────────────
        if response.status_code == 200:
            return response.json()    # parse JSON response → Python dict
        elif response.status_code == 404:
            print(f"\n  ✗  City '{city}' not found. Check the spelling.\n")
            return None
        elif response.status_code == 401:
            print("\n  ✗  Invalid API key. Check your .env file.\n")
            return None
        else:
            print(f"\n  ✗  API error (status {response.status_code}). Try again later.\n")
            return None

    except requests.exceptions.ConnectionError:
        # No internet connection
        print("\n  ✗  No internet connection. Check your network.\n")
        return None
    except requests.exceptions.Timeout:
        # Server took too long to respond
        print("\n  ✗  Request timed out. The server may be slow — try again.\n")
        return None
    except requests.exceptions.RequestException as e:
        # Catch-all for any other requests-related error
        print(f"\n  ✗  Unexpected network error: {e}\n")
        return None


def get_aqi(lat: float, lon: float) -> int | None:
    """
    Calls the OpenWeatherMap 'Air Pollution' endpoint.
    Requires latitude & longitude (we get these from the weather response).

    Returns the AQI integer (1–5), or None if something fails.
    """
    url = "https://api.openweathermap.org/data/2.5/air_pollution"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": API_KEY,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # The AQI is buried at: data["list"][0]["main"]["aqi"]
            # We use .get() with defaults at every level to avoid KeyError
            # if any field is unexpectedly missing.
            aqi = (
                data
                .get("list", [{}])[0]   # get first item in "list" array
                .get("main", {})         # get the "main" sub-dict
                .get("aqi")              # get the "aqi" value
            )
            return aqi
        else:
            return None   # AQI unavailable; we'll show weather without it
    except requests.exceptions.RequestException:
        return None


# ════════════════════════════════════════
#  SECTION C — DISPLAY (Output Formatting)
# ════════════════════════════════════════

def display_weather(city: str, weather_data: dict, aqi: int | None) -> dict:
    """
    Extracts values from the API response dict and prints a clean dashboard.
    Also builds an "entry" dict for the history file.

    KEY CONCEPT — .get() vs direct access:
      weather_data["main"]["temp"]   → crashes with KeyError if "main" is missing
      weather_data.get("main", {}).get("temp", "N/A")  → safely returns "N/A"

    We always use .get() when parsing API responses because we can't 100%
    guarantee every field will be present.
    """

    # ── Extract fields safely ─────────────────────────────────────────
    main       = weather_data.get("main", {})
    wind       = weather_data.get("wind", {})
    weather    = weather_data.get("weather", [{}])[0]  # list → grab index 0
    sys_data   = weather_data.get("sys", {})
    coord      = weather_data.get("coord", {})

    temp       = main.get("temp", "N/A")
    feels_like = main.get("feels_like", "N/A")
    humidity   = main.get("humidity", "N/A")
    wind_speed = wind.get("speed", "N/A")
    condition  = weather.get("description", "N/A").title()  # .title() = Title Case
    country    = sys_data.get("country", "")

    # Convert wind speed m/s → km/h  (API gives m/s in metric mode)
    if isinstance(wind_speed, (int, float)):
        wind_kmh = round(wind_speed * 3.6, 1)
    else:
        wind_kmh = "N/A"

    # Round temperatures to 1 decimal place
    if isinstance(temp, (int, float)):
        temp = round(temp, 1)
    if isinstance(feels_like, (int, float)):
        feels_like = round(feels_like, 1)

    # ── AQI label & advisory ──────────────────────────────────────────
    if aqi and aqi in AQI_INFO:
        aqi_label, advisory = AQI_INFO[aqi]
        aqi_display = f"{aqi} — {aqi_label}"
    else:
        aqi_display = "Unavailable"
        advisory    = "AQI data could not be fetched."

    # ── Print the dashboard ───────────────────────────────────────────
    width = 52
    print()
    print("┌" + "─" * width + "┐")
    print(f"│  🌤  Weather in {city}, {country}".ljust(width + 1) + "│")
    print("├" + "─" * width + "┤")
    print(f"│  Temperature   : {temp}°C  (Feels like {feels_like}°C)".ljust(width + 1) + "│")
    print(f"│  Humidity      : {humidity}%".ljust(width + 1) + "│")
    print(f"│  Wind Speed    : {wind_kmh} km/h".ljust(width + 1) + "│")
    print(f"│  Condition     : {condition}".ljust(width + 1) + "│")
    print("├" + "─" * width + "┤")
    print(f"│  💨  Air Quality Index : {aqi_display}".ljust(width + 1) + "│")
    print(f"│  Advisory      : {advisory[:width - 18]}".ljust(width + 1) + "│")
    if len(advisory) > width - 18:
        # wrap long advisories to second line
        print(f"│    {advisory[width - 18:]}".ljust(width + 1) + "│")
    print("└" + "─" * width + "┘")
    print()

    # ── Build history entry dict ──────────────────────────────────────
    entry = {
        "city":       f"{city}, {country}",
        "temp":       f"{temp}°C",
        "feels_like": f"{feels_like}°C",
        "humidity":   f"{humidity}%",
        "wind":       f"{wind_kmh} km/h",
        "condition":  condition,
        "aqi":        aqi_display,
    }
    return entry


def display_history(history: list) -> None:
    """Prints all saved history entries in a readable format."""
    if not history:
        print("\n  No search history yet.\n")
        return

    print()
    print("  ── SEARCH HISTORY (last 5) ──────────────────")
    for i, entry in enumerate(history, start=1):
        # enumerate() gives us (index, value) tuples → clean numbered list
        print(f"\n  [{i}] {entry.get('city', 'Unknown')}")
        print(f"       Temp      : {entry.get('temp', 'N/A')}  ({entry.get('feels_like', 'N/A')} feels like)")
        print(f"       Humidity  : {entry.get('humidity', 'N/A')}")
        print(f"       Wind      : {entry.get('wind', 'N/A')}")
        print(f"       Condition : {entry.get('condition', 'N/A')}")
        print(f"       AQI       : {entry.get('aqi', 'N/A')}")
    print()


# ══════════════════════
#  SECTION D — MAIN LOOP
# ══════════════════════

def main():
    """
    Entry point. Runs the interactive CLI loop.

    THE LOOP:
      while True → keep running until user types "quit"
      input()    → pauses and waits for the user to type something
      .strip()   → removes leading/trailing whitespace
      .lower()   → lowercases input so "Quit" / "QUIT" both work
    """

    # ── Validate API key before doing anything ────────────────────────
    if not API_KEY:
        print("\n  ✗  OPENWEATHER_API_KEY not found!")
        print("     Create a .env file with: OPENWEATHER_API_KEY=your_key_here\n")
        return

    # ── Show banner ───────────────────────────────────────────────────
    print()
    print("  ╔══════════════════════════════════════╗")
    print("  ║   🌍  WEATHER + AQI DASHBOARD  v1.0  ║")
    print("  ║   ForgeTrack Week 2 · SAE DTU         ║")
    print("  ╚══════════════════════════════════════╝")
    print()
    print("  Commands: type a city name, 'history', or 'quit'")
    print("  Tip: temperatures shown in °C, wind in km/h")

    # ── Show last search on startup ───────────────────────────────────
    history = load_history()
    if history:
        last = history[0]
        print(f"\n  Last search: {last.get('city')} — {last.get('temp')}, {last.get('condition')}")

    # ── Main interactive loop ─────────────────────────────────────────
    while True:
        print()
        user_input = input("  Enter city name: ").strip()

        # Empty input — ask again
        if not user_input:
            print("  Please type a city name.")
            continue

        # Normalize to lowercase for comparison only
        cmd = user_input.lower()

        if cmd in ("quit", "exit", "q"):
            print("\n  Goodbye! 👋\n")
            break

        elif cmd == "history":
            history = load_history()
            display_history(history)

        else:
            # Treat the input as a city name
            city = user_input   # keep original casing for display

            # Step 1: Fetch weather data
            weather_data = get_weather(city)
            if weather_data is None:
                continue   # error already printed inside get_weather()

            # Step 2: Extract coordinates for AQI call
            coord = weather_data.get("coord", {})
            lat = coord.get("lat")
            lon = coord.get("lon")

            # Step 3: Fetch AQI (using coordinates from weather response)
            aqi = None
            if lat is not None and lon is not None:
                aqi = get_aqi(lat, lon)

            # Step 4: Display and save to history
            entry = display_weather(city, weather_data, aqi)
            add_to_history(entry)


# ── Python idiom: only run main() if this file is executed directly ──
# If someone does "import weather" in another file, main() won't auto-run.
if __name__ == "__main__":
    main()
