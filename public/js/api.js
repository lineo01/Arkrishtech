const api = {
  async call(path, body, method) {
    const r = await fetch(API_URL + path, { method: method || (body ? "POST" : "GET"), headers: { "Content-Type": "application/json" }, body: body ? JSON.stringify(body) : undefined });
    if (!r.ok) { let m = r.statusText; try { const j = await r.json(); m = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail); } catch (e) {} throw new Error(m); }
    return r.json();
  }
};
