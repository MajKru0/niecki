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