function initMap(onPolygon) {
  const map = L.map("map").setView([27.693, 85.52], 14);
  const sat = L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", { attribution: "Esri", maxZoom: 19 }).addTo(map);
  const osm = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { attribution: "© OpenStreetMap", maxZoom: 19 });
  L.control.layers({ Satellite: sat, Streets: osm }).addTo(map);
  const fg = L.featureGroup().addTo(map);
  map.addControl(new L.Control.Draw({ draw: { polygon: { allowIntersection: false, shapeOptions: { color: "#243010" } }, rectangle: true, polyline: false, circle: false, marker: false, circlemarker: false }, edit: { featureGroup: fg } }));
  const send = l => onPolygon(l.getLatLngs()[0].map(p => [p.lat, p.lng]));
  map.on("draw:created", e => { fg.clearLayers(); fg.addLayer(e.layer); send(e.layer); });
  map.on("draw:edited", () => fg.eachLayer(send));
  map.on("draw:deleted", () => onPolygon(null));
  document.getElementById("loc").onclick = () => navigator.geolocation && navigator.geolocation.getCurrentPosition(p => map.setView([p.coords.latitude, p.coords.longitude], 16));
  return map;
}
