"""SQLite storage: saved fields and soil-sensor readings. File path from KS_DB (default backend/krishi.db)."""
import json, os, sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

def _path(): return os.getenv("KS_DB", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "krishi.db"))

@contextmanager
def conn():
    c = sqlite3.connect(_path()); c.row_factory = sqlite3.Row
    try: yield c; c.commit()
    finally: c.close()

def init():
    with conn() as c:
        c.execute("CREATE TABLE IF NOT EXISTS fields(id INTEGER PRIMARY KEY, name TEXT, polygon_json TEXT, lat REAL, lon REAL, ha REAL, profile_json TEXT, created_at TEXT)")
        c.execute("CREATE TABLE IF NOT EXISTS readings(id INTEGER PRIMARY KEY, field_id INTEGER, ts TEXT, moisture REAL, soil_t REAL, ph REAL, source TEXT CHECK(source IN ('manual','device')))")

now = lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")

def save_field(name, polygon, lat, lon, ha, profile):
    with conn() as c:
        return c.execute("INSERT INTO fields(name,polygon_json,lat,lon,ha,profile_json,created_at) VALUES(?,?,?,?,?,?,?)",
                         (name, json.dumps(polygon), lat, lon, ha, json.dumps(profile), now())).lastrowid

def _field(r): return dict(id=r["id"], name=r["name"], polygon=json.loads(r["polygon_json"]), lat=r["lat"], lon=r["lon"], ha=r["ha"], profile=json.loads(r["profile_json"]), created_at=r["created_at"])
def get_field(i):
    with conn() as c: r = c.execute("SELECT * FROM fields WHERE id=?", (i,)).fetchone()
    return _field(r) if r else None
def list_fields():
    with conn() as c: return [_field(r) for r in c.execute("SELECT * FROM fields ORDER BY id DESC LIMIT 50")]

def add_reading(field_id, moisture, soil_t, ph, source):
    with conn() as c:
        return c.execute("INSERT INTO readings(field_id,ts,moisture,soil_t,ph,source) VALUES(?,?,?,?,?,?)", (field_id, now(), moisture, soil_t, ph, source)).lastrowid

def latest_reading(field_id):
    with conn() as c: r = c.execute("SELECT * FROM readings WHERE field_id=? ORDER BY id DESC LIMIT 1", (field_id,)).fetchone()
    return None if not r else {k: r[k] for k in ("ts", "moisture", "soil_t", "ph", "source")}
