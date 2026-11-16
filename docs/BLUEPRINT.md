# Krishi Saathi — BLUEPRINT (source of truth)

Rule: nothing gets built that is not in this file. A new feature is added here FIRST, then built.
Budget: $0. Free tools only. Re-paste this file at the start of any new chat so context is never lost.

## 1. Purpose
Decision engine for South Asian smallholder farmers: draw field on map -> live NASA/forecast data + soil
sensors -> best crops, yield/profit ranges, dated schedule, alerts, and a chemical-free traditional-knowledge
helper. Numbers come from a deterministic engine (FAO-56 water balance). No LLM produces numbers or dates.

## 2. Architecture
HOSTING: everything runs ON the Arduino UNO Q (Debian Linux side): FastAPI serves the API AND the frontend files.
Farmer opens http://<uno-q-address>:8000 on a phone connected to the same Wi-Fi.
UNO Q (Linux, Python) --Wi-Fi--> NASA POWER + Open-Meteo (cached on disk so the app survives internet loss)
Sensors: wired to the UNO Q MCU (STM32U585) -> sketch reads them -> Bridge (RPC) -> Python app on Linux
         -> writes readings into SQLite (same DB the API reads). Manual dry/damp/wet entry stays as fallback.
Remote access away from the farm (optional, later): free tunnel (e.g. Cloudflare Tunnel or Tailscale), verify terms.

## 3. Folder tree (exact)
```
krishi-saathi/
├── BLUEPRINT.md
├── README.md
├── .gitignore
├── backend/
│   ├── requirements.txt
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py          # FastAPI app + all routes + serves ../frontend as static files
│   │   ├── engine.py        # ET0, water bucket, yield, replay, rank, schedule, alerts, whatif   (DONE except whatif)
│   │   ├── data.py          # NASA POWER history, Open-Meteo forecast, offline synthetic data    (DONE)
│   │   ├── db.py            # SQLite: fields, readings
│   │   ├── kb.py            # keyword/TF-IDF search over knowledge.json (the "Elder" chatbot)
│   │   └── knowledge.json   # verified traditional, chemical-free practices (id, title, keywords, text, source)
│   └── tests/
│       ├── test_engine.py
│       └── api_smoke.py
└── frontend/
    ├── index.html           # 4 screens: Farm, Compare, Plan, Elder
    ├── css/style.css
    └── js/
        ├── config.js        # API_URL only
        ├── api.js           # all fetch() calls
        ├── map.js           # Leaflet + draw polygon
        ├── screens.js       # render functions per screen
        └── main.js          # navigation + state
└── device/                  # runs on the Arduino UNO Q via Arduino App Lab (verify layout in step 11)
    ├── sketch/sketch.ino    # MCU: read soil moisture, soil temp, pH; expose via Bridge
    └── python/main.py       # Linux: poll Bridge every N min, write readings to SQLite, run the API service
```

## 4. API contract (backend)
| Method | Path | Purpose |
|---|---|---|
| GET  | /api/health | liveness |
| POST | /api/analyze | polygon+profile+sensors -> field, forecast, alerts, top-5 crops, schedule(top crop) |
| POST | /api/schedule | + crop -> schedule for that crop |
| POST | /api/whatif | + crop -> yield/profit for: mulch, compost, drip, hybrid seed, tiller, +2 workers |
| POST | /api/fields | save field (name, polygon, profile) -> id |
| GET  | /api/fields/{id} | load saved field |
| POST | /api/sensors/{field_id} | store reading {moisture, soil_t, ph, source:"manual"|"device"} |
| GET  | /api/sensors/{field_id}/latest | latest reading |
| POST | /api/chat | {question} -> {answer, title, source, matched:bool} (search only, no LLM) |

Input: `polygon:[[lat,lon],...]`, `profile:{water_l_day, irrigation_eff, soil, seed, workers, tools}`, `sensors:{moisture, soil_t, ph}`.

## 5. Data model (SQLite)
fields(id, name, polygon_json, lat, lon, ha, profile_json, created_at)
readings(id, field_id, ts, moisture, soil_t, ph, source)

## 6. Farmer inputs (only these four taps + map)
Water access (rain/well/canal) · Tools (hand/bullock/tiller) · Seed (saved/improved/hybrid) · Workers (1-2/3-4/5+).
Everything else is auto: area (map), weather (NASA/forecast), soil moisture/temp/pH (sensor or manual).

## 7. Build steps (each ends with a CHECKPOINT the user reports back)
1. Setup: folders, venv, requirements, git.            CP: `python --version`, `pip list` shows fastapi.
2. Engine files + tests pass.                           CP: `pytest` 6 passed.
3. API: main.py, run uvicorn, /docs works.              CP: /api/health ok, /api/analyze returns JSON (offline mode).
4. Live data: run without KS_OFFLINE on user's PC.      CP: analyze returns real NASA-based result.
5. db.py + fields + sensors endpoints.                  CP: save field, post reading, read back.
6. kb.py + knowledge.json + /api/chat.                  CP: "natural fertilizer" returns jeevamrit entry.
7. whatif in engine + /api/whatif.                      CP: tests pass, JSON shows deltas.
8. Frontend: map + Farm screen.                         CP: draw polygon, see weather + alerts.
9. Frontend: Compare table, Plan calendar, Elder chat.  CP: full flow in browser.
10. Run the whole app on the UNO Q (SSH/App Lab, copy project, venv, uvicorn).    CP: phone on same Wi-Fi opens the app.
11. Sensors: wire moisture/temp/pH to MCU, sketch + Bridge + python reader.        CP: readings appear in /api/sensors/{id}/latest.
12. Reliability: cache NASA/forecast to disk, auto-start service on boot, DB backup.  CP: unplug internet, app still works with cached data.
13. (Optional) Remote access tunnel.

## 8. OUT OF SCOPE for v1 (do not build)
LLM chatbot, SMS, user accounts/login, ESP32 or MQTT (UNO Q replaces them), payments, Nepali/Hindi UI (v1.1), pest/disease model,
satellite NDVI, crop-mix planner.

## 9. Known weak points (be honest in UI)
Kc/Ky/prices/sow windows are starter values needing agronomist review. NASA grid is ~50 km: sensors matter.
Free hosting sleeps when idle. Prices and costs are placeholders.

## 10. Hardware and hosting decisions (added after UNO Q confirmed)
- Board: Arduino UNO Q (Qualcomm QRB2210 Linux side + STM32U585 MCU side). Linux runs Python/FastAPI; MCU does real-time sensor I/O.
- MCU logic is 3.3 V (A0/A1 are not 5 V tolerant). Check every sensor's voltage against the official pinout before wiring.
- Sensors (v1): capacitive soil moisture (analog), DS18B20 soil temperature, analog pH probe (cheap pH probes drift: needs calibration, mark as low-trust in UI).
- Free-hosting caveats: only reachable on the farm Wi-Fi unless a tunnel is added; single device = single point of failure (back up the SQLite file).
- First-run speed: ranking replays ~30 years x many dates. Cache results per field+day on the UNO Q. Measure in step 10.
- DECIDED: board is the 4 GB RAM / 32 GB eMMC version (comfortable for FastAPI + SQLite + cached weather).
- Open questions: which sensors are in hand, how many farms per device (assume 1 device = 1 farm).
