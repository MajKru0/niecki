import json
from flask import Blueprint, request, jsonify, abort
from sqlalchemy import text
from db import engine



layers_bp = Blueprint("layers", __name__)

def q(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'

layers = {
    "forecast": {"table": "forecastCBDG", "geom_col": "geom",
                  "cols": ["wart_osiad", "min_subs_a", "max_subs_a", "mean_susb_", "std_subs_a", "point_count"],
                  "max": 50000, "label": "CBDG – subsidence forecast 2019", "geom": "line", "min_zoom": 0},
    "flooding_risk": {"table": "floodingCBDG", "geom_col": "geom",  "cols": ["objectid", "descript", "rb_name" ], "max": 50000, 
                     "label": "flooding Risk Area", "geom": "polygon", "min_zoom": 0,
                     "style": {"color": "#2b8cbe", "weight": 1, "fillOpacity": 0.3},},
    "clc": {"table": "clc18", "geom_col": "geom", "cols": ["id", "code_18"], "max": 50000, "label": "CLC 2018", "geom": "polygon"},
    "egms_vector": {"table": "egms_points", "geom_col": "geom", "cols": ["pid", "mean_velocity", "rmse"], "max": 20000,
                    "label": "EGMS - points", "geom": "point", "min_zoom": 25,}
}

@layers_bp.get("/", strict_slashes=False)
def catalog():
    return jsonify([
        {"name": k, "label": v["label"], "geom": v["geom"],
         "min_zoom": v.get("min_zoom", 0), "style": v.get("style", {})}
        for k, v in layers.items()
    ])

@layers_bp.get("/<name>")
def get_layer(name):
    cfg = layers.get(name) or abort(404)
    try:
        minx, miny, maxx, maxy = map(float, request.args["bbox"].split(","))
    except (KeyError, ValueError):
        abort(400, "bbox=minx,miny,maxx,maxy (EPSG:3035, metry)")

    table = q(cfg["table"])
    gcol = q(cfg.get("geom_col", "geom"))
    select_cols = ", ".join([q(c) for c in cfg["cols"]] + [f"{gcol} AS geom"])

    sql = text(f"""
        SELECT jsonb_build_object(
            'type', 'FeatureCollection',
            'features', COALESCE(jsonb_agg(f), '[]'::jsonb)
        )
        FROM (
            SELECT jsonb_build_object(
                'type', 'Feature',
                'geometry', ST_AsGeoJSON(t.geom, 1, 0)::jsonb,
                'properties', to_jsonb(t) - 'geom'
            ) AS f
            FROM (
                SELECT {select_cols} FROM {table}
                WHERE {gcol} && ST_MakeEnvelope(:minx, :miny, :maxx, :maxy, 3035)
                LIMIT :lim
            ) t
        ) s
    """)
    with engine.connect() as con:
        data = con.execute(sql, dict(minx=minx, miny=miny, maxx=maxx, maxy=maxy,
                                     lim=cfg["max"])).scalar()
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