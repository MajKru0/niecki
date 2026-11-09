import sys, pathlib
import threading
import webbrowser
import os
ROOT = pathlib.Path(__file__).resolve().parents[2]      # korzeń projektu
sys.path.insert(0, str(ROOT))    

from flask import Flask
from flask_cors import CORS
from layers import layers_bp
from config import Config

FRONTEND_DIR = ROOT / "app" / "frontend"

app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")
CORS(app, origins=[Config.FRONTEND_URL])

app.register_blueprint(layers_bp, url_prefix='/api/layers')

@app.route("/")
def index():
    return app.send_static_file("index.html")

@app.route('/api/health')
def health():
    return {"status": "ok", "message": "Backend works"}

if __name__ == '__main__':
    #app.run(debug=True, port=5000) #TODO: debug=false after developing
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        threading.Timer(1.0, lambda: webbrowser.open("http://127.0.0.1:5000")).start()
    app.run(debug=True, port=5000)