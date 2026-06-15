# 🌍 Weather + Air Quality CLI Dashboard

> **ForgeTrack 2026 · Week 2 · Tech Track**  
> A Python CLI app that fetches real-time weather and air quality data from the OpenWeatherMap API.

---

## What it does

- Fetches current **temperature, humidity, wind speed, and weather condition** for any city
- Fetches the **Air Quality Index (AQI)** and displays a health advisory
- **Saves the last 5 searches** to a local JSON file — visible on startup and via the `history` command
- Handles all errors gracefully — bad city names, no internet, invalid API keys

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/Rishiii2/weather-dashboard.git
cd weather-dashboard
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create your `.env` file

```bash
cp .env.example .env
```

Then open `.env` and replace `your_key_here` with your actual API key.

### 4. Get a free API key

Sign up at [openweathermap.org](https://openweathermap.org/api) → go to **API keys** in your profile.  
The free tier allows 60 calls/minute — more than enough.

---

## Running the app

```bash
python weather.py
```

---

## Example output

```
  ╔══════════════════════════════════════╗
  ║   🌍  WEATHER + AQI DASHBOARD  v1.0  ║
  ║   ForgeTrack Week 2 · SAE DTU         ║
  ╚══════════════════════════════════════╝

  Last search: Mumbai, IN — 31.0°C, Haze

  Enter city name: Delhi

┌────────────────────────────────────────────────────┐
│  🌤  Weather in Delhi, IN                          │
├────────────────────────────────────────────────────┤
│  Temperature   : 38.2°C  (Feels like 42.1°C)      │
│  Humidity      : 45%                               │
│  Wind Speed    : 11.5 km/h                         │
│  Condition     : Haze                              │
├────────────────────────────────────────────────────┤
│  💨  Air Quality Index : 4 — Poor                  │
│  Advisory      : Everyone should reduce prolonged  │
│    outdoor exertion.                               │
└────────────────────────────────────────────────────┘
```

---

## Commands

| Command       | What it does                        |
|---------------|-------------------------------------|
| `<city name>` | Fetch weather + AQI for that city   |
| `history`     | Show the last 5 searched cities     |
| `quit`        | Exit the app                        |

---

## Project structure

```
weather-dashboard/
├── weather.py        ← main application
├── requirements.txt  ← Python dependencies
├── .env.example      ← template for environment variables
├── .env              ← YOUR real API key (never committed)
├── .gitignore        ← keeps .env off GitHub
├── history.json      ← auto-created on first search
└── README.md         ← this file
```

---

## Tech used

- `requests` — HTTP GET calls to OpenWeatherMap
- `python-dotenv` — loads API key from `.env` file safely
- `json` — reads/writes search history to disk
- `os` — reads environment variables

---

*Built for SAE DTU ForgeTrack 2026 — Week 2: Data & APIs*
