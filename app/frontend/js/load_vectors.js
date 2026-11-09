import { clcLegendColormap } from "./layers.js";
const API = "/api";
const popup = (feature, layer) => {
  const rows = Object.entries(feature.properties)
    .map(([k, v]) => `<b>${k}</b>: ${v ?? "–"}`)
    .join("<br>");
  layer.bindPopup(rows);
};
//funkcja  ustalajaca styl clc
const styleFns = {
  clc: feature => {
    const c = clcLegendColormap(feature.properties.code_18).color;
    return { color: c, fillColor: c, weight: 1, opacity: 0.6, fillOpacity: 0.4 };
  }
};
//ładowanie danych z funkcji initvectorLayers
  async function load(entry) {
    if (entry.visible) return;                      // już pobrane, nie pobieraj drugi raz
    const res = await fetch(`${API}/layers/${entry.meta.name}`);
    if (!res.ok) throw new Error(`${entry.meta.name}: ${res.status}`);
    entry.group[entry.meta.layerN].addData(await res.json());
    entry.visible = true;
  }

export async function initVectorLayers(layerContainer, layersOn) {
  const entries = [];

  const catalog = await (await fetch(`${API}/layers`)).json();
//todo: add visible:bool to every layer
console.log(catalog, ":catalog");
  for (const meta of catalog) {
    const group = {}
    const layerN = meta.layerN; 
    group[layerN] = L.geoJSON(null, {
      style: styleFns[meta.name] ?? meta.style,
      onEachFeature: popup,
      pointToLayer: meta.geom === "point"
        ? (f, latlng) => L.circleMarker(latlng, { radius: 3, weight: 0, fillOpacity: 0.9, ...meta.style })
        : undefined
    });

    entries.push({ meta, group, visible: false, abort: null });
    console.log(entries.length);
    layersOn.push({ meta, group, visible: false, abort: null });
    layerContainer.addOverlay(group[layerN], meta.label);
  }

  window.map.on("overlayadd", e => {
    console.log(layerContainer);
    const entry = entries.find(x => x.group[x.meta.layerN] === e.layer);
    if (entry.meta.name == "egms_vector"){
      return;
    }
    load(entry).catch(console.error);
  });
}
export async function getEgmsP(layersOn){
  try{
    console.log("wuut: ", layersOn);
    const view = window.map.getBounds();
    const b = view.pad(0.3) //small movements wont need another query
    console.log(b);
    const bbox = [b.getWest(), b.getSouth(), b.getEast(), b.getNorth()].join(",");
    const entry = layersOn.find(x => x.meta.name === "egms_vector");
    const idx = layersOn.findIndex(x => x.meta.layerN == "egmsP"); 
    console.log("idx:::: ", idx, "entry??: ", entry);
    const e = window.map.getZoom(); 
    const res = await fetch(`${API}/layers/egms_vector?bbox=${bbox}&zoom=${e}`);
    if (!res.ok) throw new Error(`EGMS points: ${res.status}`);
    if(entry.visible){
      entry.visible = false;
      console.log(entry);
      const lay = layersOn[idx].group.egmsP;
      lay.clearLayers();
      //layerContainer.removeLayer(layersOn[0].group.egmsP);
    } 
    entry.group["egmsP"].addData(await res.json());
    entry.visible = true;
    
}catch (e){
  console.error(e);
}
}
