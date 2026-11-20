import json
from flask import Blueprint, request, jsonify, abort
from sqlalchemy import text
from db import engine

layers_rapg = Blueprint("raports", __name__)

map_context = { "status": False, "coordinates": [[], []], "layers": 
               {"forecats": False, "flooding": False, "clc": False,  "EgmsP": False, "DSA": False, "DSAf": False},
               "clcFilter": [], "egmsFilter": []}
AOI_3035 = [
    (4900610.46, 3098815.67),
    (4986435.67, 3099489.98),
    (4978291.48, 3049685.14),
    (4973279.67, 3010217.15),
    (4901773.54, 3023797.42),
]
AOI = AOI_3035 + [AOI_3035[0]] if AOI_3035[0] != AOI_3035[-1] else AOI_3035
AOI_WKT = "POLYGON((" + ", ".join(f"{x} {y}" for x, y in AOI) + "))"

@layers_rapg.get("/", strict_slashes=False)
def catalog():
    return jsonify([
        {"status_raport": v["status"], "name": k, "coordinates": v.get("coordinates", "[]"),
         }
        for k, v in map_context.items()
    ])

@layers_rapg.get("generate")
def getRaportData():
    bbox = request.args.get("bbox")
    radio = request.args.get("radio")
    clc_code = request.args.get("code")
    filterV = request.args.get("vf")
    layers = request.args.get("L")
    aoiGen = ""
    params = {}
    try:
        if(bbox):
            bbox = map(float, bbox.split(","))
        if(radio):
            radio = int(radio)
        if(radio == 0):
            minx, miny, maxx, maxy = bbox;
            params.update(minx=minx, miny=miny, maxx=maxx, maxy=maxy)
            aoiGen = (f'ST_MakeEnvelope(:minx, :miny, :maxx, :maxy, 4326)')
        if(radio == 1):
            bb=""
            for i in range(len(bbox)):
                bb = (bb+" "+bbox[i]+", ") if i%2 else (bb+bbox[i])
            bb = bb[0:-2]
            aoiGen = (f"ST_MakePolygon('LINESTRING(:bb)')")
            params.update(bb=bb)
    except ValueError:
        abort(400)



