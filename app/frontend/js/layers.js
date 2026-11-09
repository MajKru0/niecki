function hslToRgb(h, s, l)
{
    var r, g, b;

    if (s == 0)
    {
        r = g = b = l; // achromatic
    }
    else
    {
        function hue2rgb(p, q, t)
        {
            if (t < 0) t += 1;
            if (t > 1) t -= 1;
            if (t < 1 / 6) return p + (q - p) * 6 * t;
            if (t < 1 / 2) return q;
            if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6;
            return p;
        }

        var q = l < 0.5 ? l * (1 + s) : l + s - l * s;
        var p = 2 * l - q;

        r = hue2rgb(p, q, h + 1 / 3);
        g = hue2rgb(p, q, h);
        b = hue2rgb(p, q, h - 1 / 3);
    }

    return {
        r: Math.max(0, Math.min(Math.round(r * 255), 255)),
        g: Math.max(0, Math.min(Math.round(g * 255), 255)), 
        b: Math.max(0, Math.min(Math.round(b * 255), 255)) 
    };
}

export function egmsColorMap(normalized){
    //light between 45 and 65
    //sat from 80 up

    const hue=140-(normalized*140);
    const hueDeg = hue/360;
    var light = 0.45 + normalized/5;
    var sat = light > 0.64 ? 0.8 - normalized + 0.8 : 0.8; 
    sat = sat > 0.98 ? sat + hueDeg : sat;
    light = hue < 70 ? 0.65 - normalized/5 : light;
    light = light < 0.45 ? 0.45 : light;
    light = light > 0.65 ? 0.65 : light;
    return hslToRgb(hueDeg, sat, light);
}

export function hillshadeColourMap(normalized){
    const val = Math.round(normalized*255);
    return {r: val, g: val, b:val};
}

export function addOverLay(){
    const  control = document.querySelector(".leaflet-control-layers-overlays");
    const legend = document.createElement('label');
    const bold = document.createElement('h3');
    bold.textContent = 'Personalia:';
    control.replaceWith(legend);
    legend.append(bold, control);
}

export function clcLegendColormap(code){
//zwróć mape numer, kolor, i nazwe ze switch!
//codeNum = Number(code);
    switch(code){
        case "111":
            return {code: code, color: "rgb(235 55 52)", name: 'Continuous urban fabric'};
        case "112":
            return {code: code, color: "rgb(242 16 12)", name: 'Disontinuous urban fabric'};
        case "121":
            return {code: code, color: "rgb(252 96 242)", name: 'Industrial or commercial units and public facilities'};
        case "122":
        case "123":
        case "124":
            return {code: code, color: "rgb(252 13 236)", name: 'Transport units'};
        case "131":
            return {code: code, color: "rgb(166 135 86)", name: 'Mineral extraction sites'};
        case "132":
        case "133":
            return {code: code, color: "rgb(156 101 14)", name: 'Dump and construction sites'};
        case "141":
        case "142":
            return {code: code, color: "rgb(15 212 159)", name: 'Artificial non-agricultural vegetated areas'};
        case "211":
            return {code: code, color: "rgb(252 244 0)", name: 'Arable land'};
        case "222":
            return {code: code, color: "rgb(209 212 28)", name: 'Permanent crops'};
        case "231":
            return {code: code, color: "rgb(226 230 16)", name: 'Pastures'};
        case "242":
        case "243":
            return {code: code, color: "rgb(242 225 114)", name: 'Heterogeneous agricultural areas'};
        case "311":
        case "312":
        case "313":
            return {code: code, color: "rgb(5 166 42)", name: 'Forests'};
        case "324":
            return {code: code, color: "rgb(32 247 82)", name: 'Shrubs'};
        case "333":
            return {code: code, color: "rgb(159 201 169)", name: 'Sparsely vegetated areas'};
        case "331":
            return {code: code, color: "rgb(156 186 163)", name: 'Beaches, dunes, and sand plains'};
        case "411":
            return {code: code, color: "rgb(90 122 61)", name: 'Inland marshes'};
        case "511":
        case "512":
            return {code: code, color: "rgb(62 228 250)", name: 'Inland waters'};
        default:
            return {code: code, color: "rgb(91 143 166)", name: 'Pastures'};


    }

}