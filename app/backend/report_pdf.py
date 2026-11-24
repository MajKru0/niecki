from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

import matplotlib
matplotlib.use("Agg")                       # no GUI window on the server
from matplotlib.figure import Figure
from matplotlib.patches import Patch

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# ---------- fonts (DejaVu in ./fonts, falls back to Helvetica) ----------
FONT_DIR = Path(__file__).parent / "fonts"
try:
    pdfmetrics.registerFont(TTFont("DejaVu", str(FONT_DIR / "DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont("DejaVu-Bold", str(FONT_DIR / "DejaVuSans-Bold.ttf")))
    pdfmetrics.registerFontFamily("DejaVu", normal="DejaVu", bold="DejaVu-Bold")
    FONT, FONT_B = "DejaVu", "DejaVu-Bold"
except Exception:
    FONT, FONT_B = "Helvetica", "Helvetica-Bold"

STYLES = {
    "title": ParagraphStyle("title", fontName=FONT_B, fontSize=20, leading=24, spaceAfter=6),
    "h1": ParagraphStyle("h1", fontName=FONT_B, fontSize=14, leading=18, spaceBefore=14, spaceAfter=6),
    "h2": ParagraphStyle("h2", fontName=FONT_B, fontSize=10.5, leading=14, spaceBefore=8, spaceAfter=4),
    "body": ParagraphStyle("body", fontName=FONT, fontSize=9.5, leading=13, spaceAfter=4),
    "small": ParagraphStyle("small", fontName=FONT, fontSize=8, leading=10, textColor=colors.grey, spaceAfter=6),
    "cell": ParagraphStyle("cell", fontName=FONT, fontSize=8, leading=10),
}

LAYER_TITLES = {
    "forecast": "Subsidence forecast",
    "flooding": "Flooded areas",
    "egmsP": "EGMS points",
    "dsa": "Subsidence troughs variant 1",
    "dsaf": "Subsidence troughs variant 2",
    "clc": "CORINE Land Cover 2018",
}

# CORINE Land Cover legend (level 3)
CLC_LEGEND = {
    "111": "Continuous urban fabric", "112": "Discontinuous urban fabric",
    "121": "Industrial or commercial units", "122": "Road and rail networks and associated land",
    "123": "Port areas", "124": "Airports",
    "131": "Mineral extraction sites", "132": "Dump sites", "133": "Construction sites",
    "141": "Green urban areas", "142": "Sport and leisure facilities",
    "211": "Non-irrigated arable land", "212": "Permanently irrigated land", "213": "Rice fields",
    "221": "Vineyards", "222": "Fruit trees and berry plantations", "223": "Olive groves",
    "231": "Pastures",
    "241": "Annual crops associated with permanent crops", "242": "Complex cultivation patterns",
    "243": "Land principally occupied by agriculture, with significant areas of natural vegetation",
    "244": "Agro-forestry areas",
    "311": "Broad-leaved forest", "312": "Coniferous forest", "313": "Mixed forest",
    "321": "Natural grasslands", "322": "Moors and heathland", "323": "Sclerophyllous vegetation",
    "324": "Transitional woodland-shrub",
    "331": "Beaches, dunes, sands", "332": "Bare rocks", "333": "Sparsely vegetated areas",
    "334": "Burnt areas", "335": "Glaciers and perpetual snow",
    "411": "Inland marshes", "412": "Peat bogs",
    "421": "Salt marshes", "422": "Salines", "423": "Intertidal flats",
    "511": "Water courses", "512": "Water bodies",
    "521": "Coastal lagoons", "522": "Estuaries", "523": "Sea and ocean",
}

# CLC level 1 classes: (first digit of the code, label, pie colour)
CLC_LEVEL1 = [
    ("1", "Artificial areas", "red"),
    ("2", "Agricultural areas", "yellow"),
    ("3", "Forest and semi-natural areas", "green"),
    ("4", "Wetlands", "orange"),
    ("5", "Water bodies", "blue"),
]

SKIP_STATS = {"id", "ID", "objectid", "pid", "E", "N", "Area_Ha"}   # identifiers / not meaningful per point
code_COLS = {"code_18", "code_18"}
MAX_SCATTER_POINTS = 200_000        # EGMS map: random sample above this many points


# ---------- small helpers ----------
def norm_code(code):
    """111, 111.0, '111' -> '111'."""
    try:
        return str(int(float(code)))
    except (TypeError, ValueError):
        return str(code)


def clc_label(code):
    return CLC_LEGEND.get(norm_code(code), "Unknown class")


def clc_names(codes):
    return ", ".join(f"{norm_code(c)} ({clc_label(c)})" for c in codes)


def fmt(v, digits=2):
    if v is None or pd.isna(v):
        return "-"
    return f"{float(v):,.{digits}f}"


def to_num(s):
    return pd.to_numeric(s, errors="coerce")   # also converts Decimal from the database


def p(s):
    return Paragraph(s, STYLES["body"])


def h2(s):
    return Paragraph(s, STYLES["h2"])


def cell(s):
    return Paragraph(escape(str(s)), STYLES["cell"])   # escape: DB values may contain & or <


def styled_table(rows, col_widths=None):
    t = Table(rows, colWidths=col_widths, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), FONT),
        ("FONTNAME", (0, 0), (-1, 0), FONT_B),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f3a5f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f5f9")]),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#c8d0da")),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


def table_block(title, table):
    return [h2(title), table, Spacer(1, 0.2 * cm)]


def numeric_columns(df, skip=()):
    out = {}
    for c in df.columns:
        if c in SKIP_STATS or c in code_COLS or c in skip:
            continue
        if pd.api.types.is_datetime64_any_dtype(df[c]):
            continue
        s = to_num(df[c])
        if s.notna().any() and s.notna().mean() > 0.9:
            out[c] = s
    return out


def numeric_stats_table(nums):
    rows = [["Column", "N", "Mean", "Std. dev.", "Min", "Median", "Max"]]
    for c, s in nums.items():
        rows.append([c, fmt(s.count(), 0), fmt(s.mean()), fmt(s.std()),
                     fmt(s.min()), fmt(s.median()), fmt(s.max())])
    return styled_table(rows)


def category_table(df, col, top=10):
    counts = df[col].astype(str).value_counts().head(top)
    rows = [[col, "Count", "Share [%]"]]
    rows += [[cell(k), fmt(v, 0), fmt(100 * v / len(df), 1)] for k, v in counts.items()]
    return styled_table(rows, col_widths=[9 * cm, 3 * cm, 3 * cm])


def generic_tables(df, exclude=()):
    """Descriptive statistics for numeric columns + top-10 distributions for categorical ones."""
    items = []
    nums = numeric_columns(df, exclude)
    if nums:
        items += table_block("Descriptive statistics", numeric_stats_table(nums))
    for c in df.columns:
        if c in SKIP_STATS or c in code_COLS or c in exclude or c in nums:
            continue
        if pd.api.types.is_datetime64_any_dtype(df[c]):
            continue
        if 0 < df[c].nunique(dropna=True) <= 30:
            items += table_block(f"Distribution of '{c}' (top 10)", category_table(df, c))
    return items


def fig_to_image(fig, width_cm=17):
    """Matplotlib figure -> reportlab Image scaled to the given width."""
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    buf.seek(0)
    img = Image(buf)
    ratio = img.imageHeight / img.imageWidth
    img.drawWidth = width_cm * cm
    img.drawHeight = width_cm * cm * ratio
    return img


# ---------- EGMS point density (done in pandas) ----------
def point_density(df):
    g = (df.dropna(subset=["code_18", "ID"])
           .assign(code_18=lambda x: x["code_18"].map(norm_code),
                   Area_Ha=lambda x: to_num(x["Area_Ha"]))
           .groupby(["code_18", "ID"])
           .agg(area=("Area_Ha", "max"), num=("pid", "count"))     # each polygon counted once
           .reset_index())
    d = (g.groupby("code_18")
          .agg(sum_area_ha=("area", "sum"), points=("num", "sum"))
          .reset_index())
    d["density"] = d["points"] / d["sum_area_ha"].where(d["sum_area_ha"] > 0)
    return d.sort_values("code_18")


# ---------- charts ----------
def density_figure(d):
    """2x2 charts built from point_density() output."""
    result = d.rename(columns={"code_18": "clc_code"}).copy()
    result["clc_code"] = result["clc_code"].astype(str)          # categorical x axis
    result["percentage"] = result["points"] / result["points"].sum() * 100

    fig = Figure(figsize=(14, 10))
    (ax1, ax2), (ax3, ax4) = fig.subplots(2, 2)
    ax4_1 = ax4.twinx()

    # density plot
    result.sort_values("density", ascending=True).plot(
        x="clc_code", y="density", kind="bar", ax=ax1, color="steelblue", legend=False)
    ax1.grid(axis="y", alpha=0.3)
    ax1.set_ylabel("Density pt/ha")
    ax1.set_xlabel("CLC Code")
    ax1.set_title("Density per CLC class (pt/ha)")

    # points per class
    result.sort_values("points", ascending=True).plot(
        x="clc_code", y="points", kind="bar", ax=ax2, color="coral", legend=False)
    ax2.grid(axis="y", alpha=0.3)
    ax2.set_ylabel("Points count")
    ax2.set_xlabel("CLC Code")
    ax2.set_title("EGMS points count per CLC class")

    # point distribution per class [%], top 10
    result.nlargest(10, "points").plot(
        x="clc_code", y="percentage", kind="barh", ax=ax3, color="lightgreen", legend=False)
    ax3.grid(axis="x", alpha=0.3)
    ax3.set_xlabel("Percentage")
    ax3.set_ylabel("CLC Code")
    ax3.set_title("Top 10 classes by share of points")

    # area vs point count, top 10 classes by area
    draw = result.nlargest(10, "sum_area_ha")
    ax4.bar(draw["clc_code"], draw["sum_area_ha"], width=0.4, color="blue", alpha=0.7)
    ax4_1.plot(draw["clc_code"], draw["points"], color="red", marker="o", label="point count")
    ax4.grid(alpha=0.3)
    ax4.set_ylabel("Area [ha]")
    ax4.set_xlabel("CLC Code")
    ax4_1.set_ylabel("Points")
    ax4_1.legend(loc="upper right")
    ax4.set_title("Top 10 largest classes: area vs points count")
    for lbl in ax4.get_xticklabels():
        lbl.set_rotation(45)
        lbl.set_ha("right")

    fig.tight_layout()
    return fig


def egms_histograms_figure(df):
    """Histograms of mean velocity and RMSE."""
    fig = Figure(figsize=(12, 4))
    ax0, ax1 = fig.subplots(1, 2)
    for ax, col, title in ((ax0, "mean_velocity", "mean velocity"), (ax1, "rmse", "rmse")):
        vals = to_num(df[col]).dropna()
        if len(vals):
            ax.hist(vals, bins=50)
        else:
            ax.text(0.5, 0.5, "no data", ha="center", va="center", transform=ax.transAxes)
        ax.set_title(title)
        ax.grid(alpha=0.3)
    fig.tight_layout()
    return fig


def egms_map_figure(df):
    """Point distribution coloured by mean velocity (E, N columns as x, y). None if there is no usable data."""
    xy = (df.assign(E=to_num(df["E"]), N=to_num(df["N"]), v=to_num(df["mean_velocity"]))
            .dropna(subset=["E", "N", "v"]))
    if xy.empty:
        return None
    if len(xy) > MAX_SCATTER_POINTS:
        xy = xy.sample(MAX_SCATTER_POINTS, random_state=0)
    lo, hi = xy["v"].quantile([0.02, 0.98])                      # colour scale without outliers

    fig = Figure(figsize=(8, 8))
    ax = fig.subplots()
    sc = ax.scatter(xy["E"], xy["N"], c=xy["v"], s=1, cmap="RdYlBu", vmin=lo, vmax=hi, rasterized=True)
    fig.colorbar(sc, ax=ax, shrink=0.8, label="mean velocity")
    ax.set_aspect("equal", adjustable="datalim")
    ax.set_xlabel("E")
    ax.set_ylabel("N")
    ax.set_title("EGMS U point distribution")
    fig.tight_layout()
    return fig


def clc_level1_areas(codes, areas):
    """Sum areas by CLC level 1 class (first digit of the code)."""
    out = {k: 0.0 for k, _, _ in CLC_LEVEL1}
    for c, a in zip(codes, areas):
        k = norm_code(c)[:1]
        if k in out and pd.notna(a):
            out[k] += float(a)
    return out


def clc_pie_figure(selected, totals):
    """Pie 1: selected classes inside the area. Pie 2: whole clc18 table. Both by level 1 class."""
    fig = Figure(figsize=(12, 5.5))
    ax0, ax1 = fig.subplots(1, 2)
    pie_colors = [c for _, _, c in CLC_LEVEL1]
    for ax, areas, title in ((ax0, selected, "Selected CLC classes in the selected area"),
                             (ax1, totals, "Whole CLC 2018 table")):
        vals = [areas.get(k, 0.0) for k, _, _ in CLC_LEVEL1]
        if sum(vals) > 0:
            ax.pie(vals, colors=pie_colors, startangle=90, radius=1.0,
                   autopct=lambda pct: f"{pct:.1f}%" if pct >= 2 else "",   # hide labels of tiny slices
                   wedgeprops={"edgecolor": "white"})
        else:
            ax.text(0.5, 0.5, "no data", ha="center", va="center", transform=ax.transAxes)
            ax.axis("off")
        ax.set_title(title, fontsize=11)
    fig.legend(handles=[Patch(facecolor=c, label=l) for _, l, c in CLC_LEVEL1],
               loc="lower center", ncol=3, frameon=False)
    fig.tight_layout(rect=(0, 0.12, 1, 1))
    return fig


# ---------- sections: (df, meta) -> list of flowables ----------
def section_forecast(df, meta):
    mean_s, min_s = to_num(df["mean_subs_"]), to_num(df["min_subs_a"])
    max_s, pts = to_num(df["max_subs_a"]), to_num(df["point_coun"])
    out = [
        p(f"The selected area contains <b>{fmt(len(df), 0)}</b> forecast line features."),
        p(f"The average subsidence value (<i>mean_subs_</i>) is <b>{fmt(mean_s.mean())}</b>, "
          f"ranging from {fmt(mean_s.min())} to {fmt(mean_s.max())}. The lowest minimum "
          f"(<i>min_subs_a</i>) is <b>{fmt(min_s.min())}</b> and the highest maximum "
          f"(<i>max_subs_a</i>) is <b>{fmt(max_s.max())}</b>."),
        p(f"The <i>point_coun</i> attribute sums up to <b>{fmt(pts.sum(), 0)}</b> measurement points."),
    ]
    return out + generic_tables(df)


def section_flooding(df, meta):
    df = df.rename(columns={"rb_name": "water region", "descript": "flooded risk area"})
    out = [p(f"The selected area contains <b>{fmt(len(df), 0)}</b> flood-affected features.")]
    dates = pd.to_datetime(df["data"], errors="coerce")
    if dates.notna().any():
        out.append(p(f"The records cover the period from <b>{dates.min():%Y-%m-%d}</b> "
                     f"to <b>{dates.max():%Y-%m-%d}</b>."))
    return out + generic_tables(df, exclude=("data",))


def section_egmsP(df, meta):
    vel = to_num(df["mean_velocity"])
    share_neg = 100 * (vel < 0).sum() / max(vel.notna().sum(), 1)
    out = [
        p(f"<b>{fmt(len(df), 0)}</b> EGMS measurement points were found in the selected area "
          f"(mean velocity filter: {fmt(meta['value_filter'][0], 0)} to {fmt(meta['value_filter'][1], 0)})."),
        p(f"The mean velocity is <b>{fmt(vel.mean())}</b> (median {fmt(vel.median())}). "
          f"<b>{fmt(share_neg, 1)}%</b> of the points have a negative velocity, which typically indicates subsidence."),
    ]
    if meta["clc_codes"]:
        out.append(p(f"Only points located in the selected CLC classes are included: {clc_names(meta['clc_codes'])}."))
    out += generic_tables(df)

    # distributions of velocity and RMSE + point map
    out += [h2("Distribution of mean velocity and RMSE"), fig_to_image(egms_histograms_figure(df))]
    map_fig = egms_map_figure(df)
    if map_fig is not None:
        out += [h2("Spatial distribution of points"), fig_to_image(map_fig, width_cm=13)]
        if len(df) > MAX_SCATTER_POINTS:
            out.append(Paragraph(f"The map shows a random sample of {fmt(MAX_SCATTER_POINTS, 0)} points. "
                                 f"Colour scale is limited to the 2nd-98th percentile of mean velocity.",
                                 STYLES["small"]))

    d = point_density(df)
    if not d.empty:
        total_pts, total_area = d["points"].sum(), d["sum_area_ha"].sum()
        overall = total_pts / total_area if total_area > 0 else float("nan")
        out += [h2("Point density by CLC class"),
                p(f"The overall density is <b>{fmt(overall, 3)}</b> points per hectare "
                  f"({fmt(total_pts, 0)} points over {fmt(total_area)} ha).")]
        ranked = d.dropna(subset=["density"]).sort_values("density", ascending=False)
        if not ranked.empty:
            top = ranked.iloc[0]
            out.append(p(f"The highest density occurs in class <b>{top['code_18']}</b> "
                         f"({clc_label(top['code_18'])}): <b>{fmt(top['density'], 3)}</b> points per hectare."))
        rows = [["CLC", "Description", "Points", "Area [ha]", "Density [pts/ha]"]]
        for _, r in d.iterrows():
            rows.append([r["code_18"], cell(clc_label(r["code_18"])), fmt(r["points"], 0),
                         fmt(r["sum_area_ha"]), fmt(r["density"], 3)])
        out.append(styled_table(rows, col_widths=[1.6 * cm, 6.6 * cm, 2.2 * cm, 3.3 * cm, 3.3 * cm]))
        out.append(Paragraph(
            "Density = number of points / total area of the CLC polygons the points belong to "
            "(each polygon counted once). Polygons only partly inside the selected area are counted "
            "with their full area, so values near the area boundary may be underestimated.", STYLES["small"]))
        n_codes = len(meta["clc_codes"])          # [] = no filter ("100" or empty)
        if n_codes == 0 or n_codes >= 3:
            out += [h2("Charts"), fig_to_image(density_figure(d))]
    return out


def section_clc(df, meta):
    codes = meta["clc_codes"]
    df = df.assign(area_ha=to_num(df["area_ha"]), code_18=df["code_18"].map(norm_code))
    g = df.groupby("code_18").agg(polygons=("id", "count"), area=("area_ha", "sum"))
    if codes:
        g["in_aoi"] = to_num(df["area_in_aoi_ha"]).groupby(df["code_18"]).sum()
    g = g.sort_values("area", ascending=False).reset_index()

    out = []
    if not codes:
        total = g["area"].sum()
        out.append(p("No CLC class filter was applied, so all land-cover classes are included."))
        out.append(p(f"<b>{fmt(g['polygons'].sum(), 0)}</b> CLC polygons of <b>{len(g)}</b> land-cover classes "
                     f"intersect the selected area; their total area is <b>{fmt(total)}</b> ha."))
        if not g.empty and total > 0:
            top = g.iloc[0]
            out.append(p(f"The largest class is <b>{top['code_18']}</b> ({clc_label(top['code_18'])}), "
                         f"covering {fmt(100 * top['area'] / total, 1)}% of this area."))
        rows = [["CLC", "Description", "Polygons", "Area [ha]", "Share [%]"]]
        for _, r in g.iterrows():
            share = 100 * r["area"] / total if total > 0 else float("nan")
            rows.append([r["code_18"], cell(clc_label(r["code_18"])), fmt(r["polygons"], 0),
                         fmt(r["area"]), fmt(share, 1)])
        out.append(styled_table(rows, col_widths=[1.6 * cm, 7.0 * cm, 2.2 * cm, 3.6 * cm, 2.6 * cm]))
        return out

    out.append(p(f"Selected CLC classes: {clc_names(codes)}."))
    found = set(g["code_18"])
    missing = [norm_code(c) for c in codes if norm_code(c) not in found]
    if missing:
        out.append(p(f"No polygons were found in the selected area for: {', '.join(missing)}."))
    if g.empty:
        return out
    tot_full, tot_in = g["area"].sum(), g["in_aoi"].sum()
    out.append(p(f"The selected classes cover <b>{fmt(tot_in)}</b> ha inside the selected area, which is "
                 f"<b>{fmt(100 * tot_in / tot_full, 1) if tot_full else '-'}%</b> of the full area "
                 f"({fmt(tot_full)} ha, from the <i>area_ha</i> attribute) of the intersecting polygons."))
    rows = [["CLC", "Description", "Polygons", "Total area [ha]", "Inside area [ha]", "Inside [%]"]]
    for _, r in g.iterrows():
        share = 100 * r["in_aoi"] / r["area"] if r["area"] else float("nan")
        rows.append([r["code_18"], cell(clc_label(r["code_18"])), fmt(r["polygons"], 0),
                     fmt(r["area"]), fmt(r["in_aoi"]), fmt(share, 1)])
    out.append(styled_table(rows, col_widths=[1.5 * cm, 5.5 * cm, 1.9 * cm, 2.8 * cm, 2.9 * cm, 2.4 * cm]))

    # pie charts by level 1 class: selected classes in the area vs the whole clc18 table
    totals = meta.get("clc_totals")
    if totals:
        selected = clc_level1_areas(g["code_18"], g["in_aoi"])
        out += [h2("Land cover structure (CLC level 1)"),
                fig_to_image(clc_pie_figure(selected, totals), width_cm=16),
                Paragraph("Left: share of the selected CLC classes inside the selected area (area clipped to the "
                          "area of interest). Right: share of all CLC 2018 polygons in the database "
                          "(<i>area_ha</i> attribute).", STYLES["small"])]
    return out


def make_trough_section(label):
    def _section(df, meta):
        area = to_num(df["area_m2"])
        
        out = [
            p(f"The selected area contains <b>{fmt(len(df), 0)}</b> {label} features."),
            p(f"Their total area is <b>{fmt(area.sum() / 1e6, 3)}</b> km² (mean {fmt(area.mean())} m², "
              f"largest {fmt(area.max())} m²)."),
        ]
        if(label == "Subsidence troughs variant 2"):
                    out.appendleft(p(f"{label} is created through including some of non-measured areas into the detected depressions regions"))
        return out + generic_tables(df)
    return _section


SECTIONS = {
    "forecast": section_forecast,
    "flooding": section_flooding,
    "egmsP": section_egmsP,
    "dsa": make_trough_section("subsidence trough variant 1"),
    "dsaf": make_trough_section("subsidence trough variant 2"),
    "clc": section_clc,
}


# ---------- cross-layer analysis ----------
def section_crossings(meta):
    out = []
    for key, c in meta["crossings"].items():
        name = LAYER_TITLES[key]
        if c["pairs"] > 0:
            out.append(p(f"The forecast lines intersect the <b>{name}</b> layer at <b>{fmt(c['pairs'], 0)}</b> "
                         f"line pairs, involving {fmt(c['trough_features'], 0)} trough features. Both layers describe "
                         f"the occurrence of subsidence troughs, so these intersections mark places where "
                         f"the forecast and the delineated troughs coincide."))
        else:
            out.append(p(f"The forecast lines do not intersect the <b>{name}</b> layer anywhere in the selected "
                         f"area. Although both layers describe subsidence troughs, they indicate different locations."))
    return ([Paragraph("Forecast vs. subsidence troughs", STYLES["h1"])] + out) if out else []


def section_hazard(data, meta):
    keys = []
    for k in ("dsa", "dsaf", "flooding", "clc"):
        if k not in data or data[k].empty:
            continue
        if k == "clc" and not meta["clc_codes"]:     # all classes = whole area, not informative
            continue
        keys.append(k)
    if not keys:
        return []
    names = ", ".join(LAYER_TITLES[k] for k in keys)
    return [Paragraph("Areas of increased subsidence hazard", STYLES["h1"]),
            p(f"The selected area contains objects from the following layers: <b>{names}</b>. "
              f"Locations covered by subsidence troughs, flood-affected areas and the selected land-cover "
              f"classes are places of <b>particularly high subsidence hazard</b> and deserve special attention.")]


# ---------- PDF assembly ----------
def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont(FONT, 8)
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Page {doc.page}")
    canvas.restoreState()


def build_report_pdf(data: dict, meta: dict) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                            topMargin=2 * cm, bottomMargin=2 * cm, title="Detected Subsidence Areas Report")

    coords = ", ".join(f"{v:.5f}" for v in meta["coords"])
    clc_txt = clc_names(meta["clc_codes"]) if meta["clc_codes"] else "all classes (no filter)"
    story = [
        Paragraph("Detected Subsidence Areas Report", STYLES["title"]),
        Paragraph("Report parameters", STYLES["h1"]),
        p(f"Area of interest: {meta['mode']}, coordinates (EPSG:4326): {coords}"),
        p(f"Velocity filter: {meta['value_filter'][0]} to {meta['value_filter'][1]}"),
        p(f"CLC classes: {clc_txt}"),
    ]

    summary = [["Layer", "Objects in area"]]
    summary += [[LAYER_TITLES[k], fmt(len(df), 0)] for k, df in data.items()]
    story += [Paragraph("Summary", STYLES["h1"]), styled_table(summary, col_widths=[9 * cm, 4 * cm])]

    for key, df in data.items():
        story.append(Paragraph(LAYER_TITLES[key], STYLES["h1"]))
        if df.empty:
            story.append(p("No objects found in the selected area."))
        else:
            story.extend(SECTIONS[key](df, meta))

    story += section_crossings(meta)
    story += section_hazard(data, meta)

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buf.getvalue()