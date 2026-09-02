import * as GeoTIFF from 'https://cdn.jsdelivr.net/npm/geotiff@3.0.5/+esm';
import { egmsColorMap, hillshadeColourMap } from './layers.js';


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
    maxZoom: 18,
    minZoom: 6
});
//base map
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 19
}).addTo(map);

map.fitBounds(leafletBounds, {padding: [30, 30]});

const study_area_4326 = L.polygon(vertices_4326, {
    color: '#e74c3c',
    weight: 2,
    opacity: 0.8,
    fill: false,
    dashArray: '6, 4'
}).addTo(map);


/*
.##..........###....##....##.########.########...######.
.##.........##.##....##..##..##.......##.....##.##....##
.##........##...##....####...##.......##.....##.##......
.##.......##.....##....##....######...########...######.
.##.......#########....##....##.......##...##.........##
.##.......##.....##....##....##.......##....##..##....##
.########.##.....##....##....########.##.....##..######.
*/

const layersList = {
    egms: {
        name: 'egms mean velocity MOCK',
        type: 'raster',
        url: 'data/mocks/mock_egms.tif', 
        visible: true,
        zIndex: 100
    },
    hillshade: {
        name: 'Hillshade (DTM) MOCK',
        type: 'raster',
        url: 'data/mocks/mock_hillshade.tif', 
        visible: true,
        zIndex: 90
    }
};
const layerKeys = Object.keys(layersList);
const layerContainer = L.control.layers({}, {}).addTo(map);
const mapLayers = {};

//reading geojson TODO:

//reading rasters
async function loadRasterLayer(layerId, colorMap){
    const layer = layersList[layerKeys[layerId]];
    console.log(`Reading raster ${layerId} from ${layer.url}`);
    try{
        const response = await fetch(layer.url);
        const arrayBuffer = await response.arrayBuffer();
        const tiff = await parseGeoraster(arrayBuffer);

        //normalize
        const minVal = tiff.mins[0];
        const maxVal = tiff.maxs[0];
//TODO: add no data handlnig
        const geoRasterLayer = new GeoRasterLayer({
            georaster: tiff,
            opacity: 0.7,
            resolution: 256, // Jak gęsto próbkować piksele (zwiększ dla jakości, zmniejsz dla wydajności)

            pixelColouringFun: function(values){
                const val = values[0];
                const normalized = (val-minVal)/(maxVal-minVal);
                const color = colorMap(normalized);
                
                return `rgb(${color.r}, ${color.g}, ${color.b})`;
            }
        });


        mapLayers[layerId] = geoRasterLayer;
        if(layer.visible) {
            geoRasterLayer.addTo(map);
            console.log(`Raster ${layerId} is loaded successfulyl`);
        }

    }catch(error){
        console.error(`Error - reading raster ${layerId} has failed.`);
        console.error(error);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    //loadRasterLayer(0, egmsColorMap);
    loadRasterLayer(1, hillshadeColourMap);
    console.log('[INIT] Mapa zainicjalizowana — AOI: Central-South Silesia');
});