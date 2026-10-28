# Project summary and context

This project is a web-based system for analysing areas at risk of land subsidence. Its core is the detection of subsidence bowls in InSAR/EGMS data using the methods supplied by my supervisor (circlet transform, Hough-based circle and ellipse detection), combined with land cover (CLC 2018), CBDG subsidence forecasts and flood-prone area data. Supporting analysis is done in ArcGIS Pro, while the final application is a web app.

## Stack and key decisions

The working coordinate system is EPSG:3035 (ETRS89-LAEA), which matches the native CRS of EGMS. All other layers are reprojected to it, and the transformation to EPSG:4326 happens in SQL only when data is sent to the browser. Data lives in PostgreSQL/PostGIS. The backend is Python and Flask, configured through `.env` and `config.py`, and the frontend uses plain Leaflet with vanilla JS. I chose this over react-leaflet because of time constraints. The API is independent of the frontend, so the choice can be revisited later without touching the backend. All image processing for bowl detection is done in MATLAB, working directly on the GeoTIFF exported from ArcGIS. The binarisation step is done in ArcGIS Pro with a threshold of -15 mm/year on the vertical velocity raster (class 2 means intensive subsidence, class 1 means everything else).

## What is done

On the data side, I have the EGMS L3 100 km vertical product (2019-2023) in EPSG:3035, plus a separate horizontal displacement set (2020-2024). In PostGIS, EGMS is split into a static `egms_points` table and a long-format `egms_timeseries` table. In ArcGIS Pro I have prepared CLC 2018 clipped to the study area, the CBDG forecast layer (`subs_act` in metres, plus the `COType` cluster field from Local Moran's I), a DTM with hillshade and slope, and a flood-prone areas shapefile. The CLC file has been loaded into PostGIS, though its geometries still carry a Z dimension that needs removing.

The detection pipeline in MATLAB is in progress. It builds a density map of intensive-subsidence pixels (Gaussian filter, sigma 2.5), fills NoData pockets, applies the circlet transform (fdct2) as a shape filter, and uses `imreconstruct` to derive bowl masks. The target radius range is 250-2500 m (2.5-25 px at 100 m resolution). The code is still being debugged. Detected contours will be exported to a shapefile with ID and Area_m2 attributes, georeferenced via `intrinsicToWorld`.

The application skeleton exists: a Flask backend (`app.py`, `db.py`, `layers.py`), a frontend (`index.html`, `map.js`, `layers.js`, `style.css`), mock rasters for testing, and a loader script and notebook for importing vector files into PostGIS. The planned API consists of a layer catalogue endpoint (`/api/layers`), a per-layer GeoJSON endpoint with bbox filtering (`/api/layers/<name>?bbox=...`), and a time series endpoint for individual points.

## What remains

The immediate tasks are to strip the Z dimension from the CLC table and confirm the correct layer was read from the GeoPackage, then load the detected bowl contours into a `risk_areas` table and register it in the layer config. On the frontend, `layers.js` and `map.js` need to be rewritten around the layer catalogue, loading each layer's data only when it is ticked in the layer control, followed by a time series chart on point click and a risk layer. Rasters (EGMS, hillshade) will be served as tiles or image overlays through a separate `/api/rasters` blueprint. Later stages include SNAP interferogram processing (conditional), ranking of at-risk areas, report generation, analysis of the study area and system testing.

## Things to verify in the code

The earlier `app.py` imports `from routes.layers import layers_bp` and `rasters_bp`, but the current tree has no `routes/` folder and no `rasters.py`. `layers.py` sits directly in `app/backend/`, so the imports need adjusting, and the `rasters_bp` import should be commented out until that file exists. Also, `config.py` is in the project root while `app.py` is in `app/backend/`, so running `python app/backend/app.py` will not find `config`. Either move `config.py` next to `app.py`, add the project root to `sys.path`, or run the app as a module from the root. The same decision determines how `src/load_vector.py` should set up its import path.