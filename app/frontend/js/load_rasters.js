export async function loadRasterLayer(layerId, colorMap, layersList, layerContainer){
    
    try{
        const layerKeys = Object.keys(layersList);
        const mapLayers = {};
        const layer = layersList[layerKeys[layerId]];
        console.log(`Reading raster ${layerId} from ${layer.url}`);
        const response = await fetch(layer.url);
        const arrayBuffer = await response.arrayBuffer();
        const tiff = await parseGeoraster(arrayBuffer);

        //normalize
        const minVal = tiff.mins[0];
        const maxVal = tiff.maxs[0];
        //console.log(minVal);

        const geoRasterLayer = new GeoRasterLayer({
            georaster: tiff,
            opacity: 0.7,
            resolution: 256, // Jak gęsto próbkować piksele (zwiększ dla jakości, zmniejsz dla wydajności)

            pixelValuesToColorFn: function(values){
                const val = values[0];
                const normalized = (val-minVal)/(maxVal-minVal);
                const color = colorMap(normalized);
                //let m = Math.max(Math.max(val));
               // console.log(m);
                return `rgb(${color.r}, ${color.g}, ${color.b})`;
            }
        });
       //console.log(typeof(geoRasterLayer.options.pixelValuesToColorFn([maxVal])));
        layersList.egms.minColor = geoRasterLayer.options.pixelValuesToColorFn([minVal]);
        layersList.egms.maxColor = geoRasterLayer.options.pixelValuesToColorFn([maxVal]);
        const canvas = tiff.toCanvas({ height: 140, width: 20 });
            console.log("canvas:", canvas);
            document.getElementById("container").appendChild(canvas);
        let x1 = geoRasterLayer.options.pixelValuesToColorFn([minVal + (maxVal-minVal)/8]);
        let x3 = geoRasterLayer.options.pixelValuesToColorFn([minVal + (maxVal-minVal)/4]);
        let x2 = geoRasterLayer.options.pixelValuesToColorFn([minVal + (maxVal-minVal)/2]);
        let x5 = geoRasterLayer.options.pixelValuesToColorFn([0]);
        let x4 = geoRasterLayer.options.pixelValuesToColorFn([maxVal - (maxVal-minVal)/6]);
        let x6 = geoRasterLayer.options.pixelValuesToColorFn([maxVal - (maxVal-minVal)/5]);
        let x7 = geoRasterLayer.options.pixelValuesToColorFn([maxVal - (maxVal-minVal)/8]);
        console.log(x5);
        mapLayers[layerId] = geoRasterLayer;
        if(layer.visible) {
            geoRasterLayer.addTo(window.map);
            
            layerContainer.addOverlay(geoRasterLayer, layer.name)
const c = document.getElementById(layer.legend_id);
const ctx = c.getContext("2d");
const grad=ctx.createLinearGradient(0,115,0,0);
grad.addColorStop(0, layer.minColor);
grad.addColorStop(0.14, x1);
grad.addColorStop(0.3, x3);
grad.addColorStop(0.45, x2);
grad.addColorStop(0.5, x5);
grad.addColorStop(0.73, x6);
grad.addColorStop(0.8, x4);
grad.addColorStop(0.9, x7);
//-87,31 27,54
grad.addColorStop(1, layer.maxColor); 
            ctx.fillStyle = grad;
ctx.fillRect(10,10,50,125);
        }

    }catch(error){
        console.error(`Error - reading raster ${layerId} has failed.`);
        console.error(error);
    }
}