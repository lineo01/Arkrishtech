# 🌾 Krishi Saathi — The Complete Project Document

**Krishi Saathi** means "farming companion". This one file explains the whole project so that a child can follow the idea, a developer can build it, and any AI model can recreate it from scratch.

---

## 0. How to use this file

**If you are a person:** read Parts 1–3 for the idea, then follow Part 14 (build steps) one at a time.

**If you are an AI model asked to build this project:**
1. Read the whole file before writing any code.
2. Build ONLY what this file describes. Do not add features not listed (see Part 3, "Out of scope").
3. Code in Part 9 is tested and complete: copy it exactly. Parts marked **SPEC** are not written yet: implement them to match the described behavior and acceptance tests.
4. Build in the order of Part 14. After each step, run the check listed there before continuing.
5. Never let an AI language model produce numbers, dates, doses or yields at run time. All numbers come from the engine in Part 8–9.
6. Anything marked **VERIFY** must be checked against official documentation or a local expert; do not guess.

**Status key:** ✅ DONE and tested · 🟡 SPEC (designed, not coded) · 🔲 TODO hardware/field work

---

## 1. The story (explain it like I'm five)

Imagine a farmer named Maya. She has a small piece of land on a hill. Every year she plants the same thing, because that is what she has always done. But the weather is getting strange: sometimes too dry, sometimes too wet. And the computers that give farming advice keep telling her to buy chemicals, and they forget the clever things her grandmother taught her.

Our app is a **helpful friend for Maya**:

1. **She draws her field on a map** with her finger. Like drawing a fence around her garden.
2. **The app asks the sky and the soil.** It reads weather from NASA (a space agency that watches the Earth), tomorrow's forecast, and a little **soil sensor stuck in the ground** that says "I'm thirsty" or "I'm full".
3. **The app plays pretend.** It imagines the next growing season 30 different ways, using the real weather of the last 30 years: "What if this year was like 1998? Or 2011?" For each crop it asks: *how much would grow, and how often would it fail?*
4. **It shows Maya a simple table:** "Plant lentils on this date. You'd probably get about this much. There is a small chance of a bad year."
5. **It makes a calendar:** when to prepare the soil, when to sow, when to weed, when to harvest.
6. **It shouts when danger is near:** "Dry spell coming! Cover the soil with straw."
7. **It has an Elder friend** you can ask: "How do I feed my plants without chemicals?" The Elder answers with real traditional recipes (like jeevamrit) that grandparents used, and says where the knowledge came from.

**The soil is a bucket.** Rain fills it. Plants and sun drink from it. If it gets nearly empty, the plants are thirsty and grow less. The app keeps track of the bucket every day. That is the whole trick.

---

## 2. What problem are we solving?

| Problem | What we do |
|---|---|
| Farmers repeat one crop (monoculture) | Compare several crops, favour legumes and rotation |
| Weather is unpredictable | Replay 30 years of real weather to show best case, middle and worst case |
| AI advice pushes chemicals and ignores local knowledge | A verified traditional-knowledge library; the AI never invents advice |
| Farmers lack local, personal data | Map polygon + NASA + forecast + soil sensor on the farm |
| Too many questions confuse farmers | Only 4 taps. Everything else is detected automatically |

**Design principles**
1. **Free.** Only free tools (NASA POWER, Open-Meteo, OpenStreetMap, SQLite, open source libraries).
2. **Honest.** Show ranges and risk, not one fake-confident number. Mark placeholder data clearly.
3. **Explainable.** Every number can be traced to a formula (FAO-56 water balance).
4. **Respectful.** Traditional knowledge is credited, verified, and used with consent.
5. **Simple.** A farmer taps four buttons. That's it.
6. **Works on the farm.** Runs on one small computer (Arduino UNO Q) at the farm; survives internet loss using cached data.

---

## 3. Scope

**In scope (v1):** map polygon; weather + soil data; crop ranking; yield/profit ranges; risk; dated schedule; alerts; what-if; manual and device soil readings; search-based traditional-knowledge chat; run everything on Arduino UNO Q.

**Out of scope (do NOT build in v1):** LLM chatbot, SMS, user accounts/login, ESP32/MQTT, payments, Nepali/Hindi UI (v1.1), pest/disease model, satellite NDVI, crop-mix planner.

---

## 4. Architecture

```
 Farmer's phone/laptop (same Wi-Fi)
        │  opens http://<board-address>:8000
        ▼
 ┌────────────────── Arduino UNO Q ──────────────────┐
 │  Linux side (Debian, Python)                      │
 │   FastAPI ── serves the website + the API         │
 │     ├─ engine.py  (the science)                   │
 │     ├─ data.py    (NASA, forecast, cache)         │
 │     ├─ db.py      (SQLite: fields, readings)      │
 │     └─ kb.py      (Elder: search knowledge.json)  │
 │   device/python/main.py ◄── Bridge (RPC) ──┐      │
 │  MCU side (STM32U585, real-time)           │      │
 │   sketch.ino reads soil sensors ───────────┘      │
 └──────┬────────────────────────────────────────────┘
        │ Wi-Fi to the internet (cached when offline)
        ▼
 NASA POWER (30 years of daily weather)   Open-Meteo (16-day forecast)
```

**Flow of one request:** polygon + 4 taps + sensor reading → centre point and area → 30 years of weather → ET0 per day → for each crop and sowing date, replay every year through the soil bucket → yield fractions → money and risk → rank → schedule for the best crop → alerts from the forecast → JSON → screens.

**Hardware: Arduino UNO Q (4 GB RAM / 32 GB eMMC).** It joins a Qualcomm QRB2210 processor running Debian Linux (runs Python and FastAPI) with an STM32U585 microcontroller (reads sensors in real time). The two talk over an internal serial link using RPC messages. MCU pins are 3.3 V logic; **A0 and A1 are not 5 V tolerant**. **VERIFY** all wiring and the App Lab project layout against official Arduino documentation.

---

## 5. Technology (all free)

| Part | Tool |
|---|---|
| Backend | Python 3.10+, FastAPI, uvicorn, pydantic, requests |
| Database | SQLite (a single file) |
| Weather history | NASA POWER daily API (no key) |
| Forecast | Open-Meteo (no key; free for non-commercial use, check terms) |
| Map | Leaflet + Leaflet.draw + OpenStreetMap / Esri satellite tiles |
| Frontend | Plain HTML + CSS + JavaScript (no build step) |
| Tests | pytest |
| Hardware | Arduino UNO Q, capacitive soil-moisture sensor, DS18B20 soil temperature, analog pH probe (low trust, needs calibration) |

---

## 6. Folder tree (exact)

```
krishi-saathi/
├── BLUEPRINT.md            short source of truth
├── PROJECT.md              this file
├── README.md
├── .gitignore              venv/ __pycache__/ *.db .pytest_cache/ .env
├── backend/
│   ├── requirements.txt    fastapi uvicorn requests pydantic pytest httpx
│   ├── app/
│   │   ├── __init__.py     (empty)
│   │   ├── main.py         ✅ routes (+ static frontend, 🟡 fields/chat/whatif)
│   │   ├── engine.py       ✅ the science (🟡 whatif to add)
│   │   ├── data.py         ✅ NASA/forecast/offline data (🟡 disk cache to add)
│   │   ├── db.py           🟡 SQLite
│   │   ├── kb.py           🟡 Elder search
│   │   └── knowledge.json  🟡 traditional practices
│   └── tests/
│       ├── test_engine.py  ✅
│       └── api_smoke.py    ✅
├── frontend/               🟡
│   ├── index.html
│   ├── css/style.css
│   └── js/ config.js api.js map.js screens.js main.js
└── device/                 🔲 runs on the UNO Q (verify App Lab layout)
    ├── sketch/sketch.ino
    └── python/main.py
```
Note: the tested code below uses flat imports (`import engine as E`). When moved into `backend/app/`, change them to package imports: `from . import engine as E, data as D` (and in data.py `from .engine import et0_pm`), and run tests with `backend/` on the Python path.

---

## 7. Data sources (exact calls)

**NASA POWER daily point** (history, 30 years):
`GET https://power.larc.nasa.gov/api/temporal/daily/point` with params `parameters=T2M_MAX,T2M_MIN,PRECTOTCORR,RH2M,WS2M,ALLSKY_SFC_SW_DWN`, `community=AG`, `longitude`, `latitude`, `start=YYYYMMDD`, `end=YYYYMMDD`, `format=JSON`. Values of −999 mean missing (we carry the last good value forward). Radiation is in MJ/m²/day for community AG (**VERIFY**). Elevation is `geometry.coordinates[2]`. Grid is coarse (~50 km): local sensors matter.

**Open-Meteo forecast:**
`GET https://api.open-meteo.com/v1/forecast` with `latitude, longitude, forecast_days=16, timezone=auto, daily=temperature_2m_max,temperature_2m_min,precipitation_sum,et0_fao_evapotranspiration`.

**Offline mode:** set environment variable `KS_OFFLINE=1` to use synthetic hill-climate data (monsoon, dry winter). Used for tests only.

---

## 8. The science, explained simply (and exactly)

**8.1 ET0: how thirsty is the air?** Sun, wind, warmth and dryness pull water out of soil. ET0 (mm/day) is how much a short green lawn would lose. We use the FAO-56 Penman-Monteith equation from daily max/min temperature, humidity, wind at 2 m, solar radiation, latitude, elevation and day of year.

**8.2 Kc: how thirsty is this plant?** A seedling drinks little, a leafy crop drinks a lot, a ripening crop drinks little again. `ETc = Kc × ET0`. Each crop has Kc values for initial / mid / end stage and stage lengths (initial, development, mid, late days). Kc rises linearly during development, stays flat in mid season, then falls linearly in the late stage.

**8.3 The bucket (soil water balance).**
- Total available water `TAW = 1000 × (field capacity − wilting point) × root depth (mm)`.
- Easily available water `RAW = p × TAW` (p = how much the crop can drain before it struggles).
- `Dr` = depletion = how empty the bucket is (0 = full).
- Each day: `Ks = 1` if `Dr ≤ RAW`, else `Ks = (TAW − Dr) / (TAW − RAW)`. Actual use `ETa = Ks × ETc`.
- Update: `Dr = Dr − 0.85×rain − irrigation + ETa`, kept between 0 and TAW (below 0 = water drains away).
- Irrigation happens when `Dr > 0.9×RAW`, up to the daily amount the farmer's water allows: `litres_per_day × efficiency / (field area m²)` mm.
- Start level: from the soil-moisture sensor if available, otherwise 30% depleted.

**8.4 Yield (FAO-33).** `1 − Ya/Ym = Ky × (1 − ETa/ETc)`. Example: lentil, ETc 250 mm, ETa 160 mm, Ky 0.8 → loss 0.8 × 0.36 = 28.8 % → yield 71.2 %. A temperature factor reduces yield if mean temperature leaves the crop's range, and each frost day (< −2 °C) or heat day (> 38 °C) costs 1.5 %.

**8.5 History replay (the "30 pretend seasons").** For one sowing date, start the crop on that calendar day in every historical year and simulate. That gives ~30 yield fractions → P10 (bad year), P50 (typical), P90 (good year) and **risk = share of years with yield fraction < 0.6**.

**8.6 Money.** `kg = potential yield × hectares × yield fraction × seed multiplier × labour factor`. Labour factor = `min(1, workers × days × 0.5 / (labour days per ha × ha × tool factor)) ^ 0.7`. `net = kg × price − cost`.

**8.7 Ranking and best sowing date.** For each crop, try a sowing date every 14 days for a year, but only in the crop's allowed sowing months (agronomy and tradition: not derivable from water balance). Score = `P50 net − 0.5 × (P50 net − P10 net) − risk × 0.2 × cost`. Keep each crop's best date, sort by score.

**8.8 Schedule.** A crop-calendar template shifted to the sow date (prepare −21, −7, seed treatment −1, sow 0, weed +25, feed +30, scout +45, flowering at 55 % of cycle, harvest at cycle length, save seed +7 after) plus **water tasks** taken from the median historical year (first day of each week with water stress or irrigation). A warning appears if soil temperature is below the crop's minimum and sowing is within 7 days.

**8.9 Alerts.** Run the bucket forward over the forecast with a generic crop (Kc = 1, root 0.6 m, loam). Rules: drought if stress arrives within 10 days and forecast rain < 15 mm; low soil moisture < 25 %; frost (forecast min ≤ 2 °C); heat (max ≥ 37 °C); heavy rain (≥ 60 mm/day); acidic soil (pH < 5.2).

**8.10 Where AI fits.** Machine learning is NOT used yet, because there is no real harvest data to train on. Later, once real harvest results are collected from farmers, a model can learn to correct the simulator's errors. An LLM may later explain results in local languages or answer from the knowledge base, but must never create numbers or dates.

---

## 9. Backend code (✅ tested: 6 tests pass)

### 9.1 `backend/app/engine.py`

```python
"""Krishi Saathi engine: FAO-56 ET0 + daily soil-water bucket + history replay.
Deterministic and explainable. The LLM never produces numbers or dates."""
import math, statistics
from datetime import date, timedelta

# sow=allowed sowing months (agronomy/tradition, not derivable from water balance)
# kc=(ini,mid,end), st=(ini,dev,mid,late days), ky=FAO yield response, root=m, p=depletion fraction,
# t=optimal mean temp C, ym=unstressed yield kg/ha, labour=person-days/ha. Values are starting points: have agronomists verify.
CROPS = {
 "finger_millet": dict(sow=(5,6,7), name="Finger millet (Kodo)", kc=(.3,1.0,.3), st=(20,30,40,20), ky=.85, root=.9, p=.55, t=(15,30), ym=1500, price=70, cost=22000, labour=180, legume=False, soil_t=14),
 "buckwheat":     dict(sow=(3,4,8,9), name="Buckwheat (Fapar)", kc=(.35,1.0,.35), st=(15,20,30,15), ky=.8, root=.6, p=.5, t=(12,26), ym=1000, price=90, cost=17500, labour=120, legume=False, soil_t=10),
 "maize_beans":   dict(sow=(3,4,5), name="Maize + beans + pumpkin", kc=(.3,1.15,.5), st=(20,30,40,20), ky=1.25, root=1.0, p=.55, t=(18,32), ym=2500, price=45, cost=39000, labour=220, legume=True, soil_t=14),
 "lentil":        dict(sow=(10,11), name="Lentil (Masuro)", kc=(.4,1.1,.3), st=(20,30,40,30), ky=.85, root=.6, p=.5, t=(8,22), ym=900, price=160, cost=26000, labour=140, legume=True, soil_t=8),
 "mustard":       dict(sow=(10,11), name="Mustard", kc=(.35,1.1,.35), st=(20,25,35,20), ky=.9, root=.8, p=.6, t=(8,24), ym=800, price=110, cost=19500, labour=130, legume=False, soil_t=8),
 "wheat_barley":  dict(sow=(10,11,12), name="Hill wheat / barley", kc=(.3,1.15,.25), st=(25,35,40,30), ky=1.0, root=1.0, p=.55, t=(8,22), ym=2200, price=45, cost=37000, labour=160, legume=False, soil_t=8),
 "potato":        dict(sow=(1,2,9), name="Potato", kc=(.5,1.15,.75), st=(25,30,30,15), ky=1.1, root=.5, p=.35, t=(10,20), ym=12000, price=35, cost=160000, labour=300, legume=False, soil_t=8),
 "turmeric":      dict(sow=(4,5), name="Turmeric / Ginger", kc=(.5,1.1,.7), st=(40,60,90,50), ky=.9, root=.5, p=.4, t=(20,32), ym=3000, price=120, cost=120000, labour=320, legume=False, soil_t=18),
}
SOILS = {"sandy": (.18,.08), "loam": (.31,.15), "clay": (.38,.22)}  # (field capacity, wilting point) m3/m3
SEED = {"own": (.9,-.1), "opv": (1.0,0), "hyb": (1.2,.35)}       # (yield mult, cost adj)
TOOLS = {"hand": 1.0, "bullock": .8, "tiller": .65, "tractor": .5}
days_of = lambda c: sum(c["st"])

def _ra(lat, doy):
    ph = math.radians(lat); dr = 1+.033*math.cos(2*math.pi*doy/365); d = .409*math.sin(2*math.pi*doy/365-1.39)
    ws = math.acos(max(-1, min(1, -math.tan(ph)*math.tan(d))))
    return 24*60/math.pi*.082*dr*(ws*math.sin(ph)*math.sin(d)+math.cos(ph)*math.cos(d)*math.sin(ws))

def et0_pm(tmax, tmin, rh, u2, rs, lat, z, doy):
    """FAO-56 Penman-Monteith reference ET (mm/day). rs in MJ/m2/day, u2 m/s at 2 m."""
    t = (tmax+tmin)/2; e0 = lambda x: .6108*math.exp(17.27*x/(x+237.3))
    es = (e0(tmax)+e0(tmin))/2; ea = max(.05, rh/100*es)
    delta = 4098*e0(t)/(t+237.3)**2; P = 101.3*((293-.0065*z)/293)**5.26; g = .000665*P
    rso = max(1, (.75+2e-5*z)*_ra(lat, doy))
    rnl = 4.903e-9*(((tmax+273.16)**4+(tmin+273.16)**4)/2)*(.34-.14*math.sqrt(ea))*(1.35*min(rs/rso,1)-.35)
    rn = (1-.23)*rs-rnl
    return max(0, (.408*delta*rn+g*900/(t+273)*u2*(es-ea))/(delta+g*(1+.34*u2)))

def kc_at(c, d):
    i, dv, m, l = c["st"]; a, b, e = c["kc"]
    if d < i: return a
    if d < i+dv: return a+(b-a)*(d-i)/dv
    if d < i+dv+m: return b
    return b+(e-b)*min(1, (d-i-dv-m)/l)

def yield_fraction(ky, eta, etc):
    """FAO-33: 1 - Ya/Ym = Ky * (1 - ETa/ETc)"""
    return max(0.0, min(1.0, 1-ky*(1-eta/etc))) if etc > 0 else 0.0

def simulate(W, i0, c, soil="loam", moist=None, irr_mm=0.0, log=False):
    """Daily soil-water bucket from index i0 of weather W for one crop cycle."""
    fc, wp = SOILS[soil]; n = days_of(c); taw = 1000*(fc-wp)*c["root"]; raw = c["p"]*taw
    dr = min(taw, max(0, (fc-moist/100)*c["root"]*1000)) if moist is not None else .3*taw
    etc_t = eta_t = irr_t = 0.0; stress = heat = frost = 0; ts = 0.0; rows = []
    for d in range(n):
        j = i0+d
        etc = kc_at(c, d)*W["et0"][j]; ks = 1.0 if dr <= raw else max(0.0, (taw-dr)/(taw-raw))
        eta = ks*etc; irr = 0.0
        if irr_mm and dr > raw*.9: irr = min(irr_mm, dr)
        dr = min(taw, max(0.0, dr-.85*W["p"][j]-irr+eta))
        etc_t += etc; eta_t += eta; irr_t += irr; stress += ks < 1; ts += W["tmean"][j]
        heat += W["tmax"][j] > 38; frost += W["tmin"][j] < -2
        if log: rows.append(dict(day=d, date=W["date"][j], dr=round(dr,1), raw=round(raw,1), ks=round(ks,2), irr=round(irr,1), rain=W["p"][j]))
    tm = ts/n; lo, hi = c["t"]; tf = 1 if lo <= tm <= hi else 1-(lo-tm if tm < lo else tm-hi)/12
    yf = yield_fraction(c["ky"], eta_t, etc_t)*max(.2, tf-.015*(heat+frost))
    out = dict(yf=max(0, min(1, yf)), etc=etc_t, eta=eta_t, deficit=etc_t-eta_t, irrigation=irr_t, stress_days=stress, tmean=tm)
    if log: out["log"] = rows
    return out

def replay(W, c, month, day, soil, moist, irr_mm, years=None):
    """Replay every historical year's actual weather on this field for one sowing date."""
    res = []; n = days_of(c)
    for y in sorted({d.year for d in W["date"]}):
        try: s = date(y, month, day)
        except ValueError: continue
        i = W["idx"].get(s)
        if i is not None and i+n <= len(W["date"]): r = simulate(W, i, c, soil, moist, irr_mm); r["year"] = y; res.append(r)
    return res

def economics(c, yf, I):
    ha = I["ha"]; sm, sc = SEED[I["seed"]]
    lf = min(1, I["workers"]*days_of(c)*.5/(c["labour"]*ha*TOOLS[I["tools"]]))**.7
    kg = c["ym"]*ha*yf*sm*lf; cost = c["cost"]*ha*(1+sc)
    return kg, kg*c["price"]-cost, cost

def _q(v, q): v = sorted(v); return v[int(q*(len(v)-1))]

def evaluate(W, key, month, day, I):
    c = CROPS[key]; irr = I["water_l_day"]*I["eff"]/(I["ha"]*1e4) if I["water_l_day"] else 0
    runs = replay(W, c, month, day, I["soil"], I.get("moist"), irr)
    if len(runs) < 8: return None
    nets = [economics(c, r["yf"], I)[1] for r in runs]; kgs = [economics(c, r["yf"], I)[0] for r in runs]
    cost = economics(c, 1, I)[2]
    return dict(key=key, name=c["name"], sow=(month, day), n_years=len(runs), yield_kg=dict(p10=_q(kgs,.1), p50=_q(kgs,.5), p90=_q(kgs,.9)),
        net=dict(p10=_q(nets,.1), p50=_q(nets,.5), p90=_q(nets,.9)), cost=cost, risk=sum(r["yf"] < .6 for r in runs)/len(runs),
        deficit_mm=statistics.median(r["deficit"] for r in runs), water_need_mm=statistics.median(r["etc"] for r in runs),
        irrigation_mm=statistics.median(r["irrigation"] for r in runs), days=days_of(c), legume=c["legume"],
        held_back="Water" if statistics.median(r["deficit"] for r in runs) > .15*statistics.median(r["etc"] for r in runs) else "Climate/Labour", _runs=runs)

def rank(W, I, today=None):
    """Try a sowing date every 14 days for the next year, keep each crop's best (profit minus downside)."""
    today = today or date.today(); out = []
    for key in CROPS:
        best = None
        for k in range(26):
            d = today+timedelta(days=14*k)
            if d.month not in CROPS[key]["sow"]: continue
            e = evaluate(W, key, d.month, d.day, I)
            if not e: continue
            e["score"] = e["net"]["p50"]-.5*(e["net"]["p50"]-e["net"]["p10"])-e["risk"]*.2*e["cost"]
            e["sow_date"] = d
            if not best or e["score"] > best["score"]: best = e
        if best: out.append(best)
    return sorted(out, key=lambda e: -e["score"])

def schedule(W, key, sow, I, soil_t=None):
    """Dated tasks from a crop calendar, plus water tasks taken from the median historical year."""
    c = CROPS[key]; D = lambda n: sow+timedelta(days=n); n = days_of(c)
    irr = I["water_l_day"]*I["eff"]/(I["ha"]*1e4) if I["water_l_day"] else 0
    runs = replay(W, c, sow.month, sow.day, I["soil"], I.get("moist"), irr); tasks = []
    T = [("Clear field, add compost, light ploughing", -21, "prepare"), ("Prepare beds and drainage, gather mulch", -7, "prepare"), ("Beejamrit seed treatment", -1, "prepare"),
         ("SOW "+c["name"], 0, "sow"), ("First weeding and mulch", 25, "care"), ("Jeevamrit top-dressing", 30, "care"), ("Pest scouting (neem spray if needed)", 45, "care"),
         ("Flowering stage: keep soil moisture steady", round(n*.55), "care"), ("HARVEST", n, "harvest"), ("Save seed, compost residue, plan rotation", n+7, "harvest")]
    tasks += [dict(date=D(o).isoformat(), task=t, type=ty, reason="crop calendar") for t, o, ty in T]
    if runs:
        med = sorted(runs, key=lambda r: r["yf"])[len(runs)//2]; i0 = W["idx"][date(med["year"], sow.month, sow.day)]
        lg = simulate(W, i0, c, I["soil"], I.get("moist"), irr, log=True)["log"]; last = -9
        for r in lg:
            if (r["ks"] < 1 or r["irr"] > 0) and r["day"]-last >= 7:
                last = r["day"]; tasks.append(dict(date=D(r["day"]).isoformat(), type="water", task="Irrigate or mulch: soil water running low" if r["irr"] else "Dry spell likely: mulch, irrigate if you can", reason="water-balance model (typical year)"))
    warn = [f"Soil is {soil_t}°C; {c['name']} wants at least {c['soil_t']}°C. Delay sowing." ] if soil_t is not None and soil_t < c["soil_t"] and (sow-date.today()).days < 7 else []
    return dict(crop=key, sow_date=sow.isoformat(), tasks=sorted(tasks, key=lambda t: t["date"]), warnings=warn)

def alerts(fc, sensors):
    """fc: dict of lists tmax,tmin,rain,et0 for next days. sensors: moisture, soil_t, ph."""
    A = []; fcap, wp = SOILS["loam"]; taw = 1000*(fcap-wp)*.6; raw = .5*taw
    m = sensors.get("moisture"); dr = min(taw, max(0, (fcap-m/100)*600)) if m is not None else .3*taw; stress_in = None
    for i, (r, e) in enumerate(zip(fc["rain"], fc["et0"])):
        dr = min(taw, max(0, dr-.85*r+e))
        if dr > raw and stress_in is None: stress_in = i+1
    rain = sum(fc["rain"])
    if stress_in and stress_in <= 10 and rain < 15: A.append(dict(level="high", type="drought", msg=f"Drought risk: soil water model hits crop stress in about {stress_in} days with only {rain:.0f} mm rain forecast. Mulch now and irrigate early morning."))
    if m is not None and m < 25: A.append(dict(level="high", type="sensor", msg=f"Soil moisture is only {m}%. Irrigate or mulch."))
    if min(fc["tmin"]) <= 2: A.append(dict(level="high", type="frost", msg="Frost risk. Cover seedlings with straw overnight."))
    if max(fc["tmax"]) >= 37: A.append(dict(level="high", type="heat", msg="Heat wave expected. Shade and irrigate at dawn."))
    if max(fc["rain"]) >= 60: A.append(dict(level="high", type="flood", msg="Very heavy rain forecast. Open drainage, delay sowing and spraying."))
    ph = sensors.get("ph")
    if ph is not None and ph < 5.2: A.append(dict(level="medium", type="soil", msg=f"Soil acidic (pH {ph}). Add wood ash or lime plus compost."))
    return A
```

### 9.2 `backend/app/data.py`

```python
"""Data sources: NASA POWER (history), Open-Meteo (forecast). Set KS_OFFLINE=1 for synthetic test data."""
import os, math, random, requests
from datetime import date, timedelta
from functools import lru_cache
from engine import et0_pm

POWER = "https://power.larc.nasa.gov/api/temporal/daily/point"

def _pack(dates, tmax, tmin, p, rh, ws, rs, lat, z):
    W = dict(date=dates, p=p, tmax=tmax, tmin=tmin, tmean=[(a+b)/2 for a, b in zip(tmax, tmin)], et0=[])
    for i, d in enumerate(dates): W["et0"].append(et0_pm(tmax[i], tmin[i], rh[i], ws[i], rs[i], lat, z, d.timetuple().tm_yday))
    W["idx"] = {d: i for i, d in enumerate(dates)}; W["lat"], W["z"] = lat, z
    return W

def _clean(v):
    out, last = [], 0.0
    for x in v: last = last if x <= -900 else x; out.append(last)
    return out

@lru_cache(maxsize=32)
def get_history(lat, lon, years=30):
    if os.getenv("KS_OFFLINE"): return synthetic_history(lat, lon, years)
    end = date.today()-timedelta(days=5); start = date(end.year-years, 1, 1)
    r = requests.get(POWER, params=dict(parameters="T2M_MAX,T2M_MIN,PRECTOTCORR,RH2M,WS2M,ALLSKY_SFC_SW_DWN", community="AG", longitude=lon, latitude=lat,
        start=start.strftime("%Y%m%d"), end=end.strftime("%Y%m%d"), format="JSON"), timeout=180); r.raise_for_status()
    j = r.json(); p = j["properties"]["parameter"]; z = j["geometry"]["coordinates"][2]; keys = sorted(p["T2M_MAX"])
    dates = [date(int(k[:4]), int(k[4:6]), int(k[6:])) for k in keys]; g = lambda n: _clean([p[n][k] for k in keys])
    return _pack(dates, g("T2M_MAX"), g("T2M_MIN"), [max(0, x) for x in g("PRECTOTCORR")], g("RH2M"), g("WS2M"), g("ALLSKY_SFC_SW_DWN"), lat, z)

def get_forecast(lat, lon, days=16):
    if os.getenv("KS_OFFLINE"): return dict(tmax=[20]*days, tmin=[6]*days, rain=[0]*days, et0=[2.5]*days)
    j = requests.get("https://api.open-meteo.com/v1/forecast", params=dict(latitude=lat, longitude=lon, forecast_days=days, timezone="auto",
        daily="temperature_2m_max,temperature_2m_min,precipitation_sum,et0_fao_evapotranspiration"), timeout=30).json()["daily"]
    return dict(tmax=j["temperature_2m_max"], tmin=j["temperature_2m_min"], rain=j["precipitation_sum"], et0=j["et0_fao_evapotranspiration"])

def synthetic_history(lat, lon, years=30, seed=1):
    """Hill-climate stand-in (monsoon, dry winter) used only for offline tests."""
    r = random.Random(seed); T = [6,8,12,15,18,20,20,20,19,16,11,8]; P = [.5,.8,1.3,2.2,4.5,8,12,11,7,2.5,.4,.3]
    d0 = date(date.today().year-years, 1, 1); dates, tx, tn, p, rh, ws, rs = [], [], [], [], [], [], []
    for k in range((date.today()-timedelta(days=5)-d0).days):
        d = d0+timedelta(days=k); m = d.month-1; yr = 1+.25*math.sin(d.year*1.7)
        wet = r.random() < min(.9, P[m]*yr/9); rain = r.expovariate(1/10) if wet else 0
        mean = T[m]+r.gauss(0, 1.2); dates.append(d); tx.append(mean+5); tn.append(mean-5); p.append(rain)
        rh.append(85 if wet else 55+(25 if 5 <= m <= 8 else 0)); ws.append(1.5); rs.append((14 if wet else 19)+(0 if 4 <= m <= 8 else -2))
    return _pack(dates, tx, tn, p, rh, ws, rs, lat, 1900)
```

### 9.3 `backend/app/main.py` (current version)

```python
"""FastAPI service. Run: uvicorn main:app --reload"""
from datetime import date
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import engine as E, data as D

app = FastAPI(title="Krishi Saathi engine"); app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
SENSORS = {}   # field_id -> latest reading. Replace with PostGIS/Timescale + MQTT ingest.

class Profile(BaseModel):
    water_l_day: float = 0; irrigation_eff: float = .6; soil: str = "loam"; seed: str = "opv"; workers: int = 3; tools: str = "bullock"
class Sensors(BaseModel):
    moisture: Optional[float] = None; soil_t: Optional[float] = None; ph: Optional[float] = None
class Req(BaseModel):
    polygon: List[List[float]]; profile: Profile = Profile(); sensors: Sensors = Sensors(); field_id: Optional[str] = None; crop: Optional[str] = None

def geo(poly):
    import math
    lat = sum(p[0] for p in poly)/len(poly); lon = sum(p[1] for p in poly)/len(poly); k = 111320; cl = math.cos(math.radians(lat)); a = 0
    for i, p in enumerate(poly): q = poly[(i+1) % len(poly)]; a += p[1]*cl*k*q[0]*k-q[1]*cl*k*p[0]*k
    return lat, lon, max(.01, abs(a/2)/1e4)

def inputs(r, ha):
    s = r.sensors.dict(); s.update(SENSORS.get(r.field_id, {})) if r.field_id else None
    if r.profile.soil not in E.SOILS or r.profile.seed not in E.SEED or r.profile.tools not in E.TOOLS: raise HTTPException(400, "bad profile value")
    return dict(ha=ha, soil=r.profile.soil, seed=r.profile.seed, workers=r.profile.workers, tools=r.profile.tools, water_l_day=r.profile.water_l_day, eff=r.profile.irrigation_eff, moist=s.get("moisture")), s

@app.post("/api/sensors/{field_id}")
def ingest(field_id: str, s: Sensors): SENSORS[field_id] = {k: v for k, v in s.dict().items() if v is not None}; return {"ok": True}

@app.post("/api/analyze")
def analyze(r: Req):
    lat, lon, ha = geo(r.polygon); I, s = inputs(r, ha); W = D.get_history(round(lat, 2), round(lon, 2)); fc = D.get_forecast(lat, lon)
    ranked = E.rank(W, I)
    if not ranked: raise HTTPException(422, "not enough weather history")
    top = ranked[0]; crops = [{k: v for k, v in c.items() if k != "_runs"} | {"sow_date": c["sow_date"].isoformat()} for c in ranked[:5]]
    return dict(field=dict(lat=lat, lon=lon, ha=round(ha, 2), elevation_m=W["z"]), forecast=fc, alerts=E.alerts(fc, s), crops=crops,
                schedule=E.schedule(W, top["key"], top["sow_date"], I, s.get("soil_t")), method="FAO-56 Penman-Monteith + daily soil-water balance replayed over %d past seasons" % top["n_years"])

@app.post("/api/schedule")
def sched(r: Req):
    if r.crop not in E.CROPS: raise HTTPException(400, "unknown crop")
    lat, lon, ha = geo(r.polygon); I, s = inputs(r, ha); W = D.get_history(round(lat, 2), round(lon, 2))
    top = [c for c in E.rank(W, I) if c["key"] == r.crop]
    if not top: raise HTTPException(422, "not enough weather history")
    return E.schedule(W, r.crop, top[0]["sow_date"], I, s.get("soil_t"))
```

### 9.4 `backend/tests/test_engine.py`

```python
import os, sys, time; os.environ["KS_OFFLINE"]="1"; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
import engine as E, data as D
I = dict(ha=.5, soil="loam", seed="opv", workers=3, tools="bullock", water_l_day=0, eff=.6, moist=None)
def test_et0():
    v = E.et0_pm(22, 8, 60, 1.5, 16, 27.7, 1900, 320); assert 1.5 < v < 4, v
def test_fao33_example():
    assert abs(E.yield_fraction(.8, 160, 250)-.712) < 1e-6   # worked example from the docs
def test_irrigation_helps():
    W = D.get_history(27.7, 85.5); c = E.CROPS["lentil"]
    a = E.evaluate(W, "lentil", 10, 20, I); b = E.evaluate(W, "lentil", 10, 20, I | dict(water_l_day=4000))
    assert b["yield_kg"]["p50"] >= a["yield_kg"]["p50"] and b["risk"] <= a["risk"]
def test_wet_season_beats_dry_for_rice_like():
    W = D.get_history(27.7, 85.5); dry = E.evaluate(W, "maize_beans", 12, 1, I); wet = E.evaluate(W, "maize_beans", 5, 1, I)
    assert wet["yield_kg"]["p50"] > dry["yield_kg"]["p50"]
def test_rank_and_schedule():
    W = D.get_history(27.7, 85.5); t = time.time(); r = E.rank(W, I); print("rank secs", round(time.time()-t, 2))
    assert len(r) >= 5 and r[0]["score"] >= r[-1]["score"]
    s = E.schedule(W, r[0]["key"], r[0]["sow_date"], I); assert any(t["type"] == "sow" for t in s["tasks"])
    for c in r[:5]: print(c["name"], c["sow_date"], {k: round(v) for k, v in c["yield_kg"].items()}, "net", round(c["net"]["p50"]), "risk", round(c["risk"], 2), c["held_back"])
def test_alerts():
    a = E.alerts(dict(tmax=[20]*10, tmin=[6]*10, rain=[0]*10, et0=[4]*10), dict(moisture=20, ph=4.8)); assert any(x["type"] == "drought" for x in a) and len(a) >= 3
```

Run tests: `KS_OFFLINE=1 python -m pytest tests -s` → expect `6 passed`.

---

## 10. SPEC — database (`db.py`) 🟡

SQLite file `krishi.db` next to the app. Tables:

```sql
CREATE TABLE fields(id INTEGER PRIMARY KEY, name TEXT, polygon_json TEXT, lat REAL, lon REAL, ha REAL, profile_json TEXT, created_at TEXT);
CREATE TABLE readings(id INTEGER PRIMARY KEY, field_id INTEGER, ts TEXT, moisture REAL, soil_t REAL, ph REAL, source TEXT CHECK(source IN ('manual','device')));
```
Functions: `init()`, `save_field(name, polygon, profile) -> id`, `get_field(id)`, `add_reading(field_id, moisture, soil_t, ph, source)`, `latest_reading(field_id)`. Use parameterised queries only. **Acceptance:** save a field, add a reading, read both back; latest returns the newest by timestamp. Replace the in-memory `SENSORS` dict in main.py with this.

## 11. SPEC — Elder chatbot (`kb.py`, `knowledge.json`) 🟡

**No LLM.** `knowledge.json` is a list of entries: `{id, title, keywords[], text, source, contributor, consent: true, verified_by, language}`. `search(question)` lowercases, removes punctuation, scores each entry by keyword matches (title words count double), returns the best entry if score ≥ 1, else `matched=false` with the message: *"I do not have that yet. Ask your local elders or extension office."* Response: `{answer, title, source, matched}`. Always show the source and who verified it. **Acceptance:** "natural fertilizer" → jeevamrit entry; "aphids" → neem entry; gibberish → matched=false.

Starter entries (**VERIFY each with a local expert and credit contributors**):
- *Jeevamrit (Jholmal in Nepal):* 10 kg cow dung + 10 L cow urine + 2 kg jaggery + 2 kg pulse flour + a handful of soil in 200 L water; ferment 5–7 days, stir daily; apply weekly.
- *Beejamrit seed treatment:* 5 kg cow dung + 5 L cow urine + 50 g lime + a handful of soil in 20 L water; soak, coat seeds, shade-dry.
- *Neem spray:* 5 kg crushed neem leaves in 20 L water overnight, strain, add a little soap, spray in the evening.
- *Buttermilk spray* for fungus: 1 L sour buttermilk in 10 L water.
- *Mulching and drought:* 5–10 cm straw or leaves, half-moon trenches, irrigate at dawn.
- *Rotation and intercropping:* cereal → legume → vegetable → green manure; maize + beans + pumpkin.
- *Acidic soil:* wood ash or lime plus compost.

## 12. SPEC — what-if (`engine.whatif`) 🟡

`whatif(W, crop_key, sow_date, I)` returns a list for scenarios: current, +mulch (crop water need × 0.8), +compost (yield × 1.12), +drip (efficiency 0.9; if no water set 1500 L/day), +hybrid seed (with compost), +power tiller (tool factor 0.65), +2 workers. Each item: `{name, yield_kg_p50, net_p50, delta_yield_pct, delta_net}`. Implement mulch/compost as options in `simulate`/`economics`. **Acceptance:** drip and compost never lower median yield; response has 7 items.

## 13. API contract

| Method | Path | Body → Response |
|---|---|---|
| GET | `/api/health` | → `{ok:true}` |
| POST | `/api/analyze` | request below → field, forecast, alerts, crops (top 5), schedule, method |
| POST | `/api/schedule` | request + `crop` → `{crop, sow_date, tasks[], warnings[]}` |
| POST | `/api/whatif` 🟡 | request + `crop` → scenarios list |
| POST | `/api/fields` 🟡 / GET `/api/fields/{id}` 🟡 | save/load field |
| POST | `/api/sensors/{field_id}` | `{moisture, soil_t, ph, source}` → `{ok:true}` |
| GET | `/api/sensors/{field_id}/latest` 🟡 | latest reading |
| POST | `/api/chat` 🟡 | `{question}` → `{answer,title,source,matched}` |

**Request:**
```json
{"polygon":[[27.693,85.52],[27.694,85.522],[27.6925,85.523],[27.692,85.5205]],
 "profile":{"water_l_day":3000,"irrigation_eff":0.6,"soil":"loam","seed":"opv","workers":3,"tools":"bullock"},
 "sensors":{"moisture":22,"soil_t":13,"ph":5.0}}
```
Allowed values: soil `sandy|loam|clay`; seed `own|opv|hyb`; tools `hand|bullock|tiller|tractor`. Anything else → HTTP 400.

**Response (shape):** `field{lat,lon,ha,elevation_m}`, `forecast{tmax[],tmin[],rain[],et0[]}`, `alerts[{level,type,msg}]`, `crops[{key,name,sow,sow_date,n_years,yield_kg{p10,p50,p90},net{p10,p50,p90},cost,risk,deficit_mm,water_need_mm,irrigation_mm,days,legume,held_back,score}]`, `schedule{crop,sow_date,tasks[{date,task,type,reason}],warnings[]}`, `method`.

## 14. Build steps (each has a check)

| # | Do | Check |
|---|---|---|
| 1 | Folders, venv, requirements, git | `python --version` ≥ 3.10; fastapi installed |
| 2 | Put engine.py and data.py in `backend/app/`, fix imports, add tests | `pytest` → 6 passed |
| 3 | main.py; run `uvicorn app.main:app --reload` | `/docs` opens; `/api/analyze` works offline |
| 4 | Run without `KS_OFFLINE` | analyze returns real NASA-based result; first call may take a while |
| 5 | db.py + fields + sensors | save field, post reading, read back |
| 6 | kb.py + knowledge.json + chat | acceptance in Part 11 |
| 7 | whatif | acceptance in Part 12 |
| 8 | Frontend: map + Farm screen | draw polygon → weather strip + alerts show |
| 9 | Frontend: Compare, Plan, Elder | full flow works in browser |
| 10 | Run everything on the UNO Q | phone on same Wi-Fi opens the app |
| 11 | Sensors: wire, sketch, Bridge reader | readings appear in latest endpoint |
| 12 | Reliability: disk cache of NASA/forecast, auto-start on boot, DB backup | unplug internet, app still works with cached data |
| 13 | Optional: free tunnel for remote access | works away from the farm |

---

## 15. SPEC — frontend 🟡

Static files; no framework; Leaflet and Leaflet.draw from cdnjs. `config.js` holds `API_URL` (empty string = same origin). `api.js` is the only file that calls `fetch`. Four screens, a top weather bar visible on all.

1. **Farm screen:** satellite/street map with polygon+rectangle drawing; after drawing show area in hectares; **weather bar** (current, 7 forecast days with max/min and rain, NASA 30-day rain vs normal); **alerts card** (red = high); **soil sensor card** showing the latest reading, with a manual entry (dry/damp/wet buttons → 15 / 40 / 70 % moisture, plus optional numbers).
2. **Compare screen:** "Auto-detected" chips (area, soil moisture, soil temp, pH, rain outlook); **four tap groups** (water access: rain only / well or pond / canal; tools: hand / bullock / power tiller; seed: saved / improved / hybrid; workers: 1–2 / 3–4 / 5+ ); a plain-language verdict ("Plant X first… Safest is Y…"); a **table**: columns = top 5 crops, rows = sow date, likely yield, income, cost, net profit, bad-season risk, water needed, days to harvest, held back by, soil benefit, verdict; best value per row highlighted; tapping a crop name opens the **what-if** list (bars + % and money change).
3. **Plan screen:** a **monthly calendar**. Colour dots: brown = prepare land, green = sow, blue = care/feed/water, orange = harvest. Tap a day to list tasks with tick boxes; progress bar for crop status; "coming up" line; month arrows.
4. **Elder screen:** chat box; answer card with title, text, source, and who verified it.

Style: earthy greens, large buttons (touch friendly), works in light and dark mode, works on a phone. Show a visible note: "Prices, yields and costs are estimates." Language toggle (English/Nepali/Hindi) is v1.1.

## 16. SPEC — device on the UNO Q 🔲 (**VERIFY** against Arduino App Lab docs)

- **Sensors:** capacitive soil-moisture (analog; calibrate dry-air and water-in-cup values), DS18B20 (one-wire, soil temperature), analog pH probe (drifts; show as low-trust). Power sensors at 3.3 V; keep A0/A1 within 3.3 V.
- **Sketch (MCU):** read each sensor every N seconds, smooth with a short average, and expose a Bridge function (e.g. `readSensors`) returning moisture %, temperature °C and pH.
- **Python (Linux):** every 10 minutes call the Bridge function, then write the reading to SQLite via `db.add_reading(..., source='device')` (or POST to `/api/sensors/{id}`). Run the FastAPI service as a boot-time service (systemd).
- **Calibration:** moisture % = (dry_raw − raw) / (dry_raw − wet_raw) × 100, clamped 0–100.
- **Safety:** never connect a 5 V signal to A0/A1; use a fuse or current limit when powering from VIN (7–24 V).

## 17. Honest limits

- Kc, Ky, root depth, sowing windows, prices and costs in `CROPS` are **starter values**: a local agronomist must verify them before farmers rely on them.
- NASA's grid is ~50 km wide; hill terrain can differ a lot: the farm's own sensor is vital.
- No pest, disease or nutrient model; hail, flood and market-price swings are not captured.
- The first analysis may be slow on the board; cache results.
- Traditional knowledge must be collected with consent, credited, and verified: never copied from the internet without permission.
- One device = one point of failure: back up `krishi.db`.
- Open-Meteo's free tier is for non-commercial use; recheck terms if the project ever earns money.

## 18. Glossary for a five-year-old (and everyone else)

| Word | Meaning |
|---|---|
| Polygon | A shape you draw around your field |
| NASA POWER | A free website with weather from every day for decades |
| ET0 / ETc | How much water the sun and wind want to take (from soil/plants) each day |
| Kc | A number for how thirsty a plant is at its age |
| Bucket | The soil's water store |
| Deficit | How much water the plant needed but did not get |
| Replay | Pretending this year is like each past year |
| P10 / P50 / P90 | Bad year / normal year / good year |
| Risk | How often the replay gave a bad harvest |
| Sensor | A tiny helper in the soil that tells us how wet it is |
| Legume | Plants like lentils and beans that feed the soil |
| Jeevamrit | A traditional liquid plant food made from cow dung, urine, jaggery and pulse flour |
| MCU / MPU | The tiny "reflex brain" (sensors) and the "thinking brain" (Linux) on the UNO Q |

## 19. Checklist for an AI rebuilding this project

- [ ] Created the exact folder tree (Part 6)
- [ ] Copied engine.py, data.py, main.py, test_engine.py exactly (Part 9) and fixed imports
- [ ] `pytest` shows 6 passed in offline mode
- [ ] `/api/analyze` returns the documented JSON shape
- [ ] Implemented db.py, kb.py, knowledge.json, whatif exactly per Parts 10–12 with their acceptance checks
- [ ] Built the four screens per Part 15, using only the API in Part 13
- [ ] Added disk caching for NASA/forecast data
- [ ] Wrote device code per Part 16 and flagged every VERIFY item to the human
- [ ] Added no feature from the "out of scope" list
- [ ] Told the human which numbers are placeholders (Part 17)
