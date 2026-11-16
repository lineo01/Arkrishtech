"""Arkrishitech API + website.  Run:  cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000"""
import json, math
from datetime import date
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from . import engine as E, data as D, db, kb

app = FastAPI(title="Arkrishitech")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
db.init()

class Profile(BaseModel):
    water_l_day: float = 0; irrigation_eff: float = .6; soil: str = "loam"; seed: str = "opv"; workers: int = 3; tools: str = "bullock"
class Sensors(BaseModel):
    moisture: Optional[float] = None; soil_t: Optional[float] = None; ph: Optional[float] = None; source: str = "manual"
class Req(BaseModel):
    polygon: List[List[float]]; profile: Profile = Profile(); sensors: Sensors = Sensors(); field_id: Optional[int] = None; crop: Optional[str] = None
class FieldIn(BaseModel):
    name: str = "My field"; polygon: List[List[float]]; profile: Profile = Profile()
class Chat(BaseModel):
    question: str

dump = lambda m: getattr(m, "model_dump", getattr(m, "dict", None))()

def geo(poly):
    if len(poly) < 3 or any(not (-90 <= p[0] <= 90 and -180 <= p[1] <= 180) for p in poly): raise HTTPException(400, "polygon needs 3+ valid [lat, lon] points")
    lat = sum(p[0] for p in poly)/len(poly); lon = sum(p[1] for p in poly)/len(poly); k = 111320; cl = math.cos(math.radians(lat)); a = 0
    for i, p in enumerate(poly): q = poly[(i+1) % len(poly)]; a += p[1]*cl*k*q[0]*k-q[1]*cl*k*p[0]*k
    return lat, lon, max(.01, abs(a/2)/1e4)

def sensors_for(r):
    s = {k: v for k, v in dump(r.sensors).items() if v is not None and k != "source"}
    if not s and r.field_id: s = {k: v for k, v in (db.latest_reading(r.field_id) or {}).items() if k in ("moisture", "soil_t", "ph") and v is not None}
    return s

def inputs(r, lat, lon, ha):
    p = r.profile
    if p.soil not in E.SOILS or p.seed not in E.SEED or p.tools not in E.TOOLS: raise HTTPException(400, "bad profile value")
    s = sensors_for(r)
    return dict(ha=ha, soil=p.soil, seed=p.seed, workers=max(1, p.workers), tools=p.tools, water_l_day=max(0, p.water_l_day), eff=min(1, max(.1, p.irrigation_eff)), moist=s.get("moisture")), s

def weather(lat, lon):
    try: W = D.get_history(round(lat, 2), round(lon, 2))
    except Exception as e: raise HTTPException(503, f"Could not get NASA weather history and no cached copy exists ({type(e).__name__}). Connect to the internet once.")
    try: fc = D.get_forecast(round(lat, 2), round(lon, 2)); ok = True
    except Exception: n = 16; fc = dict(date=[], tmax=[20]*n, tmin=[10]*n, rain=[0]*n, et0=[2.5]*n); ok = False
    return W, fc, ok

_RANK = {}
def ranked(W, I, lat, lon):
    key = json.dumps([round(lat, 3), round(lon, 3), {k: v for k, v in I.items() if k != "moist"}, round((I["moist"] or -1)/5), date.today().isoformat()], sort_keys=True)
    if key not in _RANK:
        if len(_RANK) > 50: _RANK.clear()
        _RANK[key] = E.rank(W, I)
    return _RANK[key]

def pub(c): return {k: v for k, v in c.items() if k != "_runs"} | {"sow_date": c["sow_date"].isoformat()}

def climate(W):
    n = 30; last = W["date"][-n:]; rain = sum(W["p"][-n:]); norm = []
    for k in range(1, 30):
        tot = 0; ok = True
        for d in last:
            try: i = W["idx"].get(d.replace(year=d.year-k))
            except ValueError: i = None
            if i is None: ok = False; break
            tot += W["p"][i]
        if ok: norm.append(tot)
    return dict(rain_30d=round(rain), rain_30d_normal=round(sum(norm)/len(norm)) if norm else None, tmean_30d=round(sum(W["tmean"][-n:])/n, 1), last_data=last[-1].isoformat())

@app.get("/api/health")
def health(): return {"ok": True}

@app.post("/api/analyze")
def analyze(r: Req):
    lat, lon, ha = geo(r.polygon); I, s = inputs(r, lat, lon, ha); W, fc, fok = weather(lat, lon); rk = ranked(W, I, lat, lon)
    if not rk: raise HTTPException(422, "not enough weather history")
    top = rk[0]
    return dict(field=dict(lat=lat, lon=lon, ha=round(ha, 2), elevation_m=W["z"]), forecast=fc, forecast_ok=fok, climate=climate(W), sensors=s, alerts=E.alerts(fc, s),
                crops=[pub(c) for c in rk[:5]], schedule=E.schedule(W, top["key"], top["sow_date"], I, s.get("soil_t")),
                method=f"FAO-56 Penman-Monteith + daily soil-water balance, replayed over {top['n_years']} past seasons")

def _crop(r):
    if r.crop not in E.CROPS: raise HTTPException(400, "unknown crop")
    lat, lon, ha = geo(r.polygon); I, s = inputs(r, lat, lon, ha); W, fc, fok = weather(lat, lon)
    top = [c for c in ranked(W, I, lat, lon) if c["key"] == r.crop]
    if not top: raise HTTPException(422, "no sowing window found for this crop")
    return W, I, s, top[0]

@app.post("/api/schedule")
def schedule(r: Req):
    W, I, s, c = _crop(r); return E.schedule(W, r.crop, c["sow_date"], I, s.get("soil_t"))

@app.post("/api/whatif")
def whatif(r: Req):
    W, I, s, c = _crop(r); return dict(crop=r.crop, sow_date=c["sow_date"].isoformat(), scenarios=E.whatif(W, r.crop, c["sow_date"], I))

@app.post("/api/fields")
def save_field(f: FieldIn):
    lat, lon, ha = geo(f.polygon); return {"id": db.save_field(f.name, f.polygon, lat, lon, ha, dump(f.profile)), "ha": round(ha, 2)}

@app.get("/api/fields")
def fields(): return db.list_fields()

@app.get("/api/fields/{fid}")
def get_field(fid: int):
    f = db.get_field(fid)
    if not f: raise HTTPException(404, "field not found")
    return f

@app.post("/api/sensors/{fid}")
def add_sensor(fid: int, s: Sensors):
    if s.source not in ("manual", "device"): raise HTTPException(400, "source must be manual or device")
    for v, lo, hi, n in ((s.moisture, 0, 100, "moisture"), (s.soil_t, -20, 60, "soil_t"), (s.ph, 0, 14, "ph")):
        if v is not None and not lo <= v <= hi: raise HTTPException(400, f"{n} out of range")
    if s.moisture is None and s.soil_t is None and s.ph is None: raise HTTPException(400, "send at least one value")
    return {"id": db.add_reading(fid, s.moisture, s.soil_t, s.ph, s.source)}

@app.get("/api/sensors/{fid}/latest")
def latest(fid: int): return db.latest_reading(fid) or {}

@app.post("/api/chat")
def chat(c: Chat): return kb.search(c.question[:300])
_PUBLIC = Path(__file__).resolve().parents[2] / "public"

if _PUBLIC.is_dir():
    app.mount("/", StaticFiles(directory=str(_PUBLIC), html=True), name="web")