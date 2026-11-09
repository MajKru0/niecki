import json
from flask import Blueprint, request, jsonify, abort
from sqlalchemy import text
from db import engine



layers_bp = Blueprint("layers", __name__)

def q(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'

layers = {
    "forecast": {"table": "forecastCBDG", "geom_col": "geom",
                  "cols": ["wart_osiad", "min_subs_a", "max_subs_a", "mean_subs_", "std_subs_a", "point_coun"],
                  "max": 50000, "label": "CBDG – subsidence forecast 2019", "geom": "line", "min_zoom": 0, "layerN": "forecast"},
    "flooding_risk": {"table": "floodingCBDG", "geom_col": "geom",  "cols": ["objectid", "descript", "rb_name" ], "max": 50000, 
                     "label": "flooding Risk Area", "layerN": "flooding", "geom": "polygon", "min_zoom": 11, "visible": False,
                     "style": {"color": "#2b8cbe", "weight": 1, "fillOpacity": 0.3}},
    "clc": {"table": "clc18", "geom_col": "geom", "cols": ["id", "code_18"], "max": 50000, "label": "CLC 2018", "geom": "polygon", "min_zoom": 0, "layerN": "clc"},
    "egms_vector": {"table": "egms_points_stats", "geom_col": "geometry", "cols": ["pid", "mean_velocity", "rmse", "code_18", "E", "N"], "max": 20000,
                    "label": "EGMS - points", "geom": "point", "min_zoom": 13, "visible": False, "layerN": "egmsP"}
}
#TODO: add filters to egms_vector np pobierz współrzędne aktualnego widoku, żeby tylko w powiekszeniu i w danym widoku się ładowały

AOI_3035 = [
    (4900610.46, 3098815.67),
    (4986435.67, 3099489.98),
    (4978291.48, 3049685.14),
    (4973279.67, 3010217.15),
    (4901773.54, 3023797.42),
]
AOI = AOI_3035 + [AOI_3035[0]] if AOI_3035[0] != AOI_3035[-1] else AOI_3035
AOI_WKT = "POLYGON((" + ", ".join(f"{x} {y}" for x, y in AOI) + "))"

@layers_bp.get("/", strict_slashes=False)
def catalog():
    return jsonify([
        {"layerN": v.get("layerN", "e"), "name": k, "label": v["label"], "geom": v["geom"],
         "min_zoom": v.get("min_zoom", 0), "style": v.get("style", {})}
        for k, v in layers.items()
    ])

@layers_bp.get("egms_vector")
def get_huge_layers():
     zoom = int(request.args.get("zoom"))
     if(zoom < 13):
        return jsonify([{"features": {"geometry": {}}}]);
     cfg = layers.get('egms_vector') or abort(401)
     bbox = request.args.get("bbox")
     where = ""
     params = {"aoi": AOI_WKT}
     filter = request.args.get("filter")
     if(filter):
         minV, maxV = map(float, filter.split(","))
         where =(f'AND mean_velocity BETWEEN :minVel AND :maxVel');
         params.update(minVel = minV, maxVel=maxV);
     try:
        minx, miny, maxx, maxy = map(float, bbox.split(","))
     except ValueError:
        abort(400, "bbox=minx,miny,maxx,maxy (EPSG:4326, stopnie)")
     params.update(minx=minx, miny=miny, maxx=maxx, maxy=maxy)
     table = q(cfg["table"])
     gcol = q(cfg.get("geom_col", "geom"))
     select_cols = ", ".join([q(c) for c in cfg["cols"]] + [f"{gcol} AS geom"])
     sql = text(f"""
        SELECT jsonb_build_object(
            'type', 'FeatureCollection',
            'features', 
            COALESCE(jsonb_agg(f), '[]'::jsonb)
        )
        FROM (
            SELECT jsonb_build_object(
                'type', 'Feature',
                'geometry', ST_AsGeoJSON(ST_Transform(t.geom, 4326), 6)::jsonb,
                'properties', to_jsonb(t) - 'geom'
            ) AS f
            FROM (
                SELECT {select_cols} FROM {table}
                WHERE {gcol} &&  ST_Transform(
                 ST_MakeEnvelope(:minx, :miny, :maxx, :maxy, 4326), 3035)
                 AND ST_Intersects({gcol}, ST_GeomFromText(:aoi, 3035))
                 {where}
            ) t
        ) s
    """)
     with engine.connect() as con:
        data = con.execute(sql,params).scalar()
     return jsonify(data)


@layers_bp.get("/<name>")
def get_layer(name):
    cfg = layers.get(name) or abort(402)
    conditions = []

    params = {}
    where = ""
    bbox = request.args.get("bbox")
    if bbox:
        try:
            minx, miny, maxx, maxy = map(float, bbox.split(","))
        except ValueError:
            abort(400, "bbox=minx,miny,maxx,maxy (EPSG:4326, stopnie)")
        params.update(minx=minx, miny=miny, maxx=maxx, maxy=maxy)

    table = q(cfg["table"])
    gcol = q(cfg.get("geom_col", "geom"))
    
    select_cols = ", ".join([q(c) for c in cfg["cols"]] + [f"{gcol} AS geom"])
    if name == "egms_vector":
        conditions.append(f"ST_Intersects({gcol}, ST_GeomFromText(:aoi, 3035))")
        params["aoi"] = AOI_WKT
    if bbox:
        where = (f"WHERE {gcol} && ST_Transform("
                 f"ST_MakeEnvelope(:minx, :miny, :maxx, :maxy, 4326), 3035)")
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    sql = text(f"""
        SELECT jsonb_build_object(
            'type', 'FeatureCollection',
            'features', COALESCE(jsonb_agg(f), '[]'::jsonb)
        )
        FROM (
            SELECT jsonb_build_object(
                'type', 'Feature',
                'geometry', ST_AsGeoJSON(ST_Transform(t.geom, 4326), 6)::jsonb,
                'properties', to_jsonb(t) - 'geom'
            ) AS f
            FROM (
                SELECT {select_cols} FROM {table}
                {where}

            ) t
        ) s
    """)
    with engine.connect() as con:
        data = con.execute(sql, params).scalar()
    return jsonify(data)

'''
# Szereg czasowy punktu EGMS -> /api/layers/egms/<pid>/timeseries
@layers_bp.get("/egms/<int:pid>/timeseries")
def egms_timeseries(pid):
    # TODO: dopasuj nazwy kolumn do swojej tabeli (sprawdź: egms_timeseries)
    sql = text("SELECT date, displacement FROM egms_timeseries WHERE pid = :pid ORDER BY date")
    with engine.connect() as con:
        rows = con.execute(sql, {"pid": pid}).all()
    return jsonify([{"date": r[0].isoformat(), "value": r[1]} for r in rows])
'''