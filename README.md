# 🌾 Arkrishitech

A free farm decision engine for South Asian smallholders. Draw your field on a map → NASA weather history + 16-day forecast + USB-connected soil sensors (or clearly labelled simulated readings) → best crops, yield and profit ranges, risk, dated calendar, alerts, what-if, and an "Elder" chat with chemical-free traditional practices.

Numbers come from a transparent engine (FAO-56 water balance replayed over 30 past seasons), never from an AI model.

## Run it (2 minutes)
**Mac / Linux / UNO Q:** `./run.sh`   **Windows:** double-click `run.bat`
Then open **http://localhost:8000**. Needs Python 3.10+ and internet the first time (NASA data is cached on disk afterwards).

Try it without internet using synthetic weather (demo only): `KS_OFFLINE=1 ./run.sh`

## Live sensors and simulation fallback
- On **My Farm**, the sensor panel starts in **SIMULATION** mode with clearly labelled changing sample readings and bar-history charts. There is no manual “add sensors” form.
- Click **Connect sensor device** in Chrome/Edge on `http://localhost:8000` or HTTPS, choose the board's USB serial port, and use **115200 baud**. The browser reads newline-delimited JSON: `{"moisture":45.2,"soil_t":18.4,"ph":6.3}`.
- The included Arduino sketch streams that JSON every 2 seconds. Disconnecting the board returns to simulation mode. Device readings are stored against the selected field when one exists.
- Calibrate the capacitive moisture sensor (dry/wet raw values) and pH interface before treating readings as measurements. The pH slope/offset in the sketch are placeholders.

## Talk to the Indigenous Knowledge Assistant
- On **My Farm**, choose Nepali, English or Hindi, then tap **Speak** and allow microphone access. Your spoken question is transcribed and sent to the same farming knowledge retrieval endpoint as typed questions.
- Answers can be read aloud automatically; each answer also has its own **Listen** button. **Stop audio** stops playback.
- Voice uses the browser Web Speech APIs (speech recognition and speech synthesis), not a separate hosted voice AI. Recognition availability and Nepali voice quality depend on the browser, operating system and installed speech services. Chrome/Edge on localhost or HTTPS is recommended. Typing always remains available.

## Traditional knowledge retrieval
The Indigenous Knowledge Assistant uses a local retrieval pipeline over `backend/app/knowledge.json`: it scores the user's question against titles, keywords and practice text, retrieves the closest records, and returns the source and verification status. It does not call a cloud model and does not invent an answer when no useful record matches. Current entries are marked pending local review; collect local knowledge with consent and attribution before claiming it is validated Indigenous knowledge.

## Use it
Three focused tabs:
1. **My Farm**: draw your field on the map (polygon or square tool, top-left of the map). Weather strip, alerts and the live sensor bar charts fill in on the left. Connect a USB device or use the labelled simulation fallback. On the right: best crops with match bars (tap one), the farm calendar for that crop (tap a day for its tasks, tick them off), and the Indigenous Knowledge Assistant.
2. **Compare Crops**: farm conditions, the four farmer inputs (water, tools, seed, workers), ranking verdict and side-by-side crop table.
3. **Simulate**: what-if scenarios for the selected crop, recalculated by the backend engine.

## Test
```
cd backend
pip install -r requirements.txt
python -m pytest -q        # 13 tests, offline
```

## Structure
```
backend/app/engine.py    science: ET0, soil bucket, yield, replay, rank, schedule, alerts, what-if
backend/app/data.py      NASA POWER + Open-Meteo with disk cache (works offline after first load)
backend/app/db.py        SQLite: fields, sensor readings
backend/app/kb.py        local retrieval-grounded knowledge assistant (no external LLM)      backend/app/knowledge.json  practices
backend/app/main.py      API + serves frontend/
frontend/                index.html, css, js (Leaflet map, 4 screens)
device/                  Arduino UNO Q sketch + Python reader (UNTESTED on hardware, see VERIFY notes)
deploy/krishi.service    auto-start on the UNO Q
docs/                    BLUEPRINT.md, PROJECT.md (full design)
```

## API
`GET /api/health` · `POST /api/analyze` · `POST /api/schedule` · `POST /api/whatif` · `POST/GET /api/fields` · `POST /api/sensors/{id}` · `GET /api/sensors/{id}/latest` · `POST /api/chat`  (interactive docs at `/docs`)

## Put it on the Arduino UNO Q
1. Copy this folder to the board (e.g. `/home/arduino/krishi-saathi`), run `./run.sh` once, check from a phone on the same Wi-Fi: `http://<board-address>:8000`.
2. Auto-start: edit and install `deploy/krishi.service` (instructions inside).
3. Sensors: wire per `device/sketch/sketch.ino` (3.3 V only!), create an App Lab app from `device/`, set `KS_FIELD_ID` to your saved field id.
   The the USB serial sketch must be compiled for your exact board/core and sensor wiring; it has not been validated on your physical hardware in this session.

## Honest limits (please read)
- Crop numbers (Kc, Ky, root depth, sowing windows, prices, costs) in `engine.py` are **starter values**. Have a local agronomist verify them before farmers rely on them.
- Traditional-knowledge entries are common community practices marked **PENDING verification**. Collect real ones with consent and credit.
- NASA data is ~50 km grid; the soil sensor matters. pH probes drift and need calibration.
- No pest/disease/nutrient model. Map tiles need internet; weather uses cache offline.
- Open-Meteo is free for non-commercial use; recheck terms if this ever earns money.

## Compare & simulate

After drawing a field on **My farm**, open **Compare and simulate** or use the
button beneath the crop recommendations. The comparison table is generated
from the backend `/api/analyze` response. Selecting a crop loads its schedule
and what-if scenarios; changing water, tools, seed, or worker choices reruns
analysis. Use **Run simulation again** to force a fresh calculation with the
current field and choices. Keep the backend terminal running while using the
web app.


## Branding update
- The supplied Arkrishitech logo is used in the application header.
- Browser favicon files are generated from the logo emblem (`frontend/assets/favicon.ico` and PNG sizes); the Icons8 favicon library is linked in the footer as a resource for additional icon choices.
- The interface uses a responsive forest-green, warm-white and muted-gold visual system.

## Visual theme
The interface uses the requested Arkrishitech palette (`#243010`, `#87A330`, `#A1C349`, `#CAD593`, `#2A3C24`) and the Roboto Slab typeface from Google Fonts. Interface pictograms are loaded from Icons8 in a consistent iOS line style; the footer links to Icons8 for attribution and licensing details. An internet connection is required for remote font and icon assets.
