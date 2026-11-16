from fastapi.testclient import TestClient
from app.main import app
c = TestClient(app); POLY = [[27.693, 85.52], [27.694, 85.522], [27.6925, 85.523], [27.692, 85.5205]]
def body(**k): return dict(polygon=POLY, profile=dict(water_l_day=3000), sensors=dict(moisture=22, soil_t=13, ph=5.0), **k)
def test_health(): assert c.get("/api/health").json() == {"ok": True}
def test_analyze():
    r = c.post("/api/analyze", json=body()); assert r.status_code == 200, r.text; j = r.json()
    assert len(j["crops"]) >= 3 and j["schedule"]["tasks"] and "rain_30d" in j["climate"] and any(a["type"] == "sensor" for a in j["alerts"])
def test_bad_input():
    assert c.post("/api/analyze", json=dict(polygon=[[1, 2]])).status_code == 400
    assert c.post("/api/analyze", json=dict(polygon=POLY, profile=dict(soil="rock"))).status_code == 400
def test_schedule_whatif():
    k = c.post("/api/analyze", json=body()).json()["crops"][0]["key"]
    assert c.post("/api/schedule", json=body(crop=k)).json()["tasks"]
    assert len(c.post("/api/whatif", json=body(crop=k)).json()["scenarios"]) == 7
    assert c.post("/api/whatif", json=body(crop="nope")).status_code == 400
def test_fields_and_sensors():
    fid = c.post("/api/fields", json=dict(name="t", polygon=POLY)).json()["id"]; assert c.get(f"/api/fields/{fid}").json()["name"] == "t"
    assert c.post(f"/api/sensors/{fid}", json=dict(moisture=33, soil_t=12, ph=6.1, source="device")).status_code == 200
    assert c.get(f"/api/sensors/{fid}/latest").json()["moisture"] == 33
    assert c.post(f"/api/sensors/{fid}", json=dict(moisture=300)).status_code == 400
    r = c.post("/api/analyze", json=dict(polygon=POLY, field_id=fid)).json(); assert r["sensors"]["moisture"] == 33
def test_chat():
    assert "Jeevamrit" in c.post("/api/chat", json=dict(question="how to make natural fertilizer?")).json()["title"]
    assert "Neem" in c.post("/api/chat", json=dict(question="aphids on my plants")).json()["title"]
    assert c.post("/api/chat", json=dict(question="xyzzy qwerty")).json()["matched"] is False
