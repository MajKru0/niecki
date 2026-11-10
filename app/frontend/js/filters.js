import { getEgmsP, resetGeoJ} from './load_vectors.js';
import { clcLegendColormap } from './layers.js';
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
export async function filterCLC(layersOn, code){
  try{
    const entry = layersOn.find(x => x.meta.name == "clc");
    console.log("CLC FILTER");
    console.log(layersOn)
    console.log(entry);
    if(entry.visible){
      console.log('xxxxxxxxxxx');
         await resetGeoJ(entry, layersOn, "clc");
    }
    const obj = clcLegendColormap(code);
    const arr = obj.additional ?? [code];
    let arrStr = "";
    arr.forEach((el) => arrStr = arrStr+"'"+el+"',");
    let fin = arrStr.slice(0, -1);
    if(!code) fin = "";
    console.log(fin);
    const res = await fetch(`${API}/layers/${entry.meta.name}?ccode=${fin}`);
    if (!res.ok) throw new Error(`${entry.meta.name}: ${res.status}`);
    entry.group[entry.meta.layerN].addData(await res.json());
    entry.visible = true;
    console.log(entry);
  }catch (e){
  console.error(e);
}
  

}
export async function resetFilter(typ, layOn){
  //przycisk reset filter lub clc ALL
    const egmsE = layOn.find(x => x.meta.name == "egms_vector"); 
    const clcE = layOn.find(x => x.meta.name == "clc");
    if(!clcE.visible && !egmsE.visible) return;
    if(typ && egmsE && egmsE.visible){
      await filterEgms(null, null, layOn)
   }
  
  await filterCLC(layOn, 0);

}