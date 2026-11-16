const S = { poly: null, fieldId: null, tap: { water: 1, tools: 1, seed: 1, crew: 1 }, sensors: {}, sensorHistory: [], sensorMode: "simulation", res: null, sel: 0, whatif: null, sched: null };
let timer = null, whatifRequest = 0, analysisRequest = 0, simTimer = null, serialPort = null, serialReader = null, lastPersist = 0, lastAnalysis = 0;
const busy = on => { $("busy").hidden = !on; };
const fail = e => { $("err").hidden = false; $("err").innerHTML = `<img class="ui-icon" src="https://img.icons8.com/ios/50/243010/error--v1.png" alt="Error"/> ${String(e.message).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"' :"&quot;"}[c]))}`; busy(false); };
const payload = () => ({ polygon: S.poly, field_id: S.fieldId, profile: { water_l_day: GV.water[S.tap.water], irrigation_eff: 0.6, soil: "loam", seed: GV.seed[S.tap.seed], workers: GV.crew[S.tap.crew], tools: GV.tools[S.tap.tools] },
  sensors: { moisture: S.sensors.moisture ?? null, soil_t: S.sensors.soil_t ?? null, ph: S.sensors.ph ?? null } });

function show(s) {
  document.querySelectorAll(".screen").forEach(e => e.hidden = e.id !== s);
  document.querySelectorAll("#nav button").forEach(b => { const active=b.dataset.s===s; b.classList.toggle("sel",active); b.setAttribute("aria-selected",String(active)); });
  if (s === "cmp") { renderCompare(S,onTap,selectCrop); renderWhatif(S); if (S.res && !S.whatif) loadWhatif(); }
  if (s === "farm" && window.MAP) setTimeout(() => MAP.invalidateSize(), 50);
}
window.show = show;
function renderAll() {
  if (!S.res) return;
  renderWeather(S); renderAlerts(S); renderSensors(S, sensorActions);
  renderCompare(S, onTap, selectCrop); renderCrops(S, selectCrop); renderWhatif(S);
  const rp = () => renderPlan(S, rp); rp();
}
async function analyze(preserveSelection = false) {
  if (!S.poly) { fail(new Error("Draw your field on the map before comparing crops.")); return; }
  const request = ++analysisRequest;
  const previousKey = preserveSelection && S.res && S.res.crops[S.sel] ? S.res.crops[S.sel].key : null;
  $("err").hidden = true; busy(true);
  try {
    const result = await api.call("/api/analyze", payload());
    if (request !== analysisRequest) return;
    S.res = result; S.sensors = { ...(S.sensors || {}), ...(result.sensors || {}) };
    const restored = previousKey ? result.crops.findIndex(c => c.key === previousKey) : -1;
    S.sel = restored >= 0 ? restored : 0;
    S.sched = result.schedule; S.whatif = null; S.calM = null;
    $("area").textContent = `Field ≈ ${result.field.ha} ha · ${result.field.lat.toFixed(4)}, ${result.field.lon.toFixed(4)}`;
    renderAll(); busy(false); loadWhatif();
  } catch (e) { if (request === analysisRequest) fail(e); }
}
async function loadWhatif() {
  if (!S.res || !S.res.crops[S.sel]) return;
  const request = ++whatifRequest, k = S.res.crops[S.sel].key;
  $("wi").innerHTML = '<p class="foot">Running scenarios…</p>';
  try {
    const result = await api.call("/api/whatif", { ...payload(), crop: k });
    if (request !== whatifRequest || !S.res || S.res.crops[S.sel].key !== k) return;
    S.whatif = result.scenarios || []; renderWhatif(S);
  } catch (e) { if (request === whatifRequest) fail(e); }
}
async function selectCrop(i) {
  if (!S.res || !S.res.crops[i]) return;
  S.sel = i; S.whatif = null; S.calM = null;
  const request = ++whatifRequest, k = S.res.crops[i].key;
  renderCompare(S, onTap, selectCrop); renderCrops(S, selectCrop); renderWhatif(S); busy(true);
  try {
    const [sc, wi] = await Promise.all([
      api.call("/api/schedule", { ...payload(), crop: k }),
      api.call("/api/whatif", { ...payload(), crop: k })
    ]);
    if (request !== whatifRequest || !S.res || S.res.crops[S.sel].key !== k) return;
    S.sched = sc; S.whatif = wi.scenarios || []; busy(false);
    renderCompare(S, onTap, selectCrop); renderWhatif(S); const rp = () => renderPlan(S, rp); rp();
  } catch (e) { if (request === whatifRequest) fail(e); }
}
function onTap(g, v) { S.tap[g] = v; renderCompare(S, onTap, selectCrop); clearTimeout(timer); timer = setTimeout(() => analyze(true), 350); }
const sensorActions = { connect: () => S.sensorMode === "device" ? disconnectSensor() : connectSensor(), simulate: startSimulation };
function updateSensorReading(v, source) {
  // Some probes report temperature as null while they warm up. Keep the last
  // valid value for that channel instead of discarding the entire sensor frame.
  const aliases = { moisture: v.moisture ?? v.soil_moisture ?? v.humidity, soil_t: v.soil_t ?? v.temperature ?? v.temp, ph: v.ph ?? v.soil_ph };
  const limits = { moisture: [0, 100], soil_t: [-20, 60], ph: [0, 14] };
  const clean = { ...S.sensors };
  for (const key of Object.keys(limits)) {
    const n = Number(aliases[key]);
    if (aliases[key] !== null && aliases[key] !== undefined && Number.isFinite(n) && n >= limits[key][0] && n <= limits[key][1]) clean[key] = n;
  }
  if (!Object.keys(limits).some(k => Number.isFinite(clean[k]))) return;
  clean.source = source; clean.ts = new Date().toISOString();
  S.sensors = clean; S.sensorHistory.push({ ...clean }); S.sensorHistory = S.sensorHistory.slice(-24);
  S.sensorMode = source === "device" ? "device" : "simulation";
  renderSensors(S, sensorActions);
  renderAuto(S);
  if (S.fieldId && source === "device" && Date.now()-lastPersist > 10000) {
    lastPersist = Date.now();
    api.call("/api/sensors/"+S.fieldId,{moisture:clean.moisture,soil_t:clean.soil_t,ph:clean.ph,source:"device"}).catch(e=>console.warn("sensor persistence",e));
  }
  if (S.poly && Date.now()-lastAnalysis > 45000) {
    lastAnalysis = Date.now();
    analyze(true);
  }
}
function startSimulation() {
  if (serialReader) { try { serialReader.cancel(); } catch(e) {} serialReader = null; }
  if (serialPort) { try { serialPort.close(); } catch(e) {} serialPort = null; }
  if (simTimer) clearInterval(simTimer);
  S.sensorMode = "simulation";
  let tick = 0;
  const sample = () => {
    tick++;
    const wave = Math.sin(tick/5);
    updateSensorReading({moisture:Math.round(43+wave*8+Math.sin(tick/13)*3),soil_t:+(17+Math.sin(tick/8)*1.8).toFixed(1),ph:+(6.2+Math.sin(tick/17)*.15).toFixed(2)},"simulation");
  };
  sample(); simTimer = setInterval(sample,2500);
}
async function connectSensor() {
  if (!("serial" in navigator)) { fail(new Error("USB serial is not supported here. Open this app in Chrome or Edge on localhost/HTTPS, or use simulation fallback.")); return; }
  try {
    if (simTimer) { clearInterval(simTimer); simTimer=null; }
    serialPort = await navigator.serial.requestPort();
    await serialPort.open({ baudRate: 115200 });
    S.sensorMode = "device"; renderSensors(S,sensorActions);
    const decoder = new TextDecoderStream();
    const closed = serialPort.readable.pipeTo(decoder.writable);
    serialReader = decoder.readable.getReader();
    let buffer = "";
    (async()=>{
      try {
        while (true) {
          const {value,done} = await serialReader.read(); if(done) break;
          buffer += value;
          const lines = buffer.split(/\r?\n/); buffer = lines.pop() || "";
          for (const line of lines) {
            const t=line.trim(); if(!t) continue;
            try {
              let d;
              if (t.startsWith("{")) d = JSON.parse(t);
              else {
                const parts = t.split(/[;,\t]/).map(x => x.trim());
                if (parts.some(x => /[=:]/.test(x))) {
                  d = {};
                  for (const part of parts) { const m = part.match(/^([a-z_ ]+)\s*[:=]\s*(-?\d+(?:\.\d+)?|null)$/i); if (m) d[m[1].trim().toLowerCase().replace(/\s+/g,"_")] = m[2] === "null" ? null : Number(m[2]); }
                } else { const [moisture, soil_t, ph] = parts; d = { moisture: Number(moisture), soil_t: soil_t === "null" ? null : Number(soil_t), ph: Number(ph) }; }
              }
              updateSensorReading(d,"device");
            } catch(e) { console.warn("ignored sensor line",t); }
          }
        }
      } catch(e) { if(S.sensorMode==="device") console.warn("serial stream ended",e); }
      finally { try{serialReader.releaseLock()}catch(e){} serialReader=null; try{await closed}catch(e){}; if(S.sensorMode==="device") startSimulation(); }
    })();
  } catch(e) { fail(new Error("Could not connect to the sensor port: "+e.message)); startSimulation(); }
}
async function disconnectSensor() {
  S.sensorMode = "simulation";
  try { if(serialReader) await serialReader.cancel(); } catch(e) {}
  try { if(serialPort) await serialPort.close(); } catch(e) {}
  serialPort=null; serialReader=null; startSimulation();
}

window.MAP = initMap(async poly => {
  S.poly = poly; if (!poly) return;
  try { const f = await api.call("/api/fields", { name: "My field", polygon: poly }); S.fieldId = f.id; } catch (e) { return fail(e); }
  analyze();
});
document.querySelectorAll("#nav button").forEach(b => b.onclick = () => show(b.dataset.s));
if ($("runSim")) $("runSim").onclick = () => analyze(true);
$("toFarm").onclick = () => show("farm");
// Voice conversation uses the browser's speech recognition and speech synthesis.
// The answer itself still comes from the same retrieval-grounded farming assistant.
let recognition = null, listening = false;
const voiceStatus = msg => { if ($("voiceStatus")) $("voiceStatus").textContent = msg; };
function speakText(text) {
  if (!("speechSynthesis" in window)) { voiceStatus("Speech playback is not supported in this browser."); return; }
  const clean = String(text || "").trim(); if (!clean) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(clean);
  utterance.lang = $("voiceLang")?.value || "ne-NP";
  utterance.rate = 0.9; utterance.pitch = 1;
  utterance.onstart = () => voiceStatus("Speaking answer…");
  utterance.onend = () => voiceStatus("Voice assistant ready");
  utterance.onerror = () => voiceStatus("Could not play audio. You can read the answer or try another language.");
  window.speechSynthesis.speak(utterance);
}
async function askAssistant(question) {
  const q = String(question || $("q").value).trim(); if (!q) return;
  $("q").value = ""; $("ask").disabled = true; voiceStatus("Finding farming advice…");
  try {
    const answer = await api.call("/api/chat", { question: q });
    addChat(q, answer);
    if ($("voiceReplies").checked) speakText([answer.title, answer.answer].filter(Boolean).join(". "));
    else voiceStatus("Answer ready");
  } catch (e) { fail(e); voiceStatus("Could not reach the assistant. Please try again."); }
  finally { $("ask").disabled = false; }
}
$("ask").onclick = () => askAssistant();
$("q").onkeydown = e => { if (e.key === "Enter") askAssistant(); };
function startVoiceInput() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) { voiceStatus("Voice input is not supported here. Please use Chrome or Edge, or type your question."); return; }
  if (listening && recognition) { recognition.stop(); return; }
  try {
    recognition = new SpeechRecognition(); recognition.lang = $("voiceLang").value; recognition.interimResults = true; recognition.continuous = false;
    recognition.onstart = () => { listening = true; $("mic").classList.add("recording"); $("mic").innerHTML = `<img class="ui-icon" src="https://img.icons8.com/ios/50/243010/stop.png" alt=""/> Stop`; voiceStatus("Listening… speak your question"); };
    recognition.onresult = event => {
      let finalText = "", interim = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) finalText += transcript; else interim += transcript;
      }
      if (interim) { $("q").value = interim; voiceStatus("Hearing: " + interim); }
      if (finalText.trim()) { $("q").value = finalText.trim(); voiceStatus("Question captured"); askAssistant(finalText.trim()); }
    };
    recognition.onerror = event => { voiceStatus(event.error === "not-allowed" ? "Microphone permission was denied. Allow microphone access or type your question." : "Voice input error: " + event.error); };
    recognition.onend = () => { listening = false; $("mic").classList.remove("recording"); $("mic").innerHTML = `<img class="ui-icon" src="https://img.icons8.com/ios/50/243010/microphone.png" alt=""/> Speak`; if (!$("q").value.trim()) voiceStatus("Voice assistant ready"); };
    recognition.start();
  } catch (e) { voiceStatus("Could not start microphone. Check browser permission and try again."); }
}
$("mic").onclick = startVoiceInput;
$("stopVoice").onclick = () => { if (recognition && listening) recognition.stop(); if ("speechSynthesis" in window) window.speechSynthesis.cancel(); voiceStatus("Audio stopped"); };
$("voiceLang").onchange = () => { if (recognition && listening) recognition.stop(); voiceStatus("Language set to " + $("voiceLang").selectedOptions[0].textContent); };
renderSensors(S, sensorActions); startSimulation();
