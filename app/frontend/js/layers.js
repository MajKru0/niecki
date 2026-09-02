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
    //hue: 240/0 - blue 0/1 - red
    const hue=240-(normalized*240);
    const hueDeg = hue/360;
    return hslToRgb(hueDeg, 0.8, 0.5);
}

export function hillshadeColourMap(normalized){
    const val = Math.round(normalized*255);
    return {r: val, g: val, b:val};
}