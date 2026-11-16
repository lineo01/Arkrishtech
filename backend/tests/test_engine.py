import time
from app import engine as E, data as D
I = dict(ha=.5, soil="loam", seed="opv", workers=3, tools="bullock", water_l_day=0, eff=.6, moist=None)
def W(): return D.get_history(27.7, 85.5)
def test_et0(): assert 1.5 < E.et0_pm(22, 8, 60, 1.5, 16, 27.7, 1900, 320) < 4
def test_fao33_example(): assert abs(E.yield_fraction(.8, 160, 250)-.712) < 1e-6
def test_irrigation_helps():
    a = E.evaluate(W(), "lentil", 10, 20, I); b = E.evaluate(W(), "lentil", 10, 20, I | dict(water_l_day=4000))
    assert b["yield_kg"]["p50"] >= a["yield_kg"]["p50"] and b["risk"] <= a["risk"]
def test_monsoon_beats_winter_for_maize():
    assert E.evaluate(W(), "maize_beans", 5, 1, I)["yield_kg"]["p50"] > E.evaluate(W(), "maize_beans", 12, 1, I)["yield_kg"]["p50"]
def test_rank_and_schedule():
    t = time.time(); r = E.rank(W(), I); print("rank secs", round(time.time()-t, 2))
    assert len(r) >= 5 and r[0]["score"] >= r[-1]["score"]
    s = E.schedule(W(), r[0]["key"], r[0]["sow_date"], I); assert any(x["type"] == "sow" for x in s["tasks"])
def test_alerts():
    a = E.alerts(dict(tmax=[20]*10, tmin=[6]*10, rain=[0]*10, et0=[4]*10), dict(moisture=20, ph=4.8)); assert any(x["type"] == "drought" for x in a) and len(a) >= 3
def test_whatif():
    r = E.rank(W(), I)[0]; w = E.whatif(W(), r["key"], r["sow_date"], I); assert len(w) == 7
    by = {x["name"]: x for x in w}; base = by["Your plan now"]["yield_kg"]
    assert by["+ Compost or manure"]["yield_kg"] >= base and by["+ Drip irrigation"]["yield_kg"] >= base-1e-6
