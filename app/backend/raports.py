import math
from datetime import datetime
from io import BytesIO

import pandas as pd
from flask import Blueprint, request, jsonify, abort, send_file, current_app
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from db import engine
from report_pdf import build_report_pdf

layers_rapg = Blueprint("raports", __name__)

INPUT_SRID = 4326   # SRID of bbox / polygon sent by the frontend

map_context = {"status": False,
               "forecast": False, "flooding": False, "clc": False, "egmsP": False, "dsa": False, "dsaf": False}

tables = {
    "forecast": {"table": "forecastCBDG", "geom_col": "geom",
                 "cols": ["wart_osiad", "min_subs_a", "max_subs_a", "mean_subs_", "std_subs_a", "point_coun"],
                 "geom": "line"},
    "flooding": {"table": "floodingCBDG", "geom_col": "geom",
                 "cols": ["objectid", "data", "descript", "rb_name"], "geom": "polygon"},
    "egmsP": {"table": "egms_points_stats", "geom_col": "geometry",
              "cols": ["pid", "ID", "code_18", "mean_velocity", "rmse", "E", "N",
                       "acceleration", "seasonality", "Area_Ha"],
              "geom": "point", "value_col": "mean_velocity", "code_col": "code_18"},
    "dsa": {"table": "dsa", "geom_col": "geom", "cols": ["id", "area_m2"], "geom": "line"},
    "dsaf": {"table": "niecki_filled", "geom_col": "geom", "cols": ["id", "area_m2"], "geom": "line"},
    "clc": {"table": "clc18", "geom_col": "geom", "cols": ["id", "code_18", "area_ha"],
            "geom": "polygon", "code_col": "code_18", "clip_area": True},
}

AOI_3035 = [
    (4900610.46, 3098815.67),
    (4986435.67, 3099489.98),
    (4978291.48, 3049685.14),
    (4973279.67, 3010217.15),
    (4901773.54, 3023797.42),
]
AOI = AOI_3035 + [AOI_3035[0]] if AOI_3035[0] != AOI_3035[-1] else AOI_3035
AOI_WKT = "POLYGON((" + ", ".join(f"{x} {y}" for x, y in AOI) + "))"


def qi(name):
    """Always quote an identifier, exact case as written in `tables`."""
    return '"' + name.replace('"', '""') + '"'


@layers_rapg.get("/", strict_slashes=False)
def catalog():
    return jsonify([{"status_raport": v, "name": k, "coordinates": "[]"} for k, v in map_context.items()])


# ---------- helpers ----------
def _floats(raw, name):
    try:
        vals = [float(v) for v in raw.split(",")]
    except ValueError:
        abort(400, f"{name}: values must be numbers separated by commas")
    if not all(math.isfinite(v) for v in vals):
        abort(400, f"{name}: invalid values")
    return vals


def build_aoi(radio, coords):
    """aoiGen in EPSG:4326 (transformed to each table's SRID in build_query) + its parameters."""
    if radio == 0:
        if len(coords) != 4:
            abort(400, "radio=0 requires bbox=minx,miny,maxx,maxy (EPSG:4326)")
        minx, miny, maxx, maxy = coords
        raw = f"ST_MakeEnvelope(:minx, :miny, :maxx, :maxy, {INPUT_SRID})"
        params = dict(minx=minx, miny=miny, maxx=maxx, maxy=maxy)
    elif radio == 1:
        if len(coords) < 6 or len(coords) % 2:
            abort(400, "radio=1 requires at least 3 x,y pairs")
        pts = list(zip(coords[0::2], coords[1::2]))
        if pts[0] != pts[-1]:
            pts.append(pts[0])                                   # close the ring
        wkt = "POLYGON((" + ", ".join(f"{x} {y}" for x, y in pts) + "))"
        raw = f"ST_GeomFromText(:aoi_wkt, {INPUT_SRID})"
        params = {"aoi_wkt": wkt}
    else:
        abort(400, "radio must be 0 (bbox) or 1 (polygon)")
    return f"ST_MakeValid({raw})", params


def parse_clc_codes(raw):
    """Empty or containing '100' -> [] (no filtering, all code_18 classes)."""
    codes = [c.strip() for c in (raw or "").split(",") if c.strip()]
    if not all(c.isdigit() for c in codes):
        abort(400, "code: only numeric CLC codes separated by commas")
    if not codes or "100" in codes:
        return []
    return codes


def load_srids(conn):
    """{(table, geometry column): srid} read from PostGIS."""
    rows = conn.execute(text(
        "SELECT f_table_name, f_geometry_column, srid FROM geometry_columns "
        "WHERE f_table_schema = ANY(current_schemas(false))"
    )).all()
    return {(r[0], r[1]): r[2] for r in rows}


def build_query(cfg, aoi_4326, params, clc_codes, srid):
    """One independent query per table: no joins between tables."""
    geom = qi(cfg["geom_col"])
    aoi_gen = aoi_4326 if srid == INPUT_SRID else f"ST_Transform({aoi_4326}, {int(srid)})"
    select = [qi(c) for c in cfg["cols"]]
    where = [f"ST_Intersects({geom}, {aoi_gen})"]               # inside OR intersecting aoiGen
    extra = {}

    if cfg.get("clip_area") and clc_codes:                      # part of the polygon inside aoiGen [ha]
        select.append(f"ST_Area(ST_Intersection(ST_MakeValid({geom}), {aoi_gen})) / 10000.0 AS area_in_aoi_ha")
    if clc_codes and cfg.get("code_col"):
        where.append(f"CAST({qi(cfg['code_col'])} AS TEXT) = ANY(:clc_codes)")   # WHERE code IN (...)
        extra["clc_codes"] = clc_codes
    if cfg.get("value_col"):
        where.append(f"{qi(cfg['value_col'])} BETWEEN :minv AND :maxv")

    sql = f"SELECT {', '.join(select)} FROM {qi(cfg['table'])} WHERE {' AND '.join(where)}"
    used = {k: v for k, v in {**params, **extra}.items() if f":{k}" in sql}
    return sql, used


# ---------- endpoint ----------
@layers_rapg.get("/generate")
def getRaportData():
    layers_raw = request.args.get("L")
    bbox_raw = request.args.get("bbox")
    radio_raw = request.args.get("radio")
    filter_raw = request.args.get("vf")
    clc_codes = parse_clc_codes(request.args.get("code"))

    if not layers_raw:
        abort(400, "Missing parameter L")
    layers = [s.strip() for s in layers_raw.split(",") if s.strip()]
    unknown = [k for k in layers if k not in tables]
    if unknown:
        abort(400, f"Unknown layers: {', '.join(unknown)}")
    active = {k: (k in layers) for k in tables}      # per-request equivalent of map_context (True = generate)

    if radio_raw is None or not bbox_raw:
        abort(400, "radio and bbox are required")
    try:
        radio = int(radio_raw)
    except ValueError:
        abort(400, "radio must be an integer")
    coords = _floats(bbox_raw, "bbox")
    aoi_gen, aoi_params = build_aoi(radio, coords)

    fv = _floats(filter_raw, "vf") if filter_raw else [-90.0, 30.0]
    if len(fv) != 2:
        abort(400, "vf=min,max")
    params = {**aoi_params, "minv": fv[0], "maxv": fv[1]}

    ############# QUERIES ##################
    data = {}
    clc_totals = None        # area [ha] per level-1 CLC class in the WHOLE clc18 table
    try:
        with engine.connect() as conn:
            srids = load_srids(conn)
            for key, cfg in tables.items():
                if not active[key]:
                    continue
                srid = srids.get((cfg["table"], cfg["geom_col"]))
                if not srid:
                    abort(500, f"Layer '{key}': column {cfg['table']}.{cfg['geom_col']} not found in "
                               f"geometry_columns or has SRID 0 - check table/column name and SRID")
                sql, q_params = build_query(cfg, aoi_gen, params, clc_codes, srid)
                try:
                    rows = conn.execute(text(sql), q_params).mappings().all()
                except SQLAlchemyError as e:
                    current_app.logger.exception("Query error in layer %s", key)
                    abort(500, f"Layer '{key}': {getattr(e, 'orig', e)}")   # DEBUG: remove in production
                cols = cfg["cols"] + (["area_in_aoi_ha"] if cfg.get("clip_area") and clc_codes else [])
                data[key] = pd.DataFrame([dict(r) for r in rows], columns=cols)

            if active["clc"] and clc_codes:      # only needed for the second pie chart
                cfg = tables["clc"]
                try:
                    rows = conn.execute(text(
                        f"SELECT LEFT(CAST({qi(cfg['code_col'])} AS TEXT), 1) AS lvl1, "
                        f"SUM({qi('area_ha')}) AS area_ha "
                        f"FROM {qi(cfg['table'])} GROUP BY 1"
                    )).all()
                except SQLAlchemyError as e:
                    current_app.logger.exception("Query error (clc totals)")
                    abort(500, f"Layer 'clc' (totals): {getattr(e, 'orig', e)}")   # DEBUG: remove in production
                clc_totals = {str(r[0]): float(r[1] or 0) for r in rows}
    except SQLAlchemyError:
        current_app.logger.exception("Connection error in /generate")
        abort(500, "Database connection error")

    meta = {
        "mode": "bounding box" if radio == 0 else "polygon",
        "coords": coords,
        "value_filter": fv,
        "clc_codes": clc_codes,      # [] = no filtering
        "clc_totals": clc_totals,    # {"1": ha, "2": ha, ...} or None
        "crossings": {},             # no cross-table analysis
    }
    pdf_bytes = build_report_pdf(data, meta)

    return send_file(BytesIO(pdf_bytes), mimetype="application/pdf", as_attachment=True,
                     download_name=f"report_{datetime.now():%Y%m%d_%H%M}.pdf")