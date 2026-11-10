import * as GeoTIFF from 'https://cdn.jsdelivr.net/npm/geotiff@3.0.5/+esm';
import { egmsColorMap, hillshadeColourMap, getCLC } from './layers.js';
import { initVectorLayers, getEgmsP } from './load_vectors.js';
import { loadRasterLayer } from './load_rasters.js';
import { filterContext, filterCLC, resetFilter } from './filters.js';

const STUDY_AREA_EXTENT_3035 = {
    north: 3100504.8686,
    south: 2999266.3481,
    west: 4899342.9771,
    east: 5000581.4977
};
const vertices_3035 = [
    [4900610.46, 3098815.67],   
    [4986435.67, 3099489.98],   
    [4978291.48, 3049685.14],   
    [4973279.67, 3010217.15],   
    [4901773.54, 3023797.42]  
];
const form = document.getElementById('filters');
/*
.########..########...#######........##.########..######..########.####..#######..##....##
.##.....##.##.....##.##.....##.......##.##.......##....##....##.....##..##.....##.###...##
.##.....##.##.....##.##.....##.......##.##.......##..........##.....##..##.....##.####..##
.########..########..##.....##.......##.######...##..........##.....##..##.....##.##.##.##
.##........##...##...##.....##.##....##.##.......##..........##.....##..##.....##.##..####
.##........##....##..##.....##.##....##.##.......##....##....##.....##..##.....##.##...###
.##........##.....##..#######...######..########..######.....##....####..#######..##....##
*/

//need to project coordinets for leaflet (wgs84)
proj4.defs("EPSG:3035",
    "+proj=laea +lat_0=52 +lon_0=10 +x_0=4321000 +y_0=3210000 +ellps=GRS80 +units=m +no_defs");
proj4.defs("EPSG:4326",
    "+proj=longlat +datum=WGS84 +no_defs");
const vertices_4326 = vertices_3035.map(([x, y]) => {
    const [lon, lat] = proj4("EPSG:3035", "EPSG:4326", [x, y]);
    return [lat, lon];
});
const lats = vertices_4326.map(c => c[0]);
const lons = vertices_4326.map(c => c[1]);
const leafletBounds = [
    [Math.min(...lats), Math.min(...lons)],  // SW
    [Math.max(...lats), Math.max(...lons)]   // NE
];
console.log("Bounds 3035: ", STUDY_AREA_EXTENT_3035);
console.log("Bounds 4326: ", leafletBounds);
console.log("Vertices 3035: ", vertices_3035);
console.log("vertices 4326: ", vertices_4326);

/*
.##.....##....###....########.................####.##....##.####.########
.###...###...##.##...##.....##.................##..###...##..##.....##...
.####.####..##...##..##.....##.................##..####..##..##.....##...
.##.###.##.##.....##.########..................##..##.##.##..##.....##...
.##.....##.#########.##........................##..##..####..##.....##...
.##.....##.##.....##.##........................##..##...###..##.....##...
.##.....##.##.....##.##.......................####.##....##.####....##...
*/
const map = L.map('map', {
    //crs: crs3035,
    maxZoom: 18,
    minZoom: 0
});
window.map = map;
//base map
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 19
}).addTo(map);

map.fitBounds(leafletBounds, {padding: [30, 30]});


/*
.##..........###....##....##.########.########...######.
.##.........##.##....##..##..##.......##.....##.##....##
.##........##...##....####...##.......##.....##.##......
.##.......##.....##....##....######...########...######.
.##.......#########....##....##.......##...##.........##
.##.......##.....##....##....##.......##....##..##....##
.########.##.....##....##....########.##.....##..######.
*/
const vectorLayersData = [];
const layersList = {
    egms: {
        name: 'egms mean velocity MOCK',
        type: 'raster',
        url: 'data/mocks/mock_egms.tif', 
        visible: true,
        zIndex: 100,
        minColor: "",
        maxColor: "",
        legend_id: 'egms_legend'
    },
    hillshade: {
        name: 'Hillshade (DTM) MOCK',
        type: 'raster',
        url: 'data/mocks/mock_hillshade.tif', 
        visible: true,
        zIndex: 90,
        minColor: "",
        maxColor: "",
        legend_id: 'hillshade_legend'

    }
};

const study_area_4326 = L.polygon(vertices_4326, {
    color: '#e74c3c',
    weight: 2,
    opacity: 0.8,
    fill: false,
    dashArray: '6, 4'
}).addTo(map);

const layerContainer = L.control.layers({}, {}).addTo(map);
layerContainer.addOverlay(study_area_4326, "AOI bounds");


//reading rasters

async function over(nam){
    const over = document.querySelector(nam);
    //const fieldset = document.createElement('fieldset');
    const legend = document.createElement('label');
    const bold = document.createElement('h3');
    bold.textContent = 'Personalia:';
    over.replaceWith(legend);
    legend.append(bold, over);
}

map.on("zoom", function() {
    console.log(map.getZoom(), "zoom");
    //const idx = layerContainer._layers.findIndex(x => x.name == "EGMS - points");
    //console.log(layerContainer._layerControlInputs[idx].checked);
});
map.on("moveend", function(){
    console.log(vectorLayersData);
    //filterContext(map, map, layerContainer);
    const z = map.getZoom();
    if (z > 13){
        filterContext(minVel, maxVel, vectorLayersData, isFilterOn);
    }
    const idx = vectorLayersData.findIndex(x => x.meta.label == "EGMS - points");
    console.log(idx);

    if(z <= 13 && vectorLayersData.length > 0 && idx > -1){
        console.log("idx:", idx);
        vectorLayersData[idx].visible = false;
        const layer = vectorLayersData[idx].group.egmsP;
        console.log(layer);
        layer.clearLayers();

    }
    });
document.addEventListener('DOMContentLoaded', () => {
    getCLC();
    loadRasterLayer(0, egmsColorMap, layersList, layerContainer);
   // loadRasterLayer(1, hillshadeColourMap);
    initVectorLayers(layerContainer, vectorLayersData).catch(console.error);
    over(".leaflet-control-layers-overlays");
    console.log('[INIT] Mapa zainicjalizowana — AOI: Central-South Silesia');
    console.log("zoom:", map.getZoom());
    console.log(layerContainer);
});
let isFilterOn = false;
let minVel = null;
let maxVel = null;
form.addEventListener('submit', (event) => {
    event.preventDefault();
    ////////////EGMS/////////////
    const minVelVal = form.elements['filter-velocity-min'];
    const maxVelVal = form.elements['filter-velocity-max'];
    var maxv = parseFloat(maxVelVal.value);
    var minv = parseFloat(minVelVal.value);
    if(minv >= maxv){
        maxVelVal.value = minv;
        minVelVal.value = maxv;
       var tmp = maxv;
       maxv = minv;
       minv = tmp;
    }
    isFilterOn = true;
    minVel = minv;
    maxVel = maxv;
    console.log(minv);
    console.log(maxv);

   /////////CLC/////////
    //TODO: dodać filtr clc
    const selected = form.elements['filter-clc'].value;
    console.log(selected);
    if(selected != "100"){
        filterCLC(vectorLayersData, selected);
    }else{
        resetFilter(false, vectorLayersData);
    }

    filterContext(minv, maxv, vectorLayersData, isFilterOn);

    //event.preventDefault();
});
form.addEventListener('reset', (event) => {
    event.preventDefault()
    isFilterOn = false;
    resetFilter(true, vectorLayersData);
    form.elements['filter-velocity-min'].value = -90;
    form.elements['filter-velocity-max'].value = 30;
    form.elements['filter-clc'].value = 100;
    filterContext(null, null, vectorLayersData, isFilterOn);
});
