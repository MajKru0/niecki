import { getEgmsP } from './load_vectors.js';
const API = "/api";


export async function filterContext(minv, maxv, lc, isOn){
    if(!isOn){
      getEgmsP(lc);
    } else{
        console.log("min: ", minv, " max: ", maxv)
        filterEgms(minv, maxv, lc);
    }
     
}
export async function filterEgms(minVal, maxVal, layersOn){
    console.log("mm:", minVal);
  const e = window.map.getZoom();
  if(e<13) return;
  if(minVal === null) minVal = -90;
  if(!maxVal) maxVal = 30;
  const entry = layersOn.find(x => x.meta.name === "egms_vector"); 
  const idx = layersOn.findIndex(x => x.meta.layerN == "egmsP"); 
  const bounds = window.map.getBounds();
  const b = bounds.pad(0.3);
  const bbox = [b.getWest(), b.getSouth(), b.getEast(), b.getNorth()].join(",");
  const filt = [minVal, maxVal];
  try{
    const res = await fetch(`${API}/layers/egms_vector?bbox=${bbox}&zoom=${e}&filter=${filt}`);
    if (!res.ok) throw new Error(`EGMS points: ${res.status}`);
    if(entry){
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