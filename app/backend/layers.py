import json
from flask import Blueprint, request, jsonify, abort
from sqlalchemy import text



bp = Blueprint("layers", __name__, url_prefix="/api")
layers = {
    "forecast":       {"table": "forecastCBDG", "cols": ["wart_osiad", "min_subs_a", "max_subs_a", "mean_susb_", "std_subs_a", "point_count"], "max": 50000},
    "flooding_risk":{"table": "floodingCBDG",   "cols": ["objectid", "descript", "rb_name" ],                     "max": 50000},
    "clc":        {"table": "clc18",       "cols": ["code_18"],            "max": 50000},
    "egms_vector":       {"table": "egms_points",   "cols": ["pid", "mean_velocity", "rmse"], "max": 20000},
    # "risk_areas": {...}  # po utworzeniu tabeli z progowania
    #TODO: zapytaj claude o co cho
}