const $ = id => document.getElementById(id), nf = x => Math.round(x).toLocaleString("en-IN"), esc = s => String(s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const G = { water: ["Rain only", "Well or pond", "Canal or river"], tools: ["Hand tools", "Bullock plough", "Power tiller"], seed: ["My saved seed", "Improved seed", "Hybrid seed"], crew: ["1 to 2 people", "3 to 4 people", "5 or more"] };
const icon = (name, alt = "") => `<img class="ui-icon" src="https://img.icons8.com/ios/50/243010/${name}.png" alt="${alt}"/>`;
const GL = { water: "Water access", tools: "Tools", seed: "Seed", crew: "Workers" };
const GV = { water: [0, 3000, 6000], tools: ["hand", "bullock", "tiller"], seed: ["own", "opv", "hyb"], crew: [2, 4, 6] };
const TY = { prepare: ["#81917f", "Prepare land"], sow: ["#9eae91", "Sow"], care: ["#b5bda0", "Care / feed"], water: ["#8da5a0", "Water"], harvest: ["#c1b99d", "Harvest"] };

function renderWeather(S) {
  const r = S.res, f = r.forecast, c = r.climate; let h = "";
  h += `<div class="chip"><small>Field</small><b>${r.field.ha} ha</b><small>${Math.round(r.field.elevation_m)} m high</small></div>`;
  h += `<div class="chip"><small>Rain last 30 days (NASA)</small><b>${c.rain_30d} mm</b><small>normal ~${c.rain_30d_normal ?? "?"} mm</small></div>`;
  h += `<div class="chip"><small>Avg temp 30 days</small><b>${c.tmean_30d}°C</b><small>data to ${c.last_data.slice(5)}</small></div>`;
  for (let i = 0; i < Math.min(7, f.tmax.length); i++) h += `<div class="chip"><small>${(f.date[i] || "day " + (i + 1)).slice(5)}</small><b>${Math.round(f.tmax[i])}° / ${Math.round(f.tmin[i])}°</b><small>${icon("water")} ${f.rain[i]} mm</small></div>`;
  if (!r.forecast_ok) h += `<div class="chip"><small>Forecast</small><b>offline</b><small>not available</small></div>`;
  $("wx").innerHTML = h;
}
function renderAlerts(S) {
  const a = S.res.alerts; $("alerts").innerHTML = a.length ? a.map(x => `<div class="alert ${x.level === "high" ? "high" : ""}">${esc(x.msg)}</div>`).join("") : '<div class="alert ok">No major risks in the next days.</div>';
}
function renderSensors(S) {
  const s = S.sensors || {}, hist = S.sensorHistory || [];
  const metric = (name, key, unit, max, decimals = 1) => {
    const safe = s[key] !== null && s[key] !== undefined && Number.isFinite(Number(s[key])) ? Number(s[key]) : null;
    const samples = hist.slice(-10).filter(x => x[key] !== null && x[key] !== undefined).map(x => Number(x[key])).filter(Number.isFinite);
    const avg = samples.length ? samples.reduce((a,b)=>a+b,0)/samples.length : safe;
    const bars = samples.map((n,i) => `<i title="${n.toFixed(decimals)} ${unit}" style="height:${Math.max(4,Math.min(100,n/max*100))}%"></i>`).join("");
    return `<div class="sensor-metric"><div class="sensor-head"><span>${name}</span><b>${safe == null ? "—" : safe.toFixed(decimals)} <small>${unit}</small></b></div><div class="sensor-trend"><span>${avg == null ? "Awaiting reading" : `Average ${avg.toFixed(decimals)} ${unit}`}</span><div class="sensor-spark">${bars || '<i class="empty"></i>'}</div></div></div>`;
  };
  const updated = s.ts ? new Date(s.ts).toLocaleTimeString([], {hour:"2-digit",minute:"2-digit"}) : "Waiting for readings";
  $("sens").innerHTML = `<div class="sensor-status"><span class="sensor-dot ${s.ts ? 'live' : ''}"></span><b>Latest readings</b><small>${updated}</small></div>
    <div class="sensor-grid">${metric("Soil moisture","moisture","%",100,0)}${metric("Soil temperature","soil_t","°C",50,1)}${metric("Soil pH","ph","pH",14,1)}</div>`;
}

const best = (cs, f, hi) => { const v = cs.map(f), m = hi ? Math.max(...v) : Math.min(...v); return v.map(x => x === m); };
const hasNum = v => v !== null && v !== undefined && Number.isFinite(Number(v));
function renderAuto(S) {
  const r = S.res, s = S.sensors || {};
  const rows = [
    ["Field size", r ? r.field.ha + " ha" : null, "Map"],
    ["Soil moisture", hasNum(s.moisture) ? Math.round(s.moisture) + "%" : null, "Sensor"],
    ["Soil temperature", hasNum(s.soil_t) ? (+s.soil_t).toFixed(1) + "°C" : null, "Sensor"],
    ["Soil pH", hasNum(s.ph) ? (+s.ph).toFixed(1) : null, "Sensor"],
    ["Rain, last 30 days", r ? r.climate.rain_30d + " mm" : null, "NASA"]
  ];
  $("auto").innerHTML = rows.map(([l, v, src]) => `<div class="kv-row"><span>${l}<em>${src}</em></span><b class="${v == null ? "unset" : ""}">${v ?? "—"}</b></div>`).join("");
}
function renderTaps(S, onTap) {
  $("taps").innerHTML = Object.keys(G).map(g => `<div class="tap-group"><div class="tap-label" id="tl-${g}">${GL[g]}</div><div class="seg" role="group" aria-labelledby="tl-${g}">${G[g].map((l, i) => `<button type="button" class="seg-btn ${S.tap[g] === i ? "sel" : ""}" aria-pressed="${S.tap[g] === i}" data-g="${g}" data-v="${i}">${l}</button>`).join("")}</div></div>`).join("");
  document.querySelectorAll("#taps .seg-btn").forEach(b => b.onclick = () => onTap(b.dataset.g, +b.dataset.v));
}
function renderCompare(S, onTap, onCrop) {
  renderAuto(S); renderTaps(S, onTap);
  const r = S.res, empty = !r;
  $("cmpEmpty").hidden = !empty; $("tblWrap").hidden = empty;
  if (empty) { $("tbl").innerHTML = ""; $("verdict").innerHTML = ""; return; }
  const cs = r.crops;
  const top = cs[0], safe = cs.reduce((a, b) => b.risk < a.risk ? b : a);
  $("verdict").innerHTML = `<div class="reco"><div class="reco-item"><small>Best overall</small><b>${esc(top.name)}</b><span>Ranked first for current conditions. About ${nf(top.yield_kg.p50)} kg, net NPR ${nf(top.net.p50)}.</span></div><div class="reco-item"><small>Safest</small><b>${esc(safe.name)}</b><span>${Math.round(safe.risk * 100)}% bad-season risk. Pair a cereal with a legume to spread risk.</span></div></div>`;
  const rows = [["Sow on", c => c.sow_date.slice(5)], ["Likely yield", c => nf(c.yield_kg.p50) + " kg", c => c.yield_kg.p50, 1], ["Bad year – good year", c => nf(c.yield_kg.p10) + " – " + nf(c.yield_kg.p90) + " kg"], ["Income", c => "NPR " + nf(c.net.p50 + c.cost), c => c.net.p50 + c.cost, 1], ["Cost", c => "NPR " + nf(c.cost), c => c.cost, 0], ["Net profit", c => "NPR " + nf(c.net.p50), c => c.net.p50, 1], ["Bad-season risk", c => Math.round(c.risk * 100) + "%", c => c.risk, 0], ["Water needed", c => Math.round(c.water_need_mm) + " mm", c => c.water_need_mm, 0], ["Days to harvest", c => c.days, c => c.days, 0], ["Held back by", c => c.held_back], ["Soil benefit", c => c.legume ? "Restores soil" : "—"], ["Verdict", c => c === top ? "Best overall" : c === safe ? "Safest" : ""]];
  $("tbl").innerHTML = `<thead><tr><th scope="col"></th>${cs.map((c, i) => `<th scope="col" data-c="${i}" class="${i === S.sel ? "sel" : ""}" aria-sort="none" title="Select ${esc(c.name)}">${esc(c.name)}</th>`).join("")}</tr></thead><tbody>` + rows.map(([l, f, k, hi]) => { const b = k ? best(cs, k, hi) : []; return `<tr><th scope="row">${l}</th>${cs.map((c, i) => `<td class="${i === S.sel ? "cs" : ""} ${b[i] ? "bst" : ""}">${f(c)}</td>`).join("")}</tr>`; }).join("") + "</tbody>";
  document.querySelectorAll("#tbl th[data-c]").forEach(th => th.onclick = () => onCrop(+th.dataset.c));
}
function renderWhatif(S) {
  const run = $("runSim");
  if (!S.res || !S.res.crops[S.sel]) {
    run.disabled = true; $("wit").hidden = true; $("wi").innerHTML = "";
    $("simIntro").innerHTML = '<div class="empty-state"><b>No simulation yet</b><p>Draw your field on My Farm, then select a crop to see how changes to your plan affect yield and income.</p></div>';
    return;
  }
  run.disabled = false; $("wit").hidden = false;
  const c = S.res.crops[S.sel];
  $("simIntro").innerHTML = `<div class="sim-summary"><div><small>Selected crop</small><b>${esc(c.name)}</b></div><div><small>Likely yield</small><b>${nf(c.yield_kg.p50)} kg</b></div><div><small>Net profit</small><b>NPR ${nf(c.net.p50)}</b></div></div>`;
  $("wit").textContent = "If you plant " + c.name + ", what if you…";
  const w = S.whatif; if (!w) { $("wi").innerHTML = '<p class="foot">Loading…</p>'; return; }
  const mx = Math.max(...w.map(x => x.yield_kg), 1);
  const sgn = n => n >= 0 ? "+" : "−";
  $("wi").innerHTML = w.map((x, i) => `<div class="wi"><span class="wi-name">${esc(x.name)}</span><div class="wb"><i style="width:${x.yield_kg / mx * 100}%"></i></div><span class="wi-val"><b>${nf(x.yield_kg)} kg</b>${i ? `<em class="${x.delta_yield_pct >= 0 ? "pos" : "neg"}">${sgn(x.delta_yield_pct)}${Math.abs(x.delta_yield_pct).toFixed(0)}%</em><small class="${x.delta_net >= 0 ? "pos" : "neg"}">${sgn(x.delta_net)}NPR ${nf(Math.abs(x.delta_net))}</small>` : "<small>Baseline</small>"}</span></div>`).join("") + '<p class="foot">Each line re-runs all past seasons with that one change. Costs of buying a tiller or drip kit are not included.</p>';
}
const ymd = d => d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0");
function renderPlan(S, rerender) {
  const sc = S.sched; if (!sc) { $("cal").innerHTML = "Draw a field first."; return; }
  const done = JSON.parse(localStorage.ks_done || "{}"), kid = t => sc.crop + "|" + t.date + "|" + t.task, by = {};
  sc.tasks.forEach(t => (by[t.date] = by[t.date] || []).push(t));
  if (!S.calM || S.calCrop !== sc.crop) { const d = new Date(sc.sow_date + "T00:00"); S.calM = new Date(d.getFullYear(), d.getMonth(), 1); S.calSel = sc.sow_date; S.calCrop = sc.crop; }
  const y = S.calM.getFullYear(), m = S.calM.getMonth(), first = new Date(y, m, 1).getDay(), nd = new Date(y, m + 1, 0).getDate(), today = ymd(new Date());
  let g = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map(d => `<div class="dow">${d}</div>`).join(""); for (let i = 0; i < first; i++) g += "<div></div>";
  for (let d = 1; d <= nd; d++) { const k = `${y}-${String(m + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`; g += `<div class="day ${k === today ? "today" : ""} ${k === S.calSel ? "sel" : ""}" data-k="${k}"><span>${d}</span><div class="dots">${(by[k] || []).map(t => `<i class="${done[kid(t)] ? "dn" : ""}" style="background:${(TY[t.type] || TY.care)[0]}"></i>`).join("")}</div></div>`; }
  const day = by[S.calSel] || [], c = S.res.crops.find(x => x.key === sc.crop), name = c ? c.name : sc.crop;
  const pr = Math.max(0, Math.min(100, (Date.now() - new Date(sc.sow_date)) / 864e5 / (c ? c.days : 100) * 100));
  $("cal").innerHTML = `<b>${esc(name)}</b>: ${pr === 0 ? "Not sown yet" : pr < 100 ? "Growing" : "Harvest time"}<div class="bar"><i style="width:${pr}%"></i></div>${sc.warnings.map(w => `<div class="alert high">${esc(w)}</div>`).join("")}
   <div class="cnav"><button class="alt" id="cp">‹</button><b>${S.calM.toLocaleString("en", { month: "long", year: "numeric" })}</b><button class="alt" id="cn">›</button></div><div class="cal">${g}</div>
   <div class="leg">${Object.values(TY).map(t => `<span><i style="background:${t[0]}"></i>${t[1]}</span>`).join("")}</div>
   <div class="dd">${day.length ? day.map(t => `<div class="task"><input type="checkbox" data-id="${esc(kid(t))}" ${done[kid(t)] ? "checked" : ""}><span style="flex:1">${esc(t.task)}<br><small style="color:var(--mut)">${esc(t.reason)}</small></span><span class="tag">${(TY[t.type] || TY.care)[1]}</span></div>`).join("") : "No tasks on this day. Tap a day with a coloured dot."}</div>${(() => { const n = sc.tasks.filter(t => t.date >= today && !done[kid(t)]).slice(0, 2); return n.length ? `<div class="hint">Coming up: ${n.map(t => fmtDate(t.date) + " – " + esc(t.task)).join(" · ")}</div>` : ""; })()}`;
  document.querySelectorAll(".day").forEach(el => el.onclick = () => { S.calSel = el.dataset.k; rerender(); });
  $("cp").onclick = () => { S.calM = new Date(y, m - 1, 1); rerender(); }; $("cn").onclick = () => { S.calM = new Date(y, m + 1, 1); rerender(); };
  document.querySelectorAll(".dd input").forEach(el => el.onchange = () => { const d = JSON.parse(localStorage.ks_done || "{}"); d[el.dataset.id] = el.checked; localStorage.ks_done = JSON.stringify(d); rerender(); });
}
function addChat(q, a) {
  const L = $("chatlog"), u = document.createElement("div"), b = document.createElement("div");
  u.className = "m u"; u.textContent = q; b.className = "m elder-answer";
  b.innerHTML = icon("plant-under-sun") + (a.title ? `<b>${esc(a.title)}</b><br>` : "") + esc(a.answer || "I could not find a close match in the knowledge library.") +
    (a.sources && a.sources.length ? `<div class="retrieval-sources"><b>Knowledge retrieved</b>${a.sources.map(x=>`<small>• ${esc(x.title)} — ${esc(x.source)} · ${esc(x.verified_by || "Review status not recorded")} (match ${Math.round((x.score||0)*100)}%)</small>`).join("")}</div>` :
    (a.matched ? `<small>Source: ${esc(a.source)} · Review: ${esc(a.verified_by)}</small>` : "<small>No matching source found. Please check with a local agricultural extension worker or trusted elder.</small>"));
  const listen = document.createElement("button");
  listen.type = "button"; listen.className = "alt chat-listen"; listen.innerHTML = `${icon("speaker")} Listen`;
  listen.addEventListener("click", () => speakText([a.title, a.answer].filter(Boolean).join(". ")));
  b.appendChild(listen);
  L.append(u, b); L.scrollTop = L.scrollHeight;
}

const TIPS = { finger_millet: "Drought-hardy landrace; intercrop with black gram.", buckwheat: "Fast cover crop; suppresses weeds on poor soil.", maize_beans: "Three-sisters mix: beans fix nitrogen for the maize.", lentil: "Winter legume sown into leftover soil moisture.", mustard: "Use as a border or trap crop for aphids.", wheat_barley: "Use saved seed; follow a legume.", potato: "Mulch with straw; never repeat on the same plot.", turmeric: "Likes shade; mulch heavily with leaves." };
const fmtDate = iso => new Date(iso + "T00:00").toLocaleString("en", { month: "short", day: "numeric" });
function renderCrops(S, onCrop) {
  const cs = S.res.crops, top = cs[0].score;
  $("crops").innerHTML = cs.map((c, i) => {
    const m = top > 0 && c.score > 0 ? Math.max(5, Math.min(100, Math.round(c.score / top * 100))) : 100 - i * 10;
    return `<div class="crop ${i === S.sel ? "sel" : ""}" data-i="${i}"><div><b>${esc(c.name)}</b>${c.legume ? ` <span class="crop-trait">LEGUME</span>` : ""}<small>Sow ~${fmtDate(c.sow_date)} · ${c.days} days · ~${Math.round(c.water_need_mm)} mm water</small><small>${esc(TIPS[c.key] || "")}</small></div><div class="match"><b>${m}%</b><div class="bar"><i style="width:${m}%"></i></div></div></div>`;
  }).join("") + '<div class="hint">Legume crops can help restore soil. Match is relative to the best crop. Mixed cropping beats repeating one crop.</div><button id="go" class="wide">Next: calculate crops and simulate →</button>';
  document.querySelectorAll("#crops .crop").forEach(el => el.onclick = () => onCrop(+el.dataset.i));
  $("go").onclick = () => show("cmp");
}
