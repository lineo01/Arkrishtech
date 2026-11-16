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

def simulate(W, i0, c, soil="loam", moist=None, irr_mm=0.0, log=False, mult=1.0):
    """Daily soil-water bucket from index i0 of weather W for one crop cycle."""
    fc, wp = SOILS[soil]; n = days_of(c); taw = 1000*(fc-wp)*c["root"]; raw = c["p"]*taw
    dr = min(taw, max(0, (fc-moist/100)*c["root"]*1000)) if moist is not None else .3*taw
    etc_t = eta_t = irr_t = 0.0; stress = heat = frost = 0; ts = 0.0; rows = []
    for d in range(n):
        j = i0+d
        etc = kc_at(c, d)*W["et0"][j]*mult; ks = 1.0 if dr <= raw else max(0.0, (taw-dr)/(taw-raw))
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

def replay(W, c, month, day, soil, moist, irr_mm, mult=1.0):
    """Replay every historical year's actual weather on this field for one sowing date."""
    res = []; n = days_of(c)
    for y in sorted({d.year for d in W["date"]}):
        try: s = date(y, month, day)
        except ValueError: continue
        i = W["idx"].get(s)
        if i is not None and i+n <= len(W["date"]): r = simulate(W, i, c, soil, moist, irr_mm, mult=mult); r["year"] = y; res.append(r)
    return res

def economics(c, yf, I):
    ha = I["ha"]; sm, sc = SEED[I["seed"]]
    lf = min(1, I["workers"]*days_of(c)*.5/(c["labour"]*ha*TOOLS[I["tools"]]))**.7
    kg = c["ym"]*ha*yf*sm*lf*(1.12 if I.get("comp") else 1); cost = c["cost"]*ha*(1+sc)
    return kg, kg*c["price"]-cost, cost

def _q(v, q): v = sorted(v); return v[int(q*(len(v)-1))]

def evaluate(W, key, month, day, I):
    c = CROPS[key]; irr = I["water_l_day"]*I["eff"]/(I["ha"]*1e4) if I["water_l_day"] else 0
    runs = replay(W, c, month, day, I["soil"], I.get("moist"), irr, .85 if I.get("mulch") else 1.0)
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


def whatif(W, key, sow, I):
    """Re-run the replay with one change at a time. Returns p50 yield/profit and change vs. the current plan."""
    water = I["water_l_day"] or 1500
    S = [("Your plan now", {}), ("+ Mulch the soil", dict(mulch=1)), ("+ Compost or manure", dict(comp=1)),
         ("+ Drip irrigation", dict(eff=.9, water_l_day=water)), ("+ Hybrid seed (with compost)", dict(seed="hyb", comp=1)),
         ("+ Power tiller", dict(tools="tiller")), ("+ 2 more workers", dict(workers=I["workers"]+2))]
    out, base = [], None
    for name, m in S:
        e = evaluate(W, key, sow.month, sow.day, {**I, **m})
        if not e: continue
        row = dict(name=name, yield_kg=e["yield_kg"]["p50"], net=e["net"]["p50"], risk=e["risk"])
        if base is None: base = row
        row["delta_yield_pct"] = (row["yield_kg"]-base["yield_kg"])/base["yield_kg"]*100 if base["yield_kg"] else 0.0
        row["delta_net"] = row["net"]-base["net"]; out.append(row)
    return out
