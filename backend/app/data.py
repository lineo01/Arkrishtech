"""Data sources with disk cache: NASA POWER (history), Open-Meteo (forecast). KS_OFFLINE=1 uses synthetic data (tests only)."""
import os, json, time, math, random, requests
from datetime import date, timedelta
from functools import lru_cache
from .engine import et0_pm

POWER = "https://power.larc.nasa.gov/api/temporal/daily/point"
CACHE = os.getenv("KS_CACHE", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "cache"))

def _path(n): os.makedirs(CACHE, exist_ok=True); return os.path.join(CACHE, n)
def _load(n, ttl):
    p = _path(n)
    if not os.path.exists(p): return None, False
    with open(p) as f: return json.load(f), time.time()-os.path.getmtime(p) < ttl
def _save(n, d):
    with open(_path(n), "w") as f: json.dump(d, f)

def _pack(dates, tmax, tmin, p, rh, ws, rs, lat, z):
    W = dict(date=dates, p=p, tmax=tmax, tmin=tmin, tmean=[(a+b)/2 for a, b in zip(tmax, tmin)], et0=[])
    for i, d in enumerate(dates): W["et0"].append(et0_pm(tmax[i], tmin[i], rh[i], ws[i], rs[i], lat, z, d.timetuple().tm_yday))
    W["idx"] = {d: i for i, d in enumerate(dates)}; W["lat"], W["z"] = lat, z
    return W

def _clean(v):
    out, last = [], 0.0
    for x in v: last = last if (x is None or x <= -900) else x; out.append(last)
    return out

def _from_raw(r, lat):
    return _pack([date.fromisoformat(x) for x in r["dates"]], r["tmax"], r["tmin"], r["p"], r["rh"], r["ws"], r["rs"], lat, r["z"])

@lru_cache(maxsize=8)
def get_history(lat, lon, years=30):
    """30 years of daily weather. Disk cache is reused for 30 days, and used even if stale when offline."""
    if os.getenv("KS_OFFLINE"): return synthetic_history(lat, lon, years)
    name = f"hist_{lat}_{lon}.json"; raw, fresh = _load(name, 30*86400)
    if raw and fresh: return _from_raw(raw, lat)
    try:
        end = date.today()-timedelta(days=5); start = date(end.year-years, 1, 1)
        r = requests.get(POWER, params=dict(parameters="T2M_MAX,T2M_MIN,PRECTOTCORR,RH2M,WS2M,ALLSKY_SFC_SW_DWN", community="AG", longitude=lon, latitude=lat,
            start=start.strftime("%Y%m%d"), end=end.strftime("%Y%m%d"), format="JSON"), timeout=180); r.raise_for_status()
        j = r.json(); p = j["properties"]["parameter"]; keys = sorted(p["T2M_MAX"]); g = lambda n: _clean([p[n][k] for k in keys])
        raw = dict(dates=[f"{k[:4]}-{k[4:6]}-{k[6:]}" for k in keys], tmax=g("T2M_MAX"), tmin=g("T2M_MIN"), p=[max(0, x) for x in g("PRECTOTCORR")],
                   rh=g("RH2M"), ws=g("WS2M"), rs=g("ALLSKY_SFC_SW_DWN"), z=j["geometry"]["coordinates"][2])
        _save(name, raw); return _from_raw(raw, lat)
    except Exception:
        if raw: return _from_raw(raw, lat)   # stale cache beats nothing
        raise

def get_forecast(lat, lon, days=16):
    """16-day forecast incl. FAO ET0. Cached 3 hours; stale cache used if offline."""
    if os.getenv("KS_OFFLINE"):
        return dict(date=[(date.today()+timedelta(days=i)).isoformat() for i in range(days)], tmax=[20]*days, tmin=[6]*days, rain=[0]*days, et0=[2.5]*days)
    name = f"fc_{lat}_{lon}.json"; c, fresh = _load(name, 3*3600)
    if c and fresh: return c
    try:
        j = requests.get("https://api.open-meteo.com/v1/forecast", params=dict(latitude=lat, longitude=lon, forecast_days=days, timezone="auto",
            daily="temperature_2m_max,temperature_2m_min,precipitation_sum,et0_fao_evapotranspiration"), timeout=30).json()["daily"]
        f = lambda k: [x if x is not None else 0 for x in j[k]]
        c = dict(date=j["time"], tmax=f("temperature_2m_max"), tmin=f("temperature_2m_min"), rain=f("precipitation_sum"), et0=f("et0_fao_evapotranspiration"))
        _save(name, c); return c
    except Exception:
        if c: return c
        raise

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
