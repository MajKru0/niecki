import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))

from flask import Flask
from flask_cors import CORS
from layers import layers_bp
from config import Config

app = Flask(__name__)
CORS(app, origins=[Config.FRONTEND_URL])

app.register_blueprint(layers_bp, url_prefix='/api/layers')

@app.route('/api/health')
def health():
    return {"status": "ok", "message": "Backend works"}

if __name__ == '__main__':
    app.run(debug=True, port=5000) #TODO: debug=false after developing